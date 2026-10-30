import json
from dataclasses import replace

import pytest

from market_leadership.config import load_settings
from market_leadership.infrastructure.stock_membership import (
    FIXTURE_CATALOG,
    load_membership_catalog,
    validate_live_access,
)


def test_dated_fixture_has_six_active_stocks_and_two_industries():
    catalog = load_membership_catalog(FIXTURE_CATALOG)
    assert catalog.mode == "fixture"
    assert len(catalog.entries) >= 6
    assert len({entry.industry_id for entry in catalog.entries}) >= 2
    assert all(entry.active_on(catalog.observed_on) for entry in catalog.entries)


@pytest.mark.parametrize(
    "mutation", ["duplicate", "date", "parent", "metadata", "ambiguous_symbol"]
)
def test_invalid_catalog_rejected_as_error(tmp_path, mutation):
    document = json.loads(FIXTURE_CATALOG.read_text())
    if mutation == "duplicate":
        document["entries"].append(document["entries"][0])
    elif mutation == "date":
        document["entries"][0]["effective_from"] = "not-a-date"
    elif mutation == "parent":
        document["entries"][1]["sector_id"] = "OTHER"
    elif mutation == "metadata":
        del document["source_id"]
    else:
        document["entries"][1]["symbol"] = document["entries"][0]["symbol"]
        document["entries"][1]["exchange"] = "OTHER"
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        load_membership_catalog(path)


def test_live_access_rejects_fixture_and_incompatible_sources(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yfinance")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "yfinance")
    catalog = load_membership_catalog(FIXTURE_CATALOG)
    settings = load_settings()
    with pytest.raises(ValueError, match="fixture"):
        validate_live_access(catalog, settings)
    with pytest.raises(ValueError, match="single yfinance"):
        validate_live_access(catalog, replace(settings, provider_ids=("massive",)))
