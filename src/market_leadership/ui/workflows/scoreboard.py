"""Read-only weekly sector-first discovery across independent local markets."""

from datetime import date

import streamlit as st

from market_leadership.application.browse_scoreboard import browse_weekly_scoreboard
from market_leadership.application.inspect_industry import inspect_industry
from market_leadership.bootstrap import build_snapshot_repository
from market_leadership.config import load_settings
from market_leadership.infrastructure.snapshot_errors import IntegrityError, SchemaMismatch
from market_leadership.ui.components.ranking_table import render_ranking_table
from market_leadership.ui.components.regime_summary import render_regime_summary
from market_leadership.ui.workflows.industry_detail import render_industry_detail


def render_scoreboard() -> None:
    st.set_page_config(page_title="Weekly Sector Leadership", layout="wide")
    st.title("Weekly Sector Leadership")
    st.caption(
        "Controlled fixture-backed weekly results · local markets only · "
        "not live JP/GB data or investment advice"
    )
    selected = tuple(
        st.multiselect(
            "Markets",
            options=("US", "JP", "GB"),
            default=("US",),
            key="selected_weekly_markets",
        )
    )
    if not selected:
        st.info("Select one or more markets to view their calculated weekly sectors.")
        return
    repository = build_snapshot_repository(load_settings())
    try:
        boards = browse_weekly_scoreboard(repository, selected, as_of=date.today())
    except (IntegrityError, SchemaMismatch):
        st.error("A calculated weekly snapshot failed validation; no rankings were displayed.")
        return
    for board in boards:
        st.subheader(f"{board.market_id} · Sector leadership")
        if board.unavailable_reason is not None:
            st.info(
                f"{board.market_id}: {board.unavailable_reason}. "
                "Publish a completed weekly snapshot before using the scoreboard."
            )
            continue
        if board.as_of is None or board.benchmark_id is None:
            st.error(f"{board.market_id}: calculated weekly snapshot lacks local context.")
            continue
        st.caption(
            f"Local benchmark {board.benchmark_id} · {board.currency} · "
            f"{board.calendar_id} · week {board.as_of.isoformat()} · {board.return_basis} · "
            f"snapshot {board.snapshot_id} · ranks within {board.market_id} sectors"
        )
        if board.freshness == "STALE":
            st.warning(
                f"{board.market_id} weekly snapshot is stale; no newer completed week is published."
            )
        render_regime_summary(board.regime)
        if board.entries.empty:
            st.info(f"{board.market_id}: no eligible sectors are available.")
            continue
        render_ranking_table(board.entries)
        names = board.entries["name"].tolist()
        selected_sector = st.selectbox(
            "Sector",
            options=names,
            index=None,
            placeholder="Select a sector for its industries",
            key=f"weekly_sector_{board.market_id}",
        )
        if selected_sector is not None:
            selected_row = board.entries.loc[board.entries["name"] == selected_sector]
            if len(selected_row) != 1:
                st.error(f"{board.market_id}: sector selection is ambiguous.")
                continue
            try:
                detail = inspect_industry(
                    repository,
                    market_id=board.market_id,
                    sector_node_id=str(selected_row.iloc[0]["node_id"]),
                )
            except (IntegrityError, SchemaMismatch, ValueError):
                st.error(f"{board.market_id}: industry context could not be validated.")
                continue
            render_industry_detail(detail)


if __name__ == "__main__":
    render_scoreboard()
