"""Region-scoped review worklist and effective representation resolution."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from market_leadership.domain.catalog import Scope
from market_leadership.domain.industry_representations import ReviewedRepresentation
from market_leadership.infrastructure.catalog_files import CatalogSnapshot
from market_leadership.infrastructure.region_database import RegionDatabase


@dataclass(frozen=True, slots=True)
class RepresentationReviewItem:
    region_id: str
    classification_id: str
    node_id: str
    name: str
    node_type: str
    sector_id: str
    status: Literal["etf", "basket", "not_covered", "invalid"]
    representation: ReviewedRepresentation | None


def snapshot_representation_worklist(
    snapshot: CatalogSnapshot,
    *,
    scope: Scope,
    as_of: date,
    only_uncovered: bool = False,
) -> tuple[RepresentationReviewItem, ...]:
    listings = {listing.listing_id: listing for listing in snapshot.listings}
    results: list[RepresentationReviewItem] = []
    for node in sorted(
        snapshot.active_nodes(scope, as_of), key=lambda item: (item.name, item.node_id)
    ):
        etfs = tuple(
            mapping
            for mapping in snapshot.representations
            if mapping.scope == scope
            and mapping.node_id == node.node_id
            and mapping.period.active_on(as_of)
        )
        eligible_etfs = tuple(
            mapping for mapping in etfs if listings[mapping.listing_id].active_on(as_of)
        )
        baskets = tuple(
            basket
            for basket in snapshot.baskets
            if basket.scope == scope
            and basket.node_id == node.node_id
            and basket.period.active_on(as_of)
        )
        representation: ReviewedRepresentation | None = None
        if eligible_etfs or (etfs and not baskets):
            mapping = (eligible_etfs or etfs)[0]
            listing = listings[mapping.listing_id]
            representation = ReviewedRepresentation(
                mapping.representation_id,
                node.node_id,
                "etf",
                node.name,
                mapping.source_id,
                mapping.approval_reference,
                mapping.period.start,
                mapping.period.end,
                listing.provider_symbol,
                reason=None if eligible_etfs else "Unavailable reviewed listing on selected date",
            )
        elif baskets:
            basket = baskets[0]
            representation = ReviewedRepresentation(
                basket.representation_id,
                node.node_id,
                "basket",
                basket.name,
                basket.source_id,
                basket.approval_reference,
                basket.period.start,
                basket.period.end,
                constituents=basket.constituents,
            )
            inventory = {item.listing.listing_id: item.listing for item in snapshot.inventory}
            inventory.update(listings)
            if any(
                not inventory[constituent.listing_id].active_on(as_of)
                for constituent in basket.constituents
            ):
                representation = ReviewedRepresentation(
                    basket.representation_id,
                    node.node_id,
                    "basket",
                    basket.name,
                    basket.source_id,
                    basket.approval_reference,
                    basket.period.start,
                    basket.period.end,
                    constituents=basket.constituents,
                    reason="Unavailable reviewed basket listing on selected date",
                )
        status = (
            "not_covered"
            if representation is None
            else "invalid"
            if representation.invalid_reason
            else representation.kind
        )
        if only_uncovered and status in ("etf", "basket"):
            continue
        results.append(
            RepresentationReviewItem(
                scope.region_id,
                scope.classification_id,
                node.node_id,
                node.name,
                node.node_type,
                node.sector_id,
                status,
                representation,
            )
        )
    return tuple(results)


def representation_worklist(
    database: RegionDatabase,
    *,
    region_id: str,
    classification_id: str,
    as_of: date,
    only_uncovered: bool = False,
) -> tuple[RepresentationReviewItem, ...]:
    if not database.is_initialized():
        raise ValueError(f"Regional database is missing or invalid: {database.path}")
    region = database.get_region(region_id)
    if region is None or region.status != "active":
        raise ValueError(f"No active reviewed region: {region_id}")
    etfs = database.get_reviewed_industry_etfs(region_id, classification_id, as_of=as_of)
    baskets = database.get_stock_baskets(region_id, classification_id, as_of=as_of)
    results: list[RepresentationReviewItem] = []
    for sector in database.get_sectors(region_id, classification_id, as_of=as_of):
        for node in database.get_industries(
            region_id,
            classification_id,
            sector.sector_id,
            as_of=as_of,
        ):
            node_etfs = tuple(item for item in etfs if item.node_id == node.industry_id)
            node_baskets = tuple(item for item in baskets if item.node_id == node.industry_id)
            valid_etfs = tuple(item for item in node_etfs if not item.invalid_reason)
            valid_baskets = tuple(item for item in node_baskets if not item.invalid_reason)
            if len(valid_etfs) > 1 or (not valid_etfs and len(valid_baskets) > 1):
                raise ValueError(f"Multiple active reviewed representations for {node.industry_id}")
            representation = next(
                iter(valid_etfs or valid_baskets or node_etfs or node_baskets),
                None,
            )
            status = (
                "not_covered"
                if representation is None
                else "invalid"
                if representation.invalid_reason
                else representation.kind
            )
            if only_uncovered and status in ("etf", "basket"):
                continue
            results.append(
                RepresentationReviewItem(
                    region_id,
                    classification_id,
                    node.industry_id,
                    node.name,
                    node.node_type,
                    node.sector_id,
                    status,
                    representation,
                )
            )
    return tuple(results)
