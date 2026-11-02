import sqlite3
from datetime import UTC, date, datetime

import pytest

from market_leadership.infrastructure import region_database as module
from market_leadership.infrastructure.region_database import RegionDatabase

AUDIT_TABLES = (
    "etf_collection_runs",
    "etf_mapping_evidence",
    "etf_collection_evidence",
    "etf_candidate_reviews",
    "etf_review_evidence",
    "etf_representation_provenance",
)


def test_collection_persistence_reuses_evidence_and_preserves_revision(
    local_etf_database,
    local_etf_roots,
):
    from market_leadership.application.discover_etf_candidates import collect_etf_candidates

    database = local_etf_database
    with database.connect() as connection:
        before = connection.execute("SELECT * FROM database_metadata").fetchall()
    kwargs = dict(
        roots=local_etf_roots,
        catalogs=("stockviewer=config.py:INDUSTRY_ETFS",),
        observed_at=datetime(2026, 10, 31, tzinfo=UTC),
    )
    first = collect_etf_candidates(database, **kwargs)
    second = collect_etf_candidates(database, **kwargs)
    assert first.run.run_id != second.run.run_id
    assert first.candidates == second.candidates
    assert {e.evidence_id for e in first.evidence} == {e.evidence_id for e in second.evidence}
    with database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM etf_mapping_evidence").fetchone()[0] == 14
        assert connection.execute("SELECT count(*) FROM etf_candidate_reviews").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM entity_representations").fetchone()[0] == 0
        assert [tuple(r) for r in connection.execute("SELECT * FROM database_metadata")] == [
            tuple(r) for r in before
        ]
    assert database.get_etf_inventory(first.run.run_id).report() == first.report()


def test_collection_storage_failure_is_atomic(local_etf_database, local_etf_roots):
    from market_leadership.application.discover_etf_candidates import collect_etf_candidates

    with local_etf_database.connect() as connection:
        connection.execute(
            "CREATE TRIGGER fail_evidence BEFORE INSERT ON etf_mapping_evidence "
            "BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        collect_etf_candidates(
            local_etf_database,
            roots=local_etf_roots,
            catalogs=("stockviewer=config.py:INDUSTRY_ETFS",),
        )
    with local_etf_database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM etf_collection_runs").fetchone()[0] == 0


def test_reconciliation_covers_hierarchy_and_retains_unbound_alternatives(
    local_etf_database,
    local_etf_roots,
):
    from datetime import date

    from market_leadership.application.discover_etf_candidates import (
        collect_etf_candidates,
        review_etf_candidates,
    )

    inventory = collect_etf_candidates(
        local_etf_database,
        roots=local_etf_roots,
        catalogs=("stockviewer=config.py:INDUSTRY_ETFS",),
    )
    report = review_etf_candidates(
        local_etf_database,
        region_id="US",
        classification_id="LOCAL-ETF-TEST",
        as_of=date(2026, 10, 30),
    )
    assert len(report["nodes"]) == 4
    assert all(row["approved_status"] == "not_covered" for row in report["nodes"])
    node = next(row for row in report["nodes"] if row["name"] == "Semiconductors")
    assert {row["ticker"] for row in node["candidate_states"]} == {"SOXX", "SMH"}
    assert any("conflicting_evidence" in row["states"] for row in node["candidate_states"])
    assert report["unbound_candidates"]
    assert report["collection_run_id"] == inventory.run.run_id
    with pytest.raises(ValueError, match="scope"):
        review_etf_candidates(
            local_etf_database,
            region_id="US",
            classification_id="INVALID",
            as_of=date(2026, 10, 30),
        )


def collect(database, roots):
    from market_leadership.application.discover_etf_candidates import collect_etf_candidates

    return collect_etf_candidates(
        database,
        roots=roots,
        catalogs=("stockviewer=config.py:INDUSTRY_ETFS",),
        observed_at=datetime(2026, 10, 31, tzinfo=UTC),
    )


def accepted(database, inventory, **overrides):
    from market_data.domain.local_etf_evidence import qualification_issues
    from market_leadership.application.discover_etf_candidates import record_etf_candidate_review

    evidence = next(
        e for e in inventory.evidence if e.resource == "analyzer" and e.label == "Semiconductors"
    )
    arguments = dict(
        candidate_id=evidence.candidate_id,
        collection_run=inventory.run.run_id,
        region_id="US",
        classification_id="LOCAL-ETF-TEST",
        entity_id="local-etf-test-semiconductors",
        as_of=date(2026, 10, 30),
        decision="accept",
        reason="controlled exact scope and suitability",
        review_reference="test-only",
        evidence_ids=(evidence.evidence_id,),
        confirmations=(True, True, True),
        resolutions=tuple(
            (issue, "controlled assessment") for issue in qualification_issues(evidence)
        ),
        observed_at=datetime(2026, 10, 31, tzinfo=UTC),
    )
    arguments.update(overrides)
    return record_etf_candidate_review(database, **arguments)


def approve(database, review, **overrides):
    arguments = dict(
        region_id="US",
        classification_id="LOCAL-ETF-TEST",
        entity_type="industry",
        entity_id="local-etf-test-semiconductors",
        exchange_id="NASDAQ",
        symbol="SOXX",
        source_id="local-etf-test",
        approval_reference="test-only",
        effective_from=date(2020, 1, 1),
        candidate_review_id=review.review_id,
    )
    arguments.update(overrides)
    return database.add_entity_representation(**arguments)


def selection(database):
    from market_leadership.application.discover_etf_candidates import review_etf_candidates

    report = review_etf_candidates(
        database,
        region_id="US",
        classification_id="LOCAL-ETF-TEST",
        as_of=date(2026, 10, 30),
    )
    return next(row for row in report["nodes"] if row["name"] == "Semiconductors")


def test_end_to_end_approval_idempotent_links_and_retained_provenance(
    local_etf_database,
    local_etf_roots,
):
    database = local_etf_database
    inventory = collect(database, local_etf_roots)
    review = accepted(database, inventory)
    assert selection(database)["selected_review_status"] == "accepted_current"
    identifier = approve(database, review)
    with database.connect() as connection:
        revision = connection.execute(
            "SELECT value FROM database_metadata WHERE key='revision'"
        ).fetchone()[0]
    assert approve(database, review) == identifier
    new_review = accepted(database, collect(database, local_etf_roots))
    assert approve(database, new_review) == identifier
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM etf_representation_provenance WHERE representation_id=?",
                (identifier,),
            ).fetchone()[0]
            == 2
        )
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='revision'"
            ).fetchone()[0]
            == revision
        )
        assert connection.execute("SELECT count(*) FROM etf_review_evidence").fetchone()[0] == 2
        linked = connection.execute(
            "SELECT p.approval_run_id, er.entity_id, er.effective_from, l.symbol, m.evidence_id "
            "FROM etf_representation_provenance p "
            "JOIN entity_representations er ON er.representation_id=p.representation_id "
            "JOIN stock_listings l ON l.listing_id=er.listing_id "
            "JOIN etf_review_evidence m ON m.review_id=p.review_id WHERE p.review_id=?",
            (review.review_id,),
        ).fetchone()
        assert tuple(linked) == (
            inventory.run.run_id,
            "local-etf-test-semiconductors",
            "2020-01-01",
            "SOXX",
            review.evidence_ids[0],
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"confirmations": (False, True, True)},
        {"reason": " "},
        {"review_reference": ""},
        {"evidence_ids": ()},
        {"evidence_ids": ("unknown",)},
        {"resolutions": ()},
        {"entity_id": "not-a-node"},
        {"classification_id": "OTHER-TEST"},
        {"as_of": date(1999, 1, 1)},
        {"decision": "automatic"},
    ],
)
def test_invalid_decisions_do_not_mutate(local_etf_database, local_etf_roots, overrides):
    inventory = collect(local_etf_database, local_etf_roots)
    with pytest.raises(ValueError):
        accepted(local_etf_database, inventory, **overrides)
    with local_etf_database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM etf_candidate_reviews").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM etf_review_evidence").fetchone()[0] == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"symbol": "SMH"},
        {"source_id": "unknown"},
        {"approval_reference": "wrong"},
        {"effective_from": date(1999, 1, 1)},
        {"entity_id": "test-uncovered"},
        {"candidate_review_id": "unknown"},
        {"exchange_id": "UNKNOWN"},
    ],
)
def test_approval_prerequisites_preserve_database(local_etf_database, local_etf_roots, overrides):
    database = local_etf_database
    review = accepted(database, collect(database, local_etf_roots))
    with pytest.raises((ValueError, sqlite3.Error)):
        approve(database, review, **overrides)
    with database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM entity_representations").fetchone()[0] == 0
        assert (
            connection.execute("SELECT count(*) FROM etf_representation_provenance").fetchone()[0]
            == 0
        )


def test_provenance_failure_rolls_back_mapping_and_revision(local_etf_database, local_etf_roots):
    database = local_etf_database
    review = accepted(database, collect(database, local_etf_roots))
    with database.connect() as connection:
        revision = connection.execute(
            "SELECT value FROM database_metadata WHERE key='revision'"
        ).fetchone()[0]
        connection.execute(
            "CREATE TRIGGER fail_link BEFORE INSERT ON etf_representation_provenance "
            "BEGIN SELECT RAISE(ABORT, 'injected link failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        approve(database, review)
    with database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM entity_representations").fetchone()[0] == 0
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='revision'"
            ).fetchone()[0]
            == revision
        )


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("changed", "changed_or_removed_support"),
        ("removed", "changed_or_removed_support"),
        ("unreadable", "unobservable_support"),
        ("new_conflict", "new_or_changed_conflicting_evidence"),
    ],
)
def test_source_mutations_require_review_without_changing_existing_approval(
    local_etf_database,
    local_etf_roots,
    mutation,
    expected,
):
    database = local_etf_database
    review = accepted(database, collect(database, local_etf_roots))
    identifier = approve(database, review)
    path = local_etf_roots["analyzer"] / "config.py"
    original = path.read_text()
    if mutation == "changed":
        path.write_text(original.replace('"SOXX"', '"SMH"'))
    elif mutation == "removed":
        path.write_text("INDUSTRY_ETFS = {}\n")
    elif mutation == "unreadable":
        path.write_text("INDUSTRY_ETFS = { broken syntax\n")
    else:
        path.write_text(original + "\nINDUSTRY_ETFS = {'Semiconductors': 'NEW'}\n")
    collect(database, local_etf_roots)
    row = selection(database)
    assert row["selected_review_status"] == "accepted_needs_re_review"
    assert expected in row["re_review_reasons"]
    with pytest.raises(ValueError, match="review"):
        approve(database, review)
    with database.connect() as connection:
        assert (
            connection.execute("SELECT representation_id FROM entity_representations").fetchone()[0]
            == identifier
        )
    path.write_text(original)
    collect(database, local_etf_roots)
    assert selection(database)["selected_review_status"] == "accepted_current"


def test_location_only_unrelated_changes_and_missing_roots_do_not_invalidate_support(
    local_etf_database,
    local_etf_roots,
):
    database = local_etf_database
    review = accepted(database, collect(database, local_etf_roots))
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text(
        "\n\n" + path.read_text().replace("excluded-fixture-value", "different-private")
    )
    local_etf_roots["stockviewer"] /= "missing"
    collect(database, local_etf_roots)
    assert selection(database)["selected_review_status"] == "accepted_current"
    approve(database, review)


def test_rejection_clears_selection_without_fallback_and_index_cannot_be_accepted(
    local_etf_database,
    local_etf_roots,
):
    database = local_etf_database
    inventory = collect(database, local_etf_roots)
    first = accepted(database, inventory)
    second = accepted(database, inventory)
    accepted(
        database, inventory, decision="reject", confirmations=(False, False, False), resolutions=()
    )
    assert selection(database)["selected_review_status"] == "none"
    with pytest.raises(ValueError, match="selection"):
        approve(database, first)
    with pytest.raises(ValueError, match="selection"):
        approve(database, second)
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text("INDUSTRY_ETFS = {'Semiconductors': '^INDEX'}")
    with pytest.raises(ValueError, match="non-ETF"):
        accepted(database, collect(database, local_etf_roots))


def test_partial_baseline_requires_explicit_complete_review(local_etf_database, local_etf_roots):
    database = local_etf_database
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text("INDUSTRY_ETFS = {'Semiconductors': 'SOXX', 'Bad': call()}")
    review = accepted(database, collect(database, local_etf_roots))
    with pytest.raises(ValueError, match="review"):
        approve(database, review)
    path.write_text("INDUSTRY_ETFS = {'Semiconductors': 'SOXX'}")
    complete = collect(database, local_etf_roots)
    with pytest.raises(ValueError, match="review"):
        approve(database, review)
    approve(database, accepted(database, complete))


def test_review_uses_explicit_historical_date_not_observation_clock(
    local_etf_database,
    local_etf_roots,
):
    with local_etf_database.connect() as connection:
        connection.execute(
            "UPDATE industries SET effective_to='2026-10-30' "
            "WHERE industry_id='local-etf-test-semiconductors'"
        )
    inventory = collect(local_etf_database, local_etf_roots)
    review = accepted(local_etf_database, inventory)
    assert review.as_of == "2026-10-30"
    approve(local_etf_database, review, effective_to=date(2026, 10, 30))
    with pytest.raises(ValueError, match="inactive"):
        accepted(local_etf_database, inventory, as_of=date(2026, 10, 31))


def test_unobservable_qualification_context_is_unknown_not_changed(
    local_etf_database,
    local_etf_roots,
):
    finder = local_etf_roots["stockfinder"] / "src/stockfinder/data.py"
    original = finder.read_text() + "\nUS_SECTOR_ETFS = {'Chip sector': 'SOXX'}\n"
    finder.write_text(original)
    review = accepted(local_etf_database, collect(local_etf_database, local_etf_roots))
    finder.write_text("INDUSTRY_ETFS = {invalid syntax\n")
    collect(local_etf_database, local_etf_roots)
    reasons = selection(local_etf_database)["re_review_reasons"]
    assert "unobservable_qualification_context" in reasons
    assert "changed_or_removed_support" not in reasons
    with pytest.raises(ValueError, match="review"):
        approve(local_etf_database, review)
    finder.write_text(original)
    collect(local_etf_database, local_etf_roots)
    assert selection(local_etf_database)["selected_review_status"] == "accepted_current"


@pytest.mark.parametrize(
    "column,value",
    [
        ("resolution_state", "unverified"),
        ("is_primary", 0),
        ("effective_to", "2025-01-01"),
    ],
)
def test_listing_verification_and_interval_cannot_be_replaced_by_research(
    local_etf_database,
    local_etf_roots,
    column,
    value,
):
    database = local_etf_database
    review = accepted(database, collect(database, local_etf_roots))
    with database.connect() as connection:
        connection.execute(f"UPDATE stock_listings SET {column}=? WHERE symbol='SOXX'", (value,))
    with pytest.raises(ValueError, match="listing"):
        approve(database, review)
    with database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM entity_representations").fetchone()[0] == 0


def test_changed_root_requires_new_explicit_binding(local_etf_database, local_etf_roots, tmp_path):
    import shutil

    review = accepted(local_etf_database, collect(local_etf_database, local_etf_roots))
    root = tmp_path / "replacement-source"
    shutil.copytree(local_etf_roots["analyzer"], root)
    local_etf_roots["analyzer"] = root
    collect(local_etf_database, local_etf_roots)
    assert selection(local_etf_database)["selected_review_status"] == "accepted_needs_re_review"
    with pytest.raises(ValueError, match="review"):
        approve(local_etf_database, review)
    approve(
        local_etf_database,
        accepted(local_etf_database, collect(local_etf_database, local_etf_roots)),
    )


def test_upgrade_retains_existing_etf_basket_and_all_reviewed_data(representation_database):
    from decimal import Decimal

    database = representation_database
    with database.connect() as connection:
        listings = [
            row[0]
            for row in connection.execute(
                "SELECT listing_id FROM stock_listings "
                "WHERE symbol IN ('AAA', 'BBB') ORDER BY symbol"
            )
        ]
    database.add_stock_basket(
        region_id="US",
        classification_id="TEST",
        entity_id="test-cloud",
        name="Controlled basket",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
        constituents=((listings[0], Decimal("60")), (listings[1], Decimal("40"))),
    )
    database.add_entity_representation(
        region_id="US",
        classification_id="TEST",
        entity_type="industry",
        entity_id="test-cloud",
        exchange_id="NASDAQ",
        symbol="AAA",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
    )
    tables = (
        "database_metadata",
        "regions",
        "classifications",
        "industries",
        "data_sources",
        "stocks",
        "stock_listings",
        "stock_memberships",
        "entity_representations",
        "stock_baskets",
        "basket_constituents",
    )
    with database.connect() as connection:
        for table in reversed(AUDIT_TABLES):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("UPDATE database_metadata SET value='2' WHERE key='schema_version'")
        before = {
            table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
            for table in tables
            if table != "database_metadata"
        }
        revision = connection.execute(
            "SELECT value FROM database_metadata WHERE key='revision'"
        ).fetchone()[0]
    database.initialize()
    with database.connect() as connection:
        for table, rows in before.items():
            assert [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")] == rows
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='revision'"
            ).fetchone()[0]
            == revision
        )


def test_every_explicitly_bound_relationship_requires_review_after_source_change(
    local_etf_database,
    local_etf_roots,
):
    from market_leadership.application.discover_etf_candidates import review_etf_candidates

    database = local_etf_database
    inventory = collect(database, local_etf_roots)
    accepted(database, inventory)
    before = review_etf_candidates(
        database,
        region_id="US",
        classification_id="OTHER-TEST",
        as_of=date(2026, 10, 30),
    )
    assert all(row["selected_review_status"] == "none" for row in before["nodes"])
    accepted(
        database,
        inventory,
        classification_id="OTHER-TEST",
        entity_id="other-test-other-semiconductors",
    )
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text(path.read_text().replace('"SOXX"', '"SMH"'))
    collect(database, local_etf_roots)
    affected = []
    for classification in ("LOCAL-ETF-TEST", "OTHER-TEST"):
        report = review_etf_candidates(
            database,
            region_id="US",
            classification_id=classification,
            as_of=date(2026, 10, 30),
        )
        affected.extend(row for row in report["nodes"] if row["selected_review_id"] is not None)
    assert len(affected) == 2
    assert all(row["selected_review_status"] == "accepted_needs_re_review" for row in affected)


def test_schema_three_initialization_and_idempotence(tmp_path):
    database = RegionDatabase(tmp_path / "fresh.sqlite")
    database.initialize()
    database.initialize()
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='schema_version'"
            ).fetchone()[0]
            == "3"
        )
        for table in AUDIT_TABLES:
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


@pytest.mark.parametrize("version", [1, 2])
def test_legacy_upgrade_preserves_data(tmp_path, version):
    database = RegionDatabase(tmp_path / "legacy.sqlite")
    with database.connect() as connection:
        connection.executescript(module._SCHEMA)
        connection.execute(
            "UPDATE database_metadata SET value=? WHERE key='schema_version'", (str(version),)
        )
        connection.execute("UPDATE database_metadata SET value='17' WHERE key='revision'")
    database.initialize()
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='revision'"
            ).fetchone()[0]
            == "17"
        )
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='schema_version'"
            ).fetchone()[0]
            == "3"
        )


def test_unknown_version_rejected_before_schema_writes(tmp_path, monkeypatch):
    database = RegionDatabase(tmp_path / "unknown.sqlite")
    with database.connect() as connection:
        connection.executescript(module._SCHEMA)
        connection.execute("UPDATE database_metadata SET value='999' WHERE key='schema_version'")
    monkeypatch.setattr(module, "_SCHEMA", module._SCHEMA + "\nCREATE TABLE forbidden(x);\n")
    with pytest.raises(ValueError, match="Unsupported"):
        database.initialize()
    with database.connect() as connection:
        assert (
            connection.execute("SELECT 1 FROM sqlite_master WHERE name='forbidden'").fetchone()
            is None
        )


def test_schema_failure_rolls_back_entire_migration(tmp_path, monkeypatch):
    database = RegionDatabase(tmp_path / "broken.sqlite")
    with database.connect() as connection:
        connection.executescript(module._SCHEMA)
    monkeypatch.setattr(
        module,
        "_ETF_EVIDENCE_SCHEMA",
        "CREATE TABLE etf_collection_runs(x);\nINVALID SQL;\n",
        raising=False,
    )
    with pytest.raises(ValueError, match="initialize"):
        database.initialize()
    with database.connect() as connection:
        assert (
            connection.execute(
                "SELECT value FROM database_metadata WHERE key='schema_version'"
            ).fetchone()[0]
            == "1"
        )
        assert (
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name='etf_collection_runs'"
            ).fetchone()
            is None
        )
        assert "node_type" not in {
            row["name"] for row in connection.execute("PRAGMA table_info(industries)")
        }
