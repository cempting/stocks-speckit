import csv
import json
import re
import shutil
import socket
from collections.abc import Callable
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

import pytest

from market_data_tools.legacy.region_database import RegionDatabase
from market_data_tools.legacy.universe_import import import_reviewed_file


@pytest.fixture
def representation_database(tmp_path: Path) -> RegionDatabase:
    database = RegionDatabase(tmp_path / "representations.sqlite")
    source = tmp_path / "representations.csv"
    source.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom\n"
        "a,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n"
        "b,BBB,Beta,NASDAQ,Technology,Cloud,2020-01-01\n"
        "c,CCC,Gamma,NYSE,Technology,Hardware,2020-01-01\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="reviewed",
        exchange_id=None,
        coverage="test evidence",
        approval_reference="review-1",
    )
    return database


@pytest.fixture
def catalog_release(tmp_path: Path, local_etf_roots: dict[str, Path]) -> Path:
    """Create explicit test evidence without configuring the production store."""
    contracts = Path(__file__).parents[1] / "specs/010-manifest-csv-catalogs/contracts"
    grammar = (contracts / "catalog-files.md").read_text()
    headers = re.findall(r"```csv\n([^\n]+)\n```", grammar)
    roles = (
        "hierarchy",
        "stocks",
        "etf_listings",
        "sector_etfs",
        "industry_etfs",
        "sub_industry_etfs",
        "benchmarks",
    )
    columns = dict(
        zip(
            roles,
            (headers[0], headers[1], headers[2], headers[3], headers[3], headers[3], headers[4]),
            strict=True,
        )
    )
    scope = {
        "RegionId": "US",
        "ClassificationId": "TEST_CLASSIFICATION",
        "ClassificationVersion": "TEST_VERSION",
    }
    approval = {
        "SourceId": "test-source",
        "ApprovalReference": "test-approval",
        "EffectiveFrom": "2020-01-01",
        "EffectiveTo": "",
    }
    hierarchy = [
        {
            **scope,
            **approval,
            "NodeId": node,
            "NodeType": kind,
            "Name": node,
            "SectorId": "test-sector",
            "ParentIndustryId": parent,
            "ApprovalOrigin": "own",
        }
        for node, kind, parent in (
            ("test-sector", "sector", ""),
            ("test-cloud", "industry", ""),
            ("test-hardware", "industry", ""),
            ("test-empty", "industry", ""),
            ("test-specialist", "sub_industry", "test-cloud"),
        )
    ]
    stocks: list[dict[str, str]] = []
    for i, industry in enumerate(("test-cloud", "test-hardware", "test-cloud"), 1):
        row = {
            **scope,
            "RowId": f"test-row-{i}",
            "MembershipId": f"test-membership-{i}",
            "InstrumentId": f"test-stock-{i}",
            "CompanyId": "",
            "Name": f"Test stock {i}",
            "IndustryId": industry,
            "SubIndustryId": "test-specialist" if i == 1 else "",
            "ResolutionState": "identified",
            "MembershipEffectiveFrom": "2020-01-01",
            "MembershipEffectiveTo": "",
            "MembershipSourceId": "test-source",
            "MembershipApprovalReference": "test-approval",
            "MembershipReviewState": "reviewed",
        }
        if i != 3:
            row.update(
                {
                    "ListingId": f"test-listing-{i}",
                    "Ticker": f"TEST_STOCK_{i}",
                    "ProviderSymbol": f"TEST_STOCK_{i}",
                    "Exchange": "TESTEX",
                    "Currency": "USD",
                    "IsPrimary": "true",
                    "ListingResolutionState": "verified",
                    "ListingEffectiveFrom": "2019-01-01",
                    "ListingEffectiveTo": "",
                    "ListingSourceId": "test-source",
                    "ListingApprovalReference": "test-approval",
                }
            )
        stocks.append(row)
    etfs = [
        {
            **approval,
            "ListingId": "test-etf-listing",
            "RegionId": "US",
            "InstrumentId": "test-etf",
            "InstrumentType": "etf",
            "Ticker": "TEST_ETF",
            "ProviderSymbol": "TEST_ETF",
            "Name": "Test-only ETF",
            "Exchange": "TESTEX",
            "Currency": "USD",
            "IsPrimary": "true",
            "ResolutionState": "verified",
        }
    ]
    mappings = {
        "sector_etfs": [
            {
                **scope,
                **approval,
                "RepresentationId": "test-sector-etf",
                "NodeId": "test-sector",
                "ListingId": "test-etf-listing",
                "SuitabilityReference": "test-sector-suitability",
                "CandidateReviewId": "",
            }
        ],
        "industry_etfs": [
            {
                **scope,
                **approval,
                "RepresentationId": "test-cloud-etf",
                "NodeId": "test-cloud",
                "ListingId": "test-etf-listing",
                "SuitabilityReference": "test-cloud-suitability",
                "CandidateReviewId": "",
            }
        ],
        "sub_industry_etfs": [],
    }
    benchmarks = [
        {
            **approval,
            "BenchmarkId": f"test-{purpose}",
            "RegionId": "US",
            "Purpose": purpose,
            "Label": "Test-only benchmark",
            "ListingId": "test-etf-listing",
        }
        for purpose in ("sp500_comparison", "market_sentiment")
    ]
    directory = tmp_path / "authoring"
    directory.mkdir()
    artifacts: list[dict[str, object]] = []
    rows_by_role = {
        "hierarchy": hierarchy,
        "stocks": stocks,
        "etf_listings": etfs,
        "benchmarks": benchmarks,
        **mappings,
    }
    for role in roles:
        path = directory / f"{role}.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=columns[role].split(","), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows_by_role[role])
        artifacts.append(
            {
                "artifact_id": role,
                "role": role,
                "path": path.name,
                "sha256": sha256(path.read_bytes()).hexdigest(),
                "required": True,
                "row_count": len(rows_by_role[role]),
                "region_id": "US",
                "classification_id": None,
                "classification_version": None,
            }
        )
    ledger = directory / "governance.jsonl"
    ledger_scope = {
        "region_id": "US",
        "classification_id": "TEST_CLASSIFICATION",
        "classification_version": "TEST_VERSION",
    }
    ledger_period = {"start": "2020-01-01", "end": None}
    ledger_records = [
        {
            "record_type": "listing_inventory",
            "record_id": "test-inventory-record",
            "sequence": 1,
            "recorded_at": "2026-10-31T00:00:00Z",
            "origin": None,
            "payload": {
                "listing": {
                    "listing_id": "test-inventory-listing",
                    "instrument_id": "test-unclassified-stock",
                    "region_id": "US",
                    "instrument_type": "stock",
                    "ticker": "TEST_INVENTORY",
                    "provider_symbol": "TEST_INVENTORY",
                    "name": "Test-only unclassified stock",
                    "exchange": "TESTEX",
                    "currency": "USD",
                    "is_primary": False,
                    "resolution_state": "verified",
                    "period": ledger_period,
                    "source_id": "test-source",
                    "approval_reference": "test-approval",
                },
                "instrument_resolution_state": "identified",
                "company_id": None,
            },
        },
        {
            "record_type": "basket",
            "record_id": "test-basket-record",
            "sequence": 2,
            "recorded_at": "2026-10-31T00:00:00Z",
            "origin": None,
            "payload": {
                "representation_id": "test-basket",
                "scope": ledger_scope,
                "node_id": "test-empty",
                "name": "Test-only explicit basket",
                "period": ledger_period,
                "source_id": "test-source",
                "approval_reference": "test-approval",
                "review_state": "reviewed",
            },
        },
        {
            "record_type": "basket_constituent",
            "record_id": "test-basket-weight",
            "sequence": 3,
            "recorded_at": "2026-10-31T00:00:00Z",
            "origin": None,
            "payload": {
                "basket_id": "test-basket",
                "listing_id": "test-inventory-listing",
                "weight": "100.000",
            },
        },
    ]
    ledger.write_text(
        "".join(json.dumps(record) + "\n" for record in ledger_records), encoding="utf-8"
    )
    artifacts.append(
        {
            "artifact_id": "audit",
            "role": "audit",
            "path": ledger.name,
            "sha256": sha256(ledger.read_bytes()).hexdigest(),
            "required": True,
            "row_count": len(ledger_records),
            "region_id": None,
            "classification_id": None,
            "classification_version": None,
        }
    )
    manifest = {
        "format": "market-catalog-release-1",
        "release_id": "test-release",
        "created_at": "2026-10-31T00:00:00Z",
        "parent_release": None,
        "catalog_revision": "0" * 64,
        "regions": [
            {
                "region_id": "US",
                "name": "Test-only region",
                "status": "active",
                "coverage_state": "partial",
                "coverage_description": "Controlled test evidence",
                "coverage_as_of": "2026-10-30",
                "last_reviewed_at": "2026-10-30",
                "classifications": [
                    {
                        "classification_id": "TEST_CLASSIFICATION",
                        "scheme_name": "Test taxonomy",
                        "version": "TEST_VERSION",
                        "source_id": "test-source",
                        "approval_reference": "test-approval",
                        "effective_from": "2020-01-01",
                        "effective_to": None,
                    }
                ],
            }
        ],
        "evidence_sources": [
            {
                "source_id": "test-source",
                "source_type": "local_file",
                "description": "Test-only reviewed evidence",
                "coverage": "Controlled fixture",
                "authority": "Synthetic test review",
                "approval_reference": "test-approval",
                "reviewed_at": "2026-10-30",
            }
        ],
        "artifacts": artifacts,
        "research_sources": [
            {
                "resource_id": alias,
                "root": str(
                    local_etf_roots[alias]
                    if alias != "stockviewer"
                    else tmp_path / "unavailable-stockviewer"
                ),
                "required": False,
                "catalogs": [{"path": path, "name": "INDUSTRY_ETFS", "catalog_type": "industry"}],
            }
            for alias, path in (
                ("sector_rotation", "src/constants.py"),
                ("analyzer", "config.py"),
                ("stockfinder", "src/stockfinder/data.py"),
                ("stockviewer", "config.py"),
            )
        ],
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def catalog_factory(
    catalog_release: Path,
    tmp_path: Path,
) -> Callable[
    [Literal["reviewed", "invalid-count", "invalid-reference", "research-partial"]], Path
]:
    counter = 0

    def create(
        scenario: Literal["reviewed", "invalid-count", "invalid-reference", "research-partial"],
    ) -> Path:
        nonlocal counter
        counter += 1
        directory = tmp_path / f"catalog-scenario-{counter}"
        if scenario == "reviewed":
            source = Path(__file__).parent / "fixtures/catalogs/reviewed-us"
        else:
            source = catalog_release.parent
        shutil.copytree(source, directory)
        manifest = directory / "manifest.json"
        document = json.loads(manifest.read_text())
        if scenario == "invalid-count":
            document["artifacts"][0]["row_count"] += 1
        elif scenario == "invalid-reference":
            artifact = next(a for a in document["artifacts"] if a["role"] == "stocks")
            path = directory / artifact["path"]
            path.write_bytes(path.read_bytes().replace(b"test-cloud", b"test-unknown"))
            artifact["sha256"] = sha256(path.read_bytes()).hexdigest()
        elif scenario not in ("reviewed", "research-partial"):
            raise AssertionError("Unsupported controlled catalog scenario")
        manifest.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        return manifest.absolute()

    return create


@pytest.fixture
def catalog_clock() -> Callable[[], datetime]:
    return lambda: datetime(2026, 10, 31, tzinfo=UTC)


@pytest.fixture
def local_etf_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    base = Path(__file__).parent / "fixtures/local_etf_discovery"
    roots = {
        alias: tmp_path / alias
        for alias in ("sector_rotation", "analyzer", "stockfinder", "stockviewer")
    }
    for alias, root in roots.items():
        shutil.copytree(base / alias, root)

    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Local discovery must not request network data")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    return roots


@pytest.fixture
def local_etf_database(tmp_path: Path) -> RegionDatabase:
    database = RegionDatabase(tmp_path / "local-etfs.sqlite")
    source = Path(__file__).parent / "fixtures/local_etf_discovery/listings.csv"
    for classification in ("LOCAL-ETF-TEST", "OTHER-TEST"):
        selected = source
        if classification == "OTHER-TEST":
            selected = tmp_path / "other-reviewed.csv"
            selected.write_text(
                source.read_text()
                .replace("Semiconductors", "Other semiconductors")
                .replace(",Cloud,", ",Other cloud,")
            )
        import_reviewed_file(
            database,
            selected,
            region_id="US",
            classification_id=classification,
            source_id="local-etf-test",
            exchange_id=None,
            coverage="controlled test evidence",
            approval_reference="test-only",
        )
    for node, name, parent in (
        ("test-specialist", "Specialist", "local-etf-test-semiconductors"),
        ("test-uncovered", "Uncovered", None),
    ):
        database.add_review_node(
            region_id="US",
            classification_id="LOCAL-ETF-TEST",
            entity_id=node,
            name=name,
            sector_id="local-etf-test-technology",
            parent_industry_id=parent,
            source_id="local-etf-test",
            approval_reference="test-only",
            effective_from=date(2020, 1, 1),
        )
    return database
