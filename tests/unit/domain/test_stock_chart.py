from datetime import date

import pandas as pd

from market_leadership.domain.stock_chart import build_stock_chart_evidence


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
