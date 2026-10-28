import hashlib
import json
from datetime import date

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

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


def test_daily_history_fingerprint_covers_provider_and_request_scope() -> None:
    baseline = daily_history_fingerprint(
        provider_id="massive",
        symbols=("SPY",),
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
    )
    assert baseline != daily_history_fingerprint(
        provider_id="yfinance",
        symbols=("SPY",),
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
    )
    assert baseline != daily_history_fingerprint(
        provider_id="massive",
        symbols=("XLB",),
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
    )
    assert baseline != daily_history_fingerprint(
        provider_id="massive",
        symbols=("SPY",),
        start=date(2026, 1, 2),
        end=date(2026, 10, 23),
    )
    assert baseline != daily_history_fingerprint(
        provider_id="massive",
        symbols=("SPY",),
        start=date(2026, 1, 1),
        end=date(2026, 10, 24),
    )


def test_missing_cache_entry_calls_provider_once_and_publishes_entry(tmp_path) -> None:
    upstream = StubProvider([_history(99.0)])

    result = CachedMarketDataProvider(upstream, tmp_path).fetch_daily_history(
        ("SPY",),
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
    )

    assert upstream.calls == 1
    assert result["SPY"].iloc[-1]["close"] == 99.0
    assert len(list(tmp_path.rglob("CURRENT"))) == 1


@pytest.mark.parametrize(
    ("close", "volume"),
    [(-1.0, 1000.0), (100.0, -1.0)],
)
def test_invalid_price_or_volume_is_not_published(tmp_path, close, volume) -> None:
    history = _history(close)
    history["SPY"].loc[:, "volume"] = volume
    upstream = StubProvider([history])

    with pytest.raises(ValueError, match="invalid values"):
        CachedMarketDataProvider(upstream, tmp_path).fetch_daily_history(
            ("SPY",), start=date(2026, 10, 1), end=date(2026, 10, 23)
        )

    assert upstream.calls == 1
    assert not list(tmp_path.rglob("CURRENT"))


def test_cache_manifest_records_complete_normalized_request_and_provenance(tmp_path) -> None:
    request = {
        "symbols": ("spy",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    cached = CachedMarketDataProvider(StubProvider([_history(99.0)]), tmp_path)
    result = cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    manifest_path = current_path.parent / generation / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["provider_id"] == "stub"
    assert manifest["logical_data_point"] == "daily_history"
    assert manifest["request"] == {
        "provider_id": "stub",
        "logical_data_point": "daily_history",
        "schema_version": 4,
        "symbols": ["SPY"],
        "start": "2026-01-01",
        "end": "2026-10-23",
        "frequency": "1d",
        "return_basis": "adjusted",
        "currency_basis": "USD",
    }
    assert manifest["coverage"]["actual_start"] == "2026-10-23"
    assert manifest["coverage"]["actual_end"] == "2026-10-23"
    assert manifest["coverage"]["actual_end_by_symbol"] == {"SPY": "2026-10-23"}
    assert manifest["data_file"] == "data.parquet"
    assert (
        manifest["data_sha256"]
        == hashlib.sha256((manifest_path.parent / manifest["data_file"]).read_bytes()).hexdigest()
    )
    assert tuple(result) == ("SPY",)
    assert result["SPY"].iloc[-1]["close"] == 99.0


def test_fresh_persistent_hit_makes_zero_upstream_calls(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream_result = _history(100.0)
    upstream_result["SPY"].index.name = "Date"
    upstream_result["SPY"].columns.name = "Price"
    initial = StubProvider([upstream_result])
    fresh_result = CachedMarketDataProvider(initial, tmp_path).fetch_daily_history(**request)

    unavailable = StubProvider([RuntimeError("upstream must not be called")])
    cached_result = CachedMarketDataProvider(unavailable, tmp_path).fetch_daily_history(**request)

    assert unavailable.calls == 0
    assert_frame_equal(fresh_result["SPY"], cached_result["SPY"])
    assert cached_result["SPY"].index.name == "date"
    assert cached_result["SPY"].columns.name is None
    assert cached_result["SPY"].iloc[-1]["close"] == 100.0
    assert cached_result["SPY"].attrs == {
        "source_id": "stub",
        "available_on": "2026-10-23",
    }


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


def test_incompatible_manifest_schema_is_a_cache_miss(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream = StubProvider([_history(100.0), _history(105.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    manifest_path = current_path.parent / generation / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = -1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 105.0


def test_incompatible_parquet_schema_is_a_cache_miss(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream = StubProvider([_history(100.0), _history(106.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    generation_dir = current_path.parent / generation
    data_path = generation_dir / "data.parquet"
    pd.DataFrame({"unexpected": [1]}).to_parquet(data_path, index=False)
    manifest_path = generation_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["data_sha256"] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 106.0


def test_incompatible_parquet_column_types_are_a_cache_miss(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    upstream = StubProvider([_history(100.0), _history(107.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    generation_dir = current_path.parent / generation
    data_path = generation_dir / "data.parquet"
    pd.DataFrame(
        {
            "symbol": [7],
            "date": pd.to_datetime(["2026-10-23"]),
            "close": [100.0],
            "volume": [1_000.0],
        }
    ).to_parquet(data_path, index=False)
    manifest_path = generation_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["data_sha256"] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 107.0


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
    manifest["coverage"]["actual_end_by_symbol"]["SPY"] = "2026-10-22"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 103.0


def test_empty_source_response_is_not_a_fresh_coverage_hit(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    empty = {
        "SPY": pd.DataFrame(
            {
                "close": pd.Series(dtype="float64"),
                "volume": pd.Series(dtype="float64"),
            }
        )
    }
    upstream = StubProvider([empty, _history(104.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)

    assert cached.fetch_daily_history(**request)["SPY"].empty
    result = cached.fetch_daily_history(**request)

    assert upstream.calls == 2
    assert result["SPY"].iloc[-1]["close"] == 104.0


def test_failed_atomic_publication_preserves_previous_generation(tmp_path) -> None:
    request = {
        "symbols": ("SPY",),
        "start": date(2026, 1, 1),
        "end": date(2026, 10, 23),
    }
    malformed = {
        "SPY": pd.DataFrame(
            {"close": [200.0]},
            index=pd.to_datetime(["2026-10-23"]),
        )
    }
    upstream = StubProvider([_history(100.0), malformed])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    cached.fetch_daily_history(**request)
    current_path = next(tmp_path.rglob("CURRENT"))
    original_generation = current_path.read_text(encoding="ascii")

    with pytest.raises(ValueError, match="lacks canonical columns"):
        cached.fetch_daily_history(**request, force=True)

    assert current_path.read_text(encoding="ascii") == original_generation
    assert not list(tmp_path.rglob(".publishing-*"))
    assert cached.fetch_daily_history(**request)["SPY"].iloc[-1]["close"] == 100.0


def test_fingerprint_uses_normalized_provider_and_distinguishes_ranges() -> None:
    request = dict(symbols=(" spy ",), start=date(2026, 10, 22), end=date(2026, 10, 23))
    assert daily_history_fingerprint(provider_id=" STUB ", **request) == (
        daily_history_fingerprint(provider_id="stub", **request)
    )
    assert daily_history_fingerprint(provider_id="stub", **request) != (
        daily_history_fingerprint(
            provider_id="stub", symbols=("SPY",), start=request["start"], end=date(2026, 10, 24)
        )
    )


def test_manifest_records_symbol_coverage_and_real_source_availability(tmp_path) -> None:
    first = _history(100.0)["SPY"]
    first.attrs["available_on"] = "2026-10-24"
    response = {
        "SPY": first,
        "XLB": pd.DataFrame(
            {"close": [50.0], "volume": [20.0]}, index=pd.to_datetime(["2026-10-22"])
        ),
    }
    cached = CachedMarketDataProvider(
        StubProvider([response]),
        tmp_path,
        alternatives=("other",),
        selection_reason="priority",
    )
    fresh = cached.fetch_daily_history(
        ("SPY", "XLB"), start=date(2026, 10, 21), end=date(2026, 10, 23)
    )
    current = next(tmp_path.rglob("CURRENT"))
    manifest = json.loads((current.parent / current.read_text() / "manifest.json").read_text())
    assert manifest["coverage"]["actual_start_by_symbol"] == {
        "SPY": "2026-10-23",
        "XLB": "2026-10-22",
    }
    assert manifest["source_availability_by_symbol"] == {"SPY": "2026-10-24", "XLB": "2026-10-22"}
    assert manifest["selection"] == {
        "selected_provider": "stub",
        "alternatives": ["other"],
        "reason": "priority",
    }
    assert fresh["SPY"].attrs["available_on"] == "2026-10-24"


def test_forged_coverage_and_availability_do_not_turn_stale_records_into_hit(tmp_path) -> None:
    stale = {
        "SPY": pd.DataFrame(
            {"close": [10.0], "volume": [1.0]}, index=pd.to_datetime(["2026-10-22"])
        )
    }
    upstream = StubProvider([stale, _history(11.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    request = dict(symbols=("SPY",), start=date(2026, 10, 21), end=date(2026, 10, 23))
    cached.fetch_daily_history(**request)
    current = next(tmp_path.rglob("CURRENT"))
    manifest_path = current.parent / current.read_text() / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["coverage"]["actual_end_by_symbol"]["SPY"] = "2026-10-23"
    manifest["source_availability_by_symbol"]["SPY"] = "2026-10-23"
    manifest_path.write_text(json.dumps(manifest))
    assert cached.fetch_daily_history(**request)["SPY"].iloc[-1]["close"] == 11.0
    assert upstream.calls == 2


@pytest.mark.parametrize(
    "history",
    [
        pd.DataFrame(
            {"close": [1.0, 2.0], "volume": [3.0, 4.0]},
            index=pd.to_datetime(["2026-10-23", "2026-10-23"]),
        ),
        pd.DataFrame({"close": [1.0], "volume": [3.0]}, index=pd.to_datetime(["2026-10-24"])),
        pd.DataFrame(
            {"close": [float("nan")], "volume": [3.0]},
            index=pd.to_datetime(["2026-10-23"]),
        ),
    ],
)
def test_invalid_upstream_records_do_not_replace_generation(tmp_path, history) -> None:
    upstream = StubProvider([_history(100.0), {"SPY": history}])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    request = dict(symbols=("SPY",), start=date(2026, 10, 21), end=date(2026, 10, 23))
    cached.fetch_daily_history(**request)
    current = next(tmp_path.rglob("CURRENT"))
    generation = current.read_text()
    with pytest.raises(ValueError):
        cached.fetch_daily_history(**request, force=True)
    assert current.read_text() == generation
    assert cached.fetch_daily_history(**request)["SPY"].iloc[-1]["close"] == 100.0


def test_failed_pointer_swap_keeps_old_generation_and_cleans_unpublished_data(
    tmp_path, monkeypatch
) -> None:
    import os

    upstream = StubProvider([_history(100.0), _history(101.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    request = dict(symbols=("SPY",), start=date(2026, 10, 21), end=date(2026, 10, 23))
    cached.fetch_daily_history(**request)
    current = next(tmp_path.rglob("CURRENT"))
    generation = current.read_text()
    original_replace = os.replace

    def fail_pointer_swap(source, target):
        if target == current:
            raise OSError("pointer swap failed")
        original_replace(source, target)

    monkeypatch.setattr(os, "replace", fail_pointer_swap)
    with pytest.raises(OSError, match="pointer swap failed"):
        cached.fetch_daily_history(**request, force=True)
    assert current.read_text() == generation
    assert {path.name for path in current.parent.iterdir()} == {"CURRENT", generation}
    assert cached.fetch_daily_history(**request)["SPY"].iloc[-1]["close"] == 100.0


def test_checksum_valid_but_unreadable_parquet_is_a_cache_miss(tmp_path) -> None:
    upstream = StubProvider([_history(100.0), _history(102.0)])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    request = dict(symbols=("SPY",), start=date(2026, 10, 21), end=date(2026, 10, 23))
    cached.fetch_daily_history(**request)
    current = next(tmp_path.rglob("CURRENT"))
    generation_dir = current.parent / current.read_text()
    data_path = generation_dir / "data.parquet"
    data_path.write_bytes(b"not parquet")
    manifest_path = generation_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["data_sha256"] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))

    assert cached.fetch_daily_history(**request)["SPY"].iloc[-1]["close"] == 102.0
    assert upstream.calls == 2


def test_cache_hit_preserves_source_availability_distinct_from_observation(tmp_path) -> None:
    history = _history(100.0)
    history["SPY"].attrs["available_on"] = "2026-10-24"
    upstream = StubProvider([history])
    cached = CachedMarketDataProvider(upstream, tmp_path)
    request = dict(symbols=("SPY",), start=date(2026, 10, 21), end=date(2026, 10, 23))
    fresh = cached.fetch_daily_history(**request)
    hit = cached.fetch_daily_history(**request)
    assert upstream.calls == 1
    assert (
        fresh["SPY"].attrs
        == hit["SPY"].attrs
        == {"source_id": "stub", "available_on": "2026-10-24"}
    )
