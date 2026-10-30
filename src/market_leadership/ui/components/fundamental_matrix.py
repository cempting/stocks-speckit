from datetime import date
from math import isfinite
from typing import Protocol, cast

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from market_leadership.domain.fundamentals import (
    METRIC_GROUPS,
    FundamentalMetric,
    FundamentalScorecard,
)


class _StreamlitCharts(Protocol):
    def bar_chart(
        self,
        data: dict[str, list[date] | list[float]],
        *,
        x: str,
        y: str,
        x_label: str,
        y_label: str,
        height: int,
    ) -> DeltaGenerator: ...


def _render_metric(metric: FundamentalMetric) -> None:
    valid = metric.value is not None and isfinite(metric.value)
    if metric.key == "eps_consistency" and metric.value is not None:
        valid = valid and 0 <= metric.value <= 8 and metric.value.is_integer()
    with st.container():
        st.markdown(metric.label)
        st.markdown(f"**{metric.formatted if valid else 'N/A'}**")
        st.caption(metric.commentary if valid else "Data not available")
        with st.container():
            if 4 <= len(metric.history) <= 8:
                cast(_StreamlitCharts, st).bar_chart(
                    {
                        "Quarter": [point.period for point in metric.history],
                        metric.label: [
                            point.value if metric.key == "eps_consistency" else point.value * 100
                            for point in metric.history
                        ],
                    },
                    x="Quarter",
                    y=metric.label,
                    x_label="",
                    y_label="",
                    height=60,
                )
            else:
                st.caption("Insufficient quarterly history")
        st.caption(metric.detail)


def render_fundamental_matrix(scorecard: FundamentalScorecard) -> None:
    st.markdown(f"#### {scorecard.symbol}")
    st.caption(
        f"Source {scorecard.provider_id} | Quarter {scorecard.period or 'unavailable'} | "
        f"Fetched {scorecard.fetched_at.isoformat()}"
    )
    for warning in scorecard.warnings:
        st.warning(warning)
    by_key = {metric.key: metric for metric in scorecard.metrics}
    for column, (group, definitions) in zip(st.columns(3), METRIC_GROUPS, strict=True):
        with column:
            st.subheader(group)
            for key, _ in definitions:
                _render_metric(by_key[key])
