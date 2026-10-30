from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MembershipEntry:
    instrument_id: str
    company_id: str
    symbol: str
    name: str
    exchange: str
    currency: str
    sector_id: str
    sector_name: str
    industry_id: str
    industry_name: str
    effective_from: date
    effective_to: date | None

    def active_on(self, observed_on: date) -> bool:
        return self.effective_from <= observed_on and (
            self.effective_to is None or observed_on <= self.effective_to
        )


@dataclass(frozen=True)
class MembershipCatalog:
    observed_on: date
    source_id: str
    classification: str
    mode: str
    coverage: str
    approval_reference: str
    entries: tuple[MembershipEntry, ...]
    fingerprint: str


@dataclass(frozen=True)
class SelectionContext:
    mode: str
    sector_id: str
    industry_id: str
    catalog_fingerprint: str
    cutoff: str


def reconcile_selection(
    previous: SelectionContext | None,
    current: SelectionContext,
    selected: tuple[str, ...],
    valid_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if previous is not None and (
        previous.mode != current.mode
        or previous.industry_id != current.industry_id
        or previous.sector_id != current.sector_id
        or previous.cutoff != current.cutoff
    ):
        return ()
    return tuple(dict.fromkeys(identifier for identifier in selected if identifier in valid_ids))
