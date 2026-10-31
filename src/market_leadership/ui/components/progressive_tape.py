"""Row-specific chart previews and stock evidence projections for Discovery tapes."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import cast

import altair as alt
import pandas as pd
import streamlit as st

from market_leadership.domain.peer_scores import BlockPeerScore, PeerScorecard
from market_leadership.domain.stock_chart import build_discovery_chart_preview
from market_leadership.ui.dataframe import render_dataframe
from market_leadership.ui.performance_table import PERFORMANCE_COLUMNS, performance_column_styles

_ChartSeries = Sequence[Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class StockTapeRow:
    instrument_id: str
    ticker: str
    name: str
    history: pd.DataFrame
    price_state: str
    observed_on: date | None = None
    price_reason: str | None = None
    scorecard: PeerScorecard | None = None
    score_state: str = "not_loaded"
    score_reason: str | None = None
    market_cap: float | None = None
    resolution_state: str = "identified"


def chart_series(history: pd.DataFrame | None, *, limit: int = 30) -> list[float]:
    if history is None or history.empty or "close" not in history.columns:
        return []
    return [float(value) for value in history.sort_index()["close"].tail(limit)]


def attach_chart_series(
    frame: pd.DataFrame,
    *,
    identity_column: str,
    history_by_id: dict[str, pd.DataFrame],
    preview_start: date | None = None,
) -> pd.DataFrame:
    if identity_column not in frame.columns:
        raise ValueError(f"Tape frame is missing its {identity_column} identity column")
    result = frame.copy()
    price_series: list[_ChartSeries | str] = []
    volume_series: list[_ChartSeries | str] = []
    for identifier in result[identity_column]:
        history = history_by_id.get(str(identifier))
        price, volume = _preview_payloads(history, preview_start=preview_start)
        price_series.append(price)
        volume_series.append(volume)
    result.insert(0, "Price chart", price_series)
    result.insert(1, "Volume chart", volume_series)
    result.attrs["volume_legend"] = (
        "Green/red/neutral bars indicate price direction, not verified buyer or seller activity."
    )
    return result


def _overall_score_text(scorecard: PeerScorecard | None, state: str) -> str:
    if state == "error":
        return "Error"
    if state == "not_loaded":
        return "Not loaded"
    if state == "insufficient":
        return "Insufficient"
    if scorecard is None:
        return "Unavailable"

    components: tuple[BlockPeerScore, ...] = (
        scorecard.quality,
        scorecard.growth,
        scorecard.cash_flow,
    )
    if any(component.state == "insufficient" for component in components):
        return "Insufficient"
    if not all(
        component.state == "available"
        and component.value is not None
        and isfinite(component.value)
        and 0 <= component.value <= 100
        for component in components
    ):
        return "Unavailable"
    score = sum(component.value for component in components if component.value is not None) / len(
        components
    )
    return f"{score:.1f}"


def _cap_type_text(market_cap: float | None, *, state: str, resolution_state: str) -> str:
    if state in ("error", "not_loaded", "placeholder") or resolution_state == "placeholder":
        return "Unavailable"
    if market_cap is None or not isfinite(market_cap) or market_cap <= 0:
        return "Unavailable"
    if market_cap >= 10_000_000_000:
        return "Large"
    if market_cap >= 2_000_000_000:
        return "Mid"
    return "Small"


def build_stock_tape_frame(
    rows: tuple[StockTapeRow, ...], *, preview_start: date | None = None
) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "Price chart": _preview_payloads(row.history, preview_start=preview_start)[0],
                "Volume chart": _preview_payloads(row.history, preview_start=preview_start)[1],
                "Ticker": (
                    "Unresolved placeholder"
                    if row.resolution_state == "placeholder"
                    else row.ticker
                ),
                "Name": row.name,
                "CAP Type": _cap_type_text(
                    row.market_cap,
                    state=row.score_state,
                    resolution_state=row.resolution_state,
                ),
                "Total Score": _overall_score_text(row.scorecard, row.score_state),
                "Instrument ID": row.instrument_id,
                "Resolution": row.resolution_state,
            }
            for row in rows
        ]
    )
    frame.attrs["volume_legend"] = (
        "Green/red/neutral bars indicate price direction, not verified buyer or seller activity."
    )
    return frame


def _preview_payloads(
    history: pd.DataFrame | None,
    *,
    preview_start: date | None = None,
) -> tuple[_ChartSeries | str, _ChartSeries | str]:
    if history is None or history.empty:
        return "Unavailable", "Unavailable"
    preview = build_discovery_chart_preview(
        history,
        as_of=pd.DatetimeIndex(history.index).max().date(),
    )
    if preview_start is not None:
        preview = preview.loc[pd.DatetimeIndex(preview.index).date >= preview_start]
    price = [
        {
            "session": pd.Timestamp(str(session)).date().isoformat(),
            "close": float(row["close"]) if pd.notna(row["close"]) else None,
            "sma50": float(row["sma50"]) if pd.notna(row["sma50"]) else None,
        }
        for session, row in preview.iterrows()
        if pd.notna(row["close"])
    ]
    volume = [
        {
            "session": pd.Timestamp(str(session)).date().isoformat(),
            "volume": float(row["volume"]) if pd.notna(row["volume"]) else None,
            "direction": str(row["direction"]),
        }
        for session, row in preview.iterrows()
        if pd.notna(row["volume"])
    ]
    return price or "Unavailable", volume or "Unavailable"


def build_price_thumbnail(series: object) -> alt.Chart | alt.LayerChart | None:
    records = _chart_records(series)
    if not records:
        return None
    frame = pd.DataFrame.from_records(records)
    if "session" not in frame or "close" not in frame:
        return None
    price = (
        alt.Chart(frame)
        .mark_line(color="#17324d", strokeWidth=1.5)  # pyright: ignore[reportUnknownMemberType]
        .encode(
            x=alt.X("session:T", axis=None),
            y=alt.Y("close:Q", axis=None, scale=alt.Scale(zero=False)),
        )
    )
    sma_frame = frame.dropna(subset=["sma50"])
    if sma_frame.empty:
        return price.properties(width=135, height=84)
    average = (
        alt.Chart(sma_frame)
        .mark_line(color="#e09f3e", strokeWidth=1)  # pyright: ignore[reportUnknownMemberType]
        .encode(x=alt.X("session:T", axis=None), y=alt.Y("sma50:Q", axis=None))
    )
    return alt.layer(price, average).properties(width=135, height=84)


def build_volume_thumbnail(series: object) -> alt.Chart | None:
    records = _chart_records(series)
    if not records:
        return None
    frame = pd.DataFrame.from_records(records)
    if not {"session", "volume", "direction"}.issubset(frame.columns):
        return None
    return (
        alt.Chart(frame)
        .mark_bar()  # pyright: ignore[reportUnknownMemberType]
        .encode(
            x=alt.X("session:T", axis=None),
            y=alt.Y("volume:Q", axis=None),
            color=alt.Color(
                "direction:N",
                scale=alt.Scale(
                    domain=["up", "down", "neutral"],
                    range=["#16a34a", "#dc2626", "#6f8f7b"],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("session:T", title="Session"),
                alt.Tooltip("volume:Q", title="Volume"),
                alt.Tooltip("direction:N", title="Price direction"),
            ],
        )
        .properties(width=135, height=84)
    )


def _chart_records(series: object) -> list[dict[str, object]] | None:
    if not isinstance(series, list) or not series:
        return None
    records: list[dict[str, object]] = []
    for item in cast(list[object], series):
        if not isinstance(item, dict):
            return None
        if not all(isinstance(key, str) for key in cast(dict[object, object], item)):
            return None
        records.append(cast(dict[str, object], item))
    return records


def _render_visual_tape(
    frame: pd.DataFrame,
    *,
    key: str,
    selectable: bool,
    on_entity_select: Callable[[str], None] | None = None,
) -> tuple[int, ...]:
    price_column = "Price chart"
    volume_column = "Volume chart"
    if price_column not in frame.columns or volume_column not in frame.columns:
        render_dataframe(frame, hide_index=True, key=key)
        return ()
    st.caption(str(frame.attrs.get("volume_legend", "")))
    hidden_columns = ("Instrument ID", "Resolution", "Node ID")
    if "Industry" in frame.columns:
        hidden_columns += ("Status", "Representation")
    content_columns = [
        column
        for column in frame.columns
        if column not in (price_column, volume_column, *hidden_columns)
        and (not selectable or column != "Name")
    ]
    weights = [1.3, 1.3, *([1.0] * len(content_columns))]
    headings = st.columns(weights)
    headings[0].caption("Price + 50 MA")
    headings[1].caption("Volume by price direction")
    for heading, label in zip(headings[2:], content_columns, strict=True):
        heading.caption(label)

    performance_styles = {
        column: performance_column_styles(
            frame[column], dark_mode=bool(st.session_state.get("dark_mode", False))
        )
        for column in PERFORMANCE_COLUMNS
        if column in content_columns
    }
    selected_rows: list[int] = []
    for row_index, (_, row) in enumerate(frame.iterrows()):
        cells = st.columns(weights)
        with cells[0]:
            chart = build_price_thumbnail(row[price_column])
            if chart is None:
                st.caption("Price unavailable")
            else:
                st.altair_chart(chart, width="stretch", key=f"{key}_price_{row_index}")
                records = _chart_records(row[price_column])
                if records and not any(
                    isinstance(value := point.get("sma50"), (int, float)) and isfinite(value)
                    for point in records
                ):
                    st.caption("50 MA: Insufficient")
        with cells[1]:
            chart = build_volume_thumbnail(row[volume_column])
            if chart is None:
                st.caption("Volume unavailable")
            else:
                st.altair_chart(chart, width="stretch", key=f"{key}_volume_{row_index}")
        for cell, column in zip(cells[2:], content_columns, strict=True):
            value = row[column]
            with cell:
                if on_entity_select is not None and column in ("Sector", "Industry"):
                    help_text = str(row["Status"])
                    if column == "Industry":
                        help_text += f"\nRepresentation: {row['Representation']}"
                    st.button(
                        str(value),
                        key=f"{key}_select_{row['Node ID']}",
                        help=help_text,
                        on_click=on_entity_select,
                        args=(str(row["Node ID"]),),
                        use_container_width=True,
                    )
                elif selectable and column == "Ticker":
                    button_label = f"{value} · {row['Name']}"
                    if st.button(
                        button_label,
                        key=f"{key}_select_{row['Instrument ID']}",
                        use_container_width=True,
                    ):
                        selected_rows.append(row_index)
                elif column in performance_styles:
                    text = f"{float(value):.2f}%" if pd.notna(value) else "Unavailable"
                    style = performance_styles[column][row_index]
                    st.html(
                        f'<div style="{style}; padding: 0.5rem; border-radius: 0.25rem; '
                        f'text-align: right; font-variant-numeric: tabular-nums">{text}</div>'
                    )
                else:
                    st.write(value)
    return tuple(selected_rows)


def render_chart_tape(
    frame: pd.DataFrame,
    *,
    key: str,
    on_select: Callable[[str], None] | None = None,
) -> None:
    _render_visual_tape(frame, key=key, selectable=False, on_entity_select=on_select)


def render_selectable_stock_tape(frame: pd.DataFrame, *, key: str) -> tuple[int, ...]:
    return _render_visual_tape(frame, key=key, selectable=True)
