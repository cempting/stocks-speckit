from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from test_yfinance_fundamentals import FakeTicker

from market_leadership.domain.fundamentals import FundamentalRequest
from market_leadership.infrastructure.yfinance_fundamentals import FundamentalAcquisitionError
from market_leadership.ui.cache import load_fundamental_bundle, refresh_fundamental_bundle


def test_fresh_reuse_key_isolation_expiry_and_targeted_refresh():
    calls = []

    def factory(symbol):
        calls.append(symbol)
        ticker = FakeTicker()
        ticker.info = {**ticker.info, "symbol": symbol}
        return ticker

    request = FundamentalRequest("CACHE-TEST")
    now = datetime.now(UTC)
    first = refresh_fundamental_bundle(request, _factory=factory, now=now)
    assert load_fundamental_bundle(request, _factory=factory, now=now) == first
    other = replace(request, symbol="OTHER")
    refresh_fundamental_bundle(other, _factory=factory, now=now)
    refresh_fundamental_bundle(request, _factory=factory, now=now)
    load_fundamental_bundle(other, _factory=factory, now=now)
    assert calls == ["CACHE-TEST", "OTHER", "CACHE-TEST"]
    load_fundamental_bundle(request, _factory=factory, now=now + timedelta(seconds=3601))
    assert calls[-1] == "CACHE-TEST"
    assert len(calls) == 4
    load_fundamental_bundle(replace(request, schema_version=2), _factory=factory, now=now)
    assert len(calls) == 5


def test_failed_operation_is_not_cached():
    class Empty(FakeTicker):
        info = {}

    calls = []
    request = FundamentalRequest("FAILED-CACHE")
    for _ in range(2):
        with pytest.raises(FundamentalAcquisitionError):
            load_fundamental_bundle(request, _factory=lambda _: calls.append(1) or Empty())
    assert len(calls) == 2
