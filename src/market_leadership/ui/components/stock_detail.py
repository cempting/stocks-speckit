"""Detailed chart and peer-score view for one validated stock identity."""

from collections.abc import Callable

import streamlit as st

from market_data.domain.peer_scores import BlockPeerScore, PeerScorecard
from market_data.domain.stock_chart import StockChartEvidence
from market_data.domain.stock_selection import (
    MembershipEntry,
    StockIdentitySelection,
)
from market_leadership.application.load_company_evidence import CompanyEvidenceLoadResult
from market_leadership.ui.sector_chart import build_sector_chart


def _score_label(score: BlockPeerScore | None, state: str) -> str:
    if score is not None and score.value is not None and score.state == "available":
        return f"{score.value:.1f}"
    if state == "error":
        return "Error"
    if state == "not_loaded":
        return "Not loaded"
    return "Insufficient"


def render_stock_detail(
    member: MembershipEntry | StockIdentitySelection,
    chart: StockChartEvidence,
    *,
    scorecard: PeerScorecard | None,
    score_state: str,
    score_reason: str | None,
    dark_mode: bool,
    on_return: Callable[[], None],
    financial_evidence: CompanyEvidenceLoadResult | None = None,
    research_evidence: CompanyEvidenceLoadResult | None = None,
    on_load_financial: Callable[[], None] | None = None,
    on_load_research: Callable[[], None] | None = None,
    comparison_context_label: str | None = None,
    direct_membership_paths: tuple[str, ...] = (),
    widget_key_prefix: str = "market_leadership.stock_detail.",
    back_button_label: str = "Back to Discovery",
) -> None:
    st.title(f"{member.symbol or 'Unlisted'} · {member.name}")
    if isinstance(member, MembershipEntry):
        st.caption(
            f"Instrument {member.instrument_id} · Company "
            f"{member.company_id or 'unassigned'} · "
            f"Peer context {comparison_context_label or member.industry_name}"
        )
        st.caption("Direct reviewed memberships:")
        if direct_membership_paths:
            for path in direct_membership_paths:
                st.caption(path)
        else:
            st.info("No active direct membership path is available for this instrument.")
    else:
        st.caption(
            "Selected by retained stock/listing identity; industry membership is not required."
        )
        st.caption(
            f"Instrument {member.instrument_id} · Company "
            f"{member.company_id or 'unassigned'} · Region {member.region_id} · "
            f"Listing {member.listing_id or 'unavailable'}"
        )
        if member.listing_id is None:
            st.info("No verified listing is active for this instrument on the selected date.")
        elif member.currency:
            st.caption(
                f"Selected listing {member.symbol} · {member.exchange or 'exchange unavailable'} · "
                f"Trading currency {member.currency}"
            )
    st.caption(
        f"Requested through {chart.requested_as_of.isoformat()} · Observed through "
        f"{chart.observed_on.isoformat() if chart.observed_on else 'unavailable'}"
    )

    chart_column, scores_column = st.columns((2, 1))
    with chart_column:
        st.subheader("Price and volume")
        for label, state in (
            ("Price", chart.price_state),
            ("Volume", chart.volume_state),
            ("50 MA", chart.sma50_state),
            ("150-session SMA", chart.sma150_state),
        ):
            if state != "available":
                st.caption(f"{label}: {state.title()}")
        if chart.price_state == "available" or chart.volume_state == "available":
            frame = chart.history.copy()
            if chart.price_state != "available":
                frame["close"] = float("nan")
            if chart.volume_state != "available":
                frame["volume"] = float("nan")
            st.altair_chart(build_sector_chart(frame, dark_mode=dark_mode), width="stretch")
    with scores_column:
        st.subheader("Peer scorecard")
        blocks = (
            ("Quality", scorecard.quality if scorecard else None),
            ("Growth", scorecard.growth if scorecard else None),
            ("Cash Flow", scorecard.cash_flow if scorecard else None),
        )
        for label, score in blocks:
            st.metric(label, _score_label(score, score_state))
        st.caption(score_reason or "Scores follow the existing peer-scoring contract.")

    if on_load_financial is not None or on_load_research is not None:
        st.subheader("Company evidence")
        financial_column, research_column = st.columns(2)
        with financial_column:
            if on_load_financial is not None:
                st.button(
                    "Load financial evidence",
                    key=widget_key_prefix + "load_financial",
                    on_click=on_load_financial,
                )
            if financial_evidence is not None:
                _render_financial_evidence(financial_evidence)
            else:
                st.caption("Financial evidence: not loaded.")
        with research_column:
            if on_load_research is not None:
                st.button(
                    "Load stored business and moat claims",
                    key=widget_key_prefix + "load_research",
                    on_click=on_load_research,
                )
            if research_evidence is not None:
                _render_research_evidence(research_evidence)
            else:
                st.caption("Stored research: not loaded.")

    st.button(
        back_button_label,
        key=widget_key_prefix + "back",
        on_click=on_return,
    )


def _render_financial_evidence(result: CompanyEvidenceLoadResult) -> None:
    outcome = result.outcome
    st.caption(f"Financial evidence: {outcome.state} · issuer {outcome.association_state}")
    st.caption(
        f"Instrument {result.association.instrument_id} · "
        f"listing {result.association.listing_id} · "
        f"company ID {result.association.company_id or 'unassigned'}"
    )
    if outcome.association_reason:
        st.info(outcome.association_reason)
    if outcome.failures:
        for failure in outcome.failures:
            st.warning(failure)
    for item in outcome.observations:
        value = "unavailable" if item.value is None else f"{item.value:g}"
        st.write(
            f"{item.metric_key}: {value} {item.currency or item.unit} · "
            f"{item.period_end.isoformat()} · {item.basis} · {item.origin}"
        )
        st.caption(
            f"{item.definition} · scale {item.source_scale:g} · "
            f"source {item.provenance.source_id} · "
            f"publication {item.provenance.publication_date or 'unknown'} · "
            f"observed {item.provenance.observed_at.isoformat()}"
        )
    for projection in result.projections:
        item = projection.observation
        value = "unavailable" if item.value is None else f"{item.value:g}"
        st.write(
            f"Issuer-shared {item.metric_key}: {value} {item.currency or item.unit} · "
            f"{item.period_end.isoformat()} · {item.basis}"
        )
        st.caption(
            f"Acquired for listing association {projection.acquisition_association_id} · "
            f"source {item.provenance.source_id} · {item.definition} · "
            f"publication {item.provenance.publication_date or 'unknown'} · "
            f"observed {item.provenance.observed_at.isoformat()}"
        )


def _render_research_evidence(result: CompanyEvidenceLoadResult) -> None:
    outcome = result.outcome
    st.caption(f"Stored research: {outcome.state} · issuer {outcome.association_state}")
    if outcome.association_reason:
        st.info(outcome.association_reason)
    for failure in outcome.failures:
        st.warning(failure)
    for claim in outcome.claims:
        st.write(claim.summary or f"{claim.topic}: {claim.value} {claim.unit or ''}")
        st.caption(
            f"{claim.kind} · {claim.qualifications} · source {claim.provenance.source_id} · "
            f"captured {claim.provenance.observed_at.isoformat()} · "
            f"publication {claim.provenance.publication_date or 'unknown'}"
        )
        st.caption(
            f"{claim.provenance.locator or 'Source locator unavailable'} · "
            f"{claim.provenance.source_url or 'Source URL unavailable'}"
        )
