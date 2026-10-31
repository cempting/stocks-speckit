"""File-catalog-backed progressive Discovery workflow."""

import json
from collections.abc import Callable
from dataclasses import asdict
from datetime import date, datetime, timedelta
from hashlib import sha256
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from market_leadership.application.discover_sectors import (
    DiscoveryResult,
    discover_sectors_from_history,
    discovery_symbols,
    load_entity_representations,
    load_industry_representations,
)
from market_leadership.application.industry_representations import snapshot_representation_worklist
from market_leadership.application.load_stock_history import (
    StockHistoryBatch,
)
from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.score_industry import IndustryScoreResult
from market_leadership.config import Settings, load_settings
from market_leadership.domain.catalog import CatalogError, Scope, StockRow
from market_leadership.domain.industry_representations import (
    ReviewedRepresentation,
    representation_performance,
)
from market_leadership.domain.sector_performance import (
    InsufficientHistoryError,
    PerformancePeriod,
    calculate_absolute_performance,
    calculate_performance,
)
from market_leadership.domain.stock_chart import build_stock_chart_evidence
from market_leadership.infrastructure.catalog_files import CatalogSnapshot
from market_leadership.infrastructure.stock_membership import (
    load_region_membership,
    membership_entry,
)
from market_leadership.ui.cache import load_catalog_snapshot, load_member_history
from market_leadership.ui.components.progressive_tape import (
    StockTapeRow,
    attach_chart_series,
    build_stock_tape_frame,
    render_chart_tape,
    render_selectable_stock_tape,
)
from market_leadership.ui.components.stock_detail import render_stock_detail
from market_leadership.ui.navigation import clear_catalog_selections, preserve_catalog_controls

DISCOVERY_CACHE_SCHEMA_VERSION = 6
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


def _clear_member_context() -> None:
    _clear_stock_selection()
    st.session_state.pop(_SCORES_KEY, None)
    st.session_state.pop(_SCORE_CONTEXT_KEY, None)


def _clear_region_descendants() -> None:
    st.session_state.pop(_SECTOR_KEY, None)
    _clear_industry_descendants()


def _select_sector_from_tape(sector_id: str) -> None:
    st.session_state[_SECTOR_KEY] = sector_id
    _clear_industry_descendants()


def _select_industry_from_tape(industry_id: str) -> None:
    st.session_state[_INDUSTRY_KEY] = industry_id
    _clear_member_context()


def _render_breadcrumbs(
    *,
    region_id: str,
    sector_name: str | None,
    industry_name: str | None = None,
    stock_label: str | None = None,
) -> None:
    crumbs: list[tuple[str, str, Callable[[], None] | None]] = [
        (
            f"{region_id} sectors",
            "sectors",
            _clear_region_descendants if sector_name is not None else None,
        )
    ]
    if sector_name is not None:
        crumbs.append(
            (
                sector_name,
                "sector",
                _clear_industry_descendants if industry_name is not None else None,
            )
        )
    if industry_name is not None:
        crumbs.append(
            (industry_name, "industry", _clear_stock_selection if stock_label is not None else None)
        )
    if stock_label is not None:
        crumbs.append((stock_label, "stock", None))
    with st.container(horizontal=True, vertical_alignment="center", key=_PREFIX + "breadcrumbs"):
        for index, (label, key, on_return) in enumerate(crumbs):
            if index:
                st.caption(">")
            if on_return is None:
                st.caption(label)
            else:
                st.button(
                    label,
                    key=_PREFIX + "breadcrumb_" + key,
                    help=f"Return to {label}",
                    on_click=on_return,
                )


def _discovery_catalog_fingerprint(
    snapshot: CatalogSnapshot, scope: Scope, as_of: date, sector_ids: tuple[str, ...]
) -> str:
    worklist = tuple(
        item
        for item in snapshot_representation_worklist(snapshot, scope=scope, as_of=as_of)
        if item.node_type == "sector" and item.node_id in sector_ids
    )
    mappings = tuple(
        item
        for item in snapshot.representations
        if item.scope == scope and item.node_id in sector_ids and item.period.active_on(as_of)
    )
    listing_ids = {item.listing_id for item in mappings}
    listing_ids.update(
        constituent.listing_id
        for item in worklist
        if item.representation
        for constituent in item.representation.constituents
    )
    benchmarks: dict[str, object] = {}
    for purpose in ("sp500_comparison", "market_sentiment"):
        try:
            listing = snapshot.benchmark(scope.region_id, purpose, as_of)
            listing_ids.add(listing.listing_id)
            benchmarks[purpose] = asdict(listing)
        except CatalogError as error:
            benchmarks[purpose] = str(error)
    listings = {
        listing.listing_id: asdict(listing)
        for listing in (
            *snapshot.listings,
            *(row.listing for row in snapshot.stocks if row.listing is not None),
            *(item.listing for item in snapshot.inventory),
        )
        if listing.listing_id in listing_ids
    }
    payload = {
        "scope": asdict(scope),
        "as_of": as_of,
        "worklist": tuple(asdict(item) for item in worklist),
        "mappings": tuple(asdict(item) for item in mappings),
        "listings": listings,
        "benchmarks": benchmarks,
    }
    return sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


@st.cache_data(show_spinner=False)
def _calculate_discovery(
    as_of: date,
    history: dict[str, pd.DataFrame],
    cache_schema_version: int,
    catalog_fingerprint: str,
    _snapshot: CatalogSnapshot,
    scope: Scope,
    sector_ids: tuple[str, ...],
) -> DiscoveryResult:
    del cache_schema_version, catalog_fingerprint
    return discover_sectors_from_history(
        "yfinance", history, snapshot=_snapshot, scope=scope, as_of=as_of, sector_ids=sector_ids
    )


def load_discovery(
    source_cache_path: str,
    as_of: date,
    *,
    snapshot: CatalogSnapshot,
    scope: Scope,
    sector_ids: tuple[str, ...] = (),
    representation_symbols: tuple[str, ...] = (),
    force_refresh: bool,
    retry_limit: int,
) -> tuple[DiscoveryResult, dict[str, pd.DataFrame]]:
    from market_leadership.bootstrap import build_request_provider

    symbols = tuple(
        sorted(
            set(
                (
                    *discovery_symbols(snapshot, scope=scope, as_of=as_of, sector_ids=sector_ids),
                    *representation_symbols,
                )
            )
        )
    )
    provider = (
        build_request_provider("yfinance", source_cache_path, retry_limit=retry_limit)
        if symbols
        else None
    )
    history = (
        provider.fetch_daily_history(
            symbols,
            start=as_of - timedelta(days=550),
            end=as_of,
            force=force_refresh,
        )
        if provider is not None
        else {}
    )
    calculation_symbols = discovery_symbols(
        snapshot, scope=scope, as_of=as_of, sector_ids=sector_ids
    )
    return _calculate_discovery(
        as_of,
        {symbol: history[symbol] for symbol in calculation_symbols if symbol in history},
        DISCOVERY_CACHE_SCHEMA_VERSION,
        _discovery_catalog_fingerprint(snapshot, scope, as_of, sector_ids),
        snapshot,
        scope,
        sector_ids,
    ), history


def _stock_label(member: StockRow, as_of: date) -> str:
    symbol = member.provider_symbol_on(as_of)
    return f"{symbol} · {member.name}" if symbol else f"Unresolved · {member.name}"


def _render_member_tape(
    *,
    snapshot: CatalogSnapshot,
    scope: Scope,
    settings: Settings,
    region_id: str,
    revision: str,
    requested_as_of: date,
    industry_id: str,
    force_refresh: bool,
    preview_start: date,
) -> None:
    membership_result = load_region_membership(
        snapshot,
        scope=scope,
        industry_id=industry_id,
        as_of=requested_as_of,
    )
    members = membership_result.members

    if membership_result.state == "empty_membership":
        _clear_stock_selection()
        st.info("This reviewed industry has no active stock memberships for the selected date.")
        return

    provider_symbols = snapshot.provider_symbols(scope, industry_id, requested_as_of)
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
        entry
        for member in members
        if (entry := membership_entry(snapshot, member, requested_as_of)) is not None
    )
    membership_revision = membership_result.revision or revision
    score_context = (
        region_id,
        scope,
        industry_id,
        membership_revision,
        requested_as_of,
    )
    saved_scores = st.session_state.get(_SCORES_KEY)
    if st.session_state.get(_SCORE_CONTEXT_KEY) != score_context:
        st.session_state.pop(_SCORES_KEY, None)
        st.session_state.pop(_SCORE_CONTEXT_KEY, None)
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
                    from market_leadership.application.score_industry import score_industry

                    score_result = score_industry(
                        score_members,
                        cutoff=requested_as_of,
                        refresh=force_refresh,
                        cohort_fingerprint=membership_revision,
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
        symbol = member.provider_symbol_on(requested_as_of) or ""
        if symbol:
            symbol_by_id[member.instrument_id] = symbol
        evidence = history_by_symbol.get(symbol)
        history = getattr(evidence, "history", pd.DataFrame(columns=["close", "volume"]))
        state = (
            getattr(evidence, "price_state", "unavailable")
            if symbol
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
    if (
        selected_stock_id is not None and selected_stock_id not in stock_by_id
    ) or st.session_state.get(_STOCK_PICKER_KEY) not in (*stock_by_id, None):
        _clear_stock_selection()
        selected_stock_id = None
    if not isinstance(selected_stock_id, str) or selected_stock_id not in stock_by_id:
        selected_stock_id = st.selectbox(
            "Open stock detail",
            options=tuple(stock_by_id),
            index=None,
            key=_STOCK_PICKER_KEY,
            format_func=lambda key: _stock_label(stock_by_id[key], requested_as_of),
        )
        if selected_stock_id is not None:
            st.session_state[_STOCK_KEY] = selected_stock_id
    if selected_stock_id is not None:
        member = stock_by_id[selected_stock_id]
        if member.provider_symbol_on(requested_as_of) is None:
            st.title(f"Unresolved · {member.name}")
            st.caption(f"Instrument {member.instrument_id} · Industry {member.industry_id}")
            st.info("This stock has no verified listing; live market data was not requested.")
            if st.button("Back to Discovery", key=_PREFIX + "placeholder_back"):
                _clear_stock_selection()
                st.rerun()
            return
        entry = membership_entry(snapshot, member, requested_as_of)
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
    reviewed_by_id: dict[str, ReviewedRepresentation] | None = None,
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
        metrics = (
            _entity_performance(
                symbol,
                history,
                benchmark,
                as_of=observed_as_of or requested_as_of,
                performance_mode=performance_mode,
            )
            if reviewed_by_id is None
            else None
        )
        representation = (reviewed_by_id or {}).get(entity_id)
        evidence_reason: str | None = None
        if reviewed_by_id is not None:
            metrics = None
            if representation is not None and not representation.invalid_reason:
                try:
                    metrics = representation_performance(
                        representation,
                        history,
                        as_of=observed_as_of or requested_as_of,
                    )
                    if performance_mode != "Absolute":
                        benchmark_metrics = calculate_absolute_performance(
                            benchmark,
                            as_of=observed_as_of or requested_as_of,
                        )
                        metrics = {
                            period: value - benchmark_metrics[period]
                            for period, value in metrics.items()
                        }
                except ValueError as error:
                    evidence_reason = str(error)
            if representation is not None and representation.invalid_reason:
                evidence_reason = representation.invalid_reason
        covered = representation is not None if reviewed_by_id is not None else symbol is not None
        if not covered:
            status = "Not covered"
        elif representation is not None and representation.invalid_reason:
            status = f"Invalid evidence: {evidence_reason}"
        elif metrics is None:
            status = "Insufficient evidence" + (f": {evidence_reason}" if evidence_reason else "")
        elif observed_as_of != latest_completed_us_session(requested_as_of):
            status = "Stale"
        else:
            status = "Current"
        row: dict[str, object] = {
            "_chart_key": chart_key,
            label: name,
            "ETF" if label == "Industry" else "Ticker": symbol
            or ("Not covered" if label == "Industry" else "Unavailable"),
            "1 week": metrics["1w"] * 100 if metrics else None,
            "1 month": metrics["1m"] * 100 if metrics else None,
            "3 months": metrics["3m"] * 100 if metrics else None,
            "6 months": metrics["6m"] * 100 if metrics else None,
            "12 months": metrics["12m"] * 100 if metrics else None,
            "Status": status,
        }
        if label == "Industry":
            row["Representation"] = (
                representation.name if representation else symbol or "Not covered"
            )
            row["Representation type"] = (
                "ETF"
                if (representation and representation.kind == "etf") or symbol
                else "Stock basket alternative"
                if representation
                else "Not covered"
            )
            if representation and representation.kind == "basket":
                row["ETF"] = "Not an ETF"
        row["Node ID"] = entity_id
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame = attach_chart_series(
        frame,
        identity_column="_chart_key",
        history_by_id=chart_history,
        preview_start=preview_start,
    )
    return frame.drop(columns=["_chart_key"])


def render_discovery(
    *,
    configure_page: bool = True,
    settings: Settings | None = None,
    snapshot: CatalogSnapshot | None = None,
) -> None:
    if snapshot is None:
        preserve_catalog_controls()
    if configure_page:
        st.set_page_config(page_title="Discovery", page_icon="📊", layout="wide")
    st.title("Discovery")
    st.caption("Live US market evidence from yfinance. Historical outcomes are not forecasts.")

    settings = settings or load_settings()
    if snapshot is None:
        try:
            snapshot = load_catalog_snapshot(settings.catalog_manifest_path)
        except (CatalogError, OSError, ValueError) as error:
            clear_catalog_selections()
            st.error(f"Active catalog is unavailable or invalid: {error}")
            return
    regions = tuple(region for region in snapshot.release.regions if region.status == "active")
    if not regions:
        _clear_region_descendants()
        st.info("The catalog has no active reviewed regions.")
        return

    region_ids = tuple(region.region_id for region in regions)
    default_region = "US" if "US" in region_ids else region_ids[0]
    if st.session_state.get(_REGION_KEY) not in region_ids:
        _clear_region_descendants()
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
        date_key = _PREFIX + "as_of"
        if date_key not in st.session_state:
            st.session_state[date_key] = market_today
        requested_as_of = (
            st.date_input("As of", value=None, max_value=market_today, key=date_key) or market_today
        )
    with refresh_column:
        st.write("")
        force_refresh = st.button("Refresh data", use_container_width=True)
    try:
        scope = snapshot.scope_on(selected_region_id, requested_as_of)
        nodes = snapshot.active_nodes(scope, requested_as_of)
    except CatalogError as error:
        _clear_region_descendants()
        st.info(f"No reviewed classification is available for this region and date: {error}")
        return
    sectors = tuple(node for node in nodes if node.node_type == "sector")
    if not sectors:
        _clear_region_descendants()
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

    industries = tuple(
        node
        for node in nodes
        if node.node_type in ("industry", "sub_industry") and node.sector_id == selected_sector_id
    )
    industry_names = {industry.node_id: industry.name for industry in industries}
    selected_industry_id: str | None = None
    if selected_sector_id:
        industry_ids = tuple(industry.node_id for industry in industries)
        if st.session_state.get(_INDUSTRY_KEY) not in (*industry_ids, None):
            _clear_industry_descendants()
            st.warning("The saved industry selection is no longer available and was cleared.")
        if not industry_ids:
            _render_breadcrumbs(
                region_id=selected_region_id,
                sector_name=sector_names[selected_sector_id],
            )
            st.subheader("Industry momentum")
            st.info("The selected sector has no active industries.")
            return
        selected_industry_id = st.selectbox(
            "Industry",
            options=industry_ids,
            index=None,
            key=_INDUSTRY_KEY,
            on_change=_clear_member_context,
            format_func=lambda key: industry_names[key],
        )

    stock_label = None
    if selected_industry_id is not None:
        stock_id = st.session_state.get(_STOCK_KEY) or st.session_state.get(_STOCK_PICKER_KEY)
        if isinstance(stock_id, str):
            member = next(
                (
                    member
                    for member in snapshot.members(scope, selected_industry_id, requested_as_of)
                    if member.instrument_id == stock_id
                ),
                None,
            )
            if member is not None:
                stock_label = _stock_label(member, requested_as_of)
    _render_breadcrumbs(
        region_id=selected_region_id,
        sector_name=sector_names[selected_sector_id] if selected_sector_id is not None else None,
        industry_name=industry_names[selected_industry_id]
        if selected_industry_id is not None
        else None,
        stock_label=stock_label,
    )

    selected_entities = (
        tuple((industry.node_id, industry.name) for industry in industries)
        if selected_sector_id
        else tuple((sector.sector_id, sector.name) for sector in sectors)
    )
    representations = (
        load_entity_representations(
            snapshot,
            scope=scope,
            entity_type="sector",
            entity_ids=tuple(entity_id for entity_id, _ in selected_entities),
            as_of=requested_as_of,
        )
        if selected_sector_id is None
        else ()
    )
    reviewed_representations = (
        load_industry_representations(
            snapshot,
            scope=scope,
            entity_ids=tuple(entity_id for entity_id, _ in selected_entities),
            as_of=requested_as_of,
        )
        if selected_sector_id is not None
        else ()
    )
    visible_representations = (*representations, *reviewed_representations)
    reviewed_by_id = {item.node_id: item for item in visible_representations}
    representation_by_id = {
        item.node_id: item.symbol
        for item in visible_representations
        if item.symbol is not None and not item.invalid_reason
    }
    representation_symbols = (
        tuple(
            dict.fromkeys(
                (
                    *representation_by_id.values(),
                    *(
                        symbol
                        for item in visible_representations
                        if not item.invalid_reason
                        for symbol in item.symbols
                    ),
                )
            )
        )
        if selected_industry_id is None
        else ()
    )
    for purpose in ("sp500_comparison", "market_sentiment"):
        try:
            snapshot.benchmark(selected_region_id, purpose, requested_as_of)
        except CatalogError as error:
            st.warning(f"Missing catalog benchmark for {purpose}: {error}")
    try:
        with st.spinner("Loading yfinance market data..."):
            discovery, history = load_discovery(
                settings.source_cache_path,
                requested_as_of,
                snapshot=snapshot,
                scope=scope,
                sector_ids=tuple(entity_id for entity_id, _ in selected_entities)
                if selected_sector_id is None
                else (),
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
        benchmark_history = history.get(
            discovery.comparison_symbol or "", pd.DataFrame(columns=["close"])
        )
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
            reviewed_by_id=reviewed_by_id,
        )
        render_chart_tape(frame, key=_PREFIX + "sector_tape", on_select=_select_sector_from_tape)
    elif selected_industry_id is None:
        st.caption(
            "Basket returns are weighted constituent returns. Basket price and volume charts "
            "are unavailable because a basket is not a traded ETF."
        )
        benchmark_history = history.get(
            discovery.comparison_symbol or "", pd.DataFrame(columns=["close"])
        )
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
            reviewed_by_id=reviewed_by_id,
        )
        render_chart_tape(
            frame, key=_PREFIX + "industry_tape", on_select=_select_industry_from_tape
        )
    else:
        _render_member_tape(
            snapshot=snapshot,
            scope=scope,
            settings=settings,
            region_id=selected_region_id,
            revision=snapshot.catalog_revision,
            requested_as_of=requested_as_of,
            industry_id=selected_industry_id,
            force_refresh=force_refresh,
            preview_start=preview_start,
        )


if __name__ == "__main__":
    render_discovery()
