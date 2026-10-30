from datetime import date
from pathlib import Path

import pytest

from market_leadership.application.discover_sectors import load_entity_representations
from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.stock_membership import load_region_membership
from market_leadership.infrastructure.universe_import import import_reviewed_file


def _import_sample(database: RegionDatabase, tmp_path: Path) -> None:
    source = tmp_path / "members.csv"
    source.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="reviewed-sample",
        exchange_id=None,
        coverage="controlled sample",
        approval_reference="review-1",
    )


def test_region_membership_distinguishes_database_and_empty_states(tmp_path: Path) -> None:
    missing = RegionDatabase(tmp_path / "missing.sqlite")
    assert (
        load_region_membership(
            missing,
            region_id="US",
            classification_id="TEST",
            industry_id="test-cloud",
            as_of=date(2026, 10, 30),
        ).state
        == "missing_database"
    )

    invalid_path = tmp_path / "invalid.sqlite"
    invalid_path.write_text("not a database", encoding="utf-8")
    invalid = RegionDatabase(invalid_path)
    assert (
        load_region_membership(
            invalid,
            region_id="US",
            classification_id="TEST",
            industry_id="test-cloud",
            as_of=date(2026, 10, 30),
        ).state
        == "invalid_database"
    )

    empty = RegionDatabase(tmp_path / "empty.sqlite")
    empty.initialize()
    assert (
        load_region_membership(
            empty,
            region_id="US",
            classification_id="TEST",
            industry_id="test-cloud",
            as_of=date(2026, 10, 30),
        ).state
        == "empty_membership"
    )


def test_region_membership_and_entity_representations_are_database_scoped(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    database.initialize()
    _import_sample(database, tmp_path)

    result = load_region_membership(
        database,
        region_id="US",
        classification_id="TEST",
        industry_id="test-cloud",
        as_of=date(2026, 10, 30),
    )
    assert result.state == "available"
    assert result.coverage_state == "unverified"
    assert tuple(member.instrument_id for member in result.members) == ("instrument-a",)

    representation_id = database.add_entity_representation(
        region_id="US",
        classification_id="TEST",
        entity_type="industry",
        entity_id="test-cloud",
        exchange_id="NASDAQ",
        symbol="AAA",
        source_id="reviewed-sample",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
    )
    assert (
        database.add_entity_representation(
            region_id="US",
            classification_id="TEST",
            entity_type="industry",
            entity_id="test-cloud",
            exchange_id="NASDAQ",
            symbol="AAA",
            source_id="reviewed-sample",
            approval_reference="review-1",
            effective_from=date(2020, 1, 1),
        )
        == representation_id
    )
    with pytest.raises(ValueError, match="approval reference"):
        database.add_entity_representation(
            region_id="US",
            classification_id="TEST",
            entity_type="industry",
            entity_id="test-cloud",
            exchange_id="NASDAQ",
            symbol="AAA",
            source_id="reviewed-sample",
            approval_reference="wrong-review",
            effective_from=date(2020, 1, 1),
        )

    representations = load_entity_representations(
        database,
        region_id="US",
        classification_id="TEST",
        entity_type="industry",
        entity_ids=("test-cloud",),
        as_of=date(2026, 10, 30),
    )
    assert tuple(item.symbol for item in representations) == ("AAA",)


def test_all_reviewed_sector_mappings_are_dated_and_do_not_create_membership(
    tmp_path: Path,
) -> None:
    mappings = (
        ("Communication Services", "XLC"), ("Consumer Discretionary", "XLY"),
        ("Consumer Staples", "XLP"), ("Energy", "XLE"), ("Financials", "XLF"),
        ("Health Care", "XLV"), ("Industrials", "XLI"), ("Information Technology", "XLK"),
        ("Materials", "XLB"), ("Real Estate", "XLRE"), ("Utilities", "XLU"),
    )
    database = RegionDatabase(tmp_path / "universe.sqlite")
    members_file = tmp_path / "members.csv"
    members_file.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom\n"
        + "".join(
            f"stock-{index},S{index},Stock {index},NYSE,{name},Industry {index},2020-01-01\n"
            for index, (name, _) in enumerate(mappings)
        )
    )
    import_reviewed_file(
        database, members_file, region_id="US", classification_id="TEST",
        source_id="members", exchange_id=None, coverage="reviewed stock sample",
        approval_reference="test-only",
    )
    as_of = date(2026, 10, 30)
    sectors = database.get_sectors("US", "TEST", as_of=as_of)
    assert tuple(sector.name for sector in sectors) == tuple(name for name, _ in mappings)
    with database.connect() as connection:
        before = tuple(tuple(row) for row in connection.execute(
            "SELECT * FROM stock_memberships ORDER BY instrument_id"
        ))
    etfs = tmp_path / "charts.csv"
    etfs.write_text(
        "Ticker,Name,Exchange,Sector,Industry,EffectiveFrom\n"
        + "".join(f"{symbol},{symbol},NYSEARCA,,,2020-01-01\n" for _, symbol in mappings)
    )
    import_reviewed_file(
        database, etfs, region_id="US", classification_id="TEST", source_id="charts",
        exchange_id=None, coverage="chart ETFs only", approval_reference="test-only",
    )
    assert database.get_entity_representations("US", "TEST", "sector", as_of=as_of) == ()
    for sector, (_, symbol) in zip(sectors, mappings, strict=True):
        database.add_entity_representation(
            region_id="US", classification_id="TEST", entity_type="sector",
            entity_id=sector.sector_id, exchange_id="NYSEARCA", symbol=symbol,
            source_id="charts", approval_reference="test-only", effective_from=as_of,
            effective_to=date(2027, 10, 30),
        )
    active = load_entity_representations(
        database, region_id="US", classification_id="TEST", entity_type="sector",
        entity_ids=tuple(sector.sector_id for sector in sectors), as_of=as_of,
    )
    actual = {item.entity_id: item.symbol for item in active}
    assert tuple(actual[sector.sector_id] for sector in sectors) == tuple(
        symbol for _, symbol in mappings
    )
    for outside in (date(2026, 10, 29), date(2027, 10, 31)):
        assert database.get_entity_representations("US", "TEST", "sector", as_of=outside) == ()
    assert database.get_entity_representations("US", "TEST", "industry", as_of=as_of) == ()
    with database.connect() as connection:
        after = tuple(tuple(row) for row in connection.execute(
            "SELECT * FROM stock_memberships ORDER BY instrument_id"
        ))
    assert after == before
    membership = load_region_membership(
        database, region_id="US", classification_id="TEST",
        industry_id="test-industry-0", as_of=as_of,
    )
    assert membership.coverage_state == "partial"
    region = database.get_region("US")
    assert region is not None
    assert "reviewed stock sample" in region.coverage_description
    assert "chart ETFs only" in region.coverage_description


def test_membership_is_unique_and_uses_effective_classification(tmp_path: Path) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    _import_sample(database, tmp_path)
    second = tmp_path / "second.csv"
    second.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom\n"
        "instrument-a,AAA.B,Alpha,NASDAQ,Technology,Cloud,2021-01-01\n"
    )
    import_reviewed_file(
        database, second, region_id="US", classification_id="TEST", source_id="second",
        exchange_id=None, coverage="second listing", approval_reference="review-2",
    )
    with database.connect() as connection:
        connection.execute(
            "UPDATE classifications SET effective_to='2029-12-31' WHERE classification_id='TEST'"
        )
        connection.execute(
            "INSERT INTO classifications (classification_id,region_id,name,source_id,"
            "effective_from) VALUES ('FUTURE','US','Future','second','2030-01-01')"
        )
    current = load_region_membership(
        database, region_id="US", classification_id="TEST", industry_id="test-cloud",
        as_of=date(2026, 10, 30),
    )
    assert current.state == "available"
    assert tuple(member.instrument_id for member in current.members) == ("instrument-a",)
    assert len(current.members[0].listings) == 2
    historical = load_region_membership(
        database, region_id="US", classification_id="TEST", industry_id="test-cloud",
        as_of=date(2020, 10, 30),
    )
    assert len(historical.members) == 1
    assert len(historical.members[0].listings) == 1
    expired = load_region_membership(
        database, region_id="US", classification_id="TEST", industry_id="test-cloud",
        as_of=date(2030, 1, 1),
    )
    assert expired.state == "empty_membership"
