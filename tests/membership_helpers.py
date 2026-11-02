"""Deterministic catalog fixtures for stock identity and membership tests."""

import csv
import json
import shutil
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Final

V2_STOCK_HEADERS: Final = (
    "RowId",
    "RowKind",
    "MembershipId",
    "RegionId",
    "ClassificationId",
    "ClassificationVersion",
    "InstrumentId",
    "CompanyId",
    "Name",
    "IndustryId",
    "ResolutionState",
    "MembershipEffectiveFrom",
    "MembershipEffectiveTo",
    "MembershipSourceId",
    "MembershipApprovalReference",
    "MembershipReviewState",
    "ListingId",
    "Ticker",
    "ProviderSymbol",
    "Exchange",
    "Currency",
    "IsPrimary",
    "ListingResolutionState",
    "ListingEffectiveFrom",
    "ListingEffectiveTo",
    "ListingSourceId",
    "ListingApprovalReference",
)


@dataclass(frozen=True)
class MembershipFixture:
    hierarchy: tuple[dict[str, str], ...]
    stocks: tuple[dict[str, str], ...]


def build_v1_release(source_manifest: Path, output_directory: Path) -> Path:
    """Copy a controlled v1 release into a fresh, isolated fixture directory."""
    shutil.copytree(source_manifest.parent, output_directory)
    return output_directory / source_manifest.name


def membership_fixture(*, deep_levels: int = 1_050) -> MembershipFixture:
    """Build deterministic overlap, identity, temporal and deep-tree source rows."""
    hierarchy: list[dict[str, str]] = []

    def add_node(
        node_id: str,
        node_type: str,
        sector_id: str,
        parent_id: str = "",
        start: str = "2020-01-01",
        end: str = "",
    ) -> None:
        hierarchy.append(
            {
                "RegionId": "US",
                "ClassificationId": "TEST_CLASSIFICATION",
                "ClassificationVersion": "TEST_VERSION",
                "NodeId": node_id,
                "NodeType": node_type,
                "Name": node_id,
                "SectorId": sector_id,
                "ParentIndustryId": parent_id,
                "EffectiveFrom": start,
                "EffectiveTo": end,
                "SourceId": "test-source",
                "ApprovalReference": "test-approval",
                "ApprovalOrigin": "own",
            }
        )

    add_node("sector-a", "sector", "sector-a")
    add_node("sector-b", "sector", "sector-b")
    add_node("industry-a", "industry", "sector-a")
    add_node("industry-b", "industry", "sector-a")
    add_node("industry-c", "industry", "sector-b")
    add_node("empty-industry", "industry", "sector-a")
    add_node("nested-2", "industry", "sector-a", "industry-a")
    add_node("nested-3", "sub_industry", "sector-a", "nested-2")
    add_node("nested-4", "industry", "sector-a", "nested-3")
    add_node("reparented", "industry", "sector-a", "industry-a", "2020-01-01", "2024-12-31")
    add_node("reparented", "industry", "sector-a", "industry-b", "2025-01-01")
    add_node("test-sector", "sector", "test-sector")
    add_node("test-cloud", "industry", "test-sector")
    add_node("test-hardware", "industry", "test-sector")
    add_node("test-empty", "industry", "test-sector")
    add_node("test-specialist", "sub_industry", "test-sector", "test-cloud")
    parent = "industry-a"
    for level in range(2, deep_levels + 1):
        node_id = f"deep-{level:04d}"
        add_node(node_id, "industry", "sector-a", parent)
        parent = node_id

    stocks = (
        _stock_row(
            "instrument-unassigned",
            "instrument",
            "",
            "unassigned",
            "",
            "",
            resolution_state="identified",
        ),
        _stock_row(
            "instrument-placeholder",
            "instrument",
            "",
            "placeholder",
            "",
            "",
            company_id="",
        ),
        _stock_row(
            "instrument-unverified-listing",
            "instrument",
            "",
            "unverified-listing",
            "",
            "listing-unverified",
            resolution_state="identified",
            listing_state="unverified",
            ticker="FIXTURE_UNVERIFIED",
            provider_symbol="FIXTURE_UNVERIFIED",
        ),
        _stock_row(
            "membership-parent",
            "membership",
            "membership-parent",
            "share-class-a",
            "industry-a",
            "listing-a-primary",
            company_id="",
        ),
        _stock_row(
            "membership-child",
            "membership",
            "membership-child",
            "share-class-a",
            "nested-3",
            "listing-a-secondary",
            company_id="",
            ticker="FIXTURE.A2",
            provider_symbol="FIXTURE.A2",
            primary="false",
        ),
        _stock_row(
            "membership-parent-copy",
            "membership",
            "membership-parent",
            "share-class-a",
            "industry-a",
            "listing-a-secondary",
            company_id="",
            ticker="FIXTURE.A2",
            provider_symbol="FIXTURE.A2",
            primary="false",
        ),
        _stock_row(
            "membership-cross-sector",
            "membership",
            "membership-cross-sector",
            "share-class-a",
            "industry-c",
            "listing-a-primary",
            company_id="",
        ),
        _stock_row(
            "membership-share-class",
            "membership",
            "membership-share-class",
            "share-class-b",
            "industry-b",
            "listing-b",
            company_id="company-reviewed",
            ticker="FIXTURE_B",
            provider_symbol="FIXTURE_B",
        ),
        _stock_row(
            "membership-inclusive-end",
            "membership",
            "membership-inclusive-end",
            "share-class-c",
            "industry-b",
            "",
            start="2024-12-31",
            end="2024-12-31",
        ),
    )
    return MembershipFixture(tuple(hierarchy), stocks)


def _stock_row(
    row_id: str,
    row_kind: str,
    membership_id: str,
    instrument_id: str,
    industry_id: str,
    listing_id: str,
    *,
    company_id: str = "",
    ticker: str = "FIXTURE",
    provider_symbol: str = "FIXTURE",
    primary: str = "true",
    resolution_state: str | None = None,
    listing_state: str = "verified",
    start: str = "2020-01-01",
    end: str = "",
) -> dict[str, str]:
    row = dict.fromkeys(V2_STOCK_HEADERS, "")
    row.update(
        {
            "RowId": row_id,
            "RowKind": row_kind,
            "MembershipId": membership_id,
            "RegionId": "US",
            "ClassificationId": "TEST_CLASSIFICATION" if row_kind == "membership" else "",
            "ClassificationVersion": "TEST_VERSION" if row_kind == "membership" else "",
            "InstrumentId": instrument_id,
            "CompanyId": company_id,
            "Name": instrument_id,
            "IndustryId": industry_id,
            "ResolutionState": resolution_state
            if resolution_state is not None
            else ("identified" if row_kind == "membership" else "placeholder"),
            "MembershipEffectiveFrom": start if row_kind == "membership" else "",
            "MembershipEffectiveTo": end if row_kind == "membership" else "",
            "MembershipSourceId": "test-source" if row_kind == "membership" else "",
            "MembershipApprovalReference": "test-approval" if row_kind == "membership" else "",
            "MembershipReviewState": "reviewed" if row_kind == "membership" else "",
            "ListingId": listing_id,
            "Ticker": ticker if listing_id else "",
            "ProviderSymbol": provider_symbol if listing_id else "",
            "Exchange": "FIXTUREEX" if listing_id else "",
            "Currency": "USD" if listing_id else "",
            "IsPrimary": primary if listing_id else "",
            "ListingResolutionState": listing_state if listing_id else "",
            "ListingEffectiveFrom": "2019-01-01" if listing_id else "",
            "ListingEffectiveTo": "",
            "ListingSourceId": "test-source" if listing_id else "",
            "ListingApprovalReference": "test-approval" if listing_id else "",
        }
    )
    return row


def build_v2_release(
    source_manifest: Path,
    output_directory: Path,
    fixture: MembershipFixture | None = None,
) -> Path:
    """Copy a controlled release, then replace its stock grammar with v2 records."""
    manifest_path = build_v1_release(source_manifest, output_directory)
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    document["format"] = "market-catalog-release-2"
    for region in document["regions"]:
        for classification in region["classifications"]:
            classification["scheme_kind"] = "custom"
    selected = fixture if fixture is not None else membership_fixture()
    hierarchy_path: Path | None = None
    for artifact in document["artifacts"]:
        path = manifest_path.parent / artifact["path"]
        if artifact["role"] == "hierarchy":
            hierarchy_path = path
            _write_csv(path, selected.hierarchy)
            artifact["row_count"] = len(selected.hierarchy)
            artifact["sha256"] = sha256(path.read_bytes()).hexdigest()
        elif artifact["role"] == "stocks":
            _write_csv(path, selected.stocks, V2_STOCK_HEADERS)
            artifact["classification_id"] = None
            artifact["classification_version"] = None
            artifact["row_count"] = len(selected.stocks)
            artifact["sha256"] = sha256(path.read_bytes()).hexdigest()
    if hierarchy_path is None:
        raise ValueError("The source release must contain a hierarchy artifact")
    manifest_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _write_csv(
    path: Path,
    rows: tuple[dict[str, str], ...],
    headers: tuple[str, ...] | None = None,
) -> None:
    fieldnames = headers if headers is not None else tuple(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def record_request(calls: Counter[str], request_id: str) -> None:
    """Count a specific acquisition request without conflating different evidence."""
    calls[request_id] += 1


def counted_load[Result](
    calls: Counter[str], request_id: str, loader: Callable[[], Result]
) -> Result:
    record_request(calls, request_id)
    return loader()
