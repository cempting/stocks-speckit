from typing import cast

import streamlit as st

from market_leadership.config import Settings, load_settings
from market_leadership.domain.stock_selection import (
    MembershipCatalog,
    MembershipEntry,
    SelectionContext,
    reconcile_selection,
)
from market_leadership.infrastructure.stock_membership import (
    load_membership_catalog,
    validate_live_access,
)
from market_leadership.ui.dataframe import render_dataframe

PREFIX = "market_leadership.screening."


def _load_live_selection(settings: Settings) -> tuple[MembershipCatalog, SelectionContext] | None:
    try:
        if not settings.stock_membership_catalog:
            raise ValueError(
                "Configure STOCK_MEMBERSHIP_CATALOG after reviewing live coverage/rights"
            )
        catalog = load_membership_catalog(settings.stock_membership_catalog)
        validate_live_access(catalog, settings)
    except (OSError, ValueError) as error:
        st.error(f"Stock membership unavailable: {error}")
        if st.session_state.get(PREFIX + "stocks"):
            st.session_state[PREFIX + "stocks"] = []
            st.warning("Dependent stock selections cleared because membership cannot be verified.")
        return None
    active = tuple(entry for entry in catalog.entries if entry.active_on(catalog.observed_on))
    st.caption(
        f"{catalog.mode.upper()} | Membership {catalog.observed_on} | Source {catalog.source_id} | "
        f"{catalog.classification} | {catalog.coverage}"
    )
    if not active:
        st.info("This valid dated catalog has zero active stock members.")
        return None
    sectors = {entry.sector_id: entry.sector_name for entry in active}
    if st.session_state.get(PREFIX + "sector") not in sectors:
        st.session_state[PREFIX + "sector"] = next(iter(sectors))
    sector = st.selectbox(
        "Sector", tuple(sectors), key=PREFIX + "sector", format_func=lambda key: sectors[key]
    )
    industries = {
        entry.industry_id: entry.industry_name for entry in active if entry.sector_id == sector
    }
    if st.session_state.get(PREFIX + "industry") not in industries:
        st.session_state[PREFIX + "industry"] = next(iter(industries))
    industry = st.selectbox(
        "Industry",
        tuple(industries),
        key=PREFIX + "industry",
        format_func=lambda key: industries[key],
    )
    return catalog, SelectionContext(
        "live", sector, industry, catalog.fingerprint, catalog.observed_on.isoformat()
    )


def _render_industry_members(
    catalog: MembershipCatalog,
    context: SelectionContext,
) -> tuple[MembershipEntry, ...]:
    members = tuple(
        entry
        for entry in catalog.entries
        if entry.industry_id == context.industry_id
        and entry.sector_id == context.sector_id
        and entry.active_on(catalog.observed_on)
    )
    st.subheader("Available industry members")
    st.caption(
        f"{catalog.mode.upper()} | Membership date {catalog.observed_on} | "
        f"Source {catalog.source_id} | {catalog.coverage}"
    )
    render_dataframe(
        [
            {"Symbol": e.symbol, "Name": e.name, "Exchange": e.exchange, "Currency": e.currency}
            for e in members
        ],
        hide_index=True,
    )
    previous_value = st.session_state.get(PREFIX + "context")
    previous = previous_value if isinstance(previous_value, SelectionContext) else None
    old_value = st.session_state.get(PREFIX + "stocks", [])
    old = (
        tuple(value for value in cast(list[object], old_value) if isinstance(value, str))
        if isinstance(old_value, list)
        else ()
    )
    reconciled = reconcile_selection(
        previous, context, old, tuple(entry.instrument_id for entry in members)
    )
    if old != reconciled:
        st.session_state[PREFIX + "stocks"] = list(reconciled)
        st.warning(
            "Dependent stock selections cleared after an industry/evidence/membership change."
        )
    st.session_state[PREFIX + "context"] = context
    by_id = {entry.instrument_id: entry for entry in members}
    chosen = st.multiselect(
        "Selected stocks",
        tuple(by_id),
        key=PREFIX + "stocks",
        format_func=lambda key: f"{by_id[key].symbol} - {by_id[key].name}",
    )
    return tuple(by_id[identifier] for identifier in chosen)


def render_industry_deep_dive(settings: Settings) -> tuple[MembershipEntry, ...]:
    selection = _load_live_selection(settings)
    if selection is None:
        return ()
    catalog, context = selection
    return _render_industry_members(catalog, context)


if __name__ == "__main__":
    render_industry_deep_dive(load_settings())
