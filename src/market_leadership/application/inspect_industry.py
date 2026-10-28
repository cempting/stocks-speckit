"""Read industries under a selected dated local sector context."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from market_leadership.application.browse_scoreboard import read_weekly_board
from market_leadership.application.ports import WeeklySnapshotRepository
from market_leadership.infrastructure.snapshot_errors import SchemaMismatch


@dataclass(frozen=True, slots=True)
class IndustryInspection:
    market_id: str
    parent_sector: str
    parent_node_id: str
    benchmark_id: str
    currency: str
    return_basis: str
    as_of: date
    entries: pd.DataFrame
    unavailable_reason: str | None = None


def inspect_industry(
    repository: WeeklySnapshotRepository,
    *,
    market_id: str,
    sector_node_id: str,
) -> IndustryInspection:
    sector_board = read_weekly_board(repository, market_id, "SECTOR")
    if (
        sector_board.as_of is None
        or sector_board.benchmark_id is None
        or sector_board.currency is None
        or sector_board.return_basis is None
    ):
        raise ValueError(f"no sector snapshot is available for {market_id}")
    parent = sector_board.entries.loc[sector_board.entries["node_id"] == sector_node_id]
    if len(parent) != 1:
        raise ValueError(f"sector {sector_node_id} is not in {market_id}'s weekly snapshot")
    industry_board = read_weekly_board(repository, market_id, "INDUSTRY")
    if industry_board.as_of is not None and (
        industry_board.as_of != sector_board.as_of
        or industry_board.benchmark_id != sector_board.benchmark_id
        or industry_board.currency != sector_board.currency
        or industry_board.return_basis != sector_board.return_basis
    ):
        raise SchemaMismatch(
            industry_board.snapshot_id or market_id,
            "manifest",
            "industry context does not match the selected sector week",
        )
    entries = (
        industry_board.entries.loc[
            industry_board.entries["parent_node_id"] == sector_node_id
        ].copy()
        if not industry_board.entries.empty
        else pd.DataFrame()
    )
    return IndustryInspection(
        market_id=market_id,
        parent_sector=str(parent.iloc[0]["name"]),
        parent_node_id=sector_node_id,
        benchmark_id=sector_board.benchmark_id,
        currency=sector_board.currency,
        return_basis=sector_board.return_basis,
        as_of=sector_board.as_of,
        entries=entries,
        unavailable_reason=industry_board.unavailable_reason,
    )
