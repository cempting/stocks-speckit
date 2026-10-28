from dataclasses import FrozenInstanceError, fields
from datetime import date

import pytest

import market_leadership.domain
from market_leadership.domain.models import (
    AssetCategory,
    Benchmark,
    ClassificationLevel,
    ClassificationNode,
    Company,
    Instrument,
    InstrumentKind,
    Market,
    MarketRegime,
    ProxyType,
    SlopeState,
)


def test_domain_package_is_importable() -> None:
    assert market_leadership.domain is not None


def test_domain_enums_cover_equity_classification_and_regime_contracts() -> None:
    assert {level.value for level in ClassificationLevel} == {
        "SECTOR",
        "INDUSTRY_GROUP",
        "INDUSTRY",
        "SUB_INDUSTRY",
    }
    assert {kind.value for kind in InstrumentKind} == {"STOCK", "FUND", "INDEX"}
    assert {proxy.value for proxy in ProxyType} == {
        "FUND",
        "INDEX",
        "EQUAL_WEIGHT_BASKET",
        "NONE",
    }
    assert {state.value for state in SlopeState} == {"RISING", "FLAT", "FALLING", "UNDEFINED"}
    assert {regime.value for regime in MarketRegime} == {
        "BULLISH",
        "SIDEWAYS",
        "BEARISH",
        "INSUFFICIENT",
    }
    assert AssetCategory.EQUITY.value == "EQUITY"


def test_market_requires_local_benchmark_currency_and_calendar() -> None:
    benchmark = Benchmark("SPX", "SPX", "LOCAL", "US", "USD", "ADJUSTED_CLOSE")
    market = Market(
        market_id="US",
        name="United States",
        base_currency="USD",
        timezone="America/New_York",
        calendar_id="XNYS",
        local_benchmark_id=benchmark.benchmark_id,
        classification_scheme_id="GICS-US",
        enabled_from=date(2000, 1, 1),
    )

    assert market.base_currency == "USD"
    assert not hasattr(market, "__dict__")
    with pytest.raises(FrozenInstanceError):
        market.name = "Changed"


@pytest.mark.parametrize("currency", ["usd", "US", "USDT", "1SD"])
def test_market_rejects_non_iso_currency_codes(currency: str) -> None:
    with pytest.raises(ValueError, match="ISO 4217"):
        Market(
            market_id="X",
            name="Example",
            base_currency=currency,
            timezone="UTC",
            calendar_id="XEXM",
            local_benchmark_id="INDEX",
            classification_scheme_id="GICS-X",
            enabled_from=date(2020, 1, 1),
        )


def test_classification_node_preserves_effective_parent_identity() -> None:
    node = ClassificationNode(
        node_id="US-SECTOR-TECH",
        scheme_id="GICS-US",
        level=ClassificationLevel.SECTOR,
        name="Information Technology",
        parent_node_id=None,
        effective_from=date(2020, 1, 1),
    )

    assert node.parent_node_id is None
    assert not hasattr(node, "__dict__")
    with pytest.raises(FrozenInstanceError):
        node.name = "Other"


def test_company_and_instrument_are_distinct_records() -> None:
    company = Company("ACME", "Acme Corp", "US")
    instrument = Instrument(
        instrument_id="US-ACME-XNYS",
        company_id=company.company_id,
        asset_category=AssetCategory.EQUITY,
        kind=InstrumentKind.STOCK,
        symbol="ACME",
        exchange="XNYS",
        currency="USD",
        return_basis="ADJUSTED_CLOSE",
        name="Acme Corp",
        active_from=date(2020, 1, 1),
    )

    assert instrument.company_id == company.company_id
    assert not isinstance(instrument, Company)
    assert fields(Company) != fields(Instrument)
