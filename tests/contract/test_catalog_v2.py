import csv
import json
from datetime import date
from hashlib import sha256
from pathlib import Path

import pytest

from market_data.catalog import (
    ARTIFACT_LIMIT,
    RECORD_LIMIT,
    load_release,
)
from market_data.domain.catalog import CatalogError
from tests.membership_helpers import V2_STOCK_HEADERS, build_v2_release, membership_fixture


def _rewrite_artifact(manifest: Path, role: str, content: bytes) -> None:
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact = next(item for item in document["artifacts"] if item["role"] == role)
    (manifest.parent / artifact["path"]).write_bytes(content)
    artifact["sha256"] = sha256(content).hexdigest()
    artifact["row_count"] = max(0, len(content.splitlines()) - 1)
    manifest.write_text(json.dumps(document), encoding="utf-8")


def _edit_stock_rows(manifest: Path, edit) -> None:
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact = next(item for item in document["artifacts"] if item["role"] == "stocks")
    path = manifest.parent / artifact["path"]
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        headers = reader.fieldnames
    assert headers is not None
    edit(rows)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    content = path.read_bytes()
    artifact["sha256"] = sha256(content).hexdigest()
    artifact["row_count"] = len(rows)
    manifest.write_text(json.dumps(document), encoding="utf-8")


def _v2_manifest(catalog_release: Path, tmp_path: Path) -> Path:
    return build_v2_release(
        catalog_release,
        tmp_path / "v2-release",
        membership_fixture(deep_levels=4),
    )


def test_v1_is_preserved_and_v2_is_explicitly_dispatched(
    catalog_release: Path, tmp_path: Path
) -> None:
    v1 = load_release(catalog_release)
    v2 = load_release(_v2_manifest(catalog_release, tmp_path))

    assert v1.release.format == "market-catalog-release-1"
    assert v2.release.format == "market-catalog-release-2"


def test_v1_stock_rows_and_inventory_use_shared_identity_projections(
    catalog_release: Path,
) -> None:
    snapshot = load_release(catalog_release)
    unclassified = snapshot.lookup_instruments("US", "test-unclassified-stock")
    classified = snapshot.lookup_instruments("US", "test-stock-1")

    assert len(unclassified) == 1
    assert unclassified[0].memberships == ()
    assert unclassified[0].listings[0].listing_id == "test-inventory-listing"
    assert len(classified) == 1
    assert classified[0].memberships[0].membership_id == "test-membership-1"


@pytest.mark.parametrize(
    "mutation",
    [
        "classification-kind",
        "artifact-scope",
        "unknown-format",
        "duplicate-json-key",
        "unknown-field",
    ],
)
def test_v2_manifest_contract_is_strict(
    catalog_release: Path, tmp_path: Path, mutation: str
) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)
    document = json.loads(manifest.read_text(encoding="utf-8"))
    if mutation == "classification-kind":
        del document["regions"][0]["classifications"][0]["scheme_kind"]
        manifest.write_text(json.dumps(document), encoding="utf-8")
    elif mutation == "artifact-scope":
        artifact = next(item for item in document["artifacts"] if item["role"] == "stocks")
        artifact["classification_id"] = "CUSTOM-FIXTURE"
        manifest.write_text(json.dumps(document), encoding="utf-8")
    elif mutation == "unknown-format":
        document["format"] = "market-catalog-release-3"
        manifest.write_text(json.dumps(document), encoding="utf-8")
    elif mutation == "unknown-field":
        document["unexpected"] = True
        manifest.write_text(json.dumps(document), encoding="utf-8")
    else:
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                '"release_id": "test-release"',
                '"release_id": "test-release", "release_id": "duplicate"',
                1,
            ),
            encoding="utf-8",
        )
    with pytest.raises(CatalogError):
        load_release(manifest)


def test_v2_requires_exact_stock_header_and_does_not_retry_as_v1(
    catalog_release: Path, tmp_path: Path
) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact = next(item for item in document["artifacts"] if item["role"] == "stocks")
    path = manifest.parent / artifact["path"]
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=(*V2_STOCK_HEADERS, "Unknown"))
        writer.writeheader()
        writer.writerows(rows)
    content = path.read_bytes()
    artifact["sha256"] = sha256(content).hexdigest()
    artifact["row_count"] = len(rows)
    manifest.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(CatalogError, match="invalid_header"):
        load_release(manifest)


def test_v2_stock_grammar_rejects_membership_fields_on_instrument_rows(
    catalog_release: Path, tmp_path: Path
) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact = next(item for item in document["artifacts"] if item["role"] == "stocks")
    path = manifest.parent / artifact["path"]
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        headers = reader.fieldnames
    assert headers is not None
    rows[0]["MembershipId"] = "fabricated"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    _rewrite_artifact(manifest, "stocks", path.read_bytes())

    with pytest.raises(CatalogError):
        load_release(manifest)


@pytest.mark.parametrize(
    "field,value",
    [
        ("IsPrimary", "yes"),
        ("MembershipEffectiveFrom", "not-a-date"),
        ("Currency", "usd"),
    ],
)
def test_v2_rejects_invalid_typed_cells(
    catalog_release: Path, tmp_path: Path, field: str, value: str
) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)

    def edit(rows: list[dict[str, str]]) -> None:
        membership = next(row for row in rows if row["RowKind"] == "membership")
        membership[field] = value

    _edit_stock_rows(manifest, edit)
    with pytest.raises(CatalogError):
        load_release(manifest)


def test_v2_rejects_duplicate_stock_headers(catalog_release: Path, tmp_path: Path) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact = next(item for item in document["artifacts"] if item["role"] == "stocks")
    path = manifest.parent / artifact["path"]
    content = path.read_bytes().replace(b"IndustryId", b"InstrumentId", 1)
    _rewrite_artifact(manifest, "stocks", content)

    with pytest.raises(CatalogError, match="invalid_header"):
        load_release(manifest)


def test_v2_enforces_manifest_and_artifact_size_limits(
    catalog_release: Path, tmp_path: Path
) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)
    document = json.loads(manifest.read_text(encoding="utf-8"))
    artifact = next(item for item in document["artifacts"] if item["role"] == "hierarchy")
    (manifest.parent / artifact["path"]).write_bytes(b"")
    with (manifest.parent / artifact["path"]).open("wb") as stream:
        stream.truncate(ARTIFACT_LIMIT + 1)
    with pytest.raises(CatalogError, match="input_limit"):
        load_release(manifest)

    manifest.write_bytes(b" " * (RECORD_LIMIT + 1))
    with pytest.raises(CatalogError, match="input_limit"):
        load_release(manifest)


def test_v2_projections_keep_unassigned_stock_and_separate_listing_and_membership(
    catalog_release: Path, tmp_path: Path
) -> None:
    snapshot = load_release(_v2_manifest(catalog_release, tmp_path))
    unassigned = snapshot.lookup_instruments("US", "unassigned")
    placeholder = snapshot.lookup_instruments("US", "placeholder")
    share_class = next(
        member
        for member in snapshot.catalog_members
        if member.instrument.instrument_id == "share-class-a"
    )
    unverified = next(
        member
        for member in snapshot.catalog_members
        if member.instrument.instrument_id == "unverified-listing"
    )

    assert len(unassigned) == 1
    assert unassigned[0].memberships == ()
    assert unassigned[0].listings == ()
    assert placeholder == ()
    assert unverified.listings[0].resolution_state == "unverified"
    assert snapshot.listing_for_instrument(
        "US", "unverified-listing", date(2026, 10, 30)
    ).reason == "listing_unverified"
    assert snapshot.listing_for_instrument(
        "US", "share-class-a", date(2026, 10, 30)
    ).state == "ambiguous"
    assert snapshot.listing_for_instrument(
        "US",
        "share-class-a",
        date(2026, 10, 30),
        listing_id="listing-a-primary",
    ).state == "available"
    assert {item.membership_id for item in share_class.memberships} == {
        "membership-parent",
        "membership-child",
        "membership-cross-sector",
    }
    assert {item.listing_id for item in share_class.listings} == {
        "listing-a-primary",
        "listing-a-secondary",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-row-id",
        "duplicate-pairing",
        "conflicting-membership-copy",
        "conflicting-instrument-metadata",
        "conflicting-listing-copy",
        "overlapping-primary",
        "ambiguous-symbol",
    ],
)
def test_v2_rejects_duplicate_or_conflicting_identities(
    catalog_release: Path, tmp_path: Path, mutation: str
) -> None:
    manifest = _v2_manifest(catalog_release, tmp_path)

    def edit(rows: list[dict[str, str]]) -> None:
        parent_copy = next(row for row in rows if row["RowId"] == "membership-parent-copy")
        if mutation == "duplicate-row-id":
            parent_copy["RowId"] = "membership-parent"
        elif mutation == "duplicate-pairing":
            parent_copy["ListingId"] = "listing-a-primary"
        elif mutation == "conflicting-membership-copy":
            parent_copy["IndustryId"] = "industry-b"
        elif mutation == "conflicting-instrument-metadata":
            parent_copy["CompanyId"] = "different-company"
        elif mutation == "conflicting-listing-copy":
            parent_copy["Ticker"] = "DIFFERENT_TICKER"
        elif mutation == "overlapping-primary":
            for row in rows:
                if row["ListingId"] == "listing-a-secondary":
                    row["IsPrimary"] = "true"
        elif mutation == "ambiguous-symbol":
            next(row for row in rows if row["ListingId"] == "listing-b")[
                "ProviderSymbol"
            ] = "FIXTURE"

    _edit_stock_rows(manifest, edit)
    with pytest.raises(CatalogError):
        load_release(manifest)
