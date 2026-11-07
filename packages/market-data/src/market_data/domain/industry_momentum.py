"""Momentum projection from explicitly supplied reviewed industry representations."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from market_data.domain.sector_performance import (
    calculate_performance_periods,
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
    start_session: date | None = None,
    end_session: date | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    selected_sectors = set(sectors)
    for representation in representations:
        if selected_sectors and representation.sector not in selected_sectors:
            continue
        frame = history.get(representation.symbol)
        closes = (
            frame["close"] if frame is not None and not frame.empty else pd.Series(dtype="float64")
        )
        results = calculate_performance_periods(
            closes,
            as_of=as_of,
            start_session=start_session,
            end_session=end_session,
        )
        performance = {period: result.value for period, result in results.items()}
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
                "1 day": performance["1d"],
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
