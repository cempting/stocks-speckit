"""Dated, documented classification representations."""

from dataclasses import dataclass
from datetime import date

from market_leadership.domain.models import ProxyType


@dataclass(frozen=True, slots=True)
class DocumentedRepresentation:
    market_id: str
    node_id: str
    proxy_id: str
    proxy_type: ProxyType
    instrument_id: str
    composition_basis: str
    source_id: str
    qualified: bool
    effective_from: date
    effective_to: date | None
    member_ids: tuple[str, ...] = ()
    qualification_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in (
            "market_id",
            "node_id",
            "proxy_id",
            "instrument_id",
            "composition_basis",
            "source_id",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"{field.replace('_', ' ')} is required")
        if self.proxy_type is ProxyType.NONE:
            raise ValueError("NONE is not a documented representation")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective end precedes start")
        if self.proxy_type is ProxyType.EQUAL_WEIGHT_BASKET:
            if len(set(self.member_ids)) < 5:
                raise ValueError("equal-weight basket needs five distinct members")
        elif self.member_ids:
            raise ValueError("only a constituent basket can specify members")


def select_representation(
    representations: tuple[DocumentedRepresentation, ...],
    *,
    market_id: str,
    node_id: str,
    as_of: date,
) -> tuple[DocumentedRepresentation | None, str | None]:
    eligible = [
        item
        for item in representations
        if item.market_id == market_id
        and item.node_id == node_id
        and item.qualified
        and item.effective_from <= as_of
        and (item.effective_to is None or as_of <= item.effective_to)
    ]
    if len(eligible) > 1:
        raise ValueError(f"multiple qualified representations for {market_id}/{node_id}")
    if not eligible:
        return None, "NO_QUALIFIED_REPRESENTATION"
    return eligible[0], None
