"""Stock-specific chart series and exact completed-session moving averages."""

from dataclasses import dataclass
from datetime import date
from math import ceil, isfinite

import pandas as pd

from market_data.domain.consolidation import (
    CONSOLIDATION_HISTORY_WARMUP_SESSIONS,
    ConsolidationResult,
    detect_consolidation,
)

STOCK_CHART_PERIODS = ("1m", "3m", "6m", "12m", "18m", "24m")
_CHART_PERIOD_MONTHS = {period: int(period[:-1]) for period in STOCK_CHART_PERIODS}


@dataclass(frozen=True, slots=True)
class StockChartEvidence:
    instrument_id: str
    requested_as_of: date
    observed_on: date | None
    history: pd.DataFrame
    price_state: str
    volume_state: str
    sma50_state: str
    sma150_state: str
    consolidation: ConsolidationResult


def build_stock_chart_evidence(
    instrument_id: str,
    history: pd.DataFrame,
    *,
    as_of: date,
    visible_range: str | None = None,
    consolidation_result: ConsolidationResult | None = None,
) -> StockChartEvidence:
    if not instrument_id.strip():
        raise ValueError("Stock chart evidence requires a stable instrument ID")
    if visible_range is not None and visible_range not in _CHART_PERIOD_MONTHS:
        raise ValueError(f"Unsupported stock chart range: {visible_range}")
    consolidation = (
        detect_consolidation(instrument_id, history, as_of=as_of)
        if consolidation_result is None
        else consolidation_result
    )
    if consolidation.instrument_id != instrument_id or consolidation.as_of != as_of:
        raise ValueError("Consolidation evidence must match the stock and requested date")
    if history.empty:
        empty = pd.DataFrame(columns=["close", "volume", "sma50", "sma150"], dtype="float64")
        return StockChartEvidence(
            instrument_id,
            as_of,
            None,
            empty,
            "unavailable",
            "unavailable",
            "insufficient",
            "insufficient",
            consolidation,
        )

    completed = history.loc[pd.DatetimeIndex(history.index).date <= as_of].sort_index().copy()
    completed.attrs.update(history.attrs)
    if completed.index.has_duplicates:
        raise ValueError("Stock chart sessions must be unique")
    for column in ("close", "volume"):
        if column not in completed.columns:
            completed[column] = float("nan")
        completed[column] = pd.to_numeric(completed[column], errors="coerce")
    completed.loc[
        ~completed["close"].map(lambda value: isfinite(float(value)) and float(value) > 0),
        "close",
    ] = float("nan")
    completed.loc[
        ~completed["volume"].map(lambda value: isfinite(float(value)) and float(value) >= 0),
        "volume",
    ] = float("nan")
    completed["sma50"] = completed["close"].rolling(window=50, min_periods=50).mean()
    completed["sma150"] = completed["close"].rolling(window=150, min_periods=150).mean()
    observed_on = pd.DatetimeIndex(completed.index)[-1].date() if not completed.empty else None
    visible = completed
    if visible_range is not None:
        visible_start = stock_chart_visible_start(as_of, visible_range)
        visible = completed.loc[pd.DatetimeIndex(completed.index).date >= visible_start]
    if visible.empty:
        return StockChartEvidence(
            instrument_id,
            as_of,
            observed_on,
            visible,
            "unavailable",
            "unavailable",
            "insufficient",
            "insufficient",
            consolidation,
        )
    visible.attrs.update(completed.attrs)
    latest = visible.iloc[-1]
    price_valid = completed["close"].notna().all()
    volume_valid = completed["volume"].notna().all()
    return StockChartEvidence(
        instrument_id,
        as_of,
        observed_on,
        visible,
        "available" if price_valid else "insufficient",
        "available" if volume_valid else "insufficient",
        "available" if pd.notna(latest["sma50"]) else "insufficient",
        "available" if pd.notna(latest["sma150"]) else "insufficient",
        consolidation,
    )


def stock_chart_visible_start(as_of: date, visible_range: str) -> date:
    try:
        months = _CHART_PERIOD_MONTHS[visible_range]
    except KeyError:
        raise ValueError(f"Unsupported stock chart range: {visible_range}") from None
    return (pd.Timestamp(as_of) - pd.DateOffset(months=months)).date()


def stock_chart_lookback_days(
    as_of: date,
    visible_range: str,
    *,
    warmup_sessions: int = CONSOLIDATION_HISTORY_WARMUP_SESSIONS,
) -> int:
    if warmup_sessions < 1:
        raise ValueError("Stock chart warm-up must include at least one session")
    visible_start = stock_chart_visible_start(as_of, visible_range)
    visible_days = (as_of - visible_start).days
    warmup_days = ceil(warmup_sessions * 365.25 / 252)
    return visible_days + warmup_days


def build_discovery_chart_preview(
    history: pd.DataFrame,
    *,
    as_of: date,
    limit: int | None = None,
) -> pd.DataFrame:
    """Build aligned price/volume preview data with close-direction labels."""
    columns = ["close", "sma50", "volume", "direction"]
    if history.empty:
        return pd.DataFrame(columns=columns, dtype="object")
    completed = history.loc[pd.DatetimeIndex(history.index).date <= as_of].sort_index().copy()
    if completed.index.has_duplicates:
        raise ValueError("Discovery chart sessions must be unique")
    for column in ("close", "volume"):
        if column not in completed.columns:
            completed[column] = float("nan")
        completed[column] = pd.to_numeric(completed[column], errors="coerce")
    completed["sma50"] = completed["close"].rolling(window=50, min_periods=50).mean()
    previous_close = completed["close"].shift()
    completed["direction"] = "neutral"
    completed.loc[completed["close"] > previous_close, "direction"] = "up"
    completed.loc[completed["close"] < previous_close, "direction"] = "down"
    if limit is not None:
        if limit < 1:
            raise ValueError("Preview limit must be positive")
        completed = completed.tail(limit)
    return completed.loc[:, columns]
