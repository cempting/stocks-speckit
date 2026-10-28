from runpy import run_module

import streamlit as st

from market_leadership.bootstrap import build_workflow_registry
from market_leadership.ui.workflows.industry_discovery import render_industry_discovery
from market_leadership.ui.navigation import register_workflow_pages


def _render_discovery() -> None:
    run_module("market_leadership.ui.workflows.discovery_page", run_name="__main__")


workflows = build_workflow_registry(
    _render_discovery,
    render_industry_discovery,
)
navigation = st.navigation(register_workflow_pages(workflows))
navigation.run()
