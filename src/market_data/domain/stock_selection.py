from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MembershipEntry:
    instrument_id: str
    company_id: str | None
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
class StockIdentitySelection:
    instrument_id: str
    company_id: str | None
    region_id: str
    name: str
    listing_id: str | None
    symbol: str | None
    exchange: str | None
    currency: str | None


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


@dataclass(frozen=True)
class SelectionReconciliation:
    selected_ids: tuple[str, ...]
    cleared_ids: tuple[str, ...]
    reason: str | None


def reconcile_selection_with_reason(
    previous: SelectionContext | None,
    current: SelectionContext,
    selected: tuple[str, ...],
    valid_ids: tuple[str, ...],
) -> SelectionReconciliation:
    if previous is not None and previous.mode != current.mode:
        return SelectionReconciliation(
            (),
            tuple(dict.fromkeys(selected)),
            "Selections cleared because the evidence mode changed.",
        )
    valid = set(valid_ids)
    selected_ids = tuple(
        identifier
        for identifier in dict.fromkeys(selected)
        if identifier in valid
    )
    cleared_ids = tuple(
        identifier
        for identifier in dict.fromkeys(selected)
        if identifier not in valid
    )
    return SelectionReconciliation(
        selected_ids,
        cleared_ids,
        "Selections removed because they are not eligible in the current context."
        if cleared_ids
        else None,
    )


def reconcile_selection(
    previous: SelectionContext | None,
    current: SelectionContext,
    selected: tuple[str, ...],
    valid_ids: tuple[str, ...],
) -> tuple[str, ...]:
    return reconcile_selection_with_reason(previous, current, selected, valid_ids).selected_ids
