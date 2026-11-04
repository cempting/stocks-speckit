import json
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from market_data.domain.catalog import (
    Artifact,
    Basket,
    BasketDefinition,
    BasketWeight,
    Benchmark,
    CandidateAssessment,
    CatalogEntry,
    CatalogError,
    CatalogRelease,
    Classification,
    CollectionEvidence,
    CollectionOccurrence,
    EtfRepresentation,
    EvidenceSource,
    HierarchyNode,
    LedgerRecord,
    Listing,
    ListingInventory,
    NodeReview,
    ParentRelease,
    Period,
    Publication,
    Region,
    RepresentationApproval,
    RepresentationProvenance,
    ResearchCatalog,
    ResearchSource,
    ReviewEvidence,
    Scope,
    StockRow,
    decode_ledger_record,
    parse_date,
    parse_utc,
    validate_catalog,
)
from market_data.domain.industry_representations import BasketConstituent
from market_data.domain.local_etf_evidence import CollectionRun, Evidence, ReviewDecision

SCOPE = Scope("US", "TEST_CLASSIFICATION", "TEST_VERSION")
PERIOD = Period(date(2020, 1, 1))
SOURCE = EvidenceSource(
    "test-source", "local_file", "Test only", None, None, "test-approval", date(2026, 10, 30)
)


def node(node_id: str, kind: str, parent: str | None = None) -> HierarchyNode:
    return HierarchyNode(
        SCOPE,
        node_id,
        kind,
        node_id,
        "sector",
        parent,
        PERIOD,
        SOURCE.source_id,
        SOURCE.approval_reference,
        "own",
    )


def listing(**changes: object) -> Listing:
    original = Listing(
        "listing",
        "instrument",
        "US",
        "etf",
        "TEST_ETF",
        "TEST_ETF",
        "Test only",
        "TESTEX",
        "USD",
        True,
        "verified",
        PERIOD,
        "test-source",
        "test-approval",
    )
    return replace(original, **changes)


def classification() -> Classification:
    return Classification(SCOPE, "Test taxonomy", "test-source", "test-approval", PERIOD)


def test_period_inclusive_and_coverage() -> None:
    interval = Period(date(2020, 1, 1), date(2020, 1, 2))
    assert interval.active_on(date(2020, 1, 2))
    assert interval.overlaps(Period(date(2020, 1, 2), date(2020, 1, 3)))
    assert not interval.overlaps(Period(date(2020, 1, 3)))
    assert PERIOD.covers(interval)
    assert not interval.covers(PERIOD)


@pytest.mark.parametrize(
    "start,end",
    [
        (date(2020, 1, 2), date(2020, 1, 1)),
        (datetime(2020, 1, 1), None),
    ],
)
def test_invalid_period(start: date, end: date | None) -> None:
    with pytest.raises(CatalogError):
        Period(start, end)


@pytest.mark.parametrize("version", ["", " ", "latest"])
def test_scope_requires_explicit_version(version: str) -> None:
    with pytest.raises(CatalogError):
        Scope("US", "TEST_CLASSIFICATION", version)


def test_source_review_is_separate_from_registration() -> None:
    SOURCE.require_approval("test-approval")
    for source in (
        replace(SOURCE, reviewed_at=None),
        replace(SOURCE, source_type="live"),
        replace(SOURCE, approval_reference=None),
    ):
        with pytest.raises(CatalogError, match="source_approval"):
            source.require_approval("test-approval")
    with pytest.raises(CatalogError):
        SOURCE.require_approval("different")


def test_inherited_node_requires_empty_own_review() -> None:
    inherited = replace(
        node("sector", "sector"),
        approval_origin="classification_inherited",
        source_id=None,
        approval_reference=None,
    )
    validate_catalog((classification(),), (SOURCE,), (inherited,), (), (), (), ())
    with pytest.raises(CatalogError):
        replace(inherited, source_id="test-source")


def test_hierarchy_exact_parent_and_period() -> None:
    nodes = (
        node("sector", "sector"),
        node("industry", "industry"),
        node("sub", "sub_industry", "industry"),
    )
    validate_catalog((classification(),), (SOURCE,), nodes, (), (), (), ())
    for invalid in (
        replace(nodes[2], parent_industry_id="unknown"),
        replace(nodes[2], parent_industry_id="sector"),
        replace(nodes[1], scope=Scope("OTHER", "TEST_CLASSIFICATION", "TEST_VERSION")),
        replace(nodes[1], period=Period(date(2019, 1, 1))),
    ):
        with pytest.raises(CatalogError):
            validate_catalog((classification(),), (SOURCE,), (*nodes[:2], invalid), (), (), (), ())


def test_listing_verification_and_primary_are_explicit() -> None:
    assert listing().eligible
    assert listing(is_primary=False).eligible
    assert not listing(resolution_state="unverified", provider_symbol=None).eligible
    for changes in (
        {"period": None},
        {"source_id": None},
        {"provider_symbol": None},
        {"currency": "usd"},
        {"is_primary": None},
        {"resolution_state": "guessed"},
    ):
        with pytest.raises(CatalogError):
            listing(**changes)


def test_stock_without_listing_is_preserved() -> None:
    row = StockRow(
        "row",
        "membership",
        SCOPE,
        "instrument",
        None,
        "Unknown listing",
        "industry",
        None,
        "identified",
        PERIOD,
        "test-source",
        "test-approval",
        "reviewed",
        None,
    )
    assert row.provider_symbol_on(date(2026, 10, 30)) is None
    assert (
        replace(row, listing=listing(is_primary=False, instrument_type="stock")).provider_symbol_on(
            date(2026, 10, 30)
        )
        is None
    )


def test_membership_identity_and_listing_attributes_must_agree() -> None:
    nodes = (node("sector", "sector"), node("industry", "industry"))
    row = StockRow(
        "row",
        "membership",
        SCOPE,
        "instrument",
        None,
        "Test",
        "industry",
        None,
        "identified",
        PERIOD,
        "test-source",
        "test-approval",
        "reviewed",
        listing(instrument_type="stock"),
    )
    validate_catalog((classification(),), (SOURCE,), nodes, (row,), (), (), ())
    for other in (
        replace(row, row_id="other", name="Different name"),
        replace(
            row,
            row_id="other",
            membership_id="other",
            listing=listing(provider_symbol="DIFFERENT", instrument_type="stock"),
        ),
    ):
        with pytest.raises(CatalogError):
            validate_catalog((classification(),), (SOURCE,), nodes, (row, other), (), (), ())


def test_conflicting_industries_and_explicit_sub_industry() -> None:
    nodes = (
        node("sector", "sector"),
        node("industry", "industry"),
        node("other", "industry"),
        node("sub", "sub_industry", "industry"),
    )
    row = StockRow(
        "row",
        "membership",
        SCOPE,
        "instrument",
        None,
        "Test",
        "industry",
        "sub",
        "identified",
        PERIOD,
        "test-source",
        "test-approval",
        "reviewed",
        listing(instrument_type="stock"),
    )
    compatible = replace(row, row_id="other", membership_id="other")
    validate_catalog((classification(),), (SOURCE,), nodes, (row, compatible), (), (), ())
    with pytest.raises(CatalogError):
        validate_catalog(
            (classification(),),
            (SOURCE,),
            nodes,
            (row, replace(compatible, industry_id="other", sub_industry_id=None)),
            (),
            (),
            (),
        )
    with pytest.raises(CatalogError):
        validate_catalog(
            (classification(),),
            (SOURCE,),
            nodes,
            (replace(row, industry_id="other"),),
            (),
            (),
            (),
        )


def test_etf_role_exact_scope_and_verified_primary_listing() -> None:
    nodes = (node("sector", "sector"), node("industry", "industry"))
    mapping = EtfRepresentation(
        "representation",
        SCOPE,
        "industry",
        "industry",
        "listing",
        PERIOD,
        "test-source",
        "test-approval",
        "test-suitability",
        None,
    )
    validate_catalog((classification(),), (SOURCE,), nodes, (), (listing(),), (mapping,), ())
    for invalid in (
        replace(mapping, node_type="sector"),
        replace(mapping, listing_id="unknown"),
        replace(mapping, period=Period(date(2019, 1, 1))),
    ):
        with pytest.raises(CatalogError):
            validate_catalog(
                (classification(),), (SOURCE,), nodes, (), (listing(),), (invalid,), ()
            )
    with pytest.raises(CatalogError):
        validate_catalog(
            (classification(),),
            (SOURCE,),
            nodes,
            (),
            (listing(is_primary=False),),
            (mapping,),
            (),
        )


def test_benchmark_purpose_and_overlap() -> None:
    benchmark = Benchmark(
        "benchmark",
        "US",
        "market_sentiment",
        "Test",
        "listing",
        PERIOD,
        "test-source",
        "test-approval",
    )
    validate_catalog((classification(),), (SOURCE,), (), (), (listing(),), (), (benchmark,))
    with pytest.raises(CatalogError):
        replace(benchmark, purpose="arbitrary")
    with pytest.raises(CatalogError):
        validate_catalog(
            (classification(),),
            (SOURCE,),
            (),
            (),
            (listing(),),
            (),
            (benchmark, replace(benchmark, benchmark_id="other")),
        )


def test_basket_exact_decimal_weights() -> None:
    basket = Basket(
        "basket",
        SCOPE,
        "industry",
        "Test",
        PERIOD,
        "test-source",
        "test-approval",
        (
            BasketConstituent("one", "TEST_ONE", Decimal("33.3333333333333333333333333333")),
            BasketConstituent("two", "TEST_TWO", Decimal("66.6666666666666666666666666667")),
        ),
        "reviewed",
    )
    assert basket.constituents[0].weight.as_tuple().exponent == -28
    with pytest.raises(CatalogError):
        replace(basket, constituents=(BasketConstituent("one", "TEST_ONE", Decimal("99.9")),))


def test_ledger_is_immutable_typed_and_utc() -> None:
    record = LedgerRecord(
        "publication",
        "operation",
        1,
        datetime(2026, 10, 31, tzinfo=UTC),
        Publication("operation", None, "bootstrap", False),
        None,
    )
    assert record.payload.action == "bootstrap"
    for changes in (
        {"record_type": "unknown"},
        {"sequence": True},
        {"sequence": 0},
        {"recorded_at": datetime(2026, 10, 31)},
        {"payload": {"action": "bootstrap"}},
    ):
        with pytest.raises(CatalogError):
            replace(record, **changes)


def test_region_scopes_and_artifact_counts() -> None:
    region = Region(
        "US",
        "Test",
        "active",
        "partial",
        "Test-only scope",
        date(2026, 10, 30),
        None,
        (classification(),),
    )
    assert region.classifications == (classification(),)
    with pytest.raises(CatalogError):
        replace(region, region_id="OTHER")
    artifact = Artifact("stocks", "stocks", "stocks.csv", "a" * 64, True, 0, "US", None, None)
    for changes in (
        {"row_count": -1},
        {"row_count": True},
        {"sha256": "a" * 64 + "\n"},
        {"region_id": None},
        {"path": "../stocks.csv"},
    ):
        with pytest.raises(CatalogError):
            replace(artifact, **changes)


def test_entry_parent_and_release_metadata() -> None:
    entry = CatalogEntry("release", "releases/release/manifest.json", "a" * 64)
    parent = ParentRelease("parent", "b" * 64)
    audit = Artifact("audit", "audit", "audit.jsonl", "a" * 64, True, 0, None, None, None)
    release = CatalogRelease(
        entry.release_id,
        datetime(2026, 10, 31, tzinfo=UTC),
        parent,
        "a" * 64,
        (),
        (SOURCE,),
        (audit,),
        (),
    )
    assert release.parent_release is parent
    for changes in (
        {"created_at": None},
        {"created_at": datetime(2026, 10, 31)},
        {"evidence_sources": (SOURCE, SOURCE)},
        {"artifacts": ()},
        {"artifacts": (audit, audit)},
        {"regions": []},
    ):
        with pytest.raises(CatalogError):
            replace(release, **changes)
    with pytest.raises(CatalogError):
        replace(entry, manifest_path="/outside")
    with pytest.raises(CatalogError):
        replace(parent, manifest_sha256="a" * 63)


def test_research_registration_is_optional_not_approval() -> None:
    catalog = ResearchCatalog("config.py", "INDUSTRY_ETFS", "industry")
    source = ResearchSource("test-root", "/tmp/test-project", False, (catalog,))
    assert source.required is False
    for changes in ({"required": True}, {"catalogs": (catalog, catalog)}, {"root": ""}):
        with pytest.raises(CatalogError):
            replace(source, **changes)
    for changes in ({"path": "../private.py"}, {"catalog_type": "stocks"}):
        with pytest.raises(CatalogError):
            replace(catalog, **changes)


@pytest.mark.parametrize("value", ["20261030", "2026-02-30", "SECRET_DATE"])
def test_date_parser_rejects_noncontract_dates_without_echo(value: str) -> None:
    with pytest.raises(CatalogError) as error:
        parse_date(value, "date")
    assert value not in str(error.value)


@pytest.mark.parametrize(
    "value",
    [
        "2026-10-31T00:00:00",
        "2026-10-31T00:00:00+01:00",
        "SECRET_CLOCK",
    ],
)
def test_clock_parser_requires_utc_without_echo(value: str) -> None:
    with pytest.raises(CatalogError) as error:
        parse_utc(value, "clock")
    assert value not in str(error.value)


def test_non_primary_inventory_is_eligible_only_for_explicit_basket() -> None:
    held = listing(is_primary=False, instrument_type="stock")
    inventory = ListingInventory(held, "identified", None)
    definition = BasketDefinition(
        "basket", SCOPE, "industry", "Test", PERIOD, "test-source", "test-approval", "reviewed"
    )
    weight = BasketWeight("basket", held.listing_id, "100.000")
    basket = Basket(
        definition.representation_id,
        SCOPE,
        "industry",
        "Test",
        PERIOD,
        "test-source",
        "test-approval",
        (BasketConstituent(weight.listing_id, held.provider_symbol, Decimal(weight.weight)),),
        "reviewed",
    )
    validate_catalog(
        (classification(),),
        (SOURCE,),
        (node("sector", "sector"), node("industry", "industry")),
        (),
        (),
        (),
        (),
        (basket,),
        (inventory,),
    )
    for value in ("NaN", "Infinity", "0", "-1"):
        with pytest.raises(CatalogError):
            replace(weight, weight=value)
    with pytest.raises(CatalogError):
        replace(inventory, instrument_resolution_state="placeholder")


def test_inventory_conflict_and_missing_basket_history_are_not_substituted() -> None:
    held = listing(is_primary=False)
    inventory = ListingInventory(held, "identified", None)
    basket = Basket(
        "basket",
        SCOPE,
        "industry",
        "Test",
        PERIOD,
        "test-source",
        "test-approval",
        (BasketConstituent("missing", "MISSING", Decimal("100")),),
        "reviewed",
    )
    with pytest.raises(CatalogError, match="invalid_basket_listing"):
        validate_catalog(
            (classification(),),
            (SOURCE,),
            (node("sector", "sector"), node("industry", "industry")),
            (),
            (),
            (),
            (),
            (basket,),
            (inventory,),
        )

    with pytest.raises(CatalogError, match="conflicting_listing"):
        validate_catalog(
            (classification(),), (SOURCE,), (), (), (listing(),), (), (), (), (inventory,)
        )


def test_decode_typed_ledger_preserves_decimal_and_unknown_listing_identity() -> None:
    weight = BasketWeight("basket", "listing", "100.000")
    record = {
        "record_type": "basket_constituent",
        "record_id": "weight",
        "sequence": 1,
        "recorded_at": None,
        "origin": None,
        "payload": asdict(weight),
    }
    decoded = decode_ledger_record(json.dumps(record))
    assert decoded.payload == weight
    assert decoded.recorded_at is None
    inventory = ListingInventory(
        listing(instrument_type=None, is_primary=False), "identified", None
    )
    payload = asdict(inventory)
    payload["listing"]["period"] = {"start": "2020-01-01", "end": None}
    record.update(record_type="listing_inventory", payload=payload)
    assert decode_ledger_record(json.dumps(record)).payload == inventory


@pytest.mark.parametrize(
    "change",
    [
        {"record_type": "unsupported"},
        {"sequence": True},
        {"recorded_at": "2026-10-31T00:00:00"},
        {"extra": "PRIVATE_VALUE"},
        {"payload": {"action": "bootstrap"}},
        {
            "payload": {
                "operation_id": "operation",
                "expected_release": None,
                "action": "bootstrap",
                "catalog_changed": "false",
            }
        },
    ],
)
def test_ledger_decoder_rejects_invalid_fields_without_payload_echo(
    change: dict[str, object],
) -> None:
    record = {
        "record_type": "publication",
        "record_id": "operation",
        "sequence": 1,
        "recorded_at": None,
        "origin": None,
        "payload": asdict(Publication("operation", None, "bootstrap", False)),
    }
    record.update(change)
    with pytest.raises(CatalogError) as error:
        decode_ledger_record(json.dumps(record))
    assert "PRIVATE_VALUE" not in str(error.value)


def test_ledger_decoder_rejects_duplicate_json_keys() -> None:
    with pytest.raises(CatalogError, match="duplicate_key"):
        decode_ledger_record('{"record_id":"one","record_id":"two"}')


@pytest.mark.parametrize(
    "kind,payload",
    [
        (
            "node_review",
            NodeReview(SCOPE, "industry", "test-source", "test-approval", PERIOD, "review"),
        ),
        (
            "representation_approval",
            RepresentationApproval(
                "representation",
                SCOPE,
                "industry",
                "test-source",
                "test-approval",
                "suitability",
                PERIOD,
                "approval",
            ),
        ),
        (
            "basket",
            BasketDefinition(
                "basket",
                SCOPE,
                "industry",
                "Test",
                PERIOD,
                "test-source",
                "test-approval",
                "reviewed",
            ),
        ),
        (
            "collection_run",
            CollectionOccurrence(
                CollectionRun("run", "2026-10-31T00:00:00Z", "complete", ()),
                3,
            ),
        ),
        (
            "mapping_evidence",
            Evidence(
                "test",
                "/tmp/test",
                "config.py",
                "TEST",
                "Test",
                "TEST_ETF",
                "industry",
                None,
                None,
                None,
                0,
                1,
                1,
                0,
                5,
                "test-content",
                (),
                "2026-10-31T00:00:00Z",
            ),
        ),
        ("collection_evidence", CollectionEvidence("run", "evidence")),
        (
            "candidate_review",
            CandidateAssessment(
                ReviewDecision(
                    "review",
                    2,
                    "candidate",
                    "US",
                    "TEST_CLASSIFICATION",
                    "industry",
                    "2026-10-30",
                    "run",
                    "reject",
                    "Explicit test rejection",
                    "test-review",
                    ("evidence",),
                    (False, False, False),
                    (),
                    "2026-10-31T00:00:00Z",
                ),
                "TEST_VERSION",
            ),
        ),
        ("review_evidence", ReviewEvidence("review", "evidence")),
        ("representation_provenance", RepresentationProvenance("representation", "review", "run")),
        ("publication", Publication("operation", "parent", "publication", False)),
    ],
)
def test_all_supported_ledger_payloads_round_trip(kind: str, payload: object) -> None:
    record = LedgerRecord(kind, "record", 1, None, payload, None)
    raw = json.dumps(asdict(record), default=str)
    assert decode_ledger_record(raw) == record


def test_disjoint_listing_period_is_retained_without_price_eligibility() -> None:
    row = StockRow(
        "row",
        "membership",
        SCOPE,
        "instrument",
        None,
        "Test",
        "industry",
        None,
        "identified",
        Period(date(2020, 1, 1)),
        "test-source",
        "test-approval",
        "reviewed",
        listing(
            instrument_type="stock",
            period=Period(date(2018, 1, 1), date(2019, 12, 31)),
        ),
    )
    validate_catalog(
        (classification(),),
        (SOURCE,),
        (node("sector", "sector"), node("industry", "industry")),
        (row,),
        (),
        (),
        (),
    )
    assert row.provider_symbol_on(date(2026, 10, 30)) is None


def test_domain_import_succeeds_with_sql_unavailable(tmp_path: Path) -> None:
    source = Path(__file__).parents[2] / "packages/market-data/src"
    script = (
        "import sys; sys.path.insert(0, sys.argv[1]); sys.modules['sqlite3'] = None; "
        "from market_data.domain import catalog; "
        "assert not any(name.startswith('market_leadership.infrastructure') "
        "for name in sys.modules)"
    )
    subprocess.run(
        [sys.executable, "-c", script, str(source)],
        cwd=tmp_path,
        check=True,
        timeout=30,
    )
