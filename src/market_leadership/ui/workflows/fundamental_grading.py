from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil

import streamlit as st

from market_leadership.bootstrap import load_selected_fundamentals
from market_leadership.config import Settings
from market_leadership.domain.fundamentals import FundamentalBundle, FundamentalRequest
from market_leadership.domain.stock_selection import (
    MembershipCatalog,
    MembershipEntry,
    SelectionContext,
)
from market_leadership.infrastructure.stock_membership import validate_live_access
from market_leadership.infrastructure.yfinance_fundamentals import FundamentalAcquisitionError
from market_leadership.ui.cache import cached_scorecard
from market_leadership.ui.components.fundamental_matrix import render_fundamental_matrix

PREFIX = "market_leadership.fundamentals."


@dataclass(frozen=True)
class LoadedPage:
    context: SelectionContext
    stock_ids: tuple[str, ...]
    page: int
    bundles: tuple[FundamentalBundle, ...]
    errors: tuple[str, ...] = ()


def render_fundamental_grading(
    settings: Settings,
    catalog: MembershipCatalog,
    context: SelectionContext,
    selected: tuple[MembershipEntry, ...],
) -> None:
    st.subheader("Fundamental Grading")
    if not selected:
        st.session_state.pop(PREFIX + "loaded", None)
        st.info("Select stocks in Industry Deep-Dive before loading fundamentals.")
        return
    try:
        if context.mode == "live":
            validate_live_access(catalog, settings)
        if context.mode != catalog.mode or context.catalog_fingerprint != catalog.fingerprint:
            raise ValueError("Membership context changed; reselect stocks")
        valid_ids = {
            entry.instrument_id
            for entry in catalog.entries
            if entry.active_on(catalog.observed_on)
            and entry.industry_id == context.industry_id
            and entry.sector_id == context.sector_id
        }
        if any(entry.instrument_id not in valid_ids for entry in selected):
            raise ValueError("Selected stock identities are not in the dated industry membership")
    except ValueError as error:
        st.session_state.pop(PREFIX + "loaded", None)
        st.error(f"Fundamentals blocked: {error}")
        return

    identities = tuple(entry.instrument_id for entry in selected)
    selection_token = (context, identities)
    if st.session_state.get(PREFIX + "selection") != selection_token:
        st.session_state[PREFIX + "page"] = 1
        st.session_state.pop(PREFIX + "loaded", None)
        st.session_state[PREFIX + "selection"] = selection_token
    page_count = ceil(len(selected) / 5)
    page = st.selectbox("Stock page", tuple(range(1, page_count + 1)), key=PREFIX + "page")
    displayed = selected[(page - 1) * 5 : page * 5]
    st.caption(
        f"{context.mode.upper()} | Membership {catalog.observed_on} | "
        f"Page {page}/{page_count} | {len(displayed)} displayed of {len(selected)} selected | "
        "Pages never load financial evidence automatically"
    )
    loaded_value = st.session_state.get(PREFIX + "loaded")
    loaded = loaded_value if isinstance(loaded_value, LoadedPage) else None
    if loaded is not None and (
        loaded.context != context or loaded.stock_ids != identities or loaded.page != page
    ):
        st.session_state.pop(PREFIX + "loaded", None)
        loaded = None
    load = st.button("Load fundamentals", key=PREFIX + "load")
    refresh = st.button("Refresh displayed stocks", key=PREFIX + "refresh")
    partial: list[FundamentalBundle] = []
    if load or refresh:
        st.session_state.pop(PREFIX + "loaded", None)
        bundles: list[FundamentalBundle] = []
        errors: list[str] = []
        with st.spinner("Loading displayed stocks' financial evidence..."):
            for entry in displayed:
                request = FundamentalRequest(
                    entry.symbol,
                    provider_id="fixture" if context.mode == "fixture" else "yfinance",
                    cutoff=catalog.observed_on,
                    retry_limit=settings.retry_limit,
                )
                try:
                    evidence = load_selected_fundamentals(request, refresh=refresh)
                    if evidence.symbol != entry.symbol or evidence.currency != entry.currency:
                        raise ValueError("Financial symbol/currency does not match membership")
                    bundles.append(evidence)
                except FundamentalAcquisitionError as error:
                    errors.append(f"{entry.symbol}: {error}")
                    if error.partial.currency == entry.currency:
                        partial.append(error.partial)
                except (OSError, ValueError) as error:
                    errors.append(f"{entry.symbol}: financial evidence unavailable; {error}")
        loaded = LoadedPage(context, identities, page, tuple(bundles), tuple(errors))
        st.session_state[PREFIX + "loaded"] = loaded
    if loaded is None:
        st.info("Click Load fundamentals for the displayed page. No financial request was made.")
        return
    for message in loaded.errors:
        st.error(message)
    now = datetime.now(UTC)
    for evidence in (*loaded.bundles, *partial):
        if context.mode == "live":
            if now - evidence.fetched_at >= timedelta(hours=1):
                st.warning(
                    f"{evidence.symbol}: evidence expired; click Load fundamentals or Refresh."
                )
                continue
            st.caption(
                f"{evidence.symbol}: one-hour freshness window, valid until "
                f"{(evidence.fetched_at + timedelta(hours=1)).isoformat()}"
            )
        render_fundamental_matrix(cached_scorecard(evidence))
