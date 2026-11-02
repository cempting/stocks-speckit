from dataclasses import replace
from datetime import UTC, date, datetime
from hashlib import sha256

import pytest

from market_data.domain.company_evidence import (
    CompanyAssociation,
    CompanyEvidenceRequest,
    CompanyResearchClaim,
    EvidenceProvenance,
    FinancialObservation,
    SourceAssessment,
    company_association_fingerprint,
    company_association_id,
    verify_company_association,
)


def _provenance(*, observed_at: datetime | None = None) -> EvidenceProvenance:
    return EvidenceProvenance(
        source_id="source",
        provider_id="yfinance",
        assessment_fingerprint="a" * 64,
        source_url="https://example.test/filing",
        locator="income statement / Revenue",
        publication_date=date(2025, 12, 31),
        publication_precision="day",
        observed_at=observed_at or datetime(2026, 1, 2, tzinfo=UTC),
        period_start=date(2025, 10, 1),
        period_end=date(2025, 12, 31),
        payload_sha256=sha256(b"source evidence").hexdigest(),
        schema_revision="1",
        limitations=(),
    )


def _association(
    *,
    company_id: str | None = None,
    issuer_key: str | None = None,
    instrument_id: str = "share-class-a",
    listing_id: str = "listing-a",
) -> CompanyAssociation:
    return CompanyAssociation(
        association_id=company_association_id(
            instrument_id=instrument_id,
            listing_id=listing_id,
            source_id="yfinance",
            effective_from=date(2020, 1, 1),
            effective_to=None,
        ),
        instrument_id=instrument_id,
        listing_id=listing_id,
        region_id="US",
        company_id=company_id,
        provider_id="yfinance",
        provider_symbol="EXAMPLE",
        exchange="NASDAQ",
        trading_currency="USD",
        catalog_revision="b" * 64,
        effective_from=date(2020, 1, 1),
        effective_to=None,
        issuer_key=issuer_key,
        cik=None,
        issuer_domain="example.test",
        binding_reference="binding-review",
        identity_evidence="verified-domain-profile",
        state="verified",
        reason=None,
        research_binding_reference="research-binding-review",
        research_identity_evidence="verified-domain-profile",
    )


def test_company_association_preserves_nullable_issuer_ids_and_listing_identity() -> None:
    association = _association()

    assert association.company_id is None
    assert association.cik is None
    assert association.association_id != "example.test"
    assert association.association_id == company_association_id(
        instrument_id="share-class-a",
        listing_id="listing-a",
        source_id="yfinance",
        effective_from=date(2020, 1, 1),
        effective_to=None,
    )


def test_association_technical_identity_changes_with_binding_scope() -> None:
    assert _association().association_id != company_association_id(
        instrument_id="share-class-b",
        listing_id="listing-a",
        source_id="yfinance",
        effective_from=date(2020, 1, 1),
        effective_to=None,
    )


def test_canonical_domain_binding_is_not_compared_to_provider_discriminator() -> None:
    association = _association(issuer_key="domain:example.test")

    verified = verify_company_association(
        replace(association, state="unresolved", identity_evidence=None),
        as_of=date(2026, 1, 2),
        profile_issuer_key="provider-generated-uuid",
        profile_cik=None,
        profile_domain="example.test",
        profile_evidence_reference="profile-capture",
    )

    assert verified.state == "verified"


def test_listing_bindings_keep_trading_currency_and_financial_identity_separate() -> None:
    first = _association()
    second = replace(
        _association(
            instrument_id="share-class-b",
            listing_id="listing-b",
        ),
        trading_currency="EUR",
    )

    assert first.trading_currency == "USD"
    assert second.trading_currency == "EUR"
    assert first.association_id != second.association_id


def test_source_permissions_are_independent_by_role_and_use() -> None:
    financial = SourceAssessment(
        assessment_id="assessment-financial",
        source_id="source",
        role="financial",
        status="approved",
        allowed_uses=("collection", "display", "normalized_retention"),
        reviewed_at=date(2025, 1, 1),
        review_reference="review-financial",
        expires_at=None,
        fingerprint="a" * 64,
    )
    research = SourceAssessment(
        assessment_id="assessment-research",
        source_id="source",
        role="disclosure",
        status="denied",
        allowed_uses=(),
        reviewed_at=date(2025, 1, 1),
        review_reference="review-research",
        expires_at=None,
        fingerprint="c" * 64,
    )

    assert financial.permits("display", date(2026, 1, 1), role="financial")
    assert not financial.permits("display", date(2026, 1, 1), role="disclosure")
    assert not research.permits("display", date(2026, 1, 1), role="disclosure")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_financial_observation_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ValueError):
        FinancialObservation(
            observation_id="observation",
            association_id=_association().association_id,
            metric_key="revenue",
            value=value,
            unit="currency",
            currency="USD",
            source_scale=1,
            period_start=date(2025, 10, 1),
            period_end=date(2025, 12, 31),
            basis="quarterly",
            origin="source_supplied",
            definition="reported revenue",
            derivation_input_ids=(),
            provenance=_provenance(),
            state="available",
            reason=None,
        )


def test_financial_observation_retains_original_reporting_context() -> None:
    observation = FinancialObservation(
        observation_id="observation",
        association_id=_association().association_id,
        metric_key="revenue",
        value=1200.0,
        unit="currency",
        currency="EUR",
        source_scale=1000.0,
        period_start=date(2025, 10, 1),
        period_end=date(2025, 12, 31),
        basis="quarterly",
        origin="source_supplied",
        definition="Reported revenue",
        derivation_input_ids=(),
        provenance=_provenance(),
        state="available",
        reason=None,
    )

    assert observation.currency == "EUR"
    assert observation.source_scale == 1000.0
    assert observation.basis == "quarterly"
    assert observation.provenance.observed_at == datetime(2026, 1, 2, tzinfo=UTC)
    assert observation.period_start == date(2025, 10, 1)


def test_claims_keep_provenance_and_research_scope_separate() -> None:
    association = _association(issuer_key="domain:example.test")
    claim = CompanyResearchClaim(
        claim_id="claim",
        association_id=association.association_id,
        issuer_key=association.issuer_key,
        topic="business_model",
        field_key="revenue_model",
        summary="Subscription revenue",
        value=None,
        unit=None,
        currency=None,
        definition="Reported revenue model",
        qualifications="Company-reported",
        kind="management_claim",
        provenance=_provenance(),
        state="available",
        reason=None,
    )
    request = CompanyEvidenceRequest(
        association=association,
        scope="research",
        mode="historical",
        as_of=date(2026, 1, 2),
        provider_id="yfinance",
        source_ids=("source",),
        binding_fingerprint=company_association_fingerprint(association, "research"),
        assessment_fingerprint="a" * 64,
        history_window=4,
        normalization_revision="1",
        schema_revision="1",
        refresh=False,
    )
    assessment = SourceAssessment(
        assessment_id="assessment",
        source_id="source",
        role="disclosure",
        status="approved",
        allowed_uses=("display",),
        reviewed_at=date(2025, 1, 1),
        review_reference="review",
        expires_at=None,
        fingerprint="a" * 64,
    )

    assert claim.eligible_for(
        request, assessment, permission_as_of=date(2026, 1, 2)
    )
    assert claim.provenance.locator == "income statement / Revenue"
    second_share_class = _association(
        issuer_key="domain:example.test",
        instrument_id="share-class-b",
        listing_id="listing-b",
    )
    assert claim.eligible_for(
        replace(
            request,
            association=second_share_class,
            binding_fingerprint=company_association_fingerprint(
                second_share_class, "research"
            ),
        ),
        assessment,
        permission_as_of=date(2026, 1, 2),
    )


def test_stored_claim_reuse_respects_historical_capture_and_age_cutoffs() -> None:
    association = _association(issuer_key="domain:example.test")
    claim = CompanyResearchClaim(
        claim_id="claim",
        association_id=association.association_id,
        issuer_key=association.issuer_key,
        topic="competitive_advantage",
        field_key="moat",
        summary="Company-reported customer switching costs",
        value=None,
        unit=None,
        currency=None,
        definition="Reported competitive advantage",
        qualifications="Company-reported",
        kind="management_claim",
        provenance=_provenance(),
        state="available",
        reason=None,
    )
    request = CompanyEvidenceRequest(
        association=association,
        scope="research",
        mode="historical",
        as_of=date(2026, 1, 2),
        provider_id="yfinance",
        source_ids=("source",),
        binding_fingerprint=company_association_fingerprint(association, "research"),
        assessment_fingerprint="a" * 64,
        history_window=4,
        normalization_revision="1",
        schema_revision="1",
        refresh=False,
    )
    assessment = SourceAssessment(
        assessment_id="assessment",
        source_id="source",
        role="disclosure",
        status="approved",
        allowed_uses=("display", "normalized_retention"),
        reviewed_at=date(2025, 1, 1),
        review_reference="review",
        expires_at=None,
        fingerprint="a" * 64,
    )

    assert not replace(
        claim, provenance=_provenance(observed_at=datetime(2026, 1, 3, tzinfo=UTC))
    ).eligible_for(request, assessment, permission_as_of=date(2026, 1, 2))
    assert not claim.eligible_for(
        replace(request, as_of=date(2027, 4, 1)),
        assessment,
        permission_as_of=date(2027, 4, 1),
    )
    assert not claim.eligible_for(
        replace(
            request,
            scope="financial",
            binding_fingerprint=company_association_fingerprint(
                association, "financial"
            ),
        ),
        assessment,
        permission_as_of=date(2026, 1, 2),
    )
    revoked = replace(
        assessment,
        status="revoked",
        allowed_uses=(),
        reviewed_at=None,
        review_reference=None,
    )
    expired = replace(assessment, expires_at=date(2025, 12, 31))
    financial_only = replace(assessment, role="financial")
    assert not claim.eligible_for(request, revoked, permission_as_of=date(2026, 1, 2))
    assert not claim.eligible_for(request, expired, permission_as_of=date(2026, 1, 2))
    assert not claim.eligible_for(
        request, financial_only, permission_as_of=date(2026, 1, 2)
    )


def test_research_claim_rejects_future_capture_and_unnamed_opinion() -> None:
    with pytest.raises(ValueError):
        CompanyResearchClaim(
            claim_id="claim",
            association_id=_association().association_id,
            issuer_key=None,
            topic="competitive_advantage",
            field_key="moat",
            summary="Strong moat",
            value=None,
            unit=None,
            currency=None,
            definition="Opinion",
            qualifications="",
            kind="independent_opinion",
            provenance=_provenance(observed_at=datetime(2026, 1, 3, tzinfo=UTC)),
            state="available",
            reason=None,
        )
