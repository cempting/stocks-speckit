import csv
import io
import json
import shutil
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import (
    CatalogReader,
    activate_release,
    load_release,
)
from market_data.domain.catalog import CatalogError, Scope
from market_leadership.application.discover_sectors import discover_sectors
from market_leadership.application.industry_representations import snapshot_representation_worklist
from market_leadership.application.score_industry import score_industry
from market_leadership.infrastructure.stock_membership import (
    load_region_membership,
    membership_entry,
)
from tests.membership_helpers import build_v2_release, membership_fixture

AS_OF = date(2026, 10, 30)
SCOPE = Scope("US", "TEST_CLASSIFICATION", "TEST_VERSION")


def edit_rows(manifest: Path, role: str, change: Callable[[list[dict[str, str]]], None]) -> None:
    document = json.loads(manifest.read_text())
    artifact = next(item for item in document["artifacts"] if item["role"] == role)
    path = manifest.parent / artifact["path"]
    reader = csv.DictReader(io.StringIO(path.read_text()))
    headers = reader.fieldnames
    assert headers is not None
    rows = list(reader)
    change(rows)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    raw = output.getvalue().encode()
    path.write_bytes(raw)
    artifact.update(sha256=sha256(raw).hexdigest(), row_count=len(rows))
    manifest.write_text(json.dumps(document))


def test_exact_scope_membership_and_eligible_peer_requests(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    assert snapshot.scope_on("US", AS_OF) == SCOPE
    result = load_region_membership(snapshot, scope=SCOPE, industry_id="test-cloud", as_of=AS_OF)
    assert result.state == "available"
    assert {row.instrument_id for row in result.members} == {"test-stock-1", "test-stock-3"}
    assert snapshot.provider_symbols(SCOPE, "test-sector", AS_OF) == (
        "TEST_STOCK_1",
        "TEST_STOCK_2",
    )
    assert snapshot.provider_symbols(SCOPE, "test-specialist", AS_OF) == ("TEST_STOCK_1",)
    entries = tuple(
        entry
        for row in result.members
        if (entry := membership_entry(snapshot, row, AS_OF)) is not None
    )
    assert len(entries) == 1
    assert entries[0].company_id is None
    requested: list[str] = []

    def missing_financials(request, *, refresh=False):
        requested.append(request.symbol)
        raise ValueError("Controlled unavailable financial evidence")

    fingerprint = snapshot.cohort_fingerprint(SCOPE, "test-cloud", AS_OF)
    scored = score_industry(
        entries, cutoff=AS_OF, loader=missing_financials, cohort_fingerprint=fingerprint
    )
    assert requested == ["TEST_STOCK_1"]
    assert scored.eligible_instrument_ids == ("test-stock-1",)
    assert scored.cohort_fingerprint == fingerprint
    card = scored.stocks[0].scorecard
    for block, keys in (
        (card.quality, {"roe", "net_margin"}),
        (card.growth, {"revenue_yoy", "diluted_eps_yoy"}),
        (card.cash_flow, {"fcf_yield", "ocf_yoy"}),
    ):
        assert block.value is None and block.reason
        assert {metric.key for metric in block.metrics} == keys
        assert all(metric.percentile is None and metric.reason for metric in block.metrics)


def test_every_reviewed_node_has_explicit_representation_or_gap(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    rows = snapshot_representation_worklist(snapshot, scope=SCOPE, as_of=AS_OF)
    assert {item.node_id for item in rows} == {
        "test-sector",
        "test-cloud",
        "test-hardware",
        "test-empty",
        "test-specialist",
    }
    states = {item.node_id: item.status for item in rows}
    assert states["test-sector"] == states["test-cloud"] == "etf"
    assert states["test-empty"] == "basket"
    assert states["test-hardware"] == states["test-specialist"] == "not_covered"
    assert next(item for item in rows if item.node_id == "test-specialist").representation is None
    empty_basket = next(item for item in rows if item.node_id == "test-empty").representation
    assert empty_basket is not None
    assert [
        (item.listing_id, item.weight) for item in empty_basket.constituents
    ] == [("test-inventory-listing", Decimal("100.000"))]
    assert (
        load_region_membership(snapshot, scope=SCOPE, industry_id="test-empty", as_of=AS_OF).state
        == "empty_membership"
    )
    assert all(item.representation is None for item in rows if item.status == "not_covered")


def test_unrelated_reassignments_preserve_exact_cohort_fingerprints(catalog_release: Path) -> None:
    before = load_release(catalog_release)
    cloud_before = before.cohort_fingerprint(SCOPE, "test-cloud", AS_OF)
    hardware_before = before.cohort_fingerprint(SCOPE, "test-hardware", AS_OF)

    def move(rows):
        rows[0].update(IndustryId="test-empty", SubIndustryId="")

    edit_rows(catalog_release, "stocks", move)
    after = load_release(catalog_release)
    assert after.cohort_fingerprint(SCOPE, "test-cloud", AS_OF) != cloud_before
    assert after.cohort_fingerprint(SCOPE, "test-hardware", AS_OF) == hardware_before
    assert after.provider_symbols(SCOPE, "test-empty", AS_OF) == ("TEST_STOCK_1",)
    assert after.provider_symbols(SCOPE, "test-cloud", AS_OF) == ()


def test_benchmark_purposes_follow_distinct_file_listings(catalog_release: Path) -> None:
    def add_listing(rows):
        rows.append(
            {
                **rows[0],
                "ListingId": "test-sentiment-listing",
                "InstrumentId": "test-sentiment",
                "Ticker": "TEST_SENTIMENT",
                "ProviderSymbol": "TEST_SENTIMENT",
            }
        )

    edit_rows(catalog_release, "etf_listings", add_listing)
    edit_rows(
        catalog_release,
        "benchmarks",
        lambda rows: rows[1].update(ListingId="test-sentiment-listing"),
    )
    snapshot = load_release(catalog_release)
    calls: list[tuple[str, ...]] = []

    class Provider:
        provider_id = "test"

        def fetch_daily_history(self, symbols, *, start, end, force=False):
            calls.append(symbols)
            dates = pd.bdate_range(end=end, periods=400)
            return {
                symbol: pd.DataFrame(
                    {"close": range(100, 500), "volume": [1000.0] * 400}, index=dates
                )
                for symbol in symbols
            }

    result = discover_sectors(Provider(), snapshot=snapshot, scope=SCOPE, as_of=AS_OF)
    assert calls == [("TEST_ETF", "TEST_SENTIMENT")]
    assert result.sentiment.benchmark == "TEST_SENTIMENT"
    assert result.comparison_symbol == "TEST_ETF"
    assert result.benchmark_as_of == AS_OF
    assert len(result.sectors) == 1


def test_missing_benchmark_and_scope_are_explicit_not_defaults(catalog_release: Path) -> None:
    edit_rows(catalog_release, "benchmarks", lambda rows: rows.clear())
    snapshot = load_release(catalog_release)
    with pytest.raises(CatalogError, match="missing_benchmark"):
        snapshot.benchmark("US", "market_sentiment", AS_OF)
    with pytest.raises(CatalogError):
        snapshot.scope_on("OTHER", AS_OF)
    with pytest.raises(CatalogError):
        snapshot.scope_on("US", date(2010, 1, 1))


def test_compatible_assertions_deduplicate_and_nonprimary_never_request(
    catalog_release: Path,
) -> None:
    def change(rows):
        rows.append({**rows[0], "RowId": "duplicate-row", "MembershipId": "duplicate-assertion"})
        rows[1]["IsPrimary"] = "false"
        rows[0]["SubIndustryId"] = ""
        rows[-1]["SubIndustryId"] = ""

    edit_rows(catalog_release, "stocks", change)
    snapshot = load_release(catalog_release)
    assert len(snapshot.members(SCOPE, "test-sector", AS_OF)) == 3
    assert len(snapshot.members(SCOPE, "test-cloud", AS_OF)) == 2
    assert snapshot.provider_symbols(SCOPE, "test-sector", AS_OF) == ("TEST_STOCK_1",)
    assert snapshot.members(SCOPE, "test-specialist", AS_OF) == ()
    assert snapshot.provider_symbols(SCOPE, "test-specialist", AS_OF) == ()
    assert "TEST_INVENTORY" not in snapshot.provider_symbols(SCOPE, "test-sector", AS_OF)


def test_v2_industry_and_sector_queries_union_descendants_once(
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    fixture = membership_fixture(deep_levels=4)
    fixture = replace(
        fixture,
        stocks=tuple(
            row
            for row in fixture.stocks
            if row["MembershipId"] not in ("membership-parent", "membership-parent-copy")
        ),
    )
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        fixture,
    )
    snapshot = load_release(manifest)
    scope = snapshot.scope_on("US", AS_OF)

    industry_members = snapshot.members(scope, "industry-a", AS_OF)
    nested_members = snapshot.members(scope, "nested-2", AS_OF)
    cross_sector_members = snapshot.members(scope, "industry-c", AS_OF)
    sector_members = snapshot.members(scope, "sector-a", AS_OF)

    assert {row.instrument_id for row in industry_members} == {"share-class-a"}
    assert {row.instrument_id for row in nested_members} == {"share-class-a"}
    assert {row.instrument_id for row in cross_sector_members} == {"share-class-a"}
    assert {row.instrument_id for row in sector_members} == {
        "share-class-a",
        "share-class-b",
    }
    assert len(industry_members) == 1
    assert len(sector_members) == 2
    assert snapshot.members(scope, "industry-b", AS_OF)[0].instrument_id == "share-class-b"
    assert snapshot.provider_symbols(scope, "industry-a", AS_OF) == ("FIXTURE",)
    representations = {
        item.node_id: item
        for item in snapshot_representation_worklist(snapshot, scope=scope, as_of=AS_OF)
    }
    assert representations["test-cloud"].status == "etf"
    assert representations["test-specialist"].status == "not_covered"
    assert representations["test-empty"].status == "basket"
    paths = snapshot.memberships_for_instrument(scope, "share-class-a", AS_OF)
    assert {
        item.membership.industry_id for item in paths
    } == {"nested-3", "industry-c"}
    assert all(item.membership.industry_id != "industry-a" for item in paths)
    assert next(
        item for item in paths if item.membership.industry_id == "nested-3"
    ).hierarchy == tuple(
        node for node in snapshot.active_nodes(scope, AS_OF)
        if node.node_id in {"sector-a", "industry-a", "nested-2", "nested-3"}
    )
    entry = membership_entry(
        snapshot,
        industry_members[0],
        AS_OF,
        selected_node_id="industry-a",
    )
    assert entry is not None
    assert entry.industry_id == "industry-a"
    assert entry.symbol == "FIXTURE"


def test_v2_listing_copies_preserve_one_direct_membership_and_one_instrument(
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    snapshot = load_release(manifest)
    scope = snapshot.scope_on("US", AS_OF)

    direct_memberships = tuple(
        item
        for item in snapshot.membership_registry
        if item.membership_id == "membership-parent"
    )
    parent_members = snapshot.members(scope, "industry-a", AS_OF)
    instrument_members = tuple(
        item for item in parent_members if item.instrument_id == "share-class-a"
    )

    assert len(direct_memberships) == 1
    assert len(instrument_members) == 1
    assert instrument_members[0].listing is not None
    assert instrument_members[0].listing.listing_id == "listing-a-primary"


def test_v2_retained_snapshot_keeps_original_membership_after_reassignment(
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    fixture = membership_fixture(deep_levels=4)
    original_manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-original",
        fixture,
    )
    original = load_release(original_manifest)
    scope = original.scope_on("US", AS_OF)

    updated_stocks = tuple(
        {
            **row,
            "IndustryId": "industry-a",
        }
        if row["MembershipId"] == "membership-share-class"
        else row
        for row in fixture.stocks
    )
    updated_manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-reassigned",
        replace(fixture, stocks=updated_stocks),
    )
    reassigned = load_release(updated_manifest)
    reassigned_scope = reassigned.scope_on("US", AS_OF)

    assert {
        row.instrument_id for row in original.members(scope, "industry-b", AS_OF)
    } == {"share-class-b"}
    assert reassigned.members(reassigned_scope, "industry-b", AS_OF) == ()
    assert {
        row.instrument_id for row in reassigned.members(reassigned_scope, "industry-a", AS_OF)
    } == {"share-class-a", "share-class-b"}
    assert {
        item.membership.industry_id
        for item in original.memberships_for_instrument(scope, "share-class-b", AS_OF)
    } == {"industry-b"}


def test_v2_reparenting_changes_only_date_specific_ancestor_rollups(
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    fixture = membership_fixture(deep_levels=4)
    template = next(
        row for row in fixture.stocks if row["MembershipId"] == "membership-share-class"
    )
    reparented = {
        **template,
        "RowId": "membership-reparented",
        "MembershipId": "membership-reparented",
        "InstrumentId": "share-class-c",
        "CompanyId": "",
        "Name": "share-class-c",
        "IndustryId": "reparented",
        "ListingId": "",
        "Ticker": "",
        "ProviderSymbol": "",
        "Exchange": "",
        "Currency": "",
        "IsPrimary": "",
        "ListingResolutionState": "",
        "ListingEffectiveFrom": "",
        "ListingEffectiveTo": "",
        "ListingSourceId": "",
        "ListingApprovalReference": "",
    }
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        replace(fixture, stocks=(*fixture.stocks, reparented)),
    )
    snapshot = load_release(manifest)
    before_scope = snapshot.scope_on("US", date(2024, 12, 31))
    after_scope = snapshot.scope_on("US", date(2025, 1, 1))

    before = snapshot.memberships_for_instrument(before_scope, "share-class-c", date(2024, 12, 31))
    after = snapshot.memberships_for_instrument(after_scope, "share-class-c", date(2025, 1, 1))

    assert next(item for item in before if item.membership.industry_id == "reparented").hierarchy[
        -2
    ].node_id == "industry-a"
    assert next(item for item in after if item.membership.industry_id == "reparented").hierarchy[
        -2
    ].node_id == "industry-b"
    assert "share-class-c" in {
        row.instrument_id
        for row in snapshot.members(before_scope, "industry-a", date(2024, 12, 31))
    }
    assert "share-class-c" not in {
        row.instrument_id
        for row in snapshot.members(after_scope, "industry-a", date(2025, 1, 1))
    }
    assert "share-class-c" in {
        row.instrument_id
        for row in snapshot.members(after_scope, "industry-b", date(2025, 1, 1))
    }


def test_v2_membership_end_is_inclusive_during_reassignment(
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    fixture = membership_fixture(deep_levels=4)
    stocks = [dict(row) for row in fixture.stocks]
    original = next(row for row in stocks if row["MembershipId"] == "membership-share-class")
    original["MembershipEffectiveTo"] = "2024-12-31"
    reassigned = dict(original)
    reassigned.update(
        RowId="membership-share-class-reassigned",
        MembershipId="membership-share-class-reassigned",
        IndustryId="industry-a",
        MembershipEffectiveFrom="2025-01-01",
        MembershipEffectiveTo="",
    )
    fixture = replace(fixture, stocks=(*stocks, reassigned))
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        fixture,
    )
    snapshot = load_release(manifest)
    scope = snapshot.scope_on("US", date(2024, 12, 31))

    assert {
        row.instrument_id
        for row in snapshot.members(scope, "industry-b", date(2024, 12, 31))
    } == {"share-class-b", "share-class-c"}
    assert snapshot.members(scope, "industry-b", date(2025, 1, 1)) == ()
    assert {
        row.instrument_id
        for row in snapshot.members(scope, "industry-a", date(2025, 1, 1))
    } == {"share-class-a", "share-class-b"}


def test_research_changes_do_not_change_cohort_but_relevant_source_changes_do(
    catalog_release: Path,
) -> None:
    before = load_release(catalog_release)
    document = json.loads(catalog_release.read_text())
    document["research_sources"][0]["root"] = str(catalog_release.parent / "not-observable")
    catalog_release.write_text(json.dumps(document))
    research = load_release(catalog_release)
    for node in ("test-cloud", "test-hardware"):
        assert before.cohort_fingerprint(SCOPE, node, AS_OF) == research.cohort_fingerprint(
            SCOPE, node, AS_OF
        )
    document["evidence_sources"][0]["description"] = "Changed reviewed source diagnostics"
    catalog_release.write_text(json.dumps(document))
    changed = load_release(catalog_release)
    assert before.cohort_fingerprint(SCOPE, "test-cloud", AS_OF) != changed.cohort_fingerprint(
        SCOPE, "test-cloud", AS_OF
    )


def test_physical_membership_copy_does_not_change_cohort_fingerprint(
    catalog_release: Path,
) -> None:
    before = load_release(catalog_release)
    original = before.cohort_fingerprint(SCOPE, "test-cloud", AS_OF)

    def add_copy(rows):
        rows.append(
            {
                **rows[0],
                "RowId": "physical-copy-row",
                "MembershipId": "physical-copy-membership",
            }
        )

    edit_rows(catalog_release, "stocks", add_copy)
    after = load_release(catalog_release)

    assert after.cohort_fingerprint(SCOPE, "test-cloud", AS_OF) == original


def test_two_activations_switch_exact_members_and_etf_without_mutating_old_snapshot(
    catalog_release: Path,
    tmp_path: Path,
) -> None:
    entry = tmp_path / "controlled-store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    reader = CatalogReader()
    before = reader.read(entry)
    assert reader.read(entry) is before
    candidate_dir = tmp_path / "candidate"
    shutil.copytree(first.manifest_path.parent, candidate_dir)
    candidate = candidate_dir / first.manifest_path.name
    edit_rows(
        candidate, "stocks", lambda rows: rows[0].update(IndustryId="test-empty", SubIndustryId="")
    )
    edit_rows(
        candidate,
        "etf_listings",
        lambda rows: rows[0].update(ProviderSymbol="TEST_ETF_CHANGED", Ticker="TEST_ETF_CHANGED"),
    )
    second = activate_release(entry, candidate, expected_release=first.release_id)
    after = reader.read(entry)
    assert after is not before
    assert after.node_index is before.node_index
    assert after.release.release_id == second.release_id
    assert before.provider_symbols(SCOPE, "test-cloud", AS_OF) == ("TEST_STOCK_1",)
    assert after.provider_symbols(SCOPE, "test-cloud", AS_OF) == ()
    assert after.provider_symbols(SCOPE, "test-empty", AS_OF) == ("TEST_STOCK_1",)
    assert after.cohort_fingerprint(SCOPE, "test-hardware", AS_OF) == before.cohort_fingerprint(
        SCOPE, "test-hardware", AS_OF
    )
    assert after.benchmark("US", "market_sentiment", AS_OF).provider_symbol == "TEST_ETF_CHANGED"
    assert before.benchmark("US", "market_sentiment", AS_OF).provider_symbol == "TEST_ETF"


def test_research_publication_reuses_unchanged_content_indexes(
    catalog_release: Path, tmp_path: Path
) -> None:
    entry = tmp_path / "controlled-store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    reader = CatalogReader()
    before = reader.read(entry)
    activate_release(entry, first.manifest_path, expected_release=first.release_id)
    after = reader.read(entry)
    assert after is not before
    assert after.catalog_revision == before.catalog_revision
    assert after.node_index is before.node_index
    assert after.member_index is before.member_index
    assert after.cohort_fingerprint(SCOPE, "test-cloud", AS_OF) == before.cohort_fingerprint(
        SCOPE, "test-cloud", AS_OF
    )
