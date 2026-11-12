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


def _select_industry(app, prefix, node_id):
    selectbox = next(
        (widget for widget in app.selectbox if widget.key == prefix + "industry"),
        None,
    )
    if selectbox is None:
        return app.button(prefix + "industry_tape_select_" + node_id).click()
    option = next(value for value in selectbox.options if value.endswith(f"[{node_id}]"))
    return selectbox.select(option)


def _stocks(app):
    app.button(PREFIX + "sector_tape_select_test-sector").click().run(timeout=20)
    _select_industry(app, PREFIX, "test-cloud").run(timeout=20)
    return app


@pytest.mark.parametrize("industry", ["test-cloud", "test-specialist", "test-empty"])
def test_clickable_sector_and_industry_names_open_their_child_tapes(
    monkeypatch, catalog_release, industry
):
    app = _run(monkeypatch, catalog_release)
    app.segmented_control(PREFIX + "thumbnail_period").set_value("1w").run()
    app.segmented_control(PREFIX + "performance_basis").set_value("vs S&P 500").run()
    as_of = app.date_input[0].value
    sector_label = app.button(PREFIX + "sector_tape_select_test-sector").label
    assert sector_label.startswith("**") and "**  \n" in sector_label
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert not app.exception
    assert app.session_state[PREFIX + "sector"] == "test-sector"
    assert not any(widget.key == PREFIX + "sector" for widget in app.selectbox)
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value in {"Status", "Representation"} for item in app.caption)
    assert not any(item.value == "Representation type" for item in app.caption)
    button = app.button(PREFIX + "industry_tape_select_" + industry)
    assert button.help
    assert button.label.startswith("**") and "**  \n" in button.label
    assert not any(item.value == "ETF" for item in app.caption)
    button.click().run()
    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)
    if industry == "test-empty":
        assert any("no active stock memberships" in item.value for item in app.info)
    else:
        assert any(item.label == "**TEST\\_STOCK\\_1**  \nTest stock 1" for item in app.button)
        assert any(item.value == "Not loaded" for item in app.markdown)
    assert app.segmented_control(PREFIX + "thumbnail_period").value == "1w"
    assert not any(widget.label == "Performance basis" for widget in app.segmented_control)
    assert app.session_state[PREFIX + "performance_basis_state"] == "vs S&P 500"
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
    app = _run(monkeypatch, catalog_release)
    app.segmented_control(PREFIX + "thumbnail_period").set_value("1w").run()
    app.segmented_control(PREFIX + "performance_basis").set_value("vs S&P 500").run()
    app.button(PREFIX + "sector_tape_select_test-sector").click().run(timeout=20)
    _select_industry(app, PREFIX, "test-cloud").run(timeout=20)
    as_of = app.date_input[0].value
    if placeholder:
        next(
            button for button in app.button if "Unresolved placeholder" in button.label
        ).click().run()
    else:
        app.button(PREFIX + "stock_tape_select_test-stock-1").click().run()
    assert not app.exception
    assert app.button(PREFIX + "breadcrumb_sectors").label == "US sectors"
    assert any("Test stock" in item.value for item in app.caption)
    app.button(PREFIX + "breadcrumb_" + target).click().run()
    assert not app.exception
    assert any(item.value == heading for item in app.subheader)
    if sector is not None:
        assert app.session_state[PREFIX + "sector"] == sector
        assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)
        if industry is not None:
            assert app.session_state[PREFIX + "industry"] == industry
    else:
        assert PREFIX + "sector" not in app.session_state
        assert PREFIX + "industry" not in app.session_state
    assert not any(widget.key == PREFIX + "stock_picker" for widget in app.selectbox)
    assert PREFIX + "stock" not in app.session_state
    assert app.segmented_control(PREFIX + "thumbnail_period").value == "1w"
    if heading == "Contained stocks":
        assert not any(widget.label == "Performance basis" for widget in app.segmented_control)
        assert app.session_state[PREFIX + "performance_basis_state"] == "vs S&P 500"
    else:
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
    _select_industry(app, PREFIX, "test-empty").run()
    assert any("no active stock memberships" in item.value for item in app.info)
    app.button(PREFIX + "breadcrumb_sector").click().run()
    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert app.session_state[PREFIX + "sector"] == "test-sector"
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)


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
    assert not any(item.value == "Ticker" for item in app.caption)
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
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)
    _select_industry(app, PREFIX, "test-cloud").run(timeout=20)
    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)
    assert any(item.label == "**TEST\\_STOCK\\_1**  \nTest stock 1" for item in app.button)
    assert any("Unresolved placeholder" in item.label for item in app.button)
    assert any(item.value == "CAP Type" for item in app.caption)
    assert any(item.value == "Total Score" for item in app.caption)
    assert not any(item.value == "Name" for item in app.caption)
    assert not any(
        item.value in {"Quality", "Growth", "Cash Flow", "Score status", "Observed", "Chart status"}
        for item in app.caption
    )
    assert any(item.value == "Not loaded" for item in app.markdown)


def test_industry_selector_is_not_rendered_in_discovery(monkeypatch, catalog_release):
    app = _run(monkeypatch, catalog_release)
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()

    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)

    app.button(PREFIX + "industry_tape_select_test-cloud").click().run()
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)


def test_contained_stocks_keeps_breadcrumbs_without_selection_controls(
    monkeypatch, catalog_release
):
    app = _stocks(_run(monkeypatch, catalog_release))

    assert any(button.key == PREFIX + "breadcrumb_sector" for button in app.button)
    assert not any(
        widget.key in {PREFIX + "industry", PREFIX + "stock_picker"}
        for widget in app.selectbox
    )
    assert not any(widget.label == "Performance basis" for widget in app.segmented_control)
    assert any(widget.label == "Thumbnail period" for widget in app.segmented_control)
    assert not any(button.label == "Load peer scores" for button in app.button)
    assert any("cloud" in item.value.lower() for item in app.caption)
    assert not any("source" in item.value.lower() for item in app.caption)
    assert not any("not verified buyer or seller activity" in item.value for item in app.caption)
    style = next(
        element.proto.body
        for element in app.get("html")
        if ".st-key-contained_stocks_controls" in element.proto.body
    )
    assert "@media (max-width: 640px)" in style
    assert "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)" in style
    assert "grid-column: 2;" in style and "grid-row: 1;" in style


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
    assert not any(widget.label == "Performance basis" for widget in app.segmented_control)
    assert app.session_state[PREFIX + "performance_basis_state"] == "vs S&P 500"
    app.button(PREFIX + "breadcrumb_sector").click().run()
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
        "1 day",
        "1 week",
        "1 month",
        "3 months",
        "6 months",
        "1 year",
        "Status",
        "1d reason",
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
    windows = ["1 day", "1 week", "1 month", "3 months", "6 months", "1 year"]
    pd.testing.assert_frame_equal(short[windows], long[windows])
    assert len(short["Price chart"][0]) < len(long["Price chart"][0])


@pytest.mark.parametrize("ending, expected", [(102.0, 2.0), (99.0, -1.0), (100.0, 0.0)])
@pytest.mark.parametrize("reviewed", [False, True])
def test_sector_daily_return_is_independent_of_yearly_and_benchmark_history(
    ending, expected, reviewed
):
    from market_data.domain.industry_representations import ReviewedRepresentation
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    representation = ReviewedRepresentation(
        representation_id="reviewed-first",
        node_id="first",
        kind="etf",
        name="Full reviewed sector name",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
        symbol="FIRST",
    )
    frame = _build_entity_tape(
        entity_rows=(("first", "First"),),
        label="Sector",
        representation_by_id={"first": "FIRST"},
        reviewed_by_id={"first": representation} if reviewed else None,
        history={
            "FIRST": pd.DataFrame(
                {"close": [100.0, ending]},
                index=pd.to_datetime(["2026-10-29", "2026-10-30"]),
            )
        },
        benchmark=pd.Series(dtype="float64"),
        requested_as_of=date(2026, 10, 30),
        observed_as_of=date(2026, 10, 30),
        performance_mode="Absolute",
    )
    assert frame["1 day"][0] == pytest.approx(expected)
    assert pd.api.types.is_numeric_dtype(frame["1 day"])
    assert frame[["1 week", "1 month", "3 months", "6 months", "1 year"]].isna().all().all()
    assert frame["1d reason"][0] == ""


@pytest.mark.parametrize("kind, expected", [("etf", -1.0), ("basket", 0.5)])
def test_reviewed_industry_daily_return_uses_own_evidence(kind, expected):
    from decimal import Decimal

    from market_data.domain.industry_representations import (
        BasketConstituent,
        ReviewedRepresentation,
    )
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    representation = ReviewedRepresentation(
        representation_id="reviewed-industry",
        node_id="first",
        kind=kind,
        name="Full industry representation",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
        symbol="BBB" if kind == "etf" else None,
        constituents=(
            BasketConstituent("listing-aaa", "AAA", Decimal("50")),
            BasketConstituent("listing-bbb", "BBB", Decimal("50")),
        )
        if kind == "basket"
        else (),
    )
    history = {
        symbol: pd.DataFrame(
            {"close": closes, "volume": [1000, 1000]},
            index=pd.to_datetime(["2026-10-29", "2026-10-30"]),
        )
        for symbol, closes in {"AAA": [100, 102], "BBB": [200, 198], "PARENT": [100, 120]}.items()
    }
    arguments = dict(
        entity_rows=(("first", "First"), ("missing", "Not covered industry")),
        label="Industry",
        representation_by_id={"first": "BBB"} if kind == "etf" else {},
        reviewed_by_id={"first": representation},
        history=history,
        benchmark=pd.Series(dtype="float64"),
        requested_as_of=date(2026, 10, 30),
        observed_as_of=date(2026, 10, 30),
        performance_mode="Absolute",
    )
    frame = _build_entity_tape(**arguments)
    assert frame["1 day"][0] == pytest.approx(expected)
    assert frame["1 day"][0] != 20.0
    assert pd.isna(frame["1 day"][1])
    assert "approved representation" in frame["1d reason"][1]
    assert frame["Status"][1] == "Not covered"
    if kind == "basket":
        assert frame["Price chart"][0] == "Unavailable"
        assert frame["ETF"][0] == "Not an ETF"
    for preview_start in (date(2026, 10, 23), date(2026, 9, 30), date(2025, 10, 30)):
        cropped = _build_entity_tape(**arguments, preview_start=preview_start)
        pd.testing.assert_frame_equal(
            frame[["1 day", "1 week", "1 month", "3 months", "6 months", "1 year"]],
            cropped[["1 day", "1 week", "1 month", "3 months", "6 months", "1 year"]],
        )


def _stale_daily_arguments(label):
    from market_data.domain.industry_representations import ReviewedRepresentation

    index = pd.bdate_range(end="2026-10-30", periods=400)
    entity = pd.DataFrame({"close": [100.0] * 400, "volume": [1000] * 400}, index=index)
    entity.loc[pd.Timestamp("2026-10-30"), "close"] = 102.0
    entity.loc[pd.Timestamp("2026-11-02")] = [10000.0, 1000]
    benchmark = pd.Series([100.0] * 400, index=index)
    benchmark.loc[pd.Timestamp("2026-10-30")] = 100.5
    benchmark.loc[pd.Timestamp("2026-11-02")] = 10000.0
    representation = ReviewedRepresentation(
        representation_id="reviewed-first",
        node_id="first",
        kind="etf",
        name="Full reviewed representation",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
        symbol="FIRST",
    )
    return dict(
        entity_rows=(("first", "First"),),
        label=label,
        representation_by_id={"first": "FIRST"},
        reviewed_by_id={"first": representation},
        history={"FIRST": entity},
        benchmark=benchmark,
        requested_as_of=date(2026, 10, 30),
        observed_as_of=date(2026, 10, 28),
        performance_mode="Absolute",
    )


@pytest.mark.parametrize("label", ["Sector", "Industry"])
@pytest.mark.parametrize("mode, expected", [("Absolute", 2.0), ("vs S&P 500", 1.5)])
def test_daily_basis_uses_requested_sessions_while_preserving_legacy_crop(
    monkeypatch, label, mode, expected
):
    from unittest.mock import Mock

    from market_data.domain.industry_representations import representation_performance
    from market_data.domain.sector_performance import calculate_absolute_performance
    from market_leadership.ui.workflows import discovery_page

    arguments = _stale_daily_arguments(label)
    arguments["performance_mode"] = mode
    interval = Mock(wraps=discovery_page.daily_session_interval)
    benchmark_periods = Mock(wraps=discovery_page.calculate_performance_periods)
    monkeypatch.setattr(discovery_page, "daily_session_interval", interval)
    monkeypatch.setattr(discovery_page, "calculate_performance_periods", benchmark_periods)
    frame = discovery_page._build_entity_tape(**arguments)
    assert frame["1 day"][0] == pytest.approx(expected)
    assert frame["Status"][0] == "Stale"
    assert interval.call_count == 1
    assert benchmark_periods.call_count == (0 if mode == "Absolute" else 1)
    assert all(point["session"] <= "2026-10-28" for point in frame["Price chart"][0])
    legacy = representation_performance(
        arguments["reviewed_by_id"]["first"],
        arguments["history"],
        as_of=arguments["observed_as_of"],
    )
    benchmark_legacy = calculate_absolute_performance(
        arguments["benchmark"], as_of=arguments["observed_as_of"]
    )
    for heading, period in zip(
        ["1 week", "1 month", "3 months", "6 months", "1 year"],
        ["1w", "1m", "3m", "6m", "12m"],
        strict=True,
    ):
        expected_legacy = legacy[period].value - (
            benchmark_legacy[period] if mode != "Absolute" else 0
        )
        assert frame[heading][0] == expected_legacy * 100
    arguments["entity_rows"] = (("first", "First"), ("second", "Second"))
    arguments["representation_by_id"]["second"] = "FIRST"
    arguments["reviewed_by_id"]["second"] = arguments["reviewed_by_id"]["first"]
    interval.reset_mock()
    benchmark_periods.reset_mock()
    multiple = discovery_page._build_entity_tape(**arguments)
    assert multiple["1 day"].tolist() == pytest.approx([expected, expected])
    assert interval.call_count == 1
    assert benchmark_periods.call_count == (0 if mode == "Absolute" else 1)


@pytest.mark.parametrize("label", ["Sector", "Industry"])
@pytest.mark.parametrize("mode", ["Absolute", "vs S&P 500"])
@pytest.mark.parametrize("target", ["entity", "benchmark"])
def test_shared_representation_tape_retains_available_shorter_periods(label, mode, target):
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    arguments = _stale_daily_arguments(label)
    arguments["performance_mode"] = mode
    if target == "entity":
        arguments["history"]["FIRST"] = arguments["history"]["FIRST"].iloc[-30:]
    else:
        arguments["benchmark"] = arguments["benchmark"].iloc[-30:]
    frame = _build_entity_tape(**arguments)
    assert frame["1 day"][0] == pytest.approx(2.0 if mode == "Absolute" else 1.5)
    assert frame["1 week"][0] == 0
    assert frame["1 month"][0] == 0
    if target == "benchmark" and mode == "Absolute":
        assert frame["Status"][0] == "Stale"
        assert (frame[["3 months", "6 months", "1 year"]] == 0).all().all()
    else:
        assert frame[["3 months", "6 months", "1 year"]].isna().all().all()
        assert frame["Status"][0].startswith("Insufficient evidence:")
        assert "3m:" in frame["Status"][0]


@pytest.mark.parametrize("label", ["Sector", "Industry"])
@pytest.mark.parametrize("mode", ["Absolute", "vs S&P 500"])
@pytest.mark.parametrize("target", ["entity", "benchmark"])
@pytest.mark.parametrize("session", ["2026-10-29", "2026-10-30"])
def test_daily_missing_exact_endpoint_never_uses_older_valid_pair(label, mode, target, session):
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    arguments = _stale_daily_arguments(label)
    arguments["performance_mode"] = mode
    if target == "entity":
        arguments["history"]["FIRST"] = arguments["history"]["FIRST"].drop(pd.Timestamp(session))
    else:
        arguments["benchmark"] = arguments["benchmark"].drop(pd.Timestamp(session))
    frame = _build_entity_tape(**arguments)
    assert frame["Status"][0] == "Stale"
    assert (frame[["1 week", "1 month", "3 months", "6 months", "1 year"]] == 0).all().all()
    if target == "benchmark" and mode == "Absolute":
        assert frame["1 day"][0] == pytest.approx(2.0)
        assert frame["1d reason"][0] == ""
    else:
        assert pd.isna(frame["1 day"][0])
        assert session in frame["1d reason"][0]
        assert ("FIRST" if target == "entity" else "S&P 500 benchmark") in frame["1d reason"][0]


@pytest.mark.parametrize("label", ["Sector", "Industry"])
@pytest.mark.parametrize("target", ["entity", "benchmark"])
@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf"), 0.0, -1.0])
def test_daily_invalid_endpoint_is_unavailable_without_losing_longer_returns(
    label, target, invalid
):
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    arguments = _stale_daily_arguments(label)
    arguments["performance_mode"] = "vs S&P 500"
    if target == "entity":
        arguments["history"]["FIRST"].loc[pd.Timestamp("2026-10-30"), "close"] = invalid
    else:
        arguments["benchmark"].loc[pd.Timestamp("2026-10-30")] = invalid
    frame = _build_entity_tape(**arguments)
    assert pd.isna(frame["1 day"][0])
    assert "Invalid close" in frame["1d reason"][0]
    assert "2026-10-30" in frame["1d reason"][0]
    assert frame["Status"][0] == "Stale"
    assert frame["1 week"][0] == 0.0


@pytest.mark.parametrize("label", ["Sector", "Industry"])
def test_daily_representation_is_validated_at_requested_not_observed_date(label):
    from dataclasses import replace

    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    arguments = _stale_daily_arguments(label)
    representation = arguments["reviewed_by_id"]["first"]
    arguments["reviewed_by_id"]["first"] = replace(representation, effective_to=date(2026, 10, 29))
    frame = _build_entity_tape(**arguments)
    assert pd.isna(frame["1 day"][0])
    assert "effective period" in frame["1d reason"][0]
    assert frame["1 week"][0] == 0.0
    assert frame["Status"][0] == "Stale"


def test_stock_views_do_not_request_hidden_industry_proxy(monkeypatch, catalog_release):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(PAGE).run(timeout=20)
    app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert set(calls[-1]) == {"TEST_ETF", "TEST_INVENTORY"}
    calls.clear()
    _select_industry(app, PREFIX, "test-cloud").run()
    assert not app.exception
    assert ("TEST_STOCK_1",) in calls
    assert all("TEST_INVENTORY" not in symbols for symbols in calls)
    calls.clear()
    app.button(PREFIX + "stock_tape_select_test-stock-1").click().run()
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
    assert not any(item.label == "**TEST\\_STOCK\\_1**  \nTest stock 1" for item in app.button)


def test_industry_deep_dive_uses_same_file_memberships_and_preserves_missing_company_id(
    monkeypatch, catalog_release
):
    configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(DEEP).run()
    app.selectbox("market_leadership.screening.sector").select("test-sector").run()
    _select_industry(app, "market_leadership.screening.", "test-cloud").run()
    assert not app.exception
    frame = app.dataframe[0].value
    member = frame.loc[frame["Instrument ID"] == "test-stock-1"].iloc[0]
    assert member["Membership"] == "Inherited"
    assert "test-specialist" in member["Direct membership paths"]
    picker = app.multiselect("market_leadership.screening.stocks")
    assert picker.options == ["TEST_STOCK_1 · Test stock 1"]
    from market_data.catalog import CatalogReader
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
    assert any("Not covered" in text for text in representation_help)
    assert any(button.label.startswith("**No ticker**  \n") for button in app.button)
    assert set(calls[-1]) == {"TEST_ETF", "TEST_INVENTORY"}
    edit_csv(catalog_release, "industry_etfs", lambda rows: rows.clear())
    publish_entry(catalog_release)
    app.run()
    assert not app.exception
    assert any(button.help and "Not covered" in button.help for button in app.button)
    assert any(button.label.startswith("**No ticker**  \n") for button in app.button)


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
    assert any(
        button.key == PREFIX + "industry_tape_select_test-empty" for button in app.button
    )
    calls.clear()
    _select_industry(app, PREFIX, "test-empty").run()
    assert not app.exception
    assert any("no active stock memberships" in item.value for item in app.info)
    assert calls == [("TEST_ETF",)]
    assert not any(item.label == "Load peer scores" for item in app.button)


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
    assert not any(widget.key == PREFIX + "industry" for widget in app.selectbox)
    specialist_label = app.button(PREFIX + "industry_tape_select_test-specialist").label
    assert specialist_label.startswith("**No ticker**  \n")
    assert specialist_label.endswith(r"\[test\-specialist\]")
    assert r"test\-cloud" in specialist_label
    assert "Not covered" in app.button(PREFIX + "industry_tape_select_test-specialist").help
    _select_industry(app, PREFIX, "test-specialist").run()
    assert not app.exception
    assert any(item.label == "**TEST\\_STOCK\\_1**  \nTest stock 1" for item in app.button)
    assert not any("Unresolved placeholder" in item.label for item in app.button)
    deep = AppTest.from_file(DEEP).run()
    deep.selectbox("market_leadership.screening.sector").select("test-sector").run()
    _select_industry(deep, "market_leadership.screening.", "test-specialist").run()
    assert not deep.exception
    assert deep.multiselect("market_leadership.screening.stocks").options == [
        "TEST_STOCK_1 · Test stock 1"
    ]
