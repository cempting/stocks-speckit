from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

import pandas as pd


@dataclass(frozen=True, slots=True)
class DataPointRequest:
    data_point: str
    market_id: str
    identifiers: tuple[str, ...]
    frequency: str
    start: date
    end: date
    currency: str
    return_basis: str

    def __post_init__(self) -> None:
        if not self.data_point.strip() or not self.market_id.strip():
            raise ValueError("data point and market ID must not be empty")
        if not self.identifiers or any(not identifier.strip() for identifier in self.identifiers):
            raise ValueError("at least one non-empty identifier is required")
        if self.end < self.start:
            raise ValueError("request end date must not precede its start")
        if (
            len(self.currency) != 3
            or not self.currency.isascii()
            or not self.currency.isalpha()
            or not self.currency.isupper()
        ):
            raise ValueError("currency must be a three-letter ISO 4217 code")
        if not self.frequency.strip() or not self.return_basis.strip():
            raise ValueError("frequency and return basis must not be empty")


@dataclass(frozen=True, slots=True)
class ProviderCapability:
    data_point: str
    markets: frozenset[str]
    frequencies: frozenset[str]
    currencies: frozenset[str]
    return_bases: frozenset[str]
    identifiers: frozenset[str] | None = None

    def covers(self, request: DataPointRequest) -> bool:
        return (
            self.data_point == request.data_point
            and request.market_id in self.markets
            and request.frequency in self.frequencies
            and request.currency in self.currencies
            and request.return_basis in self.return_bases
            and (self.identifiers is None or set(request.identifiers).issubset(self.identifiers))
        )


class SelectionReason(StrEnum):
    CANONICAL_SCHEMA = "CANONICAL_SCHEMA"
    REQUESTED_COVERAGE = "REQUESTED_COVERAGE"
    CONFIGURED_PRIORITY = "CONFIGURED_PRIORITY"
    PROVIDER_ID = "PROVIDER_ID"


@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    provider_id: str
    provider: "MarketDataProvider"
    capability: ProviderCapability
    configured_priority: int
    canonical_schema_compatible: bool = True
    coverage_days: int = 0


@dataclass(frozen=True, slots=True)
class ProviderSelection:
    selected: ProviderCandidate
    alternatives: tuple[ProviderCandidate, ...]
    reason: SelectionReason


def select_provider(candidates: tuple[ProviderCandidate, ...]) -> ProviderSelection:
    if not candidates:
        raise ValueError("at least one provider candidate is required")
    ordered = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                not candidate.canonical_schema_compatible,
                -candidate.coverage_days,
                candidate.configured_priority,
                candidate.provider_id,
            ),
        )
    )
    first, *alternatives = ordered
    reason = SelectionReason.PROVIDER_ID
    if alternatives:
        second = alternatives[0]
        if first.canonical_schema_compatible != second.canonical_schema_compatible:
            reason = SelectionReason.CANONICAL_SCHEMA
        elif first.coverage_days != second.coverage_days:
            reason = SelectionReason.REQUESTED_COVERAGE
        elif first.configured_priority != second.configured_priority:
            reason = SelectionReason.CONFIGURED_PRIORITY
    return ProviderSelection(first, tuple(alternatives), reason)


class MarketDataProvider(Protocol):
    provider_id: str

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]: ...


class MarketDataProviderCatalog(Protocol):
    def discover(self, request: DataPointRequest) -> tuple[ProviderCandidate, ...]: ...


class SnapshotRepository(Protocol):
    def load_latest(self) -> "SnapshotReference": ...

    def load(self, snapshot_id: str) -> dict[str, pd.DataFrame]: ...

    def publish(
        self,
        *,
        snapshot_id: str,
        as_of: date,
        markets: tuple[str, ...],
        ruleset_version: str,
        tables: dict[str, pd.DataFrame],
        sources: tuple[dict[str, str | None], ...],
    ) -> "SnapshotReference": ...


@dataclass(frozen=True, slots=True)
class SnapshotReference:
    snapshot_id: str
    as_of: date
    manifest_checksum: str
    ruleset_version: str | None = None
    source_id: str | None = None
