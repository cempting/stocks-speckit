"""Streamlit workflow for the sector discovery view."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from market_leadership.application.compare_markets import MarketComparison, compare_markets
from market_leadership.application.discover_sectors import (
    BENCHMARK,
    SECTOR_PROXIES,
    DiscoveryResult,
    discover_sectors_from_history,
)
from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.bootstrap import (
    build_fixture_market_context,
    build_request_provider,
    build_snapshot_repository,
)
from market_leadership.config import load_settings
from market_leadership.infrastructure.snapshot_errors import (
    SchemaMismatch,
    SnapshotNotFound,
    SourceUnavailable,
)
from market_leadership.ui.cache import load_published_discovery
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


@st.cache_data(show_spinner=False)
def _calculate_discovery(
    provider_id: str,
    as_of: date,
    history: dict[str, pd.DataFrame],
    cache_schema_version: int,
) -> DiscoveryResult:
    del cache_schema_version  # Its value participates in Streamlit's cache key.
    return discover_sectors_from_history(provider_id, history, as_of=as_of)


def load_discovery(
    provider_id: str,
    source_cache_path: str,
    as_of: date,
    *,
    force_refresh: bool,
    cache_schema_version: int,
    retry_limit: int,
) -> DiscoveryResult:
    provider = build_request_provider(
        provider_id,
        source_cache_path,
        retry_limit=retry_limit,
    )
    history = provider.fetch_daily_history(
        (BENCHMARK, *(symbol for _, symbol in SECTOR_PROXIES)),
        start=as_of - timedelta(days=550),
        end=as_of,
        force=force_refresh,
    )
    return _calculate_discovery(provider_id, as_of, history, cache_schema_version)


def provider_options(default_provider: str, massive_available: bool) -> list[str]:
    if default_provider == "fixture":
        return ["fixture"]
    options = ["yfinance"]
    if massive_available:
        options.insert(0, "massive")
    return options


def render_fixture_comparison(comparison: MarketComparison) -> None:
    for overview in comparison.markets:
        st.subheader(f"{overview.name} ({overview.market_id})")
        observed_on = overview.as_of.isoformat() if overview.as_of is not None else "Unavailable"
        available_on = (
            overview.source_available_on.isoformat()
            if overview.source_available_on is not None
            else "Unavailable"
        )
        coverage_start = (
            overview.coverage_start.isoformat()
            if overview.coverage_start is not None
            else "Unavailable"
        )
        st.caption(
            f"Benchmark {overview.benchmark_id} · {overview.currency} · "
            f"{overview.calendar_id} · {observed_on} · "
            f"{overview.return_basis} · source {overview.source_id} available "
            f"{available_on} · coverage since {coverage_start}"
        )
        st.metric("Local regime", overview.regime)
        if overview.freshness == "insufficient":
            st.warning(f"{overview.market_id} local benchmark evidence is insufficient.")
        elif overview.freshness != "current":
            st.warning(f"{overview.market_id} benchmark or sector evidence is stale.")
        if overview.sector_outcomes:
            st.caption("Three-month local relative proxy outcomes; not weekly leadership ranks")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Sector": outcome.sector,
                            "3 months vs local benchmark": outcome.relative_3m * 100,
                            "Status": overview.freshness.title(),
                        }
                        for outcome in overview.sector_outcomes
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No dated sector outcomes are available for this market.")
        if overview.global_context is not None:
            st.caption(
                f"Separate global benchmark {overview.global_context.benchmark_id} "
                f"({overview.global_context.currency})"
            )
        elif overview.global_unavailable_reason is not None:
            st.warning(overview.global_unavailable_reason)


settings = load_settings()
selected_provider: str | None = None
requested_as_of: date | None = None
selected_markets: tuple[str, ...] = ()
force_refresh = False

(
    title_column,
    source_column,
    provider_column,
    date_column,
    refresh_column,
    theme_column,
) = st.columns([2.1, 1, 1, 1, 0.8, 0.8])
with source_column:
    source_mode = st.selectbox(
        "Data source",
        ["Live provider", "Published snapshot", "Acceptance fixture"],
        key="discovery_source_mode",
    )
with title_column:
    if source_mode == "Acceptance fixture":
        st.title("Market Comparison")
        st.caption("Controlled US/JP/GB sample · not live market data")
    else:
        st.title("US Sector Discovery")
        st.caption("GICS sector leadership through liquid US-listed proxies")
with provider_column:
    if source_mode == "Live provider":
        options = provider_options(settings.default_provider, settings.massive_available)
        selected_provider = st.selectbox(
            "Data provider",
            options,
            index=options.index(settings.default_provider)
            if settings.default_provider in options
            else 0,
            format_func=lambda value: "Massive" if value == "massive" else value.title(),
        )
    elif source_mode == "Acceptance fixture":
        selected_markets = tuple(
            st.multiselect(
                "Markets",
                options=("US", "JP", "GB"),
                default=("US",),
                key="selected_fixture_markets",
            )
        )
with date_column:
    if source_mode in ("Live provider", "Acceptance fixture"):
        market_today = datetime.now(ZoneInfo("America/New_York")).date()
        requested_as_of = st.date_input(
            "As of",
            value=date(2026, 10, 23) if source_mode == "Acceptance fixture" else market_today,
            max_value=market_today,
        )
with refresh_column:
    if source_mode == "Live provider":
        st.write("")
        st.write("")
        force_refresh = st.button(
            "Refresh data",
            icon=":material/refresh:",
            use_container_width=True,
        )
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

if source_mode == "Acceptance fixture":
    if not selected_markets:
        st.info("Select at least one fixture market to compare local outcomes.")
        st.stop()
    if requested_as_of is None:
        raise RuntimeError("Fixture observation date is unavailable")
    try:
        comparison = compare_markets(
            selected_markets,
            market_data=build_fixture_market_context(),
            as_of=requested_as_of,
        )
    except (SourceUnavailable, SchemaMismatch, KeyError, ValueError):
        st.error("Acceptance market context could not be loaded. Check the controlled fixture.")
        st.stop()
    render_fixture_comparison(comparison)
    st.stop()

try:
    if source_mode == "Published snapshot":
        with st.spinner("Loading published daily-history snapshot..."):
            reference, discovery = load_published_discovery(
                build_snapshot_repository(settings),
                settings.snapshot_dir,
            )
        snapshot_label = f" · SNAPSHOT {reference.snapshot_id}"
    else:
        if selected_provider is None or requested_as_of is None:
            raise RuntimeError("Live data controls are unavailable")
        with st.spinner(f"Loading {selected_provider} market data..."):
            discovery = load_discovery(
                selected_provider,
                settings.source_cache_path,
                requested_as_of,
                force_refresh=force_refresh,
                cache_schema_version=DISCOVERY_CACHE_SCHEMA_VERSION,
                retry_limit=settings.retry_limit,
            )
        snapshot_label = ""
except SnapshotNotFound:
    st.warning("No published daily-history snapshot is available. Build one with the snapshot CLI.")
    st.stop()
except Exception as error:
    st.error("Market data could not be loaded. The previous cached result was not replaced.")
    st.exception(error)
    st.stop()

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.markdown("#### S&P 500 sentiment")
benchmark_date = discovery.benchmark_as_of
benchmark_current = benchmark_date == latest_completed_us_session(discovery.as_of)
if not benchmark_current:
    observation = benchmark_date.isoformat() if benchmark_date is not None else "unavailable"
    st.warning(
        f"SPY close is unavailable for the requested completed session. "
        f"Latest usable SPY close: {observation}. Results are stale or insufficient."
    )
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
            "Status": (
                "Current"
                if metrics and benchmark_current
                else "Stale"
                if metrics
                else "Insufficient history"
            ),
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
    f" · SPY OBSERVED {benchmark_date.isoformat() if benchmark_date else 'UNAVAILABLE'}"
    f" · ADJUSTED DAILY BARS{snapshot_label}"
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
