"""User-controlled issuer evidence controls shared by stock detail workflows."""

from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

import streamlit as st

from market_data.catalog import CatalogSnapshot
from market_data.company_evidence import CompanyEvidenceFiles
from market_data.domain.company_evidence import (
    CompanyEvidenceRequest,
    company_association_fingerprint,
)
from market_leadership.application.load_company_evidence import CompanyEvidenceLoadResult
from market_leadership.config import Settings


def render_company_evidence_controls(
    snapshot: CatalogSnapshot,
    settings: Settings,
    *,
    instrument_id: str,
    listing_id: str,
    region_id: str,
    as_of: date,
    state_prefix: str,
) -> tuple[
    CompanyEvidenceLoadResult | None,
    CompanyEvidenceLoadResult | None,
    Callable[[], None] | None,
    Callable[[], None] | None,
]:
    from market_leadership.bootstrap import load_selected_company_evidence

    store = CompanyEvidenceFiles(Path(settings.company_evidence_root))
    try:
        association = store.find_active_association(
            instrument_id=instrument_id,
            listing_id=listing_id,
            provider_id="yfinance",
            as_of=as_of,
        )
        assessments = store.list_source_assessments()
    except (OSError, RuntimeError, ValueError) as error:
        st.error(f"Company evidence controls could not be loaded: {error}")
        return None, None, None, None
    if association is None or association.region_id != region_id:
        st.info("Company evidence is unavailable until a dated issuer binding is reviewed.")
        return None, None, None, None

    financial_assessment = next(
        (
            item
            for item in assessments
            if item.source_id == association.provider_id and item.role == "financial"
        ),
        None,
    )
    disclosure_assessments = tuple(
        item for item in assessments if item.role == "disclosure"
    )
    research_source_id = (
        st.selectbox(
            "Reviewed research source",
            options=tuple(item.source_id for item in disclosure_assessments),
            index=None,
            key=state_prefix + "research_source_" + association.association_id,
        )
        if disclosure_assessments
        else None
    )
    research_assessment = next(
        (
            item
            for item in disclosure_assessments
            if item.source_id == research_source_id
        ),
        None,
    )

    financial_result: CompanyEvidenceLoadResult | None = None
    research_result: CompanyEvidenceLoadResult | None = None
    on_load_financial: Callable[[], None] | None = None
    on_load_research: Callable[[], None] | None = None

    financial_context_key = state_prefix + "evidence_financial_context"
    financial_generation_key = state_prefix + "evidence_financial_generation"
    financial_processed_key = state_prefix + "evidence_financial_processed"
    research_context_key = state_prefix + "evidence_research_context"
    research_generation_key = state_prefix + "evidence_research_generation"

    if financial_assessment is None:
        st.info("No financial source assessment is registered for this provider.")
    else:
        financial_context = (
            association.association_id,
            company_association_fingerprint(association, "financial"),
            financial_assessment.fingerprint,
            as_of,
        )
        if st.session_state.get(financial_context_key) != financial_context:
            st.session_state[financial_context_key] = financial_context
            st.session_state[financial_generation_key] = 0
            st.session_state[financial_processed_key] = 0

        def request_financial() -> None:
            st.session_state[financial_generation_key] += 1

        on_load_financial = request_financial
        generation = st.session_state[financial_generation_key]
        processed = st.session_state[financial_processed_key]
        if generation:
            mode = (
                "current"
                if generation > processed and as_of == datetime.now(UTC).date()
                else "historical"
            )
            request = CompanyEvidenceRequest(
                association=association,
                scope="financial",
                mode=mode,
                as_of=as_of,
                provider_id=association.provider_id,
                source_ids=(financial_assessment.source_id,),
                binding_fingerprint=company_association_fingerprint(
                    association, "financial"
                ),
                assessment_fingerprint=financial_assessment.fingerprint,
                history_window=4,
                normalization_revision="company-evidence-1",
                schema_revision="company-evidence-1",
                refresh=False,
            )
            try:
                financial_result = load_selected_company_evidence(request, snapshot)
            except (OSError, RuntimeError, ValueError) as error:
                st.error(f"Financial evidence could not be loaded: {error}")
            finally:
                st.session_state[financial_processed_key] = generation

    if not disclosure_assessments:
        st.info("No independently reviewed research sources are registered.")
    elif research_assessment is None:
        st.info("Choose a reviewed disclosure source to load stored research.")
    else:
        research_context = (
            association.association_id,
            company_association_fingerprint(association, "research"),
            research_assessment.fingerprint,
            as_of,
        )
        if st.session_state.get(research_context_key) != research_context:
            st.session_state[research_context_key] = research_context
            st.session_state[research_generation_key] = 0

        def request_research() -> None:
            st.session_state[research_generation_key] += 1

        on_load_research = request_research
        generation = st.session_state[research_generation_key]
        if generation:
            try:
                financial_snapshot = store.load_latest_snapshot(
                    association.association_id, "financial"
                )
                verified_association = (
                    financial_snapshot.outcome.verified_association
                    if financial_snapshot is not None
                    else None
                )
                if verified_association is None or verified_association.state != "verified":
                    st.warning(
                        "Research requires a stored, independently verified financial issuer "
                        "identity before claims can be attached."
                    )
                elif (
                    verified_association.research_binding_reference is None
                    or verified_association.research_identity_evidence is None
                ):
                    st.warning("No independently reviewed research issuer binding is available.")
                else:
                    request = CompanyEvidenceRequest(
                        association=verified_association,
                        scope="research",
                        mode="historical",
                        as_of=as_of,
                        provider_id=verified_association.provider_id,
                        source_ids=(research_assessment.source_id,),
                        binding_fingerprint=company_association_fingerprint(
                            verified_association, "research"
                        ),
                        assessment_fingerprint=research_assessment.fingerprint,
                        history_window=4,
                        normalization_revision="company-evidence-1",
                        schema_revision="company-evidence-1",
                        refresh=False,
                    )
                    research_result = load_selected_company_evidence(request, snapshot)
            except (OSError, RuntimeError, ValueError) as error:
                st.error(f"Stored research could not be loaded: {error}")

    return (
        financial_result,
        research_result,
        on_load_financial,
        on_load_research,
    )
