from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

import pandas as pd

from market_data.catalog import CatalogSnapshot
from market_data.domain.catalog import BenchmarkPurpose, CatalogError, Scope
from market_data.domain.industry_representations import (
    ReviewedRepresentation,
    representation_performance,
)
from market_data.domain.regimes import MarketSentiment, calculate_market_sentiment
from market_data.domain.sector_performance import (
    InsufficientHistoryError,
    PerformancePeriod,
    PerformanceResult,
    calculate_absolute_performance,
    with_sma50,
)
from market_leadership.application.industry_representations import snapshot_representation_worklist
from market_leadership.application.ports import MarketDataProvider


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
    benchmark_as_of: date | None
    comparison_symbol: str | None = None
    sentiment_symbol: str | None = None
    comparison_reason: str | None = None
    sentiment_reason: str | None = None


def _empty_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "close": pd.Series(dtype="float64"),
            "volume": pd.Series(dtype="float64"),
        }
    )


def _purpose(
    snapshot: CatalogSnapshot, scope: Scope, purpose: BenchmarkPurpose, as_of: date
) -> tuple[str | None, str | None]:
    try:
        listing = snapshot.benchmark(scope.region_id, purpose, as_of)
    except CatalogError as error:
        if error.code not in ("missing_benchmark", "unavailable_benchmark"):
            raise
        return None, f"{purpose}: {error}"
    return listing.provider_symbol, None


def load_entity_representations(
    snapshot: CatalogSnapshot,
    *,
    scope: Scope,
    entity_type: Literal["sector", "industry", "sub_industry"],
    entity_ids: tuple[str, ...],
    as_of: date,
) -> tuple[ReviewedRepresentation, ...]:
    allowed_ids = set(entity_ids)
    return tuple(
        item.representation
        for item in snapshot_representation_worklist(snapshot, scope=scope, as_of=as_of)
        if item.node_type == entity_type
        and item.node_id in allowed_ids
        and item.representation is not None
    )


def load_industry_representations(
    snapshot: CatalogSnapshot, *, scope: Scope, entity_ids: tuple[str, ...], as_of: date
) -> tuple[ReviewedRepresentation, ...]:
    allowed_ids = set(entity_ids)
    return tuple(
        item.representation
        for item in snapshot_representation_worklist(snapshot, scope=scope, as_of=as_of)
        if item.node_type != "sector"
        and item.node_id in allowed_ids
        and item.representation is not None
    )


def discovery_symbols(
    snapshot: CatalogSnapshot,
    *,
    scope: Scope,
    as_of: date,
    sector_ids: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    symbols = {
        symbol
        for purpose in ("sp500_comparison", "market_sentiment")
        if (symbol := _purpose(snapshot, scope, purpose, as_of)[0]) is not None
    }
    for item in snapshot_representation_worklist(snapshot, scope=scope, as_of=as_of):
        if (
            item.node_type == "sector"
            and (sector_ids is None or item.node_id in sector_ids)
            and item.representation is not None
            and not item.representation.invalid_reason
        ):
            symbols.update(item.representation.symbols)
    return tuple(sorted(symbols))


def discover_sectors(
    provider: MarketDataProvider,
    *,
    snapshot: CatalogSnapshot,
    scope: Scope,
    as_of: date,
    force: bool = False,
    sector_ids: tuple[str, ...] | None = None,
) -> DiscoveryResult:
    symbols = discovery_symbols(snapshot, scope=scope, as_of=as_of, sector_ids=sector_ids)
    history = (
        provider.fetch_daily_history(
            symbols, start=as_of - timedelta(days=550), end=as_of, force=force
        )
        if symbols
        else {}
    )
    return discover_sectors_from_history(
        provider.provider_id,
        history,
        snapshot=snapshot,
        scope=scope,
        as_of=as_of,
        sector_ids=sector_ids,
    )


def discover_sectors_from_history(
    provider_id: str,
    history: dict[str, pd.DataFrame],
    *,
    snapshot: CatalogSnapshot,
    scope: Scope,
    as_of: date,
    sector_ids: tuple[str, ...] | None = None,
) -> DiscoveryResult:
    comparison, comparison_reason = _purpose(snapshot, scope, "sp500_comparison", as_of)
    sentiment_symbol, sentiment_reason = _purpose(snapshot, scope, "market_sentiment", as_of)
    benchmark_history = (
        history.get(comparison, _empty_history()) if comparison else _empty_history()
    )
    benchmark_history = benchmark_history.loc[
        pd.DatetimeIndex(benchmark_history.index).date <= as_of
    ].sort_index()
    benchmark_as_of = (
        pd.DatetimeIndex(benchmark_history.index)[-1].date()
        if not benchmark_history.empty
        else None
    )
    sentiment_history = (
        history.get(sentiment_symbol, _empty_history()) if sentiment_symbol else _empty_history()
    )
    sentiment_history = sentiment_history.loc[
        pd.DatetimeIndex(sentiment_history.index).date <= as_of
    ].sort_index()
    sentiment = calculate_market_sentiment(
        sentiment_history, sentiment_symbol if sentiment_symbol is not None else "Not configured"
    )
    if comparison is not None and benchmark_as_of is None:
        comparison_reason = f"No comparison benchmark close is available for {comparison}"
    if sentiment_symbol is not None and sentiment_history.empty:
        sentiment_reason = f"No market sentiment history is available for {sentiment_symbol}"
    sectors: list[SectorDiscovery] = []
    for item in snapshot_representation_worklist(snapshot, scope=scope, as_of=as_of):
        if item.node_type != "sector" or (
            sector_ids is not None and item.node_id not in sector_ids
        ):
            continue
        representation = item.representation
        symbol = representation.symbol if representation and representation.symbol else ""
        raw = history.get(symbol, _empty_history())
        raw = raw.loc[pd.DatetimeIndex(raw.index).date <= as_of].sort_index()
        chart = with_sma50(raw) if symbol else _empty_history()
        try:
            if representation is None:
                raise InsufficientHistoryError("Not covered: no reviewed representation")
            if representation.invalid_reason:
                raise InsufficientHistoryError(representation.invalid_reason)
            if benchmark_as_of is None:
                raise InsufficientHistoryError(
                    comparison_reason or "No benchmark close is available"
                )
            absolute = representation_performance(representation, history, as_of=benchmark_as_of)
            baseline = calculate_absolute_performance(
                benchmark_history["close"], as_of=benchmark_as_of
            )
            if (
                representation.kind == "etf"
                and benchmark_as_of not in pd.DatetimeIndex(chart.index).date
            ):
                raise InsufficientHistoryError(
                    f"No sector close is available on benchmark date {benchmark_as_of}"
                )
            relative: dict[PerformancePeriod, float] = {
                period: value - baseline[period] for period, value in absolute.items()
            }
            performance = PerformanceResult(absolute, relative)
            reason = None
        except (InsufficientHistoryError, ValueError) as error:
            performance = None
            reason = str(error)
        sectors.append(SectorDiscovery(item.name, symbol, performance, chart, reason))
    return DiscoveryResult(
        as_of,
        provider_id,
        sentiment,
        tuple(sectors),
        benchmark_as_of,
        comparison,
        sentiment_symbol,
        comparison_reason,
        sentiment_reason,
    )


def discover_sectors_from_snapshot(
    tables: dict[str, pd.DataFrame],
    *,
    source_id: str,
    as_of: date,
    snapshot: CatalogSnapshot,
    scope: Scope,
) -> DiscoveryResult:
    prices = tables["prices"]
    if list(prices.columns) != ["symbol", "date", "close", "volume"]:
        raise ValueError("snapshot prices must have canonical daily-history columns")
    if prices[["symbol", "date"]].isna().any().any():
        raise ValueError("snapshot prices contain missing keys")
    if prices.duplicated(subset=["symbol", "date"]).any():
        raise ValueError("snapshot prices contain duplicate symbol/date keys")
    histories: dict[str, pd.DataFrame] = {}
    for symbol in discovery_symbols(snapshot, scope=scope, as_of=as_of):
        rows = prices.loc[prices["symbol"] == symbol, ["date", "close", "volume"]].copy()
        rows["date"] = pd.to_datetime(rows["date"], errors="raise")
        history = rows.set_index("date").sort_index()
        dates = pd.DatetimeIndex(history.index).date
        history = history.loc[(dates >= as_of - timedelta(days=550)) & (dates <= as_of)].astype(
            {"close": "float64", "volume": "float64"}
        )
        history.attrs["source_id"] = source_id
        histories[symbol] = history
    return discover_sectors_from_history(
        source_id, histories, snapshot=snapshot, scope=scope, as_of=as_of
    )
