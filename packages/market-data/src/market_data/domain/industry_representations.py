"""Reviewed ETF and weighted stock-basket evidence, without proxy substitution."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from math import isfinite
from typing import Literal

import pandas as pd

from market_data.domain.sector_performance import (
    PERFORMANCE_PERIODS,
    InsufficientHistoryError,
    PerformancePeriod,
    PerformancePeriodResult,
    calculate_performance_periods,
)


@dataclass(frozen=True, slots=True)
class BasketConstituent:
    listing_id: str
    symbol: str
    weight: Decimal


def validate_weights(constituents: tuple[BasketConstituent, ...]) -> None:
    if not constituents:
        raise ValueError("Basket weights require at least one constituent")
    if len({item.listing_id for item in constituents}) != len(constituents):
        raise ValueError("Basket constituents must have distinct listing IDs")
    if len({item.symbol for item in constituents}) != len(constituents):
        raise ValueError("Basket constituents must have distinct provider symbols")
    if any(not item.weight.is_finite() or item.weight <= 0 for item in constituents):
        raise ValueError("Basket weights must be finite and positive")
    if sum(Fraction(item.weight) for item in constituents) != 100:
        raise ValueError("Basket weights must total exactly 100%")


@dataclass(frozen=True, slots=True)
class ReviewedRepresentation:
    representation_id: str
    node_id: str
    kind: Literal["etf", "basket"]
    name: str
    source_id: str
    approval_reference: str
    effective_from: date
    effective_to: date | None = None
    symbol: str | None = None
    constituents: tuple[BasketConstituent, ...] = ()
    reason: str | None = None

    @property
    def invalid_reason(self) -> str | None:
        if self.reason:
            return self.reason
        if not self.source_id.strip() or not self.approval_reference.strip():
            return "Source and approval evidence are required"
        if self.effective_to is not None and self.effective_to < self.effective_from:
            return "Representation effective dates are reversed"
        if self.kind == "etf":
            return None if self.symbol and not self.constituents else "Invalid ETF evidence"
        try:
            validate_weights(self.constituents)
        except ValueError as error:
            return str(error)
        return None

    def active_on(self, as_of: date) -> bool:
        return self.effective_from <= as_of and (
            self.effective_to is None or as_of <= self.effective_to
        )

    @property
    def symbols(self) -> tuple[str, ...]:
        if self.invalid_reason:
            return ()
        if self.kind == "etf":
            return (self.symbol,) if self.symbol else ()
        return tuple(item.symbol for item in self.constituents)


@dataclass(frozen=True, slots=True)
class RepresentationReviewItem:
    region_id: str
    classification_id: str
    node_id: str
    name: str
    node_type: str
    sector_id: str
    status: Literal["etf", "basket", "not_covered", "invalid"]
    representation: ReviewedRepresentation | None


RepresentationPeriod = PerformancePeriod
RepresentationPeriodResult = PerformancePeriodResult


def representation_performance(
    representation: ReviewedRepresentation,
    history: dict[str, pd.DataFrame],
    *,
    as_of: date,
    start_session: date | None = None,
    end_session: date | None = None,
    performance_as_of: date | None = None,
) -> dict[RepresentationPeriod, RepresentationPeriodResult]:
    """Return six fractional periods, each with an explicit unavailability reason."""
    legacy_as_of = performance_as_of if performance_as_of is not None else as_of
    if legacy_as_of > as_of:
        raise ValueError("Longer-period date must not exceed the requested date")
    if not representation.active_on(as_of) and not representation.active_on(legacy_as_of):
        raise ValueError("Representation is outside its effective period")
    if representation.invalid_reason:
        raise ValueError(representation.invalid_reason)
    symbols = representation.symbols
    constituent_results: dict[str, dict[PerformancePeriod, PerformancePeriodResult]] = {}
    basket_dates: pd.DatetimeIndex | None = None
    for symbol in symbols:
        frame = history.get(symbol)
        if frame is None or "close" not in frame:
            constituent_results[symbol] = {
                period: PerformancePeriodResult(
                    None, f"No approved constituent history for {symbol}"
                )
                for period in PERFORMANCE_PERIODS
            }
            continue
        periods = calculate_performance_periods(
            frame["close"],
            as_of=legacy_as_of,
            start_session=start_session,
            end_session=end_session,
        )
        try:
            closes = frame.loc[
                pd.DatetimeIndex(frame.index).date <= legacy_as_of, "close"
            ].sort_index()
            if closes.empty or any(
                not isfinite(float(value)) or float(value) <= 0 for value in closes
            ):
                raise InsufficientHistoryError("Invalid or missing closes")
            if representation.kind == "basket":
                dates = pd.DatetimeIndex(closes.index)
                if dates[-1].date() != legacy_as_of:
                    raise InsufficientHistoryError(f"No constituent close on {legacy_as_of}")
                if basket_dates is not None and not basket_dates.equals(dates):
                    raise InsufficientHistoryError("Incomplete aligned basket history")
                basket_dates = dates
        except ValueError as error:
            for period in PERFORMANCE_PERIODS[1:]:
                periods[period] = PerformancePeriodResult(None, str(error))
        constituent_results[symbol] = periods

    results: dict[RepresentationPeriod, RepresentationPeriodResult] = {}
    for period in PERFORMANCE_PERIODS:
        try:
            if period == "1d":
                if not representation.active_on(as_of):
                    raise ValueError("Representation is outside its effective period")
                if start_session is None or end_session is None:
                    raise InsufficientHistoryError(
                        "Daily return requires explicit completed-session dates"
                    )
                if end_session > as_of:
                    raise ValueError("Daily ending session must not exceed the requested date")
            elif not representation.active_on(legacy_as_of):
                raise ValueError("Representation is outside its effective period")
            returns: dict[str, float] = {}
            for symbol in symbols:
                result = constituent_results[symbol][period]
                if result.value is None:
                    raise InsufficientHistoryError(f"{symbol}: {result.reason}")
                returns[symbol] = result.value
            value = (
                returns[symbols[0]]
                if representation.kind == "etf"
                else sum(
                    float(item.weight / 100) * returns[item.symbol]
                    for item in representation.constituents
                )
            )
            if not isfinite(value):
                raise InsufficientHistoryError(f"Invalid approved representation {period} return")
            results[period] = RepresentationPeriodResult(value)
        except ValueError as error:
            results[period] = RepresentationPeriodResult(None, str(error))
    return results
