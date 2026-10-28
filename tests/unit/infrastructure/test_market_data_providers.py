from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from market_leadership.infrastructure.massive_provider import MassiveProvider
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider


def test_yfinance_provider_normalizes_adjusted_batch_download() -> None:
    columns = pd.MultiIndex.from_product(
        [["SPY", "XLB"], ["Close", "Volume"]], names=["Ticker", "Price"]
    )
    downloaded = pd.DataFrame(
        [[100.0, 1_000.0, 50.0, 500.0], [101.0, 1_100.0, 51.0, 550.0]],
        index=pd.to_datetime(["2026-10-22", "2026-10-23"]),
        columns=columns,
    )
    calls: list[dict[str, object]] = []

    def downloader(**kwargs: object) -> pd.DataFrame:
        calls.append(kwargs)
        return downloaded

    result = YFinanceProvider(downloader=downloader).fetch_daily_history(
        ("SPY", "XLB"),
        start=date(2026, 10, 1),
        end=date(2026, 10, 23),
    )

    assert calls[0]["auto_adjust"] is True
    assert calls[0]["interval"] == "1d"
    assert list(result["SPY"].columns) == ["close", "volume"]
    assert result["XLB"].iloc[-1].to_dict() == {"close": 51.0, "volume": 550.0}


def test_yfinance_batch_ignores_dates_with_no_observation_for_a_symbol() -> None:
    columns = pd.MultiIndex.from_product(
        [["SPY", "XLB"], ["Close", "Volume"]], names=["Ticker", "Price"]
    )
    downloaded = pd.DataFrame(
        [
            [100.0, 1_000.0, 50.0, 500.0],
            [None, None, 51.0, 550.0],
        ],
        index=pd.to_datetime(["2026-10-22", "2026-10-23"]),
        columns=columns,
    )
    provider = YFinanceProvider(downloader=lambda **kwargs: downloaded)

    result = provider.fetch_daily_history(
        ("SPY", "XLB"),
        start=date(2026, 10, 22),
        end=date(2026, 10, 23),
    )

    assert result["SPY"].index.strftime("%Y-%m-%d").tolist() == ["2026-10-22"]
    assert result["SPY"]["close"].tolist() == [100.0]
    assert result["XLB"]["close"].tolist() == [50.0, 51.0]


def test_yfinance_omits_incomplete_vendor_bar_with_volume_but_no_close() -> None:
    downloaded = pd.DataFrame(
        {"Close": [100.0, None], "Volume": [1_000.0, 1_100.0]},
        index=pd.to_datetime(["2026-10-26", "2026-10-27"]),
    )
    result = YFinanceProvider(downloader=lambda **kwargs: downloaded).fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 26),
        end=date(2026, 10, 27),
    )

    assert result["SPY"].index.strftime("%Y-%m-%d").tolist() == ["2026-10-26"]
    assert result["SPY"]["close"].tolist() == [100.0]
    assert result["SPY"].attrs["available_on"] == "2026-10-26"


def test_yfinance_rejects_incomplete_interior_bar() -> None:
    downloaded = pd.DataFrame(
        {"Close": [100.0, None, 102.0], "Volume": [1_000.0, 1_100.0, 1_200.0]},
        index=pd.to_datetime(["2026-10-23", "2026-10-26", "2026-10-27"]),
    )

    with pytest.raises(ValueError, match="Daily history for SPY contains invalid close"):
        YFinanceProvider(downloader=lambda **kwargs: downloaded).fetch_daily_history(
            ("SPY",),
            start=date(2026, 10, 23),
            end=date(2026, 10, 27),
        )


def test_yfinance_rejects_nonpositive_close_when_volume_is_present() -> None:
    downloaded = pd.DataFrame(
        {"Close": [0.0], "Volume": [1_000.0]},
        index=pd.to_datetime(["2026-10-22"]),
    )
    provider = YFinanceProvider(downloader=lambda **kwargs: downloaded)

    with pytest.raises(ValueError, match="Daily history for SPY contains invalid close"):
        provider.fetch_daily_history(
            ("SPY",),
            start=date(2026, 10, 22),
            end=date(2026, 10, 22),
        )


def test_massive_provider_normalizes_adjusted_aggregate_models() -> None:
    class Client:
        def list_aggs(self, **kwargs: object) -> list[SimpleNamespace]:
            assert kwargs["adjusted"] is True
            assert kwargs["timespan"] == "day"
            return [
                SimpleNamespace(close=100.0, volume=1_000.0, timestamp=1792728000000),
                SimpleNamespace(close=101.0, volume=1_100.0, timestamp=1792814400000),
            ]

    result = MassiveProvider(client=Client()).fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 1),
        end=date(2026, 10, 24),
    )

    assert list(result["SPY"].columns) == ["close", "volume"]
    assert result["SPY"].iloc[-1].to_dict() == {"close": 101.0, "volume": 1_100.0}
    assert result["SPY"].index.is_monotonic_increasing
