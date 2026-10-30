"""Live-only Streamlit workflow for progressive US sector and stock discovery."""

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
from market_leadership.application.load_stock_history import StockHistoryBatch
from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.score_industry import (
    IndustryScoreResult,
    score_industry,
)
from market_leadership.bootstrap import build_request_provider
from market_leadership.config import Settings, load_settings
from market_leadership.domain.industry_momentum import (
    INDUSTRY_REPRESENTATIONS,
    industry_momentum_frame,
    industry_symbols,
)
from market_leadership.domain.progressive_selection import (
    ProgressiveSelection,
    reconcile_progressive_selection,
)
from market_leadership.domain.stock_chart import build_stock_chart_evidence
from market_leadership.domain.stock_selection import MembershipEntry
from market_leadership.infrastructure.experimental_universe_catalog import (
    load_experimental_catalog,
)
from market_leadership.infrastructure.provider_errors import ProviderRequestError
from market_leadership.infrastructure.stock_membership import (
    load_membership_catalog,
    validate_live_access,
)
from market_leadership.ui.cache import load_member_history
from market_leadership.ui.components.progressive_tape import (
    StockTapeRow,
    attach_chart_series,
    build_stock_tape_frame,
    render_chart_tape,
    render_selectable_stock_tape,
)
from market_leadership.ui.components.stock_detail import render_stock_detail
from market_leadership.ui.dataframe import render_dataframe
from market_leadership.ui.performance_table import style_performance_table

DISCOVERY_CACHE_SCHEMA_VERSION = 3
_PREFIX = "market_leadership.progressive_discovery."
_SECTOR_KEY = _PREFIX + "sector"
_INDUSTRY_KEY = _PREFIX + "industry"
_STOCK_KEY = _PREFIX + "stock"
_STOCK_PICKER_KEY = _PREFIX + "stock_picker"
_CATALOG_KEY = _PREFIX + "catalog_fingerprint"
_MEMBERSHIP_DATE_KEY = _PREFIX + "membership_date"
_OBSERVATION_DATE_KEY = _PREFIX + "observation_date"
_SCORES_KEY = _PREFIX + "scores"
_SCORE_CONTEXT_KEY = _PREFIX + "score_context"


def _clear_stock_selection() -> None:
    st.session_state.pop(_STOCK_KEY, None)
    st.session_state.pop(_STOCK_PICKER_KEY, None)


def _clear_industry_descendants() -> None:
    st.session_state.pop(_INDUSTRY_KEY, None)
    st.session_state.pop(_STOCK_KEY, None)
    st.session_state.pop(_STOCK_PICKER_KEY, None)


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


def _read_selection() -> ProgressiveSelection:
    sector_id = st.session_state.get(_SECTOR_KEY)
    industry_id = st.session_state.get(_INDUSTRY_KEY)
    stock_id = st.session_state.get(_STOCK_KEY)
    valid_sectors = {symbol for _, symbol in SECTOR_PROXIES}
    return ProgressiveSelection(
        sector_id=sector_id if isinstance(sector_id, str) and sector_id in valid_sectors else None,
        industry_id=industry_id if isinstance(industry_id, str) else None,
        instrument_id=stock_id if isinstance(stock_id, str) else None,
        catalog_fingerprint=(
            st.session_state.get(_CATALOG_KEY)
            if isinstance(st.session_state.get(_CATALOG_KEY), str)
            else None
        ),
        membership_date=(
            st.session_state.get(_MEMBERSHIP_DATE_KEY)
            if isinstance(st.session_state.get(_MEMBERSHIP_DATE_KEY), date)
            else None
        ),
        observation_date=(
            st.session_state.get(_OBSERVATION_DATE_KEY)
            if isinstance(st.session_state.get(_OBSERVATION_DATE_KEY), date)
            else None
        ),
    )


def _store_selection(selection: ProgressiveSelection) -> None:
    if selection.sector_id is None:
        st.session_state.pop(_SECTOR_KEY, None)
    elif st.session_state.get(_SECTOR_KEY) != selection.sector_id:
        st.session_state[_SECTOR_KEY] = selection.sector_id
    if selection.industry_id is None:
        st.session_state.pop(_INDUSTRY_KEY, None)
    elif st.session_state.get(_INDUSTRY_KEY) != selection.industry_id:
        st.session_state[_INDUSTRY_KEY] = selection.industry_id
    if selection.instrument_id is None:
        st.session_state.pop(_STOCK_KEY, None)
    elif st.session_state.get(_STOCK_KEY) != selection.instrument_id:
        st.session_state[_STOCK_KEY] = selection.instrument_id
    st.session_state[_CATALOG_KEY] = selection.catalog_fingerprint
    st.session_state[_MEMBERSHIP_DATE_KEY] = selection.membership_date
    st.session_state[_OBSERVATION_DATE_KEY] = selection.observation_date


def _store_hierarchy(selection: ProgressiveSelection) -> None:
    if selection.sector_id is None:
        st.session_state.pop(_SECTOR_KEY, None)
    else:
        st.session_state[_SECTOR_KEY] = selection.sector_id
    if selection.industry_id is None:
        st.session_state.pop(_INDUSTRY_KEY, None)
    else:
        st.session_state[_INDUSTRY_KEY] = selection.industry_id
    if selection.instrument_id is None:
        st.session_state.pop(_STOCK_KEY, None)


def _reconcile_selection(
    selection: ProgressiveSelection,
    *,
    catalog_fingerprint: str,
    membership_date: date,
    observation_date: date,
    instrument_industry_by_id: dict[str, str] | None = None,
) -> ProgressiveSelection:
    industry_parent_by_id = {
        representation.industry_id: dict((name, symbol) for name, symbol in SECTOR_PROXIES).get(
            representation.sector, ""
        )
        for representation in INDUSTRY_REPRESENTATIONS
    }
    return reconcile_progressive_selection(
        selection,
        valid_sector_ids=tuple(symbol for _, symbol in SECTOR_PROXIES),
        industry_parent_by_id=industry_parent_by_id,
        instrument_industry_by_id=instrument_industry_by_id or {},
        catalog_fingerprint=catalog_fingerprint,
        membership_date=membership_date,
        observation_date=observation_date,
    )


def _render_member_tape(
    *,
    settings: Settings,
    requested_as_of: date,
    sector_id: str,
    industry_id: str,
    industry_name: str,
    sector_name: str,
    force_refresh: bool,
) -> None:
    if not settings.stock_membership_catalog:
        st.error(
            "Stock membership unavailable: configure STOCK_MEMBERSHIP_CATALOG after "
            "reviewing live coverage and display rights."
        )
        _clear_stock_selection()
        return
    try:
        catalog = load_membership_catalog(settings.stock_membership_catalog)
        validate_live_access(catalog, settings)
    except (OSError, ValueError) as error:
        st.error(f"Stock membership unavailable: {error}")
        _clear_stock_selection()
        return

    active_members: tuple[MembershipEntry, ...] = tuple(
        entry
        for entry in catalog.entries
        if entry.active_on(catalog.observed_on)
        and entry.sector_name == sector_name
        and entry.industry_name == industry_name
    )
    instrument_industry_by_id = {entry.instrument_id: industry_id for entry in active_members}
    previous = _read_selection()
    current = _reconcile_selection(
        ProgressiveSelection(
            sector_id=sector_id,
            industry_id=industry_id,
            instrument_id=previous.instrument_id,
            catalog_fingerprint=previous.catalog_fingerprint,
            membership_date=previous.membership_date,
            observation_date=previous.observation_date,
        ),
        catalog_fingerprint=catalog.fingerprint,
        membership_date=catalog.observed_on,
        observation_date=requested_as_of,
        instrument_industry_by_id=instrument_industry_by_id,
    )
    if previous.instrument_id is not None and current.instrument_id is None:
        _clear_stock_selection()
        st.warning("The selected stock was cleared because its membership context changed.")
    if current.industry_id is None:
        st.warning("The industry selection was cleared because its membership context changed.")
        return
    _store_selection(current)
    st.caption(
        f"{catalog.mode.upper()} · Membership {catalog.observed_on.isoformat()} · "
        f"Source {catalog.source_id} · {catalog.coverage}"
    )
    if not active_members:
        _clear_stock_selection()
        st.subheader("Contained stocks")
        st.info("This valid dated catalog has no active members for the selected industry.")
        return

    history_batch: StockHistoryBatch | None = None
    try:
        history_batch = load_member_history(
            settings.source_cache_path,
            tuple(entry.symbol for entry in active_members),
            requested_as_of,
            retry_limit=settings.retry_limit,
            force_refresh=force_refresh,
        )
        history_by_symbol = {item.symbol: item for item in history_batch.series}
    except (OSError, ProviderRequestError, ValueError) as error:
        st.error(f"Member price history could not be loaded: {error}")
        history_batch = None
        history_by_symbol = {}
    if history_batch is not None:
        observed_dates = tuple(
            item.observed_on for item in history_batch.series if item.observed_on is not None
        )
        observed_range = (
            f"{min(observed_dates).isoformat()} to {max(observed_dates).isoformat()}"
            if observed_dates
            else "unavailable"
        )
        st.caption(
            f"Price source {history_batch.provider_id.upper()} · requested "
            f"{history_batch.requested_as_of.isoformat()} · observed {observed_range}"
        )

    score_context = (
        catalog.fingerprint,
        catalog.observed_on,
        industry_id,
        requested_as_of,
    )
    saved_scores = st.session_state.get(_SCORES_KEY)
    score_result: IndustryScoreResult | None = None
    if st.session_state.get(_SCORE_CONTEXT_KEY) == score_context and isinstance(
        saved_scores, IndustryScoreResult
    ):
        score_result = saved_scores

    st.subheader("Contained stocks")
    if st.button("Load peer scores", key=_PREFIX + "load_scores"):
        try:
            with st.spinner("Loading complete industry peer evidence..."):
                score_result = score_industry(
                    active_members,
                    cutoff=requested_as_of,
                    refresh=force_refresh,
                )
            st.session_state[_SCORES_KEY] = score_result
            st.session_state[_SCORE_CONTEXT_KEY] = score_context
        except (OSError, ProviderRequestError, ValueError) as error:
            st.error(f"Industry peer scores could not be loaded: {error}")

    scores_by_id = (
        {item.instrument_id: item for item in score_result.stocks}
        if score_result is not None
        else {}
    )
    rows = tuple(
        StockTapeRow(
            instrument_id=entry.instrument_id,
            ticker=entry.symbol,
            name=entry.name,
            history=history_by_symbol[entry.symbol].history
            if entry.symbol in history_by_symbol
            else pd.DataFrame(columns=["close", "volume"]),
            price_state=history_by_symbol[entry.symbol].state
            if entry.symbol in history_by_symbol
            else "unavailable",
            observed_on=history_by_symbol[entry.symbol].observed_on
            if entry.symbol in history_by_symbol
            else None,
            price_reason=history_by_symbol[entry.symbol].reason
            if entry.symbol in history_by_symbol
            else "The provider request failed.",
            scorecard=scores_by_id[entry.instrument_id].scorecard
            if entry.instrument_id in scores_by_id
            else None,
            score_state=scores_by_id[entry.instrument_id].state
            if entry.instrument_id in scores_by_id
            else "not_loaded",
            score_reason=scores_by_id[entry.instrument_id].reason
            if entry.instrument_id in scores_by_id
            else None,
        )
        for entry in active_members
    )
    stock_frame = build_stock_tape_frame(rows)
    stock_by_id = {entry.instrument_id: entry for entry in active_members}
    selected_stock_id = st.session_state.get(_STOCK_KEY)
    if not isinstance(selected_stock_id, str) or selected_stock_id not in stock_by_id:
        selected_stock_id = st.selectbox(
            "Open stock detail",
            options=tuple(stock_by_id),
            index=None,
            key=_STOCK_PICKER_KEY,
            format_func=lambda key: f"{stock_by_id[key].symbol} · {stock_by_id[key].name}",
        )
        if selected_stock_id is not None:
            st.session_state[_STOCK_KEY] = selected_stock_id
    if selected_stock_id is not None:
        member = stock_by_id[selected_stock_id]
        history_evidence = history_by_symbol.get(member.symbol)
        chart_history = (
            history_evidence.history
            if history_evidence is not None
            else pd.DataFrame(columns=["close", "volume"])
        )
        chart = build_stock_chart_evidence(
            member.instrument_id,
            chart_history,
            as_of=requested_as_of,
        )
        score_evidence = scores_by_id.get(member.instrument_id)
        render_stock_detail(
            member,
            chart,
            scorecard=score_evidence.scorecard if score_evidence else None,
            score_state=score_evidence.state if score_evidence else "not_loaded",
            score_reason=score_evidence.reason if score_evidence else None,
            dark_mode=bool(st.session_state.get("dark_mode", False)),
            on_return=_clear_stock_selection,
        )
        return
    selected_rows = render_selectable_stock_tape(stock_frame, key=_PREFIX + "stock_tape")
    if selected_rows:
        selected_row = selected_rows[0]
        if 0 <= selected_row < len(active_members):
            st.session_state[_STOCK_KEY] = active_members[selected_row].instrument_id
            st.rerun()
        st.warning("The selected stock row is no longer available; choose a current member.")


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

    performance_mode = st.segmented_control(
        "Performance basis",
        options=["Absolute", "vs S&P 500"],
        default="Absolute",
        selection_mode="single",
    )
    sectors_by_name = dict(SECTOR_PROXIES)
    sector_names_by_id = {symbol: name for name, symbol in SECTOR_PROXIES}
    selection = _read_selection()
    # Before a membership catalog is needed, reconcile only the static sector/industry tree.
    static_selection = _reconcile_selection(
        ProgressiveSelection(
            sector_id=selection.sector_id,
            industry_id=selection.industry_id,
            instrument_id=None,
            catalog_fingerprint=selection.catalog_fingerprint,
            membership_date=selection.membership_date,
            observation_date=selection.observation_date,
        ),
        catalog_fingerprint=selection.catalog_fingerprint or "static-sector-industry-catalog",
        membership_date=selection.membership_date or date.min,
        observation_date=requested_as_of,
    )
    if static_selection.sector_id != selection.sector_id:
        selection = static_selection
        _store_hierarchy(selection)
    elif static_selection.industry_id != selection.industry_id:
        selection = static_selection
        _store_hierarchy(selection)

    selected_sector_id = st.selectbox(
        "Sector",
        options=tuple(sector_names_by_id),
        index=None,
        key=_SECTOR_KEY,
        on_change=_clear_industry_descendants,
        format_func=lambda value: sector_names_by_id[value],
        help="Choose a sector to replace the sector tape with its industry tape.",
    )

    if selected_sector_id is None:
        st.subheader("Sector performance")
        st.caption("Split-adjusted close returns over matching lookback periods")
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
        chart_histories = {
            sector.symbol: sector.history.loc[
                pd.DatetimeIndex(sector.history.index).date <= (observed or requested_as_of)
            ]
            for sector in discovery.sectors
        }
        sector_frame = attach_chart_series(
            sector_frame,
            identity_column="Proxy",
            history_by_id=chart_histories,
        )
        sector_frame["Chart status"] = sector_frame["Chart"].map(
            lambda series: "Available" if series else "Unavailable"
        )
        render_chart_tape(
            style_performance_table(sector_frame, dark_mode=dark_mode),
            key=f"sector_performance_table_{'dark' if dark_mode else 'light'}",
            column_config={
                "1 week": st.column_config.NumberColumn(format="%.2f%%"),
                "1 month": st.column_config.NumberColumn(format="%.2f%%"),
                "3 months": st.column_config.NumberColumn(format="%.2f%%"),
                "6 months": st.column_config.NumberColumn(format="%.2f%%"),
                "12 months": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )
    else:
        sector_name = sector_names_by_id.get(selected_sector_id)
        if sector_name is None:
            st.error("The selected sector is not in the current US sector catalog.")
            return
        sector_id = sectors_by_name.get(sector_name)
        if sector_id is None:
            st.error("The selected sector is not in the current US sector catalog.")
            return
        st.subheader("Industry momentum")
        industries = industry_momentum_frame(
            history,
            as_of=observed or requested_as_of,
            sectors=(sector_name,),
        )
        if industries.empty:
            st.info("No eligible industry data is available for this sector.")
            return
        industry_representations = {
            representation.industry_id: representation
            for representation in INDUSTRY_REPRESENTATIONS
            if representation.sector == sector_name
        }
        industry_histories = {
            representation.symbol: history[representation.symbol].loc[
                pd.DatetimeIndex(history[representation.symbol].index).date
                <= (observed or requested_as_of)
            ]
            for representation in INDUSTRY_REPRESENTATIONS
            if representation.sector == sector_name and representation.symbol in history
        }
        industries = attach_chart_series(
            industries,
            identity_column="Representation",
            history_by_id=industry_histories,
        )
        industries["Chart status"] = industries["Chart"].map(
            lambda series: "Available" if series else "Unavailable"
        )
        industry_ids = tuple(industry_representations)
        industry_id = st.selectbox(
            "Industry",
            options=industry_ids,
            index=None,
            key=_INDUSTRY_KEY,
            on_change=_clear_stock_selection,
            format_func=lambda value: industry_representations[value].industry_name,
            help="Choose an industry to replace the industry tape with all active member stocks.",
        )
        if industry_id is None:
            render_chart_tape(
                style_performance_table(industries, dark_mode=dark_mode),
                key=_PREFIX + "industry_tape",
                column_config={
                    "1 week": st.column_config.NumberColumn(format="%.2f%%"),
                    "1 month": st.column_config.NumberColumn(format="%.2f%%"),
                    "3 months": st.column_config.NumberColumn(format="%.2f%%"),
                    "6 months": st.column_config.NumberColumn(format="%.2f%%"),
                    "12 months": st.column_config.NumberColumn(format="%.2f%%"),
                },
            )
        else:
            representation = industry_representations[industry_id]
            _render_member_tape(
                settings=settings,
                requested_as_of=requested_as_of,
                sector_id=sector_id,
                industry_id=industry_id,
                industry_name=representation.industry_name,
                sector_name=sector_name,
                force_refresh=force_refresh,
            )

    if selected_sector_id is None:
        _render_experimental_universe_catalog(settings.experimental_universe_catalog)


if __name__ == "__main__":
    render_discovery()
