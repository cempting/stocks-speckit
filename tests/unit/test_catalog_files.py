import json
import os
from dataclasses import FrozenInstanceError
from datetime import date
from hashlib import sha256
from pathlib import Path

import pytest

from market_leadership.domain.catalog import CatalogError, Scope
from market_leadership.infrastructure import catalog_files
from market_leadership.infrastructure.catalog_files import (
    ARTIFACT_LIMIT,
    CatalogReader,
    load_release,
)

SCOPE = Scope("US", "TEST_CLASSIFICATION", "TEST_VERSION")
AS_OF = date(2026, 10, 30)


def rewrite_artifact(manifest: Path, role: str, content: bytes, count: int | None = None) -> None:
    document = json.loads(manifest.read_text())
    artifact = next(a for a in document["artifacts"] if a["role"] == role)
    (manifest.parent / artifact["path"]).write_bytes(content)
    artifact["sha256"] = sha256(content).hexdigest()
    if count is not None:
        artifact["row_count"] = count
    manifest.write_text(json.dumps(document))


def test_load_projects_exact_membership_and_empty_nodes(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    assert len(snapshot.active_nodes(SCOPE, AS_OF)) == 5
    assert len(snapshot.members(SCOPE, "test-sector", AS_OF)) == 3
    assert len(snapshot.members(SCOPE, "test-cloud", AS_OF)) == 2
    assert len(snapshot.members(SCOPE, "test-specialist", AS_OF)) == 1
    assert snapshot.members(SCOPE, "test-empty", AS_OF) == ()
    assert snapshot.provider_symbols(SCOPE, "test-sector", AS_OF) == (
        "TEST_STOCK_1",
        "TEST_STOCK_2",
    )
    assert snapshot.baskets[0].constituents[0].weight.as_tuple().exponent == -3
    assert snapshot.benchmark("US", "market_sentiment", AS_OF).provider_symbol == "TEST_ETF"
    with pytest.raises(FrozenInstanceError):
        snapshot.catalog_revision = "changed"


@pytest.mark.parametrize(
    "content,code",
    [
        (b"", "invalid_header"),
        (b"NodeId,NodeId\none,two\n", "invalid_header"),
        (b"PRIVATE_HEADER\nPRIVATE_VALUE\n", "invalid_header"),
        (b"\xff", "invalid_utf8"),
    ],
)
def test_strict_csv_headers_and_encoding(catalog_release: Path, content: bytes, code: str) -> None:
    rewrite_artifact(catalog_release, "hierarchy", content)
    with pytest.raises(CatalogError, match=code) as error:
        load_release(catalog_release)
    assert "PRIVATE_VALUE" not in str(error.value)


def test_bom_and_crlf_are_accepted(catalog_release: Path) -> None:
    original = (catalog_release.parent / "hierarchy.csv").read_bytes()
    rewrite_artifact(
        catalog_release, "hierarchy", b"\xef\xbb\xbf" + original.replace(b"\n", b"\r\n")
    )
    assert len(load_release(catalog_release).nodes) == 5


@pytest.mark.parametrize("mutation", ["count", "hash", "required", "scope", "missing"])
def test_registered_artifact_validation(catalog_release: Path, mutation: str) -> None:
    document = json.loads(catalog_release.read_text())
    artifact = document["artifacts"][0]
    if mutation == "missing":
        (catalog_release.parent / artifact["path"]).unlink()
    elif mutation == "count":
        artifact["row_count"] += 1
    elif mutation == "hash":
        artifact["sha256"] = "f" * 64
    elif mutation == "scope":
        artifact["region_id"] = "OTHER"
    else:
        artifact["required"] = False
    catalog_release.write_text(json.dumps(document))
    with pytest.raises(CatalogError):
        load_release(catalog_release)


def test_symlink_escape_is_rejected(catalog_release: Path, tmp_path: Path) -> None:
    artifact = catalog_release.parent / "hierarchy.csv"
    outside = tmp_path / "private.csv"
    artifact.rename(outside)
    artifact.symlink_to(outside)
    with pytest.raises(CatalogError, match="unsafe_path"):
        load_release(catalog_release)


def test_artifact_limit_is_enforced_before_capture(catalog_release: Path) -> None:
    artifact = catalog_release.parent / "hierarchy.csv"
    with artifact.open("wb") as stream:
        stream.truncate(ARTIFACT_LIMIT + 1)
    with pytest.raises(CatalogError, match="input_limit"):
        load_release(catalog_release)


def test_unknown_or_duplicate_ledger_records_fail(catalog_release: Path) -> None:
    path = catalog_release.parent / "governance.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    rewrite_artifact(catalog_release, "audit", b"".join([*lines, lines[0]]), len(lines) + 1)
    with pytest.raises(CatalogError, match="duplicate_record"):
        load_release(catalog_release)


def test_same_size_restored_mtime_corruption_never_uses_cached_success(
    catalog_release: Path, tmp_path: Path
) -> None:
    document = json.loads(catalog_release.read_text())
    document["catalog_revision"] = load_release(catalog_release).catalog_revision
    catalog_release.write_text(json.dumps(document))
    entry = tmp_path / "CURRENT.json"
    entry.write_text(
        json.dumps(
            {
                "format": "market-catalog-entry-1",
                "release_id": "test-release",
                "manifest_path": str(catalog_release.relative_to(tmp_path)),
                "manifest_sha256": sha256(catalog_release.read_bytes()).hexdigest(),
            }
        )
    )
    reader = CatalogReader()
    first = reader.read(entry)
    assert reader.read(entry) is first
    artifact = catalog_release.parent / "hierarchy.csv"
    before = artifact.stat()
    artifact.write_bytes(artifact.read_bytes().replace(b"test-cloud", b"test-clouX"))
    os.utime(artifact, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(CatalogError, match="checksum"):
        reader.read(entry)


def test_unregistered_blank_listing_fields_do_not_create_requests(catalog_release: Path) -> None:
    assert load_release(catalog_release).provider_symbols(SCOPE, "test-cloud", AS_OF) == (
        "TEST_STOCK_1",
    )


def test_before_after_capture_detects_mid_read_edit(
    catalog_release: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = catalog_release.parent / "hierarchy.csv"
    original = catalog_files._identity
    observations = 0

    def edited_identity(path: Path) -> catalog_files.FileIdentity:
        nonlocal observations
        if path == artifact:
            observations += 1
            if observations == 2:
                artifact.write_bytes(artifact.read_bytes().replace(b"test-cloud", b"test-clouX"))
        return original(path)

    monkeypatch.setattr(catalog_files, "_identity", edited_identity)
    with pytest.raises(CatalogError, match="concurrent_edit"):
        load_release(catalog_release)


def test_checked_in_reviewed_fixture_has_controlled_exact_output() -> None:
    manifest = Path(__file__).parents[1] / "fixtures/catalogs/reviewed-us/manifest.json"
    snapshot = load_release(manifest)
    assert len(snapshot.nodes) == 4
    assert len(snapshot.stocks) == 2
    assert snapshot.provider_symbols(SCOPE, "test-sector", AS_OF) == ("TEST_STOCK_1",)
    assert snapshot.baskets[0].constituents[0].weight == 100
