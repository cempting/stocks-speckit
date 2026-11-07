from datetime import date

import pandas as pd
import pytest

from market_data.domain.sector_performance import (
    InsufficientHistoryError,
    calculate_absolute_performance,
    calculate_daily_return,
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


def test_selected_absolute_period_does_not_require_unrelated_yearly_history() -> None:
    closes = _monthly_closes([100, 101, 102, 103])
    result = calculate_absolute_performance(closes, as_of=date(2026, 1, 31), period="1m")
    assert result == {"1m": pytest.approx(103 / 102 - 1)}
    with pytest.raises(InsufficientHistoryError):
        calculate_absolute_performance(closes, as_of=date(2026, 1, 31))


def test_selected_absolute_period_rejects_unsupported_daily_offset() -> None:
    with pytest.raises(ValueError, match="Unsupported performance period"):
        calculate_absolute_performance(
            _monthly_closes([100, 101]), as_of=date(2025, 11, 30), period="1d"
        )


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


@pytest.mark.parametrize(("end", "expected"), [(102.0, 0.02), (99.0, -0.01), (100.0, 0.0)])
def test_daily_return_uses_only_exact_adjusted_endpoints(end, expected):
    closes = pd.Series(
        [float("nan"), 100.0, end, 500.0],
        index=pd.to_datetime(["2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02"]),
    )
    assert calculate_daily_return(
        closes, start_session=date(2026, 10, 29), end_session=date(2026, 10, 30)
    ) == pytest.approx(expected)


@pytest.mark.parametrize("missing", ["2026-10-29", "2026-10-30"])
def test_daily_return_never_substitutes_an_older_available_close(missing):
    closes = pd.Series([98.0, 100.0, 102.0], index=pd.bdate_range("2026-10-28", periods=3))
    with pytest.raises(InsufficientHistoryError, match=missing):
        calculate_daily_return(
            closes.drop(pd.Timestamp(missing)),
            start_session=date(2026, 10, 29),
            end_session=date(2026, 10, 30),
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 0.0, -1.0])
@pytest.mark.parametrize("endpoint", [0, 1])
def test_daily_return_rejects_invalid_endpoint_prices(value, endpoint):
    values = [100.0, 102.0]
    values[endpoint] = value
    closes = pd.Series(values, index=pd.bdate_range("2026-10-29", periods=2))
    with pytest.raises(InsufficientHistoryError, match="2026-10"):
        calculate_daily_return(
            closes, start_session=date(2026, 10, 29), end_session=date(2026, 10, 30)
        )


@pytest.mark.parametrize("dates", [
    ["2026-10-29", "2026-10-29", "2026-10-30"],
    ["2026-10-29 09:00", "2026-10-29 16:00", "2026-10-30 16:00"],
])
def test_daily_return_rejects_duplicate_observation_dates(dates):
    closes = pd.Series([100.0, 101.0, 102.0], index=pd.to_datetime(dates))
    with pytest.raises(ValueError, match="unique"):
        calculate_daily_return(
            closes, start_session=date(2026, 10, 29), end_session=date(2026, 10, 30)
        )


@pytest.mark.parametrize("start", [date(2026, 10, 30), date(2026, 11, 2)])
def test_daily_return_rejects_unordered_sessions(start):
    closes = pd.Series([100.0, 102.0], index=pd.bdate_range("2026-10-29", periods=2))
    with pytest.raises(ValueError, match="earlier"):
        calculate_daily_return(closes, start_session=start, end_session=date(2026, 10, 30))


def test_daily_return_handles_session_timezone_without_changing_legacy_periods():
    closes = pd.Series(
        range(100, 500), index=pd.bdate_range(end="2026-10-30", periods=400)
    )
    before = calculate_absolute_performance(closes, as_of=date(2026, 10, 30))
    assert tuple(before) == ("1w", "1m", "3m", "6m", "12m")
    daily = calculate_daily_return(
        closes.tz_localize("America/New_York"),
        start_session=date(2026, 10, 29), end_session=date(2026, 10, 30),
    )
    assert daily == pytest.approx(499 / 498 - 1)
    assert before == calculate_absolute_performance(closes, as_of=date(2026, 10, 30))


@pytest.mark.parametrize(
    "closes",
    [
        pd.Series([100.0, 102.0]),
        pd.Series([100.0, 102.0], index=pd.to_datetime(["2026-10-29", None])),
    ],
)
def test_daily_return_rejects_malformed_observation_index(closes):
    with pytest.raises(ValueError, match="datetime"):
        calculate_daily_return(
            closes, start_session=date(2026, 10, 29), end_session=date(2026, 10, 30)
        )


@pytest.mark.parametrize(
    "closes",
    [
        pd.Series(dtype="float64"),
        pd.Series(["bad", 102.0], index=pd.to_datetime(["2026-10-29", "2026-10-30"])),
        pd.Series([1e-300, 1e300], index=pd.to_datetime(["2026-10-29", "2026-10-30"])),
    ],
)
def test_daily_return_rejects_empty_nonnumeric_or_overflowing_evidence(closes):
    with pytest.raises(InsufficientHistoryError):
        calculate_daily_return(
            closes, start_session=date(2026, 10, 29), end_session=date(2026, 10, 30)
        )
