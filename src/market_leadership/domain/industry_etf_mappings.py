"""Reviewed ETF mappings for industry momentum rows."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ClassificationEtfMapping:
    region_id: str
    classification_id: str
    node_id: str
    symbol: str
    name: str
    effective_from: date
    effective_to: date | None = None
    approved: bool = True

    def __post_init__(self) -> None:
        for field in ("region_id", "classification_id", "node_id", "symbol", "name"):
            value = getattr(self, field)
            if not value.strip():
                raise ValueError(f"{field.replace('_', ' ')} is required")
        object.__setattr__(self, "region_id", self.region_id.strip().upper())
        object.__setattr__(self, "classification_id", self.classification_id.strip().upper())
        object.__setattr__(self, "node_id", self.node_id.strip())
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective end precedes start")

    def active_on(self, as_of: date) -> bool:
        return (
            self.approved
            and self.effective_from <= as_of
            and (self.effective_to is None or as_of <= self.effective_to)
        )


def mapping_for(
    mappings: tuple[ClassificationEtfMapping, ...],
    *,
    region_id: str,
    classification_id: str,
    node_id: str,
    as_of: date,
) -> ClassificationEtfMapping | None:
    matches = tuple(
        mapping
        for mapping in mappings
        if mapping.region_id == region_id.upper()
        and mapping.classification_id == classification_id.upper()
        and mapping.node_id == node_id
        and mapping.active_on(as_of)
    )
    if len(matches) > 1:
        raise ValueError(f"multiple active ETF mappings for {node_id}")
    return matches[0] if matches else None
