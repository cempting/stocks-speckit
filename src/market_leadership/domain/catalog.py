"""SQL-independent identities, temporal evidence and reviewed catalog validation."""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal, cast

from market_leadership.domain.industry_representations import (
    BasketConstituent,
    validate_weights,
)
from market_leadership.domain.local_etf_evidence import (
    CatalogObservation,
    CollectionRun,
    Evidence,
    ResourceInspection,
    ReviewDecision,
    integer_field,
    optional_text,
    text_field,
)

type NodeType = Literal["sector", "industry", "sub_industry"]
type ArtifactRole = Literal[
    "hierarchy",
    "stocks",
    "etf_listings",
    "sector_etfs",
    "industry_etfs",
    "sub_industry_etfs",
    "benchmarks",
    "audit",
    "migration_archive",
]
type BenchmarkPurpose = Literal["sp500_comparison", "market_sentiment"]
type CatalogType = Literal[
    "industry",
    "sector_context",
    "index_context",
    "commodity_context",
]
ARTIFACT_ROLES = frozenset(
    {
        "hierarchy",
        "stocks",
        "etf_listings",
        "sector_etfs",
        "industry_etfs",
        "sub_industry_etfs",
        "benchmarks",
        "audit",
        "migration_archive",
    }
)


class CatalogError(ValueError):
    def __init__(self, code: str, field: str) -> None:
        self.code = code
        self.field = field
        super().__init__(f"{code}: {field}")


def require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise CatalogError("invalid_text", field)


def require_date(value: object, field: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise CatalogError("invalid_date", field)


def parse_date(value: str, field: str) -> date:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise CatalogError("invalid_date", field)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise CatalogError("invalid_date", field) from None


def parse_utc(value: str, field: str) -> datetime:
    if (
        re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
            r"(?:\.[0-9]+)?(?:Z|\+00:00)",
            value,
        )
        is None
    ):
        raise CatalogError("invalid_utc", field)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise CatalogError("invalid_utc", field) from None
    require_utc(parsed, field, nullable=False)
    return parsed


def require_hash(value: object, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise CatalogError("invalid_sha256", field)


def require_relative_path(value: str, field: str) -> None:
    require_text(value, field)
    if (
        PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).drive
        or "\\" in value
        or ".." in PurePosixPath(value).parts
        or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value)
    ):
        raise CatalogError("unsafe_path", field)


def require_tuple(value: object, field: str) -> None:
    if not isinstance(value, tuple):
        raise CatalogError("mutable_records", field)


def require_utc(value: object, field: str, *, nullable: bool = True) -> None:
    if value is None and not nullable:
        raise CatalogError("invalid_utc", field)
    if value is not None and (not isinstance(value, datetime) or value.utcoffset() != timedelta(0)):
        raise CatalogError("invalid_utc", field)


@dataclass(frozen=True, slots=True)
class Period:
    start: date
    end: date | None = None

    def __post_init__(self) -> None:
        require_date(self.start, "EffectiveFrom")
        if self.end is not None:
            require_date(self.end, "EffectiveTo")
            if self.end < self.start:
                raise CatalogError("reversed_period", "EffectiveTo")

    @property
    def last(self) -> date:
        return self.end if self.end is not None else date.max

    def active_on(self, as_of: date) -> bool:
        require_date(as_of, "as_of")
        return self.start <= as_of <= self.last

    def overlaps(self, other: "Period") -> bool:
        return self.start <= other.last and other.start <= self.last

    def covers(self, other: "Period") -> bool:
        return self.start <= other.start and self.last >= other.last


@dataclass(frozen=True, slots=True)
class Scope:
    region_id: str
    classification_id: str
    classification_version: str

    def __post_init__(self) -> None:
        for field in ("region_id", "classification_id", "classification_version"):
            require_text(getattr(self, field), field)
        if self.classification_version.casefold() == "latest":
            raise CatalogError("unreviewed_version", "classification_version")


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    source_id: str
    source_type: Literal["local_file", "live"]
    description: str
    coverage: str | None
    authority: str | None
    approval_reference: str | None
    reviewed_at: date | None

    def __post_init__(self) -> None:
        require_text(self.source_id, "source_id")
        require_text(self.description, "description")
        if self.source_type not in ("local_file", "live"):
            raise CatalogError("invalid_source_type", "source_type")
        for field in ("coverage", "authority", "approval_reference"):
            value = getattr(self, field)
            if value is not None and not isinstance(value, str):
                raise CatalogError("invalid_text", field)
        if self.reviewed_at is not None:
            require_date(self.reviewed_at, "reviewed_at")

    def require_approval(self, reference: str) -> None:
        if (
            self.source_type != "local_file"
            or self.reviewed_at is None
            or not reference.strip()
            or reference != self.approval_reference
        ):
            raise CatalogError("source_approval", "ApprovalReference")


@dataclass(frozen=True, slots=True)
class Classification:
    scope: Scope
    scheme_name: str
    source_id: str
    approval_reference: str
    period: Period

    def __post_init__(self) -> None:
        for field in ("scheme_name", "source_id", "approval_reference"):
            require_text(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class Region:
    region_id: str
    name: str
    status: Literal["active", "inactive"]
    coverage_state: Literal["complete", "partial", "unverified"]
    coverage_description: str
    coverage_as_of: date
    last_reviewed_at: date | None
    classifications: tuple[Classification, ...]

    def __post_init__(self) -> None:
        for field in ("region_id", "name", "coverage_description"):
            require_text(getattr(self, field), field)
        require_date(self.coverage_as_of, "coverage_as_of")
        if self.last_reviewed_at is not None:
            require_date(self.last_reviewed_at, "last_reviewed_at")
        if self.status not in ("active", "inactive"):
            raise CatalogError("invalid_status", "status")
        if self.coverage_state not in ("complete", "partial", "unverified"):
            raise CatalogError("invalid_coverage", "coverage_state")
        require_tuple(self.classifications, "classifications")
        if any(c.scope.region_id != self.region_id for c in self.classifications):
            raise CatalogError("scope_mismatch", "classifications")
        for i, current in enumerate(self.classifications):
            if any(current.period.overlaps(other.period) for other in self.classifications[:i]):
                raise CatalogError("ambiguous_classification", "classifications")


@dataclass(frozen=True, slots=True)
class Artifact:
    artifact_id: str
    role: ArtifactRole
    path: str
    sha256: str
    required: bool
    row_count: int
    region_id: str | None
    classification_id: str | None
    classification_version: str | None

    def __post_init__(self) -> None:
        require_text(self.artifact_id, "artifact_id")
        require_relative_path(self.path, "path")
        require_hash(self.sha256, "sha256")
        if self.role not in ARTIFACT_ROLES or self.required is not True:
            raise CatalogError("invalid_artifact", "role/required")
        if type(self.row_count) is not int or self.row_count < 0:
            raise CatalogError("invalid_count", "row_count")
        for field in ("region_id", "classification_id", "classification_version"):
            value = getattr(self, field)
            if value is not None:
                require_text(value, field)
        if (self.classification_id is None) != (self.classification_version is None):
            raise CatalogError("incomplete_scope", "classification_version")
        if self.role == "stocks" and self.region_id is None:
            raise CatalogError("missing_region", "region_id")


@dataclass(frozen=True, slots=True)
class ParentRelease:
    release_id: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        require_text(self.release_id, "release_id")
        require_hash(self.manifest_sha256, "manifest_sha256")


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    release_id: str
    manifest_path: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        require_text(self.release_id, "release_id")
        require_relative_path(self.manifest_path, "manifest_path")
        require_hash(self.manifest_sha256, "manifest_sha256")


@dataclass(frozen=True, slots=True)
class ResearchCatalog:
    path: str
    name: str
    catalog_type: CatalogType

    def __post_init__(self) -> None:
        require_relative_path(self.path, "catalog.path")
        require_text(self.name, "catalog.name")
        if self.catalog_type not in (
            "industry",
            "sector_context",
            "index_context",
            "commodity_context",
        ):
            raise CatalogError("invalid_catalog_type", "catalog_type")


@dataclass(frozen=True, slots=True)
class ResearchSource:
    resource_id: str
    root: str
    required: bool
    catalogs: tuple[ResearchCatalog, ...]

    def __post_init__(self) -> None:
        require_text(self.resource_id, "resource_id")
        require_text(self.root, "root")
        require_tuple(self.catalogs, "catalogs")
        if self.required is not False:
            raise CatalogError("invalid_research_source", "required/catalogs")
        identities = {(catalog.path, catalog.name) for catalog in self.catalogs}
        if len(identities) != len(self.catalogs):
            raise CatalogError("duplicate_catalog", "catalogs")


@dataclass(frozen=True, slots=True)
class CatalogRelease:
    release_id: str
    created_at: datetime
    parent_release: ParentRelease | None
    catalog_revision: str
    regions: tuple[Region, ...]
    evidence_sources: tuple[EvidenceSource, ...]
    artifacts: tuple[Artifact, ...]
    research_sources: tuple[ResearchSource, ...]

    def __post_init__(self) -> None:
        require_text(self.release_id, "release_id")
        require_utc(self.created_at, "created_at", nullable=False)
        require_hash(self.catalog_revision, "catalog_revision")
        for field in ("regions", "evidence_sources", "artifacts", "research_sources"):
            require_tuple(getattr(self, field), field)
        for records, key in (
            (self.regions, "region_id"),
            (self.evidence_sources, "source_id"),
            (self.artifacts, "artifact_id"),
            (self.research_sources, "resource_id"),
        ):
            identities = [getattr(record, key) for record in records]
            if len(set(identities)) != len(identities):
                raise CatalogError("duplicate_identity", key)
        if len({a.path for a in self.artifacts}) != len(self.artifacts):
            raise CatalogError("duplicate_path", "artifacts")
        if sum(a.role == "audit" for a in self.artifacts) != 1:
            raise CatalogError("invalid_audit_count", "artifacts")
        known_regions = {region.region_id for region in self.regions}
        known_scopes = {c.scope for region in self.regions for c in region.classifications}
        for artifact in self.artifacts:
            if artifact.region_id is not None and artifact.region_id not in known_regions:
                raise CatalogError("unknown_region", "artifacts")
            if artifact.classification_id is not None:
                if artifact.region_id is None or artifact.classification_version is None:
                    raise CatalogError("incomplete_scope", "artifacts")
                scope = Scope(
                    artifact.region_id, artifact.classification_id, artifact.classification_version
                )
                if scope not in known_scopes:
                    raise CatalogError("unknown_scope", "artifacts")
        for region in self.regions:
            if region.status != "active":
                continue
            stocks = [
                a for a in self.artifacts if a.role == "stocks" and a.region_id == region.region_id
            ]
            if len(stocks) != 1:
                raise CatalogError("invalid_stock_artifact_count", "artifacts")
            for role in ARTIFACT_ROLES - {"stocks", "audit", "migration_archive"}:
                if not any(
                    a.role == role and a.region_id in (None, region.region_id)
                    for a in self.artifacts
                ):
                    raise CatalogError("missing_role", role)


@dataclass(frozen=True, slots=True)
class HierarchyNode:
    scope: Scope
    node_id: str
    node_type: NodeType
    name: str
    sector_id: str
    parent_industry_id: str | None
    period: Period
    source_id: str | None
    approval_reference: str | None
    approval_origin: Literal["own", "classification_inherited"]

    def __post_init__(self) -> None:
        for field in ("node_id", "name", "sector_id"):
            require_text(getattr(self, field), field)
        if self.node_type not in ("sector", "industry", "sub_industry"):
            raise CatalogError("invalid_node_type", "NodeType")
        if self.node_type == "sector" and self.sector_id != self.node_id:
            raise CatalogError("invalid_sector_reference", "SectorId")
        if self.node_type == "sub_industry":
            require_text(self.parent_industry_id, "ParentIndustryId")
        elif self.parent_industry_id is not None:
            raise CatalogError("unexpected_parent", "ParentIndustryId")
        if self.approval_origin == "own":
            require_text(self.source_id, "SourceId")
            require_text(self.approval_reference, "ApprovalReference")
        elif self.approval_origin == "classification_inherited":
            if self.source_id is not None or self.approval_reference is not None:
                raise CatalogError("unexpected_own_review", "ApprovalOrigin")
        else:
            raise CatalogError("invalid_approval_origin", "ApprovalOrigin")


@dataclass(frozen=True, slots=True)
class Listing:
    listing_id: str
    instrument_id: str
    region_id: str
    instrument_type: Literal["stock", "etf"] | None
    ticker: str | None
    provider_symbol: str | None
    name: str | None
    exchange: str | None
    currency: str | None
    is_primary: bool | None
    resolution_state: Literal["verified", "unverified"]
    period: Period | None
    source_id: str | None
    approval_reference: str | None

    def __post_init__(self) -> None:
        for field in ("listing_id", "instrument_id", "region_id"):
            require_text(getattr(self, field), field)
        if self.instrument_type not in ("stock", "etf", None):
            raise CatalogError("invalid_instrument_type", "InstrumentType")
        if self.resolution_state not in ("verified", "unverified"):
            raise CatalogError("invalid_listing_state", "ListingResolutionState")
        if self.is_primary is not None and type(self.is_primary) is not bool:
            raise CatalogError("invalid_boolean", "IsPrimary")
        for field in (
            "ticker",
            "provider_symbol",
            "name",
            "exchange",
            "currency",
            "source_id",
            "approval_reference",
        ):
            value = getattr(self, field)
            if value is not None:
                require_text(value, field)
        if self.currency is not None and re.fullmatch(r"[A-Z]{3}", self.currency) is None:
            raise CatalogError("invalid_currency", "Currency")
        if self.resolution_state == "verified":
            for field in (
                "ticker",
                "provider_symbol",
                "exchange",
                "currency",
                "source_id",
                "approval_reference",
            ):
                require_text(getattr(self, field), field)
            if self.period is None or self.is_primary is None:
                raise CatalogError("incomplete_verified_listing", "period/IsPrimary")

    @property
    def eligible(self) -> bool:
        return self.resolution_state == "verified" and self.period is not None

    def active_on(self, as_of: date) -> bool:
        return self.eligible and self.period is not None and self.period.active_on(as_of)


@dataclass(frozen=True, slots=True)
class StockRow:
    row_id: str
    membership_id: str
    scope: Scope
    instrument_id: str
    company_id: str | None
    name: str
    industry_id: str
    sub_industry_id: str | None
    resolution_state: Literal["identified", "placeholder"]
    period: Period
    source_id: str
    approval_reference: str
    membership_review_state: Literal["reviewed"]
    listing: Listing | None

    def __post_init__(self) -> None:
        for field in (
            "row_id",
            "membership_id",
            "instrument_id",
            "name",
            "industry_id",
            "source_id",
            "approval_reference",
        ):
            require_text(getattr(self, field), field)
        for field in ("company_id", "sub_industry_id"):
            value = getattr(self, field)
            if value is not None:
                require_text(value, field)
        if self.resolution_state not in ("identified", "placeholder"):
            raise CatalogError("invalid_instrument_state", "ResolutionState")
        if self.membership_review_state != "reviewed":
            raise CatalogError("unreviewed_membership", "MembershipReviewState")
        if self.listing is not None:
            if self.listing.instrument_type == "etf":
                raise CatalogError("etf_stock_membership", "InstrumentId")
            if (self.listing.instrument_id, self.listing.region_id) != (
                self.instrument_id,
                self.scope.region_id,
            ):
                raise CatalogError("listing_identity_mismatch", "ListingId")
            if self.listing.eligible and self.resolution_state != "identified":
                raise CatalogError("unidentified_instrument", "ResolutionState")

    def provider_symbol_on(self, as_of: date) -> str | None:
        if (
            self.resolution_state != "identified"
            or not self.period.active_on(as_of)
            or self.listing is None
            or self.listing.is_primary is not True
            or not self.listing.active_on(as_of)
        ):
            return None
        return self.listing.provider_symbol


@dataclass(frozen=True, slots=True)
class EtfRepresentation:
    representation_id: str
    scope: Scope
    node_id: str
    node_type: NodeType
    listing_id: str
    period: Period
    source_id: str
    approval_reference: str
    suitability_reference: str
    candidate_review_id: str | None

    def __post_init__(self) -> None:
        for field in (
            "representation_id",
            "node_id",
            "listing_id",
            "source_id",
            "approval_reference",
            "suitability_reference",
        ):
            require_text(getattr(self, field), field)
        if self.node_type not in ("sector", "industry", "sub_industry"):
            raise CatalogError("invalid_node_type", "node_type")
        if self.candidate_review_id is not None:
            require_text(self.candidate_review_id, "CandidateReviewId")


@dataclass(frozen=True, slots=True)
class Benchmark:
    benchmark_id: str
    region_id: str
    purpose: BenchmarkPurpose
    label: str
    listing_id: str
    period: Period
    source_id: str
    approval_reference: str

    def __post_init__(self) -> None:
        for field in (
            "benchmark_id",
            "region_id",
            "label",
            "listing_id",
            "source_id",
            "approval_reference",
        ):
            require_text(getattr(self, field), field)
        if self.purpose not in ("sp500_comparison", "market_sentiment"):
            raise CatalogError("invalid_benchmark_purpose", "Purpose")


@dataclass(frozen=True, slots=True)
class Basket:
    representation_id: str
    scope: Scope
    node_id: str
    name: str
    period: Period
    source_id: str
    approval_reference: str
    constituents: tuple[BasketConstituent, ...]
    review_state: Literal["reviewed"]

    def __post_init__(self) -> None:
        for field in ("representation_id", "node_id", "name", "source_id", "approval_reference"):
            require_text(getattr(self, field), field)
        require_tuple(self.constituents, "constituents")
        if self.review_state != "reviewed":
            raise CatalogError("unreviewed_basket", "review_state/constituents")
        try:
            validate_weights(self.constituents)
        except ValueError as error:
            raise CatalogError("invalid_basket_weights", "constituents") from error


@dataclass(frozen=True, slots=True)
class BasketDefinition:
    representation_id: str
    scope: Scope
    node_id: str
    name: str
    period: Period
    source_id: str
    approval_reference: str
    review_state: Literal["reviewed"]

    def __post_init__(self) -> None:
        for field in ("representation_id", "node_id", "name", "source_id", "approval_reference"):
            require_text(getattr(self, field), field)
        if self.review_state != "reviewed":
            raise CatalogError("unreviewed_basket", "review_state")


@dataclass(frozen=True, slots=True)
class ListingInventory:
    listing: Listing
    instrument_resolution_state: Literal["identified", "placeholder"]
    company_id: str | None

    def __post_init__(self) -> None:
        if self.instrument_resolution_state not in ("identified", "placeholder"):
            raise CatalogError("invalid_instrument_state", "instrument_resolution_state")
        if self.listing.eligible and self.instrument_resolution_state != "identified":
            raise CatalogError("unidentified_instrument", "listing_inventory")
        if self.company_id is not None:
            require_text(self.company_id, "company_id")


@dataclass(frozen=True, slots=True)
class NodeReview:
    scope: Scope
    node_id: str
    source_id: str
    approval_reference: str
    period: Period
    action: str

    def __post_init__(self) -> None:
        for field in ("node_id", "source_id", "approval_reference", "action"):
            require_text(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class RepresentationApproval:
    representation_id: str
    scope: Scope
    node_id: str
    source_id: str
    approval_reference: str
    suitability_reference: str | None
    period: Period
    action: str

    def __post_init__(self) -> None:
        for field in (
            "representation_id",
            "node_id",
            "source_id",
            "approval_reference",
            "action",
        ):
            require_text(getattr(self, field), field)
        if self.suitability_reference is not None:
            require_text(self.suitability_reference, "suitability_reference")


@dataclass(frozen=True, slots=True)
class BasketWeight:
    basket_id: str
    listing_id: str
    weight: str

    def __post_init__(self) -> None:
        require_text(self.basket_id, "basket_id")
        require_text(self.listing_id, "listing_id")
        require_text(self.weight, "weight")
        try:
            value = Decimal(self.weight)
        except InvalidOperation as error:
            raise CatalogError("invalid_weight", "weight") from error
        if not value.is_finite() or value <= 0:
            raise CatalogError("invalid_weight", "weight")


@dataclass(frozen=True, slots=True)
class CollectionOccurrence:
    run: CollectionRun
    event_order: int

    def __post_init__(self) -> None:
        if type(self.event_order) is not int or self.event_order < 1:
            raise CatalogError("invalid_event_order", "collection_run")
        require_text(self.run.run_id, "run_id")
        parse_utc(self.run.observed_at, "collection_run.observed_at")


@dataclass(frozen=True, slots=True)
class CollectionEvidence:
    run_id: str
    evidence_id: str

    def __post_init__(self) -> None:
        require_text(self.run_id, "run_id")
        require_text(self.evidence_id, "evidence_id")


@dataclass(frozen=True, slots=True)
class CandidateAssessment:
    review: ReviewDecision
    classification_version: str

    def __post_init__(self) -> None:
        require_text(self.classification_version, "classification_version")
        if self.review.decision not in ("accept", "reject"):
            raise CatalogError("invalid_decision", "decision")
        for field in (
            "review_id",
            "candidate_id",
            "region_id",
            "classification_id",
            "entity_id",
            "run_id",
            "reason",
            "review_reference",
        ):
            require_text(getattr(self.review, field), field)
        if type(self.review.event_order) is not int or self.review.event_order < 1:
            raise CatalogError("invalid_event_order", "candidate_review")
        parse_date(self.review.as_of, "candidate_review.as_of")
        parse_utc(self.review.observed_at, "candidate_review.observed_at")
        if (
            len(self.review.confirmations) != 3
            or any(type(value) is not bool for value in self.review.confirmations)
            or not self.review.evidence_ids
            or len(set(self.review.evidence_ids)) != len(self.review.evidence_ids)
        ):
            raise CatalogError("invalid_assessment", "confirmations/evidence_ids")
        if self.review.decision == "accept" and not all(self.review.confirmations):
            raise CatalogError("incomplete_confirmation", "candidate_review")


@dataclass(frozen=True, slots=True)
class ReviewEvidence:
    review_id: str
    evidence_id: str

    def __post_init__(self) -> None:
        require_text(self.review_id, "review_id")
        require_text(self.evidence_id, "evidence_id")


@dataclass(frozen=True, slots=True)
class RepresentationProvenance:
    representation_id: str
    review_id: str
    approval_run_id: str

    def __post_init__(self) -> None:
        require_text(self.representation_id, "representation_id")
        require_text(self.review_id, "review_id")
        require_text(self.approval_run_id, "approval_run_id")


@dataclass(frozen=True, slots=True)
class Publication:
    operation_id: str
    expected_release: str | None
    action: str
    catalog_changed: bool

    def __post_init__(self) -> None:
        require_text(self.operation_id, "operation_id")
        require_text(self.action, "action")
        if self.expected_release is not None:
            require_text(self.expected_release, "expected_release")
        if type(self.catalog_changed) is not bool:
            raise CatalogError("invalid_boolean", "catalog_changed")


@dataclass(frozen=True, slots=True)
class LedgerOrigin:
    table: str | None
    primary_key: tuple[tuple[str, str | int | float | None], ...]
    action: str | None

    def __post_init__(self) -> None:
        require_tuple(self.primary_key, "origin.primary_key")
        if self.table is None:
            require_text(self.action, "origin.action")
            if self.primary_key:
                raise CatalogError("unexpected_primary_key", "origin")
        else:
            require_text(self.table, "origin.table")
            if not self.primary_key:
                raise CatalogError("missing_primary_key", "origin")


type LedgerPayload = (
    ListingInventory
    | NodeReview
    | RepresentationApproval
    | BasketDefinition
    | BasketWeight
    | CollectionOccurrence
    | Evidence
    | CollectionEvidence
    | CandidateAssessment
    | ReviewEvidence
    | RepresentationProvenance
    | Publication
)
PAYLOAD_TYPES: dict[str, type[LedgerPayload]] = {
    "listing_inventory": ListingInventory,
    "node_review": NodeReview,
    "representation_approval": RepresentationApproval,
    "basket": BasketDefinition,
    "basket_constituent": BasketWeight,
    "collection_run": CollectionOccurrence,
    "mapping_evidence": Evidence,
    "collection_evidence": CollectionEvidence,
    "candidate_review": CandidateAssessment,
    "review_evidence": ReviewEvidence,
    "representation_provenance": RepresentationProvenance,
    "publication": Publication,
}


@dataclass(frozen=True, slots=True)
class LedgerRecord:
    record_type: str
    record_id: str
    sequence: int
    recorded_at: datetime | None
    payload: LedgerPayload
    origin: LedgerOrigin | None

    def __post_init__(self) -> None:
        require_text(self.record_id, "record_id")
        if type(self.sequence) is not int or self.sequence < 1:
            raise CatalogError("invalid_sequence", "sequence")
        require_utc(self.recorded_at, "recorded_at")
        expected = PAYLOAD_TYPES.get(self.record_type)
        if expected is None or not isinstance(self.payload, expected):
            raise CatalogError("invalid_payload", "record_type/payload")


def json_object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CatalogError("invalid_object", field)
    entries = cast(dict[object, object], value)
    if any(not isinstance(key, str) for key in entries):
        raise CatalogError("invalid_object", field)
    return cast(dict[str, object], entries)


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError("duplicate_key", "json")
        result[key] = value
    return result


def decode_json(raw: str | bytes) -> object:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_json_object,
            parse_constant=lambda _: _invalid_json_number(),
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, CatalogError):
            raise
        raise CatalogError("invalid_json", "json") from None


def _invalid_json_number() -> object:
    raise CatalogError("invalid_number", "json")


def _record_fields(data: dict[str, object], record_type: type[object]) -> None:
    if not is_dataclass(record_type):
        raise CatalogError("invalid_record_type", "ledger")
    if set(data) != {field.name for field in fields(record_type)}:
        raise CatalogError("invalid_fields", record_type.__name__)


def _boolean(data: dict[str, object], key: str, *, nullable: bool = False) -> bool | None:
    value = data[key]
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise CatalogError("invalid_boolean", key)
    return value


def _decoded_period(value: object) -> Period:
    data = json_object(value, "period")
    _record_fields(data, Period)
    end = optional_text(data, "end")
    return Period(
        parse_date(text_field(data, "start"), "start"),
        parse_date(end, "end") if end is not None else None,
    )


def _decoded_scope(value: object) -> Scope:
    data = json_object(value, "scope")
    _record_fields(data, Scope)
    return Scope(*(text_field(data, field.name) for field in fields(Scope)))


def _decoded_listing(value: object) -> Listing:
    data = json_object(value, "listing")
    _record_fields(data, Listing)
    return Listing(
        text_field(data, "listing_id"),
        text_field(data, "instrument_id"),
        text_field(data, "region_id"),
        cast(Literal["stock", "etf"] | None, optional_text(data, "instrument_type")),
        optional_text(data, "ticker"),
        optional_text(data, "provider_symbol"),
        optional_text(data, "name"),
        optional_text(data, "exchange"),
        optional_text(data, "currency"),
        _boolean(data, "is_primary", nullable=True),
        cast(Literal["verified", "unverified"], text_field(data, "resolution_state")),
        _decoded_period(data["period"]) if data["period"] is not None else None,
        optional_text(data, "source_id"),
        optional_text(data, "approval_reference"),
    )


def _decoded_payload(kind: str, data: dict[str, object]) -> LedgerPayload:
    expected = PAYLOAD_TYPES.get(kind)
    if expected is None:
        raise CatalogError("invalid_payload", "record_type")
    _record_fields(data, expected)
    match kind:
        case "listing_inventory":
            return ListingInventory(
                _decoded_listing(data["listing"]),
                cast(
                    Literal["identified", "placeholder"],
                    text_field(data, "instrument_resolution_state"),
                ),
                optional_text(data, "company_id"),
            )
        case "basket_constituent":
            return BasketWeight(
                text_field(data, "basket_id"),
                text_field(data, "listing_id"),
                text_field(data, "weight"),
            )
        case "publication":
            changed = _boolean(data, "catalog_changed")
            if changed is None:
                raise CatalogError("invalid_boolean", "catalog_changed")
            return Publication(
                text_field(data, "operation_id"),
                optional_text(data, "expected_release"),
                text_field(data, "action"),
                changed,
            )
        case "collection_run":
            run = json_object(data["run"], "run")
            _record_fields(run, CollectionRun)
            resources = run["resources"]
            if not isinstance(resources, list):
                raise CatalogError("invalid_resources", "collection_run")
            for resource in cast(list[object], resources):
                entry = json_object(resource, "resource")
                _record_fields(entry, ResourceInspection)
                catalogs = entry["catalogs"]
                if not isinstance(catalogs, list):
                    raise CatalogError("invalid_catalogs", "collection_run")
                for catalog in cast(list[object], catalogs):
                    _record_fields(json_object(catalog, "catalog"), CatalogObservation)
            return CollectionOccurrence(
                CollectionRun.decode(json.dumps(run)), integer_field(data, "event_order")
            )
        case "mapping_evidence":
            item = Evidence.decode(json.dumps(data))
            parse_utc(item.observed_at, "mapping_evidence.observed_at")
            return item
        case "candidate_review":
            review = json_object(data["review"], "review")
            _record_fields(review, ReviewDecision)
            return CandidateAssessment(
                ReviewDecision.decode(json.dumps(review)),
                text_field(data, "classification_version"),
            )
        case "collection_evidence":
            return CollectionEvidence(text_field(data, "run_id"), text_field(data, "evidence_id"))
        case "review_evidence":
            return ReviewEvidence(text_field(data, "review_id"), text_field(data, "evidence_id"))
        case "representation_provenance":
            return RepresentationProvenance(
                text_field(data, "representation_id"),
                text_field(data, "review_id"),
                text_field(data, "approval_run_id"),
            )
        case "node_review":
            return NodeReview(
                _decoded_scope(data["scope"]),
                text_field(data, "node_id"),
                text_field(data, "source_id"),
                text_field(data, "approval_reference"),
                _decoded_period(data["period"]),
                text_field(data, "action"),
            )
        case "representation_approval":
            return RepresentationApproval(
                text_field(data, "representation_id"),
                _decoded_scope(data["scope"]),
                text_field(data, "node_id"),
                text_field(data, "source_id"),
                text_field(data, "approval_reference"),
                optional_text(data, "suitability_reference"),
                _decoded_period(data["period"]),
                text_field(data, "action"),
            )
        case "basket":
            return BasketDefinition(
                text_field(data, "representation_id"),
                _decoded_scope(data["scope"]),
                text_field(data, "node_id"),
                text_field(data, "name"),
                _decoded_period(data["period"]),
                text_field(data, "source_id"),
                text_field(data, "approval_reference"),
                cast(Literal["reviewed"], text_field(data, "review_state")),
            )
        case _:
            raise CatalogError("invalid_payload", "record_type")


def decode_ledger_record(raw: str | bytes) -> LedgerRecord:
    data = json_object(decode_json(raw), "ledger")
    _record_fields(data, LedgerRecord)
    try:
        kind = text_field(data, "record_type")
        origin = None
        if data["origin"] is not None:
            original = json_object(data["origin"], "origin")
            _record_fields(original, LedgerOrigin)
            keys = original["primary_key"]
            if not isinstance(keys, list):
                raise CatalogError("invalid_primary_key", "origin")
            pairs: list[tuple[str, str | int | float | None]] = []
            for item in cast(list[object], keys):
                if not isinstance(item, list):
                    raise CatalogError("invalid_primary_key", "origin")
                pair = cast(list[object], item)
                if len(pair) != 2:
                    raise CatalogError("invalid_primary_key", "origin")
                key, value = pair
                if not isinstance(key, str) or (
                    value is not None and type(value) not in (str, int, float)
                ):
                    raise CatalogError("invalid_primary_key", "origin")
                pairs.append((key, cast(str | int | float | None, value)))
            origin = LedgerOrigin(
                optional_text(original, "table"), tuple(pairs), optional_text(original, "action")
            )
        clock = optional_text(data, "recorded_at")
        return LedgerRecord(
            kind,
            text_field(data, "record_id"),
            integer_field(data, "sequence"),
            parse_utc(clock, "recorded_at") if clock is not None else None,
            _decoded_payload(kind, json_object(data["payload"], "payload")),
            origin,
        )
    except (ValueError, TypeError, KeyError) as error:
        if isinstance(error, CatalogError):
            raise
        raise CatalogError("invalid_payload", "ledger") from None


def _source_approval(
    sources: dict[str, EvidenceSource],
    source_id: str | None,
    reference: str | None,
) -> None:
    source = sources.get(source_id) if source_id is not None else None
    if source is None or reference is None:
        raise CatalogError("unknown_source", "SourceId/ApprovalReference")
    source.require_approval(reference)


def _covered(periods: tuple[Period, ...], required: Period) -> bool:
    cursor = required.start
    for period in sorted(periods, key=lambda item: item.start):
        if period.last < cursor:
            continue
        if period.start > cursor:
            return False
        if period.last >= required.last:
            return True
        cursor = period.last + timedelta(days=1)
    return False


def _matching_nodes(
    index: dict[tuple[Scope, str], list[HierarchyNode]],
    scope: Scope,
    node_id: str,
    node_type: NodeType,
    period: Period,
    sector_id: str | None = None,
) -> tuple[HierarchyNode, ...]:
    nodes = tuple(index.get((scope, node_id), ()))
    if (
        not nodes
        or any(
            node.node_type != node_type or (sector_id is not None and node.sector_id != sector_id)
            for node in nodes
        )
        or not _covered(tuple(node.period for node in nodes), period)
    ):
        raise CatalogError("invalid_node_reference", "NodeId/period")
    return nodes


def validate_catalog(
    classifications: tuple[Classification, ...],
    sources: tuple[EvidenceSource, ...],
    nodes: tuple[HierarchyNode, ...],
    stocks: tuple[StockRow, ...],
    listings: tuple[Listing, ...],
    representations: tuple[EtfRepresentation, ...],
    benchmarks: tuple[Benchmark, ...],
    baskets: tuple[Basket, ...] = (),
    inventory: tuple[ListingInventory, ...] = (),
) -> None:
    source_index = {source.source_id: source for source in sources}
    if len(source_index) != len(sources):
        raise CatalogError("duplicate_source", "source_id")
    classification_index = {item.scope: item for item in classifications}
    if len(classification_index) != len(classifications):
        raise CatalogError("duplicate_classification", "scope")
    for classification in classifications:
        _source_approval(source_index, classification.source_id, classification.approval_reference)

    node_index: dict[tuple[Scope, str], list[HierarchyNode]] = defaultdict(list)
    for node in nodes:
        classification = classification_index.get(node.scope)
        if classification is None or not classification.period.covers(node.period):
            raise CatalogError("invalid_classification_reference", "NodeId")
        if node.approval_origin == "own":
            _source_approval(source_index, node.source_id, node.approval_reference)
        previous = node_index[(node.scope, node.node_id)]
        if any(
            node.period.overlaps(other.period)
            or (node.node_type, node.sector_id, node.parent_industry_id)
            != (
                other.node_type,
                other.sector_id,
                other.parent_industry_id,
            )
            for other in previous
        ):
            raise CatalogError("conflicting_node", "NodeId")
        previous.append(node)
    for node in nodes:
        _matching_nodes(node_index, node.scope, node.sector_id, "sector", node.period)
        if node.node_type == "sub_industry":
            if node.parent_industry_id is None:
                raise CatalogError("missing_parent", "ParentIndustryId")
            _matching_nodes(
                node_index,
                node.scope,
                node.parent_industry_id,
                "industry",
                node.period,
                node.sector_id,
            )

    listing_index: dict[str, Listing] = {}
    for listing in (
        *listings,
        *(row.listing for row in stocks if row.listing is not None),
        *(item.listing for item in inventory),
    ):
        previous_listing = listing_index.get(listing.listing_id)
        if previous_listing is not None and previous_listing != listing:
            raise CatalogError("conflicting_listing", "ListingId")
        listing_index[listing.listing_id] = listing
        if listing.eligible:
            _source_approval(source_index, listing.source_id, listing.approval_reference)
    instrument_types: dict[str, str] = {}
    primary: dict[tuple[str, str], list[Listing]] = defaultdict(list)
    symbols: dict[tuple[str, str], list[Listing]] = defaultdict(list)
    for listing in listing_index.values():
        if listing.instrument_type is not None:
            known_type = instrument_types.get(listing.instrument_id)
            if known_type is not None and known_type != listing.instrument_type:
                raise CatalogError("conflicting_instrument_type", "InstrumentId")
            instrument_types[listing.instrument_id] = listing.instrument_type
        if listing.period is None:
            continue
        if listing.is_primary:
            same_instrument = primary[(listing.region_id, listing.instrument_id)]
            if any(
                other.period is not None and other.period.overlaps(listing.period)
                for other in same_instrument
            ):
                raise CatalogError("conflicting_primary_listing", "ListingId")
            same_instrument.append(listing)
        if listing.provider_symbol is not None:
            same_symbol = symbols[(listing.region_id, listing.provider_symbol)]
            if any(
                other.period is not None and other.period.overlaps(listing.period)
                for other in same_symbol
            ):
                raise CatalogError("ambiguous_provider_symbol", "ProviderSymbol")
            same_symbol.append(listing)

    row_ids: set[str] = set()
    membership_index: dict[str, StockRow] = {}
    instrument_index: dict[str, tuple[str | None, str, str]] = {}
    cohorts: dict[tuple[Scope, str], list[StockRow]] = defaultdict(list)
    physical: set[tuple[str, str | None]] = set()
    for row in stocks:
        if row.row_id in row_ids:
            raise CatalogError("duplicate_row", "RowId")
        row_ids.add(row.row_id)
        pairing = (row.membership_id, row.listing.listing_id if row.listing else None)
        if pairing in physical:
            raise CatalogError("duplicate_pairing", "RowId")
        physical.add(pairing)
        previous_row = membership_index.get(row.membership_id)
        signature = (
            row.scope,
            row.instrument_id,
            row.company_id,
            row.name,
            row.industry_id,
            row.sub_industry_id,
            row.resolution_state,
            row.period,
            row.source_id,
            row.approval_reference,
            row.membership_review_state,
        )
        if previous_row is not None:
            previous_signature = (
                previous_row.scope,
                previous_row.instrument_id,
                previous_row.company_id,
                previous_row.name,
                previous_row.industry_id,
                previous_row.sub_industry_id,
                previous_row.resolution_state,
                previous_row.period,
                previous_row.source_id,
                previous_row.approval_reference,
                previous_row.membership_review_state,
            )
            if previous_signature != signature:
                raise CatalogError("conflicting_membership", "MembershipId")
        membership_index[row.membership_id] = row
        metadata = (row.company_id, row.name, row.resolution_state)
        if (
            row.instrument_id in instrument_index
            and instrument_index[row.instrument_id] != metadata
        ):
            raise CatalogError("conflicting_instrument", "InstrumentId")
        instrument_index[row.instrument_id] = metadata
        _source_approval(source_index, row.source_id, row.approval_reference)
        _matching_nodes(node_index, row.scope, row.industry_id, "industry", row.period)
        if row.sub_industry_id is not None:
            sub_nodes = _matching_nodes(
                node_index, row.scope, row.sub_industry_id, "sub_industry", row.period
            )
            if any(node.parent_industry_id != row.industry_id for node in sub_nodes):
                raise CatalogError("wrong_sub_industry_parent", "SubIndustryId")
        previous_cohort = cohorts[(row.scope, row.instrument_id)]
        if any(
            row.period.overlaps(other.period)
            and (
                row.industry_id != other.industry_id
                or (
                    row.sub_industry_id is not None
                    and other.sub_industry_id is not None
                    and row.sub_industry_id != other.sub_industry_id
                )
            )
            for other in previous_cohort
        ):
            raise CatalogError("conflicting_assignment", "IndustryId/SubIndustryId")
        previous_cohort.append(row)

    representation_ids: set[str] = set()
    node_representations: dict[tuple[Scope, str], list[EtfRepresentation]] = defaultdict(list)
    for representation in representations:
        if representation.representation_id in representation_ids:
            raise CatalogError("duplicate_representation", "RepresentationId")
        representation_ids.add(representation.representation_id)
        _source_approval(source_index, representation.source_id, representation.approval_reference)
        _matching_nodes(
            node_index,
            representation.scope,
            representation.node_id,
            representation.node_type,
            representation.period,
        )
        listing = listing_index.get(representation.listing_id)
        if (
            listing is None
            or listing.instrument_type != "etf"
            or not listing.eligible
            or listing.is_primary is not True
            or listing.region_id != representation.scope.region_id
            or listing.period is None
            or not listing.period.covers(representation.period)
        ):
            raise CatalogError("invalid_etf_listing", "ListingId")
        previous_representations = node_representations[
            (representation.scope, representation.node_id)
        ]
        if any(item.period.overlaps(representation.period) for item in previous_representations):
            raise CatalogError("conflicting_representation", "RepresentationId")
        previous_representations.append(representation)

    benchmark_ids: set[str] = set()
    benchmark_index: dict[tuple[str, BenchmarkPurpose], list[Benchmark]] = defaultdict(list)
    for benchmark in benchmarks:
        if benchmark.benchmark_id in benchmark_ids:
            raise CatalogError("duplicate_benchmark", "BenchmarkId")
        benchmark_ids.add(benchmark.benchmark_id)
        _source_approval(source_index, benchmark.source_id, benchmark.approval_reference)
        listing = listing_index.get(benchmark.listing_id)
        if (
            listing is None
            or not listing.eligible
            or listing.is_primary is not True
            or listing.region_id != benchmark.region_id
            or listing.period is None
            or not listing.period.covers(benchmark.period)
        ):
            raise CatalogError("invalid_benchmark_listing", "ListingId")
        previous_benchmarks = benchmark_index[(benchmark.region_id, benchmark.purpose)]
        if any(item.period.overlaps(benchmark.period) for item in previous_benchmarks):
            raise CatalogError("ambiguous_benchmark", "Purpose")
        previous_benchmarks.append(benchmark)

    basket_index: dict[tuple[Scope, str], list[Basket]] = defaultdict(list)
    for basket in baskets:
        if basket.representation_id in representation_ids:
            raise CatalogError("duplicate_representation", "basket")
        representation_ids.add(basket.representation_id)
        _source_approval(source_index, basket.source_id, basket.approval_reference)
        target_nodes = node_index.get((basket.scope, basket.node_id))
        if not target_nodes:
            raise CatalogError("unknown_basket_node", "NodeId")
        _matching_nodes(
            node_index, basket.scope, basket.node_id, target_nodes[0].node_type, basket.period
        )
        if any(
            item.period.overlaps(basket.period)
            for item in node_representations[(basket.scope, basket.node_id)]
        ) or any(
            item.period.overlaps(basket.period)
            for item in basket_index[(basket.scope, basket.node_id)]
        ):
            raise CatalogError("conflicting_basket", "NodeId")
        basket_index[(basket.scope, basket.node_id)].append(basket)
        for constituent in basket.constituents:
            listing = listing_index.get(constituent.listing_id)
            if (
                listing is None
                or not listing.eligible
                or listing.period is None
                or listing.region_id != basket.scope.region_id
                or listing.provider_symbol != constituent.symbol
                or not listing.period.covers(basket.period)
            ):
                raise CatalogError("invalid_basket_listing", "ListingId")
