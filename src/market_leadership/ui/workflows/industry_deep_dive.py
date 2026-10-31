"""Industry Deep-Dive selection backed by the active reviewed file catalog."""

from datetime import date
from typing import cast

import pandas as pd
import streamlit as st

from market_leadership.config import Settings, load_settings
from market_leadership.domain.catalog import CatalogError
from market_leadership.domain.stock_selection import (
    MembershipEntry,
    SelectionContext,
    reconcile_selection,
)
from market_leadership.infrastructure.catalog_files import CatalogSnapshot
from market_leadership.infrastructure.stock_membership import (
    load_region_membership,
    membership_entry,
)
from market_leadership.ui.cache import load_catalog_snapshot
from market_leadership.ui.dataframe import render_dataframe
from market_leadership.ui.navigation import clear_catalog_selections, preserve_catalog_controls

_PREFIX = "market_leadership.screening."
_REGION_KEY = _PREFIX + "region"
_SECTOR_KEY = _PREFIX + "sector"
_INDUSTRY_KEY = _PREFIX + "industry"
_STOCKS_KEY = _PREFIX + "stocks"
_CONTEXT_KEY = _PREFIX + "context"


def _clear_stocks() -> None:
    st.session_state[_STOCKS_KEY] = []


def _clear_industry() -> None:
    st.session_state.pop(_INDUSTRY_KEY, None)
    st.session_state.pop(_CONTEXT_KEY, None)
    _clear_stocks()


def _clear_region() -> None:
    st.session_state.pop(_SECTOR_KEY, None)
    _clear_industry()


def render_industry_deep_dive(
    settings: Settings | None = None,
    *,
    snapshot: CatalogSnapshot | None = None,
    as_of: date | None = None,
) -> tuple[MembershipEntry, ...]:
    if snapshot is None:
        preserve_catalog_controls()
    st.subheader("Industry Deep-Dive")
    settings = settings or load_settings()
    if snapshot is None:
        try:
            snapshot = load_catalog_snapshot(settings.catalog_manifest_path)
        except (CatalogError, OSError, ValueError) as error:
            clear_catalog_selections()
            st.error(f"Active catalog is unavailable or invalid: {error}")
            return ()
    regions = tuple(region for region in snapshot.release.regions if region.status == "active")
    if not regions:
        st.session_state.pop(_SECTOR_KEY, None)
        _clear_industry()
        st.info("The catalog has no active reviewed regions.")
        return ()

    region_ids = tuple(region.region_id for region in regions)
    default_region = "US" if "US" in region_ids else region_ids[0]
    if st.session_state.get(_REGION_KEY) not in region_ids:
        st.session_state.pop(_SECTOR_KEY, None)
        _clear_industry()
        st.session_state[_REGION_KEY] = default_region
    if len(region_ids) > 1:
        region_id = st.selectbox(
            "Region",
            region_ids,
            key=_REGION_KEY,
            format_func=lambda key: next(
                region.name for region in regions if region.region_id == key
            ),
            on_change=_clear_region,
        )
    else:
        region_id = next(iter(region_ids))
    region = next(item for item in regions if item.region_id == region_id)
    st.caption(
        f"Coverage: {region.coverage_state.upper()} · {region.coverage_description} · "
        f"As of {region.coverage_as_of.isoformat()}"
    )
    as_of = as_of or date.today()
    try:
        scope = snapshot.scope_on(region_id, as_of)
        nodes = snapshot.active_nodes(scope, as_of)
    except CatalogError as error:
        st.session_state.pop(_SECTOR_KEY, None)
        _clear_industry()
        st.info(f"This region has no active reviewed classification: {error}")
        return ()
    sectors = tuple(node for node in nodes if node.node_type == "sector")
    if not sectors:
        _clear_region()
        st.info("No active sectors are available in this region.")
        return ()
    sector_names = {item.sector_id: item.name for item in sectors}
    if st.session_state.get(_SECTOR_KEY) not in (*sector_names, None):
        _clear_industry()
        st.session_state.pop(_SECTOR_KEY, None)
    sector_id = st.selectbox(
        "Sector",
        tuple(sector_names),
        index=None,
        key=_SECTOR_KEY,
        format_func=lambda key: sector_names[key],
        on_change=_clear_industry,
    )
    if sector_id is None:
        return ()
    industries = tuple(
        node
        for node in nodes
        if node.node_type in ("industry", "sub_industry") and node.sector_id == sector_id
    )
    industry_names = {item.node_id: item.name for item in industries}
    if not industry_names:
        _clear_industry()
        st.info("The selected sector has no active industries.")
        return ()
    if st.session_state.get(_INDUSTRY_KEY) not in (*industry_names, None):
        _clear_stocks()
        st.session_state.pop(_INDUSTRY_KEY, None)
    industry_id = st.selectbox(
        "Industry",
        tuple(industry_names),
        index=None,
        key=_INDUSTRY_KEY,
        format_func=lambda key: industry_names[key],
        on_change=_clear_stocks,
    )
    if industry_id is None:
        return ()
    membership = load_region_membership(
        snapshot,
        scope=scope,
        industry_id=industry_id,
        as_of=as_of,
    )
    if membership.state == "empty_membership":
        _clear_stocks()
        st.session_state.pop(_CONTEXT_KEY, None)
        st.info("This reviewed industry has no active stock memberships for the selected date.")
        return ()
    members = membership.members
    st.subheader("Available industry members")
    render_dataframe(
        pd.DataFrame(
            [
                {
                    "Instrument ID": member.instrument_id,
                    "Symbol": member.provider_symbol_on(as_of)
                    if member.provider_symbol_on(as_of)
                    else "Unresolved placeholder",
                    "Name": member.name,
                    "Exchange": member.listing.exchange
                    if member.provider_symbol_on(as_of) and member.listing
                    else "Unavailable",
                    "Resolution": member.resolution_state,
                }
                for member in members
            ]
        ),
        hide_index=True,
    )
    current = SelectionContext(
        f"catalog:{scope.region_id}:{scope.classification_id}:{scope.classification_version}",
        sector_id,
        industry_id,
        membership.revision,
        as_of.isoformat(),
    )
    previous_value = st.session_state.get(_CONTEXT_KEY)
    previous = previous_value if isinstance(previous_value, SelectionContext) else None
    old_value = st.session_state.get(_STOCKS_KEY, [])
    old = (
        tuple(value for value in cast(list[object], old_value) if isinstance(value, str))
        if isinstance(old_value, list)
        else ()
    )
    entries = tuple(
        entry
        for member in members
        if (entry := membership_entry(snapshot, member, as_of)) is not None
    )
    valid_ids = tuple(entry.instrument_id for entry in entries)
    selected_ids = reconcile_selection(previous, current, old, valid_ids)
    if old != selected_ids:
        st.session_state[_STOCKS_KEY] = list(selected_ids)
        st.warning("Dependent stock selections cleared after an industry or catalog change.")
    st.session_state[_CONTEXT_KEY] = current
    entry_by_id = {entry.instrument_id: entry for entry in entries}
    chosen = st.multiselect(
        "Selected stocks",
        tuple(entry_by_id),
        key=_STOCKS_KEY,
        format_func=lambda key: f"{entry_by_id[key].symbol} · {entry_by_id[key].name}",
    )
    return tuple(entry_by_id[identifier] for identifier in chosen)


if __name__ == "__main__":
    render_industry_deep_dive()
