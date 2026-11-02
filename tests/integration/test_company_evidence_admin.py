import json
from datetime import date
from pathlib import Path

import pytest

from market_data.catalog import load_release
from market_data.company_evidence import CompanyEvidenceFiles
from market_data.domain.company_evidence import company_association_id
from market_data_tools.company_evidence_admin import main
from tests.membership_helpers import build_v2_release, membership_fixture


def _catalog_manifest(catalog_release: Path, tmp_path: Path) -> Path:
    return build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )


def test_review_source_records_scoped_review_without_fetching_urls(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "evidence"
    result = main(
        [
            "review-source",
            "--source-id",
            "synthetic-source",
            "--role",
            "disclosure",
            "--publisher",
            "Synthetic publisher",
            "--terms-url",
            "https://publisher.example/terms",
            "--coverage-reference",
            "synthetic-coverage-record",
            "--authority",
            "annual issuer disclosures",
            "--status",
            "approved",
            "--reviewed-at",
            "2026-01-02",
            "--review-reference",
            "operator-review-17",
            "--structured-capability",
            "annual-report-index",
            "--permission",
            "collection",
            "--permission",
            "display",
            "--allowed-host",
            "issuer.example",
            "--allowed-route",
            "/investors/annual-reports",
            "--evidence-root",
            str(root),
            "--expected-revision",
            "none",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    assert result == 0
    assert report["report_version"] == "company-evidence-admin-1"
    assert report["status"] == "recorded"
    assessment = CompanyEvidenceFiles(root).load_source_assessment("synthetic-source")
    assert assessment.status == "approved"
    assert assessment.allowed_uses == ("collection", "display")
    assert assessment.structured_capabilities == ("annual-report-index",)
    assert assessment.allowed_hosts == ("issuer.example",)
    assert assessment.allowed_routes == ("/investors/annual-reports",)


def test_review_source_requires_explicit_collection_capabilities_hosts_and_cas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    common = [
        "review-source",
        "--source-id",
        "source",
        "--role",
        "financial",
        "--publisher",
        "Synthetic publisher",
        "--terms-url",
        "https://publisher.example/terms",
        "--coverage-reference",
        "coverage",
        "--authority",
        "statements",
        "--status",
        "approved",
        "--reviewed-at",
        "2026-01-02",
        "--review-reference",
        "review",
        "--permission",
        "collection",
        "--evidence-root",
        str(tmp_path / "evidence"),
        "--expected-revision",
        "none",
    ]

    assert main(common) == 2
    assert "structured capabilities and allowed hosts" in capsys.readouterr().err
    common.extend(["--structured-capability", "statements", "--allowed-host", "data.example"])
    assert main(common) == 0
    capsys.readouterr()

    assert main(common) == 2
    assert "revision changed" in capsys.readouterr().err


def test_bind_issuer_requires_dated_catalog_listing_and_never_verifies_or_grants(
    catalog_release: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _catalog_manifest(catalog_release, tmp_path)
    root = tmp_path / "evidence"
    arguments = [
        "bind-issuer",
        "--manifest",
        str(manifest),
        "--instrument-id",
        "share-class-a",
        "--listing-id",
        "listing-a-primary",
        "--provider-id",
        "yfinance",
        "--cik",
        "0000123456",
        "--issuer-domain",
        "issuer.example",
        "--effective-from",
        "2020-01-01",
        "--identity-reference",
        "operator-binding-review",
        "--evidence-root",
        str(root),
        "--expected-revision",
        "none",
    ]

    assert main(arguments) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["report_version"] == "company-evidence-admin-1"
    assert report["permission_granted"] is False
    catalog = load_release(manifest)
    association_id = company_association_id(
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        source_id="yfinance",
        effective_from=date(2020, 1, 1),
        effective_to=None,
    )
    association = CompanyEvidenceFiles(root).load_association(association_id)
    assert association.catalog_revision == catalog.catalog_revision
    assert association.company_id is None
    assert association.state == "unresolved"
    assert association.identity_evidence is None

    assert main(arguments) == 2
    assert "revision changed" in capsys.readouterr().err


def test_bind_issuer_rejects_missing_identity_and_unknown_listing(
    catalog_release: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _catalog_manifest(catalog_release, tmp_path)
    arguments = [
        "bind-issuer",
        "--manifest",
        str(manifest),
        "--instrument-id",
        "share-class-a",
        "--listing-id",
        "listing-a-primary",
        "--provider-id",
        "yfinance",
        "--effective-from",
        "2020-01-01",
        "--identity-reference",
        "review",
        "--evidence-root",
        str(tmp_path / "evidence"),
        "--expected-revision",
        "none",
    ]
    assert main(arguments) == 2
    assert "At least one" in capsys.readouterr().err

    arguments[arguments.index("listing-a-primary")] = "unknown-listing"
    arguments.extend(["--issuer-domain", "issuer.example"])
    assert main(arguments) == 2
    assert "not present in the captured catalog" in capsys.readouterr().err
