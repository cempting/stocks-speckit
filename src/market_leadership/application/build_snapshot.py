"""Publish a verified daily-history input snapshot from an explicit provider request."""

import argparse
import hashlib
import io
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Protocol

import pandas as pd

from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.ports import (
    DataPointRequest,
    SnapshotReference,
    SnapshotRepository,
)
from market_leadership.application.request_market_data import RequestedMarketData
from market_leadership.infrastructure.provider_validation import canonicalize_daily_history


class DailyHistoryRequest(Protocol):
    def execute(self, request: DataPointRequest, *, force: bool = False) -> RequestedMarketData: ...


def build_daily_history_snapshot(
    request_service: DailyHistoryRequest,
    repository: SnapshotRepository,
    *,
    snapshot_id: str,
    as_of: date,
    symbols: tuple[str, ...],
    start: date,
    force_refresh: bool = False,
) -> SnapshotReference:
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("snapshot symbols must be nonempty and unique")
    required_session = latest_completed_us_session(as_of)
    if start > required_session:
        raise ValueError("snapshot start date must not follow the required session")
    request = DataPointRequest(
        data_point="daily_history",
        market_id="US",
        identifiers=symbols,
        frequency="1d",
        start=start,
        end=required_session,
        currency="USD",
        return_basis="adjusted",
    )
    result = request_service.execute(request, force=force_refresh)
    if set(result.data) != set(symbols):
        raise ValueError("provider response must include every requested symbol")
    canonical = canonicalize_daily_history(
        result.data,
        symbols,
        start=start,
        end=required_session,
        source_id=result.selected.provider_id,
    )
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        history = canonical[symbol]
        if history.empty or history.index[-1].date() != required_session:
            raise ValueError(f"daily history for {symbol} does not cover the required session")
        records = history.reset_index()
        records["date"] = records["date"].dt.date
        records.insert(0, "symbol", symbol)
        frames.append(records.loc[:, ["symbol", "date", "close", "volume"]])
    prices = pd.concat(frames, ignore_index=True)
    buffer = io.BytesIO()
    prices.to_parquet(buffer, index=False)
    return repository.publish(
        snapshot_id=snapshot_id,
        as_of=required_session,
        markets=("US",),
        ruleset_version="daily-history-1",
        tables={"prices": prices},
        sources=(
            {
                "source_id": result.selected.provider_id,
                "name": result.selected.provider_id,
                "dataset": "daily_history",
                "version": "1",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "checksum": hashlib.sha256(buffer.getvalue()).hexdigest(),
                "license_label": None,
            },
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a daily-history input snapshot")
    parser.add_argument("--provider", choices=("fixture", "massive", "yfinance"), required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    from dataclasses import replace

    from market_leadership.bootstrap import build_market_data_request
    from market_leadership.config import load_settings
    from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository

    settings = replace(load_settings(), provider_ids=(args.provider,))
    reference = build_daily_history_snapshot(
        build_market_data_request(settings),
        ParquetSnapshotRepository(args.output),
        snapshot_id=args.snapshot_id,
        as_of=args.as_of,
        symbols=tuple(args.symbols),
        start=args.start,
        force_refresh=args.force_refresh,
    )
    print(reference.snapshot_id)


if __name__ == "__main__":
    main()
