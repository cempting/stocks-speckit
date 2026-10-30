"""Industry rows retain the selected sector and local benchmark context."""

import streamlit as st

from market_leadership.application.inspect_industry import IndustryInspection
from market_leadership.ui.dataframe import render_dataframe
from market_leadership.ui.performance_table import (
    industry_performance_frame,
    performance_table_height,
    style_performance_table,
)


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
        st.caption(
            "Short-period adjusted-close outcomes with qualified representation evidence; "
            "historical results, not forecasts."
        )
        frame = industry_performance_frame(detail.entries, parent_sector=detail.parent_sector)
        render_dataframe(
            style_performance_table(
                frame,
                dark_mode=bool(st.session_state.get("dark_mode", False)),
            ),
            hide_index=True,
            height=performance_table_height(len(frame)),
            width="stretch",
            column_config={
                "1 week": st.column_config.NumberColumn(format="%.2f%%"),
                "1 month": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )
