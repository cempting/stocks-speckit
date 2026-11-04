"""Build explicit test-owned authoring inputs without acquisition."""

import argparse
import csv
import json
from dataclasses import asdict
from datetime import date
from hashlib import sha256
from pathlib import Path

from market_data.catalog import HEADERS, load_release
from market_data.domain.company_evidence import SourceAssessment
from tests.company_evidence_helpers import verified_association
from tests.membership_helpers import build_v2_release, membership_fixture


def _write_json(path: Path, document: object) -> None:
    path.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _v1_catalog(directory: Path) -> Path:
    directory.mkdir()
    scope = {
        "RegionId": "US", "ClassificationId": "TEST_CLASSIFICATION",
        "ClassificationVersion": "TEST_VERSION",
    }
    approval = {
        "SourceId": "test-source", "ApprovalReference": "test-approval",
        "EffectiveFrom": "2020-01-01", "EffectiveTo": "",
    }
    hierarchy = [
        {
            **scope, **approval, "NodeId": node, "NodeType": kind, "Name": node,
            "SectorId": "test-sector", "ParentIndustryId": parent, "ApprovalOrigin": "own",
        }
        for node, kind, parent in (
            ("test-sector", "sector", ""), ("test-cloud", "industry", ""),
            ("test-hardware", "industry", ""), ("test-empty", "industry", ""),
            ("test-specialist", "sub_industry", "test-cloud"),
        )
    ]
    stock = {
        **scope, "RowId": "test-stock-row", "MembershipId": "test-membership",
        "InstrumentId": "test-stock", "CompanyId": "", "Name": "Synthetic stock",
        "IndustryId": "test-cloud", "SubIndustryId": "test-specialist",
        "ResolutionState": "identified", "MembershipEffectiveFrom": "2020-01-01",
        "MembershipEffectiveTo": "", "MembershipSourceId": "test-source",
        "MembershipApprovalReference": "test-approval", "MembershipReviewState": "reviewed",
        "ListingId": "test-stock-listing", "Ticker": "SYNTHETIC",
        "ProviderSymbol": "SYNTHETIC", "Exchange": "NASDAQ", "Currency": "USD",
        "IsPrimary": "true", "ListingResolutionState": "verified",
        "ListingEffectiveFrom": "2019-01-01", "ListingEffectiveTo": "",
        "ListingSourceId": "test-source", "ListingApprovalReference": "test-approval",
    }
    etf = {
        **approval, "ListingId": "test-etf-listing", "RegionId": "US",
        "InstrumentId": "test-etf", "InstrumentType": "etf", "Ticker": "TEST_ETF",
        "ProviderSymbol": "TEST_ETF", "Name": "Synthetic ETF", "Exchange": "NASDAQ",
        "Currency": "USD", "IsPrimary": "true", "ResolutionState": "verified",
    }
    rows_by_role = {
        "hierarchy": hierarchy, "stocks": [stock], "etf_listings": [etf],
        "sector_etfs": [{
            **scope, **approval, "RepresentationId": "test-sector-etf", "NodeId": "test-sector",
            "ListingId": "test-etf-listing", "SuitabilityReference": "test-suitability",
            "CandidateReviewId": "",
        }],
        "industry_etfs": [],
        "sub_industry_etfs": [],
        "benchmarks": [
            {
                **approval, "BenchmarkId": f"test-{purpose}", "RegionId": "US",
                "Purpose": purpose, "Label": "Synthetic ETF benchmark",
                "ListingId": "test-etf-listing",
            }
            for purpose in ("sp500_comparison", "market_sentiment")
        ],
    }
    artifacts: list[dict[str, object]] = []
    for role, rows in rows_by_role.items():
        path = directory / f"{role}.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=HEADERS[role].split(","),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        artifacts.append({
            "artifact_id": role, "role": role, "path": path.name,
            "sha256": sha256(path.read_bytes()).hexdigest(), "required": True,
            "row_count": len(rows), "region_id": "US", "classification_id": None,
            "classification_version": None,
        })
    audit = directory / "governance.jsonl"
    audit.write_text("", encoding="utf-8")
    artifacts.append({
        "artifact_id": "audit", "role": "audit", "path": audit.name,
        "sha256": sha256(b"").hexdigest(), "required": True, "row_count": 0,
        "region_id": None, "classification_id": None, "classification_version": None,
    })
    manifest = directory / "manifest.json"
    _write_json(manifest, {
        "format": "market-catalog-release-1", "release_id": "synthetic-v1",
        "created_at": "2026-10-31T00:00:00Z", "parent_release": None,
        "catalog_revision": "0" * 64,
        "regions": [{
            "region_id": "US", "name": "Synthetic region", "status": "active",
            "coverage_state": "partial", "coverage_description": "Test-only evidence",
            "coverage_as_of": "2026-10-30", "last_reviewed_at": "2026-10-30",
            "classifications": [{
                "classification_id": "TEST_CLASSIFICATION", "scheme_name": "Synthetic taxonomy",
                "version": "TEST_VERSION", "source_id": "test-source",
                "approval_reference": "test-approval", "effective_from": "2020-01-01",
                "effective_to": None,
            }],
        }],
        "evidence_sources": [{
            "source_id": "test-source", "source_type": "local_file",
            "description": "Synthetic reviewed evidence", "coverage": "Controlled fixture",
            "authority": "Test review", "approval_reference": "test-approval",
            "reviewed_at": "2026-10-30",
        }],
        "artifacts": artifacts, "research_sources": [],
    })
    return manifest


def _registries(manifest: Path, directory: Path) -> None:
    catalog = load_release(manifest)
    directory.mkdir()
    binding = verified_association(
        instrument_id="test-stock" if catalog.release.format.endswith("-1") else "share-class-a",
        listing_id=(
            "test-stock-listing" if catalog.release.format.endswith("-1") else "listing-a-primary"
        ),
        provider_symbol="SYNTHETIC" if catalog.release.format.endswith("-1") else "FIXTURE_A",
        exchange="NASDAQ" if catalog.release.format.endswith("-1") else "TESTEX",
        catalog_revision=catalog.catalog_revision,
    )
    binding_record = asdict(binding)
    for field in ("effective_from", "effective_to"):
        value = binding_record[field]
        binding_record[field] = value.isoformat() if value is not None else None
    _write_json(directory / "bindings.json", {
        "format": "market-structure-bindings-1", "bindings": [binding_record],
    })
    reference = SourceAssessment(
        assessment_id="test-news-review", source_id="test-news", role="reference",
        status="approved", allowed_uses=(), reviewed_at=date(2026, 10, 30),
        review_reference="synthetic-news-review", expires_at=None,
        fingerprint=sha256(b"synthetic-news-review").hexdigest(),
    )
    assessment_record = asdict(reference)
    assessment_record["reviewed_at"] = reference.reviewed_at.isoformat()
    registrations = [
        {
            "source_id": source_id, "name": name, "kind": kind, "location": None,
            "region_ids": ["US"], "scope_refs": [],
            "provenance_reference": "synthetic-review", "review_state": "approved",
        }
        for source_id, name, kind in (
            ("test-source", "Synthetic structure evidence", "reference"),
            ("yfinance", "Controlled observation provider", "market_data"),
            ("test-news", "Synthetic news metadata", "news"),
        )
    ]
    _write_json(directory / "sources.json", {
        "format": "market-structure-sources-1", "sources": registrations,
        "assessments": [assessment_record],
    })
    policy: dict[str, object] = {
        "policy_id": "test-observations", "source_id": "yfinance", "provider_id": "yfinance",
        "status": "approved", "reviewed_at": "2026-10-30T00:00:00.000000Z",
        "review_reference": "synthetic-observation-review", "expires_at": "2027-10-30",
        "allowed_uses": ["collection", "display", "normalized_retention"],
        "region_ids": ["US"], "currencies": ["USD"], "frequencies": ["1d"],
        "return_bases": ["adjusted"], "freshness_seconds": 300, "max_retention_days": 365,
    }
    policy["fingerprint"] = sha256(json.dumps(
        policy, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode()).hexdigest()
    _write_json(directory / "observation-policies.json", {
        "format": "market-structure-observation-policies-1", "policies": [policy],
    })
    _write_json(directory / "indexes.json", {
        "format": "market-structure-indexes-1", "indexes": [{
            "index_id": "test-index", "name": "Synthetic true index", "region_id": "US",
            "provider_id": "yfinance", "provider_symbol": "TEST_INDEX", "calendar_id": "XNYS",
            "currency": "USD", "return_basis": "adjusted", "effective_from": "2020-01-01",
            "effective_to": None, "source_id": "yfinance",
            "approval_reference": "synthetic-index-review", "context_purposes": ["comparison"],
        }],
    })


def build_demo(output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=False)
    v1 = _v1_catalog(output / "catalog")
    v2 = build_v2_release(v1, output / "catalog-v2", membership_fixture(deep_levels=4))
    for version, manifest in ((1, v1), (2, v2)):
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["release_id"] = f"synthetic-v{version}"
        document["catalog_revision"] = load_release(manifest).catalog_revision
        _write_json(manifest, document)
    registries = output / "registries"
    registries_v2 = output / "registries-v2"
    _registries(v1, registries)
    _registries(v2, registries_v2)
    return {"v1": v1, "v2": v2, "registries": registries, "registries_v2": registries_v2}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = build_demo(args.output)
    print(json.dumps({"format": "market-structure-demo-1", **{
        key: str(value) for key, value in paths.items()
    }}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
