from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd


class InsufficientHistoryError(ValueError):
    """Raised when a return period lacks a valid starting observation."""


PerformancePeriod = Literal["1w", "1m", "3m", "6m", "12m"]


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
) -> dict[PerformancePeriod, float]:
    as_of_timestamp = pd.Timestamp(as_of)
    prepared = _prepare_closes(closes, as_of_timestamp)
    latest = _close_on_or_before(prepared, as_of_timestamp)
    absolute: dict[PerformancePeriod, float] = {}
    periods: tuple[tuple[PerformancePeriod, pd.DateOffset], ...] = (
        ("1w", pd.DateOffset(days=7)),
        ("1m", pd.DateOffset(months=1)),
        ("3m", pd.DateOffset(months=3)),
        ("6m", pd.DateOffset(months=6)),
        ("12m", pd.DateOffset(months=12)),
    )
    for period, offset in periods:
        absolute[period] = latest / _close_on_or_before(prepared, as_of_timestamp - offset) - 1
    return absolute


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
