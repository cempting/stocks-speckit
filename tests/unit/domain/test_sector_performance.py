from datetime import date

import pandas as pd
import pytest

from market_leadership.domain.sector_performance import (
    InsufficientHistoryError,
    calculate_performance,
    with_sma50,
)


def _monthly_closes(values: list[float]) -> pd.Series:
    index = pd.date_range("2025-10-31", periods=len(values), freq="ME")
    return pd.Series(values, index=index, dtype="float64")


def test_calculate_absolute_and_relative_calendar_month_returns() -> None:
    sector = _monthly_closes([100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124])
    benchmark = _monthly_closes([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112])

    result = calculate_performance(sector, benchmark, as_of=date(2026, 10, 31))

    assert result.absolute["1m"] == pytest.approx((124 / 122) - 1)
    assert result.absolute["3m"] == pytest.approx((124 / 118) - 1)
    assert result.absolute["6m"] == pytest.approx((124 / 112) - 1)
    assert result.absolute["12m"] == pytest.approx((124 / 100) - 1)
    assert result.relative["1m"] == pytest.approx(result.absolute["1m"] - ((112 / 111) - 1))
    assert result.relative["3m"] == pytest.approx(result.absolute["3m"] - ((112 / 109) - 1))
    assert result.relative["6m"] == pytest.approx(result.absolute["6m"] - ((112 / 106) - 1))
    assert result.relative["12m"] == pytest.approx(result.absolute["12m"] - ((112 / 100) - 1))


def test_calculate_one_week_return_uses_close_on_or_before_target_date() -> None:
    index = pd.bdate_range("2025-10-24", "2026-10-26")
    sector = pd.Series(range(100, 100 + len(index)), index=index, dtype="float64")
    benchmark = pd.Series(range(200, 200 + len(index)), index=index, dtype="float64")

    result = calculate_performance(sector, benchmark, as_of=date(2026, 10, 26))

    sector_week = (sector.iloc[-1] / sector.loc[:"2026-10-19"].iloc[-1]) - 1
    benchmark_week = (benchmark.iloc[-1] / benchmark.loc[:"2026-10-19"].iloc[-1]) - 1
    assert result.absolute["1w"] == pytest.approx(sector_week)
    assert result.relative["1w"] == pytest.approx(sector_week - benchmark_week)


def test_calculate_performance_rejects_missing_twelve_month_history() -> None:
    closes = _monthly_closes([100, 101, 102, 103])

    with pytest.raises(InsufficientHistoryError):
        calculate_performance(closes, closes, as_of=date(2026, 1, 31))


def test_with_sma50_preserves_missing_warmup_values() -> None:
    frame = pd.DataFrame(
        {
            "close": range(1, 61),
            "volume": range(101, 161),
        },
        index=pd.date_range("2026-07-01", periods=60, freq="B"),
    )

    result = with_sma50(frame)

    assert result["sma50"].iloc[:49].isna().all()
    assert result["sma50"].iloc[49] == pytest.approx(sum(range(1, 51)) / 50)
    assert result["sma50"].iloc[-1] == pytest.approx(sum(range(11, 61)) / 50)
