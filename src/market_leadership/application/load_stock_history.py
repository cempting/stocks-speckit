"""Load canonical daily history for one selected industry's active members."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import isfinite

import pandas as pd

from market_leadership.application.ports import MarketDataProvider


@dataclass(frozen=True, slots=True)
class StockHistorySeries:
    symbol: str
    history: pd.DataFrame
    observed_on: date | None
    state: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class StockHistoryBatch:
    provider_id: str
    requested_as_of: date
    series: tuple[StockHistorySeries, ...]


def load_stock_history(
    provider: MarketDataProvider,
    symbols: tuple[str, ...],
    *,
    as_of: date,
    force: bool = False,
) -> StockHistoryBatch:
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("Stock history requires a nonempty, duplicate-free member set")
    if any(not symbol or symbol != symbol.upper() for symbol in symbols):
        raise ValueError("Stock history symbols must be nonempty canonical uppercase symbols")
    requested = provider.fetch_daily_history(
        symbols,
        start=as_of - timedelta(days=550),
        end=as_of,
        force=force,
    )
    series: list[StockHistorySeries] = []
    for symbol in symbols:
        history = requested.get(symbol)
        if history is None or history.empty:
            series.append(
                StockHistorySeries(
                    symbol,
                    pd.DataFrame(columns=["close", "volume"], dtype="float64"),
                    None,
                    "unavailable",
                    "The provider returned no history for this member.",
                )
            )
            continue
        if not {"close", "volume"}.issubset(history.columns):
            series.append(
                StockHistorySeries(
                    symbol,
                    pd.DataFrame(columns=["close", "volume"], dtype="float64"),
                    None,
                    "insufficient",
                    "The member history is missing close or volume evidence.",
                )
            )
            continue
        eligible = history.loc[
            pd.DatetimeIndex(history.index).date <= as_of, ["close", "volume"]
        ].sort_index()
        values_valid = (
            not eligible.empty
            and not eligible.index.has_duplicates
            and all(isfinite(float(value)) and float(value) > 0 for value in eligible["close"])
            and all(isfinite(float(value)) and float(value) >= 0 for value in eligible["volume"])
        )
        if not values_valid:
            series.append(
                StockHistorySeries(
                    symbol,
                    pd.DataFrame(columns=["close", "volume"], dtype="float64"),
                    None,
                    "insufficient",
                    "The member history is empty or contains invalid observations.",
                )
            )
            continue
        series.append(
            StockHistorySeries(
                symbol,
                eligible,
                pd.DatetimeIndex(eligible.index)[-1].date(),
                "available",
            )
        )
    return StockHistoryBatch(provider.provider_id, as_of, tuple(series))
