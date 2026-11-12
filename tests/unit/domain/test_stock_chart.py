from datetime import date

import pandas as pd
import pytest

from market_data.domain.consolidation import CONSOLIDATION_HISTORY_WARMUP_SESSIONS
from market_data.domain.stock_chart import (
    build_discovery_chart_preview,
    build_stock_chart_evidence,
    stock_chart_lookback_days,
    stock_chart_visible_start,
)


def _history(count: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "close": [float(value) for value in range(1, count + 1)],
            "volume": [1000.0] * count,
        },
        index=pd.bdate_range("2026-01-01", periods=count),
    )


def test_price_volume_and_exact_50_and_150_session_averages():
    history = _history(160)

    chart = build_stock_chart_evidence(
        "instrument-a",
        history,
        as_of=history.index[-1].date(),
    )

    assert chart.price_state == "available"
    assert chart.volume_state == "available"
    assert chart.sma50_state == "available"
    assert chart.sma150_state == "available"
    assert chart.history["sma50"].iloc[-1] == sum(range(111, 161)) / 50
    assert chart.history["sma150"].iloc[-1] == sum(range(11, 161)) / 150


def test_moving_average_insufficiency_is_per_series_and_future_rows_are_excluded():
    history = _history(149)
    future = pd.DataFrame(
        {"close": [1000.0], "volume": [1000.0]},
        index=pd.DatetimeIndex(["2027-01-01"]),
    )
    combined = pd.concat([history, future])
    chart = build_stock_chart_evidence(
        "instrument-a",
        combined,
        as_of=history.index[-1].date(),
    )

    assert chart.price_state == "available"
    assert chart.volume_state == "available"
    assert chart.sma50_state == "available"
    assert chart.sma150_state == "insufficient"
    assert len(chart.history) == 149
    assert pd.isna(chart.history["sma150"].iloc[-1])


@pytest.mark.parametrize("visible_range", ["1m", "3m", "6m", "12m", "18m", "24m"])
def test_visible_range_uses_only_completed_sessions_in_selected_month_window(
    visible_range: str,
) -> None:
    history = _history(800)
    as_of = history.index[-1].date()
    months = int(visible_range[:-1])
    visible_start = (pd.Timestamp(as_of) - pd.DateOffset(months=months)).date()

    chart = build_stock_chart_evidence(
        "instrument-a",
        history,
        as_of=as_of,
        visible_range=visible_range,
    )

    assert chart.history.index[0].date() >= visible_start
    assert chart.history.index[-1].date() == as_of
    assert len(chart.history) == sum(
        visible_start <= session.date() <= as_of for session in history.index
    )


def test_visible_range_uses_prior_sessions_for_moving_average_warmup() -> None:
    history = _history(300)
    as_of = history.index[-1].date()
    visible_start = (pd.Timestamp(as_of) - pd.DateOffset(months=1)).date()

    chart = build_stock_chart_evidence(
        "instrument-a",
        history,
        as_of=as_of,
        visible_range="1m",
    )

    first_visible = chart.history.iloc[0]
    start_position = history.index.searchsorted(pd.Timestamp(visible_start))
    assert chart.history.index[0].date() >= visible_start
    assert pd.notna(first_visible["sma50"])
    assert pd.notna(first_visible["sma150"])
    assert first_visible["sma50"] == history["close"].iloc[
        start_position - 49 : start_position + 1
    ].mean()
    assert first_visible["sma150"] == history["close"].iloc[
        start_position - 149 : start_position + 1
    ].mean()


def test_history_request_covers_visible_range_and_moving_average_warmup() -> None:
    as_of = date(2026, 10, 23)
    visible_start = stock_chart_visible_start(as_of, "24m")
    lookback_days = stock_chart_lookback_days(as_of, "24m")

    assert visible_start == date(2024, 10, 23)
    assert lookback_days > (
        (as_of - visible_start).days + CONSOLIDATION_HISTORY_WARMUP_SESSIONS
    )


def test_stock_chart_preserves_adjusted_ohlc_source_and_consolidation_evidence() -> None:
    history = _history(300)
    history["open"] = history["close"]
    history["high"] = history["close"] * 1.01
    history["low"] = history["close"] * 0.99
    history["split_ratio"] = 0.0
    history.attrs.update(
        {
            "source_id": "fixture",
            "adjusted_ohlc": True,
            "volume_comparable": True,
        }
    )

    chart = build_stock_chart_evidence(
        "instrument-a",
        history,
        as_of=history.index[-1].date(),
    )

    assert chart.consolidation.source_id == "fixture"
    assert chart.consolidation.as_of == history.index[-1].date()
    assert {"open", "high", "low", "split_ratio"}.issubset(chart.history.columns)
    assert chart.history.attrs["adjusted_ohlc"] is True
    assert chart.history.attrs["volume_comparable"] is True


def test_stock_chart_does_not_infer_ohlc_for_consolidation() -> None:
    history = _history(300)

    chart = build_stock_chart_evidence(
        "instrument-a",
        history,
        as_of=history.index[-1].date(),
    )

    assert "missing_adjusted_ohlc" in chart.consolidation.reason_codes


def test_gap_in_close_history_does_not_bridge_moving_average_window() -> None:
    history = _history(200)
    history.iloc[-10, history.columns.get_loc("close")] = float("nan")

    chart = build_stock_chart_evidence(
        "instrument-a",
        history,
        as_of=history.index[-1].date(),
    )

    assert chart.price_state == "insufficient"
    assert chart.sma50_state == "insufficient"
    assert pd.isna(chart.history["sma50"].iloc[-1])


def test_empty_history_marks_all_series_without_fabricated_values():
    chart = build_stock_chart_evidence(
        "instrument-a",
        pd.DataFrame(columns=["close", "volume"]),
        as_of=date(2026, 10, 23),
    )

    assert (chart.price_state, chart.volume_state) == ("unavailable", "unavailable")
    assert (chart.sma50_state, chart.sma150_state) == ("insufficient", "insufficient")


def test_discovery_preview_uses_same_completed_sessions_for_price_volume_and_direction():
    history = pd.DataFrame(
        {
            "close": [10.0, 11.0, 11.0, 9.0, 12.0],
            "volume": [100.0, 110.0, 120.0, 130.0, 140.0],
        },
        index=pd.bdate_range("2026-10-19", periods=5),
    )

    preview = build_discovery_chart_preview(history, as_of=date(2026, 10, 23))

    assert preview.index.equals(history.index)
    assert preview["direction"].tolist() == ["neutral", "up", "neutral", "down", "up"]
    assert preview["close"].tolist() == history["close"].tolist()
    assert preview["volume"].tolist() == history["volume"].tolist()
    assert preview["sma50"].isna().all()


def test_discovery_preview_excludes_future_observations_and_calculates_exact_sma50():
    history = _history(55)
    history.loc[pd.Timestamp("2027-01-01")] = (1000.0, 1000.0)

    preview = build_discovery_chart_preview(history, as_of=date(2026, 3, 18))

    assert len(preview) == 55
    assert preview["sma50"].iloc[:49].isna().all()
    assert preview["sma50"].iloc[49] == sum(range(1, 51)) / 50


@pytest.mark.parametrize("missing", ["close", "volume"])
def test_missing_column_keeps_other_series_and_observation_date(missing: str) -> None:
    history = _history(160).drop(columns=[missing])
    chart = build_stock_chart_evidence(
        "instrument-a", history, as_of=history.index[-1].date()
    )
    assert chart.observed_on == history.index[-1].date()
    assert len(chart.history) == len(history)
    assert (chart.price_state if missing == "close" else chart.volume_state) == "insufficient"
    assert (chart.volume_state if missing == "close" else chart.price_state) == "available"
    assert chart.sma50_state == ("insufficient" if missing == "close" else "available")
    assert chart.sma150_state == ("insufficient" if missing == "close" else "available")
    preview = build_discovery_chart_preview(history, as_of=chart.requested_as_of)
    if missing == "close":
        assert preview["direction"].eq("neutral").all()
