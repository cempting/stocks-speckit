from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Literal

import pandas as pd


class InsufficientHistoryError(ValueError):
    """Raised when a return period lacks a valid starting observation."""


PerformancePeriod = Literal["1d", "1w", "1m", "3m", "6m", "12m"]
PERFORMANCE_PERIODS: tuple[PerformancePeriod, ...] = ("1d", "1w", "1m", "3m", "6m", "12m")
_CALENDAR_PERIODS: tuple[tuple[PerformancePeriod, pd.DateOffset], ...] = (
    ("1w", pd.DateOffset(days=7)),
    ("1m", pd.DateOffset(months=1)),
    ("3m", pd.DateOffset(months=3)),
    ("6m", pd.DateOffset(months=6)),
    ("12m", pd.DateOffset(months=12)),
)


@dataclass(frozen=True, slots=True)
class PerformancePeriodResult:
    value: float | None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PerformanceResult:
    absolute: dict[PerformancePeriod, float]
    relative: dict[PerformancePeriod, float]


def _close_on_or_before(closes: pd.Series, when: pd.Timestamp) -> float:
    eligible = closes.loc[closes.index <= when]
    if eligible.empty:
        raise InsufficientHistoryError(f"No close is available on or before {when.date()}")
    return float(eligible.iloc[-1])


def _prepare_closes(closes: pd.Series, as_of: pd.Timestamp) -> pd.Series:
    prepared = closes.dropna().sort_index()
    if prepared.index.has_duplicates:
        raise ValueError("Close dates must be unique")
    prepared = prepared.loc[prepared.index <= as_of]
    if prepared.empty:
        raise InsufficientHistoryError(f"No close is available on or before {as_of.date()}")
    return prepared


def calculate_absolute_performance(
    closes: pd.Series,
    *,
    as_of: date,
    period: PerformancePeriod | None = None,
    start_session: date | None = None,
    end_session: date | None = None,
) -> dict[PerformancePeriod, float]:
    """Require all five legacy horizons by default, or calculate one selected period."""
    if period == "1d":
        if start_session is None or end_session is None:
            raise InsufficientHistoryError("Daily return requires explicit completed-session dates")
        return {
            "1d": calculate_daily_return(
                closes, start_session=start_session, end_session=end_session
            )
        }
    as_of_timestamp = pd.Timestamp(as_of)
    prepared = _prepare_closes(closes, as_of_timestamp)
    latest = _close_on_or_before(prepared, as_of_timestamp)
    absolute: dict[PerformancePeriod, float] = {}
    periods = _CALENDAR_PERIODS
    if period is not None and period not in {candidate for candidate, _ in periods}:
        raise ValueError(f"Unsupported performance period: {period}")
    for candidate, offset in periods:
        if period is None or candidate == period:
            absolute[candidate] = (
                latest / _close_on_or_before(prepared, as_of_timestamp - offset) - 1
            )
    return absolute


def calculate_performance_periods(
    closes: pd.Series,
    *,
    as_of: date,
    start_session: date | None = None,
    end_session: date | None = None,
) -> dict[PerformancePeriod, PerformancePeriodResult]:
    """Calculate six independent display horizons, preparing calendar history only once."""
    results: dict[PerformancePeriod, PerformancePeriodResult] = {}
    try:
        daily = calculate_absolute_performance(
            closes,
            as_of=as_of,
            period="1d",
            start_session=start_session,
            end_session=end_session,
        )["1d"]
        results["1d"] = PerformancePeriodResult(daily)
    except ValueError as error:
        results["1d"] = PerformancePeriodResult(None, str(error))

    timestamp = pd.Timestamp(as_of)
    try:
        if closes.empty:
            raise InsufficientHistoryError(f"No close is available on or before {as_of}")
        if not isinstance(closes.index, pd.DatetimeIndex) or closes.index.hasnans:
            raise ValueError("Close dates must be valid datetime observations")
        calendar_closes = closes.tz_localize(None) if closes.index.tz is not None else closes
        prepared = _prepare_closes(calendar_closes, timestamp)
        latest = _close_on_or_before(prepared, timestamp)
    except ValueError as error:
        results.update(
            (period, PerformancePeriodResult(None, str(error))) for period, _ in _CALENDAR_PERIODS
        )
        return results
    for period, offset in _CALENDAR_PERIODS:
        try:
            baseline = _close_on_or_before(prepared, timestamp - offset)
            if any(not isfinite(price) or price <= 0 for price in (latest, baseline)):
                raise InsufficientHistoryError(f"Invalid close for {period}")
            value = latest / baseline - 1
            if not isfinite(value):
                raise InsufficientHistoryError(f"Invalid {period} return")
            results[period] = PerformancePeriodResult(value)
        except ValueError as error:
            results[period] = PerformancePeriodResult(None, str(error))
    return results


def calculate_daily_return(closes: pd.Series, *, start_session: date, end_session: date) -> float:
    if start_session >= end_session:
        raise ValueError("Daily starting session must be earlier than ending session")
    if closes.empty:
        raise InsufficientHistoryError(
            f"No closes for required daily sessions {start_session} and {end_session}"
        )
    if not isinstance(closes.index, pd.DatetimeIndex) or closes.index.hasnans:
        raise ValueError("Daily close dates must be valid datetime observations")
    dates = pd.Index(closes.index.date)
    if dates.has_duplicates:
        raise ValueError("Close dates must be unique")
    prices: list[float] = []
    for session in (start_session, end_session):
        observation = closes.loc[dates == session]
        if observation.empty:
            raise InsufficientHistoryError(f"No close for required session {session}")
        try:
            price = float(observation.iloc[0])
        except (TypeError, ValueError, OverflowError) as error:
            raise InsufficientHistoryError(
                f"Invalid close for required session {session}"
            ) from error
        if not isfinite(price) or price <= 0:
            raise InsufficientHistoryError(f"Invalid close for required session {session}")
        prices.append(price)
    result = prices[1] / prices[0] - 1
    if not isfinite(result):
        raise InsufficientHistoryError(
            f"Invalid daily return for required sessions {start_session} and {end_session}"
        )
    return result


def calculate_performance(
    sector_closes: pd.Series,
    benchmark_closes: pd.Series,
    *,
    as_of: date,
) -> PerformanceResult:
    absolute = calculate_absolute_performance(sector_closes, as_of=as_of)
    benchmark_absolute = calculate_absolute_performance(benchmark_closes, as_of=as_of)
    relative: dict[PerformancePeriod, float] = {}
    for period, sector_return in absolute.items():
        relative[period] = sector_return - benchmark_absolute[period]

    return PerformanceResult(absolute=absolute, relative=relative)


def with_sma50(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"close", "volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    result = frame.sort_index().copy()
    result["sma50"] = result["close"].rolling(window=50, min_periods=50).mean()
    return result
