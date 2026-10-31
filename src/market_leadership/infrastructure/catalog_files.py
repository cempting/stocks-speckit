"""Captured, validated file releases and coherent local POSIX publication."""

import csv
import fcntl
import io
import json
import os
import shutil
import stat
from collections import defaultdict
from collections.abc import Callable, Generator, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Literal, Protocol, cast
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from market_leadership.domain.catalog import (
    Artifact,
    ArtifactRole,
    Basket,
    BasketDefinition,
    BasketWeight,
    Benchmark,
    BenchmarkPurpose,
    CandidateAssessment,
    CatalogEntry,
    CatalogError,
    CatalogRelease,
    Classification,
    CollectionEvidence,
    CollectionOccurrence,
    EtfRepresentation,
    EvidenceSource,
    HierarchyNode,
    LedgerRecord,
    Listing,
    ListingInventory,
    NodeReview,
    NodeType,
    ParentRelease,
    Period,
    Region,
    RepresentationApproval,
    RepresentationProvenance,
    ResearchCatalog,
    ResearchSource,
    ReviewEvidence,
    Scope,
    StockRow,
    decode_json,
    decode_ledger_record,
    json_object,
    parse_date,
    parse_utc,
    require_date,
    require_hash,
    require_relative_path,
    validate_catalog,
)
from market_leadership.domain.industry_representations import BasketConstituent
from market_leadership.domain.local_etf_evidence import Evidence, optional_text, text_field

ARTIFACT_LIMIT = 64 * 1024 * 1024
RECORD_LIMIT = 1024 * 1024
HEADERS = {
    "hierarchy": (
        "RegionId,ClassificationId,ClassificationVersion,NodeId,NodeType,Name,SectorId,"
        "ParentIndustryId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,ApprovalOrigin"
    ),
    "stocks": (
        "RowId,MembershipId,RegionId,ClassificationId,ClassificationVersion,InstrumentId,"
        "CompanyId,Name,IndustryId,SubIndustryId,ResolutionState,MembershipEffectiveFrom,"
        "MembershipEffectiveTo,MembershipSourceId,MembershipApprovalReference,MembershipReviewState,"
        "ListingId,Ticker,ProviderSymbol,Exchange,Currency,IsPrimary,ListingResolutionState,"
        "ListingEffectiveFrom,ListingEffectiveTo,ListingSourceId,ListingApprovalReference"
    ),
    "etf_listings": (
        "ListingId,RegionId,InstrumentId,InstrumentType,Ticker,ProviderSymbol,Name,Exchange,"
        "Currency,IsPrimary,ResolutionState,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference"
    ),
    "sector_etfs": (
        "RepresentationId,RegionId,ClassificationId,ClassificationVersion,NodeId,ListingId,"
        "EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,SuitabilityReference,CandidateReviewId"
    ),
    "benchmarks": (
        "BenchmarkId,RegionId,Purpose,Label,ListingId,EffectiveFrom,EffectiveTo,SourceId,"
        "ApprovalReference"
    ),
}
HEADERS["industry_etfs"] = HEADERS["sub_industry_etfs"] = HEADERS["sector_etfs"]
_SCHEMA = decode_json(
    files("market_leadership.infrastructure").joinpath("catalog-manifest.schema.json").read_bytes()
)
_VALIDATOR = Draft202012Validator(json_object(_SCHEMA, "schema"), format_checker=FormatChecker())
csv.field_size_limit(RECORD_LIMIT)


class _ManifestValidator(Protocol):
    def iter_errors(self, instance: dict[str, object]) -> Iterator[ValidationError]: ...


@dataclass(frozen=True, slots=True)
class FileIdentity:
    path: Path
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int


def _identity(path: Path) -> FileIdentity:
    try:
        info = path.stat()
    except OSError:
        raise CatalogError("unavailable_file", "artifact") from None
    if not stat.S_ISREG(info.st_mode):
        raise CatalogError("invalid_file_type", "artifact")
    return FileIdentity(
        path, info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
    )


def _contained(root: Path, relative: str) -> Path:
    require_relative_path(relative, "path")
    try:
        canonical = root.resolve(strict=True)
        path = (canonical / relative).resolve(strict=True)
    except (OSError, RuntimeError):
        raise CatalogError("unavailable_file", "path") from None
    if not path.is_relative_to(canonical) or path == canonical:
        raise CatalogError("unsafe_path", "path")
    return path


def _capture(path: Path, limit: int) -> tuple[bytes, FileIdentity]:
    before = _identity(path)
    if before.size > limit:
        raise CatalogError("input_limit", "artifact")
    try:
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (before.device, before.inode):
                raise CatalogError("concurrent_edit", "artifact")
            raw = stream.read(limit + 1)
    except OSError:
        raise CatalogError("unavailable_file", "artifact") from None
    if len(raw) > limit:
        raise CatalogError("input_limit", "artifact")
    if _identity(path) != before:
        raise CatalogError("concurrent_edit", "artifact")
    return raw, before


def _shape(raw: bytes, format_name: str) -> dict[str, object]:
    data = json_object(decode_json(raw), "manifest")
    if (
        data.get("format") != format_name
        or next(cast(_ManifestValidator, _VALIDATOR).iter_errors(data), None) is not None
    ):
        raise CatalogError("invalid_manifest", "schema")
    return data


def _objects(value: object, field: str) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        raise CatalogError("invalid_array", field)
    return tuple(json_object(item, field) for item in cast(list[object], value))


def _nullable_date(data: dict[str, object], key: str) -> date | None:
    value = optional_text(data, key)
    return parse_date(value, key) if value is not None else None


def _release(data: dict[str, object]) -> CatalogRelease:
    regions: list[Region] = []
    for item in _objects(data["regions"], "regions"):
        region_id = text_field(item, "region_id")
        classifications = tuple(
            Classification(
                Scope(region_id, text_field(c, "classification_id"), text_field(c, "version")),
                text_field(c, "scheme_name"),
                text_field(c, "source_id"),
                text_field(c, "approval_reference"),
                Period(
                    parse_date(text_field(c, "effective_from"), "effective_from"),
                    _nullable_date(c, "effective_to"),
                ),
            )
            for c in _objects(item["classifications"], "classifications")
        )
        regions.append(
            Region(
                region_id,
                text_field(item, "name"),
                cast(Literal["active", "inactive"], text_field(item, "status")),
                cast(
                    Literal["complete", "partial", "unverified"], text_field(item, "coverage_state")
                ),
                text_field(item, "coverage_description"),
                parse_date(text_field(item, "coverage_as_of"), "coverage_as_of"),
                _nullable_date(item, "last_reviewed_at"),
                classifications,
            )
        )
    sources = tuple(
        EvidenceSource(
            text_field(item, "source_id"),
            cast(Literal["local_file", "live"], text_field(item, "source_type")),
            text_field(item, "description"),
            optional_text(item, "coverage"),
            optional_text(item, "authority"),
            optional_text(item, "approval_reference"),
            _nullable_date(item, "reviewed_at"),
        )
        for item in _objects(data["evidence_sources"], "evidence_sources")
    )
    artifacts = tuple(
        Artifact(
            text_field(item, "artifact_id"),
            cast(ArtifactRole, text_field(item, "role")),
            text_field(item, "path"),
            text_field(item, "sha256"),
            item["required"] is True,
            cast(int, item["row_count"]),
            optional_text(item, "region_id"),
            optional_text(item, "classification_id"),
            optional_text(item, "classification_version"),
        )
        for item in _objects(data["artifacts"], "artifacts")
    )
    research = tuple(
        ResearchSource(
            text_field(item, "resource_id"),
            text_field(item, "root"),
            item["required"] is True,
            tuple(
                ResearchCatalog(
                    text_field(c, "path"),
                    text_field(c, "name"),
                    cast(
                        Literal["industry", "sector_context", "index_context", "commodity_context"],
                        text_field(c, "catalog_type"),
                    ),
                )
                for c in _objects(item["catalogs"], "catalogs")
            ),
        )
        for item in _objects(data["research_sources"], "research_sources")
    )
    parent = None
    if data["parent_release"] is not None:
        original = json_object(data["parent_release"], "parent_release")
        parent = ParentRelease(
            text_field(original, "release_id"), text_field(original, "manifest_sha256")
        )
    return CatalogRelease(
        text_field(data, "release_id"),
        parse_utc(text_field(data, "created_at"), "created_at"),
        parent,
        text_field(data, "catalog_revision"),
        tuple(regions),
        sources,
        artifacts,
        research,
    )


def _csv(raw: bytes, role: str) -> tuple[dict[str, str], ...]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError:
        raise CatalogError("invalid_utf8", role) from None
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    offsets = [0]
    for line in io.StringIO(text, newline=""):
        offsets.append(offsets[-1] + len(line.encode("utf-8")))
    try:
        header = next(reader, None)
        expected = HEADERS[role].split(",")
        if header != expected:
            raise CatalogError("invalid_header", role)
        rows: list[dict[str, str]] = []
        previous_line = reader.line_num
        for row in reader:
            if len(row) != len(expected):
                raise CatalogError("invalid_row", f"{role}:{reader.line_num}")
            if offsets[reader.line_num] - offsets[previous_line] > RECORD_LIMIT:
                raise CatalogError("input_limit", f"{role}:{reader.line_num}")
            previous_line = reader.line_num
            rows.append(dict(zip(expected, row, strict=True)))
        return tuple(rows)
    except csv.Error:
        raise CatalogError("invalid_csv", role) from None


def _scope(row: dict[str, str]) -> Scope:
    return Scope(row["RegionId"], row["ClassificationId"], row["ClassificationVersion"])


def _period(row: dict[str, str], prefix: str = "") -> Period:
    start = row[f"{prefix}EffectiveFrom"]
    end = row[f"{prefix}EffectiveTo"]
    return Period(
        parse_date(start, f"{prefix}EffectiveFrom"), parse_date(end, "EffectiveTo") if end else None
    )


def _bool(value: str) -> bool | None:
    if value == "":
        return None
    if value not in ("true", "false"):
        raise CatalogError("invalid_boolean", "IsPrimary")
    return value == "true"


def _listing(row: dict[str, str], *, stock: bool = False) -> Listing | None:
    if stock:
        listing_fields = HEADERS["stocks"].split(",")[16:]
        if not row["ListingId"]:
            if any(row[field] for field in listing_fields):
                raise CatalogError("incomplete_listing", "ListingId")
            return None
    prefix = "Listing" if stock else ""
    period = None
    if row[f"{prefix}EffectiveFrom"]:
        period = _period(row, prefix)
    elif row[f"{prefix}EffectiveTo"]:
        raise CatalogError("incomplete_period", "ListingEffectiveFrom")
    return Listing(
        row["ListingId"],
        row["InstrumentId"],
        row["RegionId"],
        "stock" if stock else cast(Literal["etf"], row["InstrumentType"]),
        row["Ticker"] or None,
        row["ProviderSymbol"] or None,
        row["Name"],
        row["Exchange"] or None,
        row["Currency"] or None,
        _bool(row["IsPrimary"]),
        cast(Literal["verified", "unverified"], row[f"{prefix}ResolutionState"]),
        period,
        row[f"{prefix}SourceId"] or None,
        row[f"{prefix}ApprovalReference"] or None,
    )


def _scoped(artifact: Artifact, row: dict[str, str]) -> None:
    for declared, key in (
        (artifact.region_id, "RegionId"),
        (artifact.classification_id, "ClassificationId"),
        (artifact.classification_version, "ClassificationVersion"),
    ):
        if declared is not None and row.get(key) != declared:
            raise CatalogError("artifact_scope_mismatch", artifact.role)


def _jsonl(raw: bytes, role: str) -> tuple[bytes, ...]:
    lines = tuple(line for line in raw.split(b"\n") if line.strip())
    for number, line in enumerate(lines, 1):
        if len(line) > RECORD_LIMIT:
            raise CatalogError("input_limit", f"{role}:{number}")
        json_object(decode_json(line), role)
    return lines


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    release: CatalogRelease
    catalog_revision: str
    manifest_path: Path
    manifest_sha256: str
    nodes: tuple[HierarchyNode, ...]
    stocks: tuple[StockRow, ...]
    listings: tuple[Listing, ...]
    representations: tuple[EtfRepresentation, ...]
    benchmarks: tuple[Benchmark, ...]
    ledger: tuple[LedgerRecord, ...]
    inventory: tuple[ListingInventory, ...]
    baskets: tuple[Basket, ...]
    fingerprints: tuple[FileIdentity, ...]
    captured: tuple[tuple[str, bytes], ...]
    node_index: tuple[tuple[Scope, tuple[HierarchyNode, ...]], ...]
    member_index: tuple[tuple[tuple[Scope, str], tuple[StockRow, ...]], ...]

    def scope_on(self, region_id: str, as_of: date) -> Scope:
        require_date(as_of, "as_of")
        region = next((item for item in self.release.regions if item.region_id == region_id), None)
        if region is None or region.status != "active":
            raise CatalogError("unavailable_region", "region_id")
        scopes = tuple(
            item.scope for item in region.classifications if item.period.active_on(as_of)
        )
        if len(scopes) != 1:
            raise CatalogError("unavailable_classification", "scope/as_of")
        return scopes[0]

    def active_nodes(self, scope: Scope, as_of: date) -> tuple[HierarchyNode, ...]:
        require_date(as_of, "as_of")
        region = next(
            (item for item in self.release.regions if item.region_id == scope.region_id), None
        )
        if region is None or region.status != "active":
            raise CatalogError("unavailable_region", "region_id")
        classification = next(
            (item for item in region.classifications if item.scope == scope), None
        )
        if classification is None or not classification.period.active_on(as_of):
            raise CatalogError("unavailable_classification", "scope/as_of")
        return tuple(
            node
            for key, nodes in self.node_index
            if key == scope
            for node in nodes
            if node.period.active_on(as_of)
        )

    def members(self, scope: Scope, node_id: str, as_of: date) -> tuple[StockRow, ...]:
        if not any(node.node_id == node_id for node in self.active_nodes(scope, as_of)):
            raise CatalogError("inactive_node", "NodeId")
        selected: dict[str, StockRow] = {}
        for key, rows in self.member_index:
            if key != (scope, node_id):
                continue
            for row in rows:
                if row.period.active_on(as_of):
                    previous = selected.get(row.instrument_id)
                    if previous is None or (
                        previous.provider_symbol_on(as_of) is None
                        and row.provider_symbol_on(as_of) is not None
                    ):
                        selected[row.instrument_id] = row
        return tuple(selected[key] for key in sorted(selected))

    def provider_symbols(self, scope: Scope, node_id: str, as_of: date) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    symbol
                    for row in self.members(scope, node_id, as_of)
                    if (symbol := row.provider_symbol_on(as_of)) is not None
                }
            )
        )

    def cohort_fingerprint(self, scope: Scope, node_id: str, as_of: date) -> str:
        rows = self.members(scope, node_id, as_of)
        # Physical row/assertion IDs do not alter a deduplicated scoring cohort.
        members = [
            {
                key: value
                for key, value in asdict(row).items()
                if key not in ("row_id", "membership_id")
            }
            for row in rows
        ]
        source_ids = {row.source_id for row in rows}
        source_ids.update(
            row.listing.source_id
            for row in rows
            if row.listing is not None and row.listing.source_id is not None
        )
        payload = {
            "scope": asdict(scope),
            "node_id": node_id,
            "as_of": as_of.isoformat(),
            "members": members,
            "sources": [
                asdict(source)
                for source in sorted(self.release.evidence_sources, key=lambda item: item.source_id)
                if source.source_id in source_ids
            ],
        }
        return sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()

    def benchmark(self, region_id: str, purpose: BenchmarkPurpose, as_of: date) -> Listing:
        require_date(as_of, "as_of")
        selected = tuple(
            mapping
            for mapping in self.benchmarks
            if mapping.region_id == region_id
            and mapping.purpose == purpose
            and mapping.period.active_on(as_of)
        )
        if len(selected) != 1:
            raise CatalogError("missing_benchmark", "Purpose")
        listing = next(
            listing
            for listing in (
                *self.listings,
                *(row.listing for row in self.stocks if row.listing is not None),
                *(item.listing for item in self.inventory),
            )
            if listing.listing_id == selected[0].listing_id
        )
        if not listing.active_on(as_of):
            raise CatalogError("unavailable_benchmark", "ListingId/as_of")
        return listing

    def check_integrity(self) -> None:
        if any(_identity(identity.path) != identity for identity in self.fingerprints):
            raise CatalogError("changed_artifact", "release")
        for artifact, fingerprint in zip(
            self.release.artifacts, self.fingerprints[1:], strict=True
        ):
            if _contained(self.manifest_path.parent, artifact.path) != fingerprint.path:
                raise CatalogError("changed_artifact", "path")


def _governance(
    ledger: tuple[LedgerRecord, ...],
    listings: tuple[Listing, ...],
    nodes: tuple[HierarchyNode, ...],
    representations: tuple[EtfRepresentation, ...],
) -> tuple[tuple[ListingInventory, ...], tuple[Basket, ...]]:
    inventory = tuple(r.payload for r in ledger if isinstance(r.payload, ListingInventory))
    listing_index = {listing.listing_id: listing for listing in listings}
    listing_index.update((item.listing.listing_id, item.listing) for item in inventory)
    definitions = {
        r.payload.representation_id: r.payload
        for r in ledger
        if isinstance(r.payload, BasketDefinition)
    }
    weights: dict[str, list[BasketConstituent]] = defaultdict(list)
    for record in ledger:
        weight = record.payload
        if isinstance(weight, BasketWeight):
            listing = listing_index.get(weight.listing_id)
            if (
                weight.basket_id not in definitions
                or listing is None
                or listing.provider_symbol is None
            ):
                raise CatalogError("invalid_basket_reference", "basket_constituent")
            weights[weight.basket_id].append(
                BasketConstituent(
                    weight.listing_id, listing.provider_symbol, Decimal(weight.weight)
                )
            )
    baskets = tuple(
        Basket(
            item.representation_id,
            item.scope,
            item.node_id,
            item.name,
            item.period,
            item.source_id,
            item.approval_reference,
            tuple(weights[item.representation_id]),
            item.review_state,
        )
        for item in definitions.values()
    )
    runs = {
        r.payload.run.run_id: r.payload
        for r in ledger
        if isinstance(r.payload, CollectionOccurrence)
    }
    evidence = {r.payload.evidence_id: r.payload for r in ledger if isinstance(r.payload, Evidence)}
    reviews = {
        r.payload.review.review_id: r.payload
        for r in ledger
        if isinstance(r.payload, CandidateAssessment)
    }
    for records, expected in (
        (definitions, BasketDefinition),
        (runs, CollectionOccurrence),
        (evidence, Evidence),
        (reviews, CandidateAssessment),
    ):
        if len(records) != sum(isinstance(record.payload, expected) for record in ledger):
            raise CatalogError("duplicate_payload_identity", "ledger")
    for values, field in (
        (tuple(item.event_order for item in runs.values()), "collection_event_order"),
        (tuple(item.review.event_order for item in reviews.values()), "review_event_order"),
    ):
        if len(set(values)) != len(values):
            raise CatalogError("duplicate_event_order", field)
    collection_links = {
        (r.payload.run_id, r.payload.evidence_id)
        for r in ledger
        if isinstance(r.payload, CollectionEvidence)
    }
    review_links = {
        (r.payload.review_id, r.payload.evidence_id)
        for r in ledger
        if isinstance(r.payload, ReviewEvidence)
    }
    provenance = tuple(r.payload for r in ledger if isinstance(r.payload, RepresentationProvenance))
    for links, expected in (
        (collection_links, CollectionEvidence),
        (review_links, ReviewEvidence),
    ):
        if len(links) != sum(isinstance(record.payload, expected) for record in ledger):
            raise CatalogError("duplicate_research_link", "ledger")
    for occurrence in runs.values():
        for resource in occurrence.run.resources:
            for catalog in resource.catalogs:
                for key in catalog.evidence_ids:
                    item = evidence.get(key)
                    if (
                        item is None
                        or (occurrence.run.run_id, key) not in collection_links
                        or item.source_key != catalog.source_key
                        or (item.resource, item.root) != (resource.alias, resource.root)
                    ):
                        raise CatalogError("invalid_observation_link", "collection_run")
    mapping_index = {item.representation_id: item for item in representations}
    for record in ledger:
        payload = record.payload
        if isinstance(payload, CollectionEvidence):
            if payload.run_id not in runs or payload.evidence_id not in evidence:
                raise CatalogError("invalid_research_link", "collection_evidence")
        elif isinstance(payload, ReviewEvidence):
            if (
                payload.review_id not in reviews
                or payload.evidence_id not in evidence
                or payload.evidence_id not in reviews[payload.review_id].review.evidence_ids
            ):
                raise CatalogError("invalid_research_link", "review_evidence")
        elif isinstance(payload, CandidateAssessment):
            review = payload.review
            if review.run_id not in runs or any(
                key not in evidence
                or (review.run_id, key) not in collection_links
                or (review.review_id, key) not in review_links
                or evidence[key].candidate_id != review.candidate_id
                for key in review.evidence_ids
            ):
                raise CatalogError("invalid_research_link", "candidate_review")
            scope = Scope(
                review.region_id, review.classification_id, payload.classification_version
            )
            if not any(
                node.scope == scope
                and node.node_id == review.entity_id
                and node.period.active_on(parse_date(review.as_of, "as_of"))
                for node in nodes
            ):
                raise CatalogError("invalid_review_target", "candidate_review")
        elif isinstance(payload, RepresentationProvenance):
            mapping = mapping_index.get(payload.representation_id)
            assessment = reviews.get(payload.review_id)
            if mapping is None or assessment is None or payload.approval_run_id not in runs:
                raise CatalogError("invalid_provenance", "representation_provenance")
            review = assessment.review
            if (
                review.decision != "accept"
                or mapping.candidate_review_id != review.review_id
                or mapping.scope
                != Scope(
                    review.region_id, review.classification_id, assessment.classification_version
                )
                or mapping.node_id != review.entity_id
                or any(
                    (payload.approval_run_id, key) not in collection_links
                    for key in review.evidence_ids
                )
            ):
                raise CatalogError("invalid_provenance", "representation_provenance")
        elif isinstance(payload, NodeReview):
            if not any(
                node.scope == payload.scope
                and node.node_id == payload.node_id
                and node.source_id == payload.source_id
                and node.approval_reference == payload.approval_reference
                and node.period.covers(payload.period)
                for node in nodes
            ):
                raise CatalogError("invalid_node_review", "node_review")
        elif isinstance(payload, RepresentationApproval):
            mapping = mapping_index.get(payload.representation_id)
            if mapping is None or (
                mapping.scope,
                mapping.node_id,
                mapping.source_id,
                mapping.approval_reference,
                mapping.suitability_reference,
                mapping.period,
            ) != (
                payload.scope,
                payload.node_id,
                payload.source_id,
                payload.approval_reference,
                payload.suitability_reference,
                payload.period,
            ):
                raise CatalogError("invalid_approval", "representation_approval")
    for mapping in representations:
        if mapping.candidate_review_id is not None and not any(
            item.representation_id == mapping.representation_id
            and item.review_id == mapping.candidate_review_id
            for item in provenance
        ):
            raise CatalogError("missing_provenance", "CandidateReviewId")
    return inventory, baskets


def _revision(
    release: CatalogRelease, ledger: tuple[LedgerRecord, ...], source_ids: set[str]
) -> str:
    relevant = tuple(
        asdict(record.payload)
        for record in ledger
        if isinstance(
            record.payload,
            (ListingInventory, BasketDefinition, BasketWeight, NodeReview, RepresentationApproval),
        )
    )
    content = {
        "regions": [asdict(region) for region in release.regions],
        "sources": [
            asdict(source) for source in release.evidence_sources if source.source_id in source_ids
        ],
        "artifacts": [
            (
                a.role,
                a.region_id,
                a.classification_id,
                a.classification_version,
                a.sha256,
                a.row_count,
            )
            for a in release.artifacts
            if a.role not in ("audit", "migration_archive")
        ],
        "approvals": relevant,
    }
    return sha256(
        json.dumps(content, default=str, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_release(
    manifest_path: Path, *, _previous: CatalogSnapshot | None = None
) -> CatalogSnapshot:
    manifest_path = manifest_path.resolve()
    raw, manifest_identity = _capture(manifest_path, RECORD_LIMIT)
    release = _release(_shape(raw, "market-catalog-release-1"))
    fingerprints = [manifest_identity]
    captured: list[tuple[str, bytes]] = []
    nodes: list[HierarchyNode] = []
    stocks: list[StockRow] = []
    listings: list[Listing] = []
    representations: list[EtfRepresentation] = []
    benchmarks: list[Benchmark] = []
    ledger: list[LedgerRecord] = []
    for artifact in release.artifacts:
        path = _contained(manifest_path.parent, artifact.path)
        content, fingerprint = _capture(path, ARTIFACT_LIMIT)
        if sha256(content).hexdigest() != artifact.sha256:
            raise CatalogError("checksum_mismatch", artifact.role)
        fingerprints.append(fingerprint)
        captured.append((artifact.path, content))
        if artifact.role in ("audit", "migration_archive"):
            lines = _jsonl(content, artifact.role)
            if artifact.role == "audit":
                ledger.extend(decode_ledger_record(line) for line in lines)
            count = len(lines)
        else:
            rows = _csv(content, artifact.role)
            count = len(rows)
            for number, row in enumerate(rows, 1):
                try:
                    _scoped(artifact, row)
                    match artifact.role:
                        case "hierarchy":
                            nodes.append(
                                HierarchyNode(
                                    _scope(row),
                                    row["NodeId"],
                                    cast(NodeType, row["NodeType"]),
                                    row["Name"],
                                    row["SectorId"],
                                    row["ParentIndustryId"] or None,
                                    _period(row),
                                    row["SourceId"] or None,
                                    row["ApprovalReference"] or None,
                                    cast(
                                        Literal["own", "classification_inherited"],
                                        row["ApprovalOrigin"],
                                    ),
                                )
                            )
                        case "stocks":
                            stocks.append(
                                StockRow(
                                    row["RowId"],
                                    row["MembershipId"],
                                    _scope(row),
                                    row["InstrumentId"],
                                    row["CompanyId"] or None,
                                    row["Name"],
                                    row["IndustryId"],
                                    row["SubIndustryId"] or None,
                                    cast(
                                        Literal["identified", "placeholder"], row["ResolutionState"]
                                    ),
                                    _period(row, "Membership"),
                                    row["MembershipSourceId"],
                                    row["MembershipApprovalReference"],
                                    cast(Literal["reviewed"], row["MembershipReviewState"]),
                                    _listing(row, stock=True),
                                )
                            )
                        case "etf_listings":
                            listing = _listing(row)
                            if listing is None or listing.instrument_type != "etf":
                                raise CatalogError("invalid_etf_type", "InstrumentType")
                            listings.append(listing)
                        case "sector_etfs" | "industry_etfs" | "sub_industry_etfs":
                            representations.append(
                                EtfRepresentation(
                                    row["RepresentationId"],
                                    _scope(row),
                                    row["NodeId"],
                                    cast(NodeType, artifact.role.removesuffix("_etfs")),
                                    row["ListingId"],
                                    _period(row),
                                    row["SourceId"],
                                    row["ApprovalReference"],
                                    row["SuitabilityReference"],
                                    row["CandidateReviewId"] or None,
                                )
                            )
                        case "benchmarks":
                            benchmarks.append(
                                Benchmark(
                                    row["BenchmarkId"],
                                    row["RegionId"],
                                    cast(BenchmarkPurpose, row["Purpose"]),
                                    row["Label"],
                                    row["ListingId"],
                                    _period(row),
                                    row["SourceId"],
                                    row["ApprovalReference"],
                                )
                            )
                except CatalogError as error:
                    raise CatalogError(
                        error.code, f"{artifact.role}:{number}:{error.field}"
                    ) from None
        if count != artifact.row_count:
            raise CatalogError("row_count_mismatch", artifact.role)
    if len({(item.device, item.inode) for item in fingerprints}) != len(fingerprints):
        raise CatalogError("duplicate_artifact_identity", "artifacts")
    if len({listing.listing_id for listing in listings}) != len(listings):
        raise CatalogError("duplicate_listing", "etf_listings")
    if len({record.record_id for record in ledger}) != len(ledger):
        raise CatalogError("duplicate_record", "record_id")
    if any(
        left.sequence >= right.sequence for left, right in zip(ledger, ledger[1:], strict=False)
    ):
        raise CatalogError("invalid_sequence", "ledger")
    all_listings = tuple([*listings, *(row.listing for row in stocks if row.listing is not None)])
    inventory, baskets = _governance(
        tuple(ledger), all_listings, tuple(nodes), tuple(representations)
    )
    known_regions = {region.region_id for region in release.regions}
    if any(
        listing.region_id not in known_regions
        for listing in (*all_listings, *(item.listing for item in inventory))
    ):
        raise CatalogError("unknown_listing_region", "RegionId")
    classifications = tuple(c for region in release.regions for c in region.classifications)
    validate_catalog(
        classifications,
        release.evidence_sources,
        tuple(nodes),
        tuple(stocks),
        tuple(listings),
        tuple(representations),
        tuple(benchmarks),
        baskets,
        inventory,
    )
    source_ids = {
        item.source_id
        for item in (
            *classifications,
            *nodes,
            *stocks,
            *all_listings,
            *representations,
            *benchmarks,
            *baskets,
        )
        if item.source_id is not None
    }
    source_ids.update(
        item.listing.source_id for item in inventory if item.listing.source_id is not None
    )
    revision = _revision(release, tuple(ledger), source_ids)
    node_index: dict[Scope, list[HierarchyNode]] = defaultdict(list)
    member_index: dict[tuple[Scope, str], list[StockRow]] = defaultdict(list)
    same_nodes = _previous is not None and tuple(nodes) == _previous.nodes
    same_members = same_nodes and _previous is not None and tuple(stocks) == _previous.stocks
    if not same_nodes:
        for node in nodes:
            node_index[node.scope].append(node)
    if not same_members:
        sectors = {(node.scope, node.node_id): node.sector_id for node in nodes}
        for row in stocks:
            for node_id in (
                sectors[(row.scope, row.industry_id)],
                row.industry_id,
                row.sub_industry_id,
            ):
                if node_id is not None:
                    member_index[(row.scope, node_id)].append(row)
    snapshot = CatalogSnapshot(
        release,
        revision,
        manifest_path,
        sha256(raw).hexdigest(),
        tuple(nodes),
        tuple(stocks),
        tuple(listings),
        tuple(representations),
        tuple(benchmarks),
        tuple(ledger),
        inventory,
        baskets,
        tuple(fingerprints),
        tuple(captured),
        _previous.node_index
        if same_nodes and _previous is not None
        else tuple((key, tuple(value)) for key, value in node_index.items()),
        _previous.member_index
        if same_members and _previous is not None
        else tuple((key, tuple(value)) for key, value in member_index.items()),
    )
    snapshot.check_integrity()
    return snapshot


class CatalogReader:
    def __init__(self) -> None:
        self._cached: tuple[FileIdentity, CatalogSnapshot] | None = None

    def read(self, entry_path: Path) -> CatalogSnapshot:
        entry_path = entry_path.absolute()
        identity = _identity(entry_path)
        if self._cached is not None and self._cached[0] == identity:
            snapshot = self._cached[1]
            try:
                snapshot.check_integrity()
                return snapshot
            except CatalogError as error:
                if error.code != "changed_artifact":
                    raise
        raw, identity = _capture(entry_path, RECORD_LIMIT)
        data = _shape(raw, "market-catalog-entry-1")
        entry = CatalogEntry(
            text_field(data, "release_id"),
            text_field(data, "manifest_path"),
            text_field(data, "manifest_sha256"),
        )
        manifest_path = _contained(entry_path.parent, entry.manifest_path)
        snapshot = load_release(
            manifest_path, _previous=self._cached[1] if self._cached is not None else None
        )
        if snapshot.manifest_sha256 != entry.manifest_sha256:
            raise CatalogError("checksum_mismatch", "manifest")
        if snapshot.release.release_id != entry.release_id:
            raise CatalogError("release_identity_mismatch", "entry")
        if snapshot.release.catalog_revision != snapshot.catalog_revision:
            raise CatalogError("revision_mismatch", "catalog_revision")
        if _identity(entry_path) != identity:
            raise CatalogError("concurrent_edit", "entry")
        self._cached = identity, snapshot
        return snapshot


class PublicationError(CatalogError):
    def __init__(
        self,
        code: str,
        *,
        publication_state: Literal["not_published", "unknown"] = "not_published",
        operation_id: str | None = None,
        expected_release: str | None = None,
    ) -> None:
        self.publication_state = publication_state
        self.operation_id = operation_id
        self.expected_release = expected_release
        super().__init__(code, "publication")


@dataclass(frozen=True, slots=True)
class PublishedRelease:
    release_id: str
    catalog_revision: str
    catalog_changed: bool
    manifest_path: Path


def initialize_store(directory: Path) -> None:
    if directory.is_symlink():
        raise CatalogError("unsafe_store", "directory")
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("releases", ".staging", ".writer.lock"):
        if (directory / name).is_symlink():
            raise CatalogError("unsafe_store", name)
    (directory / "releases").mkdir(exist_ok=True)
    (directory / ".staging").mkdir(exist_ok=True)
    (directory / ".writer.lock").touch(exist_ok=True)


@contextmanager
def _writer(store: Path) -> Generator[None]:
    initialize_store(store)
    with (store / ".writer.lock").open("rb") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise PublicationError("writer_conflict") from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _manifest_document(snapshot: CatalogSnapshot) -> dict[str, object]:
    raw, _ = _capture(snapshot.manifest_path, RECORD_LIMIT)
    if sha256(raw).hexdigest() != snapshot.manifest_sha256:
        raise CatalogError("checksum_mismatch", "manifest")
    return _shape(raw, "market-catalog-release-1")


def _publish(
    entry_path: Path,
    candidate: CatalogSnapshot,
    parent: CatalogSnapshot | None,
    *,
    action: str,
    clock: Callable[[], datetime],
    fault: Callable[[str], None],
    expected_entry_hash: str | None,
) -> PublishedRelease:
    operation = uuid4().hex
    store = entry_path.parent
    staging = store / ".staging" / operation
    destination = store / "releases" / operation
    temporary_entry = store / f".{entry_path.name}-{operation}.tmp"
    attempted_commit = False
    try:
        document = _manifest_document(candidate)
        staging.mkdir()
        captured = dict(candidate.captured)
        audit = next(a for a in candidate.release.artifacts if a.role == "audit")
        ledger_bytes = captured[audit.path]
        if parent is not None:
            prior_audit = next(a for a in parent.release.artifacts if a.role == "audit")
            prior_bytes = dict(parent.captured)[prior_audit.path]
            if not ledger_bytes.startswith(prior_bytes):
                raise PublicationError("ledger_prefix_mismatch")
            old_archive = tuple(
                a for a in parent.release.artifacts if a.role == "migration_archive"
            )
            for archived in old_archive:
                if not any(
                    a.role == "migration_archive" and a.sha256 == archived.sha256
                    for a in candidate.release.artifacts
                ):
                    raise PublicationError("archive_retention_required")
        now = clock()
        parse_utc(now.isoformat(), "publication_clock")
        changed = parent is None or parent.catalog_revision != candidate.catalog_revision
        record: dict[str, object] = {
            "record_type": "publication",
            "record_id": operation,
            "sequence": candidate.ledger[-1].sequence + 1 if candidate.ledger else 1,
            "recorded_at": now.isoformat(),
            "origin": (
                {
                    "table": None,
                    "primary_key": [],
                    "action": (
                        f"recovery-entry:{expected_entry_hash};target:{candidate.manifest_sha256}"
                    ),
                }
                if action == "recovery"
                else None
            ),
            "payload": {
                "operation_id": operation,
                "expected_release": parent.release.release_id if parent else None,
                "action": action,
                "catalog_changed": changed,
            },
        }
        separator = b"\n" if ledger_bytes and not ledger_bytes.endswith(b"\n") else b""
        captured[audit.path] = ledger_bytes + separator + json.dumps(record).encode() + b"\n"
        for path, content in captured.items():
            _write(staging / path, content)
        document.update(
            release_id=operation,
            created_at=now.isoformat(),
            catalog_revision=candidate.catalog_revision,
            parent_release={
                "release_id": parent.release.release_id,
                "manifest_sha256": parent.manifest_sha256,
            }
            if parent
            else None,
        )
        artifacts = _objects(document["artifacts"], "artifacts")
        for artifact in artifacts:
            if artifact["role"] == "audit":
                artifact["sha256"] = sha256(captured[audit.path]).hexdigest()
                artifact["row_count"] = len(candidate.ledger) + 1
        manifest_raw = json.dumps(document, sort_keys=True, indent=2).encode() + b"\n"
        _write(staging / "manifest.json", manifest_raw)
        verified = load_release(staging / "manifest.json")
        if verified.catalog_revision != candidate.catalog_revision:
            raise PublicationError("revision_mismatch")
        for directory, _, _ in os.walk(staging, topdown=False):
            _sync_directory(Path(directory))
        fault("staged")
        os.rename(staging, destination)
        _sync_directory(store / "releases")
        _sync_directory(store / ".staging")
        fault("release_renamed")
        entry = {
            "format": "market-catalog-entry-1",
            "release_id": operation,
            "manifest_path": str((destination / "manifest.json").relative_to(store)),
            "manifest_sha256": sha256(manifest_raw).hexdigest(),
        }
        _write(temporary_entry, json.dumps(entry, sort_keys=True).encode() + b"\n")
        fault("before_commit")
        candidate.check_integrity()
        if parent is not None:
            parent.check_integrity()
        if expected_entry_hash is None:
            if entry_path.exists():
                raise PublicationError("entry_conflict")
        else:
            current_raw, _ = _capture(entry_path, RECORD_LIMIT)
            if sha256(current_raw).hexdigest() != expected_entry_hash:
                raise PublicationError("entry_conflict")
        attempted_commit = True
        os.replace(temporary_entry, entry_path)
        fault("after_commit")
        _sync_directory(store)
        return PublishedRelease(
            operation, candidate.catalog_revision, changed, destination / "manifest.json"
        )
    except (OSError, CatalogError) as error:
        if attempted_commit:
            raise PublicationError(
                "commit_indeterminate",
                publication_state="unknown",
                operation_id=operation,
                expected_release=parent.release.release_id if parent else None,
            ) from None
        code = error.code if isinstance(error, CatalogError) else "publication_io"
        raise PublicationError(
            code,
            operation_id=operation,
            expected_release=parent.release.release_id if parent else None,
        ) from None
    finally:
        if not attempted_commit:
            try:
                if temporary_entry.exists():
                    temporary_entry.unlink()
                if staging.exists():
                    shutil.rmtree(staging)
            except OSError:
                raise PublicationError("staging_cleanup_failed") from None


def _noop_fault(point: str) -> None:
    pass


def activate_release(
    entry_path: Path,
    manifest_path: Path,
    *,
    expected_release: str | None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    fault: Callable[[str], None] = _noop_fault,
) -> PublishedRelease:
    entry_path = entry_path.absolute()
    with _writer(entry_path.parent):
        expected_entry_hash = (
            sha256(_capture(entry_path, RECORD_LIMIT)[0]).hexdigest()
            if entry_path.exists()
            else None
        )
        parent = CatalogReader().read(entry_path) if entry_path.exists() else None
        if (parent.release.release_id if parent else None) != expected_release:
            raise PublicationError("release_conflict")
        candidate = load_release(manifest_path)
        return _publish(
            entry_path,
            candidate,
            parent,
            action="activation" if parent else "bootstrap",
            clock=clock,
            fault=fault,
            expected_entry_hash=expected_entry_hash,
        )


def recover_release(
    entry_path: Path,
    manifest_path: Path,
    *,
    target_sha256: str,
    expected_entry_sha256: str,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> PublishedRelease:
    require_hash(target_sha256, "target_sha256")
    require_hash(expected_entry_sha256, "expected_entry_sha256")
    entry_path = entry_path.absolute()
    with _writer(entry_path.parent):
        raw, _ = _capture(entry_path, RECORD_LIMIT)
        if sha256(raw).hexdigest() != expected_entry_sha256:
            raise PublicationError("entry_conflict")
        candidate = load_release(manifest_path)
        if candidate.manifest_sha256 != target_sha256:
            raise CatalogError("checksum_mismatch", "recovery_target")
        if candidate.release.catalog_revision != candidate.catalog_revision:
            raise CatalogError("revision_mismatch", "recovery_target")
        try:
            parent = CatalogReader().read(entry_path)
        except CatalogError as error:
            if error.code == "concurrent_edit":
                raise
            try:
                current = _shape(raw, "market-catalog-entry-1")
            except CatalogError:
                current = None
            if current is not None and current["release_id"] != candidate.release.release_id:
                raise PublicationError("recovery_history_unavailable") from None
            parent = candidate
        return _publish(
            entry_path,
            candidate,
            parent,
            action="recovery",
            clock=clock,
            fault=_noop_fault,
            expected_entry_hash=expected_entry_sha256,
        )
