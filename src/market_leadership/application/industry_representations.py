"""Region-scoped review worklist and effective representation resolution."""

from datetime import date

from market_data.catalog import CatalogSnapshot
from market_data.domain.catalog import Scope
from market_data.domain.industry_representations import (
    RepresentationReviewItem,
    ReviewedRepresentation,
)


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
