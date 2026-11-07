from dataclasses import replace
from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from market_data.domain.industry_representations import (
    BasketConstituent,
    ReviewedRepresentation,
    representation_performance,
)
from market_data_tools.legacy.region_database import RegionDatabase

DAY = date(2026, 10, 30)


def _daily_representation(kind="basket"):
    return ReviewedRepresentation(
        representation_id="daily", node_id="test-cloud", kind=kind, name="Daily evidence",
        source_id="fixture", approval_reference="review-1", effective_from=date(2020, 1, 1),
        symbol="BBB" if kind == "etf" else None,
        constituents=() if kind == "etf" else (
            BasketConstituent("a", "AAA", Decimal("50")),
            BasketConstituent("b", "BBB", Decimal("50")),
        ),
    )


def _daily_history():
    index = pd.bdate_range("2026-10-29", periods=2)
    return {
        "AAA": pd.DataFrame({"close": [100.0, 102.0]}, index=index),
        "BBB": pd.DataFrame({"close": [200.0, 198.0]}, index=index),
    }


@pytest.mark.parametrize(("kind", "expected"), [("etf", -0.01), ("basket", 0.005)])
def test_representation_performance_returns_six_independent_periods(kind, expected):
    result = representation_performance(
        _daily_representation(kind), _daily_history(), as_of=DAY,
        start_session=date(2026, 10, 29), end_session=DAY,
    )
    assert list(result) == ["1d", "1w", "1m", "3m", "6m", "12m"]
    assert result["1d"].value == pytest.approx(expected)
    assert result["1d"].reason is None
    for period in ("1w", "1m", "3m", "6m", "12m"):
        assert result[period].value is None
        assert result[period].reason


def test_representation_performance_daily_gap_preserves_longer_values():
    index = pd.bdate_range(end=DAY, periods=300)
    history = {"BBB": pd.DataFrame({"close": 100.0}, index=index)}
    history["BBB"] = history["BBB"].drop(pd.Timestamp("2026-10-29"))
    result = representation_performance(
        _daily_representation("etf"), history, as_of=DAY,
        start_session=date(2026, 10, 29), end_session=DAY,
    )
    assert result["1d"].value is None
    assert result["1d"].reason is not None
    assert "2026-10-29" in result["1d"].reason
    for period in ("1w", "1m", "3m", "6m", "12m"):
        assert result[period].value == 0
        assert result[period].reason is None


def test_representation_performance_longer_periods_are_independently_available():
    index = pd.bdate_range(end=DAY, periods=30)
    history = {"BBB": pd.DataFrame({"close": 100.0}, index=index)}
    result = representation_performance(
        _daily_representation("etf"), history, as_of=DAY,
        start_session=date(2026, 10, 29), end_session=DAY,
    )
    for period in ("1d", "1w", "1m"):
        assert result[period].value == 0
        assert result[period].reason is None
    for period in ("3m", "6m", "12m"):
        assert result[period].value is None
        assert result[period].reason


def test_representation_prepares_calendar_history_once_per_constituent(monkeypatch):
    from market_data.domain import sector_performance

    prepares = []
    original = sector_performance._prepare_closes

    def prepare(*args):
        prepares.append(True)
        return original(*args)

    monkeypatch.setattr(sector_performance, "_prepare_closes", prepare)
    index = pd.bdate_range(end=DAY, periods=400)
    results = representation_performance(
        _daily_representation(),
        {symbol: pd.DataFrame({"close": 100.0}, index=index) for symbol in ("AAA", "BBB")},
        as_of=DAY, start_session=date(2026, 10, 29), end_session=DAY,
    )
    assert all(result.value == 0 for result in results.values())
    assert len(prepares) == 2


@pytest.mark.parametrize(("kind", "expected"), [("etf", -0.01), ("basket", 0.005)])
def test_daily_representation_preserves_approved_etf_and_exact_basket_weights(kind, expected):
    representation = _daily_representation(kind)
    result = representation_performance(
        representation, _daily_history(), as_of=DAY,
        start_session=date(2026, 10, 29), end_session=DAY,
    )
    assert result["1d"].value == pytest.approx(expected)
    assert result["1d"].reason is None
    assert representation.source_id == "fixture"
    assert representation.approval_reference == "review-1"


@pytest.mark.parametrize("symbol", ["AAA", "BBB"])
@pytest.mark.parametrize("session", ["2026-10-29", "2026-10-30"])
def test_daily_basket_does_not_drop_missing_constituents_or_shift_sessions(symbol, session):
    history = _daily_history()
    history[symbol] = history[symbol].drop(pd.Timestamp(session))
    result = representation_performance(
        _daily_representation(), history, as_of=DAY,
        start_session=date(2026, 10, 29), end_session=DAY,
    )
    assert result["1d"].value is None
    assert result["1d"].reason is not None
    assert symbol in result["1d"].reason


@pytest.mark.parametrize("change", [
    {"approval_reference": ""},
    {"effective_from": date(2027, 1, 1)},
    {"effective_to": date(2026, 10, 29)},
    {"reason": "Unapproved representation"},
    {"constituents": (
        BasketConstituent("a", "AAA", Decimal("60")),
        BasketConstituent("b", "BBB", Decimal("39")),
    )},
])
def test_daily_representation_requires_current_approved_evidence(change):
    with pytest.raises(ValueError):
        representation_performance(
            replace(_daily_representation(), **change), _daily_history(), as_of=DAY,
            start_session=date(2026, 10, 29), end_session=DAY,
        )


def approve_basket(database: RegionDatabase, weights: tuple[str, str] = ("60", "40")) -> str:
    with database.connect() as connection:
        listings = {
            row["symbol"]: row["listing_id"]
            for row in connection.execute("SELECT symbol, listing_id FROM stock_listings")
        }
    return database.add_stock_basket(
        region_id="US",
        classification_id="TEST",
        entity_id="test-cloud",
        name="Reviewed cloud basket",
        source_id="reviewed",
        approval_reference="review-1",
        effective_from=date(2020, 1, 1),
        constituents=tuple(
            (listings[symbol], Decimal(weight))
            for symbol, weight in zip(("AAA", "BBB"), weights, strict=True)
        ),
    )


def test_approved_basket_retains_exact_weights_and_evidence(representation_database):
    identifier = approve_basket(representation_database, ("33.333333333", "66.666666667"))
    (basket,) = representation_database.get_stock_baskets("US", "TEST", as_of=DAY)
    assert basket.representation_id == identifier
    assert basket.source_id == "reviewed"
    assert basket.approval_reference == "review-1"
    assert basket.effective_from == date(2020, 1, 1)
    assert sum(item.weight for item in basket.constituents) == Decimal("100")
    assert tuple(item.symbol for item in basket.constituents) == ("AAA", "BBB")
    assert representation_database.get_stock_baskets("US", "TEST", as_of=date(2019, 1, 1)) == ()
    revision = representation_database.get_revision()
    assert approve_basket(representation_database, ("33.333333333", "66.666666667")) == identifier
    assert representation_database.get_revision() == revision


@pytest.mark.parametrize(
    "weights", [("60", "39"), ("0", "100"), ("-1", "101"), ("NaN", "40"), ("Infinity", "40")]
)
def test_basket_rejects_invalid_weights_atomically(representation_database, weights):
    revision = representation_database.get_revision()
    with pytest.raises(ValueError, match="weight"):
        approve_basket(representation_database, weights)
    assert representation_database.get_stock_baskets("US", "TEST", as_of=DAY) == ()
    assert representation_database.get_revision() == revision


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE stock_listings SET resolution_state = 'unverified' WHERE symbol = 'BBB'",
        "UPDATE stock_listings SET effective_to = '2025-01-01' WHERE symbol = 'BBB'",
        "UPDATE data_sources SET approval_reference = NULL WHERE source_id = 'reviewed'",
        "UPDATE data_sources SET reviewed_at = NULL WHERE source_id = 'reviewed'",
        "UPDATE industries SET effective_to = '2025-01-01' WHERE industry_id = 'test-cloud'",
    ],
)
def test_basket_approval_requires_valid_evidence_for_entire_period(representation_database, sql):
    with representation_database.connect() as connection:
        connection.execute(sql)
    with pytest.raises(ValueError):
        approve_basket(representation_database)


def test_invalidated_basket_is_explicit_and_has_no_request_symbols(representation_database):
    from market_data_tools.legacy.industry_representations import representation_worklist

    approve_basket(representation_database)
    with representation_database.connect() as connection:
        connection.execute(
            "UPDATE stock_listings SET resolution_state = 'unverified' WHERE symbol = 'BBB'"
        )
    item = next(
        item
        for item in representation_worklist(
            representation_database, region_id="US", classification_id="TEST", as_of=DAY
        )
        if item.node_id == "test-cloud"
    )
    assert item.status == "invalid"
    assert item.representation is not None
    assert item.representation.symbols == ()
    assert item.representation.reason


def test_schema_upgrade_preserves_existing_reviewed_etf(representation_database):
    database = representation_database
    identifier = database.add_entity_representation(
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
    with database.connect() as connection:
        connection.execute("ALTER TABLE entity_representations DROP COLUMN approval_reference")
        for column in ("node_type", "parent_industry_id", "source_id", "approval_reference"):
            connection.execute(f"ALTER TABLE industries DROP COLUMN {column}")
        connection.execute("UPDATE database_metadata SET value = '1' WHERE key = 'schema_version'")
    database.initialize()
    assert database.is_initialized()
    assert (
        database.get_entity_representations("US", "TEST", "industry", as_of=DAY)[
            0
        ].representation_id
        == identifier
    )
    (etf,) = database.get_reviewed_industry_etfs("US", "TEST", as_of=DAY)
    assert etf.approval_reference == "review-1"


def test_decimal_weight_total_is_exact_beyond_decimal_context_precision(representation_database):
    with pytest.raises(ValueError, match="exactly 100"):
        approve_basket(
            representation_database,
            ("50.000000000000000000000000000001", "50"),
        )


def test_corrupted_weight_total_stays_invalid_without_request_symbols(representation_database):
    approve_basket(representation_database)
    with representation_database.connect() as connection:
        connection.execute("UPDATE basket_constituents SET weight = '1'")
    (basket,) = representation_database.get_stock_baskets("US", "TEST", as_of=DAY)
    assert basket.invalid_reason == "Basket weights must total exactly 100%"
    assert basket.symbols == ()
