import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.snapshot_errors import (
    IntegrityError,
    SchemaMismatch,
    SnapshotNotFound,
)

SCHEMA = json.loads(
    (
        Path(__file__).parents[2]
        / "specs/001-market-leadership-screener/contracts/weekly-snapshot-manifest.schema.json"
    ).read_text(encoding="utf-8")
)
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def _source() -> dict[str, str | None]:
    return {
        "source_id": "fixture",
        "name": "Fixture",
        "dataset": "weekly-leadership",
        "version": "1",
        "retrieved_at": "2026-10-24T12:00:00Z",
        "checksum": "a" * 64,
        "license_label": None,
    }


def _table(market_id: str = "US", level: str = "SECTOR") -> pd.DataFrame:
    return pd.DataFrame(
        {"market_id": [market_id], "level": [level], "node_id": ["technology"], "rank": [1]}
    )


def _publish(
    repository: ParquetSnapshotRepository,
    snapshot_id: str = "weekly-1",
    *,
    market_id: str = "US",
    level: str = "SECTOR",
    as_of: date = date(2026, 10, 23),
    tables: dict[str, pd.DataFrame] | None = None,
):
    return repository.publish_weekly(
        snapshot_id=snapshot_id,
        market_id=market_id,
        level=level,
        as_of=as_of,
        benchmark_id="SPY",
        currency="USD",
        return_basis="total_return",
        classification_version="gics-2026",
        representation_version="etf-2026",
        ruleset_version="2",
        tables={"leadership": _table(market_id, level)} if tables is None else tables,
        sources=(_source(),),
    )


def test_weekly_publish_load_and_latest_are_isolated_from_daily(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository)
    later = _publish(repository, "weekly-2", as_of=date(2026, 10, 30))
    _publish(repository, "jp-weekly", market_id="JP", as_of=date(2026, 10, 31))
    _publish(repository, "industry-weekly", level="INDUSTRY", as_of=date(2026, 10, 31))
    repository.publish(
        snapshot_id="daily",
        as_of=date(2026, 11, 1),
        markets=("US",),
        ruleset_version="1",
        tables={"prices": pd.DataFrame({"close": [100.0]})},
        sources=(_source(),),
    )

    manifest, tables = repository.load_weekly("weekly-1")

    assert manifest["schema_version"] == "weekly-1.0.0"
    assert manifest["market_id"] == "US"
    assert manifest["level"] == "SECTOR"
    assert manifest["benchmark_id"] == "SPY"
    assert manifest["sources"] == [_source()]
    assert not list(VALIDATOR.iter_errors(manifest))
    pd.testing.assert_frame_equal(tables["leadership"], _table())
    assert repository.load_latest_weekly("US", "SECTOR") == later
    assert repository.load_latest_weekly("JP", "SECTOR").snapshot_id == "jp-weekly"
    assert repository.load_latest_weekly("US", "INDUSTRY").snapshot_id == "industry-weekly"
    assert repository.load_latest().snapshot_id == "daily"
    assert (
        later.manifest_checksum == repository.load_latest_weekly("US", "SECTOR").manifest_checksum
    )
    assert not list((tmp_path / "weekly").glob(".publishing-*"))


def test_weekly_rejects_daily_manifest_and_missing_scope(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    repository.publish(
        snapshot_id="daily",
        as_of=date(2026, 10, 23),
        markets=("US",),
        ruleset_version="1",
        tables={"prices": pd.DataFrame({"close": [100.0]})},
        sources=(_source(),),
    )
    with pytest.raises((SchemaMismatch, SnapshotNotFound)):
        repository.load_weekly("daily")
    with pytest.raises(SnapshotNotFound):
        repository.load_latest_weekly("US", "SECTOR")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"level": "COUNTRY"}, "level"),
        ({"market_id": ""}, "market"),
        ({"tables": {"leadership": _table("JP")}}, "market"),
        ({"tables": {"leadership": _table("US", "INDUSTRY")}}, "level"),
        ({"tables": {"leadership": pd.DataFrame({"node_id": ["a"]})}}, "market_id"),
        (
            {
                "tables": {
                    "leadership": pd.DataFrame(
                        {"market_id": ["US", "JP"], "level": ["SECTOR", "SECTOR"]}
                    )
                }
            },
            "market",
        ),
    ],
)
def test_weekly_rejects_malformed_or_cross_market_data(tmp_path, kwargs, message) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository, "good")
    with pytest.raises((ValueError, SchemaMismatch), match=message):
        _publish(repository, "bad", **kwargs)
    assert repository.load_weekly("good")[0]["snapshot_id"] == "good"
    assert not (tmp_path / "weekly" / "bad").exists()


def test_weekly_immutable_and_detects_tampering_without_fallback(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository, "good")
    _publish(repository, "bad", as_of=date(2026, 10, 30))
    with pytest.raises(IntegrityError, match="immutable"):
        _publish(repository, "good")
    path = tmp_path / "weekly" / "bad" / "leadership.parquet"
    path.write_bytes(path.read_bytes() + b"bad")
    with pytest.raises(IntegrityError, match="checksum"):
        repository.load_weekly("bad")
    with pytest.raises(IntegrityError, match="checksum"):
        repository.load_latest_weekly("US", "SECTOR")
    assert repository.load_weekly("good")[0]["snapshot_id"] == "good"


def test_weekly_rejects_duplicate_scope_and_preserves_prior_snapshot(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository, "original")

    with pytest.raises(IntegrityError, match="already published"):
        _publish(repository, "duplicate")

    assert repository.load_weekly("original")[0]["as_of"] == "2026-10-23"
    assert not (tmp_path / "weekly" / "duplicate").exists()


@pytest.mark.parametrize("tamper", ["rows", "columns", "scope", "version", "path"])
def test_weekly_rejects_manifest_tampering(tmp_path, tamper) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    _publish(repository)
    path = tmp_path / "weekly" / "weekly-1" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if tamper == "rows":
        manifest["tables"][0]["rows"] = 2
    elif tamper == "columns":
        manifest["tables"][0]["columns"][0]["dtype"] = "int64"
    elif tamper == "scope":
        manifest["market_id"] = "JP"
    elif tamper == "version":
        manifest["schema_version"] = "1.0.0"
    else:
        manifest["tables"][0]["path"] = "../escape.parquet"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises((IntegrityError, SchemaMismatch)):
        repository.load_weekly("weekly-1")
