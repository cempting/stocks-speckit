from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import cast

import pytest

from market_data.catalog import load_release
from market_data.company_evidence import (
    CompanyEvidenceFiles,
    CompanyEvidenceStoreError,
    RevisionConflictError,
)
from market_data.domain.company_evidence import (
    eligible_research_claims,
    verify_company_association,
)
from market_data.domain.fundamentals import FinancialQuarter, FundamentalBundle
from market_leadership.application.load_company_evidence import load_company_evidence
from tests.company_evidence_helpers import (
    association_for_case,
    financial_assessment,
    load_company_fixture,
    request_for,
    research_assessment,
    research_claim,
    snapshot_for,
    verified_association,
)
from tests.membership_helpers import build_v2_release, membership_fixture


def _cases(value: object) -> tuple[dict[str, object], ...]:
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return tuple(cast(dict[str, object], item) for item in value)


def test_synthetic_profile_and_binding_cases_require_identity_corroboration() -> None:
    fixture = load_company_fixture("financial_cases.json")
    assert fixture["format"] == "company-evidence-financial-cases-1"

    for case in _cases(fixture["cases"]):
        association = association_for_case(case)
        verified = verify_company_association(
            association,
            as_of=date(2026, 1, 2),
            profile_issuer_key=cast(str | None, case.get("profile_issuer_key")),
            profile_cik=cast(str | None, case.get("profile_cik")),
            profile_domain=cast(str | None, case.get("profile_domain")),
            profile_evidence_reference=cast(
                str | None, case.get("profile_evidence_reference")
            ),
        )

        assert verified.state == case["expected_state"], case["case"]
        assert verified.company_id == case["expected_company_id"]
        assert verified.cik == case["expected_cik"]
        if verified.state == "verified":
            assert verified.identity_evidence == case["profile_evidence_reference"]
        else:
            assert verified.reason


def test_reviewed_claim_fixture_keeps_source_kind_qualification_and_locator() -> None:
    fixture = load_company_fixture("disclosures/reviewed_claim_snapshots.json")
    claims = _cases(fixture["claims"])

    assert fixture["format"] == "company-reviewed-claims-1"
    assert {claim["topic"] for claim in claims} == {
        "business_model",
        "competitive_advantage",
    }
    assert all(claim["source_id"] == "reviewed-disclosure" for claim in claims)
    assert all(claim["kind"] == "management_claim" for claim in claims)
    assert all(claim["qualifications"] and claim["locator"] for claim in claims)
    assert all(claim["publication_date"] == "2025-12-31" for claim in claims)


def test_versioned_store_round_trips_records_and_keeps_immutable_history(tmp_path: Path) -> None:
    store = CompanyEvidenceFiles(tmp_path / "evidence")
    association = verified_association()
    request = request_for(association)
    assessment = research_assessment()
    claim = research_claim(association)
    first = snapshot_for(request, claims=(claim,))

    assessment_revision = store.save_source_assessment(
        assessment, expected_revision=None
    )
    binding_revision = store.save_association(association, expected_revision=None)
    first_revision = store.publish_snapshot(first, expected_revision=None)

    assert assessment_revision == assessment.fingerprint
    assert store.load_source_assessment(assessment.source_id) == assessment
    assert store.load_association(association.association_id) == association
    assert store.load_latest_snapshot(association.association_id, "research") == first

    second_request = replace(request, as_of=date(2026, 1, 3))
    second = snapshot_for(
        second_request,
        claims=(claim,),
        predecessor_sha256=first_revision,
    )
    second_revision = store.publish_snapshot(second, expected_revision=first_revision)

    assert second_revision != first_revision
    assert store.load_latest_snapshot(association.association_id, "research") == second
    assert len(tuple((tmp_path / "evidence" / "snapshots").rglob("*.json"))) == 2
    assert binding_revision == store.save_association(
        association, expected_revision=binding_revision
    )
    with pytest.raises(RevisionConflictError):
        store.publish_snapshot(first, expected_revision=None)


def test_evidence_reader_rejects_path_escape_and_corrupt_snapshot(tmp_path: Path) -> None:
    store = CompanyEvidenceFiles(tmp_path / "evidence")

    with pytest.raises(CompanyEvidenceStoreError, match="Unsafe evidence-relative path"):
        store.load_snapshot("../outside.json")

    association = verified_association()
    snapshot = snapshot_for(
        request_for(association),
        claims=(research_claim(association),),
    )
    store.publish_snapshot(snapshot, expected_revision=None)
    snapshot_path = next((tmp_path / "evidence" / "snapshots").rglob("*.json"))
    snapshot_path.write_text('{"format":"corrupt"}', encoding="utf-8")

    with pytest.raises(CompanyEvidenceStoreError):
        store.load_latest_snapshot(association.association_id, "research")


def test_stored_claims_attach_to_verified_share_class_only_with_current_research_grant() -> None:
    source_association = verified_association()
    claim = research_claim(source_association)
    snapshot = snapshot_for(request_for(source_association), claims=(claim,))
    second_share_class = verified_association(
        instrument_id="instrument-b",
        listing_id="listing-b",
        trading_currency="EUR",
    )
    target_request = request_for(second_share_class)
    approved = research_assessment()

    attached = eligible_research_claims(
        snapshot,
        target_request,
        (approved,),
        permission_as_of=date(2026, 1, 2),
    )
    assert attached == (claim,)
    assert attached[0].association_id == source_association.association_id
    assert second_share_class.trading_currency == "EUR"

    for denied_assessment in (
        research_assessment(status="denied"),
        research_assessment(status="revoked"),
        research_assessment(expires_at=date(2025, 12, 31)),
        research_assessment(role="financial"),
    ):
        assert not eligible_research_claims(
            snapshot,
            target_request,
            (denied_assessment,),
            permission_as_of=date(2026, 1, 2),
        )
    assert not eligible_research_claims(
        snapshot,
        replace(target_request, as_of=date(2026, 1, 1)),
        (approved,),
        permission_as_of=date(2026, 1, 2),
    )
    assert not eligible_research_claims(
        snapshot,
        target_request,
        (),
        permission_as_of=date(2026, 1, 2),
    )


def _catalog_snapshot(catalog_release: Path, tmp_path: Path):
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    return load_release(manifest)


def _financial_bundle(
    *,
    profile_state: str = "available",
    profile_domain: str | None = "issuer.example",
) -> FundamentalBundle:
    return FundamentalBundle(
        symbol="FIXTURE",
        provider_id="yfinance",
        fetched_at=datetime(2026, 1, 2, 12, tzinfo=UTC),
        currency="USD",
        income=(
            FinancialQuarter(
                date(2025, 12, 31),
                (("revenue", 120.0), ("net_income", -5.0)),
            ),
        ),
        cash=(),
        balance=(),
        issuer_discriminator=None,
        profile_state=cast(
            str, profile_state
        ),  # values are constrained by the test fixture
        profile_domain=profile_domain,
        trading_currency="USD",
        market_cap=1_200_000_000.0,
        market_cap_as_of=date(2026, 1, 2),
    )


def _financial_request(catalog, *, listing_id: str = "listing-a-primary"):
    association = verified_association(
        instrument_id="share-class-a",
        listing_id=listing_id,
        provider_symbol="FIXTURE" if listing_id == "listing-a-primary" else "FIXTURE.A2",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
        research_binding=False,
    )
    association = replace(
        association,
        state="unresolved",
        identity_evidence=None,
        reason="Awaiting one-ticker profile corroboration",
    )
    request = replace(
        request_for(association, scope="financial", source_ids=("yfinance",)),
        mode="current",
    )
    return association, request


def test_financial_acquisition_requires_listing_and_profile_gate_before_publication(
    catalog_release: Path, tmp_path: Path
) -> None:
    catalog = _catalog_snapshot(catalog_release, tmp_path)
    association, request = _financial_request(catalog)
    calls = 0

    def loader(fundamental_request):
        nonlocal calls
        calls += 1
        assert fundamental_request.symbol == "FIXTURE"
        return _financial_bundle()

    result = load_company_evidence(
        request,
        catalog=catalog,
        assessments=(financial_assessment(),),
        store=CompanyEvidenceFiles(tmp_path / "evidence"),
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        financial_loader=loader,
    )

    assert calls == 1
    assert result.association.state == "verified"
    assert result.outcome.state == "complete"
    reported = tuple(
        item for item in result.outcome.observations if item.origin == "source_supplied"
    )
    assert len(reported) == 3
    assert {item.currency for item in reported} == {"USD"}
    derived_margin = next(
        item
        for item in result.outcome.observations
        if item.metric_key == "net_margin"
    )
    assert derived_margin.value == pytest.approx(-5 / 120)
    assert derived_margin.derivation_input_ids
    market_cap = next(
        item
        for item in result.outcome.observations
        if item.metric_key == "market_capitalization"
    )
    assert market_cap.value == 1_200_000_000
    assert market_cap.currency == "USD"
    assert market_cap.period_end == date(2026, 1, 2)
    assert result.snapshot is not None
    assert result.snapshot.request.association.association_id == association.association_id


@pytest.mark.parametrize(
    ("profile_state", "profile_domain", "expected_state"),
    [
        ("missing", None, "unresolved"),
        ("available", "successor.example", "mismatch"),
    ],
)
def test_unresolved_or_successor_profile_never_publishes_financial_facts(
    catalog_release: Path,
    tmp_path: Path,
    profile_state: str,
    profile_domain: str | None,
    expected_state: str,
) -> None:
    catalog = _catalog_snapshot(catalog_release, tmp_path)
    _, request = _financial_request(catalog)
    store = CompanyEvidenceFiles(tmp_path / "evidence")

    result = load_company_evidence(
        request,
        catalog=catalog,
        assessments=(financial_assessment(),),
        store=store,
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        financial_loader=lambda _: _financial_bundle(
            profile_state=profile_state,
            profile_domain=profile_domain,
        ),
    )

    assert result.outcome.association_state == expected_state
    assert result.outcome.state == "blocked"
    assert not result.outcome.observations
    assert result.snapshot is None
    assert store.load_latest_snapshot(request.association.association_id, "financial") is None


def test_denied_financial_source_and_nonprimary_listing_make_no_provider_request(
    catalog_release: Path, tmp_path: Path
) -> None:
    catalog = _catalog_snapshot(catalog_release, tmp_path)
    _, request = _financial_request(catalog)
    denied_calls = 0

    def fail_if_called(_):
        nonlocal denied_calls
        denied_calls += 1
        raise AssertionError("Denied sources must not call the provider")

    denied = load_company_evidence(
        request,
        catalog=catalog,
        assessments=(financial_assessment(status="denied"),),
        store=CompanyEvidenceFiles(tmp_path / "denied"),
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        financial_loader=fail_if_called,
    )
    assert denied.outcome.state == "blocked"
    assert denied_calls == 0

    _, secondary_request = _financial_request(catalog, listing_id="listing-a-secondary")
    secondary = load_company_evidence(
        secondary_request,
        catalog=catalog,
        assessments=(financial_assessment(),),
        store=CompanyEvidenceFiles(tmp_path / "secondary"),
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        financial_loader=fail_if_called,
    )
    assert secondary.outcome.state == "blocked"
    assert secondary.outcome.association_state == "mismatch"
    assert denied_calls == 0


def test_company_loader_reuses_stored_research_across_verified_share_classes_only(
    catalog_release: Path, tmp_path: Path
) -> None:
    catalog = _catalog_snapshot(catalog_release, tmp_path)
    original = verified_association(
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        provider_symbol="FIXTURE",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
    )
    claim = research_claim(original)
    archive = snapshot_for(request_for(original), claims=(claim,))
    target = verified_association(
        instrument_id="share-class-b",
        listing_id="listing-b",
        provider_symbol="FIXTURE_B",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
    )
    target_request = request_for(target)
    calls = 0

    def forbidden_financial_loader(_):
        nonlocal calls
        calls += 1
        raise AssertionError("Research attachment must not acquire financial data")

    result = load_company_evidence(
        target_request,
        catalog=catalog,
        assessments=(research_assessment(),),
        store=CompanyEvidenceFiles(tmp_path / "evidence"),
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        financial_loader=forbidden_financial_loader,
        archive_snapshot=archive,
    )

    assert calls == 0
    assert result.outcome.state == "complete"
    assert result.outcome.claims == (claim,)
    assert result.outcome.claims[0].association_id == original.association_id
    assert result.outcome.claims[0].provenance.locator == "Business / Revenue model"


def test_company_loader_blocks_claim_reuse_without_separate_research_binding_or_grant(
    catalog_release: Path, tmp_path: Path
) -> None:
    catalog = _catalog_snapshot(catalog_release, tmp_path)
    association = verified_association(
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        provider_symbol="FIXTURE",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
        research_binding=False,
    )
    with pytest.raises(ValueError, match="separately reviewed issuer binding"):
        request_for(association)

    association = verified_association(
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        provider_symbol="FIXTURE",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
    )
    archive = snapshot_for(
        request_for(association),
        claims=(research_claim(association),),
    )
    denied = load_company_evidence(
        request_for(association),
        catalog=catalog,
        assessments=(research_assessment(status="revoked"),),
        store=CompanyEvidenceFiles(tmp_path / "evidence"),
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        archive_snapshot=archive,
    )
    assert denied.outcome.state == "blocked"
    assert not denied.outcome.claims

    after_cutoff = load_company_evidence(
        request_for(association, as_of=date(2026, 1, 1)),
        catalog=catalog,
        assessments=(research_assessment(),),
        store=CompanyEvidenceFiles(tmp_path / "evidence"),
        clock=lambda: datetime(2026, 1, 2, 13, tzinfo=UTC),
        archive_snapshot=archive,
    )
    assert after_cutoff.outcome.state == "blocked"
    assert not after_cutoff.outcome.claims
