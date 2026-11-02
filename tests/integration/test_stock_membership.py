import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from market_data.catalog import load_release
from market_data.domain.catalog import CatalogError, Scope
from market_data.domain.fundamentals import FundamentalBundle, FundamentalRequest
from market_data.domain.stock_selection import MembershipCatalog, MembershipEntry
from market_leadership.application.score_industry import (
    PEER_OBSERVATION_BASIS,
    PEER_SCORE_RULES_REVISION,
    PeerComparisonContext,
    score_industry,
)
from market_leadership.config import load_settings
from market_leadership.infrastructure.stock_membership import (
    membership_entry,
    validate_live_access,
)
from market_leadership.ui.catalog_labels import industry_path_label
from tests.integration.test_catalog_workflows import AS_OF, SCOPE, edit_rows


def test_dated_files_preserve_exact_membership_across_two_industries(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    assert len(snapshot.members(SCOPE, "test-cloud", AS_OF)) == 2
    assert len(snapshot.members(SCOPE, "test-hardware", AS_OF)) == 1
    assert snapshot.provider_symbols(SCOPE, "test-sector", AS_OF) == (
        "TEST_STOCK_1",
        "TEST_STOCK_2",
    )


def test_parent_context_keeps_direct_membership_path_and_result_facts_are_sensitive(
    catalog_release: Path,
) -> None:
    snapshot = load_release(catalog_release)
    row = next(
        item
        for item in snapshot.members(SCOPE, "test-cloud", AS_OF)
        if item.instrument_id == "test-stock-1"
    )
    paths = snapshot.memberships_for_instrument(SCOPE, row.instrument_id, AS_OF)
    entry = membership_entry(
        snapshot,
        row,
        AS_OF,
        selected_node_id="test-cloud",
    )

    assert entry is not None
    assert entry.industry_id == "test-cloud"
    assert {item.membership.industry_id for item in paths} == {"test-specialist"}
    active_nodes = snapshot.active_nodes(SCOPE, AS_OF)
    specialist = next(item for item in active_nodes if item.node_id == "test-specialist")
    assert industry_path_label(specialist, active_nodes) == (
        "test-sector / test-cloud / test-specialist [test-specialist]"
    )

    context = PeerComparisonContext(
        Scope("US", "TEST_CLASSIFICATION", "TEST_VERSION"),
        "test-cloud",
        AS_OF,
        (entry.instrument_id,),
        ((entry.instrument_id, "test-listing-1"),),
        "cohort-fingerprint",
        PEER_SCORE_RULES_REVISION,
        PEER_OBSERVATION_BASIS,
    )

    def bundle(fetched_at: datetime) -> FundamentalBundle:
        return FundamentalBundle(
            "TEST_STOCK_1",
            "yfinance",
            fetched_at,
            "USD",
            (),
            (),
            (),
        )

    first = score_industry(
        (entry,),
        cutoff=AS_OF,
        loader=lambda request, *, refresh=False: bundle(
            datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
        ),
        cohort_fingerprint=context.cohort_fingerprint,
        comparison_context=context,
    )
    second = score_industry(
        (entry,),
        cutoff=AS_OF,
        loader=lambda request, *, refresh=False: bundle(
            datetime(2026, 10, 30, 12, 1, tzinfo=UTC)
        ),
        cohort_fingerprint=context.cohort_fingerprint,
        comparison_context=context,
    )

    assert first.context is not None
    assert second.context is not None
    assert first.context.scope == context.scope
    assert first.context.industry_id == "test-cloud"
    assert first.context.eligible_listing_ids == ((entry.instrument_id, "test-listing-1"),)
    assert first.context.fact_fingerprint != second.context.fact_fingerprint
    assert first.result_fingerprint != second.result_fingerprint


def test_peer_cohorts_reuse_only_loaded_requests_across_a_b_a_contexts() -> None:
    cutoff = date(2026, 10, 30)

    def member(instrument_id: str) -> MembershipEntry:
        return MembershipEntry(
            instrument_id,
            None,
            instrument_id.upper(),
            instrument_id,
            "TESTEX",
            "USD",
            "sector-a",
            "Sector A",
            "industry-a",
            "Industry A",
            date(2020, 1, 1),
            None,
        )

    cohort_a = (member("instrument-a"), member("instrument-shared"))
    cohort_b = (member("instrument-shared"), member("instrument-b"))
    acquisitions: Counter[str] = Counter()
    cached: dict[FundamentalRequest, FundamentalBundle] = {}

    def load(request: FundamentalRequest, *, refresh: bool = False) -> FundamentalBundle:
        del refresh
        if request not in cached:
            acquisitions[request.symbol] += 1
            cached[request] = FundamentalBundle(
                request.symbol,
                "yfinance",
                datetime(2026, 10, 30, 12, 0, tzinfo=UTC),
                "USD",
                (),
                (),
                (),
            )
        return cached[request]

    def compare(members: tuple[MembershipEntry, ...], industry_id: str):
        ids = tuple(item.instrument_id for item in members)
        context = PeerComparisonContext(
            Scope("US", "CUSTOM", "v2"),
            industry_id,
            cutoff,
            ids,
            tuple((item.instrument_id, f"listing-{item.instrument_id}") for item in members),
            f"cohort-{industry_id}",
            PEER_SCORE_RULES_REVISION,
            PEER_OBSERVATION_BASIS,
        )
        return score_industry(
            members,
            cutoff=cutoff,
            loader=load,
            cohort_fingerprint=context.cohort_fingerprint,
            comparison_context=context,
        )

    assert acquisitions == Counter()
    result_a = compare(cohort_a, "industry-a")
    assert acquisitions == {"INSTRUMENT-A": 1, "INSTRUMENT-SHARED": 1}
    result_b = compare(cohort_b, "industry-b")
    assert acquisitions == {
        "INSTRUMENT-A": 1,
        "INSTRUMENT-SHARED": 1,
        "INSTRUMENT-B": 1,
    }
    returned_a = compare(cohort_a, "industry-a")

    assert result_a.eligible_instrument_ids == ("instrument-a", "instrument-shared")
    assert result_b.eligible_instrument_ids == ("instrument-shared", "instrument-b")
    assert returned_a.result_fingerprint == result_a.result_fingerprint
    assert acquisitions == {
        "INSTRUMENT-A": 1,
        "INSTRUMENT-SHARED": 1,
        "INSTRUMENT-B": 1,
    }


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
