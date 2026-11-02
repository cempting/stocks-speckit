from dataclasses import dataclass
from datetime import date
from typing import Literal

from market_data.catalog import CatalogSnapshot
from market_data.domain.catalog import CatalogError, Region, Scope, StockRow
from market_data.domain.stock_selection import MembershipCatalog, MembershipEntry
from market_leadership.config import Settings

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
    snapshot: CatalogSnapshot,
    row: StockRow,
    as_of: date,
    *,
    selected_node_id: str | None = None,
) -> MembershipEntry | None:
    symbol = row.provider_symbol_on(as_of)
    if symbol is None:
        return None
    selected_id = selected_node_id or row.industry_id
    effective_memberships = snapshot.memberships_for_instrument(
        row.scope, row.instrument_id, as_of
    )
    direct_path = next(
        (
            item
            for item in effective_memberships
            if item.membership.membership_id == row.membership_id
        ),
        None,
    )
    if direct_path is None:
        return None
    path_node_ids = tuple(node.node_id for node in direct_path.hierarchy)
    if selected_id not in path_node_ids:
        return None
    selected_index = path_node_ids.index(selected_id)
    if selected_index == 0:
        return None
    industry = direct_path.hierarchy[selected_index]
    sector = direct_path.hierarchy[0]
    listing = row.listing
    if (
        listing is None
        or listing.period is None
        or listing.exchange is None
        or listing.currency is None
    ):
        raise CatalogError("incomplete_verified_listing", "ListingId")
    effective_nodes = direct_path.hierarchy[: selected_index + 1]
    start_dates = (
        row.period.start,
        listing.period.start,
        *(node.period.start for node in effective_nodes),
    )
    end_dates = tuple(
        end
        for end in (
            row.period.end,
            listing.period.end,
            *(node.period.end for node in effective_nodes),
        )
        if end is not None
    )
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
        max(start_dates),
        min(end_dates) if end_dates else None,
    )


def membership_path_labels(
    snapshot: CatalogSnapshot,
    scope: Scope,
    instrument_id: str,
    as_of: date,
) -> tuple[str, ...]:
    return tuple(
        f"{' / '.join(node.name for node in path.hierarchy)} "
        f"[{path.membership.industry_id}]"
        for path in snapshot.memberships_for_instrument(scope, instrument_id, as_of)
    )


def validate_live_access(catalog: MembershipCatalog, settings: Settings) -> None:
    if settings.provider_ids != ("yfinance",) or settings.default_provider != "yfinance":
        raise ValueError("Live grading requires a single yfinance source; review provider settings")
    if catalog.mode != "live":
        raise ValueError("A fixture catalog cannot authorize live requests")
    raise ValueError(
        "Independent JSON membership catalogs are retired; use the manifest-backed root tabs"
    )
