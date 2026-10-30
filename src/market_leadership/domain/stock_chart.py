"""Stock-specific chart series and exact completed-session moving averages."""

from dataclasses import dataclass
from datetime import date
from math import isfinite

import pandas as pd


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


def build_stock_chart_evidence(
    instrument_id: str,
    history: pd.DataFrame,
    *,
    as_of: date,
) -> StockChartEvidence:
    if not instrument_id.strip():
        raise ValueError("Stock chart evidence requires a stable instrument ID")
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
        )

    completed = history.loc[pd.DatetimeIndex(history.index).date <= as_of].sort_index().copy()
    if completed.index.has_duplicates:
        raise ValueError("Stock chart sessions must be unique")
    close_valid = (
        "close" in completed.columns
        and not completed["close"].empty
        and all(isfinite(float(value)) and float(value) > 0 for value in completed["close"])
    )
    volume_valid = (
        "volume" in completed.columns
        and not completed["volume"].empty
        and all(isfinite(float(value)) and float(value) >= 0 for value in completed["volume"])
    )
    if not close_valid:
        completed["sma50"] = pd.Series(index=completed.index, dtype="float64")
        completed["sma150"] = pd.Series(index=completed.index, dtype="float64")
        return StockChartEvidence(
            instrument_id,
            as_of,
            None,
            completed,
            "insufficient",
            "available" if volume_valid else "insufficient",
            "insufficient",
            "insufficient",
        )

    completed["sma50"] = completed["close"].rolling(window=50, min_periods=50).mean()
    completed["sma150"] = completed["close"].rolling(window=150, min_periods=150).mean()
    latest = completed.iloc[-1]
    return StockChartEvidence(
        instrument_id,
        as_of,
        pd.DatetimeIndex(completed.index)[-1].date(),
        completed,
        "available",
        "available" if volume_valid else "insufficient",
        "available" if pd.notna(latest["sma50"]) else "insufficient",
        "available" if pd.notna(latest["sma150"]) else "insufficient",
    )


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
