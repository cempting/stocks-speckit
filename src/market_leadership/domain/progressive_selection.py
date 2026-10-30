from dataclasses import dataclass
from datetime import date
from typing import Literal

VisibleStage = Literal["sectors", "industries", "stocks", "stock_detail"]


@dataclass(frozen=True, slots=True)
class ProgressiveSelection:
    sector_id: str | None = None
    industry_id: str | None = None
    instrument_id: str | None = None
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
) -> ProgressiveSelection:
    if not catalog_fingerprint.strip():
        raise ValueError("catalog_fingerprint must not be empty")

    catalog_changed = (
        selection.catalog_fingerprint is not None
        and selection.catalog_fingerprint != catalog_fingerprint
    ) or (
        selection.membership_date is not None
        and selection.membership_date != membership_date
    )
    sector_id = (
        selection.sector_id if selection.sector_id in valid_sector_ids else None
    )
    industry_id = selection.industry_id
    if (
        sector_id is None
        or catalog_changed
        or industry_parent_by_id.get(industry_id or "") != sector_id
    ):
        industry_id = None

    instrument_id = selection.instrument_id
    if (
        industry_id is None
        or catalog_changed
        or instrument_industry_by_id.get(instrument_id or "") != industry_id
    ):
        instrument_id = None

    return ProgressiveSelection(
        sector_id=sector_id,
        industry_id=industry_id,
        instrument_id=instrument_id,
        catalog_fingerprint=catalog_fingerprint,
        membership_date=membership_date,
        observation_date=observation_date,
    )
