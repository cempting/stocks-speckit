import sqlite3
from datetime import date
from pathlib import Path

import pytest

from market_data_tools.legacy.region_database import RegionDatabase
from market_data_tools.legacy.universe_import import import_reviewed_file


def _write_csv(path: Path, rows: str) -> Path:
    path.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom\n" + rows,
        encoding="utf-8",
    )
    return path


def test_initialize_and_query_region_scoped_unique_industry_members(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    first = _write_csv(
        tmp_path / "first.csv",
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n"
        "instrument-b,BBB,Beta,NYSE,Technology,Cloud,2020-01-01\n",
    )
    second = _write_csv(
        tmp_path / "second.csv",
        "instrument-a,AAA.A,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n",
    )
    for source_id, path in (("source-a", first), ("source-b", second)):
        import_reviewed_file(
            database,
            path,
            region_id="US",
            classification_id="TEST",
            source_id=source_id,
            exchange_id=None,
            coverage="controlled listings",
            approval_reference="review-1",
        )

    members = database.get_industry_members("US", "TEST", "test-cloud", as_of=date(2026, 10, 30))

    assert [member.instrument_id for member in members] == ["instrument-a", "instrument-b"]
    assert len(members[0].listings) == 2
    assert database.get_region("US").coverage_state == "unverified"


def test_schema_enforces_foreign_keys_and_one_active_primary_listing(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO regions (
                region_id, name, coverage_state, coverage_description, coverage_as_of
            ) VALUES ('US', 'United States', 'unverified', 'test', '2026-10-30')
            """
        )
        connection.execute(
            """
            INSERT INTO data_sources (source_id, source_type, description)
            VALUES ('source', 'local_file', 'Test source')
            """
        )
        connection.execute(
            """
            INSERT INTO stocks (instrument_id, name, resolution_state, classification_state)
            VALUES ('stock', 'Stock', 'identified', 'classified')
            """
        )
        connection.execute(
            """
            INSERT INTO stock_listings (
                listing_id, instrument_id, region_id, exchange_id, symbol, currency,
                is_primary, effective_from, source_id, resolution_state
            ) VALUES ('listing-1', 'stock', 'US', 'NASDAQ', 'AAA', 'USD', 1,
                      '2020-01-01', 'source', 'verified')
            """
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO stock_listings (
                    listing_id, instrument_id, region_id, exchange_id, symbol, currency,
                    is_primary, effective_from, source_id, resolution_state
                ) VALUES ('listing-2', 'stock', 'US', 'NYSE', 'AAA.B', 'USD', 1,
                          '2020-01-01', 'source', 'verified')
                """
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE regions SET coverage_state = 'unknown' WHERE region_id = 'US'
                """
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO stock_listings (
                    listing_id, instrument_id, region_id, exchange_id, symbol, currency,
                    is_primary, effective_from, source_id, resolution_state
                ) VALUES ('listing-3', 'missing-stock', 'US', 'NYSE', 'BBB', 'USD', 0,
                          '2020-01-01', 'source', 'verified')
                """
            )


def test_get_industry_members_respects_effective_dates_and_placeholders(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    source = _write_csv(
        tmp_path / "members.csv",
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n"
        "instrument-b,,,NASDAQ,Technology,Cloud,2020-01-01\n",
    )
    source.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom,ResolutionState\n"
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01,identified\n"
        "instrument-b,,Placeholder,NASDAQ,Technology,Cloud,2020-01-01,placeholder\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="source-a",
        exchange_id=None,
        coverage="controlled listings",
        approval_reference="review-1",
    )

    members = database.get_industry_members("US", "TEST", "test-cloud", as_of=date(2026, 10, 30))

    assert [member.instrument_id for member in members] == ["instrument-a", "instrument-b"]
    assert members[1].resolution_state == "placeholder"
    assert members[1].listings == ()
    assert database.get_industry_members("US", "TEST", "test-cloud", as_of=date(2019, 12, 31)) == ()
    assert members[1].classification_state == "classified"


def test_entity_representations_are_region_and_date_scoped(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    source = _write_csv(
        tmp_path / "members.csv",
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
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
    with database.connect() as connection:
        listing_id = connection.execute(
            "SELECT listing_id FROM stock_listings WHERE symbol = 'AAA'"
        ).fetchone()["listing_id"]
        connection.execute(
            """
            INSERT INTO entity_representations (
                representation_id, region_id, classification_id, entity_type,
                entity_id, listing_id, effective_from, source_id
            ) VALUES ('rep-a', 'US', 'TEST', 'industry', 'test-cloud', ?,
                      '2020-01-01', 'source-a')
            """,
            (listing_id,),
        )

    representations = database.get_entity_representations(
        "US", "TEST", "industry", as_of=date(2026, 10, 30)
    )

    assert [(item.entity_id, item.symbol) for item in representations] == [("test-cloud", "AAA")]
    assert (
        database.get_entity_representations("EU", "TEST", "industry", as_of=date(2026, 10, 30))
        == ()
    )


def test_overlapping_same_industry_memberships_return_one_security(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    for source_id, ticker, start in (
        ("first", "AAA", "2020-01-01"),
        ("second", "AAA.B", "2021-01-01"),
    ):
        source = _write_csv(
            tmp_path / f"{source_id}.csv",
            f"stock-a,{ticker},Alpha,NASDAQ,Technology,Cloud,{start}\n",
        )
        import_reviewed_file(
            database, source, region_id="US", classification_id="TEST",
            source_id=source_id, exchange_id=None, coverage="test",
            approval_reference="review",
        )
    members = database.get_industry_members(
        "US", "TEST", "test-cloud", as_of=date(2026, 10, 30)
    )
    assert len(members) == 1
    assert len(members[0].listings) == 2
    historical = database.get_industry_members(
        "US", "TEST", "test-cloud", as_of=date(2020, 6, 1)
    )
    assert len(historical) == 1
    assert len(historical[0].listings) == 1


def test_classification_selection_uses_requested_effective_date(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    source = _write_csv(
        tmp_path / "source.csv", "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n"
    )
    import_reviewed_file(
        database, source, region_id="US", classification_id="CURRENT",
        source_id="source", exchange_id=None, coverage="test", approval_reference="review",
    )
    with database.connect() as connection:
        connection.execute(
            "UPDATE classifications SET effective_from='2020-01-01', "
            "effective_to='2029-12-31' WHERE classification_id='CURRENT'"
        )
        connection.execute(
            "INSERT INTO classifications "
            "(classification_id,region_id,name,source_id,effective_from) "
            "VALUES ('FUTURE','US','Future','source','2030-01-01')"
        )
    assert database.get_classification_id("US", as_of=date(2019, 1, 1)) is None
    assert database.get_classification_id("US", as_of=date(2026, 10, 30)) == "CURRENT"
    assert database.get_classification_id("US", as_of=date(2030, 1, 1)) == "FUTURE"
