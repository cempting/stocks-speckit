from datetime import date

import pandas as pd
import pytest

from market_data.domain.stock_chart import (
    build_discovery_chart_preview,
    build_stock_chart_evidence,
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
