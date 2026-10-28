"""Calendar-lookback, matching-basis local relative-strength calculations."""

import math
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Literal, cast

import pandas as pd

Period = Literal["1w", "1m", "3m", "6m", "12m"]
PERIODS: tuple[tuple[Period, pd.DateOffset], ...] = (
    ("1w", pd.DateOffset(days=7)),
    ("1m", pd.DateOffset(months=1)),
    ("3m", pd.DateOffset(months=3)),
    ("6m", pd.DateOffset(months=6)),
    ("12m", pd.DateOffset(months=12)),
)


class MissingStrengthReason(StrEnum):
    """Reasons a requested return/composite cannot be calculated."""

    CURRENCY_MISMATCH = "currency_mismatch"
    RETURN_BASIS_MISMATCH = "return_basis_mismatch"
    NO_SHARED_END = "no_shared_end"
    MISSING_1W = "missing_1w"
    MISSING_1M = "missing_1m"
    MISSING_3M = "missing_3m"
    MISSING_6M = "missing_6m"
    MISSING_12M = "missing_12m"


_MISSING_START: dict[Period, MissingStrengthReason] = {
    "1w": MissingStrengthReason.MISSING_1W,
    "1m": MissingStrengthReason.MISSING_1M,
    "3m": MissingStrengthReason.MISSING_3M,
    "6m": MissingStrengthReason.MISSING_6M,
    "12m": MissingStrengthReason.MISSING_12M,
}


@dataclass(frozen=True, slots=True)
class RelativeStrengthResult:
    """Fractional returns, matched observation dates and explicit missing evidence.

    Relative returns are entry absolute return minus local benchmark absolute
    return. ``composite`` is absent unless all three weighted terms exist.
    """

    absolute: dict[Period, float]
    relative: dict[Period, float]
    starting_on: dict[Period, date]
    ending_on: date | None
    composite: float | None
    missing_reasons: tuple[MissingStrengthReason, ...]


def _validated_closes(closes: pd.Series, label: str, as_of: date) -> pd.Series:
    if not isinstance(closes.index, pd.DatetimeIndex):
        raise ValueError(f"{label} close dates must be a DatetimeIndex")
    if closes.index.has_duplicates:
        raise ValueError(f"{label} close dates must be unique")
    if closes.index.tz is not None:
        raise ValueError(f"{label} close dates must be timezone-naive local session dates")
    valid = closes.loc[closes.index <= pd.Timestamp(as_of)].dropna().sort_index()
    for close in valid:
        if not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
            raise ValueError(f"{label} closes must be finite positive numbers")
    return valid


def calculate_relative_strength(
    entry_closes: pd.Series,
    benchmark_closes: pd.Series,
    *,
    as_of: date,
    currency: str,
    benchmark_currency: str,
    return_basis: str,
    benchmark_return_basis: str,
) -> RelativeStrengthResult:
    """Compare two dated close series without mixing dates, currency or return basis.

    Each period uses the latest *shared* close on/before its calendar target;
    the ending close must be the latest available close of each series on/before
    ``as_of``. Missing lookbacks remain absent rather than borrowing a later
    date or inventing a rank-eligible composite.
    """
    for label, value in (
        ("currency", currency),
        ("benchmark_currency", benchmark_currency),
        ("return_basis", return_basis),
        ("benchmark_return_basis", benchmark_return_basis),
    ):
        if not value.strip():
            raise ValueError(f"{label} must not be empty")
    reasons: list[MissingStrengthReason] = []
    if currency != benchmark_currency:
        reasons.append(MissingStrengthReason.CURRENCY_MISMATCH)
    if return_basis != benchmark_return_basis:
        reasons.append(MissingStrengthReason.RETURN_BASIS_MISMATCH)
    if reasons:
        return RelativeStrengthResult({}, {}, {}, None, None, tuple(reasons))

    entry = _validated_closes(entry_closes, "entry", as_of)
    benchmark = _validated_closes(benchmark_closes, "benchmark", as_of)
    shared_dates = entry.index.intersection(benchmark.index).sort_values()
    if (
        entry.empty
        or benchmark.empty
        or shared_dates.empty
        or shared_dates[-1] != entry.index[-1]
        or shared_dates[-1] != benchmark.index[-1]
    ):
        return RelativeStrengthResult(
            {}, {}, {}, None, None, (MissingStrengthReason.NO_SHARED_END,)
        )

    end = cast(pd.Timestamp, shared_dates[-1])
    absolute: dict[Period, float] = {}
    relative: dict[Period, float] = {}
    starting_on: dict[Period, date] = {}
    for period, offset in PERIODS:
        target = end - offset
        eligible = [
            cast(pd.Timestamp, timestamp)
            for timestamp in shared_dates
            if cast(pd.Timestamp, timestamp) <= target
        ]
        if not eligible:
            reasons.append(_MISSING_START[period])
            continue
        start = eligible[-1]
        entry_return = float(entry.loc[end] / entry.loc[start] - 1)
        benchmark_return = float(benchmark.loc[end] / benchmark.loc[start] - 1)
        absolute[period] = entry_return
        relative[period] = entry_return - benchmark_return
        starting_on[period] = start.date()

    composite = None
    if all(period in relative for period in ("3m", "6m", "12m")):
        composite = 0.4 * relative["3m"] + 0.3 * relative["6m"] + 0.3 * relative["12m"]
    return RelativeStrengthResult(
        absolute, relative, starting_on, end.date(), composite, tuple(reasons)
    )
