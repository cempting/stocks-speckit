"""Immutable local research evidence, identities, and observation comparisons."""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import cast

REPORT_VERSION = "local-etf-discovery-1"


def identity(*values: object) -> str:
    return sha256(json.dumps(values, ensure_ascii=True, sort_keys=True).encode()).hexdigest()


def fields(text: str) -> dict[str, object]:
    value: object = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Invalid persisted local ETF record")
    return cast(dict[str, object], value)


def text_field(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Invalid persisted local ETF field: {key}")
    return value


def optional_text(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"Invalid persisted local ETF field: {key}")
    return value


def integer_field(data: dict[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Invalid persisted local ETF field: {key}")
    return value


def sequence_field(data: dict[str, object], key: str) -> tuple[object, ...]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Invalid persisted local ETF field: {key}")
    return tuple(cast(list[object], value))


def strings_field(data: dict[str, object], key: str) -> tuple[str, ...]:
    values = sequence_field(data, key)
    if any(not isinstance(value, str) for value in values):
        raise ValueError(f"Invalid persisted local ETF field: {key}")
    return cast(tuple[str, ...], values)


@dataclass(frozen=True, slots=True)
class Evidence:
    resource: str
    root: str
    file: str
    catalog: str
    label: str
    ticker: str
    catalog_type: str
    region: str | None
    classification: str | None
    node_level: str | None
    ordinal: int
    line: int
    end_line: int
    column: int
    end_column: int
    catalog_content_id: str
    context: tuple[str, ...]
    observed_at: str

    def __post_init__(self) -> None:
        if self.catalog_type not in (
            "industry",
            "sector_context",
            "index_context",
            "commodity_context",
        ):
            raise ValueError("Unsupported local ETF evidence catalog type")
        if not self.label.strip() or not self.ticker.strip():
            raise ValueError("Local ETF evidence label/ticker must not be empty")
        if self.ordinal < 0 or self.line < 1 or self.end_line < self.line:
            raise ValueError("Invalid local ETF declaration location")

    @property
    def normalized_ticker(self) -> str:
        return self.ticker.strip().upper()

    @property
    def scope_key(self) -> tuple[str, str | None, str | None, str | None]:
        return (self.label, self.region, self.classification, self.node_level)

    @property
    def source_key(self) -> str:
        return identity(self.resource, self.root, self.file, self.catalog)

    @property
    def candidate_id(self) -> str | None:
        if self.catalog_type != "industry":
            return None
        return identity(
            self.label,
            self.normalized_ticker,
            self.catalog_type,
            self.region,
            self.classification,
            self.node_level,
        )

    @property
    def semantic_fingerprint(self) -> str:
        return identity(
            self.label,
            self.ticker,
            self.catalog_type,
            self.region,
            self.classification,
            self.node_level,
            self.context,
        )

    @property
    def evidence_id(self) -> str:
        return identity(
            self.source_key,
            self.catalog_content_id,
            self.semantic_fingerprint,
            self.ordinal,
            self.line,
            self.end_line,
            self.column,
            self.end_column,
        )

    @classmethod
    def decode(cls, payload: str) -> "Evidence":
        data = fields(payload)
        return cls(
            resource=text_field(data, "resource"),
            root=text_field(data, "root"),
            file=text_field(data, "file"),
            catalog=text_field(data, "catalog"),
            label=text_field(data, "label"),
            ticker=text_field(data, "ticker"),
            catalog_type=text_field(data, "catalog_type"),
            region=optional_text(data, "region"),
            classification=optional_text(data, "classification"),
            node_level=optional_text(data, "node_level"),
            ordinal=integer_field(data, "ordinal"),
            line=integer_field(data, "line"),
            end_line=integer_field(data, "end_line"),
            column=integer_field(data, "column"),
            end_column=integer_field(data, "end_column"),
            catalog_content_id=text_field(data, "catalog_content_id"),
            observed_at=text_field(data, "observed_at"),
            context=strings_field(data, "context"),
        )


@dataclass(frozen=True, slots=True)
class CatalogObservation:
    source_key: str
    file: str
    catalog: str
    complete: bool
    content_id: str | None
    evidence_ids: tuple[str, ...]
    issues: tuple[str, ...]

    @classmethod
    def decode(cls, payload: str) -> "CatalogObservation":
        data = fields(payload)
        complete = data.get("complete")
        if not isinstance(complete, bool):
            raise ValueError("Invalid persisted catalog completeness")
        return cls(
            text_field(data, "source_key"),
            text_field(data, "file"),
            text_field(data, "catalog"),
            complete,
            optional_text(data, "content_id"),
            strings_field(data, "evidence_ids"),
            strings_field(data, "issues"),
        )


@dataclass(frozen=True, slots=True)
class ResourceInspection:
    alias: str
    root: str
    status: str
    catalogs: tuple[CatalogObservation, ...]
    issues: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in (
            "inspected",
            "inspected_with_issues",
            "missing",
            "inaccessible",
            "unsupported",
        ):
            raise ValueError("Invalid local ETF resource inspection status")

    @classmethod
    def decode(cls, payload: str) -> "ResourceInspection":
        data = fields(payload)
        return cls(
            text_field(data, "alias"),
            text_field(data, "root"),
            text_field(data, "status"),
            tuple(
                CatalogObservation.decode(json.dumps(item))
                for item in sequence_field(data, "catalogs")
            ),
            strings_field(data, "issues"),
        )


@dataclass(frozen=True, slots=True)
class CollectionRun:
    run_id: str
    observed_at: str
    status: str
    resources: tuple[ResourceInspection, ...]

    def __post_init__(self) -> None:
        if self.status not in ("complete", "partial", "failed"):
            raise ValueError("Invalid local ETF collection status")

    @classmethod
    def decode(cls, payload: str) -> "CollectionRun":
        data = fields(payload)
        return cls(
            text_field(data, "run_id"),
            text_field(data, "observed_at"),
            text_field(data, "status"),
            tuple(
                ResourceInspection.decode(json.dumps(item))
                for item in sequence_field(data, "resources")
            ),
        )


def qualification_issues(
    item: Evidence,
    *,
    region: str | None = None,
    classification: str | None = None,
    node_level: str | None = None,
) -> tuple[str, ...]:
    issues = ["unknown_instrument_type"]
    for field, value in (
        ("region", item.region),
        ("classification", item.classification),
        ("node_level", item.node_level),
    ):
        if value is None:
            issues.append(f"unknown_{field}")
    for field, declared, target in (
        ("region", item.region, region),
        ("classification", item.classification, classification),
        ("node_level", item.node_level, node_level),
    ):
        if declared is not None and target is not None and declared != target:
            issues.append(f"declared_{field}_mismatch")
    if item.normalized_ticker.startswith("^"):
        issues.append("non_etf")
    for prefix, issue in (
        ("sector_context:", "broad_sector_proxy"),
        ("index_context:", "index_proxy"),
        ("commodity_context:", "commodity_proxy"),
        ("thematic_context:", "thematic_proxy"),
    ):
        if any(context.startswith(prefix) for context in item.context):
            issues.append(issue)
    return tuple(sorted(set(issues)))


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    evidence: tuple[Evidence, ...]

    @property
    def issues(self) -> tuple[str, ...]:
        return tuple(
            sorted({issue for item in self.evidence for issue in qualification_issues(item)})
        )


def group_candidates(evidence: tuple[Evidence, ...]) -> tuple[Candidate, ...]:
    groups: dict[str, list[Evidence]] = defaultdict(list)
    for item in evidence:
        if item.candidate_id is not None:
            groups[item.candidate_id].append(item)
    return tuple(
        Candidate(key, tuple(sorted(items, key=lambda item: item.evidence_id)))
        for key, items in sorted(groups.items())
    )


@dataclass(frozen=True, slots=True)
class EvidenceChange:
    source_key: str
    evidence_id: str
    state: str


@dataclass(frozen=True, slots=True)
class Inventory:
    run: CollectionRun
    evidence: tuple[Evidence, ...]
    changes: tuple[EvidenceChange, ...] = ()

    @property
    def candidates(self) -> tuple[Candidate, ...]:
        return group_candidates(self.evidence)

    def candidate_reports(self) -> list[dict[str, object]]:
        candidates: list[dict[str, object]] = []
        for candidate in self.candidates:
            first = candidate.evidence[0]
            candidates.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "label": first.label,
                    "ticker": first.ticker,
                    "normalized_ticker": first.normalized_ticker,
                    "declared_region": first.region,
                    "declared_classification": first.classification,
                    "declared_node_level": first.node_level,
                    "issues": candidate.issues,
                    "occurrences": [
                        {**asdict(item), "evidence_id": item.evidence_id}
                        for item in candidate.evidence
                    ],
                }
            )
        return candidates

    def report(self) -> dict[str, object]:
        return {
            "report_version": REPORT_VERSION,
            "collection_run_id": self.run.run_id,
            "observed_at": self.run.observed_at,
            "status": self.run.status,
            "resources": [
                {
                    **asdict(resource),
                    "declaration_count": sum(len(c.evidence_ids) for c in resource.catalogs),
                    "catalogs": [
                        {**asdict(c), "declaration_count": len(c.evidence_ids)}
                        for c in resource.catalogs
                    ],
                }
                for resource in self.run.resources
            ],
            "candidates": self.candidate_reports(),
            "context": [
                {**asdict(item), "evidence_id": item.evidence_id}
                for item in self.evidence
                if item.catalog_type != "industry"
            ],
            "changes": [asdict(change) for change in self.changes],
        }


def compare_observations(
    current: Inventory, previous: tuple[Inventory, ...]
) -> tuple[EvidenceChange, ...]:
    baselines: dict[str, tuple[Evidence, ...]] = {}
    for inventory in previous:
        for resource in inventory.run.resources:
            for catalog in resource.catalogs:
                if catalog.complete:
                    baselines[catalog.source_key] = tuple(
                        item for item in inventory.evidence if item.source_key == catalog.source_key
                    )
    catalogs = {
        catalog.source_key: catalog
        for resource in current.run.resources
        for catalog in resource.catalogs
    }
    changes: list[EvidenceChange] = []
    for source, evidence in sorted(baselines.items()):
        observation = catalogs.get(source)
        now = tuple(item for item in current.evidence if item.source_key == source)
        for item in evidence:
            if observation is None or not observation.complete:
                state = "unknown"
            elif any(item.semantic_fingerprint == e.semantic_fingerprint for e in now):
                continue
            else:
                state = "changed" if any(item.label == e.label for e in now) else "removed"
            changes.append(EvidenceChange(source, item.evidence_id, state))
    return tuple(changes)


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    review_id: str
    event_order: int
    candidate_id: str
    region_id: str
    classification_id: str
    entity_id: str
    as_of: str
    run_id: str
    decision: str
    reason: str
    review_reference: str
    evidence_ids: tuple[str, ...]
    confirmations: tuple[bool, bool, bool]
    resolutions: tuple[tuple[str, str], ...]
    observed_at: str

    @classmethod
    def decode(cls, payload: str) -> "ReviewDecision":
        data = fields(payload)
        confirmations = sequence_field(data, "confirmations")
        if len(confirmations) != 3 or any(not isinstance(value, bool) for value in confirmations):
            raise ValueError("Invalid persisted reviewer confirmations")
        resolutions: list[tuple[str, str]] = []
        for entry in sequence_field(data, "resolutions"):
            if not isinstance(entry, list):
                raise ValueError("Invalid persisted issue resolution")
            pair = cast(list[object], entry)
            if len(pair) != 2:
                raise ValueError("Invalid persisted issue resolution")
            left, right = pair
            if not isinstance(left, str) or not isinstance(right, str):
                raise ValueError("Invalid persisted issue resolution")
            resolutions.append((left, right))
        return cls(
            text_field(data, "review_id"),
            integer_field(data, "event_order"),
            text_field(data, "candidate_id"),
            text_field(data, "region_id"),
            text_field(data, "classification_id"),
            text_field(data, "entity_id"),
            text_field(data, "as_of"),
            text_field(data, "run_id"),
            text_field(data, "decision"),
            text_field(data, "reason"),
            text_field(data, "review_reference"),
            strings_field(data, "evidence_ids"),
            cast(tuple[bool, bool, bool], confirmations),
            tuple(resolutions),
            text_field(data, "observed_at"),
        )


@dataclass(frozen=True, slots=True)
class ResearchSnapshot:
    inventories: tuple[Inventory, ...]
    reviews: tuple[ReviewDecision, ...]

    @property
    def latest(self) -> Inventory:
        if not self.inventories:
            raise ValueError("No persisted ETF collection is available")
        return self.inventories[-1]


def selected_review(
    reviews: tuple[ReviewDecision, ...],
    region: str,
    classification: str,
    node: str,
) -> ReviewDecision | None:
    selected = None
    for review in sorted(reviews, key=lambda item: item.event_order):
        if (review.region_id, review.classification_id, review.entity_id) != (
            region,
            classification,
            node,
        ):
            continue
        if review.decision == "accept":
            selected = review
        elif selected is not None and selected.candidate_id == review.candidate_id:
            selected = None
    return selected


def review_evidence(review: ReviewDecision, snapshot: ResearchSnapshot) -> tuple[Evidence, ...]:
    inventory = next((i for i in snapshot.inventories if i.run.run_id == review.run_id), None)
    if inventory is None:
        raise ValueError("Candidate review refers to an unknown collection run")
    selected = tuple(e for e in inventory.evidence if e.evidence_id in review.evidence_ids)
    if len(selected) != len(review.evidence_ids) or any(
        e.candidate_id != review.candidate_id for e in selected
    ):
        raise ValueError("Candidate review evidence is inconsistent with its collection")
    return selected


def scope_compatible(evidence: Evidence, region: str, classification: str) -> bool:
    return evidence.region in (None, region) and evidence.classification in (None, classification)


def binding_nodes(
    candidate: Candidate,
    snapshot: ResearchSnapshot,
    region: str,
    classification: str,
) -> tuple[str, ...]:
    nodes: set[str] = set()
    for review in snapshot.reviews:
        if (
            review.decision != "accept"
            or review.region_id != region
            or review.classification_id != classification
        ):
            continue
        for supported in review_evidence(review, snapshot):
            if any(
                e.source_key == supported.source_key and e.scope_key == supported.scope_key
                for e in candidate.evidence
            ):
                nodes.add(review.entity_id)
    return tuple(sorted(nodes))


def support_reasons(review: ReviewDecision, snapshot: ResearchSnapshot) -> tuple[str, ...]:
    original = next(i for i in snapshot.inventories if i.run.run_id == review.run_id)
    supported = review_evidence(review, snapshot)
    old_catalogs = {c.source_key: c for r in original.run.resources for c in r.catalogs}
    latest = snapshot.latest
    current_catalogs = {c.source_key: c for r in latest.run.resources for c in r.catalogs}
    reasons: set[str] = set()
    for evidence in supported:
        old = old_catalogs.get(evidence.source_key)
        current = current_catalogs.get(evidence.source_key)
        if old is None or not old.complete:
            reasons.add("support_was_not_completely_reviewed")
        if current is None or not current.complete:
            reasons.add("unobservable_support")
        elif not any(
            e.source_key == evidence.source_key
            and e.semantic_fingerprint == evidence.semantic_fingerprint
            for e in latest.evidence
        ):
            unknown_context = any(
                context.catalog_type != "industry"
                and context.normalized_ticker == evidence.normalized_ticker
                and (
                    context.source_key not in current_catalogs
                    or not current_catalogs[context.source_key].complete
                )
                for context in original.evidence
            )
            declaration_unchanged = any(
                e.source_key == evidence.source_key
                and e.scope_key == evidence.scope_key
                and e.ticker == evidence.ticker
                and e.catalog_type == evidence.catalog_type
                for e in latest.evidence
            )
            reasons.add(
                "unobservable_qualification_context"
                if unknown_context and declaration_unchanged
                else "changed_or_removed_support"
            )
    labels = {e.label for e in supported}
    tickers = {e.normalized_ticker for e in supported}

    def alternatives(inventory: Inventory) -> set[tuple[str, str]]:
        bound = {
            candidate.candidate_id
            for candidate in inventory.candidates
            if review.entity_id
            in binding_nodes(
                candidate,
                snapshot,
                review.region_id,
                review.classification_id,
            )
        }
        return {
            (e.source_key, e.semantic_fingerprint)
            for e in inventory.evidence
            if e.catalog_type == "industry"
            and e.normalized_ticker not in tickers
            and (
                (
                    e.label in labels
                    and scope_compatible(e, review.region_id, review.classification_id)
                )
                or e.candidate_id in bound
            )
        }

    if alternatives(latest) - alternatives(original):
        reasons.add("new_or_changed_conflicting_evidence")
    for context in original.evidence:
        if context.catalog_type != "industry" and context.normalized_ticker in tickers:
            observation = current_catalogs.get(context.source_key)
            if observation is None or not observation.complete:
                reasons.add("unobservable_qualification_context")
    return tuple(sorted(reasons))


def validate_review(
    review: ReviewDecision,
    evidence: tuple[Evidence, ...],
    *,
    node_level: str,
) -> None:
    if review.decision not in ("accept", "reject"):
        raise ValueError("Candidate review decision must be accept or reject")
    if not review.reason.strip() or not review.review_reference.strip():
        raise ValueError("Candidate review reason and reference must not be empty")
    if (
        not review.evidence_ids
        or len(set(review.evidence_ids)) != len(review.evidence_ids)
        or {e.evidence_id for e in evidence} != set(review.evidence_ids)
        or any(e.candidate_id != review.candidate_id for e in evidence)
    ):
        raise ValueError("Review requires a non-empty consistent candidate/run evidence selection")
    if len(review.confirmations) != 3:
        raise ValueError("Candidate review confirmations must be three explicit booleans")
    resolutions = dict(review.resolutions)
    if len(resolutions) != len(review.resolutions) or any(
        not issue.strip() or not rationale.strip() for issue, rationale in review.resolutions
    ):
        raise ValueError("Issue resolutions must be unique and non-empty")
    if review.decision == "reject":
        return
    issues = {
        issue
        for e in evidence
        for issue in qualification_issues(
            e,
            region=review.region_id,
            classification=review.classification_id,
            node_level=node_level,
        )
    }
    if "non_etf" in issues:
        raise ValueError("Known index/non-ETF evidence cannot be accepted as an ETF")
    if not all(review.confirmations):
        raise ValueError(
            "Acceptance requires ETF identity, exact scope, and suitability confirmations"
        )
    unresolved = issues - resolutions.keys()
    if unresolved:
        raise ValueError(
            f"Candidate review requires issue resolutions: {', '.join(sorted(unresolved))}"
        )
    if resolutions.keys() - issues:
        raise ValueError("Candidate review contains unknown issue resolutions")
