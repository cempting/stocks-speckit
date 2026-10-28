from runpy import run_module

import streamlit as st

from market_leadership.bootstrap import build_workflow_registry
from market_leadership.ui.navigation import to_pages


def _render_discovery() -> None:
    run_module("market_leadership.ui.workflows.discovery_page", run_name="__main__")


navigation = st.navigation(to_pages(build_workflow_registry(_render_discovery)))
navigation.run()
