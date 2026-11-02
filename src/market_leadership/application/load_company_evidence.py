"""Identity-gated loading and reattachment of retained company evidence."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from math import isfinite
from typing import Literal

from market_data.catalog import CatalogSnapshot
from market_data.company_evidence import (
    CompanyEvidenceFiles,
)
from market_data.domain.catalog import Listing
from market_data.domain.company_evidence import (
    CompanyAssociation,
    CompanyEvidenceOutcome,
    CompanyEvidenceRequest,
    CompanyEvidenceSnapshot,
    CompanyResearchClaim,
    EvidenceProvenance,
    FinancialObservation,
    IssuerFinancialProjection,
    SourceAssessment,
    create_company_evidence_snapshot,
    eligible_research_claims,
    project_issuer_financial_evidence,
    verify_company_association,
)
from market_data.domain.fundamentals import (
    FinancialQuarter,
    FundamentalBundle,
    FundamentalRequest,
)
from market_leadership.infrastructure.yfinance_fundamentals import FundamentalAcquisitionError

FinancialLoader = Callable[[FundamentalRequest], FundamentalBundle]
Clock = Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class CompanyEvidenceLoadResult:
    association: CompanyAssociation
    outcome: CompanyEvidenceOutcome
    snapshot: CompanyEvidenceSnapshot | None
    projections: tuple[IssuerFinancialProjection, ...] = ()


def project_stored_issuer_observations(
    request: CompanyEvidenceRequest,
    snapshots: tuple[CompanyEvidenceSnapshot, ...],
    assessments: tuple[SourceAssessment, ...],
    *,
    permission_as_of: date,
) -> tuple[IssuerFinancialProjection, ...]:
    if request.scope != "financial":
        return ()
    return tuple(
        projection
        for snapshot in snapshots
        for projection in project_issuer_financial_evidence(
            snapshot,
            request.association,
            assessments,
            as_of=request.as_of,
            permission_as_of=permission_as_of,
        )
    )


def load_company_evidence(
    request: CompanyEvidenceRequest,
    *,
    catalog: CatalogSnapshot,
    assessments: tuple[SourceAssessment, ...],
    store: CompanyEvidenceFiles,
    clock: Clock,
    financial_loader: FinancialLoader | None = None,
    archive_snapshot: CompanyEvidenceSnapshot | None = None,
    archive_snapshots: tuple[CompanyEvidenceSnapshot, ...] = (),
    financial_snapshots: tuple[CompanyEvidenceSnapshot, ...] | None = None,
    retry_limit: int = 2,
) -> CompanyEvidenceLoadResult:
    started_at = _now_utc(clock())
    listing, listing_failure, listing_state = _eligible_listing(
        request.association, catalog, request.as_of
    )
    if listing is None:
        return _blocked(
            request.association,
            started_at,
            listing_failure,
            association_state=listing_state,
        )
    if request.scope == "research":
        return _load_research(
            request,
            assessments=assessments,
            store=store,
            clock=clock,
            archived_snapshots=(
                archive_snapshots
                if archive_snapshots
                else (archive_snapshot,) if archive_snapshot is not None else ()
            ),
            started_at=started_at,
        )
    if request.mode == "historical":
        result = _load_financial_archive(
            request,
            assessments=assessments,
            store=store,
            clock=clock,
            snapshot=archive_snapshot,
            started_at=started_at,
        )
        return _attach_issuer_projections(
            result,
            request,
            assessments=assessments,
            store=store,
            clock=clock,
            financial_snapshots=financial_snapshots,
        )
    if request.as_of != started_at.date():
        return _blocked(
            request.association,
            started_at,
            "Current financial requests must use today's date",
        )
    assessment = _assessment_for(
        request, assessments, role="financial", permission_date=started_at.date()
    )
    if assessment is None:
        return _blocked(
            request.association,
            started_at,
            "Financial collection, display and normalized retention are not approved",
            started_at=started_at,
        )
    if financial_loader is None:
        raise ValueError("Current financial requests require a financial loader")

    acquisition_error: FundamentalAcquisitionError | None = None
    try:
        bundle = financial_loader(
            FundamentalRequest(
                symbol=request.association.provider_symbol,
                provider_id=request.provider_id,
                history_window=request.history_window,
                frequency="quarterly",
                schema_version=1,
                retry_limit=retry_limit,
            )
        )
    except FundamentalAcquisitionError as error:
        acquisition_error = error
        bundle = error.partial
    completed_at = _now_utc(clock())
    verified = _verify_profile(request.association, bundle)
    if verified.state != "verified":
        reason = verified.reason or "Issuer profile did not corroborate the reviewed binding"
        return _blocked(
            verified,
            completed_at,
            reason,
            association_state=verified.state,
            started_at=started_at,
        )
    if bundle.provider_id != request.provider_id or bundle.symbol != listing.provider_symbol:
        failed = _with_association_failure(
            verified, "Acquired financial profile does not match the selected listing"
        )
        return _blocked(
            failed,
            completed_at,
            failed.reason or "Acquired profile does not match selected listing",
            association_state="mismatch",
            started_at=started_at,
        )
    observations = _financial_observations(
        verified,
        bundle,
        assessment=assessment,
        schema_revision=request.schema_revision,
    )
    failures = tuple(
        dict.fromkeys(
            (
                *bundle.warnings,
                *(acquisition_error.component_errors if acquisition_error else ()),
            )
        )
    )
    if not observations:
        return _blocked(
            verified,
            completed_at,
            "No financial observations were available after issuer verification",
            started_at=started_at,
            failures=failures,
        )
    outcome = CompanyEvidenceOutcome(
        state="partial" if failures else "complete",
        observations=observations,
        claims=(),
        failures=failures,
        started_at=started_at,
        captured_at=_now_utc(bundle.fetched_at),
        completed_at=completed_at,
        association_state="verified",
        verified_association=verified,
    )
    stored_snapshot = create_company_evidence_snapshot(
        request=request,
        outcome=outcome,
        policy_references=(assessment.fingerprint, verified.binding_reference or ""),
    )
    current = store.load_latest_snapshot(verified.association_id, "financial")
    store.publish_snapshot(
        stored_snapshot,
        expected_revision=current.content_sha256 if current else None,
    )
    result = CompanyEvidenceLoadResult(verified, outcome, stored_snapshot)
    return _attach_issuer_projections(
        result,
        request,
        assessments=assessments,
        store=store,
        clock=clock,
        financial_snapshots=financial_snapshots,
    )


def _attach_issuer_projections(
    result: CompanyEvidenceLoadResult,
    request: CompanyEvidenceRequest,
    *,
    assessments: tuple[SourceAssessment, ...],
    store: CompanyEvidenceFiles,
    clock: Clock,
    financial_snapshots: tuple[CompanyEvidenceSnapshot, ...] | None,
) -> CompanyEvidenceLoadResult:
    consumer = result.outcome.verified_association
    if (
        request.scope != "financial"
        or result.outcome.state not in ("complete", "partial")
        or consumer is None
        or consumer.state != "verified"
    ):
        return result
    projection_request = replace(request, association=consumer)
    projections = project_stored_issuer_observations(
        projection_request,
        financial_snapshots
        if financial_snapshots is not None
        else store.list_latest_snapshots("financial"),
        assessments,
        permission_as_of=_now_utc(clock()).date(),
    )
    return replace(result, projections=projections)


def _load_research(
    request: CompanyEvidenceRequest,
    *,
    assessments: tuple[SourceAssessment, ...],
    store: CompanyEvidenceFiles,
    clock: Clock,
    archived_snapshots: tuple[CompanyEvidenceSnapshot, ...],
    started_at: datetime,
) -> CompanyEvidenceLoadResult:
    now = _now_utc(clock())
    if request.association.state != "verified":
        return _blocked(
            request.association,
            now,
            "Research requires a separately verified issuer binding",
            association_state=request.association.state,
            started_at=started_at,
        )
    eligible_assessments = tuple(
        assessment
        for assessment in assessments
        if assessment.role == "disclosure"
        and assessment.source_id in request.source_ids
        and assessment.fingerprint == request.assessment_fingerprint
        and assessment.permits("display", now.date(), role="disclosure")
        and assessment.permits("normalized_retention", now.date(), role="disclosure")
    )
    if not eligible_assessments:
        return _blocked(
            request.association,
            now,
            "Research display and normalized retention are not approved",
            started_at=started_at,
        )
    snapshots = archived_snapshots or tuple(
        snapshot
        for snapshot in (
            store.load_latest_snapshot(request.association.association_id, "research"),
        )
        if snapshot is not None
    )
    if not snapshots:
        return _blocked(
            request.association, now, "No retained research snapshot is available",
            started_at=started_at,
        )
    claims_by_id: dict[str, CompanyResearchClaim] = {}
    source_snapshot: CompanyEvidenceSnapshot | None = None
    for snapshot in snapshots:
        eligible_claims = eligible_research_claims(
            snapshot,
            request,
            eligible_assessments,
            permission_as_of=now.date(),
        )
        if eligible_claims and source_snapshot is None:
            source_snapshot = snapshot
        for claim in eligible_claims:
            existing = claims_by_id.get(claim.claim_id)
            if existing is not None and existing != claim:
                raise ValueError("Stored research contains conflicting copies of a claim")
            claims_by_id[claim.claim_id] = claim
    claims = tuple(claims_by_id.values())
    if not claims:
        return _blocked(
            request.association,
            now,
            "No retained research claims are currently permitted for this date and issuer",
            started_at=started_at,
        )
    outcome = CompanyEvidenceOutcome(
        state="complete",
        observations=(),
        claims=claims,
        failures=(),
        started_at=started_at,
        captured_at=max(
            claim.provenance.observed_at for claim in claims
        ),
        completed_at=now,
        association_state="verified",
    )
    return CompanyEvidenceLoadResult(request.association, outcome, source_snapshot)


def _load_financial_archive(
    request: CompanyEvidenceRequest,
    *,
    assessments: tuple[SourceAssessment, ...],
    store: CompanyEvidenceFiles,
    clock: Clock,
    snapshot: CompanyEvidenceSnapshot | None,
    started_at: datetime,
) -> CompanyEvidenceLoadResult:
    now = _now_utc(clock())
    if snapshot is None:
        snapshot = store.load_latest_snapshot(request.association.association_id, "financial")
    if snapshot is None or snapshot.request.scope != "financial":
        return _blocked(
            request.association, now, "No retained financial snapshot is available",
            started_at=started_at,
        )
    if (
        snapshot.request.association.association_id != request.association.association_id
        or snapshot.outcome.association_state != "verified"
        or snapshot.outcome.verified_association is None
        or snapshot.outcome.verified_association.state != "verified"
        or snapshot.request.binding_fingerprint != request.binding_fingerprint
        or snapshot.outcome.verified_association.catalog_revision
        != request.association.catalog_revision
    ):
        return _blocked(
            request.association, now, "Archived financial identity does not match the request",
            association_state="mismatch", started_at=started_at,
        )
    cutoff = datetime.combine(request.as_of, time.max, tzinfo=UTC)
    if snapshot.outcome.captured_at > cutoff:
        return _blocked(
            request.association, now, "Archived financial capture is after the requested date",
            started_at=started_at,
        )
    eligible = tuple(
        observation
        for observation in snapshot.outcome.observations
        if observation.period_end <= request.as_of
        and any(
            assessment.source_id == observation.provenance.source_id
            and assessment.role == "financial"
            and assessment.fingerprint == observation.provenance.assessment_fingerprint
            and assessment.permits("display", now.date(), role="financial")
            and assessment.permits("normalized_retention", now.date(), role="financial")
            for assessment in assessments
        )
    )
    if not eligible:
        return _blocked(
            request.association, now, "No archived observations are currently permitted",
            started_at=started_at,
        )
    outcome = CompanyEvidenceOutcome(
        state="partial" if snapshot.outcome.failures else "complete",
        observations=eligible,
        claims=(),
        failures=snapshot.outcome.failures,
        started_at=started_at,
        captured_at=snapshot.outcome.captured_at,
        completed_at=now,
        association_state="verified",
        verified_association=snapshot.outcome.verified_association,
    )
    return CompanyEvidenceLoadResult(
        snapshot.outcome.verified_association, outcome, snapshot
    )


def _eligible_listing(
    association: CompanyAssociation,
    catalog: CatalogSnapshot,
    as_of: date,
) -> tuple[Listing | None, str, Literal["unresolved", "expired", "mismatch"]]:
    if association.state in ("mismatch", "expired"):
        return (
            None,
            association.reason or "Issuer association is not eligible",
            association.state,
        )
    if association.catalog_revision != catalog.catalog_revision:
        return None, "Catalog revision changed; reselect the reviewed listing", "unresolved"
    if not association.active_on(as_of):
        return None, "Issuer binding is outside its effective dates", "expired"
    result = catalog.listing_for_instrument(
        association.region_id,
        association.instrument_id,
        as_of,
        listing_id=association.listing_id,
    )
    listing = result.listing
    if result.state != "available" or listing is None:
        state: Literal["unresolved", "expired", "mismatch"] = (
            "expired" if result.reason == "listing_inactive" else "unresolved"
        )
        return None, "Selected listing is not eligible on the requested date", state
    if (
        listing.instrument_type != "stock"
        or listing.is_primary is not True
        or listing.provider_symbol != association.provider_symbol
        or listing.exchange != association.exchange
        or listing.currency != association.trading_currency
    ):
        return None, "Selected listing does not match its reviewed binding", "mismatch"
    return listing, "", "unresolved"


def _assessment_for(
    request: CompanyEvidenceRequest,
    assessments: tuple[SourceAssessment, ...],
    *,
    role: Literal["financial", "disclosure", "reference"],
    permission_date: date,
) -> SourceAssessment | None:
    return next(
        (
            assessment
            for assessment in assessments
            if assessment.source_id in request.source_ids
            and assessment.role == role
            and assessment.fingerprint == request.assessment_fingerprint
            and assessment.permits("collection", permission_date, role=role)
            and assessment.permits("display", permission_date, role=role)
            and assessment.permits("normalized_retention", permission_date, role=role)
        ),
        None,
    )


def _verify_profile(
    association: CompanyAssociation, bundle: FundamentalBundle
) -> CompanyAssociation:
    evidence_reference = (
        f"yfinance-profile:{bundle.fingerprint}"
        if bundle.profile_state == "available"
        and (
            bundle.issuer_discriminator is not None
            or bundle.profile_cik is not None
            or bundle.profile_domain is not None
        )
        else None
    )
    return verify_company_association(
        association,
        as_of=bundle.fetched_at.date(),
        profile_issuer_key=bundle.issuer_discriminator,
        profile_cik=bundle.profile_cik,
        profile_domain=bundle.profile_domain,
        profile_evidence_reference=evidence_reference,
    )


def _financial_observations(
    association: CompanyAssociation,
    bundle: FundamentalBundle,
    *,
    assessment: SourceAssessment,
    schema_revision: str,
) -> tuple[FinancialObservation, ...]:
    output: list[FinancialObservation] = []
    for table_name, quarters in (
        ("income", bundle.income),
        ("cash", bundle.cash),
        ("balance", bundle.balance),
    ):
        for quarter in quarters:
            output.extend(
                _quarter_observations(
                    table_name,
                    quarter,
                    association,
                    bundle,
                    assessment,
                    schema_revision,
                )
            )
    return tuple(output)


def _quarter_observations(
    table_name: str,
    quarter: FinancialQuarter,
    association: CompanyAssociation,
    bundle: FundamentalBundle,
    assessment: SourceAssessment,
    schema_revision: str,
) -> tuple[FinancialObservation, ...]:
    observations: list[FinancialObservation] = []
    for metric_key, value in quarter.values:
        if value is None or not isfinite(value):
            continue
        observations.append(
            FinancialObservation(
                observation_id=(
                    f"{association.association_id}:{table_name}:{metric_key}:"
                    f"{quarter.period.isoformat()}"
                ),
                association_id=association.association_id,
                metric_key=metric_key,
                value=value,
                unit="currency" if metric_key != "diluted_eps" else "currency_per_share",
                currency=bundle.currency or None,
                source_scale=1.0,
                period_start=None,
                period_end=quarter.period,
                basis="quarterly",
                origin="source_supplied",
                definition=f"Source-provided {table_name} value for {metric_key}",
                derivation_input_ids=(),
                provenance=EvidenceProvenance(
                    source_id=assessment.source_id,
                    provider_id=bundle.provider_id,
                    assessment_fingerprint=assessment.fingerprint,
                    source_url=None,
                    locator=f"{table_name}/{metric_key}",
                    publication_date=None,
                    publication_precision="unknown",
                    observed_at=_now_utc(bundle.fetched_at),
                    period_start=None,
                    period_end=quarter.period,
                    payload_sha256=bundle.fingerprint,
                    schema_revision=schema_revision,
                    limitations=("Provider does not expose a verified publication vintage",),
                ),
                state="available",
                reason=None,
            )
        )
    return tuple(observations)


def _blocked(
    association: CompanyAssociation,
    now: datetime,
    reason: str,
    *,
    association_state: Literal["verified", "unresolved", "mismatch", "expired"] | None = None,
    started_at: datetime | None = None,
    failures: tuple[str, ...] = (),
) -> CompanyEvidenceLoadResult:
    current = _now_utc(now)
    effective_state = association_state or association.state
    outcome = CompanyEvidenceOutcome(
        state="blocked",
        observations=(),
        claims=(),
        failures=tuple(dict.fromkeys((*failures, reason))),
        started_at=started_at or current,
        captured_at=current,
        completed_at=current,
        association_state=effective_state,
        association_reason=reason,
    )
    result_association = (
        _with_association_failure(association, reason, state=effective_state)
        if effective_state != "verified"
        else association
    )
    return CompanyEvidenceLoadResult(result_association, outcome, None)


def _with_association_failure(
    association: CompanyAssociation,
    reason: str,
    *,
    state: Literal["unresolved", "mismatch", "expired"] = "unresolved",
) -> CompanyAssociation:
    return replace(association, state=state, reason=reason)


def _now_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("Company evidence clock must return timezone-aware UTC")
    return value
