"""Detailed chart and peer-score view for one validated stock identity."""

from collections.abc import Callable

import pandas as pd
import streamlit as st

from market_data.domain.company_evidence import FinancialObservation
from market_data.domain.consolidation import ConsolidationInterval, ConsolidationResult
from market_data.domain.peer_scores import BlockPeerScore, PeerScorecard
from market_data.domain.stock_chart import (
    STOCK_CHART_PERIODS,
    StockChartEvidence,
    build_stock_chart_evidence,
)
from market_data.domain.stock_selection import (
    MembershipEntry,
    StockIdentitySelection,
)
from market_leadership.application.load_company_evidence import CompanyEvidenceLoadResult
from market_leadership.ui.sector_chart import build_sector_chart

_FINANCIAL_LABELS = {
    "revenue": "Revenue",
    "gross_profit": "Gross profit",
    "operating_income": "Operating income",
    "ebit": "EBIT",
    "net_income": "Net income",
    "diluted_eps": "Diluted EPS",
    "ocf": "Operating cash flow",
    "capex": "Capital expenditure",
    "fcf": "Free cash flow",
    "assets": "Total assets",
    "current_assets": "Current assets",
    "current_liabilities": "Current liabilities",
    "cash_and_equivalents": "Cash and equivalents",
    "total_debt": "Total debt",
    "shareholders_equity": "Shareholders' equity",
    "shares_outstanding": "Shares outstanding",
    "sales_yoy": "Revenue YoY",
    "eps_yoy": "Diluted EPS YoY",
    "gross_margin": "Gross margin",
    "operating_margin": "Operating margin",
    "net_margin": "Net margin",
    "fcf_margin": "FCF margin",
    "roce": "ROCE",
    "current_ratio": "Current ratio",
    "debt_to_equity": "Debt-to-equity",
}
_PERCENT_METRICS = {
    "sales_yoy",
    "eps_yoy",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "fcf_margin",
    "roce",
}


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
    listing_identity = (
        (member.listing_id, member.symbol, member.exchange)
        if isinstance(member, StockIdentitySelection)
        else (member.symbol, member.exchange)
    )
    chart_range_key = widget_key_prefix + "chart_range"
    chart_range_context_key = widget_key_prefix + "chart_range_context"
    chart_context = (member.instrument_id, listing_identity)
    if st.session_state.get(chart_range_context_key) != chart_context:
        st.session_state.pop(chart_range_key, None)
        st.session_state[chart_range_context_key] = chart_context
    if st.session_state.get(chart_range_key) not in STOCK_CHART_PERIODS:
        st.session_state.pop(chart_range_key, None)
    chart_range = st.selectbox(
        "Chart period",
        options=STOCK_CHART_PERIODS,
        index=2,
        key=chart_range_key,
    )
    selected_chart = build_stock_chart_evidence(
        chart.instrument_id,
        chart.history,
        as_of=chart.requested_as_of,
        visible_range=chart_range,
        consolidation_result=chart.consolidation,
    )
    visible_start = (
        selected_chart.history.index[0].date()
        if not selected_chart.history.empty
        else "no observations"
    )
    st.caption(
        f"Chart period {chart_range} · from {visible_start} · requested through "
        f"{selected_chart.requested_as_of.isoformat()} · observed through "
        f"{selected_chart.observed_on.isoformat() if selected_chart.observed_on else 'unavailable'}"
    )

    chart_column, scores_column = st.columns((2, 1))
    with chart_column:
        selected_interval = _render_consolidation_evidence(
            selected_chart.consolidation,
            selected_chart.history,
            chart_context=chart_context,
            widget_key_prefix=widget_key_prefix,
        )
        st.subheader("Price and volume")
        for label, state in (
            ("Price", selected_chart.price_state),
            ("Volume", selected_chart.volume_state),
            ("50 MA", selected_chart.sma50_state),
            ("150-session SMA", selected_chart.sma150_state),
        ):
            if state != "available":
                st.caption(f"{label}: {state.title()}")
        if (
            selected_chart.price_state != "unavailable"
            or selected_chart.volume_state != "unavailable"
        ):
            frame = selected_chart.history.copy()
            if frame["close"].notna().sum() == 0:
                frame["close"] = float("nan")
            if frame["volume"].notna().sum() == 0:
                frame["volume"] = float("nan")
            st.altair_chart(
                build_sector_chart(
                    frame,
                    dark_mode=dark_mode,
                    max_rows=None,
                    consolidation_interval=selected_interval,
                ),
                width="stretch",
            )
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


def _render_consolidation_evidence(
    result: ConsolidationResult,
    visible_history: pd.DataFrame,
    *,
    chart_context: tuple[object, ...],
    widget_key_prefix: str,
) -> ConsolidationInterval | None:
    st.subheader("Consolidation detection")
    selection_key = widget_key_prefix + "consolidation_interval"
    context_key = widget_key_prefix + "consolidation_context"
    context = (*chart_context, result.as_of, tuple(item.interval_id for item in result.intervals))
    if st.session_state.get(context_key) != context:
        st.session_state.pop(selection_key, None)
        st.session_state[context_key] = context

    if result.state == "insufficient":
        reasons = ", ".join(result.reason_codes) or "unspecified evidence gap"
        st.warning(
            f"Consolidation evidence is insufficient as of {result.as_of.isoformat()}: "
            f"{reasons}."
        )
    elif not result.intervals:
        st.info("No qualifying consolidation interval was found in the available history.")

    if not result.intervals:
        return None

    intervals = tuple(reversed(result.intervals))
    selected_index = st.selectbox(
        "Inspect interval",
        options=tuple(range(len(intervals))),
        format_func=lambda index: (
            f"{'Latest' if index == 0 else f'Older {index}'} · "
            f"{intervals[index].start_session.isoformat()} – "
            f"{intervals[index].end_session.isoformat()}"
        ),
        key=selection_key,
    )
    interval = intervals[selected_index]
    st.caption(
        f"{interval.duration_sessions} sessions "
        f"(about {interval.approx_calendar_duration} calendar days) · "
        f"{interval.start_session.isoformat()} to {interval.end_session.isoformat()} · "
        f"detected as of {interval.as_of.isoformat()}"
    )
    st.caption(
        f"Observed corridor {interval.lower:,.2f}–{interval.upper:,.2f} · "
        f"width {interval.width_pct:.1f}% · median ATR(14) {interval.median_atr14:,.2f}"
    )
    st.caption(
        f"Volume context: {interval.volume_context.spike_sessions} spike sessions out of "
        f"{interval.volume_context.lookback_sessions} · spike threshold "
        f"{interval.volume_context.spike_multiplier:g}× prior median"
    )
    if interval.start_boundary_truncated:
        st.warning("The interval begins at the available-history boundary and may be truncated.")
    if "history_truncated" in result.reason_codes:
        st.caption("Available detector history is bounded; older intervals may be omitted.")

    if not visible_history.empty:
        visible_start = pd.DatetimeIndex(visible_history.index).date.min()
        visible_end = pd.DatetimeIndex(visible_history.index).date.max()
        if interval.end_session < visible_start or interval.start_session > visible_end:
            st.info(
                "This interval is outside the visible chart period; the chart period stays fixed."
            )
            return None
        return interval
    st.info("No chart observations are available to annotate this interval.")
    return None


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
    observations = outcome.observations
    st.markdown("**Company size**")
    market_caps = [
        item
        for item in observations
        if item.metric_key == "market_capitalization" and item.state == "available"
    ]
    if market_caps:
        market_cap = max(market_caps, key=lambda item: item.period_end)
        amount = (
            "unavailable"
            if market_cap.value is None
            else f"{market_cap.value:,.0f} {market_cap.currency or market_cap.unit}"
        )
        st.write(
            f"Market capitalization: {amount} · As of {market_cap.period_end.isoformat()}"
        )
        _render_observation_context(market_cap)
    else:
        st.caption("Market capitalization: Not reported")

    quarterly = tuple(item for item in observations if item.basis == "quarterly")
    periods = tuple(sorted({item.period_end for item in quarterly}, reverse=True)[:8])
    st.markdown("**Quarterly fundamentals — latest eight periods**")
    visible_keys = {
        item.metric_key
        for item in quarterly
        if item.metric_key in _FINANCIAL_LABELS
    }
    key_order = tuple(key for key in _FINANCIAL_LABELS if key in visible_keys)
    for period in periods:
        st.markdown(f"**Quarter ended {period.isoformat()}**")
        facts = {item.metric_key: item for item in quarterly if item.period_end == period}
        for key in key_order:
            item = facts.get(key)
            label = _FINANCIAL_LABELS[key]
            if item is None:
                st.write(f"{label}: Not reported")
                continue
            status = item.origin.replace("_", " ").title()
            value = _format_financial_value(item.metric_key, item.value, item.currency, item.unit)
            if item.value is None:
                status = (
                    "Insufficient evidence"
                    if item.state == "insufficient"
                    else item.state.replace("_", " ").title()
                )
            st.write(
                f"{label}: {value} · {item.currency or item.unit} · {status}"
            )
            _render_observation_context(item)
    for projection in result.projections:
        item = projection.observation
        value = _format_financial_value(item.metric_key, item.value, item.currency, item.unit)
        st.write(
            f"Issuer-shared {item.metric_key}: {value} {item.currency or item.unit} · "
            f"{item.period_end.isoformat()} · {item.basis}"
        )
        _render_observation_context(
            item,
            prefix=f"Acquired for listing association {projection.acquisition_association_id} · ",
        )


def _format_financial_value(
    metric_key: str,
    value: float | None,
    currency: str | None,
    unit: str,
) -> str:
    if value is None:
        return "Unavailable"
    if metric_key in _PERCENT_METRICS:
        return f"{value * 100:.1f}%"
    if metric_key in ("current_ratio", "debt_to_equity"):
        return f"{value:.2f}x"
    if metric_key == "shares_outstanding":
        return f"{value:,.0f}"
    if unit == "currency_per_share":
        return f"{value:g} {currency or 'currency'}/share"
    if unit == "currency":
        return f"{value:,.0f}"
    return f"{value:g}"


def _render_observation_context(
    item: FinancialObservation,
    *,
    prefix: str = "",
) -> None:
    st.caption(
        f"{prefix}{item.definition} · scale {item.source_scale:g} · "
        f"source {item.provenance.source_id} · "
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
