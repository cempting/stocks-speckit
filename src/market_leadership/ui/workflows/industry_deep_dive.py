"""Industry Deep-Dive selection backed by the reviewed regional database."""

from datetime import date
from typing import cast

import streamlit as st

from market_leadership.config import Settings
from market_leadership.domain.stock_selection import (
    MembershipEntry,
    SelectionContext,
    reconcile_selection,
)
from market_leadership.infrastructure.region_database import RegionDatabase, StockMembershipRecord
from market_leadership.infrastructure.stock_membership import load_region_membership
from market_leadership.ui.dataframe import render_dataframe

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
    _clear_stocks()


def _entry(member: StockMembershipRecord) -> MembershipEntry | None:
    listing = member.primary_listing
    if listing is None or member.resolution_state != "identified":
        return None
    return MembershipEntry(
        member.instrument_id,
        member.company_id or member.instrument_id,
        listing.provider_symbol or listing.symbol,
        member.name,
        listing.exchange_id,
        listing.currency,
        member.sector_id,
        member.sector_name,
        member.industry_id,
        member.industry_name,
        member.effective_from,
        member.effective_to,
    )


def render_industry_deep_dive(settings: Settings | None = None) -> tuple[MembershipEntry, ...]:
    del settings
    st.subheader("Industry Deep-Dive")
    database = RegionDatabase()
    if not database.is_initialized():
        if database.path.exists():
            st.error(f"Regional stock database is invalid: {database.path}")
        else:
            st.info(
                "Initialize and populate the regional stock database to use Industry Deep-Dive."
            )
        return ()
    regions = database.get_regions()
    if not regions:
        st.info("The regional database has no reviewed membership data.")
        return ()

    region_ids = tuple(region.region_id for region in regions)
    default_region = "US" if "US" in region_ids else region_ids[0]
    if st.session_state.get(_REGION_KEY) not in region_ids:
        st.session_state[_REGION_KEY] = default_region
    if len(region_ids) > 1:
        region_id = st.selectbox(
            "Region",
            region_ids,
            key=_REGION_KEY,
            format_func=lambda key: next(
                region.name for region in regions if region.region_id == key
            ),
            on_change=_clear_industry,
        )
    else:
        region_id = next(iter(region_ids))
    region = next(item for item in regions if item.region_id == region_id)
    st.caption(
        f"Coverage: {region.coverage_state.upper()} · {region.coverage_description} · "
        f"As of {region.coverage_as_of.isoformat()}"
    )
    classification_id = database.get_classification_id(region_id)
    if classification_id is None:
        st.info("This region has no active reviewed classification.")
        return ()
    as_of = date.today()
    sectors = database.get_sectors(region_id, classification_id, as_of=as_of)
    if not sectors:
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
    industries = database.get_industries(region_id, classification_id, sector_id, as_of=as_of)
    industry_names = {item.industry_id: item.name for item in industries}
    if not industry_names:
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
        database,
        region_id=region_id,
        classification_id=classification_id,
        industry_id=industry_id,
        as_of=as_of,
    )
    if membership.state == "empty_membership":
        st.info("This reviewed industry has no active stock memberships for today.")
        return ()
    members = membership.members
    st.subheader("Available industry members")
    render_dataframe(
        [
            {
                "Instrument ID": member.instrument_id,
                "Symbol": member.primary_listing.symbol
                if member.primary_listing
                else "Unresolved placeholder",
                "Name": member.name,
                "Exchange": member.primary_listing.exchange_id
                if member.primary_listing
                else "Unavailable",
                "Resolution": member.resolution_state,
            }
            for member in members
        ],
        hide_index=True,
    )
    current = SelectionContext(
        f"database:{region_id}",
        sector_id,
        industry_id,
        database.get_revision(),
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
    entries = tuple(entry for member in members if (entry := _entry(member)) is not None)
    valid_ids = tuple(entry.instrument_id for entry in entries)
    selected_ids = reconcile_selection(previous, current, old, valid_ids)
    if old != selected_ids:
        st.session_state[_STOCKS_KEY] = list(selected_ids)
        st.warning("Dependent stock selections cleared after an industry or database change.")
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
