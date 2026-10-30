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
