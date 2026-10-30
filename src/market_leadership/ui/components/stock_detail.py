"""Detailed chart and peer-score view for one validated stock identity."""

from collections.abc import Callable

import streamlit as st

from market_leadership.domain.peer_scores import BlockPeerScore, PeerScorecard
from market_leadership.domain.stock_chart import StockChartEvidence
from market_leadership.domain.stock_selection import MembershipEntry
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
    member: MembershipEntry,
    chart: StockChartEvidence,
    *,
    scorecard: PeerScorecard | None,
    score_state: str,
    score_reason: str | None,
    dark_mode: bool,
    on_return: Callable[[], None],
) -> None:
    st.title(f"{member.symbol} · {member.name}")
    st.caption(f"Instrument {member.instrument_id} · Industry {member.industry_name}")
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

    st.button(
        "Back to Discovery",
        key="market_leadership.stock_detail.back",
        on_click=on_return,
    )
