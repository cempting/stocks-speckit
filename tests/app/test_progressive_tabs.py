import os
import shutil
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import configure_ui

ROOT = Path(__file__).parents[2]


def _select_industry(app, key, node_id):
    selectbox = app.selectbox(key + "industry")
    option = next(value for value in selectbox.options if value.endswith(f"[{node_id}]"))
    return selectbox.select(option)


def test_entrypoint_has_four_tabs_and_resolves_catalog_once(monkeypatch, catalog_release):
    from market_data.catalog import CatalogReader

    calls = configure_ui(monkeypatch, catalog_release)
    reads = []
    original = CatalogReader.read

    def read(self, path):
        snapshot = original(self, path)
        reads.append(snapshot)
        return snapshot

    monkeypatch.setattr(CatalogReader, "read", read)
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Discovery",
        "Industry Deep-Dive",
        "Yahoo Classification Preview",
        "Find a stock",
    ]
    assert len(reads) == 1
    assert calls == [("TEST_ETF",)]
    app.run()
    assert len(reads) == 2
    assert reads[0] is reads[1]


@pytest.mark.parametrize("corrupt", ["manifest", "same-size-stock-file"])
def test_invalid_catalog_clears_both_tabs_without_provider_calls(
    monkeypatch, catalog_release, corrupt
):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    for prefix in (
        "market_leadership.progressive_discovery.",
        "market_leadership.screening.",
    ):
        for suffix in (
            "sector",
            "industry",
            "stock",
            "stocks",
            "scores",
            "score_context",
            "context",
        ):
            app.session_state[prefix + suffix] = "test-sector" if suffix == "sector" else "stale"
    app.session_state["market_leadership.progressive_discovery.thumbnail_period"] = "1w"
    lookup_prefix = "market_leadership.stock_lookup."
    app.session_state[lookup_prefix + "lookup_query"] = "stale"
    app.session_state[lookup_prefix + "lookup_history"] = "stale"
    app.session_state["dark_mode"] = True
    calls.clear()
    if corrupt == "manifest":
        catalog_release.write_text("{}")
    else:
        path = catalog_release.parent / "stocks.csv"
        original = path.stat()
        content = path.read_bytes()
        path.write_bytes(content.replace(b"Test stock 1", b"Test stock X"))
        os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
        assert path.stat().st_size == original.st_size
        assert path.stat().st_mtime_ns == original.st_mtime_ns
    app.run()
    assert not app.exception
    assert any("catalog" in item.value.lower() for item in app.error)
    assert calls == []
    assert app.session_state["dark_mode"] is True
    assert app.session_state["market_leadership.progressive_discovery.thumbnail_period"] == "1w"
    for prefix in ("market_leadership.progressive_discovery.", "market_leadership.screening."):
        for suffix in ("sector", "industry", "stocks", "scores"):
            assert prefix + suffix not in app.session_state
    assert not any(key.startswith(lookup_prefix) for key in app.session_state)


def test_discovery_does_not_read_legacy_experimental_catalog(monkeypatch, catalog_release):
    configure_ui(monkeypatch, catalog_release)
    monkeypatch.setenv("EXPERIMENTAL_UNIVERSE_CATALOG", str(catalog_release.parent / "unused.json"))
    monkeypatch.setenv(
        "MARKET_UNIVERSE_DATABASE_PATH", str(catalog_release.parent / "unused.sqlite")
    )
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    assert not app.exception
    assert not any("Experimental provider-label" in item.value for item in app.subheader)
    assert not (catalog_release.parent / "unused.sqlite").exists()


def test_two_controlled_activations_preserve_unaffected_cohort_scores_and_price_cache(
    monkeypatch, catalog_release
):
    from market_data.catalog import CatalogReader, activate_release
    from market_leadership.ui.workflows import discovery_page
    from tests.app.test_stock_detail import _score_result
    from tests.fixtures.catalogs.ui import edit_csv

    calls = configure_ui(monkeypatch, catalog_release)
    entry = catalog_release.parent / "controlled-store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    monkeypatch.setenv("MARKET_CATALOG_MANIFEST_PATH", str(entry))
    reader = CatalogReader()
    first_snapshot = reader.read(entry)
    score_calls = []
    discovery_calls = []
    original_calculate = discovery_page.discover_sectors_from_history
    discovery_page._calculate_discovery.clear()

    def calculate(*args, **kwargs):
        discovery_calls.append(kwargs["sector_ids"])
        return original_calculate(*args, **kwargs)

    monkeypatch.setattr(discovery_page, "discover_sectors_from_history", calculate)

    def score(
        members,
        *,
        cutoff,
        refresh=False,
        cohort_fingerprint=None,
        comparison_context=None,
    ):
        score_calls.append(cohort_fingerprint)
        assert comparison_context is not None
        return _score_result(members)

    monkeypatch.setattr("market_leadership.application.score_industry.score_industry", score)
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    discovery = "market_leadership.progressive_discovery."
    screening = "market_leadership.screening."
    app.button(discovery + "sector_tape_select_test-sector").click().run()
    _select_industry(app, discovery, "test-cloud").run()
    app.selectbox(screening + "sector").select("test-sector").run()
    _select_industry(app, screening, "test-cloud").run()
    app.multiselect(screening + "stocks").select("test-stock-1").run()
    next(button for button in app.button if button.label == "Load peer scores").click().run()
    app.segmented_control(discovery + "thumbnail_period").set_value("1w").run()
    app.date_input[0].set_value(date(2026, 10, 30)).run()
    next(button for button in app.button if button.label == "Load peer scores").click().run()
    assert not app.exception
    loaded = len(score_calls)
    calculated = len(discovery_calls)
    calls.clear()
    candidate = catalog_release.parent / "next-authoring/manifest.json"
    shutil.copytree(first.manifest_path.parent, candidate.parent)
    edit_csv(
        candidate,
        "stocks",
        lambda rows: [
            row.update(Name="Unrelated reviewed change")
            for row in rows
            if row["IndustryId"] == "test-hardware"
        ],
    )
    second = activate_release(entry, candidate, expected_release=first.release_id)
    second_snapshot = reader.read(entry)
    assert second.release_id != first.release_id
    assert reader.read(entry) is second_snapshot
    as_of = date(2026, 10, 30)
    assert first_snapshot.cohort_fingerprint(
        first_snapshot.scope_on("US", as_of), "test-cloud", as_of
    ) == (
        second_snapshot.cohort_fingerprint(
            second_snapshot.scope_on("US", as_of), "test-cloud", as_of
        )
    )
    app.run()
    assert not app.exception
    assert len(score_calls) == loaded
    assert len(discovery_calls) == calculated
    assert app.multiselect(screening + "stocks").value == ["test-stock-1"]
    assert app.segmented_control(discovery + "thumbnail_period").value == "1w"
    assert app.date_input[0].value == as_of
    assert all("TEST_STOCK_1" not in symbols for symbols in calls)
