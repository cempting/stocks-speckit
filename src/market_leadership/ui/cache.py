from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from market_leadership.application.discover_sectors import (
    DiscoveryResult,
    discover_sectors_from_snapshot,
)
from market_leadership.application.ports import DataPointRequest, SnapshotReference
from market_leadership.application.request_market_data import (
    RequestedMarketData,
    RequestMarketData,
)
from market_leadership.domain.fundamentals import (
    FundamentalBundle,
    FundamentalRequest,
    FundamentalScorecard,
    build_scorecard,
)
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.snapshot_errors import IntegrityError, SchemaMismatch
from market_leadership.infrastructure.yfinance_fundamentals import (
    TickerFactory,
    read_fundamentals,
    ticker_factory,
)


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


@st.cache_data(max_entries=256, show_spinner=False)
def cached_scorecard(bundle: FundamentalBundle, history_window: int = 8) -> FundamentalScorecard:
    return build_scorecard(bundle, history_window)
