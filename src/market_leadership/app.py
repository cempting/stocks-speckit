import streamlit as st

from market_data.domain.catalog import CatalogError
from market_leadership.config import load_settings
from market_leadership.ui.cache import load_catalog_snapshot
from market_leadership.ui.navigation import clear_catalog_selections, preserve_catalog_controls
from market_leadership.ui.theme import apply_theme
from market_leadership.ui.workflows.discovery_page import render_discovery
from market_leadership.ui.workflows.industry_deep_dive import render_industry_deep_dive
from market_leadership.ui.workflows.stock_lookup import render_stock_lookup
from market_leadership.ui.workflows.yahoo_classification_preview import (
    render_yahoo_classification_preview,
)

st.set_page_config(page_title="Market Leadership Screener", layout="wide")
settings = load_settings()
preserve_catalog_controls()
discovery_tab, industry_tab, yahoo_classification_tab, stock_lookup_tab = st.tabs(
    ("Discovery", "Industry Deep-Dive", "Yahoo Classification Preview", "Find a stock")
)
try:
    snapshot = load_catalog_snapshot(settings.catalog_manifest_path)
except (CatalogError, OSError, ValueError) as error:
    apply_theme()
    clear_catalog_selections()
    st.error(f"Active catalog is unavailable or invalid: {error}")
else:
    with discovery_tab:
        render_discovery(configure_page=False, settings=settings, snapshot=snapshot)
    with industry_tab:
        render_industry_deep_dive(settings, snapshot=snapshot)
    with yahoo_classification_tab:
        render_yahoo_classification_preview(settings, snapshot=snapshot)
    with stock_lookup_tab:
        render_stock_lookup(configure_page=False, settings=settings, snapshot=snapshot)
