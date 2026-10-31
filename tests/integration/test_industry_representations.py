from datetime import date
from decimal import Decimal

import pytest

from market_leadership.application.industry_representations import representation_worklist

DAY = date(2026, 10, 30)


def _basket(database, *, start=date(2020, 1, 1), end=None, approval="review-1"):
    with database.connect() as connection:
        listings = [
            row["listing_id"]
            for row in connection.execute(
                "SELECT listing_id FROM stock_listings "
                "WHERE symbol IN ('AAA', 'BBB') ORDER BY symbol"
            )
        ]
    return database.add_stock_basket(
        region_id="US",
        classification_id="TEST",
        entity_id="test-cloud",
        name="Cloud alternative",
        source_id="reviewed",
        approval_reference=approval,
        effective_from=start,
        effective_to=end,
        constituents=((listings[0], Decimal("60")), (listings[1], Decimal("40"))),
    )


def _etf(database, *, start=date(2020, 1, 1), end=None):
    return database.add_entity_representation(
        region_id="US",
        classification_id="TEST",
        entity_type="industry",
        entity_id="test-cloud",
        exchange_id="NASDAQ",
        symbol="AAA",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=start,
        effective_to=end,
    )


def _worklist(database, **kwargs):
    return representation_worklist(
        database,
        region_id="US",
        classification_id="TEST",
        as_of=DAY,
        **kwargs,
    )


def test_worklist_covers_every_industry_and_subindustry_including_empty_nodes(
    representation_database,
):
    database = representation_database
    database.add_review_node(
        region_id="US",
        classification_id="TEST",
        entity_id="test-specialist",
        name="Specialist",
        sector_id="test-technology",
        parent_industry_id="test-cloud",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
    )
    assert [(item.node_id, item.status) for item in _worklist(database)] == [
        ("test-cloud", "not_covered"),
        ("test-hardware", "not_covered"),
        ("test-specialist", "not_covered"),
    ]
    _etf(database)
    assert {item.node_id for item in _worklist(database, only_uncovered=True)} == {
        "test-hardware",
        "test-specialist",
    }
    assert _worklist(database)[0].representation.symbols == ("AAA",)
    assert _worklist(database)[2].node_type == "sub_industry"


def test_basket_is_effective_fallback_and_etf_supersedes_without_parent_substitution(
    representation_database,
):
    database = representation_database
    _basket(database, end=date(2026, 10, 31))
    assert _worklist(database)[0].status == "basket"
    _etf(database, start=DAY)
    assert _worklist(database)[0].status == "etf"
    assert _worklist(database)[1].status == "not_covered"
    before = representation_worklist(
        database,
        region_id="US",
        classification_id="TEST",
        as_of=date(2026, 10, 29),
    )
    assert before[0].status == "basket"


def test_basket_cannot_be_approved_overlapping_a_current_or_future_etf(representation_database):
    _etf(representation_database, start=date(2027, 1, 1))
    with pytest.raises(ValueError, match="ETF"):
        _basket(representation_database)
    _basket(representation_database, end=date(2026, 12, 31))


def test_basket_rejects_duplicate_wrong_region_and_unreviewed_evidence(representation_database):
    database = representation_database
    with pytest.raises(ValueError, match="reviewed"):
        _basket(database, approval="not-reviewed")
    with database.connect() as connection:
        listing = connection.execute(
            "SELECT listing_id FROM stock_listings WHERE symbol = 'AAA'"
        ).fetchone()["listing_id"]
    with pytest.raises(ValueError, match="distinct"):
        database.add_stock_basket(
            region_id="US",
            classification_id="TEST",
            entity_id="test-cloud",
            name="Duplicate",
            source_id="reviewed",
            approval_reference="review-1",
            effective_from=date(2020, 1, 1),
            constituents=((listing, Decimal("50")), (listing, Decimal("50"))),
        )
    with pytest.raises(ValueError):
        database.add_stock_basket(
            region_id="CA",
            classification_id="TEST",
            entity_id="test-cloud",
            name="Wrong region",
            source_id="reviewed",
            approval_reference="review-1",
            effective_from=date(2020, 1, 1),
            constituents=((listing, Decimal("100")),),
        )


def test_expired_and_unreviewed_baskets_do_not_cover_nodes(representation_database):
    database = representation_database
    _basket(database, end=date(2025, 1, 1))
    assert _worklist(database)[0].status == "not_covered"
    with database.connect() as connection:
        connection.execute(
            "UPDATE stock_baskets SET effective_to = NULL, review_state = 'unreviewed'"
        )
    assert _worklist(database)[0].status == "not_covered"


def test_changed_source_approval_invalidates_etf_without_substitution(representation_database):
    database = representation_database
    _etf(database)
    with database.connect() as connection:
        connection.execute("UPDATE data_sources SET approval_reference = 'changed'")
    assert _worklist(database)[0].status == "invalid"
    assert database.get_entity_representations("US", "TEST", "industry", as_of=DAY) == ()


def test_future_valid_listing_inside_basket_period_blocks_basket_approval(representation_database):
    database = representation_database
    database.add_entity_representation(
        region_id="US",
        classification_id="TEST",
        entity_type="industry",
        entity_id="test-cloud",
        exchange_id="NYSE",
        symbol="CCC",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
    )
    with database.connect() as connection:
        connection.execute(
            "UPDATE stock_listings SET effective_from = '2027-01-01' WHERE symbol = 'CCC'"
        )
    with pytest.raises(ValueError, match="ETF"):
        _basket(database)
