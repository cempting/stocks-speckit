import csv
import json
from copy import deepcopy
from datetime import date
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from market_data.domain.stock_chart import stock_chart_lookback_days
from tests.fixtures.catalogs.ui import configure_ui, edit_csv, publish_entry
from tests.membership_helpers import build_v2_release, membership_fixture

ROOT = Path(__file__).parents[2]
LOOKUP_PREFIX = "market_leadership.stock_lookup."


def _run_lookup(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
    *,
    include_canada: bool = False,
) -> tuple[AppTest, list[tuple[str, ...]], list[str], list[str]]:
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    if include_canada:
        _add_canada_region(manifest)
    provider_calls = configure_ui(monkeypatch, manifest)
    history_calls: list[str] = []
    evidence_calls: list[str] = []

    def load_selected_history(*_args, **_kwargs):
        history_calls.append("selected history")
        return SimpleNamespace(series=())

    monkeypatch.setattr(
        "market_leadership.bootstrap.load_selected_stock_history",
        load_selected_history,
    )
    monkeypatch.setattr(
        "market_leadership.bootstrap.load_selected_company_evidence",
        lambda *_args, **_kwargs: evidence_calls.append("company evidence"),
    )
    return (
        AppTest.from_file(
            ROOT / "src/market_leadership/ui/workflows/stock_lookup.py"
        ).run(timeout=20),
        provider_calls,
        history_calls,
        evidence_calls,
    )


def _add_canada_region(manifest: Path) -> None:
    document = json.loads(manifest.read_text())
    canada = deepcopy(document["regions"][0])
    canada.update(region_id="CA", name="Test Canada")
    document["regions"].append(canada)
    for artifact in tuple(document["artifacts"]):
        if artifact["role"] == "audit":
            continue
        source = manifest.parent / artifact["path"]
        with source.open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        assert fields
        target = manifest.parent / f"canada-{artifact['role']}.csv"
        with target.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            if artifact["role"] == "hierarchy":
                writer.writerow(
                    dict(
                        rows[0],
                        RegionId="CA",
                        NodeId="ca-sector",
                        SectorId="ca-sector",
                        Name="Canadian sector",
                    )
                )
        document["artifacts"].append(
            dict(
                artifact,
                artifact_id=f"canada-{artifact['role']}",
                region_id="CA",
                path=target.name,
                row_count=1 if artifact["role"] == "hierarchy" else 0,
                sha256=sha256(target.read_bytes()).hexdigest(),
            )
        )
    manifest.write_text(json.dumps(document))
    publish_entry(manifest)


def test_lookup_requires_explicit_identity_and_listing_for_ambiguous_results(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, provider_calls, history_calls, evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("share-class").run(timeout=20)

    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    assert any("share-class-a" in option for option in instrument_picker.options)
    assert any("share-class-b" in option for option in instrument_picker.options)
    assert instrument_picker.value is None

    selected_option = next(
        option for option in instrument_picker.options if "share-class-b" in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    listing_picker = app.selectbox(LOOKUP_PREFIX + "lookup_listing")
    assert listing_picker.value is None
    assert listing_picker.options
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    provider_calls.clear()
    history_calls.clear()
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)

    assert not app.exception
    assert any("share-class-b" in item.value for item in app.caption)
    assert provider_calls == []
    assert history_calls == []
    assert evidence_calls == []


def test_history_is_requested_only_after_explicit_load(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, _provider_calls, history_calls, _evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("share-class").run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(
        option for option in instrument_picker.options if "share-class-b" in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    listing_picker = app.selectbox(LOOKUP_PREFIX + "lookup_listing")
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)

    assert history_calls == []
    app.button(LOOKUP_PREFIX + "load_lookup_history").click().run(timeout=20)

    assert not app.exception
    assert history_calls == ["selected history"]


def test_selected_chart_range_requests_and_reuses_required_history_coverage(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, _provider_calls, _history_calls, _evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    lookbacks: list[int] = []

    def load_history(*_args, **kwargs):
        lookbacks.append(kwargs["lookback_days"])
        return SimpleNamespace(series=())

    monkeypatch.setattr("market_leadership.bootstrap.load_selected_stock_history", load_history)
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("share-class").run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(
        option for option in instrument_picker.options if "share-class-b" in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    listing_picker = app.selectbox(LOOKUP_PREFIX + "lookup_listing")
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)

    expected_lookback = stock_chart_lookback_days(
        app.date_input(LOOKUP_PREFIX + "as_of").value,
        "24m",
    )
    range_key = LOOKUP_PREFIX + "detail.chart_range"
    app.selectbox(range_key).select("24m").run(timeout=20)
    app.button(LOOKUP_PREFIX + "load_lookup_history").click().run(timeout=20)

    assert not app.exception
    assert lookbacks == [expected_lookback]

    app.selectbox(range_key).select("1m").run(timeout=20)
    assert not app.exception
    assert lookbacks == [expected_lookback, expected_lookback]


def test_changing_as_of_date_clears_selected_lookup_context(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, _provider_calls, _history_calls, _evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("share-class").run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(
        option for option in instrument_picker.options if "share-class-b" in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    listing_picker = app.selectbox(LOOKUP_PREFIX + "lookup_listing")
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)
    assert app.session_state[LOOKUP_PREFIX + "lookup_open"] is True

    app.date_input(LOOKUP_PREFIX + "as_of").set_value(date(2026, 10, 1)).run(timeout=20)

    assert not app.exception
    assert LOOKUP_PREFIX + "lookup_open" not in app.session_state
    assert LOOKUP_PREFIX + "lookup_history" not in app.session_state
    assert app.selectbox(LOOKUP_PREFIX + "lookup_instrument").value is None


def test_changing_region_clears_selected_lookup_and_history_state(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, _provider_calls, history_calls, _evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path, include_canada=True
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("share-class").run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(
        option for option in instrument_picker.options if "share-class-b" in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    listing_picker = app.selectbox(LOOKUP_PREFIX + "lookup_listing")
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)
    app.button(LOOKUP_PREFIX + "load_lookup_history").click().run(timeout=20)
    assert history_calls == ["selected history"]

    app.selectbox(LOOKUP_PREFIX + "region").select("Test Canada").run(timeout=20)

    assert not app.exception
    assert LOOKUP_PREFIX + "lookup_open" not in app.session_state
    assert LOOKUP_PREFIX + "lookup_history" not in app.session_state
    assert LOOKUP_PREFIX + "lookup_instrument" not in app.session_state
    assert any("No retained stock identity matches" in item.value for item in app.info)


def test_catalog_revision_change_clears_selected_lookup_and_history_state(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, _provider_calls, history_calls, _evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("share-class").run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(
        option for option in instrument_picker.options if "share-class-b" in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    listing_picker = app.selectbox(LOOKUP_PREFIX + "lookup_listing")
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)
    app.button(LOOKUP_PREFIX + "load_lookup_history").click().run(timeout=20)
    assert history_calls == ["selected history"]

    manifest = tmp_path / "catalog-v2" / "manifest.json"
    edit_csv(manifest, "hierarchy", lambda rows: rows[0].update(Name="Revised sector"))
    publish_entry(manifest)
    app.run(timeout=20)

    assert not app.exception
    assert LOOKUP_PREFIX + "lookup_open" not in app.session_state
    assert LOOKUP_PREFIX + "lookup_history" not in app.session_state
    assert app.selectbox(LOOKUP_PREFIX + "lookup_instrument").value is None


@pytest.mark.parametrize(
    ("query", "instrument_id"),
    [
        ("unassigned", "unassigned"),
        ("unverified-listing", "unverified-listing"),
    ],
)
def test_lookup_opens_without_a_verified_listing_or_remote_prefetch(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
    query: str,
    instrument_id: str,
) -> None:
    app, provider_calls, history_calls, evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value(query).run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(
        option for option in instrument_picker.options if instrument_id in option
    )
    instrument_picker.select(selected_option).run(timeout=20)
    assert not any(
        item.key == LOOKUP_PREFIX + "lookup_listing" for item in app.selectbox
    )
    provider_calls.clear()
    history_calls.clear()
    app.button(LOOKUP_PREFIX + "open_lookup").click().run(timeout=20)

    assert not app.exception
    assert any(instrument_id in item.value for item in app.caption)
    assert any(
        "No verified listing is active" in item.value for item in app.info
    )
    assert provider_calls == []
    assert history_calls == []
    assert evidence_calls == []


def test_no_match_clears_the_previous_lookup_selection(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    app, _provider_calls, _history_calls, _evidence_calls = _run_lookup(
        monkeypatch, catalog_release, tmp_path
    )
    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("unassigned").run(timeout=20)
    instrument_picker = app.selectbox(LOOKUP_PREFIX + "lookup_instrument")
    selected_option = next(option for option in instrument_picker.options if "unassigned" in option)
    instrument_picker.select(selected_option).run(timeout=20)

    app.text_input(LOOKUP_PREFIX + "lookup_query").set_value("no-such-retained-stock").run(
        timeout=20
    )

    assert not app.exception
    assert any("No retained stock identity matches" in item.value for item in app.info)
    assert LOOKUP_PREFIX + "lookup_instrument" not in app.session_state
