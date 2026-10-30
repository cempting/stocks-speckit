from dataclasses import dataclass
from datetime import date
from typing import Literal

VisibleStage = Literal["sectors", "industries", "stocks", "stock_detail"]


@dataclass(frozen=True, slots=True)
class ProgressiveSelection:
    sector_id: str | None = None
    industry_id: str | None = None
    instrument_id: str | None = None
    region_id: str | None = None
    database_revision: str | None = None
    catalog_fingerprint: str | None = None
    membership_date: date | None = None
    observation_date: date | None = None

    @property
    def visible_stage(self) -> VisibleStage:
        if self.instrument_id is not None:
            return "stock_detail"
        if self.industry_id is not None:
            return "stocks"
        if self.sector_id is not None:
            return "industries"
        return "sectors"


def reconcile_progressive_selection(
    selection: ProgressiveSelection,
    *,
    valid_sector_ids: tuple[str, ...],
    industry_parent_by_id: dict[str, str],
    instrument_industry_by_id: dict[str, str],
    catalog_fingerprint: str,
    membership_date: date,
    observation_date: date,
    region_id: str | None = None,
    database_revision: str | None = None,
) -> ProgressiveSelection:
    if not catalog_fingerprint.strip():
        raise ValueError("catalog_fingerprint must not be empty")

    catalog_changed = (
        selection.catalog_fingerprint is not None
        and selection.catalog_fingerprint != catalog_fingerprint
    ) or (selection.membership_date is not None and selection.membership_date != membership_date)
    database_changed = (
        selection.database_revision is not None
        and database_revision is not None
        and selection.database_revision != database_revision
    )
    region_changed = (
        selection.region_id is not None
        and region_id is not None
        and region_id != selection.region_id
    )
    sector_id = (
        selection.sector_id
        if selection.sector_id in valid_sector_ids and not region_changed
        else None
    )
    industry_id = selection.industry_id
    if (
        sector_id is None
        or region_changed
        or catalog_changed
        or database_changed
        or industry_parent_by_id.get(industry_id or "") != sector_id
    ):
        industry_id = None

    instrument_id = selection.instrument_id
    if (
        industry_id is None
        or catalog_changed
        or database_changed
        or instrument_industry_by_id.get(instrument_id or "") != industry_id
    ):
        instrument_id = None

    return ProgressiveSelection(
        sector_id=sector_id,
        industry_id=industry_id,
        instrument_id=instrument_id,
        region_id=region_id if region_id is not None else selection.region_id,
        database_revision=(
            database_revision if database_revision is not None else selection.database_revision
        ),
        catalog_fingerprint=catalog_fingerprint,
        membership_date=membership_date,
        observation_date=observation_date,
    )
