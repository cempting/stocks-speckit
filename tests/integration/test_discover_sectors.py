from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_data.catalog import load_release
from market_leadership.application.discover_sectors import (
    discover_sectors,
    discover_sectors_from_snapshot,
)
from tests.integration.test_catalog_workflows import SCOPE, edit_rows


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


def _second_sector(manifest: Path) -> None:
    edit_rows(
        manifest,
        "hierarchy",
        lambda rows: rows.append(
            {
                **rows[0],
                "NodeId": "test-sector-2",
                "SectorId": "test-sector-2",
                "Name": "Other test sector",
            }
        ),
    )
    edit_rows(
        manifest,
        "etf_listings",
        lambda rows: rows.append(
            {
                **rows[0],
                "ListingId": "test-etf-2",
                "InstrumentId": "test-etf-instrument-2",
                "ProviderSymbol": "TEST_ETF_2",
                "Ticker": "TEST_ETF_2",
            }
        ),
    )
    edit_rows(
        manifest,
        "sector_etfs",
        lambda rows: rows.append(
            {
                **rows[0],
                "RepresentationId": "test-sector-representation-2",
                "NodeId": "test-sector-2",
                "ListingId": "test-etf-2",
            }
        ),
    )


def test_discovery_returns_all_sectors_sentiment_metrics_and_charts(catalog_release: Path) -> None:
    _second_sector(catalog_release)
    snapshot = load_release(catalog_release)
    symbols = ("TEST_ETF", "TEST_ETF_2")
    history = {symbol: _history(scale=1 + offset / 100) for offset, symbol in enumerate(symbols)}
    history["TEST_ETF_2"] = _history(periods=80)

    result = discover_sectors(
        StubProvider(history), snapshot=snapshot, scope=SCOPE, as_of=date(2026, 10, 23)
    )

    assert result.provider_id == "stub"
    assert result.as_of == date(2026, 10, 23)
    assert result.sentiment.regime == "Bullish"
    assert result.sentiment.benchmark == "TEST_ETF"
    assert [sector.name for sector in result.sectors] == sorted(
        sector.name for sector in result.sectors
    )
    assert len(result.sectors) == 2

    materials = next(sector for sector in result.sectors if sector.symbol == "TEST_ETF")
    assert materials.performance is not None
    assert set(materials.performance.absolute) == {"1w", "1m", "3m", "6m", "12m"}
    assert set(materials.performance.relative) == {"1w", "1m", "3m", "6m", "12m"}
    assert list(materials.history.columns) == ["close", "volume", "sma50"]
    assert materials.history["sma50"].notna().sum() > 0

    real_estate = next(sector for sector in result.sectors if sector.symbol == "TEST_ETF_2")
    assert real_estate.performance is None
    assert real_estate.insufficient_reason is not None


def test_snapshot_prices_can_drive_discovery_without_provider_calls(catalog_release: Path) -> None:
    history = _history()
    prices = history.reset_index(names="date")
    prices.insert(0, "symbol", "TEST_ETF")

    discovery = discover_sectors_from_snapshot(
        {"prices": prices},
        source_id="fixture",
        as_of=date(2026, 10, 23),
        snapshot=load_release(catalog_release),
        scope=SCOPE,
    )

    assert discovery.provider_id == "fixture"
    assert discovery.sentiment.benchmark == "TEST_ETF"
    assert len(discovery.sectors) == 1
    assert discovery.sectors[0].performance is not None


def test_missing_latest_benchmark_close_does_not_mix_return_end_dates(
    catalog_release: Path,
) -> None:
    _second_sector(catalog_release)
    history = {symbol: _history() for symbol in ("TEST_ETF", "TEST_ETF_2")}
    history["TEST_ETF"] = history["TEST_ETF"].iloc[:-1]
    history["TEST_ETF_2"] = history["TEST_ETF_2"].iloc[:-2]

    result = discover_sectors(
        StubProvider(history),
        snapshot=load_release(catalog_release),
        scope=SCOPE,
        as_of=date(2026, 10, 23),
    )

    assert result.benchmark_as_of == date(2026, 10, 22)
    materials = next(sector for sector in result.sectors if sector.symbol == "TEST_ETF_2")
    assert materials.performance is None
    assert "2026-10-22" in materials.insufficient_reason
    financials = next(sector for sector in result.sectors if sector.symbol == "TEST_ETF")
    assert financials.performance is not None
    assert financials.performance.absolute["1w"] == pytest.approx(
        history["TEST_ETF"].loc["2026-10-22", "close"]
        / history["TEST_ETF"].loc["2026-10-15", "close"]
        - 1
    )
