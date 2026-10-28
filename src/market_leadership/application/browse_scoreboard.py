"""Read a separate immutable weekly sector scoreboard for each selected market."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from market_leadership.application.ports import WeeklySnapshotRepository
from market_leadership.application.weekly_calendar import latest_completed_market_week
from market_leadership.infrastructure.snapshot_errors import SchemaMismatch, SnapshotNotFound


@dataclass(frozen=True, slots=True)
class WeeklyBoard:
    market_id: str
    level: str
    benchmark_id: str | None
    currency: str | None
    return_basis: str | None
    as_of: date | None
    snapshot_id: str | None
    entries: pd.DataFrame
    unavailable_reason: str | None = None
    regime: str | None = None
    calendar_id: str | None = None
    freshness: str | None = None


def read_weekly_board(
    repository: WeeklySnapshotRepository, market_id: str, level: str, *, as_of: date | None = None
) -> WeeklyBoard:
    try:
        reference = repository.load_latest_weekly(market_id, level)
    except SnapshotNotFound:
        return WeeklyBoard(
            market_id,
            level,
            None,
            None,
            None,
            None,
            None,
            pd.DataFrame(),
            "No calculated weekly snapshot is available",
        )
    manifest, tables = repository.load_weekly(reference.snapshot_id)
    if "entries" not in tables:
        raise SchemaMismatch(reference.snapshot_id, "entries", "weekly entries table is missing")
    if not {
        "market_id",
        "level",
        "node_id",
        "parent_node_id",
        "name",
        "rank",
        "market_regime",
        "calendar_id",
    }.issubset(tables["entries"].columns):
        raise SchemaMismatch(reference.snapshot_id, "entries", "weekly entry fields are missing")
    entries = (
        tables["entries"]
        .sort_values(["rank", "name"], kind="stable", na_position="last")
        .reset_index(drop=True)
    )
    regimes = entries["market_regime"].unique()
    if len(regimes) != 1:
        raise SchemaMismatch(reference.snapshot_id, "entries", "market regime must be unambiguous")
    calendars = entries["calendar_id"].unique()
    if len(calendars) != 1:
        raise SchemaMismatch(
            reference.snapshot_id, "entries", "market calendar must be unambiguous"
        )
    calendar_id = str(calendars[0])
    if as_of is not None and reference.as_of > as_of:
        raise SchemaMismatch(reference.snapshot_id, "manifest", "snapshot date is after evaluation")
    freshness = (
        (
            "CURRENT"
            if reference.as_of == latest_completed_market_week(calendar_id, as_of)
            else "STALE"
        )
        if as_of is not None
        else None
    )
    return WeeklyBoard(
        market_id=market_id,
        level=level,
        benchmark_id=manifest["benchmark_id"],
        currency=manifest["currency"],
        return_basis=manifest["return_basis"],
        as_of=reference.as_of,
        snapshot_id=reference.snapshot_id,
        entries=entries,
        regime=str(regimes[0]),
        calendar_id=calendar_id,
        freshness=freshness,
    )


def browse_weekly_scoreboard(
    repository: WeeklySnapshotRepository,
    selected_market_ids: tuple[str, ...],
    *,
    as_of: date | None = None,
) -> tuple[WeeklyBoard, ...]:
    if not selected_market_ids or len(set(selected_market_ids)) != len(selected_market_ids):
        raise ValueError("select one or more distinct markets")
    return tuple(
        read_weekly_board(repository, market, "SECTOR", as_of=as_of)
        for market in selected_market_ids
    )
