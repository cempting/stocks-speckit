from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from market_data.domain.peer_scores import (
    BlockPeerScore,
    MetricPeerScore,
    PeerScorecard,
)
from market_leadership.ui.components.progressive_tape import (
    StockTapeRow,
    attach_chart_series,
    build_price_thumbnail,
    build_stock_tape_frame,
    build_volume_thumbnail,
)


def _history(closes: tuple[float, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        {"close": closes, "volume": [100.0] * len(closes)},
        index=pd.date_range("2026-10-19", periods=len(closes), freq="D"),
    )


@pytest.mark.parametrize("entity_column", ["Sector", "Industry"])
def test_entity_name_buttons_select_stable_ids_even_when_names_match(entity_column: str) -> None:
    def app_script(entity_column: str) -> None:
        import pandas as pd
        import streamlit as st

        from market_leadership.ui.components.progressive_tape import render_chart_tape

        def select(node_id: str) -> None:
            st.session_state["selected_node"] = node_id

        frame = pd.DataFrame(
            {
                "Price chart": ["Unavailable", "Unavailable"],
                "Volume chart": ["Unavailable", "Unavailable"],
                entity_column: ["Same name", "Same name"],
                "Node ID": ["first", "second"],
                "Status": ["Not covered", "Invalid evidence: expired mapping"],
                "Representation": ["Not covered", "Reviewed basket"],
            }
        )
        if entity_column == "Industry":
            frame["Representation type"] = ["Not covered", "Stock basket alternative"]
        render_chart_tape(frame, key="entities", on_select=select)
        st.write(f"Selected: {st.session_state.get('selected_node')}")

    app = AppTest.from_function(app_script, args=(entity_column,)).run()
    assert not app.exception
    assert [item.label for item in app.button] == ["Same name", "Same name"]
    assert not any(item.value == "Node ID" for item in app.caption)
    assert not any(item.value == "Status" for item in app.caption)
    if entity_column == "Industry":
        assert not any(
            item.value in {"Status", "Representation", "Representation type"}
            for item in app.caption
        )
        assert (
            "Representation type: Stock basket alternative"
            in app.button("entities_select_second").help
        )
    assert "Invalid evidence: expired mapping" in app.button("entities_select_second").help
    app.button("entities_select_second").click().run()
    assert not app.exception
    assert any(item.value == "Selected: second" for item in app.markdown)


def test_stock_list_shows_name_only_in_ticker_button_and_preserves_selection() -> None:
    def app_script() -> None:
        import pandas as pd
        import streamlit as st

        from market_leadership.ui.components.progressive_tape import (
            StockTapeRow,
            build_stock_tape_frame,
            render_selectable_stock_tape,
        )

        rows = (
            StockTapeRow(
                instrument_id="stock-a",
                ticker="AAA",
                name="Alpha",
                history=pd.DataFrame(),
                price_state="unavailable",
            ),
            StockTapeRow(
                instrument_id="placeholder",
                ticker="",
                name="Unresolved company",
                history=pd.DataFrame(),
                price_state="unavailable",
                resolution_state="placeholder",
            ),
        )
        selected = render_selectable_stock_tape(build_stock_tape_frame(rows), key="stock-list")
        st.write(f"Selected rows: {selected}")

    app = AppTest.from_function(app_script).run()
    assert not app.exception
    headings = {
        "Price + 50 MA",
        "Volume by price direction",
        "Ticker",
        "Name",
        "CAP Type",
        "Total Score",
    }
    assert [item.value for item in app.caption if item.value in headings] == [
        "Price + 50 MA",
        "Volume by price direction",
        "Ticker",
        "CAP Type",
        "Total Score",
    ]
    assert [item.label for item in app.button] == [
        "AAA · Alpha",
        "Unresolved placeholder · Unresolved company",
    ]
    assert not any(item.value in {"Alpha", "Unresolved company"} for item in app.markdown)
    app.button[0].click().run()
    assert not app.exception
    assert any(item.value == "Selected rows: (0,)" for item in app.markdown)


@pytest.mark.parametrize("sma50", [None, 10.5])
def test_chart_thumbnails_have_double_height_without_changing_width(
    sma50: float | None,
) -> None:
    price = build_price_thumbnail([{"session": "2026-10-19", "close": 11.0, "sma50": sma50}])
    volume = build_volume_thumbnail([{"session": "2026-10-19", "volume": 100.0, "direction": "up"}])

    for chart in (price, volume):
        assert chart is not None
        specification = chart.to_dict()
        assert specification["height"] == 84
        assert specification["width"] == 135


@pytest.mark.parametrize("dark_mode", [False, True])
@pytest.mark.parametrize("sma50", [None, 10.5])
def test_thumbnail_colors_follow_dark_mode(dark_mode: bool, sma50: float | None) -> None:
    price = build_price_thumbnail(
        [{"session": "2026-10-19", "close": 11.0, "sma50": sma50}], dark_mode=dark_mode
    )
    volume = build_volume_thumbnail(
        [{"session": "2026-10-19", "volume": 100.0, "direction": "up"}], dark_mode=dark_mode
    )
    assert price is not None and volume is not None
    price_spec = price.to_dict()
    assert price_spec["background"] == ("#111820" if dark_mode else "#f7f8f6")
    assert volume.to_dict()["background"] == price_spec["background"]
    mark = price_spec["mark"] if sma50 is None else price_spec["layer"][0]["mark"]
    assert mark["color"] == ("#7dd3fc" if dark_mode else "#17324d")


def _scorecard(instrument_id: str) -> PeerScorecard:
    metric = MetricPeerScore("metric", 1.0, 62.5, 5, "available")
    quality = BlockPeerScore("Quality", 62.5, "available", (metric, metric))
    growth = BlockPeerScore("Growth", None, "insufficient", (metric, metric))
    cash_flow = BlockPeerScore("Cash Flow", None, "insufficient", (metric, metric))
    return PeerScorecard(instrument_id, quality, growth, cash_flow)


def _available_scorecard(instrument_id: str) -> PeerScorecard:
    metric = MetricPeerScore("metric", 1.0, 62.5, 5, "available")
    quality = BlockPeerScore("Quality", 60.0, "available", (metric, metric))
    growth = BlockPeerScore("Growth", 75.0, "available", (metric, metric))
    cash_flow = BlockPeerScore("Cash Flow", 90.0, "available", (metric, metric))
    return PeerScorecard(instrument_id, quality, growth, cash_flow)


def test_chart_previews_are_joined_by_each_rows_own_identity():
    rows = pd.DataFrame({"ID": ["sector-a", "sector-b"]})

    result = attach_chart_series(
        rows,
        identity_column="ID",
        history_by_id={
            "sector-a": _history((1, 2, 3)),
            "sector-b": _history((10, 20, 30)),
        },
    )

    assert [[point["close"] for point in row] for row in result["Price chart"]] == [
        [1, 2, 3],
        [10, 20, 30],
    ]
    assert result["Volume chart"].map(lambda row: isinstance(row, list)).all()
    industries = attach_chart_series(
        pd.DataFrame({"Representation": ["AERO", "CLOUD"]}),
        identity_column="Representation",
        history_by_id={
            "AERO": _history((3, 2, 1)),
            "CLOUD": _history((30, 20, 10)),
        },
    )
    assert [[point["close"] for point in row] for row in industries["Price chart"]] == [
        [3, 2, 1],
        [30, 20, 10],
    ]


@pytest.mark.parametrize(
    "offset",
    [
        pd.DateOffset(weeks=1),
        pd.DateOffset(months=1),
        pd.DateOffset(months=3),
        pd.DateOffset(months=6),
        pd.DateOffset(years=1),
    ],
)
def test_thumbnail_period_filters_both_series_without_losing_sma_warmup(
    offset: pd.DateOffset,
) -> None:
    sessions = pd.bdate_range(end="2026-10-30", periods=400)
    history = pd.DataFrame({"close": range(1, 401), "volume": range(1000, 1400)}, index=sessions)
    start = (sessions[-1] - offset).date()
    expected = history.loc[sessions.date >= start]
    entity_frame = attach_chart_series(
        pd.DataFrame({"ID": ["sector-a"]}),
        identity_column="ID",
        history_by_id={"sector-a": history},
        preview_start=start,
    )
    stock_frame = build_stock_tape_frame(
        (
            StockTapeRow(
                instrument_id="stock-a",
                ticker="AAA",
                name="Alpha",
                history=history,
                price_state="available",
            ),
        ),
        preview_start=start,
    )

    for frame in (entity_frame, stock_frame):
        price = frame["Price chart"].iloc[0]
        volume = frame["Volume chart"].iloc[0]
        expected_sessions = [session.date().isoformat() for session in expected.index]
        assert [point["session"] for point in price] == expected_sessions
        assert [point["session"] for point in volume] == expected_sessions
        assert price[0]["sma50"] == (history["close"].rolling(50).mean().loc[expected.index[0]])
        assert volume[0]["direction"] == "up"
    assert stock_frame.columns.tolist()[:6] == [
        "Price chart",
        "Volume chart",
        "Ticker",
        "Name",
        "CAP Type",
        "Total Score",
    ]


def test_thumbnail_window_without_observations_is_unavailable():
    frame = attach_chart_series(
        pd.DataFrame({"ID": ["stale"]}),
        identity_column="ID",
        history_by_id={"stale": _history((1, 2, 3))},
        preview_start=date(2026, 10, 30),
    )

    assert frame["Price chart"].iloc[0] == "Unavailable"
    assert frame["Volume chart"].iloc[0] == "Unavailable"


@pytest.mark.parametrize("count,expected", [(10, True), (80, False)])
def test_price_cell_discloses_insufficient_sma_without_changing_plot_height(
    count: int, expected: bool
) -> None:
    def app_script(count: int) -> None:
        from datetime import date

        import pandas as pd

        from market_leadership.ui.components.progressive_tape import (
            attach_chart_series,
            render_chart_tape,
        )

        history = pd.DataFrame(
            {"close": range(1, count + 1), "volume": [100.0] * count},
            index=pd.bdate_range(end="2026-10-30", periods=count),
        )
        frame = attach_chart_series(
            pd.DataFrame({"Sector": ["Short"]}),
            identity_column="Sector",
            history_by_id={"Short": history},
            preview_start=date(2026, 10, 23),
        )
        render_chart_tape(frame, key="sma-disclosure")

    app = AppTest.from_function(app_script, args=(count,)).run()
    assert not app.exception
    assert any("50 MA: Insufficient" == item.value for item in app.caption) == expected


def test_stock_tape_contains_identity_cap_type_and_total_score_states():
    frame = build_stock_tape_frame(
        (
            StockTapeRow(
                instrument_id="instrument-a",
                ticker="AAA",
                name="Alpha",
                history=_history((10, 12)),
                price_state="available",
                observed_on=date(2026, 10, 20),
                scorecard=_available_scorecard("instrument-a"),
                score_state="available",
                market_cap=10_000_000_000,
            ),
            StockTapeRow(
                instrument_id="instrument-b",
                ticker="BBB",
                name="Beta",
                history=_history((8, 10)),
                price_state="available",
                scorecard=_scorecard("instrument-b"),
                score_state="available",
                market_cap=2_000_000_000,
            ),
            StockTapeRow(
                instrument_id="instrument-c",
                ticker="CCC",
                name="Gamma",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="unavailable",
                score_state="not_loaded",
            ),
            StockTapeRow(
                instrument_id="instrument-d",
                ticker="DDD",
                name="Delta",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="unavailable",
                score_state="error",
            ),
            StockTapeRow(
                instrument_id="instrument-placeholder",
                ticker="Unresolved placeholder",
                name="Unresolved",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="placeholder",
                score_state="placeholder",
                resolution_state="placeholder",
            ),
        )
    )

    assert [[point["close"] for point in row] for row in frame["Price chart"].iloc[:1]] == [
        [10, 12]
    ]
    assert frame.columns.tolist() == [
        "Price chart",
        "Volume chart",
        "Ticker",
        "Name",
        "CAP Type",
        "Total Score",
        "Instrument ID",
        "Resolution",
    ]
    assert [frame[column].iloc[0] for column in ("Ticker", "Name", "CAP Type")] == [
        "AAA",
        "Alpha",
        "Large",
    ]
    assert frame["CAP Type"].tolist() == [
        "Large",
        "Mid",
        "Unavailable",
        "Unavailable",
        "Unavailable",
    ]
    assert frame["Total Score"].tolist() == [
        "75.0",
        "Insufficient",
        "Not loaded",
        "Error",
        "Unavailable",
    ]


@pytest.mark.parametrize(
    ("market_cap", "expected"),
    [
        (10_000_000_000, "Large"),
        (2_000_000_000, "Mid"),
        (1, "Small"),
        (None, "Unavailable"),
        (0, "Unavailable"),
        (float("nan"), "Unavailable"),
    ],
)
def test_stock_tape_classifies_current_capitalization(
    market_cap: float | None, expected: str
) -> None:
    frame = build_stock_tape_frame(
        (
            StockTapeRow(
                instrument_id="instrument-a",
                ticker="AAA",
                name="Alpha",
                history=_history((10, 12)),
                price_state="available",
                score_state="available",
                market_cap=market_cap,
            ),
        )
    )

    assert frame["CAP Type"].tolist() == [expected]


def test_price_and_volume_chart_columns_are_adjacent_and_keep_direction_states():
    history = pd.DataFrame(
        {"close": [10.0, 12.0, 12.0, 9.0], "volume": [100.0, 120.0, 140.0, 90.0]},
        index=pd.date_range("2026-10-19", periods=4, freq="D"),
    )

    frame = build_stock_tape_frame(
        (
            StockTapeRow(
                instrument_id="instrument-a",
                ticker="AAA",
                name="Alpha",
                history=history,
                price_state="available",
            ),
            StockTapeRow(
                instrument_id="instrument-b",
                ticker="BBB",
                name="Beta",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="unavailable",
            ),
        )
    )

    columns = frame.columns.tolist()
    assert columns.index("Volume chart") == columns.index("Price chart") + 1
    assert frame["Price chart"].iloc[0][-1]["close"] == 9.0
    assert [point["direction"] for point in frame["Volume chart"].iloc[0]] == [
        "neutral",
        "up",
        "neutral",
        "down",
    ]
    assert frame["Price chart"].iloc[1] == "Unavailable"
    assert frame["Volume chart"].iloc[1] == "Unavailable"
    assert "price direction" in frame.attrs["volume_legend"].lower()


def test_stock_tape_keeps_chart_evidence_without_metadata_columns():
    frame = build_stock_tape_frame(
        (
            StockTapeRow(
                instrument_id="instrument-a",
                ticker="AAA",
                name="Alpha",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="unavailable",
                score_state="not_loaded",
            ),
            StockTapeRow(
                instrument_id="instrument-placeholder",
                ticker="Unresolved placeholder",
                name="Unresolved",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="placeholder",
                score_state="placeholder",
                resolution_state="placeholder",
            ),
        )
    )

    assert "Observed" not in frame.columns
    assert "Chart status" not in frame.columns
    assert frame["Price chart"].tolist() == ["Unavailable", "Unavailable"]
    assert frame["Volume chart"].tolist() == ["Unavailable", "Unavailable"]
    assert frame["Ticker"].tolist() == ["AAA", "Unresolved placeholder"]


def test_missing_price_and_volume_series_are_reported_independently():
    history = pd.DataFrame(
        {"close": [10.0, 11.0], "volume": [float("nan"), float("nan")]},
        index=pd.date_range("2026-10-19", periods=2, freq="D"),
    )
    frame = attach_chart_series(
        pd.DataFrame({"ID": ["instrument-a"]}),
        identity_column="ID",
        history_by_id={"instrument-a": history},
    )

    assert isinstance(frame["Price chart"].iloc[0], list)
    assert frame["Volume chart"].iloc[0] == "Unavailable"

    history["close"] = float("nan")
    history["volume"] = [100.0, 110.0]
    frame = attach_chart_series(
        pd.DataFrame({"ID": ["instrument-a"]}),
        identity_column="ID",
        history_by_id={"instrument-a": history},
    )

    assert frame["Price chart"].iloc[0] == "Unavailable"
    assert isinstance(frame["Volume chart"].iloc[0], list)


@pytest.mark.parametrize(
    ("dark_mode", "gain", "loss", "neutral", "foreground"),
    [
        (False, "#5f9f75", "#d66d65", "#f4f6f5", "#17212b"),
        (True, "#166534", "#991b1b", "#18232d", "#edf3f7"),
    ],
)
def test_visual_tape_preserves_performance_colors_and_formats_missing_values(
    dark_mode: bool, gain: str, loss: str, neutral: str, foreground: str
) -> None:
    def render(dark_mode: bool) -> None:
        import pandas as pd
        import streamlit as st

        from market_leadership.ui.components.progressive_tape import render_chart_tape
        from market_leadership.ui.performance_table import PERFORMANCE_COLUMNS

        st.session_state["dark_mode"] = dark_mode
        frame = pd.DataFrame(
            {
                "Price chart": ["Unavailable"] * 4,
                "Volume chart": ["Unavailable"] * 4,
                "Sector": ["Gaining", "Declining", "Flat", "Missing"],
                **{column: [8.0, -4.0, 0.0, None] for column in PERFORMANCE_COLUMNS},
            }
        )
        render_chart_tape(frame, key="test-sector")

    app = AppTest.from_function(render, args=(dark_mode,)).run()

    assert not app.exception
    cells = [element.proto.body for element in app.get("html")]
    assert len(cells) == 20
    for row_index, (color, text) in enumerate(
        [(gain, "8.00%"), (loss, "-4.00%"), (neutral, "0.00%")]
    ):
        for cell in cells[row_index * 5 : (row_index + 1) * 5]:
            assert f"background-color: {color}" in cell
            assert f"color: {foreground}" in cell
            assert text in cell
    for cell in cells[15:]:
        assert "Unavailable" in cell
        assert "background-color" not in cell
    assert sum(item.value == "Price unavailable" for item in app.caption) == 4
    assert sum(item.value == "Volume unavailable" for item in app.caption) == 4
