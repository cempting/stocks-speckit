"""Momentum projection from explicitly supplied reviewed industry representations."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from market_data.domain.sector_performance import (
    InsufficientHistoryError,
    calculate_absolute_performance,
)


@dataclass(frozen=True, slots=True)
class IndustryRepresentation:
    industry_id: str
    industry_name: str
    sector: str
    symbol: str


def industry_symbols(representations: tuple[IndustryRepresentation, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(representation.symbol for representation in representations))


def industry_momentum_frame(
    history: dict[str, pd.DataFrame],
    *,
    as_of: date,
    sectors: tuple[str, ...],
    representations: tuple[IndustryRepresentation, ...],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    selected_sectors = set(sectors)
    for representation in representations:
        if selected_sectors and representation.sector not in selected_sectors:
            continue
        frame = history.get(representation.symbol)
        closes = (
            frame.loc[pd.DatetimeIndex(frame.index).date <= as_of, "close"]
            if frame is not None and not frame.empty
            else pd.Series(dtype="float64")
        )
        try:
            performance = (
                calculate_absolute_performance(closes, as_of=as_of)
                if not closes.empty
                else {"1w": None, "1m": None, "3m": None, "6m": None, "12m": None}
            )
        except InsufficientHistoryError:
            performance = {"1w": None, "1m": None, "3m": None, "6m": None, "12m": None}
        rows.append(
            {
                "Industry": representation.industry_name,
                "Sector": representation.sector,
                "Representation": representation.symbol,
                "ETF": representation.symbol,
                "Evidence state": (
                    "available"
                    if all(value is not None for value in performance.values())
                    else "insufficient_evidence"
                    if not closes.empty
                    else "unavailable_evidence"
                ),
                "1 week": performance["1w"],
                "1 month": performance["1m"],
                "3 months": performance["3m"],
                "6 months": performance["6m"],
                "12 months": performance["12m"],
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["Industry", "Representation"], kind="stable").reset_index(drop=True)
