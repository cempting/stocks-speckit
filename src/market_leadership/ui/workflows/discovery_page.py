"""Live-only Streamlit workflow for US sector and industry discovery."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from market_leadership.application.discover_sectors import (
    BENCHMARK,
    SECTOR_PROXIES,
    DiscoveryResult,
    discover_sectors_from_history,
)
from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.bootstrap import build_request_provider
from market_leadership.config import load_settings
from market_leadership.domain.industry_momentum import industry_momentum_frame, industry_symbols
from market_leadership.infrastructure.experimental_universe_catalog import (
    load_experimental_catalog,
)
from market_leadership.ui.dataframe import render_dataframe
from market_leadership.ui.performance_table import performance_table_height, style_performance_table
from market_leadership.ui.sector_chart import build_sector_chart

DISCOVERY_CACHE_SCHEMA_VERSION = 3


@st.cache_data(show_spinner=False)
def _calculate_discovery(
    as_of: date, history: dict[str, pd.DataFrame], cache_schema_version: int
) -> DiscoveryResult:
    del cache_schema_version
    return discover_sectors_from_history("yfinance", history, as_of=as_of)


def load_discovery(
    source_cache_path: str,
    as_of: date,
    *,
    force_refresh: bool,
    retry_limit: int,
) -> tuple[DiscoveryResult, dict[str, pd.DataFrame]]:
    provider = build_request_provider("yfinance", source_cache_path, retry_limit=retry_limit)
    symbols = (BENCHMARK, *(symbol for _, symbol in SECTOR_PROXIES), *industry_symbols())
    history = provider.fetch_daily_history(
        symbols,
        start=as_of - timedelta(days=550),
        end=as_of,
        force=force_refresh,
    )
    return _calculate_discovery(as_of, history, DISCOVERY_CACHE_SCHEMA_VERSION), history


def _industry_chart(frame: pd.DataFrame, *, dark_mode: bool) -> None:
    if len(frame) < 150:
        st.info("Industry chart evidence is insufficient: fewer than 150 completed sessions.")
        return
    chart_history = frame.sort_index().copy()
    chart_history["sma50"] = chart_history["close"].rolling(50, min_periods=50).mean()
    chart_history["sma150"] = chart_history["close"].rolling(150, min_periods=150).mean()
    trend = (
        float(chart_history["sma50"].iloc[-1] / chart_history["sma50"].iloc[-21] - 1)
        if pd.notna(chart_history["sma50"].iloc[-21])
        else None
    )
    st.caption(
        "Industry-owned adjusted-close and official-session volume evidence; "
        "historical analysis, not a recommendation or forecast."
    )
    st.caption(
        f"50-session average: {chart_history['sma50'].iloc[-1]:.2f} · "
        f"150-session average: {chart_history['sma150'].iloc[-1]:.2f} · "
        f"50-session trend: {trend:.2%}" if trend is not None else "Trend evidence is insufficient."
    )
    st.altair_chart(build_sector_chart(chart_history, dark_mode=dark_mode), width="stretch")


def _render_experimental_universe_catalog(path: str) -> None:
    st.subheader("Experimental provider-label industry catalog")
    st.caption(
        "This is a provisional US-universe experiment, not the GICS momentum catalog. "
        "It does not select stock proxies or assign market-cap bands until dated evidence is added."
    )
    try:
        catalog = load_experimental_catalog(path)
    except FileNotFoundError:
        st.info("No experimental catalog has been generated yet.")
        return
    except (OSError, ValueError) as error:
        st.error(f"Experimental industry catalog could not be loaded: {error}")
        return
    frame = pd.DataFrame(
        [
            {
                "Sector": industry.sector,
                "Industry": industry.industry,
                "Members": industry.member_count,
                "Sources": ", ".join(industry.source_ids),
                "Classification conflicts": industry.classification_conflict_count,
                "Market-cap band": "Unverified",
                "Proxy status": "Awaiting qualification",
            }
            for industry in catalog.industries
        ]
    )
    st.caption(
        f"Retrieved {catalog.generated_at.date().isoformat()} · "
        f"{catalog.member_count:,} classified securities · "
        f"{len(catalog.industries)} provider-label industries"
    )
    render_dataframe(frame, hide_index=True, height=700, width="stretch")


def render_discovery(*, configure_page: bool = True) -> None:
    if configure_page:
        st.set_page_config(page_title="Discovery", page_icon="📊", layout="wide")
    settings = load_settings()
    market_today = datetime.now(ZoneInfo("America/New_York")).date()
    dark_mode = bool(st.session_state.get("dark_mode", False))
    st.title("Discovery")
    st.caption("Live US market evidence from yfinance. Historical outcomes are not forecasts.")

    date_column, refresh_column = st.columns((3, 1))
    with date_column:
        requested_as_of = st.date_input("As of", value=market_today, max_value=market_today)
    with refresh_column:
        st.write("")
        force_refresh = st.button("Refresh data", use_container_width=True)
    try:
        with st.spinner("Loading yfinance market data..."):
            discovery, history = load_discovery(
                settings.source_cache_path,
                requested_as_of,
                force_refresh=force_refresh,
                retry_limit=settings.retry_limit,
            )
    except Exception as error:
        st.error("Live yfinance market data could not be loaded; no fallback data is displayed.")
        st.exception(error)
        return

    observed = discovery.benchmark_as_of
    st.caption(
        f"SOURCE YFINANCE · REQUESTED {requested_as_of.isoformat()} · "
        f"OBSERVED {observed.isoformat() if observed else 'UNAVAILABLE'} · ADJUSTED DAILY BARS"
    )
    if observed != latest_completed_us_session(requested_as_of):
        st.warning(
            "The latest completed benchmark session is unavailable; "
            "results are stale or insufficient."
        )

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

    sector_rows: list[dict[str, object]] = []
    for sector in discovery.sectors:
        metrics = None
        if sector.performance is not None:
            metrics = (
                sector.performance.absolute
                if performance_mode == "Absolute"
                else sector.performance.relative
            )
        sector_rows.append(
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
                    if metrics and observed == latest_completed_us_session(requested_as_of)
                    else "Stale"
                    if metrics
                    else "Insufficient history"
                ),
            }
        )
    sector_frame = pd.DataFrame(sector_rows)
    render_dataframe(
        style_performance_table(sector_frame, dark_mode=dark_mode),
        key=f"sector_performance_table_{'dark' if dark_mode else 'light'}",
        hide_index=True,
        height=performance_table_height(len(sector_frame)),
        width="stretch",
        column_config={
            "1 week": st.column_config.NumberColumn(format="%.2f%%"),
            "1 month": st.column_config.NumberColumn(format="%.2f%%"),
            "3 months": st.column_config.NumberColumn(format="%.2f%%"),
            "6 months": st.column_config.NumberColumn(format="%.2f%%"),
            "12 months": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    st.subheader("Industry momentum")
    available_sectors = tuple(name for name, _ in SECTOR_PROXIES)
    selected_sectors = tuple(
        st.multiselect("Parent sectors", available_sectors, default=list(available_sectors))
    )
    scope = ", ".join(selected_sectors) if selected_sectors else "no parent sectors"
    st.caption(f"Trend scope: {scope} · adjusted-close returns")
    industries = industry_momentum_frame(
        history,
        as_of=observed or requested_as_of,
        sectors=selected_sectors,
    )
    if industries.empty:
        st.info("No eligible industry data is available for the selected sector scope.")
    else:
        render_dataframe(
            style_performance_table(industries, dark_mode=dark_mode),
            hide_index=True,
            height=performance_table_height(len(industries)),
            width="stretch",
            column_config={
                "1 week": st.column_config.NumberColumn(format="%.2f%%"),
                "1 month": st.column_config.NumberColumn(format="%.2f%%"),
                "3 months": st.column_config.NumberColumn(format="%.2f%%"),
                "6 months": st.column_config.NumberColumn(format="%.2f%%"),
                "12 months": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )
        choices = industries.loc[industries["1 week"].notna(), ["Industry", "Representation"]]
        if not choices.empty:
            selected = st.selectbox(
                "Inspect industry chart", choices["Industry"].tolist(), index=None
            )
            if selected is not None:
                symbol = choices.loc[choices["Industry"].eq(selected), "Representation"].iloc[0]
                _industry_chart(history[symbol], dark_mode=dark_mode)

    _render_experimental_universe_catalog(settings.experimental_universe_catalog)

    st.subheader("Sector tape")
    for sector in discovery.sectors:
        if sector.history.empty:
            st.info(f"{sector.name}: no chart history is available.")
        else:
            st.markdown(f"#### {sector.name} · `{sector.symbol}`")
            st.altair_chart(
                build_sector_chart(sector.history, dark_mode=dark_mode), width="stretch"
            )


if __name__ == "__main__":
    render_discovery()
