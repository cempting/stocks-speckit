import copy
import json
from collections.abc import Callable
from importlib.resources import files
from pathlib import Path
from typing import Literal

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from market_data.catalog import load_release
from market_data.domain.catalog import CatalogError


def contract_schema() -> dict[str, object]:
    path = Path(__file__).parents[2] / (
        "specs/010-manifest-csv-catalogs/contracts/catalog-manifest.schema.json"
    )
    return json.loads(path.read_text())


def validator() -> Draft202012Validator:
    schema = contract_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_packaged_schema_matches_contract() -> None:
    resource = files("market_data.schemas").joinpath("catalog-manifest.schema.json")
    assert json.loads(resource.read_text()) == contract_schema()


def test_controlled_release_schema(catalog_release: Path) -> None:
    validator().validate(json.loads(catalog_release.read_text()))


@pytest.mark.parametrize(
    "path",
    [
        "/outside.json",
        "../outside.json",
        "nested/../outside.json",
        "nested\\outside.json",
        "https://example.invalid/manifest.json",
        "C:/outside.json",
    ],
)
def test_entry_rejects_unsafe_path(path: str) -> None:
    entry = {
        "format": "market-catalog-entry-1",
        "release_id": "test",
        "manifest_path": path,
        "manifest_sha256": "a" * 64,
    }
    assert not validator().is_valid(entry)


@pytest.mark.parametrize(
    "key,value",
    [
        ("format", "market-catalog-entry-2"),
        ("release_id", ""),
        ("manifest_sha256", "a" * 63),
        ("manifest_sha256", "A" * 64),
        ("manifest_sha256", "a" * 64 + "\n"),
        ("unknown", True),
    ],
)
def test_entry_rejects_invalid_shape(key: str, value: object) -> None:
    entry = {
        "format": "market-catalog-entry-1",
        "release_id": "test",
        "manifest_path": "releases/test/manifest.json",
        "manifest_sha256": "a" * 64,
    }
    entry[key] = value
    assert not validator().is_valid(entry)


@pytest.mark.parametrize(
    "key,value",
    [
        ("created_at", "2026-10-31T01:00:00+01:00"),
        ("created_at", "not-a-time"),
        ("artifacts", []),
        ("catalog_revision", ""),
    ],
)
def test_release_rejects_invalid_shape(catalog_release: Path, key: str, value: object) -> None:
    release = json.loads(catalog_release.read_text())
    release[key] = value
    assert not validator().is_valid(release)


def test_release_rejects_duplicate_audit(catalog_release: Path) -> None:
    release = json.loads(catalog_release.read_text())
    release["artifacts"].append(copy.deepcopy(release["artifacts"][-1]))
    assert not validator().is_valid(release)


@pytest.mark.parametrize(
    "key,value",
    [
        ("row_count", -1),
        ("row_count", True),
        ("required", False),
        ("role", "research"),
        ("region_id", ""),
        ("classification_id", ""),
        ("classification_version", ""),
        ("path", "../private.csv"),
        ("sha256", "A" * 64),
        ("extra", "private"),
    ],
)
def test_artifact_rejects_invalid_shape(catalog_release: Path, key: str, value: object) -> None:
    release = json.loads(catalog_release.read_text())
    release["artifacts"][0][key] = value
    assert not validator().is_valid(release)


def test_research_is_optional_and_blank_scope_is_not_null(catalog_release: Path) -> None:
    release = json.loads(catalog_release.read_text())
    assert validator().is_valid(release)
    release["research_sources"][0]["required"] = True
    assert not validator().is_valid(release)


@pytest.mark.parametrize(
    "scenario", ["reviewed", "invalid-count", "invalid-reference", "research-partial"]
)
def test_controlled_factory_variants_are_isolated_and_truthful(
    catalog_factory: Callable[
        [Literal["reviewed", "invalid-count", "invalid-reference", "research-partial"]], Path
    ],
    scenario: Literal["reviewed", "invalid-count", "invalid-reference", "research-partial"],
) -> None:
    manifest = catalog_factory(scenario)
    assert manifest.is_absolute()
    if scenario.startswith("invalid"):
        with pytest.raises(CatalogError):
            load_release(manifest)
    else:
        snapshot = load_release(manifest)
        assert snapshot.release.regions[0].coverage_state == "partial"
        assert snapshot.nodes
        if scenario == "research-partial":
            assert snapshot.release.research_sources
            assert any(
                not Path(source.root).exists() for source in snapshot.release.research_sources
            )


def test_captured_artifacts_match_registered_bytes_and_identity(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    captured = dict(snapshot.captured)
    assert len(captured) == len(snapshot.release.artifacts)
    for artifact in snapshot.release.artifacts:
        assert captured[artifact.path] == (catalog_release.parent / artifact.path).read_bytes()
    assert snapshot.manifest_path == catalog_release


def test_reader_rejects_duplicate_manifest_keys_before_validation(catalog_release: Path) -> None:
    catalog_release.write_text('{"format":"one","format":"two"}')
    with pytest.raises(CatalogError, match="duplicate_key"):
        load_release(catalog_release)
