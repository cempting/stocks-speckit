import streamlit as st

from market_leadership.config import load_settings
from market_leadership.ui.workflows.discovery_page import render_discovery
from market_leadership.ui.workflows.industry_deep_dive import render_industry_deep_dive

st.set_page_config(page_title="Market Leadership Screener", layout="wide")
settings = load_settings()
discovery_tab, industry_tab = st.tabs(("Discovery", "Industry Deep-Dive"))
with discovery_tab:
    render_discovery(configure_page=False)
with industry_tab:
    render_industry_deep_dive(settings)
