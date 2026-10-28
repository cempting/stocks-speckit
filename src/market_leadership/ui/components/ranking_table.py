"""Render supplied weekly ranking values without recalculating leadership."""

import pandas as pd
import streamlit as st


def render_ranking_table(entries: pd.DataFrame, *, industry: bool = False) -> None:
    columns = [
        ("name", "Industry" if industry else "Sector"),
        ("rank", "Rank"),
        ("status", "Status"),
        ("composite", "Composite"),
        ("score_change", "Score change"),
        ("rank_change", "Rank change"),
        ("momentum", "Momentum"),
        ("proxy_type", "Proxy"),
        ("sufficiency", "Sufficiency"),
        ("as_of", "As of"),
        ("observation_date", "Observed"),
        ("available_on", "Available on"),
        ("coverage_start", "Coverage since"),
    ]
    if industry:
        columns.extend(
            [
                ("parent_relative_3m", "3m vs parent sector"),
                ("relative_3m", "3m vs local benchmark"),
            ]
        )
    columns.extend(
        [
            ("composition_basis", "Composition basis"),
            ("source_id", "Source"),
            ("missing_reasons", "Missing evidence"),
        ]
    )
    required = {field for field, _ in columns}
    if missing := required.difference(entries.columns):
        raise ValueError(f"weekly ranking is missing fields: {', '.join(sorted(missing))}")
    displayed = entries.loc[:, [field for field, _ in columns]].copy()
    displayed.columns = [label for _, label in columns]
    st.dataframe(displayed, hide_index=True, width="stretch")
