from datetime import date
from pathlib import Path

from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.universe_import import (
    import_reviewed_file,
    validate_import,
)


def _csv(path: Path, contents: str) -> Path:
    path.write_text(contents, encoding="utf-8")
    return path


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
