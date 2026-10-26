from datetime import date

import numpy as np
import pandas as pd

from market_leadership.application.discover_sectors import discover_sectors


class StubProvider:
    provider_id = "stub"

    def __init__(self, history: dict[str, pd.DataFrame]) -> None:
        self.history = history

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del start, end, force
        return {symbol: self.history[symbol] for symbol in symbols}


def _history(scale: float = 1.0, periods: int = 320) -> pd.DataFrame:
    index = pd.bdate_range(end="2026-10-23", periods=periods)
    return pd.DataFrame(
        {
            "close": np.linspace(80, 140, periods) * scale,
            "volume": np.linspace(1_000_000, 1_500_000, periods),
        },
        index=index,
    )


def test_discovery_returns_all_sectors_sentiment_metrics_and_charts() -> None:
    symbols = ("SPY", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY")
    history = {symbol: _history(scale=1 + offset / 100) for offset, symbol in enumerate(symbols)}
    history["XLRE"] = _history(periods=80)

    result = discover_sectors(StubProvider(history), as_of=date(2026, 10, 23))

    assert result.provider_id == "stub"
    assert result.as_of == date(2026, 10, 23)
    assert result.sentiment.regime == "Bullish"
    assert result.sentiment.benchmark == "SPY"
    assert [sector.name for sector in result.sectors] == sorted(
        sector.name for sector in result.sectors
    )
    assert len(result.sectors) == 11

    materials = next(sector for sector in result.sectors if sector.symbol == "XLB")
    assert materials.performance is not None
    assert set(materials.performance.absolute) == {"1w", "1m", "3m", "6m", "12m"}
    assert set(materials.performance.relative) == {"1w", "1m", "3m", "6m", "12m"}
    assert list(materials.history.columns) == ["close", "volume", "sma50"]
    assert materials.history["sma50"].notna().sum() > 0

    real_estate = next(sector for sector in result.sectors if sector.symbol == "XLRE")
    assert real_estate.performance is None
    assert real_estate.insufficient_reason is not None
