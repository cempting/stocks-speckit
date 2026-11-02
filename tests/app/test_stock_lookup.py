from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import configure_ui
from tests.membership_helpers import build_v2_release, membership_fixture

ROOT = Path(__file__).parents[2]
LOOKUP_PREFIX = "market_leadership.progressive_discovery."


def _run_lookup(
    monkeypatch: pytest.MonkeyPatch,
    catalog_release: Path,
    tmp_path: Path,
) -> tuple[AppTest, list[tuple[str, ...]], list[str], list[str]]:
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    provider_calls = configure_ui(monkeypatch, manifest)
    history_calls: list[str] = []
    evidence_calls: list[str] = []
    monkeypatch.setattr(
        "market_leadership.ui.workflows.discovery_page.load_member_history",
        lambda *_args, **_kwargs: history_calls.append("member history"),
    )
    monkeypatch.setattr(
        "market_leadership.bootstrap.load_selected_company_evidence",
        lambda *_args, **_kwargs: evidence_calls.append("company evidence"),
    )
    return (
        AppTest.from_file(
            ROOT / "src/market_leadership/ui/workflows/discovery_page.py"
        ).run(timeout=20),
        provider_calls,
        history_calls,
        evidence_calls,
    )


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
