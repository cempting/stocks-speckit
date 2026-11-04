from datetime import date
from pathlib import Path

import pytest

from market_data_tools.legacy.region_database import RegionDatabase
from market_data_tools.legacy.universe_import import (
    ImportReport,
    import_reviewed_file,
    validate_import,
)


def _csv(path: Path, contents: str) -> Path:
    path.write_text(contents, encoding="utf-8")
    return path


def _published_snapshot(database: RegionDatabase) -> dict[str, list[tuple[object, ...]]]:
    tables = (
        "regions",
        "classifications",
        "sectors",
        "industries",
        "stocks",
        "stock_listings",
        "stock_memberships",
    )
    with database.connect() as connection:
        snapshot = {
            table: [
                tuple(row)
                for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            ]
            for table in tables
        }
        snapshot["metadata"] = [
            tuple(row)
            for row in connection.execute(
                "SELECT key, value FROM database_metadata ORDER BY key"
            ).fetchall()
        ]
    return snapshot


def test_validation_reports_placeholders_unclassified_rows_and_conflicts(tmp_path: Path) -> None:
    source = _csv(
        tmp_path / "input.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,ResolutionState\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud,identified\n"
        "stock-b,BBB,Beta,NASDAQ,,,identified\n"
        "stock-c,,Unresolved,NASDAQ,Technology,Cloud,placeholder\n"
        "stock-d,DDD,Delta,NASDAQ,Finance,Banks,identified\n"
        "stock-d,DDD,Delta,NASDAQ,Technology,Cloud,identified\n",
    )

    report = validate_import(
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
    )

    assert report.status == "validated"
    assert report.accepted_rows == 3
    assert report.placeholder_rows == 1
    assert report.unclassified_rows == 1
    assert report.conflicting_rows == 2
    assert report.issues
    assert any("conflict" in issue.kind for issue in report.issues)


def test_missing_classification_values_are_imported_as_unclassified(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    source = _csv(
        tmp_path / "input.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,undefined,undefined\n"
        "stock-b,BBB,Beta,NASDAQ,Technology,\n",
    )

    report = import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="candidate exchange file",
        approval_reference="review-1",
    )

    assert report.status == "committed_partial"
    assert report.accepted_rows == 2
    assert report.inserted_rows == 2
    assert report.unclassified_rows == 2
    with database.connect() as connection:
        stocks = connection.execute(
            "SELECT classification_state FROM stocks ORDER BY instrument_id"
        ).fetchall()
        memberships = connection.execute("SELECT COUNT(*) FROM stock_memberships").fetchone()
    assert [row["classification_state"] for row in stocks] == [
        "unclassified",
        "unclassified",
    ]
    assert memberships[0] == 0


def test_partial_import_is_idempotent_and_reports_conflicting_rows(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    source = _csv(
        tmp_path / "input.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n"
        "stock-b,BBB,Beta,NASDAQ,,\n"
        "stock-c,CCC,Gamma,NASDAQ,Finance,Banks\n"
        "stock-c,CCC,Gamma,NASDAQ,Technology,Cloud\n",
    )

    first = import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="candidate exchange file",
        approval_reference="review-1",
    )
    second = import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="candidate exchange file",
        approval_reference="review-1",
    )

    assert first.status == "committed_partial"
    assert first.accepted_rows == 2
    assert first.conflicting_rows == 2
    assert second.status == "committed_partial"
    assert second.inserted_rows == 0
    assert (
        len(
            database.get_industry_members(
                "US", "TEST", "test-cloud", as_of=first.completed_at.date()
            )
        )
        == 1
    )
    assert database.get_region("US").coverage_state == "partial"


def test_structurally_invalid_import_does_not_change_database(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    good = _csv(
        tmp_path / "good.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        good,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="reviewed",
        approval_reference="review-1",
    )
    invalid = _csv(
        tmp_path / "invalid.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-b,BBB,Beta,NASDAQ,Technology,Cloud,unexpected\n",
    )
    before = database.get_industry_members(
        "US", "TEST", "test-cloud", as_of=database.get_region("US").coverage_as_of
    )

    try:
        import_reviewed_file(
            database,
            invalid,
            region_id="US",
            classification_id="TEST",
            source_id="source-b",
            exchange_id=None,
            coverage="invalid",
            approval_reference="review-2",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("structurally invalid input must be rejected")

    after = database.get_industry_members(
        "US", "TEST", "test-cloud", as_of=database.get_region("US").coverage_as_of
    )
    assert after == before


def test_second_local_source_reports_conflict_without_overwriting_membership(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    conflicting = _csv(
        tmp_path / "conflicting.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Finance,Banks\n",
    )
    import_reviewed_file(
        database,
        original,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="source A",
        approval_reference="review-1",
    )
    report = import_reviewed_file(
        database,
        conflicting,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="source B",
        approval_reference="review-2",
    )

    assert report.status == "rejected"
    assert report.conflicting_rows > 0
    members = database.get_industry_members("US", "TEST", "test-cloud", as_of=date(2026, 10, 30))
    assert [member.instrument_id for member in members] == ["stock-a"]
    assert members[0].industry_name == "Cloud"


def test_fully_rejected_import_preserves_published_state_but_records_audit(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        original,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="original reviewed scope",
        approval_reference="review-1",
    )
    before = _published_snapshot(database)
    rejected = _csv(
        tmp_path / "rejected.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,ResolutionState\n"
        "stock-a,,Renamed Alpha,,Finance,Banks,placeholder\n",
    )

    report = import_reviewed_file(
        database,
        rejected,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="rejected scope",
        approval_reference="review-2",
    )

    assert report.status == "rejected"
    assert report.accepted_rows == 0
    assert _published_snapshot(database) == before
    with database.connect() as connection:
        run = connection.execute(
            "SELECT status, issue_count FROM import_runs WHERE source_id = 'source-b'"
        ).fetchone()
        issues = connection.execute(
            """
            SELECT issue_kind FROM import_issues
            WHERE import_run_id = (
                SELECT import_run_id FROM import_runs WHERE source_id = 'source-b'
            )
            """
        ).fetchall()
    assert run["status"] == "rejected"
    assert run["issue_count"] > 0
    assert issues


def test_quarantined_row_leaves_no_dependent_records_beside_accepted_row(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        original,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="original reviewed scope",
        approval_reference="review-1",
    )
    mixed = _csv(
        tmp_path / "mixed.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-b,BBB,Beta,NASDAQ,Finance,Banks\n"
        "stock-c,AAA,Gamma,NASDAQ,Health,Devices\n",
    )

    report = import_reviewed_file(
        database,
        mixed,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="mixed reviewed scope",
        approval_reference="review-2",
    )

    assert report.status == "committed_partial"
    assert report.accepted_rows == 1
    assert report.conflicting_rows > 0
    with database.connect() as connection:
        stocks = {
            row["instrument_id"]
            for row in connection.execute("SELECT instrument_id FROM stocks").fetchall()
        }
        industries = {
            row["industry_id"]
            for row in connection.execute("SELECT industry_id FROM industries").fetchall()
        }
        members = {
            row["instrument_id"]
            for row in connection.execute("SELECT instrument_id FROM stock_memberships").fetchall()
        }
    assert stocks == {"stock-a", "stock-b"}
    assert industries == {"test-cloud", "test-banks"}
    assert members == {"stock-a", "stock-b"}


def test_reviewed_import_promotes_placeholder_and_classification_state(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    placeholder = _csv(
        tmp_path / "placeholder.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,ResolutionState\n"
        "stock-a,,Alpha,,Technology,Cloud,placeholder\n",
    )
    import_reviewed_file(
        database,
        placeholder,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="placeholder",
        approval_reference="review-1",
    )
    verified = _csv(
        tmp_path / "verified.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        verified,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="verified listing",
        approval_reference="review-2",
    )

    with database.connect() as connection:
        stock = connection.execute(
            "SELECT resolution_state, classification_state FROM stocks WHERE instrument_id = ?",
            ("stock-a",),
        ).fetchone()
    assert tuple(stock) == ("identified", "classified")


def test_incomplete_later_import_does_not_downgrade_classified_stock(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    classified = _csv(
        tmp_path / "classified.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        classified,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="classified",
        approval_reference="review-1",
    )
    incomplete = _csv(
        tmp_path / "incomplete.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,,\n",
    )
    import_reviewed_file(
        database,
        incomplete,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="incomplete follow-up",
        approval_reference="review-2",
    )

    with database.connect() as connection:
        stock = connection.execute(
            "SELECT resolution_state, classification_state FROM stocks WHERE instrument_id = ?",
            ("stock-a",),
        ).fetchone()
    assert tuple(stock) == ("identified", "classified")


def test_reviewed_membership_promotes_existing_unclassified_stock(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    unclassified = _csv(
        tmp_path / "unclassified.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,,\n",
    )
    import_reviewed_file(
        database,
        unclassified,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="unclassified listing",
        approval_reference="review-1",
    )
    classified = _csv(
        tmp_path / "classified.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        classified,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="reviewed membership",
        approval_reference="review-2",
    )

    with database.connect() as connection:
        stock = connection.execute(
            "SELECT classification_state FROM stocks WHERE instrument_id = ?",
            ("stock-a",),
        ).fetchone()
        memberships = connection.execute(
            "SELECT COUNT(*) FROM stock_memberships WHERE instrument_id = ?",
            ("stock-a",),
        ).fetchone()[0]
    assert stock["classification_state"] == "classified"
    assert memberships == 1


def test_validation_checks_existing_database_conflicts_without_writing(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        original,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="original",
        approval_reference="review-1",
    )
    before = _published_snapshot(database)
    conflicting = _csv(
        tmp_path / "conflicting.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Finance,Banks\n",
    )

    report = validate_import(
        conflicting,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        database=database,
    )

    assert report.accepted_rows == 0
    assert report.conflicting_rows > 0
    assert any(issue.kind == "classification_conflict" for issue in report.issues)
    assert _published_snapshot(database) == before


def test_validation_detects_inconsistent_identity_within_input(tmp_path: Path) -> None:
    source = _csv(
        tmp_path / "inconsistent.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n"
        "stock-a,BBB,Changed Name,NYSE,Technology,Cloud\n",
    )

    report = validate_import(
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
    )

    assert report.accepted_rows == 0
    assert any(issue.kind == "identity_conflict" for issue in report.issues)


def test_replay_restores_database_conflict_diagnostics(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    conflicting = _csv(
        tmp_path / "conflicting.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Finance,Banks\n",
    )
    import_reviewed_file(
        database,
        original,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="original",
        approval_reference="review-1",
    )
    first = import_reviewed_file(
        database,
        conflicting,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="conflicting",
        approval_reference="review-2",
    )
    replay = import_reviewed_file(
        database,
        conflicting,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        exchange_id=None,
        coverage="conflicting",
        approval_reference="review-2",
    )

    assert first.status == replay.status == "rejected"
    assert replay.inserted_rows == 0
    assert replay.conflicting_rows == first.conflicting_rows > 0
    assert replay.issues == first.issues


def test_replay_rejects_changed_review_or_classification_context(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    source = _csv(
        tmp_path / "input.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="reviewed",
        approval_reference="review-1",
    )

    try:
        import_reviewed_file(
            database,
            source,
            region_id="US",
            classification_id="TEST",
            source_id="source-a",
            exchange_id=None,
            coverage="reviewed",
            approval_reference="changed-review",
        )
    except ValueError as error:
        assert "source id" in str(error).lower()
    else:
        raise AssertionError("a replay under a different approval must be rejected")

    try:
        import_reviewed_file(
            database,
            source,
            region_id="CA",
            classification_id="OTHER",
            source_id="source-a",
            exchange_id=None,
            coverage="reviewed",
            approval_reference="review-1",
        )
    except ValueError as error:
        assert "context" in str(error).lower()
    else:
        raise AssertionError("a replay under a different region/classification must be rejected")


def test_region_coverage_combines_exchange_and_chart_only_sources(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    exchange = _csv(
        tmp_path / "exchange.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    chart_only = _csv(
        tmp_path / "chart-only.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "chart-a,SPY,Market Fund,NYSE,,\n",
    )
    import_reviewed_file(
        database,
        exchange,
        region_id="US",
        classification_id="TEST",
        source_id="exchange-source",
        exchange_id=None,
        coverage="NASDAQ and NYSE exchange listings",
        approval_reference="review-exchange",
    )
    import_reviewed_file(
        database,
        chart_only,
        region_id="US",
        classification_id="TEST",
        source_id="chart-source",
        exchange_id=None,
        coverage="chart proxy listings only",
        approval_reference="review-chart",
    )

    region = database.get_region("US")

    assert "NASDAQ and NYSE exchange listings" in region.coverage_description
    assert "chart proxy listings only" in region.coverage_description
    assert region.coverage_state == "partial"


def _reviewed(
    database: RegionDatabase,
    source: Path,
    *,
    source_id: str = "source-a",
    classification_id: str = "TEST",
    region_id: str = "US",
    coverage: str = "reviewed listings",
) -> ImportReport:
    return import_reviewed_file(
        database,
        source,
        region_id=region_id,
        classification_id=classification_id,
        source_id=source_id,
        exchange_id=None,
        coverage=coverage,
        approval_reference=f"review-{source_id}",
    )


@pytest.mark.parametrize(
    ("sector_name", "classification_id"),
    [("Renamed Technology", "TEST"), ("Technology", "test")],
)
def test_validate_and_import_reject_existing_sector_identity_conflicts(
    tmp_path: Path, sector_name: str, classification_id: str
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,SectorId\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud,technology\n",
    )
    _reviewed(database, original)
    conflicting = _csv(
        tmp_path / "conflicting.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,SectorId\n"
        f"stock-b,BBB,Beta,NASDAQ,{sector_name},Devices,technology\n",
    )
    before = _published_snapshot(database)

    validation = validate_import(
        conflicting,
        region_id="US",
        classification_id=classification_id,
        source_id="source-b",
        database=database,
    )
    assert validation.accepted_rows == 0
    assert any("sector" in issue.detail.lower() for issue in validation.issues)
    assert _published_snapshot(database) == before

    imported = _reviewed(
        database,
        conflicting,
        source_id="source-b",
        classification_id=classification_id,
    )
    assert imported.status == "rejected"
    assert imported.issues == validation.issues
    assert _published_snapshot(database) == before


@pytest.mark.parametrize(
    ("provider_symbol", "currency", "effective_to"),
    [("AAA.NEW", "USD", ""), ("AAA", "CAD", ""), ("AAA", "USD", "2030-01-01")],
)
def test_validation_shares_import_listing_identity_checks(
    tmp_path: Path, provider_symbol: str, currency: str, effective_to: str
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    _reviewed(database, original)
    conflicting = _csv(
        tmp_path / "conflicting.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,ProviderSymbol,Currency,EffectiveTo\n"
        f"stock-a,AAA,Alpha,NASDAQ,Technology,Cloud,{provider_symbol},{currency},{effective_to}\n",
    )
    before = _published_snapshot(database)

    validation = validate_import(
        conflicting,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        database=database,
    )
    assert validation.accepted_rows == 0
    assert any(issue.kind == "listing_conflict" for issue in validation.issues)
    assert _published_snapshot(database) == before

    imported = _reviewed(database, conflicting, source_id="source-b")
    assert imported.status == "rejected"
    assert imported.issues == validation.issues
    assert _published_snapshot(database) == before


def test_validation_reports_classification_owned_by_another_region(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    source = _csv(
        tmp_path / "members.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    _reviewed(database, source)
    before = _published_snapshot(database)

    validation = validate_import(
        source,
        region_id="CA",
        classification_id="TEST",
        source_id="source-b",
        database=database,
    )
    assert validation.accepted_rows == 0
    assert any("region" in issue.detail.lower() for issue in validation.issues)
    assert _published_snapshot(database) == before

    imported = _reviewed(database, source, source_id="source-b", region_id="CA")
    assert imported.status == "rejected"
    assert imported.issues == validation.issues
    assert _published_snapshot(database) == before


def test_coverage_recovers_legacy_sources_from_all_regional_associations(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    original = _csv(
        tmp_path / "first.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    _reviewed(database, original, coverage="first exchange")
    second = _csv(
        tmp_path / "second.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-b,BBB,Beta,NYSE,Technology,Cloud\n",
    )
    second_coverage = "second exchange; descriptive text — not a source ID"
    _reviewed(database, second, source_id="source-b", coverage=second_coverage)
    chart = _csv(
        tmp_path / "chart.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "chart-a,SPY,Market Fund,NYSE,,\n",
    )
    _reviewed(database, chart, source_id="chart-source", coverage="chart-only scope")
    with database.connect() as connection:
        connection.execute(
            "DELETE FROM database_metadata WHERE key LIKE 'regional_reviewed_coverage:%'"
        )
        connection.execute(
            "UPDATE regions SET coverage_description = 'chart-only scope' WHERE region_id = 'US'"
        )
        connection.executemany(
            """
            INSERT INTO data_sources (
                source_id, source_type, description, coverage, authority, approval_reference
            ) VALUES (?, 'local_file', ?, ?, 'reviewed_local', 'review-legacy')
            """,
            [
                ("member-source", "legacy memberships", "membership-only scope"),
                ("representation-source", "legacy representations", "representation-only scope"),
            ],
        )
        connection.execute(
            "UPDATE stock_memberships SET source_id = 'member-source' "
            "WHERE instrument_id = 'stock-a'"
        )
        connection.execute(
            """
            INSERT INTO entity_representations (
                representation_id, region_id, classification_id, entity_type, entity_id,
                listing_id, effective_from, source_id
            )
            SELECT 'legacy-representation', 'US', 'TEST', 'sector', 'test-technology',
                   listing_id, '1970-01-01', 'representation-source'
            FROM stock_listings WHERE instrument_id = 'chart-a'
            """
        )
    latest = _csv(
        tmp_path / "latest.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-c,CCC,Gamma,NASDAQ,Technology,Cloud\n",
    )

    _reviewed(database, latest, source_id="source-c", coverage="latest reviewed scope")

    region = database.get_region("US")
    assert region.coverage_description == (
        "Reviewed sources: chart-source — chart-only scope; "
        "member-source — membership-only scope; "
        "representation-source — representation-only scope; "
        "source-a — first exchange; "
        f"source-b — {second_coverage}; source-c — latest reviewed scope"
    )
    assert region.coverage_state == "partial"


@pytest.mark.parametrize("source_id", ["source-a", "second-exchange"])
def test_legacy_replay_without_persisted_context_is_rejected_without_guessing(
    tmp_path: Path, source_id: str
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    if source_id == "second-exchange":
        initial = _csv(
            tmp_path / "initial.csv",
            "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
            "stock-b,BBB,Beta,NYSE,Technology,Cloud\n",
        )
        _reviewed(database, initial)
    source = _csv(
        tmp_path / "members.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    original = _reviewed(database, source, source_id=source_id)
    with database.connect() as connection:
        connection.execute(
            "UPDATE import_runs SET input_fingerprint = ? WHERE source_id = ?",
            (original.input_fingerprint, source_id),
        )
    before = _published_snapshot(database)

    with pytest.raises(ValueError, match="Legacy.*context"):
        _reviewed(database, source, source_id=source_id)

    assert _published_snapshot(database) == before


def test_multiple_errors_for_one_row_count_as_one_conflicting_row_on_replay(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    _reviewed(database, original)
    conflicting = _csv(
        tmp_path / "conflicting.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,ProviderSymbol\n"
        "stock-a,AAA,Changed Name,NASDAQ,Finance,Banks,AAA.NEW\n",
    )

    validation = validate_import(
        conflicting,
        region_id="US",
        classification_id="TEST",
        source_id="source-b",
        database=database,
    )
    imported = _reviewed(database, conflicting, source_id="source-b")
    replay = _reviewed(database, conflicting, source_id="source-b")

    for report in (validation, imported, replay):
        assert report.row_count == 1
        assert report.conflicting_rows == 1
        assert len(report.issues) >= 3
    assert validation.issues == imported.issues == replay.issues


def test_coverage_retains_accepted_source_without_new_listing_or_membership(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    _reviewed(database, original, coverage="first reviewed scope")
    duplicate = _reviewed(
        database, original, source_id="duplicate-review", coverage="independent reviewed scope"
    )
    assert duplicate.accepted_rows == 1
    assert duplicate.inserted_rows == 0
    latest = _csv(
        tmp_path / "latest.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-b,BBB,Beta,NASDAQ,Technology,Cloud\n",
    )

    _reviewed(database, latest, source_id="source-b", coverage="latest reviewed scope")

    description = database.get_region("US").coverage_description
    assert "duplicate-review — independent reviewed scope" in description
    assert "source-a — first reviewed scope" in description
    assert "source-b — latest reviewed scope" in description


def test_coverage_preserves_previous_reviewed_scope_when_source_scope_changes(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    original = _csv(
        tmp_path / "original.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
    )
    _reviewed(database, original, coverage="historical exchange scope")
    latest = _csv(
        tmp_path / "latest.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-b,BBB,Beta,NASDAQ,Technology,Cloud\n",
    )

    _reviewed(database, latest, coverage="new reviewed scope")

    description = database.get_region("US").coverage_description
    assert "historical exchange scope" in description
    assert "new reviewed scope" in description
