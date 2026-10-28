"""Render a supplied market regime without inferring one from ranking rows."""

import streamlit as st


def render_regime_summary(regime: str | None) -> None:
    st.metric("Local market regime", regime if regime is not None else "Unavailable")
