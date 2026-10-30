"""Load canonical daily history for one selected industry's active members."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import isfinite

import pandas as pd

from market_leadership.application.ports import MarketDataProvider
from market_leadership.infrastructure.region_database import StockMembershipRecord


@dataclass(frozen=True, slots=True)
class StockHistorySeries:
    symbol: str
    history: pd.DataFrame
    observed_on: date | None
    state: str
    reason: str | None = None
    price_state: str = "unavailable"
    volume_state: str = "unavailable"


@dataclass(frozen=True, slots=True)
class StockHistoryBatch:
    provider_id: str
    requested_as_of: date
    series: tuple[StockHistorySeries, ...]


def verified_primary_provider_symbols(
    members: tuple[StockMembershipRecord, ...],
) -> tuple[str, ...]:
    symbols: list[str] = []
    for member in members:
        primary = member.primary_listing
        if (
            member.resolution_state == "identified"
            and primary is not None
            and primary.resolution_state == "verified"
        ):
            symbol = primary.provider_symbol or primary.symbol
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return tuple(symbols)


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
        eligible = history.loc[
            pd.DatetimeIndex(history.index).date <= as_of
        ].reindex(columns=["close", "volume"]).sort_index()
        if eligible.empty or eligible.index.has_duplicates:
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
        states: dict[str, str] = {}
        for column in ("close", "volume"):
            values = pd.to_numeric(eligible[column], errors="coerce")
            valid = values.map(lambda value: isfinite(float(value))) & (
                values > 0 if column == "close" else values >= 0
            )
            eligible[column] = values.where(valid)
            states[column] = "available" if valid.all() else "insufficient"
        complete = all(state == "available" for state in states.values())
        series.append(
            StockHistorySeries(
                symbol,
                eligible,
                pd.DatetimeIndex(eligible.index)[-1].date(),
                "available" if complete else "insufficient",
                None if complete else "Close or volume evidence is incomplete; see series states.",
                states["close"],
                states["volume"],
            )
        )
    return StockHistoryBatch(provider.provider_id, as_of, tuple(series))
