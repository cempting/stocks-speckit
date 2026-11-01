import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import bound_classification, configure_ui, edit_csv, publish_entry

ROOT = Path(__file__).parents[2]
PAGE = ROOT / "src/market_leadership/ui/workflows/discovery_page.py"
DEEP = ROOT / "src/market_leadership/ui/workflows/industry_deep_dive.py"
PREFIX = "market_leadership.progressive_discovery."


def _run(monkeypatch, catalog_release):
    configure_ui(monkeypatch, catalog_release)
    return AppTest.from_file(PAGE).run(timeout=20)


def _stocks(app):
    app.button(PREFIX + "sector_tape_select_test-sector").click().run(timeout=20)
    app.selectbox(PREFIX + "industry").select("test-cloud").run(timeout=20)
    return app


@pytest.mark.parametrize("industry", ["test-cloud", "test-specialist", "test-empty"])
def test_clickable_sector_and_industry_names_open_their_child_tapes(
    monkeypatch, catalog_release, industry
):
    app = _run(monkeypatch, catalog_release)
    app.segmented_control(PREFIX + "thumbnail_period").set_value("1w").run()
    app.segmented_control(PREFIX + "performance_basis").set_value("vs S&P 500").run()
    as_of = app.date_input[0].value
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert not app.exception
    assert app.session_state[PREFIX + "sector"] == "test-sector"
    assert not any(widget.key == PREFIX + "sector" for widget in app.selectbox)
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value in {"Status", "Representation"} for item in app.caption)
    assert not any(item.value == "Representation type" for item in app.caption)
    button = app.button(PREFIX + "industry_tape_select_" + industry)
    assert button.help
    button.click().run()
    assert not app.exception
    assert app.selectbox(PREFIX + "industry").value == industry
    assert any(item.value == "Contained stocks" for item in app.subheader)
    if industry == "test-empty":
        assert any("no active stock memberships" in item.value for item in app.info)
    else:
        assert any(item.label == "TEST_STOCK_1 · Test stock 1" for item in app.button)
        assert any(item.value == "Not loaded" for item in app.markdown)
    assert app.segmented_control(PREFIX + "thumbnail_period").value == "1w"
    assert app.segmented_control(PREFIX + "performance_basis").value == "vs S&P 500"
    assert app.date_input[0].value == as_of


@pytest.mark.parametrize(
    ("target", "heading", "sector", "industry"),
    [
        ("sectors", "Sector performance", None, None),
        ("sector", "Industry momentum", "test-sector", None),
        ("industry", "Contained stocks", "test-sector", "test-cloud"),
    ],
)
@pytest.mark.parametrize("placeholder", [False, True])
def test_breadcrumbs_return_to_ancestors_and_preserve_controls(
    monkeypatch, catalog_release, target, heading, sector, industry, placeholder
):
    app = _stocks(_run(monkeypatch, catalog_release))
    app.segmented_control(PREFIX + "thumbnail_period").set_value("1w").run()
    app.segmented_control(PREFIX + "performance_basis").set_value("vs S&P 500").run()
    as_of = app.date_input[0].value
    if placeholder:
        next(
            button for button in app.button if "Unresolved placeholder" in button.label
        ).click().run()
    else:
        app.selectbox(PREFIX + "stock_picker").select("test-stock-1").run()
    assert not app.exception
    assert app.button(PREFIX + "breadcrumb_sectors").label == "US sectors"
    assert any("Test stock" in item.value for item in app.caption)
    app.button(PREFIX + "breadcrumb_" + target).click().run()
    assert not app.exception
    assert any(item.value == heading for item in app.subheader)
    if sector is not None:
        assert app.session_state[PREFIX + "sector"] == sector
        assert app.selectbox(PREFIX + "industry").value == industry
    else:
        assert PREFIX + "sector" not in app.session_state
        assert PREFIX + "industry" not in app.session_state
    assert PREFIX + "stock" not in app.session_state
    assert app.segmented_control(PREFIX + "thumbnail_period").value == "1w"
    assert app.segmented_control(PREFIX + "performance_basis").value == "vs S&P 500"
    assert app.date_input[0].value == as_of


def test_breadcrumbs_allow_return_from_industry_and_empty_stock_lists(monkeypatch, catalog_release):
    app = _run(monkeypatch, catalog_release)
    assert any(item.value == "US sectors" for item in app.caption)
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    app.button(PREFIX + "breadcrumb_sectors").click().run()
    assert not app.exception
    assert PREFIX + "sector" not in app.session_state
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    app.selectbox(PREFIX + "industry").select("test-empty").run()
    assert any("no active stock memberships" in item.value for item in app.info)
    app.button(PREFIX + "breadcrumb_sector").click().run()
    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert app.session_state[PREFIX + "sector"] == "test-sector"
    assert app.selectbox(PREFIX + "industry").value is None


def test_discovery_shows_only_sector_tape_until_sector_is_selected(monkeypatch, catalog_release):
    app = _run(monkeypatch, catalog_release)
    assert not app.exception
    assert any(item.value == "Sector performance" for item in app.subheader)
    assert not any(
        item.value in {"Industry momentum", "Contained stocks"} for item in app.subheader
    )
    assert not any(widget.key == PREFIX + "sector" for widget in app.selectbox)
    assert any("Price + 50 MA" in item.value for item in app.caption)
    assert any("Volume by price direction" in item.value for item in app.caption)
    assert any(item.value == "Ticker" for item in app.caption)
    assert not any(item.value == "Status" for item in app.caption)
    assert app.button(PREFIX + "sector_tape_select_test-sector").help
    assert not any(item.value == "Representation" for item in app.caption)
    assert any("not verified buyer or seller activity" in item.value for item in app.caption)


def test_sector_and_industry_selection_replaces_tape_and_shows_all_members(
    monkeypatch, catalog_release
):
    app = _run(monkeypatch, catalog_release)
    app.button(PREFIX + "sector_tape_select_test-sector").click().run(timeout=20)
    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Sector performance" for item in app.subheader)
    app.selectbox(PREFIX + "industry").select("test-cloud").run(timeout=20)
    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert any(item.label == "TEST_STOCK_1 · Test stock 1" for item in app.button)
    assert any("Unresolved placeholder" in item.label for item in app.button)
    assert any(item.value == "CAP Type" for item in app.caption)
    assert any(item.value == "Total Score" for item in app.caption)
    assert not any(item.value == "Name" for item in app.caption)
    assert not any(
        item.value in {"Quality", "Growth", "Cash Flow", "Score status", "Observed", "Chart status"}
        for item in app.caption
    )
    assert any(item.value == "Not loaded" for item in app.markdown)
    assert any(item.label == "Load peer scores" for item in app.button)


def test_thumbnail_period_and_performance_basis_persist_across_tapes(monkeypatch, catalog_release):
    app = _run(monkeypatch, catalog_release)
    period = app.segmented_control(PREFIX + "thumbnail_period")
    assert period.options == ["1w", "1m", "3m", "6m", "1y"]
    assert period.value == "3m"
    period.set_value("1w").run()
    app.segmented_control(PREFIX + "performance_basis").set_value("vs S&P 500").run()
    _stocks(app)
    assert not app.exception
    assert app.segmented_control(PREFIX + "thumbnail_period").value == "1w"
    assert app.segmented_control(PREFIX + "performance_basis").value == "vs S&P 500"


def test_cleared_performance_controls_use_preserved_defaults(monkeypatch, catalog_release):
    app = _run(monkeypatch, catalog_release)
    initial_cells = [item.proto.body for item in app.get("html")]
    initial_charts = [
        item.proto.spec for item in (app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart"))
    ]
    app.segmented_control(PREFIX + "thumbnail_period").set_value("1w").run()
    app.segmented_control(PREFIX + "performance_basis").set_value("vs S&P 500").run()
    app.segmented_control(PREFIX + "thumbnail_period").set_value(None).run()
    app.segmented_control(PREFIX + "performance_basis").set_value(None).run()
    assert not app.exception
    assert [item.proto.body for item in app.get("html")] == initial_cells
    assert [
        item.proto.spec for item in (app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart"))
    ] == initial_charts


@pytest.mark.parametrize("label", ["Sector", "Industry"])
def test_entity_tape_preserves_complete_column_and_row_order(label):
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    frame = _build_entity_tape(
        entity_rows=(("first", "First"), ("second", "Second")),
        label=label,
        representation_by_id={},
        history={},
        benchmark=pd.Series(dtype="float64"),
        requested_as_of=date(2026, 10, 30),
        observed_as_of=None,
        performance_mode="Absolute",
    )
    assert frame.columns.tolist() == [
        "Price chart",
        "Volume chart",
        label,
        "ETF" if label == "Industry" else "Ticker",
        "1 week",
        "1 month",
        "3 months",
        "6 months",
        "12 months",
        "Status",
    ] + (["Representation", "Representation type"] if label == "Industry" else []) + ["Node ID"]
    assert frame[label].tolist() == ["First", "Second"]
    assert frame["Node ID"].tolist() == ["first", "second"]
    assert frame["Status"].tolist() == ["Not covered", "Not covered"]


def test_thumbnail_period_does_not_change_performance_returns():
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    history = pd.DataFrame(
        {"close": range(100, 500), "volume": [1000] * 400},
        index=pd.bdate_range(end="2026-10-30", periods=400),
    )
    arguments = dict(
        entity_rows=(("first", "First"),),
        label="Sector",
        representation_by_id={"first": "FIRST"},
        history={"FIRST": history},
        benchmark=history["close"],
        requested_as_of=date(2026, 10, 30),
        observed_as_of=date(2026, 10, 30),
        performance_mode="Absolute",
    )
    short = _build_entity_tape(**arguments, preview_start=date(2026, 10, 23))
    long = _build_entity_tape(**arguments, preview_start=date(2025, 10, 30))
    windows = ["1 week", "1 month", "3 months", "6 months", "12 months"]
    pd.testing.assert_frame_equal(short[windows], long[windows])
    assert len(short["Price chart"][0]) < len(long["Price chart"][0])


def test_stock_views_do_not_request_hidden_industry_proxy(monkeypatch, catalog_release):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(PAGE).run(timeout=20)
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert set(calls[-1]) == {"TEST_ETF", "TEST_INVENTORY"}
    calls.clear()
    app.selectbox(PREFIX + "industry").select("test-cloud").run()
    assert not app.exception
    assert ("TEST_STOCK_1",) in calls
    assert all("TEST_INVENTORY" not in symbols for symbols in calls)
    calls.clear()
    app.selectbox(PREFIX + "stock_picker").select("test-stock-1").run()
    assert not app.exception
    assert all(symbols == ("TEST_ETF",) for symbols in calls)
    next(item for item in app.button if item.label == "Back to Discovery").click().run()
    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)


def test_discovery_and_deep_dive_ignore_future_classification(monkeypatch, catalog_release):
    bound_classification(catalog_release, "2029-12-31")
    document = json.loads(catalog_release.read_text())
    region = document["regions"][0]
    region["classifications"][0]["effective_to"] = "2029-12-31"
    future = dict(
        region["classifications"][0],
        classification_id="FUTURE",
        effective_from="2030-01-01",
        effective_to=None,
    )
    region["classifications"].append(future)
    catalog_release.write_text(json.dumps(document))
    app = _run(monkeypatch, catalog_release)
    app.date_input[0].set_value(date(2026, 10, 30)).run()
    assert not app.exception
    assert [
        button.key
        for button in app.button
        if button.key and button.key.startswith(PREFIX + "sector_tape_select_")
    ] == [PREFIX + "sector_tape_select_test-sector"]
    app.date_input[0].set_value(date(2019, 1, 1)).run()
    assert not app.exception
    assert any("classification" in item.value for item in (*app.info, *app.error))
    deep = AppTest.from_file(DEEP).run()
    assert not deep.exception
    assert deep.selectbox("market_leadership.screening.sector").options == ["test-sector"]


@pytest.mark.parametrize("invalid", [False, True])
def test_unavailable_catalog_shows_explicit_error_without_provider_calls(
    monkeypatch, catalog_release, invalid
):
    calls = configure_ui(monkeypatch, catalog_release)
    entry = catalog_release.parent / "CURRENT.json"
    if invalid:
        entry.write_text("invalid catalog")
    else:
        entry.unlink()
    app = AppTest.from_file(PAGE).run()
    assert not app.exception
    assert any("catalog" in item.value.lower() for item in app.error)
    assert calls == []


def test_inactive_region_clears_dependents_without_provider_calls(monkeypatch, catalog_release):
    import json

    calls = configure_ui(monkeypatch, catalog_release)
    app = _stocks(AppTest.from_file(PAGE).run())
    document = json.loads(catalog_release.read_text())
    document["regions"][0]["status"] = "inactive"
    catalog_release.write_text(json.dumps(document))
    publish_entry(catalog_release)
    calls.clear()
    app.run()
    assert not app.exception
    assert calls == []
    assert PREFIX + "industry" not in app.session_state


def test_changing_sector_clears_selected_industry_and_members(monkeypatch, catalog_release):
    app = _stocks(_run(monkeypatch, catalog_release))
    app.button(PREFIX + "breadcrumb_sectors").click().run()
    assert not app.exception
    assert PREFIX + "industry" not in app.session_state
    assert not any(item.label == "TEST_STOCK_1 · Test stock 1" for item in app.button)


def test_industry_deep_dive_uses_same_file_memberships_and_preserves_missing_company_id(
    monkeypatch, catalog_release
):
    configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(DEEP).run()
    app.selectbox("market_leadership.screening.sector").select("test-sector").run()
    app.selectbox("market_leadership.screening.industry").select("test-cloud").run()
    assert not app.exception
    assert any("TEST_STOCK_1" in str(item.value) for item in app.dataframe)
    picker = app.multiselect("market_leadership.screening.stocks")
    assert picker.options == ["TEST_STOCK_1 · Test stock 1"]
    from market_leadership.infrastructure.catalog_files import CatalogReader
    from market_leadership.infrastructure.stock_membership import membership_entry

    snapshot = CatalogReader().read(catalog_release.parent / "CURRENT.json")
    scope = snapshot.scope_on("US", date(2026, 10, 30))
    entry = membership_entry(
        snapshot, snapshot.members(scope, "test-cloud", date(2026, 10, 30))[0], date(2026, 10, 30)
    )
    assert entry is not None and entry.company_id is None


def test_discovery_distinguishes_etf_basket_and_not_covered_and_batches_active_symbols(
    monkeypatch, catalog_release
):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(PAGE).run()
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert not app.exception
    assert not any(item.value == "Representation type" for item in app.caption)
    representation_help = [button.help for button in app.button if button.help]
    assert any(
        "Representation type: Stock basket alternative" in text for text in representation_help
    )
    assert any("Representation type: ETF" in text for text in representation_help)
    assert any(item.value == "Not covered" for item in app.markdown)
    assert set(calls[-1]) == {"TEST_ETF", "TEST_INVENTORY"}
    edit_csv(catalog_release, "industry_etfs", lambda rows: rows.clear())
    publish_entry(catalog_release)
    app.run()
    assert not app.exception
    assert any(item.value == "Not covered" for item in app.markdown)


def test_expired_unverified_and_nonprimary_listings_never_request_prices(
    monkeypatch, catalog_release
):
    def expire(rows):
        rows[0]["ListingEffectiveTo"] = "2025-01-01"
        rows[1]["ListingResolutionState"] = "unverified"

    edit_csv(catalog_release, "stocks", expire)
    calls = configure_ui(monkeypatch, catalog_release)
    app = _stocks(AppTest.from_file(PAGE).run())
    assert not app.exception
    assert all("TEST_STOCK_1" not in symbols for symbols in calls)
    assert not any(item.label == "Load peer scores" for item in app.button)


def test_reviewed_zero_member_industry_is_visible_without_fabricated_stocks(
    monkeypatch, catalog_release
):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(PAGE).run()
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert "test-empty" in app.selectbox(PREFIX + "industry").options
    calls.clear()
    app.selectbox(PREFIX + "industry").select("test-empty").run()
    assert not app.exception
    assert any("no active stock memberships" in item.value for item in app.info)
    assert calls == [("TEST_ETF",)]
    assert not any(item.label == "Load peer scores" for item in app.button)


@pytest.mark.parametrize("missing", [None, "quality", "growth", "cash_flow"])
def test_total_score_requires_complete_quality_growth_and_cash_flow(
    monkeypatch, catalog_release, missing
):
    from dataclasses import replace

    from market_leadership.domain.peer_scores import BlockPeerScore
    from tests.app.test_stock_detail import _score_result

    configure_ui(monkeypatch, catalog_release)
    cohorts = []

    def score(members, *, cutoff, refresh=False, cohort_fingerprint=None):
        cohorts.append(tuple(member.instrument_id for member in members))
        result = _score_result(members)
        evidence = result.stocks[0]
        card = replace(
            evidence.scorecard,
            quality=BlockPeerScore("Quality", 30, "available", ()),
            growth=BlockPeerScore("Growth", 60, "available", ()),
            cash_flow=BlockPeerScore("Cash Flow", 90, "available", ()),
        )
        if missing:
            card = replace(card, **{missing: BlockPeerScore(missing, None, "insufficient", ())})
        return replace(result, stocks=(replace(evidence, scorecard=card),))

    monkeypatch.setattr("market_leadership.application.score_industry.score_industry", score)
    app = _stocks(AppTest.from_file(PAGE).run())
    assert not cohorts
    next(button for button in app.button if button.label == "Load peer scores").click().run()
    assert not app.exception
    assert cohorts == [("test-stock-1",)]
    assert any(item.value == ("Insufficient" if missing else "60.0") for item in app.markdown)


def test_multiple_regions_default_to_us_and_clear_descendants_on_switch(
    monkeypatch, catalog_release
):
    import csv
    from copy import deepcopy
    from hashlib import sha256

    document = json.loads(catalog_release.read_text())
    canada = deepcopy(document["regions"][0])
    canada.update(region_id="CA", name="Test Canada")
    document["regions"].insert(0, canada)
    for artifact in tuple(document["artifacts"]):
        if artifact["role"] == "audit":
            continue
        source = catalog_release.parent / artifact["path"]
        with source.open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        assert fields
        target = catalog_release.parent / f"canada-{artifact['role']}.csv"
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
    catalog_release.write_text(json.dumps(document))
    app = _stocks(_run(monkeypatch, catalog_release))
    assert app.selectbox(PREFIX + "region").value == "US"
    app.selectbox(PREFIX + "region").select("CA").run()
    assert not app.exception
    assert PREFIX + "sector" not in app.session_state
    assert PREFIX + "industry" not in app.session_state
    assert PREFIX + "scores" not in app.session_state
    app.button(PREFIX + "sector_tape_select_ca-sector").click().run()
    assert not app.exception
    assert any("no active industries" in item.value for item in app.info)
    assert app.button(PREFIX + "breadcrumb_sectors").label == "CA sectors"
    app.button(PREFIX + "breadcrumb_sectors").click().run()
    assert not app.exception
    assert app.selectbox(PREFIX + "region").value == "CA"
    assert PREFIX + "sector" not in app.session_state


def test_reviewed_subindustry_remains_a_gap_row_with_exact_members(monkeypatch, catalog_release):
    app = _run(monkeypatch, catalog_release)
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert "test-specialist" in app.selectbox(PREFIX + "industry").options
    assert app.button(PREFIX + "industry_tape_select_test-specialist").label == "test-specialist"
    assert "Not covered" in app.button(PREFIX + "industry_tape_select_test-specialist").help
    app.selectbox(PREFIX + "industry").select("test-specialist").run()
    assert not app.exception
    assert any(item.label == "TEST_STOCK_1 · Test stock 1" for item in app.button)
    assert not any("Unresolved placeholder" in item.label for item in app.button)
    deep = AppTest.from_file(DEEP).run()
    deep.selectbox("market_leadership.screening.sector").select("test-sector").run()
    deep.selectbox("market_leadership.screening.industry").select("test-specialist").run()
    assert not deep.exception
    assert deep.multiselect("market_leadership.screening.stocks").options == [
        "TEST_STOCK_1 · Test stock 1"
    ]
