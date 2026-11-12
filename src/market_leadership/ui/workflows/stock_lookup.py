"""Dedicated retained-stock lookup workflow."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from market_data.catalog import CatalogSnapshot
from market_data.domain.catalog import CatalogMember, Listing
from market_data.domain.stock_chart import (
    build_stock_chart_evidence,
    stock_chart_lookback_days,
)
from market_data.domain.stock_selection import StockIdentitySelection
from market_leadership.config import Settings, load_settings
from market_leadership.ui.cache import load_catalog_snapshot
from market_leadership.ui.components.company_evidence import render_company_evidence_controls
from market_leadership.ui.components.stock_detail import render_stock_detail
from market_leadership.ui.navigation import clear_catalog_selections, preserve_catalog_controls
from market_leadership.ui.theme import apply_theme

_PREFIX = "market_leadership.stock_lookup."
_REGION_KEY = _PREFIX + "region"
_AS_OF_KEY = _PREFIX + "as_of"
_QUERY_KEY = _PREFIX + "lookup_query"
_INSTRUMENT_KEY = _PREFIX + "lookup_instrument"
_LISTING_KEY = _PREFIX + "lookup_listing"
_OPEN_KEY = _PREFIX + "lookup_open"
_CONTEXT_KEY = _PREFIX + "lookup_context"
_HISTORY_KEY = _PREFIX + "lookup_history"
_HISTORY_CONTEXT_KEY = _PREFIX + "lookup_history_context"
_HISTORY_LOOKBACK_KEY = _PREFIX + "lookup_history_lookback"
_DETAIL_WIDGET_PREFIX = _PREFIX + "detail."


def _clear_lookup_selection() -> None:
    for key in (
        _INSTRUMENT_KEY,
        _LISTING_KEY,
        _OPEN_KEY,
        _CONTEXT_KEY,
        _HISTORY_KEY,
        _HISTORY_CONTEXT_KEY,
    ):
        st.session_state.pop(key, None)


def _listing_lookup_label(listing: Listing) -> str:
    return (
        f"{listing.provider_symbol} · {listing.exchange} · {listing.currency} · "
        f"{listing.listing_id}"
    )


def _render_lookup(
    snapshot: CatalogSnapshot,
    *,
    settings: Settings,
    region_id: str,
    as_of: date,
) -> None:
    query = st.text_input("Search retained stock identities", key=_QUERY_KEY).strip()
    if not query:
        _clear_lookup_selection()
        return

    matches: tuple[CatalogMember, ...] = snapshot.lookup_instruments(region_id, query)
    if not matches:
        _clear_lookup_selection()
        st.info("No retained stock identity matches this search.")
        return

    instrument_ids = tuple(item.instrument.instrument_id for item in matches)
    if st.session_state.get(_INSTRUMENT_KEY) not in (*instrument_ids, None):
        _clear_lookup_selection()
    by_id = {item.instrument.instrument_id: item for item in matches}
    selected_id = st.selectbox(
        "Matching stock identities",
        options=instrument_ids,
        index=None,
        key=_INSTRUMENT_KEY,
        format_func=lambda key: (
            f"{by_id[key].instrument.name} · {key} · "
            f"{len(by_id[key].listings)} listing(s)"
        ),
    )
    if selected_id is None:
        if len(matches) > 1:
            st.info("Choose one exact stock identity before opening its detail.")
        return

    member = by_id[selected_id]
    listings = tuple(
        listing
        for listing in member.listings
        if listing.instrument_type == "stock" and listing.active_on(as_of)
    )
    listing_ids = tuple(listing.listing_id for listing in listings)
    if st.session_state.get(_LISTING_KEY) not in (*listing_ids, None):
        st.session_state.pop(_LISTING_KEY, None)
    listing_by_id = {listing.listing_id: listing for listing in listings}
    listing_id = (
        st.selectbox(
            "Active verified listing",
            options=listing_ids,
            index=None,
            key=_LISTING_KEY,
            format_func=lambda key: _listing_lookup_label(listing_by_id[key]),
        )
        if listing_ids
        else None
    )
    if not listing_ids:
        st.info("No verified listing is active on this date; no remote data will be requested.")

    detail_context = (
        region_id,
        member.instrument.instrument_id,
        listing_id,
        as_of,
        snapshot.catalog_revision,
    )
    if st.session_state.get(_CONTEXT_KEY) != detail_context:
        st.session_state.pop(_OPEN_KEY, None)
        st.session_state.pop(_HISTORY_KEY, None)
        st.session_state.pop(_HISTORY_CONTEXT_KEY, None)
        st.session_state.pop(_HISTORY_LOOKBACK_KEY, None)
        st.session_state.pop(_DETAIL_WIDGET_PREFIX + "chart_range", None)
        st.session_state.pop(_DETAIL_WIDGET_PREFIX + "chart_range_context", None)
        st.session_state[_CONTEXT_KEY] = detail_context
    if st.button("Open stock detail", key=_PREFIX + "open_lookup"):
        if listings and listing_id is None:
            st.info("Select the exact listing to open its detail.")
            return
        st.session_state[_OPEN_KEY] = True
    if st.session_state.get(_OPEN_KEY) is not True:
        return

    listing = listing_by_id[listing_id] if listing_id is not None else None
    selection = StockIdentitySelection(
        instrument_id=member.instrument.instrument_id,
        company_id=member.instrument.company_id,
        region_id=member.instrument.region_id,
        name=member.instrument.name,
        listing_id=listing.listing_id if listing else None,
        symbol=listing.provider_symbol if listing else None,
        exchange=listing.exchange if listing else None,
        currency=listing.currency if listing else None,
    )
    history_context = (detail_context, listing.listing_id if listing else None)
    if st.session_state.get(_HISTORY_CONTEXT_KEY) != history_context:
        st.session_state.pop(_HISTORY_KEY, None)
        st.session_state.pop(_HISTORY_LOOKBACK_KEY, None)
        st.session_state[_HISTORY_CONTEXT_KEY] = history_context
    history_requested = st.session_state.get(_HISTORY_KEY) == history_context
    load_history = listing is not None and st.button(
        "Load selected history", key=_PREFIX + "load_lookup_history"
    )
    refresh_history = listing is not None and st.button(
        "Refresh selected history", key=_PREFIX + "refresh_lookup_history"
    )
    if listing is not None and (load_history or refresh_history):
        st.session_state[_HISTORY_KEY] = history_context
        history_requested = True

    history_result = None
    if listing is not None and history_requested:
        try:
            from market_leadership.bootstrap import load_selected_stock_history

            chart_range = st.session_state.get(
                _DETAIL_WIDGET_PREFIX + "chart_range", "6m"
            )
            requested_lookback_days = stock_chart_lookback_days(as_of, chart_range)
            if refresh_history:
                lookback_days = requested_lookback_days
            else:
                lookback_days = max(
                    requested_lookback_days,
                    st.session_state.get(_HISTORY_LOOKBACK_KEY, 0),
                )
            st.session_state[_HISTORY_LOOKBACK_KEY] = lookback_days
            history_result = load_selected_stock_history(
                snapshot,
                region_id=region_id,
                instrument_id=selection.instrument_id,
                listing_id=listing.listing_id,
                as_of=as_of,
                require_primary=False,
                lookback_days=lookback_days,
                refresh=refresh_history,
            )
        except (OSError, RuntimeError, ValueError) as error:
            st.error(f"Selected listing history could not be loaded: {error}")
    history = (
        history_result.series[0].history
        if history_result is not None and history_result.series
        else pd.DataFrame(columns=["close", "volume"])
    )
    chart = build_stock_chart_evidence(selection.instrument_id, history, as_of=as_of)
    if history_result is not None and history_result.series:
        item = history_result.series[0]
        st.caption(f"Selected listing history: {item.state}")
        if item.reason:
            st.info(item.reason)
        for start, end in item.unverifiable_intervals:
            st.warning(
                f"History continuity unavailable from {start.isoformat()} through "
                f"{end.isoformat()}."
            )
    elif listing is not None:
        st.caption("No price request has been made; use Load selected history to continue.")

    if listing is not None:
        (
            financial_evidence,
            research_evidence,
            on_load_financial,
            on_load_research,
        ) = render_company_evidence_controls(
            snapshot,
            settings,
            instrument_id=selection.instrument_id,
            listing_id=listing.listing_id,
            region_id=region_id,
            as_of=as_of,
            state_prefix=_PREFIX,
        )
    else:
        financial_evidence = None
        research_evidence = None
        on_load_financial = None
        on_load_research = None

    render_stock_detail(
        selection,
        chart,
        scorecard=None,
        score_state="not_loaded",
        score_reason="Peer scores require a reviewed industry membership.",
        dark_mode=bool(st.session_state.get("dark_mode", False)),
        on_return=_clear_lookup_selection,
        financial_evidence=financial_evidence,
        research_evidence=research_evidence,
        on_load_financial=on_load_financial,
        on_load_research=on_load_research,
        widget_key_prefix=_DETAIL_WIDGET_PREFIX,
        back_button_label="Back to Find a stock",
    )


def render_stock_lookup(
    *,
    configure_page: bool = True,
    settings: Settings | None = None,
    snapshot: CatalogSnapshot | None = None,
) -> None:
    if snapshot is None:
        preserve_catalog_controls()
    if configure_page:
        st.set_page_config(page_title="Find a stock", page_icon=":material/search:", layout="wide")
    st.title("Find a stock")
    apply_theme()

    settings = settings or load_settings()
    if snapshot is None:
        try:
            snapshot = load_catalog_snapshot(settings.catalog_manifest_path)
        except (OSError, RuntimeError, ValueError) as error:
            clear_catalog_selections()
            st.error(f"Active catalog is unavailable or invalid: {error}")
            return

    regions = tuple(region for region in snapshot.release.regions if region.status == "active")
    if not regions:
        _clear_lookup_selection()
        st.info("The catalog has no active reviewed regions.")
        return

    region_ids = tuple(region.region_id for region in regions)
    default_region = "US" if "US" in region_ids else region_ids[0]
    previous_revision = st.session_state.get(_PREFIX + "catalog_revision")
    if previous_revision != snapshot.catalog_revision:
        _clear_lookup_selection()
        st.session_state[_PREFIX + "catalog_revision"] = snapshot.catalog_revision
    if st.session_state.get(_REGION_KEY) not in region_ids:
        _clear_lookup_selection()
        st.session_state[_REGION_KEY] = default_region
    selected_region_id = st.selectbox(
        "Region",
        options=region_ids,
        key=_REGION_KEY,
        format_func=lambda key: next(region.name for region in regions if region.region_id == key),
        on_change=_clear_lookup_selection,
    )

    market_today = datetime.now(ZoneInfo("America/New_York")).date()
    if _AS_OF_KEY not in st.session_state:
        st.session_state[_AS_OF_KEY] = market_today
    requested_as_of = (
        st.date_input(
            "As of",
            value=None,
            max_value=market_today,
            key=_AS_OF_KEY,
            on_change=_clear_lookup_selection,
        )
        or market_today
    )
    _render_lookup(
        snapshot,
        settings=settings,
        region_id=selected_region_id,
        as_of=requested_as_of,
    )


if __name__ == "__main__":
    render_stock_lookup()
