import json
from datetime import date

import pandas as pd
import pytest

from market_leadership.infrastructure.parquet_provider import ParquetSnapshotProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.snapshot_errors import (
    IntegrityError,
    SchemaMismatch,
    SnapshotNotFound,
)


def _source() -> dict[str, str | None]:
    return {
        "source_id": "fixture",
        "name": "Fixture data",
        "dataset": "prices",
        "version": "1",
        "retrieved_at": "2026-10-24T12:00:00Z",
        "checksum": "a" * 64,
        "license_label": None,
    }


def _publish(repository: ParquetSnapshotRepository, snapshot_id: str = "snapshot-1"):
    return repository.publish(
        snapshot_id=snapshot_id,
        as_of=date(2026, 10, 23),
        markets=("US",),
        ruleset_version="1",
        tables={
            "prices": pd.DataFrame(
                {
                    "symbol": ["SPY"],
                    "date": [date(2026, 10, 23)],
                    "close": [100.0],
                    "volume": [1_000.0],
                }
            )
        },
        sources=(_source(),),
    )


def test_snapshot_repository_publishes_atomically_and_loads_verified_parquet(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)

    reference = _publish(repository)
    loaded = repository.load("snapshot-1")

    assert reference.snapshot_id == "snapshot-1"
    assert reference.as_of == date(2026, 10, 23)
    assert len(reference.manifest_checksum) == 64
    assert loaded["prices"].to_dict(orient="records") == [
        {
            "symbol": "SPY",
            "date": date(2026, 10, 23),
            "close": 100.0,
            "volume": 1_000.0,
        }
    ]
    assert repository.load_latest() == reference
    assert not list(tmp_path.glob(".publishing-*"))


def test_snapshot_repository_rejects_republication_and_unsafe_ids(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository)

    with pytest.raises(IntegrityError, match="immutable"):
        _publish(repository)
    with pytest.raises(ValueError, match="invalid snapshot ID"):
        repository.load("../outside")


def test_snapshot_repository_rejects_invalid_manifest_schema(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository)
    manifest_path = tmp_path / "snapshot-1" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["unlisted"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SchemaMismatch, match="Additional properties"):
        repository.load("snapshot-1")


def test_snapshot_repository_rejects_table_checksum_mismatch(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository)
    table_path = tmp_path / "snapshot-1" / "prices.parquet"
    table_path.write_bytes(table_path.read_bytes() + b"bad")

    with pytest.raises(IntegrityError, match="checksum"):
        repository.load("snapshot-1")


def test_snapshot_repository_reports_missing_snapshots(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)

    with pytest.raises(SnapshotNotFound, match="manifest"):
        repository.load_latest()


def test_parquet_provider_returns_canonical_filtered_price_history(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    repository.publish(
        snapshot_id="provider-snapshot",
        as_of=date(2026, 10, 23),
        markets=("US",),
        ruleset_version="1",
        tables={
            "prices": pd.DataFrame(
                {
                    "symbol": ["SPY", "SPY"],
                    "date": [date(2026, 10, 22), date(2026, 10, 24)],
                    "close": [100.0, 102.0],
                    "volume": [1_000.0, 1_200.0],
                }
            )
        },
        sources=(_source(),),
    )
    provider = ParquetSnapshotProvider(tmp_path, "provider-snapshot")

    result = provider.fetch_daily_history(
        ("SPY", "XLB"),
        start=date(2026, 10, 1),
        end=date(2026, 10, 23),
    )

    assert result["SPY"].to_dict(orient="records") == [{"close": 100.0, "volume": 1_000.0}]
    assert result["XLB"].empty
    assert result["SPY"].attrs["source_id"] == "parquet"
