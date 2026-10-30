"""Database-backed progressive Discovery workflow."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from market_leadership.application.discover_sectors import (
    BENCHMARK,
    DiscoveryResult,
    discover_sectors_from_history,
    load_entity_representations,
)
from market_leadership.application.load_stock_history import (
    StockHistoryBatch,
    verified_primary_provider_symbols,
)
from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.score_industry import IndustryScoreResult, score_industry
from market_leadership.bootstrap import build_request_provider
from market_leadership.config import Settings, load_settings
from market_leadership.domain.sector_performance import (
    InsufficientHistoryError,
    PerformancePeriod,
    calculate_performance,
)
from market_leadership.domain.stock_chart import build_stock_chart_evidence
from market_leadership.domain.stock_selection import MembershipEntry
from market_leadership.infrastructure.region_database import (
    RegionDatabase,
    StockMembershipRecord,
)
from market_leadership.infrastructure.stock_membership import load_region_membership
from market_leadership.ui.cache import load_member_history
from market_leadership.ui.components.progressive_tape import (
    StockTapeRow,
    attach_chart_series,
    build_stock_tape_frame,
    render_chart_tape,
    render_selectable_stock_tape,
)
from market_leadership.ui.components.stock_detail import render_stock_detail

DISCOVERY_CACHE_SCHEMA_VERSION = 4
_PREFIX = "market_leadership.progressive_discovery."
_REGION_KEY = _PREFIX + "region"
_SECTOR_KEY = _PREFIX + "sector"
_INDUSTRY_KEY = _PREFIX + "industry"
_STOCK_KEY = _PREFIX + "stock"
_STOCK_PICKER_KEY = _PREFIX + "stock_picker"
_SCORES_KEY = _PREFIX + "scores"
_SCORE_CONTEXT_KEY = _PREFIX + "score_context"


def _clear_stock_selection() -> None:
    st.session_state.pop(_STOCK_KEY, None)
    st.session_state.pop(_STOCK_PICKER_KEY, None)


def _clear_industry_descendants() -> None:
    st.session_state.pop(_INDUSTRY_KEY, None)
    st.session_state.pop(_STOCK_KEY, None)
    st.session_state.pop(_STOCK_PICKER_KEY, None)
    st.session_state.pop(_SCORES_KEY, None)
    st.session_state.pop(_SCORE_CONTEXT_KEY, None)


def _clear_region_descendants() -> None:
    st.session_state.pop(_SECTOR_KEY, None)
    _clear_industry_descendants()


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
    representation_symbols: tuple[str, ...] = (),
    force_refresh: bool,
    retry_limit: int,
) -> tuple[DiscoveryResult, dict[str, pd.DataFrame]]:
    provider = build_request_provider("yfinance", source_cache_path, retry_limit=retry_limit)
    symbols = tuple(dict.fromkeys((BENCHMARK, *representation_symbols)))
    history = provider.fetch_daily_history(
        symbols,
        start=as_of - timedelta(days=550),
        end=as_of,
        force=force_refresh,
    )
    return _calculate_discovery(as_of, history, DISCOVERY_CACHE_SCHEMA_VERSION), history


def _membership_entry(member: StockMembershipRecord) -> MembershipEntry | None:
    listing = member.primary_listing
    if listing is None or member.resolution_state != "identified":
        return None
    return MembershipEntry(
        instrument_id=member.instrument_id,
        company_id=member.company_id or member.instrument_id,
        symbol=listing.provider_symbol or listing.symbol,
        name=member.name,
        exchange=listing.exchange_id,
        currency=listing.currency,
        sector_id=member.sector_id,
        sector_name=member.sector_name,
        industry_id=member.industry_id,
        industry_name=member.industry_name,
        effective_from=member.effective_from,
        effective_to=member.effective_to,
    )


def _stock_label(member: StockMembershipRecord) -> str:
    listing = member.primary_listing
    return f"{listing.symbol} · {member.name}" if listing else f"Unresolved · {member.name}"


def _render_member_tape(
    *,
    database: RegionDatabase,
    settings: Settings,
    region_id: str,
    classification_id: str,
    revision: str,
    requested_as_of: date,
    industry_id: str,
    force_refresh: bool,
    preview_start: date,
) -> None:
    membership_result = load_region_membership(
        database,
        region_id=region_id,
        classification_id=classification_id,
        industry_id=industry_id,
        as_of=requested_as_of,
    )
    if membership_result.state in ("missing_database", "invalid_database"):
        st.error(
            "Industry membership could not be read: "
            f"{membership_result.state.replace('_', ' ')} at {database.path}"
        )
        _clear_stock_selection()
        return
    members = membership_result.members

    if membership_result.state == "empty_membership":
        _clear_stock_selection()
        st.info("This reviewed industry has no active stock memberships for the selected date.")
        return

    provider_symbols = verified_primary_provider_symbols(members)
    history_batch: StockHistoryBatch | None = None
    history_by_symbol: dict[str, object] = {}
    if provider_symbols:
        try:
            history_batch = load_member_history(
                settings.source_cache_path,
                provider_symbols,
                requested_as_of,
                retry_limit=settings.retry_limit,
                force_refresh=force_refresh,
            )
            history_by_symbol = {item.symbol: item for item in history_batch.series}
        except (OSError, RuntimeError, ValueError) as error:
            st.error(f"Member price history could not be loaded: {error}")
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

    score_members = tuple(
        entry for member in members if (entry := _membership_entry(member)) is not None
    )
    membership_revision = membership_result.revision or revision
    score_context = (
        region_id,
        classification_id,
        industry_id,
        membership_revision,
        requested_as_of,
    )
    saved_scores = st.session_state.get(_SCORES_KEY)
    score_result = (
        saved_scores
        if st.session_state.get(_SCORE_CONTEXT_KEY) == score_context
        and isinstance(saved_scores, IndustryScoreResult)
        else None
    )
    if score_members:
        if st.button("Load peer scores", key=_PREFIX + "load_scores"):
            try:
                with st.spinner("Loading complete industry peer evidence..."):
                    score_result = score_industry(
                        score_members,
                        cutoff=requested_as_of,
                        refresh=force_refresh,
                    )
                st.session_state[_SCORES_KEY] = score_result
                st.session_state[_SCORE_CONTEXT_KEY] = score_context
            except (OSError, RuntimeError, ValueError) as error:
                st.error(f"Industry peer scores could not be loaded: {error}")
    else:
        st.caption("Peer scores are unavailable because no verified primary listing is present.")

    scores_by_id = (
        {item.instrument_id: item for item in score_result.stocks}
        if score_result is not None
        else {}
    )
    rows: list[StockTapeRow] = []
    symbol_by_id: dict[str, str] = {}
    for member in members:
        listing = member.primary_listing
        symbol = (listing.provider_symbol or listing.symbol) if listing else ""
        if symbol:
            symbol_by_id[member.instrument_id] = symbol
        evidence = history_by_symbol.get(symbol)
        history = getattr(evidence, "history", pd.DataFrame(columns=["close", "volume"]))
        state = (
            getattr(evidence, "price_state", "unavailable")
            if member.resolution_state == "identified" and listing is not None
            else "placeholder"
            if member.resolution_state == "placeholder"
            else "unavailable"
        )
        score = scores_by_id.get(member.instrument_id)
        rows.append(
            StockTapeRow(
                instrument_id=member.instrument_id,
                ticker=symbol or "Unresolved placeholder",
                name=member.name,
                history=history if isinstance(history, pd.DataFrame) else pd.DataFrame(),
                price_state=state,
                observed_on=getattr(evidence, "observed_on", None),
                price_reason=getattr(evidence, "reason", None),
                scorecard=score.scorecard if score else None,
                score_state=score.state
                if score
                else ("placeholder" if member.resolution_state == "placeholder" else "not_loaded"),
                score_reason=score.reason if score else None,
                market_cap=score.market_cap if score else None,
                resolution_state=member.resolution_state,
            )
        )

    stock_frame = build_stock_tape_frame(tuple(rows), preview_start=preview_start)
    stock_by_id = {member.instrument_id: member for member in members}
    selected_stock_id = st.session_state.get(_STOCK_KEY)
    if not isinstance(selected_stock_id, str) or selected_stock_id not in stock_by_id:
        selected_stock_id = st.selectbox(
            "Open stock detail",
            options=tuple(stock_by_id),
            index=None,
            key=_STOCK_PICKER_KEY,
            format_func=lambda key: _stock_label(stock_by_id[key]),
        )
        if selected_stock_id is not None:
            st.session_state[_STOCK_KEY] = selected_stock_id
    if selected_stock_id is not None:
        member = stock_by_id[selected_stock_id]
        listing = member.primary_listing
        if listing is None:
            st.title(f"Unresolved · {member.name}")
            st.caption(f"Instrument {member.instrument_id} · Industry {member.industry_name}")
            st.info("This stock has no verified listing; live market data was not requested.")
            if st.button("Back to Discovery", key=_PREFIX + "placeholder_back"):
                _clear_stock_selection()
                st.rerun()
            return
        entry = _membership_entry(member)
        if entry is None:
            st.error("This security has no eligible verified primary listing.")
            return
        symbol = symbol_by_id.get(member.instrument_id, entry.symbol)
        evidence = history_by_symbol.get(symbol)
        chart_history = getattr(evidence, "history", pd.DataFrame(columns=["close", "volume"]))
        chart = build_stock_chart_evidence(
            member.instrument_id,
            chart_history if isinstance(chart_history, pd.DataFrame) else pd.DataFrame(),
            as_of=requested_as_of,
        )
        score = scores_by_id.get(member.instrument_id)
        render_stock_detail(
            entry,
            chart,
            scorecard=score.scorecard if score else None,
            score_state=score.state if score else "not_loaded",
            score_reason=score.reason if score else None,
            dark_mode=bool(st.session_state.get("dark_mode", False)),
            on_return=_clear_stock_selection,
        )
        return

    selected_rows = render_selectable_stock_tape(stock_frame, key=_PREFIX + "stock_tape")
    if selected_rows:
        st.session_state[_STOCK_KEY] = members[selected_rows[0]].instrument_id
        st.rerun()


def _entity_performance(
    symbol: str | None,
    history: dict[str, pd.DataFrame],
    benchmark: pd.Series,
    *,
    as_of: date,
    performance_mode: str,
) -> dict[PerformancePeriod, float] | None:
    if not symbol or symbol not in history or history[symbol].empty or benchmark.empty:
        return None
    entity_history = history[symbol].loc[
        pd.DatetimeIndex(history[symbol].index).date <= as_of, "close"
    ]
    benchmark_history = benchmark.loc[pd.DatetimeIndex(benchmark.index).date <= as_of]
    try:
        result = calculate_performance(entity_history, benchmark_history, as_of=as_of)
        return result.absolute if performance_mode == "Absolute" else result.relative
    except InsufficientHistoryError:
        return None


def _build_entity_tape(
    *,
    entity_rows: tuple[tuple[str, str], ...],
    label: str,
    representation_by_id: dict[str, str],
    history: dict[str, pd.DataFrame],
    benchmark: pd.Series,
    requested_as_of: date,
    observed_as_of: date | None,
    performance_mode: str,
    preview_start: date | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    chart_history: dict[str, pd.DataFrame] = {}
    for entity_id, name in entity_rows:
        symbol = representation_by_id.get(entity_id)
        chart_key = symbol or f"unavailable-{entity_id}"
        if symbol and symbol in history:
            chart_history[symbol] = history[symbol].loc[
                pd.DatetimeIndex(history[symbol].index).date <= (observed_as_of or requested_as_of)
            ]
        metrics = _entity_performance(
            symbol,
            history,
            benchmark,
            as_of=observed_as_of or requested_as_of,
            performance_mode=performance_mode,
        )
        if symbol is None:
            status = "Chart representation unavailable"
        elif metrics is None:
            status = "Insufficient history"
        elif observed_as_of != latest_completed_us_session(requested_as_of):
            status = "Stale"
        else:
            status = "Current"
        rows.append(
            {
                "_chart_key": chart_key,
                label: name,
                "Ticker": symbol or "Unavailable",
                "1 week": metrics["1w"] * 100 if metrics else None,
                "1 month": metrics["1m"] * 100 if metrics else None,
                "3 months": metrics["3m"] * 100 if metrics else None,
                "6 months": metrics["6m"] * 100 if metrics else None,
                "12 months": metrics["12m"] * 100 if metrics else None,
                "Status": status,
            }
        )
    frame = pd.DataFrame(rows)
    frame = attach_chart_series(
        frame,
        identity_column="_chart_key",
        history_by_id=chart_history,
        preview_start=preview_start,
    )
    return frame.drop(columns=["_chart_key"])


def render_discovery(*, configure_page: bool = True) -> None:
    if configure_page:
        st.set_page_config(page_title="Discovery", page_icon="📊", layout="wide")
    st.title("Discovery")
    st.caption("Live US market evidence from yfinance. Historical outcomes are not forecasts.")

    database = RegionDatabase()
    if not database.is_initialized():
        if database.path.exists():
            st.error(f"Regional stock database is invalid: {database.path}")
        else:
            st.info(
                "Initialize and populate the regional stock database to enable industry filtering. "
                "Run `uv run python -m market_leadership.universe_admin init`, then validate and "
                "import a reviewed local file."
            )
        return
    regions = database.get_regions()
    if not regions:
        st.info(
            "The regional database is initialized but has no reviewed data. Validate and import "
            "a reviewed local universe file with `market_leadership.universe_admin import`."
        )
        return

    region_ids = tuple(region.region_id for region in regions)
    default_region = "US" if "US" in region_ids else region_ids[0]
    if st.session_state.get(_REGION_KEY) not in region_ids:
        st.session_state[_REGION_KEY] = default_region
    if len(region_ids) > 1:
        selected_region_id = st.selectbox(
            "Region",
            options=region_ids,
            key=_REGION_KEY,
            format_func=lambda key: next(
                region.name for region in regions if region.region_id == key
            ),
            on_change=_clear_region_descendants,
        )
    else:
        selected_region_id = next(iter(region_ids))
    region = next(record for record in regions if record.region_id == selected_region_id)
    st.caption(
        f"Coverage: {region.coverage_state.upper()} · {region.coverage_description} · "
        f"As of {region.coverage_as_of.isoformat()}"
    )
    market_today = datetime.now(ZoneInfo("America/New_York")).date()
    date_column, refresh_column = st.columns((3, 1))
    with date_column:
        requested_as_of = st.date_input("As of", value=market_today, max_value=market_today)
    with refresh_column:
        st.write("")
        force_refresh = st.button("Refresh data", use_container_width=True)
    classification_id = database.get_classification_id(
        selected_region_id, as_of=requested_as_of
    )
    if classification_id is None:
        st.info("No reviewed classification is available for this region and date.")
        return
    sectors = database.get_sectors(selected_region_id, classification_id, as_of=requested_as_of)
    if not sectors:
        st.info("This region has no active sectors in its reviewed classification.")
        return
    valid_sector_ids = tuple(sector.sector_id for sector in sectors)
    if st.session_state.get(_SECTOR_KEY) not in (*valid_sector_ids, None):
        _clear_industry_descendants()
        st.session_state.pop(_SECTOR_KEY, None)
        st.warning("The saved sector selection is no longer available and was cleared.")
    sector_names = {sector.sector_id: sector.name for sector in sectors}
    selected_sector_id = st.selectbox(
        "Sector",
        options=valid_sector_ids,
        index=None,
        key=_SECTOR_KEY,
        on_change=_clear_industry_descendants,
        format_func=lambda key: sector_names[key],
    )

    industries = (
        database.get_industries(
            selected_region_id,
            classification_id,
            selected_sector_id,
            as_of=requested_as_of,
        )
        if selected_sector_id
        else ()
    )
    selected_industry_id: str | None = None
    if selected_sector_id:
        industry_ids = tuple(industry.industry_id for industry in industries)
        if st.session_state.get(_INDUSTRY_KEY) not in (*industry_ids, None):
            _clear_stock_selection()
            st.session_state.pop(_INDUSTRY_KEY, None)
            st.warning("The saved industry selection is no longer available and was cleared.")
        if not industry_ids:
            st.subheader("Industry momentum")
            st.info("The selected sector has no active industries.")
            return
        industry_names = {industry.industry_id: industry.name for industry in industries}
        selected_industry_id = st.selectbox(
            "Industry",
            options=industry_ids,
            index=None,
            key=_INDUSTRY_KEY,
            on_change=_clear_stock_selection,
            format_func=lambda key: industry_names[key],
        )

    selected_entities = (
        tuple((industry.industry_id, industry.name) for industry in industries)
        if selected_sector_id
        else tuple((sector.sector_id, sector.name) for sector in sectors)
    )
    representations = load_entity_representations(
        database,
        region_id=selected_region_id,
        classification_id=classification_id,
        entity_type="sector" if selected_sector_id is None else "industry",
        entity_ids=tuple(entity_id for entity_id, _ in selected_entities),
        as_of=requested_as_of,
    )
    representation_by_id = {item.entity_id: item.symbol for item in representations}
    representation_symbols = (
        tuple(dict.fromkeys(representation_by_id.values()))
        if selected_industry_id is None
        else ()
    )
    settings = load_settings()
    try:
        with st.spinner("Loading yfinance market data..."):
            discovery, history = load_discovery(
                settings.source_cache_path,
                requested_as_of,
                representation_symbols=representation_symbols,
                force_refresh=force_refresh,
                retry_limit=settings.retry_limit,
            )
    except (OSError, RuntimeError, ValueError) as error:
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
    title_column, period_column, basis_column = st.columns((2, 2, 2))
    with title_column:
        st.subheader(
            "Sector performance"
            if selected_sector_id is None
            else "Industry momentum"
            if selected_industry_id is None
            else "Contained stocks"
        )
    with period_column:
        thumbnail_period = st.segmented_control(
            "Thumbnail period",
            options=["1w", "1m", "3m", "6m", "1y"],
            default="3m",
            selection_mode="single",
            key=_PREFIX + "thumbnail_period",
        )
    with basis_column:
        performance_mode = st.segmented_control(
            "Performance basis",
            options=["Absolute", "vs S&P 500"],
            default="Absolute",
            selection_mode="single",
            key=_PREFIX + "performance_basis",
        )
    period_offsets = {
        "1w": pd.DateOffset(weeks=1),
        "1m": pd.DateOffset(months=1),
        "3m": pd.DateOffset(months=3),
        "6m": pd.DateOffset(months=6),
        "1y": pd.DateOffset(years=1),
    }
    preview_start = (
        pd.Timestamp(requested_as_of) - period_offsets[thumbnail_period or "3m"]
    ).date()
    if selected_sector_id is None:
        benchmark_history = history.get(BENCHMARK, pd.DataFrame(columns=["close"]))
        frame = _build_entity_tape(
            entity_rows=selected_entities,
            label="Sector",
            representation_by_id=representation_by_id,
            history=history,
            benchmark=benchmark_history.get("close", pd.Series(dtype="float64")),
            requested_as_of=requested_as_of,
            observed_as_of=observed,
            performance_mode=performance_mode or "Absolute",
            preview_start=preview_start,
        )
        render_chart_tape(frame, key=_PREFIX + "sector_tape")
    elif selected_industry_id is None:
        benchmark_history = history.get(BENCHMARK, pd.DataFrame(columns=["close"]))
        frame = _build_entity_tape(
            entity_rows=selected_entities,
            label="Industry",
            representation_by_id=representation_by_id,
            history=history,
            benchmark=benchmark_history.get("close", pd.Series(dtype="float64")),
            requested_as_of=requested_as_of,
            observed_as_of=observed,
            performance_mode=performance_mode or "Absolute",
            preview_start=preview_start,
        )
        render_chart_tape(frame, key=_PREFIX + "industry_tape")
    else:
        _render_member_tape(
            database=database,
            settings=settings,
            region_id=selected_region_id,
            classification_id=classification_id,
            revision=database.get_revision(),
            requested_as_of=requested_as_of,
            industry_id=selected_industry_id,
            force_refresh=force_refresh,
            preview_start=preview_start,
        )


if __name__ == "__main__":
    render_discovery()
