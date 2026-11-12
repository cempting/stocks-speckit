from datetime import date, timedelta

import pandas as pd

from market_data.domain.consolidation import ConsolidationInterval, VolumeContext
from market_leadership.ui.sector_chart import build_sector_chart


def _interval(start: date, end: date) -> ConsolidationInterval:
    return ConsolidationInterval(
        interval_id="interval-a",
        instrument_id="instrument-a",
        detector_version="quiet-sideways-v1",
        start_session=start,
        end_session=end,
        duration_sessions=5,
        approx_calendar_duration=(end - start).days + 1,
        lower=95.0,
        upper=105.0,
        width_absolute=10.0,
        width_pct=100 * (105 / 95 - 1),
        median_atr14=2.0,
        volume_context=VolumeContext(20, 2.0, 1000.0, 900.0, 0),
        as_of=end,
        observable_history_start=start,
        start_boundary_truncated=False,
        ongoing=True,
        current_or_previous_session=True,
    )


def test_sector_chart_uses_dark_mode_palette() -> None:
    index = pd.date_range("2026-01-01", periods=60, freq="B")
    frame = pd.DataFrame(
        {
            "close": range(100, 160),
            "sma50": range(95, 155),
            "volume": range(1_000_000, 1_000_060),
        },
        index=index,
    )

    specification = build_sector_chart(frame, dark_mode=True).to_dict()

    assert specification["background"] == "#111820"
    assert specification["vconcat"][0]["encoding"]["color"]["scale"]["range"] == [
        "#7dd3fc",
        "#f4b860",
    ]
    assert specification["config"]["axis"]["labelColor"] == "#aebbc8"


def test_sector_chart_colors_volume_by_close_direction() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="B")
    frame = pd.DataFrame(
        {
            "close": [100, 105, 101, 101],
            "sma50": [100, 101, 102, 103],
            "volume": [1_000_000, 1_100_000, 900_000, 800_000],
        },
        index=index,
    )

    specification = build_sector_chart(frame).to_dict()
    volume_specification = specification["vconcat"][1]

    assert volume_specification["encoding"]["color"]["field"] == "volume_signal"
    assert volume_specification["encoding"]["color"]["scale"] == {
        "domain": ["Buy", "Sell", "Neutral"],
        "range": ["#16a34a", "#dc2626", "#6f8f7b"],
    }
    assert volume_specification["encoding"]["tooltip"][2]["field"] == "volume_signal"
    volume_data_name = volume_specification["data"]["name"]
    assert [row["volume_signal"] for row in specification["datasets"][volume_data_name]] == [
        "Neutral",
        "Buy",
        "Sell",
        "Neutral",
    ]


def test_stock_detail_chart_includes_both_moving_average_series() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="B")
    frame = pd.DataFrame(
        {
            "close": [100, 105, 101, 101],
            "sma50": [99, 100, 101, 102],
            "sma150": [95, 96, 97, 98],
            "volume": [1_000_000, 1_100_000, 900_000, 800_000],
        },
        index=index,
    )

    specification = build_sector_chart(frame).to_dict()
    price_data = specification["datasets"][specification["vconcat"][0]["data"]["name"]]

    assert {row["series"] for row in price_data} == {"close", "sma50", "sma150"}


def test_stock_detail_can_render_more_than_thumbnail_history_limit() -> None:
    index = pd.date_range("2025-01-01", periods=300, freq="B")
    frame = pd.DataFrame(
        {
            "close": range(100, 400),
            "sma50": range(95, 395),
            "sma150": range(50, 350),
            "volume": range(1_000_000, 1_000_300),
        },
        index=index,
    )

    limited = build_sector_chart(frame).to_dict()
    full = build_sector_chart(frame, max_rows=None).to_dict()

    limited_volume = limited["datasets"][limited["vconcat"][1]["data"]["name"]]
    full_volume = full["datasets"][full["vconcat"][1]["data"]["name"]]
    assert len(limited_volume) == 260
    assert len(full_volume) == 300


def test_stock_detail_chart_shades_interval_and_draws_observed_corridor_bounds() -> None:
    index = pd.date_range("2026-10-20", periods=5, freq="B")
    frame = pd.DataFrame(
        {
            "close": [100, 101, 102, 101, 103],
            "sma50": [99, 99.5, 100, 100.5, 101],
            "sma150": [95, 95, 95, 95, 95],
            "volume": [1_000, 1_100, 900, 1_200, 1_000],
        },
        index=index,
    )
    interval = _interval(index[0].date() - timedelta(days=5), index[-1].date())

    specification = build_sector_chart(
        frame,
        max_rows=None,
        consolidation_interval=interval,
    ).to_dict()

    price = specification["vconcat"][0]
    rectangle = next(layer for layer in price["layer"] if layer["mark"]["type"] == "rect")
    rectangle_data = specification["datasets"][rectangle["data"]["name"]][0]
    assert rectangle_data["lower"] == 95.0
    assert rectangle_data["upper"] == 105.0
    assert rectangle_data["plot_start"] == pd.Timestamp(index[0]).isoformat()
    assert rectangle_data["plot_end"] == pd.Timestamp(index[-1]).isoformat()
    assert any(layer["mark"]["type"] == "rule" for layer in price["layer"])
