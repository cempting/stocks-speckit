import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from market_leadership.config import load_settings
from market_leadership.domain.catalog import CatalogError
from market_leadership.domain.stock_selection import MembershipCatalog
from market_leadership.infrastructure.catalog_files import load_release
from market_leadership.infrastructure.stock_membership import validate_live_access
from tests.integration.test_catalog_workflows import AS_OF, SCOPE, edit_rows


def test_dated_files_preserve_exact_membership_across_two_industries(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    assert len(snapshot.members(SCOPE, "test-cloud", AS_OF)) == 2
    assert len(snapshot.members(SCOPE, "test-hardware", AS_OF)) == 1
    assert snapshot.provider_symbols(SCOPE, "test-sector", AS_OF) == (
        "TEST_STOCK_1",
        "TEST_STOCK_2",
    )


@pytest.mark.parametrize(
    "mutation", ["duplicate", "date", "parent", "metadata", "ambiguous_symbol"]
)
def test_invalid_catalog_rejected_as_error(catalog_release: Path, mutation: str) -> None:
    def change(rows):
        if mutation == "duplicate":
            rows.append(rows[0])
        elif mutation == "date":
            rows[0]["MembershipEffectiveFrom"] = "not-a-date"
        elif mutation == "parent":
            rows[1]["IndustryId"] = "OTHER"
        elif mutation == "ambiguous_symbol":
            rows[1]["ProviderSymbol"] = rows[0]["ProviderSymbol"]
            rows[1]["Exchange"] = "OTHER"

    if mutation == "metadata":
        document = json.loads(catalog_release.read_text())
        document["evidence_sources"] = []
        catalog_release.write_text(json.dumps(document))
    else:
        edit_rows(catalog_release, "stocks", change)
    with pytest.raises(CatalogError):
        load_release(catalog_release)


def test_live_access_rejects_fixture_and_incompatible_sources(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yfinance")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "yfinance")
    catalog = MembershipCatalog(date.today(), "test", "TEST", "fixture", "test", "test", (), "test")
    settings = load_settings()
    with pytest.raises(ValueError, match="fixture"):
        validate_live_access(catalog, settings)
    with pytest.raises(ValueError, match="single yfinance"):
        validate_live_access(catalog, replace(settings, provider_ids=("massive",)))
    with pytest.raises(ValueError, match="retired"):
        validate_live_access(replace(catalog, mode="live"), settings)
