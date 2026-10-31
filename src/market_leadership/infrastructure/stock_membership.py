from dataclasses import dataclass
from datetime import date
from typing import Literal

from market_leadership.config import Settings
from market_leadership.domain.catalog import CatalogError, Region, Scope, StockRow
from market_leadership.domain.stock_selection import MembershipCatalog, MembershipEntry
from market_leadership.infrastructure.catalog_files import CatalogSnapshot

MembershipLoadState = Literal["available", "empty_membership"]


@dataclass(frozen=True, slots=True)
class RegionMembershipResult:
    state: MembershipLoadState
    region: Region
    coverage_state: str
    coverage_description: str
    revision: str
    members: tuple[StockRow, ...]


def load_region_membership(
    snapshot: CatalogSnapshot,
    *,
    scope: Scope,
    industry_id: str,
    as_of: date,
) -> RegionMembershipResult:
    members = snapshot.members(scope, industry_id, as_of)
    region = next(item for item in snapshot.release.regions if item.region_id == scope.region_id)
    return RegionMembershipResult(
        "available" if members else "empty_membership",
        region,
        region.coverage_state,
        region.coverage_description,
        snapshot.cohort_fingerprint(scope, industry_id, as_of),
        members,
    )


def membership_entry(
    snapshot: CatalogSnapshot, row: StockRow, as_of: date
) -> MembershipEntry | None:
    symbol = row.provider_symbol_on(as_of)
    if symbol is None:
        return None
    nodes = snapshot.active_nodes(row.scope, as_of)
    industry = next((node for node in nodes if node.node_id == row.industry_id), None)
    if industry is None:
        raise CatalogError("inactive_node", "IndustryId")
    sector = next((node for node in nodes if node.node_id == industry.sector_id), None)
    listing = row.listing
    if (
        sector is None
        or listing is None
        or listing.period is None
        or listing.exchange is None
        or listing.currency is None
    ):
        raise CatalogError("incomplete_verified_listing", "ListingId")
    end_dates = tuple(end for end in (row.period.end, listing.period.end) if end is not None)
    return MembershipEntry(
        row.instrument_id,
        row.company_id,
        symbol,
        row.name,
        listing.exchange,
        listing.currency,
        sector.node_id,
        sector.name,
        industry.node_id,
        industry.name,
        max(row.period.start, listing.period.start),
        min(end_dates) if end_dates else None,
    )


def validate_live_access(catalog: MembershipCatalog, settings: Settings) -> None:
    if settings.provider_ids != ("yfinance",) or settings.default_provider != "yfinance":
        raise ValueError("Live grading requires a single yfinance source; review provider settings")
    if catalog.mode != "live":
        raise ValueError("A fixture catalog cannot authorize live requests")
    raise ValueError(
        "Independent JSON membership catalogs are retired; use the manifest-backed root tabs"
    )
