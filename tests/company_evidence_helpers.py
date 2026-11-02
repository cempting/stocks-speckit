"""Source-free helpers for issuer-evidence acceptance tests."""

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast

from market_data.domain.company_evidence import (
    AssessmentRole,
    AssessmentStatus,
    CompanyAssociation,
    CompanyEvidenceOutcome,
    CompanyEvidenceRequest,
    CompanyEvidenceSnapshot,
    CompanyResearchClaim,
    EvidenceProvenance,
    EvidenceScope,
    EvidenceUse,
    SourceAssessment,
    company_association_fingerprint,
    company_association_id,
    create_company_evidence_snapshot,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "acceptance" / "company_evidence"


def load_company_fixture(name: str) -> dict[str, object]:
    path = (FIXTURE_ROOT / name).resolve()
    if FIXTURE_ROOT.resolve() not in path.parents:
        raise ValueError("Fixture path escapes the company-evidence fixture directory")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("synthetic") is not True:
        raise ValueError("Company evidence tests require explicit synthetic fixture data")
    return cast(dict[str, object], data)


def association_for_case(case: dict[str, object]) -> CompanyAssociation:
    case_id = str(case["case"])
    instrument_id = f"instrument-{case_id}"
    listing_id = f"listing-{case_id}"
    effective_from = date(2020, 1, 1)
    return CompanyAssociation(
        association_id=company_association_id(
            instrument_id=instrument_id,
            listing_id=listing_id,
            source_id="yfinance",
            effective_from=effective_from,
            effective_to=None,
        ),
        instrument_id=instrument_id,
        listing_id=listing_id,
        region_id="US",
        company_id=cast(str | None, case.get("expected_company_id")),
        provider_id="yfinance",
        provider_symbol="SYNTHETIC",
        exchange="NASDAQ",
        trading_currency="USD",
        catalog_revision="b" * 64,
        effective_from=effective_from,
        effective_to=None,
        issuer_key=cast(str | None, case.get("binding_issuer_key")),
        cik=cast(str | None, case.get("binding_cik")),
        issuer_domain=cast(str | None, case.get("binding_domain")),
        binding_reference=cast(str | None, case.get("binding_evidence")),
        identity_evidence=None,
        state="unresolved",
        reason="Awaiting profile corroboration",
    )


def verified_association(
    *,
    instrument_id: str = "instrument-a",
    listing_id: str = "listing-a",
    trading_currency: str = "USD",
    provider_symbol: str = "SYNTHETIC",
    exchange: str = "NASDAQ",
    catalog_revision: str = "b" * 64,
    issuer_domain: str | None = "issuer.example",
    research_binding: bool = True,
) -> CompanyAssociation:
    effective_from = date(2020, 1, 1)
    return CompanyAssociation(
        association_id=company_association_id(
            instrument_id=instrument_id,
            listing_id=listing_id,
            source_id="yfinance",
            effective_from=effective_from,
            effective_to=None,
        ),
        instrument_id=instrument_id,
        listing_id=listing_id,
        region_id="US",
        company_id=None,
        provider_id="yfinance",
        provider_symbol=provider_symbol,
        exchange=exchange,
        trading_currency=trading_currency,
        catalog_revision=catalog_revision,
        effective_from=effective_from,
        effective_to=None,
        issuer_key="domain:issuer.example",
        cik=None,
        issuer_domain=issuer_domain,
        binding_reference="synthetic-binding-review",
        identity_evidence="synthetic-profile-capture",
        state="verified",
        reason=None,
        research_binding_reference=(
            "synthetic-research-binding" if research_binding else None
        ),
        research_identity_evidence=(
            "synthetic-research-profile" if research_binding else None
        ),
    )


def request_for(
    association: CompanyAssociation,
    *,
    scope: EvidenceScope = "research",
    as_of: date = date(2026, 1, 2),
    source_ids: tuple[str, ...] = ("reviewed-disclosure",),
) -> CompanyEvidenceRequest:
    return CompanyEvidenceRequest(
        association=association,
        scope=scope,
        mode="historical",
        as_of=as_of,
        provider_id="yfinance",
        source_ids=source_ids,
        binding_fingerprint=company_association_fingerprint(association, scope),
        assessment_fingerprint="a" * 64,
        history_window=4,
        normalization_revision="normalization-1",
        schema_revision="evidence-1",
        refresh=False,
    )


def research_assessment(
    *,
    status: AssessmentStatus = "approved",
    role: AssessmentRole = "disclosure",
    allowed_uses: tuple[EvidenceUse, ...] = ("display", "normalized_retention"),
    expires_at: date | None = None,
) -> SourceAssessment:
    approved = status == "approved"
    return SourceAssessment(
        assessment_id=f"assessment-{role}",
        source_id="reviewed-disclosure",
        role=role,
        status=status,
        allowed_uses=allowed_uses if approved else (),
        reviewed_at=date(2025, 1, 1) if approved else None,
        review_reference="synthetic-review" if approved else None,
        expires_at=expires_at,
        fingerprint="a" * 64,
    )


def financial_assessment(*, status: AssessmentStatus = "approved") -> SourceAssessment:
    approved = status == "approved"
    return SourceAssessment(
        assessment_id="assessment-financial",
        source_id="yfinance",
        role="financial",
        status=status,
        allowed_uses=(
            ("collection", "display", "normalized_retention") if approved else ()
        ),
        reviewed_at=date(2025, 1, 1) if approved else None,
        review_reference="synthetic-financial-review" if approved else None,
        expires_at=None,
        fingerprint="a" * 64,
    )


def research_claim(association: CompanyAssociation) -> CompanyResearchClaim:
    return CompanyResearchClaim(
        claim_id="synthetic-business-model",
        association_id=association.association_id,
        issuer_key=association.issuer_key,
        topic="business_model",
        field_key="revenue_model",
        summary="Synthetic management-reported subscription revenue",
        value=None,
        unit=None,
        currency=None,
        definition="Reported revenue model",
        qualifications="Synthetic; management-reported",
        kind="management_claim",
        provenance=EvidenceProvenance(
            source_id="reviewed-disclosure",
            provider_id="yfinance",
            assessment_fingerprint="a" * 64,
            source_url="https://issuer.example/annual-report",
            locator="Business / Revenue model",
            publication_date=date(2025, 12, 31),
            publication_precision="day",
            observed_at=datetime(2026, 1, 2, 12, tzinfo=UTC),
            period_start=None,
            period_end=date(2025, 12, 31),
            payload_sha256=sha256(b"synthetic disclosure").hexdigest(),
            schema_revision="evidence-1",
            limitations=("Synthetic fixture only",),
        ),
        state="available",
        reason=None,
    )


def snapshot_for(
    request: CompanyEvidenceRequest,
    *,
    claims: tuple[CompanyResearchClaim, ...] = (),
    predecessor_sha256: str | None = None,
) -> CompanyEvidenceSnapshot:
    started_at = datetime(2026, 1, 2, 12, tzinfo=UTC)
    outcome = CompanyEvidenceOutcome(
        state="complete",
        observations=(),
        claims=claims,
        failures=(),
        started_at=started_at,
        captured_at=started_at,
        completed_at=started_at,
    )
    return create_company_evidence_snapshot(
        request=request,
        outcome=outcome,
        predecessor_sha256=predecessor_sha256,
        policy_references=("synthetic-review",),
    )


@dataclass(slots=True)
class EvidenceRequestCounters:
    profile_requests: int = 0
    financial_requests: int = 0
    research_requests: int = 0
    history_requests: int = 0
    persisted_snapshots: int = 0
