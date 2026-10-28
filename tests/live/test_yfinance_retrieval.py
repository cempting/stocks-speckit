import os
from datetime import date

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from market_leadership.infrastructure.market_data_cache import CachedMarketDataProvider
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_MARKET_DATA") != "1",
        reason="set RUN_LIVE_MARKET_DATA=1 to call yfinance",
    ),
]


def _fail_download(**kwargs: object) -> pd.DataFrame:
    raise RuntimeError("network was called during a cache hit")


def test_yfinance_retrieval_and_persistent_cache(tmp_path) -> None:
    symbols = ("SPY", "XLF")
    start = date(2025, 1, 2)
    end = date(2025, 1, 10)
    live = CachedMarketDataProvider(YFinanceProvider(), tmp_path).fetch_daily_history(
        symbols,
        start=start,
        end=end,
        force=True,
    )

    for symbol in symbols:
        frame = live[symbol]
        assert not frame.empty
        assert list(frame.columns) == ["close", "volume"]
        assert isinstance(frame.index, pd.DatetimeIndex)
        actual_dates = frame.index.strftime("%Y-%m-%d").tolist()
        assert actual_dates[0] == start.isoformat()
        assert actual_dates[-1] == end.isoformat()
        assert bool(frame["close"].notna().all())

    cached = CachedMarketDataProvider(
        YFinanceProvider(downloader=_fail_download),
        tmp_path,
    ).fetch_daily_history(symbols, start=start, end=end)

    for symbol in symbols:
        assert_frame_equal(cached[symbol], live[symbol], check_freq=False)
    assert list(tmp_path.rglob("CURRENT"))
    assert list(tmp_path.rglob("manifest.json"))
    assert list(tmp_path.rglob("data.parquet"))
