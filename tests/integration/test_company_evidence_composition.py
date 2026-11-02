from dataclasses import replace
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path

import pandas as pd

from market_data.catalog import load_release
from market_data.company_evidence import CompanyEvidenceFiles
from market_data.domain.company_evidence import (
    CompanyEvidenceRequest,
    company_association_fingerprint,
)
from market_leadership.application.load_company_evidence import (
    project_stored_issuer_observations,
)
from market_leadership.bootstrap import load_selected_company_evidence
from market_leadership.ui.cache import clear_company_evidence_caches
from tests.company_evidence_helpers import (
    financial_assessment,
    request_for,
    research_assessment,
    research_claim,
    snapshot_for,
    verified_association,
)
from tests.integration.test_yfinance_fundamentals import FakeTicker
from tests.membership_helpers import build_v2_release, membership_fixture


def _catalog_artifact_hashes(manifest_path: Path) -> dict[str, str]:
    release_root = manifest_path.parent
    return {
        path.relative_to(release_root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(release_root.rglob("*"))
        if path.is_file()
    }


class IssuerTicker(FakeTicker):
    info = {
        "symbol": "FIXTURE",
        "financialCurrency": "USD",
        "currency": "USD",
        "website": "https://issuer.example",
        "uuid": "provider-issuer-uuid",
    }
    quarterly_financials = pd.DataFrame(
        {pd.Timestamp("2025-12-31"): [100, 40, -5, 5, 10, 1]},
        index=[
            "Total Revenue",
            "Gross Profit",
            "Operating Income",
            "EBIT",
            "Net Income",
            "Diluted EPS",
        ],
    )
    quarterly_cashflow = pd.DataFrame(
        {pd.Timestamp("2025-12-31"): [12, -2]},
        index=["Operating Cash Flow", "Capital Expenditure"],
    )
    quarterly_balance_sheet = pd.DataFrame(
        {pd.Timestamp("2025-12-31"): [200, 100]},
        index=["Total Assets", "Current Liabilities"],
    )


def test_production_composition_rechecks_permissions_outside_cached_acquisition(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_company_evidence_caches()
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    catalog = load_release(manifest)
    catalog_hashes = _catalog_artifact_hashes(manifest)
    association = verified_association(
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        provider_symbol="FIXTURE",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
        issuer_domain="issuer.example",
        research_binding=False,
    )
    association = replace(
        association,
        state="unresolved",
        identity_evidence=None,
        reason="Awaiting the selected provider profile",
    )
    assessment = financial_assessment()
    root = tmp_path / "company-evidence"
    monkeypatch.setenv("COMPANY_EVIDENCE_ROOT", str(root))
    store = CompanyEvidenceFiles(root)
    store.save_association(association, expected_revision=None)
    store.save_source_assessment(assessment, expected_revision=None)
    assert store.list_source_assessments() == (assessment,)
    request = CompanyEvidenceRequest(
        association=association,
        scope="financial",
        mode="current",
        as_of=date(2026, 1, 2),
        provider_id="yfinance",
        source_ids=("yfinance",),
        binding_fingerprint=company_association_fingerprint(association, "financial"),
        assessment_fingerprint=assessment.fingerprint,
        history_window=4,
        normalization_revision="normalization-1",
        schema_revision="evidence-1",
        refresh=False,
    )
    calls: list[str] = []

    def factory(symbol: str) -> IssuerTicker:
        calls.append(symbol)
        ticker = IssuerTicker()
        ticker.info = {**ticker.info, "symbol": symbol}
        return ticker

    def clock() -> datetime:
        return datetime(2026, 1, 2, 12, tzinfo=UTC)

    first = load_selected_company_evidence(
        request, catalog, clock=clock, _factory=factory
    )
    reused = load_selected_company_evidence(
        request, catalog, clock=clock, _factory=factory
    )
    assert first.outcome.state == "complete"
    assert reused.outcome.state == "complete"
    assert first.snapshot is not None
    assert calls == ["FIXTURE"]
    assert len(first.outcome.observations) == 10
    assert len(reused.outcome.observations) == 10
    assert store.list_latest_snapshots("research") == ()
    historical = load_selected_company_evidence(
        replace(request, mode="historical"),
        catalog,
        clock=clock,
        _factory=factory,
    )
    assert historical.outcome.state == "complete"
    assert historical.outcome.observations == first.outcome.observations
    assert calls == ["FIXTURE"]

    second_class = verified_association(
        instrument_id="share-class-b",
        listing_id="listing-b",
        provider_symbol="FIXTURE_B",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
        issuer_domain="issuer.example",
        research_binding=False,
    )
    second_class = replace(
        second_class,
        state="unresolved",
        identity_evidence=None,
        reason="Awaiting the selected provider profile",
    )
    store.save_association(second_class, expected_revision=None)
    second_request = CompanyEvidenceRequest(
        association=second_class,
        scope="financial",
        mode="current",
        as_of=date(2026, 1, 2),
        provider_id="yfinance",
        source_ids=("yfinance",),
        binding_fingerprint=company_association_fingerprint(
            second_class, "financial"
        ),
        assessment_fingerprint=assessment.fingerprint,
        history_window=4,
        normalization_revision="normalization-1",
        schema_revision="evidence-1",
        refresh=False,
    )
    second_result = load_selected_company_evidence(
        second_request, catalog, clock=clock, _factory=factory
    )
    assert second_result.outcome.state == "complete"
    assert second_result.snapshot is not None
    assert len(second_result.outcome.observations) == 10
    assert calls == ["FIXTURE", "FIXTURE_B"]
    assert second_result.projections
    assert all(
        projection.acquisition_association_id == association.association_id
        and projection.consumer_association_id == second_class.association_id
        for projection in second_result.projections
    )
    projections = project_stored_issuer_observations(
        replace(second_request, association=second_result.association),
        (first.snapshot,),
        (assessment,),
        permission_as_of=date(2026, 1, 2),
    )
    assert projections
    assert all(
        projection.acquisition_association_id == association.association_id
        and projection.consumer_association_id == second_class.association_id
        and projection.observation.association_id == association.association_id
        and projection.observation.currency == "USD"
        for projection in projections
    )

    revoked = replace(
        assessment,
        status="revoked",
        allowed_uses=(),
        reviewed_at=None,
        review_reference=None,
        fingerprint="c" * 64,
    )
    store.save_source_assessment(
        revoked, expected_revision=assessment.fingerprint
    )
    assert store.list_source_assessments() == (revoked,)
    blocked = load_selected_company_evidence(
        request, catalog, clock=clock, _factory=factory
    )
    assert blocked.outcome.state == "blocked"
    assert not blocked.outcome.observations
    assert calls == ["FIXTURE", "FIXTURE_B"]
    assert _catalog_artifact_hashes(manifest) == catalog_hashes
    clear_company_evidence_caches()


def test_production_composition_finds_stored_research_from_verified_sibling_class(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    catalog = load_release(manifest)
    original = verified_association(
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        provider_symbol="FIXTURE",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
    )
    consumer = verified_association(
        instrument_id="share-class-b",
        listing_id="listing-b",
        provider_symbol="FIXTURE_B",
        exchange="FIXTUREEX",
        catalog_revision=catalog.catalog_revision,
    )
    assessment = research_assessment()
    root = tmp_path / "company-evidence"
    monkeypatch.setenv("COMPANY_EVIDENCE_ROOT", str(root))
    store = CompanyEvidenceFiles(root)
    store.save_association(original, expected_revision=None)
    store.save_association(consumer, expected_revision=None)
    store.save_source_assessment(assessment, expected_revision=None)
    archived = snapshot_for(
        request_for(original),
        claims=(research_claim(original),),
    )
    store.publish_snapshot(archived, expected_revision=None)
    assert store.list_latest_snapshots("research") == (archived,)

    def clock() -> datetime:
        return datetime(2026, 1, 2, 13, tzinfo=UTC)

    result = load_selected_company_evidence(
        request_for(consumer),
        catalog,
        clock=clock,
    )

    assert result.outcome.state == "complete"
    assert len(result.outcome.claims) == 1
    assert result.outcome.claims[0].association_id == original.association_id
    assert result.outcome.claims[0].provenance.source_id == assessment.source_id

    revoked = replace(
        assessment,
        status="revoked",
        allowed_uses=(),
        reviewed_at=None,
        review_reference=None,
        fingerprint="d" * 64,
    )
    store.save_source_assessment(revoked, expected_revision=assessment.fingerprint)
    blocked = load_selected_company_evidence(
        request_for(consumer),
        catalog,
        clock=clock,
    )
    assert blocked.outcome.state == "blocked"
    assert not blocked.outcome.claims
