import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = (
    Path(__file__).parents[2]
    / "specs/001-market-leadership-screener/contracts/snapshot-manifest.schema.json"
)
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def valid_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot-2026-10-23",
        "as_of": "2026-10-23",
        "built_at": "2026-10-24T12:00:00Z",
        "ruleset_version": "1",
        "markets": ["US"],
        "tables": [
            {
                "name": "prices",
                "path": "prices.parquet",
                "rows": 1,
                "sha256": "a" * 64,
            }
        ],
        "sources": [
            {
                "source_id": "fixture",
                "name": "Fixture",
                "dataset": "acceptance",
                "version": "1",
                "retrieved_at": "2026-10-24T12:00:00Z",
                "checksum": "b" * 64,
            }
        ],
    }


def test_manifest_accepts_all_required_fields_and_declared_format() -> None:
    errors = list(VALIDATOR.iter_errors(valid_manifest()))

    assert errors == []


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "snapshot_id",
        "as_of",
        "built_at",
        "ruleset_version",
        "markets",
        "tables",
        "sources",
    ],
)
def test_manifest_requires_every_top_level_field(field: str) -> None:
    manifest = valid_manifest()
    del manifest[field]

    assert list(VALIDATOR.iter_errors(manifest))
    assert list(VALIDATOR.iter_errors(manifest))


@pytest.mark.parametrize("field", ["name", "path", "rows", "sha256"])
def test_manifest_requires_every_table_field(field: str) -> None:
    manifest = valid_manifest()
    del manifest["tables"][0][field]

    assert list(VALIDATOR.iter_errors(manifest))


@pytest.mark.parametrize(
    ("field", "invalid_value", "valid_value"),
    [
        ("schema_version", "2.0.0", "1.0.0"),
        ("snapshot_id", "invalid id", "valid-id_1.0"),
        ("as_of", "2026-10-23T00:00:00Z", "2026-10-23"),
        ("built_at", "not-a-date", "2026-10-24T12:00:00Z"),
        ("ruleset_version", "", "1"),
        ("markets", [], ["US"]),
        (
            "tables",
            [],
            [{"name": "prices", "path": "prices.parquet", "rows": 0, "sha256": "a" * 64}],
        ),
        ("sources", [], [valid_manifest()["sources"][0]]),
    ],
)
def test_manifest_enforces_declared_top_level_constraints(
    field: str, invalid_value: object, valid_value: object
) -> None:
    manifest = valid_manifest()
    manifest[field] = invalid_value

    assert list(VALIDATOR.iter_errors(manifest))
    manifest[field] = valid_value
    assert list(VALIDATOR.iter_errors(manifest)) == []


@pytest.mark.parametrize(
    "field", ["source_id", "name", "dataset", "version", "retrieved_at", "checksum"]
)
def test_manifest_requires_every_source_field(field: str) -> None:
    manifest = valid_manifest()
    del manifest["sources"][0][field]

    assert list(VALIDATOR.iter_errors(manifest))


def test_manifest_enforces_table_path_rows_and_checksum_formats() -> None:
    manifest = valid_manifest()
    table = manifest["tables"][0]
    table["path"] = "/absolute/prices.parquet"
    table["rows"] = -1
    table["sha256"] = "g" * 64

    errors = list(VALIDATOR.iter_errors(manifest))

    assert len(errors) == 3


def test_manifest_enforces_source_timestamp_and_checksum_formats() -> None:
    manifest = valid_manifest()
    source = manifest["sources"][0]
    source["retrieved_at"] = "yesterday"
    source["checksum"] = "z" * 64

    assert len(list(VALIDATOR.iter_errors(manifest))) == 2


def test_manifest_rejects_undeclared_top_level_properties() -> None:
    manifest = valid_manifest()
    manifest["unlisted"] = True

    errors = list(VALIDATOR.iter_errors(manifest))

    assert any("Additional properties" in error.message for error in errors)


@pytest.mark.parametrize("collection", ["tables", "sources"])
def test_manifest_rejects_undeclared_nested_properties(collection: str) -> None:
    manifest = valid_manifest()
    manifest[collection][0]["unexpected"] = True

    errors = list(VALIDATOR.iter_errors(manifest))

    assert any("Additional properties" in error.message for error in errors)


def test_manifest_rejects_duplicate_markets_and_invalid_optional_license_label() -> None:
    manifest = valid_manifest()
    manifest["markets"] = ["US", "US"]
    manifest["sources"][0]["license_label"] = 4

    assert len(list(VALIDATOR.iter_errors(manifest))) == 2
