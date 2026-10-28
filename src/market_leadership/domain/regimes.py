from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class MarketSentiment:
    benchmark: str
    regime: str
    close: float | None
    sma150: float | None
    normalized_slope_pct: float | None
    slope_state: str


def calculate_market_sentiment(frame: pd.DataFrame, benchmark: str = "SPY") -> MarketSentiment:
    closes = cast(pd.Series, frame["close"]).sort_index()
    sma150 = cast(
        pd.Series,
        closes.rolling(window=150, min_periods=150).mean(),
    )
    if closes.empty or pd.isna(closes.iloc[-1]) or pd.isna(sma150.iloc[-1]):
        return MarketSentiment(benchmark, "Insufficient", None, None, None, "Undefined")

    latest_close = float(closes.iloc[-1])
    latest_sma = float(sma150.iloc[-1])
    if len(sma150) < 20 or sma150.iloc[-20:].isna().any():
        return MarketSentiment(
            benchmark,
            "Sideways",
            latest_close,
            latest_sma,
            None,
            "Undefined",
        )

    averages = sma150.iloc[-20:].to_numpy(dtype=float)
    slope = float(np.polyfit(np.arange(20, dtype=float), averages, 1)[0])
    normalized_slope_pct = slope / latest_sma * 100
    if normalized_slope_pct > 0.025:
        slope_state = "Rising"
    elif normalized_slope_pct < -0.025:
        slope_state = "Falling"
    else:
        slope_state = "Flat"

    if latest_close > latest_sma and slope_state == "Rising":
        regime = "Bullish"
    elif latest_close < latest_sma and slope_state == "Falling":
        regime = "Bearish"
    else:
        regime = "Sideways"

    return MarketSentiment(
        benchmark,
        regime,
        latest_close,
        latest_sma,
        normalized_slope_pct,
        slope_state,
    )
