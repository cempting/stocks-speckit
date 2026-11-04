"""Typed issuer, listing, financial, and stored research evidence records."""

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime, time
from hashlib import sha256
from math import isfinite
from typing import Literal
from urllib.parse import urlsplit

AssociationState = Literal["verified", "unresolved", "mismatch", "expired"]
AssessmentRole = Literal["financial", "disclosure", "reference"]
AssessmentStatus = Literal["unreviewed", "approved", "denied", "revoked"]
EvidenceUse = Literal["collection", "display", "normalized_retention", "raw_retention"]
FinancialBasis = Literal["quarterly", "annual", "ytd", "unknown"]
ObservationOrigin = Literal["source_supplied", "derived"]
ObservationState = Literal[
    "available",
    "not_loaded",
    "insufficient",
    "unavailable",
    "not_comparable",
    "stale",
    "error",
]
ClaimTopic = Literal["business_model", "competitive_advantage", "orders"]
ClaimKind = Literal["reported_fact", "management_claim", "independent_opinion"]
ClaimState = Literal[
    "not_loaded",
    "available",
    "not_disclosed",
    "unsupported_structure",
    "not_comparable",
    "stale",
    "blocked",
    "error",
]
EvidenceScope = Literal["financial", "research"]
EvidenceMode = Literal["current", "historical"]
OutcomeState = Literal["complete", "partial", "blocked", "error"]


def _text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"{field} must be nonempty text")


def _hash(value: object, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _utc(value: datetime, field: str) -> None:
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field} must be timezone-aware UTC")


def company_association_id(
    *,
    instrument_id: str,
    listing_id: str,
    source_id: str,
    effective_from: date,
    effective_to: date | None,
) -> str:
    for field, value in (
        ("instrument_id", instrument_id),
        ("listing_id", listing_id),
        ("source_id", source_id),
    ):
        _text(value, field)
    material = {
        "effective_from": effective_from.isoformat(),
        "effective_to": effective_to.isoformat() if effective_to else None,
        "instrument_id": instrument_id,
        "listing_id": listing_id,
        "source_id": source_id,
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_company_association(
    association: "CompanyAssociation",
    *,
    as_of: date,
    profile_issuer_key: str | None,
    profile_cik: str | None,
    profile_domain: str | None,
    profile_evidence_reference: str | None,
) -> "CompanyAssociation":
    if not association.active_on(as_of):
        return replace(association, state="expired", reason="Listing binding is outside its dates")
    if not association.binding_reference:
        return replace(
            association, state="unresolved", reason="No independently reviewed issuer binding"
        )
    if not profile_evidence_reference:
        return replace(
            association, state="unresolved", reason="Issuer profile evidence is unavailable"
        )
    if profile_cik is not None and re.fullmatch(r"[0-9]{10}", profile_cik) is None:
        return replace(association, state="unresolved", reason="Issuer profile CIK is invalid")

    comparisons: list[bool] = []
    if (
        association.issuer_key is not None
        and not association.issuer_key.startswith(("cik:", "domain:"))
        and profile_issuer_key is not None
    ):
        comparisons.append(association.issuer_key == profile_issuer_key)
    if association.cik is not None and profile_cik is not None:
        comparisons.append(association.cik == profile_cik)
    if association.issuer_domain is not None and profile_domain is not None:
        comparisons.append(
            association.issuer_domain.rstrip(".").casefold()
            == profile_domain.rstrip(".").casefold()
        )
    if any(not match for match in comparisons):
        return replace(
            association,
            state="mismatch",
            reason="Profile conflicts with the reviewed issuer binding",
        )
    if not any(comparisons):
        return replace(
            association,
            state="unresolved",
            reason="Profile does not corroborate the issuer binding",
        )
    return replace(
        association,
        state="verified",
        identity_evidence=profile_evidence_reference,
        reason=None,
    )


@dataclass(frozen=True, slots=True)
class CompanyAssociation:
    association_id: str
    instrument_id: str
    listing_id: str
    region_id: str
    company_id: str | None
    provider_id: str
    provider_symbol: str
    exchange: str
    trading_currency: str
    catalog_revision: str
    effective_from: date
    effective_to: date | None
    issuer_key: str | None
    cik: str | None
    issuer_domain: str | None
    binding_reference: str | None
    identity_evidence: str | None
    state: AssociationState
    reason: str | None
    research_binding_reference: str | None = None
    research_identity_evidence: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "association_id",
            "instrument_id",
            "listing_id",
            "region_id",
            "provider_id",
            "provider_symbol",
            "exchange",
            "trading_currency",
        ):
            _text(getattr(self, field), field)
        _hash(self.association_id, "association_id")
        _hash(self.catalog_revision, "catalog_revision")
        for field in ("company_id", "issuer_key", "issuer_domain"):
            value = getattr(self, field)
            if value is not None:
                _text(value, field)
        if self.cik is not None and re.fullmatch(r"[0-9]{10}", self.cik) is None:
            raise ValueError("CIK must contain ten digits")
        if (
            self.trading_currency != self.trading_currency.upper()
            or len(self.trading_currency) != 3
        ):
            raise ValueError("Trading currency must be an uppercase three-letter code")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Association effective period is reversed")
        if self.state not in ("verified", "unresolved", "mismatch", "expired"):
            raise ValueError("Unknown issuer association state")
        if self.state == "verified":
            _text(self.binding_reference, "binding_reference")
            _text(self.identity_evidence, "identity_evidence")
        if self.reason is not None:
            _text(self.reason, "reason")
        if self.research_binding_reference is not None:
            _text(self.research_binding_reference, "research_binding_reference")
        if self.research_identity_evidence is not None:
            _text(self.research_identity_evidence, "research_identity_evidence")
        if (self.research_binding_reference is None) != (
            self.research_identity_evidence is None
        ):
            raise ValueError("Research issuer binding and evidence must be recorded together")
        expected = company_association_id(
            instrument_id=self.instrument_id,
            listing_id=self.listing_id,
            source_id=self.provider_id,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
        )
        if self.association_id != expected:
            raise ValueError("Association ID does not match the captured listing binding")

    def active_on(self, as_of: date) -> bool:
        return (
            self.effective_from <= as_of
            and (self.effective_to is None or as_of <= self.effective_to)
        )


def company_association_fingerprint(
    association: CompanyAssociation, scope: EvidenceScope
) -> str:
    reference = (
        association.binding_reference
        if scope == "financial"
        else association.research_binding_reference
    )
    material = {
        "association_id": association.association_id,
        "catalog_revision": association.catalog_revision,
        "effective_from": association.effective_from.isoformat(),
        "effective_to": (
            association.effective_to.isoformat() if association.effective_to else None
        ),
        "issuer_domain": association.issuer_domain,
        "issuer_key": association.issuer_key,
        "cik": association.cik,
        "scope": scope,
        "binding_reference": reference,
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceAssessment:
    assessment_id: str
    source_id: str
    role: AssessmentRole
    status: AssessmentStatus
    allowed_uses: tuple[EvidenceUse, ...]
    reviewed_at: date | None
    review_reference: str | None
    expires_at: date | None
    fingerprint: str
    publisher: str | None = None
    terms_url: str | None = None
    coverage_reference: str | None = None
    authority: str | None = None
    structured_capabilities: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = ()
    allowed_routes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.assessment_id, "assessment_id")
        _text(self.source_id, "source_id")
        _hash(self.fingerprint, "fingerprint")
        if self.role not in ("financial", "disclosure", "reference"):
            raise ValueError("Unknown source role")
        if self.status not in ("unreviewed", "approved", "denied", "revoked"):
            raise ValueError("Unknown source assessment status")
        if len(set(self.allowed_uses)) != len(self.allowed_uses):
            raise ValueError("Allowed uses must be a unique immutable tuple")
        if any(
            use not in ("collection", "display", "normalized_retention", "raw_retention")
            for use in self.allowed_uses
        ):
            raise ValueError("Unknown source use")
        if self.review_reference is not None:
            _text(self.review_reference, "review_reference")
        for field in ("publisher", "coverage_reference", "authority"):
            value = getattr(self, field)
            if value is not None:
                _text(value, field)
        if self.terms_url is not None:
            _text(self.terms_url, "terms_url")
            parsed_terms_url = urlsplit(self.terms_url)
            if (
                parsed_terms_url.scheme not in ("http", "https")
                or not parsed_terms_url.hostname
                or parsed_terms_url.username
                or parsed_terms_url.password
            ):
                raise ValueError("Terms URLs must be public HTTP(S) URLs without credentials")
        for field, values in (
            ("structured_capabilities", self.structured_capabilities),
            ("allowed_hosts", self.allowed_hosts),
            ("allowed_routes", self.allowed_routes),
        ):
            if type(values) is not tuple or len(set(values)) != len(values):
                raise ValueError(f"{field} must be a unique immutable tuple")
            for value in values:
                _text(value, field)
        for host in self.allowed_hosts:
            if (
                host != host.casefold()
                or urlsplit(f"//{host}").hostname != host
                or "/" in host
                or ":" in host
            ):
                raise ValueError("Allowed hosts must be lowercase hostnames without ports")
        for route in self.allowed_routes:
            if (
                not route.startswith("/")
                or route.startswith("//")
                or ".." in route.split("/")
                or urlsplit(route).query
                or urlsplit(route).fragment
            ):
                raise ValueError("Allowed routes must be safe absolute paths")
        if self.status == "approved" and (self.reviewed_at is None or not self.review_reference):
            raise ValueError("Approved sources require a dated review reference")
        if self.status != "approved" and self.allowed_uses:
            raise ValueError("Unapproved sources cannot authorize uses")
        if self.role == "reference" and self.allowed_uses:
            raise ValueError("Reference-only sources cannot authorize collection or retention")

    def permits(self, use: EvidenceUse, as_of: date, *, role: AssessmentRole) -> bool:
        return (
            role == self.role
            and self.status == "approved"
            and self.reviewed_at is not None
            and self.reviewed_at <= as_of
            and use in self.allowed_uses
            and (self.expires_at is None or as_of <= self.expires_at)
        )


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    source_id: str
    provider_id: str
    assessment_fingerprint: str
    source_url: str | None
    locator: str | None
    publication_date: date | None
    publication_precision: Literal["day", "month", "year", "unknown"]
    observed_at: datetime
    period_start: date | None
    period_end: date | None
    payload_sha256: str
    schema_revision: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("source_id", "provider_id", "schema_revision"):
            _text(getattr(self, field), field)
        _hash(self.assessment_fingerprint, "assessment_fingerprint")
        _hash(self.payload_sha256, "payload_sha256")
        _utc(self.observed_at, "observed_at")
        for field in ("locator",):
            value = getattr(self, field)
            if value is not None:
                _text(value, field)
        if self.source_url is not None:
            _text(self.source_url, "source_url")
            parsed = urlsplit(self.source_url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
                raise ValueError("Source URLs must be public HTTP(S) URLs without credentials")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError("Provenance period is reversed")
        if self.publication_precision not in ("day", "month", "year", "unknown"):
            raise ValueError("Unknown publication precision")


@dataclass(frozen=True, slots=True)
class FinancialObservation:
    observation_id: str
    association_id: str
    metric_key: str
    value: float | None
    unit: str
    currency: str | None
    source_scale: float
    period_start: date | None
    period_end: date
    basis: FinancialBasis
    origin: ObservationOrigin
    definition: str
    derivation_input_ids: tuple[str, ...]
    provenance: EvidenceProvenance
    state: ObservationState
    reason: str | None

    def __post_init__(self) -> None:
        for field in ("observation_id", "association_id", "metric_key", "unit", "definition"):
            _text(getattr(self, field), field)
        if self.value is not None and (
            isinstance(self.value, bool) or not isfinite(self.value)
        ):
            raise ValueError("Financial observations must be finite numbers")
        if (
            isinstance(self.source_scale, bool)
            or not isfinite(self.source_scale)
            or self.source_scale <= 0
        ):
            raise ValueError("Source scale must be finite and positive")
        if self.currency is not None and re.fullmatch(r"[A-Z]{3}", self.currency) is None:
            raise ValueError("Currency must be an uppercase three-letter code")
        if self.period_start is not None and self.period_start > self.period_end:
            raise ValueError("Observation period is reversed")
        if self.basis not in ("quarterly", "annual", "ytd", "unknown"):
            raise ValueError("Unknown financial basis")
        if self.origin not in ("source_supplied", "derived"):
            raise ValueError("Unknown observation origin")
        if self.state not in (
            "available",
            "not_loaded",
            "insufficient",
            "unavailable",
            "not_comparable",
            "stale",
            "error",
        ):
            raise ValueError("Unknown financial observation state")
        if self.reason is not None:
            _text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class IssuerFinancialProjection:
    issuer_key: str
    acquisition_association_id: str
    consumer_association_id: str
    observation: FinancialObservation

    def __post_init__(self) -> None:
        for field in ("issuer_key", "acquisition_association_id", "consumer_association_id"):
            _text(getattr(self, field), field)
        if self.observation.association_id != self.acquisition_association_id:
            raise ValueError("Issuer projection must preserve its acquisition association")


@dataclass(frozen=True, slots=True)
class CompanyResearchClaim:
    claim_id: str
    association_id: str
    issuer_key: str | None
    topic: ClaimTopic
    field_key: str
    summary: str | None
    value: float | None
    unit: str | None
    currency: str | None
    definition: str
    qualifications: str
    kind: ClaimKind
    provenance: EvidenceProvenance
    state: ClaimState
    reason: str | None
    named_source: str | None = None
    inspected_disclosure_scope: str | None = None
    basis: FinancialBasis | None = None

    def __post_init__(self) -> None:
        for field in ("claim_id", "association_id", "field_key", "definition", "qualifications"):
            _text(getattr(self, field), field)
        if self.issuer_key is not None:
            _text(self.issuer_key, "issuer_key")
        if self.topic not in ("business_model", "competitive_advantage", "orders"):
            raise ValueError("Unknown research claim topic")
        if self.summary is not None:
            _text(self.summary, "summary")
        if self.value is not None and (
            isinstance(self.value, bool) or not isfinite(self.value)
        ):
            raise ValueError("Research values must be finite numbers")
        for field in (
            "unit",
            "currency",
            "named_source",
            "inspected_disclosure_scope",
        ):
            value = getattr(self, field)
            if value is not None:
                _text(value, field)
        if self.currency is not None and re.fullmatch(r"[A-Z]{3}", self.currency) is None:
            raise ValueError("Currency must be an uppercase three-letter code")
        if self.state == "available" and self.summary is None and self.value is None:
            raise ValueError("A claim needs a factual summary or a finite value")
        if self.state == "not_disclosed" and self.inspected_disclosure_scope is None:
            raise ValueError("Not-disclosed claims require a successfully inspected scope")
        if self.topic == "orders" and self.state == "available" and self.basis is None:
            raise ValueError("Order claims require their actual reporting basis")
        if self.basis is not None and self.basis not in (
            "quarterly",
            "annual",
            "ytd",
            "unknown",
        ):
            raise ValueError("Unknown research reporting basis")
        if self.kind not in ("reported_fact", "management_claim", "independent_opinion"):
            raise ValueError("Unknown research claim kind")
        if self.kind == "independent_opinion" and self.named_source is None:
            raise ValueError("Independent opinions require a named source")
        if self.state not in (
            "not_loaded",
            "available",
            "not_disclosed",
            "unsupported_structure",
            "not_comparable",
            "stale",
            "blocked",
            "error",
        ):
            raise ValueError("Unknown research claim state")
        if self.reason is not None:
            _text(self.reason, "reason")

    def eligible_for(
        self,
        request: "CompanyEvidenceRequest",
        assessment: SourceAssessment,
        *,
        permission_as_of: date,
        shared_issuer_keys: tuple[str, ...] = (),
    ) -> bool:
        cutoff = datetime.combine(request.as_of, time.max, tzinfo=UTC)
        association = request.association
        age_limit = 135 if self.topic == "orders" and self.basis == "quarterly" else 450
        fresh_after = self.provenance.publication_date is not None and (
            request.as_of - self.provenance.publication_date
        ).days > age_limit
        association_matches = self.association_id == association.association_id or (
            self.issuer_key is not None
            and (
                self.issuer_key == association.issuer_key
                or self.issuer_key in shared_issuer_keys
            )
        )
        return (
            request.scope == "research"
            and request.provider_id == association.provider_id
            and association_matches
            and association.state == "verified"
            and association.active_on(request.as_of)
            and association.research_binding_reference is not None
            and association.research_identity_evidence is not None
            and self.state == "available"
            and assessment.source_id == self.provenance.source_id
            and assessment.source_id in request.source_ids
            and assessment.fingerprint == self.provenance.assessment_fingerprint
            and assessment.fingerprint == request.assessment_fingerprint
            and assessment.permits("display", permission_as_of, role="disclosure")
            and not fresh_after
            and self.provenance.observed_at <= cutoff
        )


@dataclass(frozen=True, slots=True)
class CompanyEvidenceRequest:
    association: CompanyAssociation
    scope: EvidenceScope
    mode: EvidenceMode
    as_of: date
    provider_id: str
    source_ids: tuple[str, ...]
    binding_fingerprint: str
    assessment_fingerprint: str
    history_window: int
    normalization_revision: str
    schema_revision: str
    refresh: bool

    def __post_init__(self) -> None:
        if self.association.state not in ("verified", "unresolved"):
            raise ValueError("Evidence requests require a current, non-conflicting association")
        if self.scope not in ("financial", "research") or self.mode not in (
            "current",
            "historical",
        ):
            raise ValueError("Unknown evidence request scope or mode")
        if self.scope == "research" and (
            self.association.research_binding_reference is None
            or self.association.research_identity_evidence is None
        ):
            raise ValueError("Research requests require a separately reviewed issuer binding")
        _text(self.provider_id, "provider_id")
        _hash(self.binding_fingerprint, "binding_fingerprint")
        _hash(self.assessment_fingerprint, "assessment_fingerprint")
        if self.binding_fingerprint != company_association_fingerprint(
            self.association, self.scope
        ):
            raise ValueError(
                "Request binding fingerprint does not match the reviewed issuer binding"
            )
        if not self.source_ids:
            raise ValueError("Evidence requests require explicit sources")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Evidence request sources must be unique")
        if self.provider_id != self.association.provider_id:
            raise ValueError("Evidence provider does not match the reviewed issuer binding")
        if not 4 <= self.history_window <= 8:
            raise ValueError("Evidence history window must be four to eight quarters")
        _text(self.normalization_revision, "normalization_revision")
        _text(self.schema_revision, "schema_revision")
        if type(self.refresh) is not bool:
            raise ValueError("refresh must be a Boolean")


@dataclass(frozen=True, slots=True)
class CompanyEvidenceOutcome:
    state: OutcomeState
    observations: tuple[FinancialObservation, ...]
    claims: tuple[CompanyResearchClaim, ...]
    failures: tuple[str, ...]
    started_at: datetime
    captured_at: datetime
    completed_at: datetime
    association_state: AssociationState = "verified"
    association_reason: str | None = None
    verified_association: CompanyAssociation | None = None

    def __post_init__(self) -> None:
        if self.state not in ("complete", "partial", "blocked", "error"):
            raise ValueError("Unknown evidence outcome state")
        for field in ("started_at", "captured_at", "completed_at"):
            _utc(getattr(self, field), field)
        if self.started_at > self.completed_at or self.captured_at > self.completed_at:
            raise ValueError("Evidence outcome timestamps are inconsistent")
        if self.association_state not in (
            "verified",
            "unresolved",
            "mismatch",
            "expired",
        ):
            raise ValueError("Unknown evidence association state")
        if self.state in ("complete", "partial") and self.association_state != "verified":
            raise ValueError("Attached evidence requires a verified association")
        if self.verified_association is not None and (
            self.verified_association.state != self.association_state
        ):
            raise ValueError("Outcome association state does not match its verified binding")
        if self.association_reason is not None:
            _text(self.association_reason, "association_reason")
        for failure in self.failures:
            _text(failure, "failure")


@dataclass(frozen=True, slots=True)
class CompanyEvidenceSnapshot:
    version: int
    request: CompanyEvidenceRequest
    outcome: CompanyEvidenceOutcome
    content_sha256: str
    predecessor_sha256: str | None
    policy_references: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValueError("Unsupported company evidence snapshot version")
        _hash(self.content_sha256, "content_sha256")
        if self.predecessor_sha256 is not None:
            _hash(self.predecessor_sha256, "predecessor_sha256")
        for reference in self.policy_references:
            _text(reference, "policy_reference")
        if self.request.scope == "financial" and self.outcome.claims:
            raise ValueError("Financial snapshots cannot contain research claims")
        if self.request.scope == "research" and self.outcome.observations:
            raise ValueError("Research snapshots cannot contain financial observations")
        association_id = self.request.association.association_id
        verified_association = self.outcome.verified_association
        if self.outcome.state in ("complete", "partial") and verified_association is None:
            raise ValueError("Attached evidence must retain its verified issuer association")
        if (
            verified_association is not None
            and verified_association.association_id != association_id
        ):
            raise ValueError("Verified association does not match the request identity")
        if (
            verified_association is not None
            and company_association_fingerprint(verified_association, self.request.scope)
            != self.request.binding_fingerprint
        ):
            raise ValueError("Verified association differs from the requested binding")
        if any(
            item.association_id != association_id
            for item in (*self.outcome.observations, *self.outcome.claims)
        ):
            raise ValueError("Snapshot evidence must retain its acquisition association")
        expected = company_evidence_snapshot_digest(
            request=self.request,
            outcome=self.outcome,
            version=self.version,
            predecessor_sha256=self.predecessor_sha256,
            policy_references=self.policy_references,
        )
        if expected != self.content_sha256:
            raise ValueError("Snapshot content hash does not match its public evidence")


def eligible_research_claims(
    snapshot: CompanyEvidenceSnapshot,
    request: CompanyEvidenceRequest,
    assessments: tuple[SourceAssessment, ...],
    *,
    permission_as_of: date,
) -> tuple[CompanyResearchClaim, ...]:
    if request.scope != "research":
        raise ValueError("Research claims require a research-scope request")
    source = snapshot.outcome.verified_association
    if (
        snapshot.request.scope != "research"
        or snapshot.outcome.state not in ("complete", "partial")
        or snapshot.outcome.association_state != "verified"
        or source is None
        or source.state != "verified"
        or source.research_binding_reference is None
        or source.research_identity_evidence is None
        or request.as_of < snapshot.request.as_of
        or snapshot.outcome.captured_at
        > datetime.combine(request.as_of, time.max, tzinfo=UTC)
    ):
        return ()
    shared_issuer_key = (
        _shared_issuer_key(source, request.association)
        if source.association_id != request.association.association_id
        else None
    )
    if source.association_id != request.association.association_id and shared_issuer_key is None:
        return ()
    shared_issuer_keys = tuple(
        dict.fromkeys(
            key
            for key in (
                source.issuer_key,
                request.association.issuer_key,
                shared_issuer_key,
            )
            if key is not None
        )
    )
    by_source = {assessment.source_id: assessment for assessment in assessments}
    if len(by_source) != len(assessments):
        raise ValueError("Duplicate current source assessments")
    return tuple(
        claim
        for claim in snapshot.outcome.claims
        if (assessment := by_source.get(claim.provenance.source_id)) is not None
        and claim.eligible_for(
            request,
            assessment,
            permission_as_of=permission_as_of,
            shared_issuer_keys=shared_issuer_keys,
        )
    )


def project_issuer_financial_evidence(
    snapshot: CompanyEvidenceSnapshot,
    consumer: CompanyAssociation,
    assessments: tuple[SourceAssessment, ...],
    *,
    as_of: date,
    permission_as_of: date,
) -> tuple[IssuerFinancialProjection, ...]:
    source = snapshot.outcome.verified_association
    if (
        snapshot.request.scope != "financial"
        or snapshot.outcome.association_state != "verified"
        or snapshot.outcome.state not in ("complete", "partial")
        or source is None
        or source.state != "verified"
        or source.association_id == consumer.association_id
        or consumer.state != "verified"
        or not source.active_on(as_of)
        or not consumer.active_on(as_of)
        or snapshot.request.as_of > as_of
        or snapshot.outcome.captured_at
        > datetime.combine(as_of, time.max, tzinfo=UTC)
    ):
        return ()
    issuer_key = _shared_issuer_key(source, consumer)
    if issuer_key is None:
        return ()
    by_fingerprint = {
        assessment.fingerprint: assessment for assessment in assessments
    }
    if len(by_fingerprint) != len(assessments):
        raise ValueError("Duplicate current source assessment fingerprints")
    eligible: list[IssuerFinancialProjection] = []
    for observation in snapshot.outcome.observations:
        assessment = by_fingerprint.get(observation.provenance.assessment_fingerprint)
        if (
            observation.period_end > as_of
            or assessment is None
            or assessment.source_id not in snapshot.request.source_ids
            or assessment.source_id != observation.provenance.source_id
            or assessment.role != "financial"
            or not assessment.permits("display", permission_as_of, role="financial")
            or not assessment.permits(
                "normalized_retention", permission_as_of, role="financial"
            )
        ):
            continue
        eligible.append(
            IssuerFinancialProjection(
                issuer_key=issuer_key,
                acquisition_association_id=source.association_id,
                consumer_association_id=consumer.association_id,
                observation=observation,
            )
        )
    return tuple(eligible)


def _shared_issuer_key(
    source: CompanyAssociation, consumer: CompanyAssociation
) -> str | None:
    if source.cik is not None and source.cik == consumer.cik:
        return f"cik:{source.cik}"
    source_domain = (
        source.issuer_domain.rstrip(".").casefold()
        if source.issuer_domain is not None
        else None
    )
    consumer_domain = (
        consumer.issuer_domain.rstrip(".").casefold()
        if consumer.issuer_domain is not None
        else None
    )
    if source_domain is not None and source_domain == consumer_domain:
        return f"domain:{source_domain}"
    if source.issuer_key is not None and source.issuer_key == consumer.issuer_key:
        return source.issuer_key
    return None


def company_evidence_snapshot_digest(
    *,
    request: CompanyEvidenceRequest,
    outcome: CompanyEvidenceOutcome,
    version: int = 1,
    predecessor_sha256: str | None = None,
    policy_references: tuple[str, ...] = (),
) -> str:
    material = {
        "outcome": asdict(outcome),
        "policy_references": policy_references,
        "predecessor_sha256": predecessor_sha256,
        "request": asdict(request),
        "version": version,
    }
    encoded = json.dumps(
        material,
        default=lambda value: (
            value.isoformat() if isinstance(value, (date, datetime)) else str(value)
        ),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def create_company_evidence_snapshot(
    *,
    request: CompanyEvidenceRequest,
    outcome: CompanyEvidenceOutcome,
    predecessor_sha256: str | None = None,
    policy_references: tuple[str, ...] = (),
) -> CompanyEvidenceSnapshot:
    outcome = (
        replace(outcome, verified_association=request.association)
        if outcome.association_state == "verified" and outcome.verified_association is None
        else outcome
    )
    return CompanyEvidenceSnapshot(
        version=1,
        request=request,
        outcome=outcome,
        content_sha256=company_evidence_snapshot_digest(
            request=request,
            outcome=outcome,
            predecessor_sha256=predecessor_sha256,
            policy_references=policy_references,
        ),
        predecessor_sha256=predecessor_sha256,
        policy_references=policy_references,
    )
