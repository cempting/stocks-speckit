from datetime import date

import pandas as pd
import streamlit as st

from market_leadership.application.discover_sectors import DiscoveryResult, discover_sectors
from market_leadership.bootstrap import build_provider
from market_leadership.config import load_settings
from market_leadership.ui.performance_table import (
    performance_table_height,
    style_performance_table,
)
from market_leadership.ui.sector_chart import build_sector_chart

DISCOVERY_CACHE_SCHEMA_VERSION = 2

st.set_page_config(
    page_title="US Sector Discovery",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark_mode = bool(st.session_state.dark_mode)
theme = (
    {
        "ink": "#edf3f7",
        "muted": "#aebbc8",
        "line": "#334451",
        "paper": "#111820",
        "surface": "#18232d",
        "control": "#22313d",
        "selected": "#3f2728",
        "accent_text": "#ff9b91",
    }
    if dark_mode
    else {
        "ink": "#17212b",
        "muted": "#64707d",
        "line": "#dce2e7",
        "paper": "#f7f8f6",
        "surface": "#ffffff",
        "control": "#e9eeea",
        "selected": "#faecea",
        "accent_text": "#a83d34",
    }
)

st.markdown(
    f"""
    <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap'
        );
    :root {{
        --ink: {theme["ink"]};
        --muted: {theme["muted"]};
        --line: {theme["line"]};
        --paper: {theme["paper"]};
        --surface: {theme["surface"]};
        --control: {theme["control"]};
        --selected: {theme["selected"]};
        --accent-text: {theme["accent_text"]};
    }}
    .stApp {{
        background: var(--paper);
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }}
    [data-testid="stHeader"] {{ background: var(--paper); }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label {{
        color: var(--ink);
    }}
    h1, h2, h3 {{ font-family: 'DM Sans', sans-serif; letter-spacing: 0; }}
    h1 {{ font-size: 2rem !important; font-weight: 700 !important; }}
    [data-testid="stCaptionContainer"] p {{ color: var(--muted); }}
    [data-baseweb="select"] > div,
    [data-testid="stDateInput"] input {{
        background: var(--surface);
        border-color: var(--line);
        color: var(--ink);
    }}
    [data-testid="stButton"] button[kind="secondary"] {{
        background: var(--surface);
        border-color: var(--line);
        color: var(--ink);
    }}
    [data-testid="stButton"] button[kind="secondary"]:hover {{
        background: var(--control);
        border-color: var(--accent-text);
        color: var(--ink);
    }}
    [data-testid="stButton"] button[kind="secondary"] p,
    [data-variant="segmented_control"] p {{ color: inherit !important; }}
    [data-variant="segmented_control"] {{
        background: var(--surface) !important;
        border-color: var(--line) !important;
        color: var(--ink) !important;
    }}
    [data-variant="segmented_control"][data-selected="true"] {{
        background: var(--selected) !important;
        border-color: var(--accent-text) !important;
        color: var(--accent-text) !important;
    }}
    [data-testid="stMetric"] {{
        background: transparent;
        border-left: 3px solid #6f8f7b;
        padding-left: 1rem;
    }}
    [data-testid="stMetricLabel"] {{ color: var(--muted); }}
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--line);
        border-radius: 6px;
        color-scheme: {"dark" if dark_mode else "light"};
    }}
    [data-testid="stDataFrameResizable"] {{ border-color: var(--line) !important; }}
    .stDataFrameGlideDataEditor {{
        --gdg-text-dark: {theme["ink"]} !important;
        --gdg-text-medium: {theme["muted"]} !important;
        --gdg-text-light: {theme["muted"]} !important;
        --gdg-text-header: {theme["muted"]} !important;
        --gdg-bg-cell: {theme["surface"]} !important;
        --gdg-bg-cell-medium: {theme["surface"]} !important;
        --gdg-bg-header: {theme["control"]} !important;
        --gdg-bg-header-has-focus: {theme["line"]} !important;
        --gdg-bg-header-hovered: {theme["line"]} !important;
        --gdg-border-color: {theme["line"]} !important;
        --gdg-horizontal-border-color: {theme["line"]} !important;
    }}
    .source-line {{ color: var(--muted) !important; font: 500 0.78rem 'IBM Plex Mono', monospace; }}
    .section-rule {{ border-top: 1px solid var(--line); margin: 1.2rem 0 1rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_discovery(
    provider_id: str,
    cache_path: str,
    as_of: date,
    refresh_version: int,
    cache_schema_version: int,
) -> DiscoveryResult:
    del cache_schema_version  # Its value participates in Streamlit's cache key.
    provider = build_provider(provider_id, cache_path)
    return discover_sectors(provider, as_of=as_of, force=refresh_version > 0)


def provider_options(default_provider: str, massive_available: bool) -> list[str]:
    if default_provider == "fixture":
        return ["fixture"]
    options = ["yfinance"]
    if massive_available:
        options.insert(0, "massive")
    return options


settings = load_settings()
if "refresh_version" not in st.session_state:
    st.session_state.refresh_version = 0

title_column, provider_column, date_column, refresh_column, theme_column = st.columns(
    [2.1, 1, 1, 0.8, 0.8]
)
with title_column:
    st.title("US Sector Discovery")
    st.caption("GICS sector leadership through liquid US-listed proxies")
with provider_column:
    options = provider_options(settings.default_provider, settings.massive_available)
    selected_provider = st.selectbox(
        "Data provider",
        options,
        index=(
            options.index(settings.default_provider) if settings.default_provider in options else 0
        ),
        format_func=lambda value: "Massive" if value == "massive" else value.title(),
    )
with date_column:
    requested_as_of = st.date_input("As of", value=date.today(), max_value=date.today())
with refresh_column:
    st.write("")
    st.write("")
    if st.button("Refresh data", icon=":material/refresh:", use_container_width=True):
        st.session_state.refresh_version += 1
with theme_column:
    st.write("")
    st.write("")
    if st.button(
        "",
        key="theme_mode_button",
        icon=":material/light_mode:" if dark_mode else ":material/dark_mode:",
        help="Switch to light mode" if dark_mode else "Switch to dark mode",
        type="secondary",
        width="stretch",
    ):
        st.session_state.dark_mode = not dark_mode
        st.rerun()

try:
    with st.spinner(f"Loading {selected_provider} market data..."):
        discovery = load_discovery(
            selected_provider,
            settings.market_data_cache_path,
            requested_as_of,
            st.session_state.refresh_version,
            DISCOVERY_CACHE_SCHEMA_VERSION,
        )
except Exception as error:
    st.error("Market data could not be loaded. The previous cached result was not replaced.")
    st.exception(error)
    st.stop()

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.markdown("#### S&P 500 sentiment")
sentiment = discovery.sentiment
metric_columns = st.columns(4)
metric_columns[0].metric("Regime", sentiment.regime)
metric_columns[1].metric(
    "SPY close",
    f"${sentiment.close:,.2f}" if sentiment.close is not None else "Unavailable",
)
metric_columns[2].metric(
    "150-session average",
    f"${sentiment.sma150:,.2f}" if sentiment.sma150 is not None else "Unavailable",
)
metric_columns[3].metric(
    "Average trend",
    sentiment.slope_state,
    f"{sentiment.normalized_slope_pct:.3f}% / session"
    if sentiment.normalized_slope_pct is not None
    else None,
)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
heading_column, mode_column = st.columns([2, 1])
with heading_column:
    st.subheader("Sector performance")
    st.caption("Split-adjusted close returns over matching lookback periods")
with mode_column:
    performance_mode = st.segmented_control(
        "Performance basis",
        options=["Absolute", "vs S&P 500"],
        default="Absolute",
        selection_mode="single",
    )

performance_rows: list[dict[str, object]] = []
for sector in discovery.sectors:
    metrics = None
    if sector.performance is not None:
        metrics = (
            sector.performance.absolute
            if performance_mode == "Absolute"
            else sector.performance.relative
        )
    performance_rows.append(
        {
            "Sector": sector.name,
            "Proxy": sector.symbol,
            "1 week": metrics["1w"] * 100 if metrics else None,
            "1 month": metrics["1m"] * 100 if metrics else None,
            "3 months": metrics["3m"] * 100 if metrics else None,
            "6 months": metrics["6m"] * 100 if metrics else None,
            "12 months": metrics["12m"] * 100 if metrics else None,
            "Status": "Current" if metrics else "Insufficient history",
        }
    )

performance_frame = pd.DataFrame(performance_rows)
st.dataframe(
    style_performance_table(performance_frame, dark_mode=dark_mode),
    key=f"performance_table_{'dark' if dark_mode else 'light'}",
    hide_index=True,
    height=performance_table_height(len(performance_frame)),
    width="stretch",
    column_config={
        "1 week": st.column_config.NumberColumn(format="%.2f%%"),
        "1 month": st.column_config.NumberColumn(format="%.2f%%"),
        "3 months": st.column_config.NumberColumn(format="%.2f%%"),
        "6 months": st.column_config.NumberColumn(format="%.2f%%"),
        "12 months": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

source_label = (
    f"SOURCE {discovery.provider_id.upper()} · REQUESTED {discovery.as_of.isoformat()}"
    " · ADJUSTED DAILY BARS"
)
st.markdown(f'<p class="source-line">{source_label}</p>', unsafe_allow_html=True)
st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.subheader("Sector tape")
st.caption("Latest 260 sessions · adjusted close and SMA50 · official-session volume")

chart_columns = st.columns(2)
for index, sector in enumerate(discovery.sectors):
    with chart_columns[index % 2]:
        st.markdown(f"#### {sector.name} · `{sector.symbol}`")
        if sector.history.empty:
            st.warning("No chart history is available for this proxy.")
        else:
            st.altair_chart(
                build_sector_chart(sector.history, dark_mode=dark_mode),
                width="stretch",
            )
