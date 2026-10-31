from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from market_leadership.application.discover_sectors import (
    DiscoveryResult,
    discover_sectors_from_snapshot,
)
from market_leadership.application.load_stock_history import (
    StockHistoryBatch,
    StockHistorySeries,
    load_stock_history,
)
from market_leadership.application.ports import DataPointRequest, SnapshotReference
from market_leadership.application.request_market_data import (
    RequestedMarketData,
    RequestMarketData,
)
from market_leadership.domain.catalog import Scope
from market_leadership.domain.fundamentals import (
    FundamentalBundle,
    FundamentalRequest,
    FundamentalScorecard,
    build_scorecard,
)
from market_leadership.infrastructure.catalog_files import CatalogReader, CatalogSnapshot
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.snapshot_errors import IntegrityError, SchemaMismatch
from market_leadership.infrastructure.yfinance_fundamentals import (
    TickerFactory,
    read_fundamentals,
    ticker_factory,
)


@st.cache_resource(show_spinner=False)
def _catalog_reader() -> CatalogReader:
    return CatalogReader()


def load_catalog_snapshot(entry_path: str | Path) -> CatalogSnapshot:
    # The reader verifies active file signatures, including ctime, before every reuse.
    return _catalog_reader().read(Path(entry_path))


@st.cache_data(show_spinner=False)
def _cached_snapshot_tables(
    _snapshot_root: str,
    snapshot_id: str,
    manifest_checksum: str,
) -> dict[str, pd.DataFrame]:
    repository = ParquetSnapshotRepository(_snapshot_root)
    reference = repository.reference(snapshot_id)
    if reference.manifest_checksum != manifest_checksum:
        raise IntegrityError(
            snapshot_id,
            "manifest",
            "manifest checksum changed while loading snapshot",
        )
    return repository.load(snapshot_id)


def load_snapshot_tables(
    snapshot_root: str | Path,
    snapshot_id: str,
    manifest_checksum: str,
) -> dict[str, pd.DataFrame]:
    return _cached_snapshot_tables(str(snapshot_root), snapshot_id, manifest_checksum)


def load_published_discovery(
    repository: ParquetSnapshotRepository,
    snapshot_root: str | Path,
    *,
    snapshot: CatalogSnapshot,
    scope: Scope,
) -> tuple[SnapshotReference, DiscoveryResult]:
    reference = repository.load_latest()
    if reference.ruleset_version != "daily-history-1" or reference.source_id is None:
        raise SchemaMismatch(
            reference.snapshot_id,
            "manifest",
            "latest snapshot must be a single-source daily-history input snapshot",
        )
    tables = load_snapshot_tables(snapshot_root, reference.snapshot_id, reference.manifest_checksum)
    return reference, discover_sectors_from_snapshot(
        tables,
        source_id=reference.source_id,
        as_of=reference.as_of,
        snapshot=snapshot,
        scope=scope,
    )


def clear_snapshot_cache() -> None:
    _cached_snapshot_tables.clear()


def refresh_market_data(
    request_use_case: RequestMarketData,
    request: DataPointRequest,
) -> RequestedMarketData:
    return request_use_case.execute(request, force=True)


@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)
def _cached_fundamentals(
    request: FundamentalRequest,
    _factory: TickerFactory,
    _now: datetime,
) -> FundamentalBundle:
    return read_fundamentals(request, _factory, now=_now)


def load_fundamental_bundle(
    request: FundamentalRequest,
    *,
    _factory: TickerFactory = ticker_factory,
    now: datetime | None = None,
) -> FundamentalBundle:
    current = now or datetime.now(UTC)
    evidence = _cached_fundamentals(request, _factory, current)
    if (current - evidence.fetched_at).total_seconds() >= 3600:
        _cached_fundamentals.clear(request, _factory, current)
        evidence = _cached_fundamentals(request, _factory, current)
    return evidence


def refresh_fundamental_bundle(
    request: FundamentalRequest,
    *,
    _factory: TickerFactory = ticker_factory,
    now: datetime | None = None,
) -> FundamentalBundle:
    current = now or datetime.now(UTC)
    _cached_fundamentals.clear(request, _factory, current)
    return load_fundamental_bundle(request, _factory=_factory, now=current)


def _request_member_history(
    source_cache_path: str,
    symbols: tuple[str, ...],
    as_of: date,
    retry_limit: int,
    *,
    force_refresh: bool,
) -> StockHistoryBatch:
    from market_leadership.bootstrap import build_request_provider

    provider = build_request_provider(
        "yfinance",
        source_cache_path,
        retry_limit=retry_limit,
    )
    return load_stock_history(provider, symbols, as_of=as_of, force=force_refresh)


class _HistoryCacheMiss(Exception):
    pass


@st.cache_data(ttl=3600, max_entries=2048, show_spinner=False)
def _cached_member_series(
    source_cache_path: str,
    symbol: str,
    as_of: date,
    retry_limit: int,
    _seed: tuple[str, StockHistorySeries] | None = None,
) -> tuple[str, StockHistorySeries]:
    # A missing entry raises instead of caching unavailable or incomplete evidence.
    if _seed is None:
        raise _HistoryCacheMiss
    return _seed


def load_member_history(
    source_cache_path: str,
    symbols: tuple[str, ...],
    as_of: date,
    *,
    retry_limit: int,
    force_refresh: bool = False,
) -> StockHistoryBatch:
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("Stock history requires a nonempty, duplicate-free member set")
    cached: dict[str, StockHistorySeries] = {}
    provider_id = "yfinance"
    for symbol in symbols:
        if force_refresh:
            _cached_member_series.clear(source_cache_path, symbol, as_of, retry_limit)
            continue
        try:
            provider_id, cached[symbol] = _cached_member_series(
                source_cache_path, symbol, as_of, retry_limit
            )
        except _HistoryCacheMiss:
            continue
    missing = tuple(symbol for symbol in symbols if symbol not in cached)
    if missing:
        batch = _request_member_history(
            source_cache_path,
            missing,
            as_of,
            retry_limit,
            force_refresh=force_refresh,
        )
        provider_id = batch.provider_id
        for item in batch.series:
            cached[item.symbol] = item
            if item.state == "available":
                _cached_member_series(
                    source_cache_path,
                    item.symbol,
                    as_of,
                    retry_limit,
                    _seed=(provider_id, item),
                )
    return StockHistoryBatch(provider_id, as_of, tuple(cached[symbol] for symbol in symbols))


@st.cache_data(max_entries=256, show_spinner=False)
def cached_scorecard(bundle: FundamentalBundle, history_window: int = 8) -> FundamentalScorecard:
    return build_scorecard(bundle, history_window)
