"""Sector-filtered industry discovery with source-specific result paths."""

from datetime import date
from typing import cast

import streamlit as st

from market_leadership.application.browse_scoreboard import read_weekly_board
from market_leadership.application.discover_sectors import SECTOR_PROXIES
from market_leadership.application.inspect_industry import inspect_industry
from market_leadership.bootstrap import build_snapshot_repository
from market_leadership.config import load_settings
from market_leadership.infrastructure.snapshot_errors import IntegrityError, SchemaMismatch
from market_leadership.ui.workflows.industry_detail import render_industry_detail

_HANDOFF_KEY = "market_leadership.industry_handoff"
_MODE_KEY = "market_leadership.industry_mode"
_SECTORS_KEY = "market_leadership.industry_selected_sectors"


def _consume_handoff() -> dict[str, object] | None:
    value = st.session_state.pop(_HANDOFF_KEY, None)
    if value is None:
        return None
    if not isinstance(value, dict):
        st.error("Industry navigation context is invalid; select the parent sector again.")
        return None
    return cast(dict[str, object], value)


def render_industry_discovery(*, configure_page: bool = True) -> None:
    if configure_page:
        st.set_page_config(page_title="Industry Discovery", layout="wide")
    st.title("Industry Discovery")
    st.caption(
        "Select US parent sectors to inspect their industries. Weekly fixture rankings and "
        "live daily evidence are separate modes."
    )

    handoff = _consume_handoff()
    if handoff is not None:
        if handoff.get("market_id") != "US":
            st.error("Industry Discovery currently supports US only.")
            return
        mode = handoff.get("mode")
        if mode not in ("weekly", "live"):
            st.error("Industry navigation context has an unsupported evidence mode.")
            return
        st.session_state[_MODE_KEY] = "Weekly snapshot" if mode == "weekly" else "Live US"

    mode = st.selectbox(
        "Evidence mode",
        options=("Weekly snapshot", "Live US"),
        key=_MODE_KEY,
    )
    if mode == "Live US":
        sector_names = [name for name, _ in SECTOR_PROXIES]
        supplied_names: object = handoff.get("sector_names", []) if handoff else []
        handoff_names = (
            [
                name
                for name in cast(list[object], supplied_names)
                if isinstance(name, str) and name in sector_names
            ]
            if isinstance(supplied_names, list)
            else []
        )
        st.multiselect(
            "Sectors",
            options=sector_names,
            default=handoff_names,
            key=_SECTORS_KEY,
            help="Choose parent sectors for a future authorized live industry catalog.",
        )
        st.info(
            "Live industry results are not enabled. The source review found candidate ETF "
            "exposures, but no verified dated industry catalog, point-in-time stock membership "
            "and market-cap source, or deployment rights for live derived results. No live "
            "provider request was made."
        )
        return

    repository = build_snapshot_repository(load_settings())
    try:
        sector_board = read_weekly_board(repository, "US", "SECTOR", as_of=date.today())
    except (IntegrityError, SchemaMismatch):
        st.error("The weekly sector snapshot failed validation; no industries were displayed.")
        return
    if sector_board.entries.empty or sector_board.as_of is None:
        st.info("No completed US weekly sector snapshot is available to select parent sectors.")
        return

    sectors_by_name = {
        str(row["name"]): str(row["node_id"]) for _, row in sector_board.entries.iterrows()
    }
    if handoff is not None:
        requested_ids = handoff.get("sector_node_ids")
        if not isinstance(requested_ids, list) or not requested_ids:
            st.error("Industry navigation context has no parent sector.")
            return
        requested_ids = cast(list[object], requested_ids)
        handoff_as_of = handoff.get("as_of")
        if handoff_as_of is not None and handoff_as_of != sector_board.as_of.isoformat():
            st.error("The selected sector week has changed; choose the parent sector again.")
            return
        unknown_ids = [
            node_id for node_id in requested_ids if node_id not in sectors_by_name.values()
        ]
        if unknown_ids:
            st.error("A selected parent sector is not in the current weekly US snapshot.")
            return
        st.session_state[_SECTORS_KEY] = [
            name for name, node_id in sectors_by_name.items() if node_id in requested_ids
        ]

    selected_names = st.multiselect(
        "Sectors",
        options=list(sectors_by_name),
        key=_SECTORS_KEY,
        help="Choose one or more parent sectors. Each sector keeps its own ranking context.",
    )
    if not selected_names:
        st.info("Select one or more sectors to view their industries.")
        return

    for selected_name in selected_names:
        sector_node_id = sectors_by_name.get(selected_name)
        if sector_node_id is None:
            st.error(f"{selected_name} is not a valid parent sector in the weekly snapshot.")
            continue
        try:
            detail = inspect_industry(
                repository,
                market_id="US",
                sector_node_id=sector_node_id,
            )
        except (IntegrityError, SchemaMismatch, ValueError):
            st.error(f"{selected_name}: weekly industry context could not be validated.")
            continue
        render_industry_detail(detail)


if __name__ == "__main__":
    render_industry_discovery()
