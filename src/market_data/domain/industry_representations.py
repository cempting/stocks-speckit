"""Reviewed ETF and weighted stock-basket evidence, without proxy substitution."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from math import isfinite
from typing import Literal

import pandas as pd

from market_data.domain.sector_performance import (
    InsufficientHistoryError,
    PerformancePeriod,
    calculate_absolute_performance,
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


def representation_performance(
    representation: ReviewedRepresentation,
    history: dict[str, pd.DataFrame],
    *,
    as_of: date,
) -> dict[PerformancePeriod, float]:
    if not representation.active_on(as_of):
        raise ValueError("Representation is outside its effective period")
    if representation.invalid_reason:
        raise ValueError(representation.invalid_reason)
    results: dict[str, dict[PerformancePeriod, float]] = {}
    basket_dates: pd.DatetimeIndex | None = None
    for symbol in representation.symbols:
        frame = history.get(symbol)
        if frame is None or frame.empty or "close" not in frame:
            raise InsufficientHistoryError(f"No approved constituent history for {symbol}")
        closes = frame.loc[pd.DatetimeIndex(frame.index).date <= as_of, "close"].sort_index()
        if closes.empty or any(not isfinite(float(value)) or float(value) <= 0 for value in closes):
            raise InsufficientHistoryError(f"Invalid or missing closes for {symbol}")
        if representation.kind == "basket":
            dates = pd.DatetimeIndex(closes.index)
            if dates[-1].date() != as_of:
                raise InsufficientHistoryError(f"No constituent close on {as_of}: {symbol}")
            # Never align by dropping missing constituent observations or renormalizing weights.
            if basket_dates is not None and not basket_dates.equals(dates):
                raise InsufficientHistoryError(f"Incomplete aligned basket history for {symbol}")
            basket_dates = dates
        results[symbol] = calculate_absolute_performance(closes, as_of=as_of)
    if representation.kind == "etf":
        return results[representation.symbols[0]]
    periods: tuple[PerformancePeriod, ...] = ("1w", "1m", "3m", "6m", "12m")
    return {
        period: sum(
            float(item.weight / 100) * results[item.symbol][period]
            for item in representation.constituents
        )
        for period in periods
    }
