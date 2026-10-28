"""Industry rows retain the selected sector and local benchmark context."""

import streamlit as st

from market_leadership.application.inspect_industry import IndustryInspection
from market_leadership.ui.components.ranking_table import render_ranking_table


def render_industry_detail(detail: IndustryInspection) -> None:
    st.subheader(f"{detail.parent_sector} industries")
    st.caption(
        f"{detail.market_id} · parent sector {detail.parent_sector} · "
        f"local benchmark {detail.benchmark_id} · {detail.currency} · "
        f"{detail.as_of.isoformat()} · {detail.return_basis}"
    )
    if detail.unavailable_reason is not None:
        st.info(detail.unavailable_reason)
    elif detail.entries.empty:
        st.info("No dated industries are available for this sector.")
    else:
        st.caption("Local-relative and parent-sector-relative historical outcomes; not forecasts")
        render_ranking_table(detail.entries, industry=True)
