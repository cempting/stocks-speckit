import json
from datetime import date

import pandas as pd
import pytest

from market_leadership.infrastructure.market_data_cache import (
    CachedMarketDataProvider,
    daily_history_fingerprint,
)


def _history(close: float) -> dict[str, pd.DataFrame]:
    return {
        "SPY": pd.DataFrame(
            {"close": [close], "volume": [1_000.0]},
            index=pd.to_datetime(["2026-10-23"]),
        )
    }


class StubProvider:
    provider_id = "stub"

    def __init__(self, responses: list[dict[str, pd.DataFrame] | Exception]) -> None:
        self.responses = responses
        self.calls = 0

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del symbols, start, end, force
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def test_daily_history_fingerprint_normalizes_symbol_order() -> None:
    first = daily_history_fingerprint(
        provider_id="yfinance",
        symbols=("spy", "XLB"),
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
    )
    second = daily_history_fingerprint(
        provider_id="yfinance",
        symbols=("XLB", "SPY"),
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
    )

    assert first == second


def test_fresh_persistent_hit_makes_zero_upstream_calls(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    initial = StubProvider([_history(100.0)])
    CachedMarketDataProvider(initial, tmp_path).fetch_daily_history(**request)

    unavailable = StubProvider([RuntimeError("upstream must not be called")])
    result = CachedMarketDataProvider(unavailable, tmp_path).fetch_daily_history(**request)

    assert unavailable.calls == 0
    assert result["SPY"].iloc[-1]["close"] == 100.0


def test_force_refreshes_and_failed_refresh_preserves_prior_generation(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream = StubProvider([_history(100.0), _history(101.0), RuntimeError("rate limited")])
    cached = CachedMarketDataProvider(upstream, tmp_path)

    cached.fetch_daily_history(**request)
    refreshed = cached.fetch_daily_history(**request, force=True)
    with pytest.raises(RuntimeError, match="rate limited"):
        cached.fetch_daily_history(**request, force=True)
    preserved = cached.fetch_daily_history(**request)

    assert upstream.calls == 3
    assert refreshed["SPY"].iloc[-1]["close"] == 101.0
    assert preserved["SPY"].iloc[-1]["close"] == 101.0
    assert not list(tmp_path.rglob(".publishing-*"))


def test_checksum_failure_is_a_cache_miss(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream = StubProvider([_history(100.0), _history(102.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    data_path = current_path.parent / generation / "data.parquet"
    with data_path.open("ab") as data_file:
        data_file.write(b"corrupt")

    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 102.0


def test_undercovered_manifest_is_a_cache_miss(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream = StubProvider([_history(100.0), _history(103.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    manifest_path = current_path.parent / generation / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["coverage"]["requested_end"] = "2026-10-22"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 103.0