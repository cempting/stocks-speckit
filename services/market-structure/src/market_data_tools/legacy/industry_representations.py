"""Review worklists for explicitly selected legacy SQLite stores."""

from datetime import date

from market_data.domain.industry_representations import RepresentationReviewItem
from market_data_tools.legacy.region_database import RegionDatabase


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
