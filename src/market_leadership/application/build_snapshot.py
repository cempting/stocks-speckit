"""Publish a verified daily-history input snapshot from an explicit provider request."""

import argparse
import hashlib
import io
import json
import math
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Protocol, cast

import pandas as pd

from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.ports import (
    DataPointRequest,
    SnapshotReference,
    SnapshotRepository,
    WeeklyInputProvider,
    WeeklyMarketInputs,
    WeeklyPriceHistory,
    WeeklySnapshotRepository,
)
from market_leadership.application.request_market_data import RequestedMarketData
from market_leadership.domain.models import ClassificationLevel
from market_leadership.domain.proxies import DocumentedRepresentation, select_representation
from market_leadership.domain.rankings import (
    LeadershipCandidate,
    PriorWeeklyRank,
    RankIdentity,
    rank_leadership,
)
from market_leadership.domain.regimes import calculate_market_sentiment
from market_leadership.domain.relative_strength import (
    RelativeStrengthResult,
    calculate_relative_strength,
)
from market_leadership.infrastructure.provider_validation import canonicalize_daily_history
from market_leadership.infrastructure.snapshot_errors import SnapshotNotFound


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
        if history.empty or cast(pd.Timestamp, history.index[-1]).date() != required_session:
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


def _strength(
    entry: WeeklyPriceHistory,
    benchmark: WeeklyPriceHistory,
    as_of: date,
) -> RelativeStrengthResult:
    return calculate_relative_strength(
        entry.closes,
        benchmark.closes,
        as_of=as_of,
        currency=entry.currency,
        benchmark_currency=benchmark.currency,
        return_basis=entry.return_basis,
        benchmark_return_basis=benchmark.return_basis,
    )


def _composite_history(
    entry: WeeklyPriceHistory,
    benchmark: WeeklyPriceHistory,
    as_of: date,
) -> tuple[float, ...]:
    sessions = [
        cast(pd.Timestamp, session).date()
        for session in benchmark.closes.index
        if cast(pd.Timestamp, session).date() <= as_of
    ]
    composites: list[float] = []
    for session in sessions[-50:]:
        score = _strength(entry, benchmark, session).composite
        composites.append(score if score is not None else math.nan)
    return tuple(composites)


def _prior_ranks(
    repository: WeeklySnapshotRepository,
    market_id: str,
    level: str,
    as_of: date,
) -> dict[RankIdentity, PriorWeeklyRank]:
    try:
        reference = repository.load_latest_weekly(market_id, level)
    except SnapshotNotFound:
        return {}
    if reference.as_of >= as_of:
        return {}
    _, tables = repository.load_weekly(reference.snapshot_id)
    previous: dict[RankIdentity, PriorWeeklyRank] = {}
    rows = cast(list[dict[str, object]], tables["entries"].to_dict(orient="records"))
    for row in rows:
        score_raw, rank_raw = row["composite"], row["rank"]
        if score_raw is None or rank_raw is None:
            continue
        score = float(str(score_raw))
        rank = float(str(rank_raw))
        if math.isnan(score) or math.isnan(rank):
            continue
        if not math.isfinite(score) or not math.isfinite(rank) or rank < 1 or not rank.is_integer():
            raise ValueError("published prior weekly rank and score must be finite and valid")
        parent_value = row["parent_node_id"]
        if isinstance(parent_value, str):
            parent_id = parent_value
        elif parent_value is None or (isinstance(parent_value, float) and math.isnan(parent_value)):
            parent_id = None
        else:
            raise ValueError("published prior weekly parent identity is invalid")
        node_id = row["node_id"]
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("published prior weekly node identity is invalid")
        identity = (str(row["market_id"]), str(row["level"]), parent_id, node_id)
        previous[identity] = PriorWeeklyRank(score, int(rank))
    return previous


def _weekly_source(inputs: WeeklyMarketInputs) -> tuple[dict[str, str | None], ...]:
    content = json.dumps(
        {
            "market_id": inputs.market.market_id,
            "as_of": inputs.as_of.isoformat(),
            "classification_version": inputs.classification_version,
            "representation_version": inputs.representation_version,
            "nodes": [node.node_id for node in inputs.classifications],
            "proxies": [proxy.proxy_id for proxy in inputs.representations],
            "histories": {
                name: list(
                    zip(history.closes.index.astype(str), history.closes.tolist(), strict=True)
                )
                for name, history in sorted(inputs.histories.items())
            },
        },
        sort_keys=True,
    )
    return (
        {
            "source_id": inputs.source_id,
            "name": "Controlled weekly fixture",
            "dataset": "weekly-leadership-fixture",
            "version": inputs.classification_version,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "checksum": hashlib.sha256(content.encode()).hexdigest(),
            "license_label": "controlled acceptance fixture; not licensed live data",
        },
    )


def build_weekly_snapshot(
    provider: WeeklyInputProvider,
    repository: WeeklySnapshotRepository,
    *,
    snapshot_id: str,
    market_id: str,
    level: str,
    as_of: date,
) -> SnapshotReference:
    """Calculate and publish one completed local market's weekly classification level."""
    if level not in (ClassificationLevel.SECTOR, ClassificationLevel.INDUSTRY):
        raise ValueError("weekly level must be SECTOR or INDUSTRY")
    if provider.provider_id != "fixture":
        raise NotImplementedError("weekly provider source rights have not been verified")
    inputs = provider.weekly_inputs(market_id, as_of=as_of)
    if inputs.market.market_id != market_id or inputs.as_of > as_of:
        raise ValueError("weekly provider returned a different market or future observation")
    benchmark = inputs.histories.get(inputs.market.local_benchmark_id)
    if benchmark is None:
        raise ValueError("weekly local benchmark history is unavailable")
    sentiment = calculate_market_sentiment(
        pd.DataFrame({"close": benchmark.closes}), benchmark=inputs.market.local_benchmark_id
    )
    candidates: list[LeadershipCandidate] = []
    details: dict[
        str, tuple[DocumentedRepresentation | None, tuple[str, ...], RelativeStrengthResult | None]
    ] = {}
    for node in inputs.classifications:
        if node.level != level:
            continue
        proxy, reason = select_representation(
            inputs.representations,
            market_id=market_id,
            node_id=node.node_id,
            as_of=inputs.as_of,
        )
        extra_reasons = (reason,) if reason is not None else ()
        history = inputs.histories.get(proxy.instrument_id) if proxy is not None else None
        if history is None:
            if not extra_reasons:
                extra_reasons = ("MISSING_PROXY_HISTORY",)
            history = WeeklyPriceHistory(
                instrument_id=node.node_id,
                currency=benchmark.currency,
                return_basis=benchmark.return_basis,
                closes=pd.Series(dtype="float64", index=pd.DatetimeIndex([])),
                source_id=inputs.source_id,
                available_on=inputs.as_of,
            )
        strength = _strength(history, benchmark, inputs.as_of)
        parent_strength = None
        if level == ClassificationLevel.INDUSTRY:
            parent_proxy, _ = select_representation(
                inputs.representations,
                market_id=market_id,
                node_id=node.parent_node_id or "",
                as_of=inputs.as_of,
            )
            parent_history = (
                inputs.histories.get(parent_proxy.instrument_id)
                if parent_proxy is not None
                else None
            )
            if parent_history is not None:
                parent_strength = _strength(history, parent_history, inputs.as_of)
            if parent_strength is None or parent_strength.ending_on is None:
                extra_reasons += ("PARENT_COMPARISON_UNAVAILABLE",)
        candidates.append(
            LeadershipCandidate(
                market_id=market_id,
                level=level,
                parent_node_id=node.parent_node_id,
                node_id=node.node_id,
                name=node.name,
                strength=strength,
                composite_history=_composite_history(history, benchmark, inputs.as_of),
            )
        )
        details[node.node_id] = (proxy, extra_reasons, parent_strength)
    ranked = rank_leadership(
        candidates,
        previous=_prior_ranks(repository, market_id, level, inputs.as_of),
    )
    records: list[dict[str, object]] = []
    for row in ranked:
        proxy, extra_reasons, parent_strength = details[row.node_id]
        missing = [missing.value for missing in row.missing_reasons]
        missing.extend(extra_reasons)
        record: dict[str, object] = {
            "market_id": market_id,
            "level": level,
            "node_id": row.node_id,
            "parent_node_id": row.parent_node_id,
            "name": row.name,
            "proxy_id": proxy.proxy_id if proxy is not None else None,
            "proxy_type": proxy.proxy_type.value if proxy is not None else "NONE",
            "composition_basis": proxy.composition_basis if proxy is not None else None,
            "source_id": proxy.source_id if proxy is not None else inputs.source_id,
            "qualified": proxy.qualified if proxy is not None else False,
            "proxy_effective_from": proxy.effective_from if proxy is not None else None,
            "benchmark_id": inputs.market.local_benchmark_id,
            "market_regime": sentiment.regime.upper(),
            "calendar_id": inputs.market.calendar_id,
            "currency": inputs.market.base_currency,
            "return_basis": benchmark.return_basis,
            "as_of": inputs.as_of,
            "observation_date": row.strength.ending_on,
            "available_on": inputs.as_of,
            "coverage_start": (
                cast(pd.Timestamp, benchmark.closes.index[0]).date()
                if not benchmark.closes.empty
                else None
            ),
            "composite": row.strength.composite,
            "composite_average": row.composite_average,
            "prior_composite": row.prior_composite,
            "score_change": row.score_change,
            "prior_rank": row.prior_rank,
            "rank_change": row.rank_change,
            "rank": row.rank,
            "status": row.status.value if row.status is not None else None,
            "momentum": row.momentum.value if row.momentum is not None else None,
            "sufficiency": "SUFFICIENT" if row.rank is not None else "INSUFFICIENT",
            "missing_reasons": ",".join(dict.fromkeys(missing)),
        }
        for period in ("1w", "1m", "3m", "6m", "12m"):
            record[f"absolute_{period}"] = row.strength.absolute.get(period)
            record[f"relative_{period}"] = row.strength.relative.get(period)
            record[f"comparison_start_{period}"] = row.strength.starting_on.get(period)
            record[f"parent_relative_{period}"] = (
                parent_strength.relative.get(period) if parent_strength is not None else None
            )
        records.append(record)
    if not records:
        raise ValueError(f"no dated {level} classifications for {market_id}")
    return repository.publish_weekly(
        snapshot_id=snapshot_id,
        market_id=market_id,
        level=level,
        as_of=inputs.as_of,
        benchmark_id=inputs.market.local_benchmark_id,
        currency=inputs.market.base_currency,
        return_basis=benchmark.return_basis,
        classification_version=inputs.classification_version,
        representation_version=inputs.representation_version,
        ruleset_version="weekly-leadership-1",
        tables={"entries": pd.DataFrame.from_records(records)},
        sources=_weekly_source(inputs),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish daily input or calculated weekly snapshot"
    )
    parser.add_argument("--weekly", action="store_true")
    parser.add_argument("--provider", choices=("fixture", "massive", "yfinance"), required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument("--market", choices=("US", "JP", "GB"))
    parser.add_argument("--level", choices=("SECTOR", "INDUSTRY"))
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    from market_leadership.infrastructure.fixture_provider import FixtureProvider
    from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository

    if args.weekly:
        if args.provider != "fixture" or args.market is None or args.level is None:
            parser.error("weekly builds require --provider fixture, --market and --level")
        if args.start is not None or args.symbols is not None or args.force_refresh:
            parser.error("--start, --symbols and --force-refresh apply only to daily inputs")
        reference = build_weekly_snapshot(
            FixtureProvider(),
            ParquetSnapshotRepository(args.output),
            snapshot_id=args.snapshot_id,
            market_id=args.market,
            level=args.level,
            as_of=args.as_of,
        )
        print(reference.snapshot_id)
        return
    if args.start is None or args.symbols is None:
        parser.error("daily input builds require --start and --symbols")
    if args.market is not None or args.level is not None:
        parser.error("--market and --level apply only to weekly builds")

    from dataclasses import replace

    from market_leadership.bootstrap import build_market_data_request
    from market_leadership.config import load_settings

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
