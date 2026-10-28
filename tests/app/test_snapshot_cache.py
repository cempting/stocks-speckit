from datetime import date

import pandas as pd

from market_leadership.application.ports import DataPointRequest, SnapshotReference
from market_leadership.infrastructure.market_data_cache import CachedMarketDataProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.ui.cache import (
    clear_snapshot_cache,
    load_snapshot_tables,
    refresh_market_data,
)


def _publish_snapshot(root, snapshot_id: str = "cache-test") -> SnapshotReference:
    repository = ParquetSnapshotRepository(root)
    return repository.publish(
        snapshot_id=snapshot_id,
        as_of=date(2026, 10, 23),
        markets=("US",),
        ruleset_version="1",
        tables={"prices": pd.DataFrame({"symbol": ["SPY"], "close": [100.0]})},
        sources=(
            {
                "source_id": "fixture",
                "name": "Fixture",
                "dataset": "prices",
                "version": "1",
                "retrieved_at": "2026-10-24T12:00:00Z",
                "checksum": "a" * 64,
                "license_label": None,
            },
        ),
    )


def test_snapshot_cache_loads_once_per_snapshot_and_manifest_checksum(
    tmp_path, monkeypatch
) -> None:
    reference = _publish_snapshot(tmp_path)
    original_load = ParquetSnapshotRepository.load
    load_calls: list[str] = []

    def counting_load(repository, snapshot_id: str):
        load_calls.append(snapshot_id)
        return original_load(repository, snapshot_id)

    monkeypatch.setattr(ParquetSnapshotRepository, "load", counting_load)
    clear_snapshot_cache()
    filters = {"market": "US"}

    first = load_snapshot_tables(tmp_path, reference.snapshot_id, reference.manifest_checksum)
    first["prices"].loc[0, "close"] = -1
    filters["market"] = "CA"
    second = load_snapshot_tables(tmp_path, reference.snapshot_id, reference.manifest_checksum)

    assert load_calls == [reference.snapshot_id]
    assert second["prices"].loc[0, "close"] == 100.0
    assert filters == {"market": "CA"}


def test_changed_manifest_checksum_invalidates_cached_snapshot(tmp_path, monkeypatch) -> None:
    clear_snapshot_cache()
    published_checksum = {"value": "a" * 64}
    loads: list[str] = []

    def reference(repository, snapshot_id: str) -> SnapshotReference:
        return SnapshotReference(
            snapshot_id,
            date(2026, 10, 23),
            published_checksum["value"],
        )

    def load(repository, snapshot_id: str) -> dict[str, pd.DataFrame]:
        loads.append(snapshot_id)
        return {"prices": pd.DataFrame({"close": [float(len(loads))]})}

    monkeypatch.setattr(ParquetSnapshotRepository, "reference", reference)
    monkeypatch.setattr(ParquetSnapshotRepository, "load", load)

    first = load_snapshot_tables(tmp_path, "same-snapshot", published_checksum["value"])
    repeated = load_snapshot_tables(tmp_path, "same-snapshot", published_checksum["value"])
    published_checksum["value"] = "b" * 64
    changed = load_snapshot_tables(tmp_path, "same-snapshot", published_checksum["value"])

    assert loads == ["same-snapshot", "same-snapshot"]
    assert first["prices"].loc[0, "close"] == 1.0
    assert repeated["prices"].loc[0, "close"] == 1.0
    assert changed["prices"].loc[0, "close"] == 2.0


def test_snapshot_load_reruns_never_call_upstream_provider(tmp_path, monkeypatch) -> None:
    reference = _publish_snapshot(tmp_path)
    upstream_calls = 0

    def count_upstream_calls(*args, **kwargs):
        nonlocal upstream_calls
        upstream_calls += 1
        return {}

    monkeypatch.setattr(CachedMarketDataProvider, "fetch_daily_history", count_upstream_calls)
    clear_snapshot_cache()
    load_snapshot_tables(tmp_path, reference.snapshot_id, reference.manifest_checksum)
    load_snapshot_tables(tmp_path, reference.snapshot_id, reference.manifest_checksum)

    assert upstream_calls == 0


def test_explicit_refresh_delegates_once_to_request_use_case() -> None:
    request = DataPointRequest(
        data_point="daily_history",
        market_id="US",
        identifiers=("SPY",),
        frequency="1d",
        start=date(2026, 10, 1),
        end=date(2026, 10, 23),
        currency="USD",
        return_basis="adjusted",
    )

    class RequestSpy:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, received_request: DataPointRequest, *, force: bool = False) -> str:
            self.calls += 1
            assert received_request is request
            assert force is True
            return "refreshed"

    request_use_case = RequestSpy()

    result = refresh_market_data(request_use_case, request)

    assert result == "refreshed"
    assert request_use_case.calls == 1
