from datetime import date
from types import SimpleNamespace

import pandas as pd

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
        end=date(2026, 10, 23),
    )

    assert list(result["SPY"].columns) == ["close", "volume"]
    assert result["SPY"].iloc[-1].to_dict() == {"close": 101.0, "volume": 1_100.0}
    assert result["SPY"].index.is_monotonic_increasing
