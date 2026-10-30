"""Row-specific chart previews and stock evidence projections for Discovery tapes."""

from dataclasses import dataclass
from datetime import date
from math import isfinite

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler
from streamlit.elements.lib.column_types import ColumnConfig

from market_leadership.domain.peer_scores import BlockPeerScore, PeerScorecard
from market_leadership.ui.dataframe import render_dataframe, render_selectable_dataframe


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


def chart_series(history: pd.DataFrame | None, *, limit: int = 30) -> list[float]:
    if history is None or history.empty or "close" not in history.columns:
        return []
    return [float(value) for value in history.sort_index()["close"].tail(limit)]


def attach_chart_series(
    frame: pd.DataFrame,
    *,
    identity_column: str,
    history_by_id: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    if identity_column not in frame.columns:
        raise ValueError(f"Tape frame is missing its {identity_column} identity column")
    result = frame.copy()
    result.insert(
        0,
        "Chart",
        [
            chart_series(history_by_id.get(str(identifier)))
            for identifier in result[identity_column]
        ],
    )
    return result


def _score_text(score: BlockPeerScore | None, state: str) -> str:
    if score is not None and score.state == "available" and score.value is not None:
        if isfinite(score.value) and 0 <= score.value <= 100:
            return f"{score.value:.1f}"
        return "Unavailable"
    if state == "error":
        return "Error"
    if score is not None and score.state == "insufficient":
        return "Insufficient"
    if state == "not_loaded":
        return "Not loaded"
    return "Unavailable"


def build_stock_tape_frame(rows: tuple[StockTapeRow, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Chart": chart_series(row.history),
                "Ticker": row.ticker,
                "Name": row.name,
                "Price": (
                    f"{float(row.history['close'].iloc[-1]):.2f}"
                    if row.price_state == "available"
                    and not row.history.empty
                    and isfinite(float(row.history["close"].iloc[-1]))
                    else row.price_state.title()
                ),
                "Chart status": (
                    "Available"
                    if row.price_state == "available"
                    else f"{row.price_state.title()}: {row.price_reason}"
                    if row.price_reason
                    else row.price_state.title()
                ),
                "Observed": row.observed_on.isoformat() if row.observed_on else "Unavailable",
                "Quality": _score_text(
                    row.scorecard.quality if row.scorecard else None, row.score_state
                ),
                "Growth": _score_text(
                    row.scorecard.growth if row.scorecard else None, row.score_state
                ),
                "Cash Flow": _score_text(
                    row.scorecard.cash_flow if row.scorecard else None, row.score_state
                ),
                "Score status": row.score_reason or row.score_state.replace("_", " ").title(),
            }
            for row in rows
        ]
    )


def render_chart_tape(
    frame: pd.DataFrame | Styler,
    *,
    key: str,
    column_config: dict[str, ColumnConfig] | None = None,
) -> None:
    config = dict(column_config or {})
    config["Chart"] = st.column_config.LineChartColumn("Chart", width="small")
    render_dataframe(
        frame,
        hide_index=True,
        key=key,
        column_config=config,
    )


def render_selectable_stock_tape(frame: pd.DataFrame, *, key: str) -> tuple[int, ...]:
    selection = render_selectable_dataframe(
        frame,
        key=key,
        column_config={"Chart": st.column_config.LineChartColumn("Chart", width="small")},
    )
    return tuple(selection.selection.rows)
