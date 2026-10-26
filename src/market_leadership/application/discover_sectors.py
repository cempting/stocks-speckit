from dataclasses import dataclass
from datetime import date, timedelta
from typing import cast

import pandas as pd

from market_leadership.application.ports import MarketDataProvider
from market_leadership.domain.regimes import MarketSentiment, calculate_market_sentiment
from market_leadership.domain.sector_performance import (
    InsufficientHistoryError,
    PerformanceResult,
    calculate_performance,
    with_sma50,
)

BENCHMARK = "SPY"
SECTOR_PROXIES: tuple[tuple[str, str], ...] = (
    ("Communication Services", "XLC"),
    ("Consumer Discretionary", "XLY"),
    ("Consumer Staples", "XLP"),
    ("Energy", "XLE"),
    ("Financials", "XLF"),
    ("Health Care", "XLV"),
    ("Industrials", "XLI"),
    ("Information Technology", "XLK"),
    ("Materials", "XLB"),
    ("Real Estate", "XLRE"),
    ("Utilities", "XLU"),
)


@dataclass(frozen=True, slots=True)
class SectorDiscovery:
    name: str
    symbol: str
    performance: PerformanceResult | None
    history: pd.DataFrame
    insufficient_reason: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    as_of: date
    provider_id: str
    sentiment: MarketSentiment
    sectors: tuple[SectorDiscovery, ...]


def _empty_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "close": pd.Series(dtype="float64"),
            "volume": pd.Series(dtype="float64"),
        }
    )


def discover_sectors(
    provider: MarketDataProvider,
    *,
    as_of: date,
    force: bool = False,
) -> DiscoveryResult:
    symbols = (BENCHMARK, *(symbol for _, symbol in SECTOR_PROXIES))
    history = provider.fetch_daily_history(
        symbols,
        start=as_of - timedelta(days=550),
        end=as_of,
        force=force,
    )
    benchmark_history = history.get(BENCHMARK, _empty_history())
    sentiment = calculate_market_sentiment(benchmark_history, BENCHMARK)
    benchmark_closes = cast(pd.Series, benchmark_history["close"])
    sectors: list[SectorDiscovery] = []

    for name, symbol in SECTOR_PROXIES:
        raw_history = history.get(symbol, _empty_history())
        chart_history = with_sma50(raw_history)
        try:
            performance = calculate_performance(
                cast(pd.Series, chart_history["close"]),
                benchmark_closes,
                as_of=as_of,
            )
            reason = None
        except InsufficientHistoryError as error:
            performance = None
            reason = str(error)
        sectors.append(
            SectorDiscovery(
                name=name,
                symbol=symbol,
                performance=performance,
                history=chart_history,
                insufficient_reason=reason,
            )
        )

    return DiscoveryResult(
        as_of=as_of,
        provider_id=provider.provider_id,
        sentiment=sentiment,
        sectors=tuple(sectors),
    )
