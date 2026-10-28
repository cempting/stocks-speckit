import copy
from datetime import date

import pytest

from market_leadership.infrastructure.fixture_provider import FixtureProvider


@pytest.mark.parametrize(
    ("market_id", "benchmark", "currency", "scheme"),
    [
        ("US", "SPX", "USD", "GICS-US"),
        ("JP", "N225", "JPY", "GICS-JP"),
        ("GB", "UKX", "GBP", "GICS-GB"),
    ],
)
def test_weekly_fixture_has_dated_local_classifications_and_representations(
    market_id: str, benchmark: str, currency: str, scheme: str
) -> None:
    inputs = FixtureProvider().weekly_inputs(market_id, as_of=date(2026, 10, 28))

    assert inputs.market.local_benchmark_id == benchmark
    assert inputs.market.base_currency == currency
    assert inputs.as_of == date(2026, 10, 23)
    sectors = [node for node in inputs.classifications if node.level == "SECTOR"]
    industries = [node for node in inputs.classifications if node.level == "INDUSTRY"]
    assert len(sectors) >= 2 and industries
    by_id = {node.node_id: node for node in inputs.classifications}
    for industry in industries:
        assert industry.scheme_id == scheme
        assert industry.parent_node_id in by_id
        assert by_id[industry.parent_node_id].level == "SECTOR"
    assert len(inputs.representations) == len(inputs.classifications)
    for proxy in inputs.representations:
        assert proxy.market_id == market_id
        assert proxy.node_id in by_id
        assert proxy.effective_from <= inputs.as_of
        assert proxy.source_id and proxy.composition_basis
        assert proxy.proxy_type in ("FUND", "INDEX", "EQUAL_WEIGHT_BASKET")
        assert proxy.qualified
        assert proxy.instrument_id in inputs.histories
    assert benchmark in inputs.histories
    assert all(
        series.currency == currency and series.return_basis == "adjusted"
        for series in inputs.histories.values()
    )


def test_weekly_fixture_rejects_unknown_market_and_uses_previous_completed_week() -> None:
    provider = FixtureProvider()
    with pytest.raises(ValueError, match="market"):
        provider.weekly_inputs("XX", as_of=date(2026, 10, 28))
    assert provider.weekly_inputs("US", as_of=date(2026, 10, 23)).as_of == date(2026, 10, 16)


def test_local_holiday_weeks_keep_each_markets_own_completion_date() -> None:
    provider = FixtureProvider()

    assert provider.weekly_inputs("US", as_of=date(2026, 4, 3)).as_of == date(2026, 4, 2)
    assert provider.weekly_inputs("JP", as_of=date(2026, 4, 3)).as_of == date(2026, 3, 27)
    assert provider.weekly_inputs("GB", as_of=date(2026, 4, 3)).as_of == date(2026, 4, 2)


def test_weekly_inputs_are_not_advertised_as_live_price_provider_capability() -> None:
    from market_leadership.infrastructure.yfinance_provider import YFinanceProvider

    assert {capability.data_point for capability in YFinanceProvider.capabilities()} == {
        "daily_history"
    }


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("source_id", "", "source"),
        ("composition_basis", "", "composition"),
    ],
)
def test_weekly_fixture_rejects_unqualified_or_future_proxy(
    monkeypatch, field: str, value: str, expected: str
) -> None:
    from market_leadership.infrastructure.fixture_provider import load_acceptance_market_context

    fixture = copy.deepcopy(load_acceptance_market_context())
    fixture["weekly"]["representations"][0][field] = value
    monkeypatch.setattr(
        "market_leadership.infrastructure.fixture_provider.load_acceptance_market_context",
        lambda: fixture,
    )

    with pytest.raises(ValueError, match=expected):
        FixtureProvider().weekly_inputs("US", as_of=date(2026, 10, 28))


def test_future_dated_representation_is_not_applied_retrospectively(monkeypatch) -> None:
    from market_leadership.infrastructure.fixture_provider import load_acceptance_market_context

    fixture = copy.deepcopy(load_acceptance_market_context())
    fixture["weekly"]["representations"][0]["effective_from"] = "2026-10-24"
    monkeypatch.setattr(
        "market_leadership.infrastructure.fixture_provider.load_acceptance_market_context",
        lambda: fixture,
    )

    inputs = FixtureProvider().weekly_inputs("US", as_of=date(2026, 10, 28))
    assert "US-TECH" in {node.node_id for node in inputs.classifications}
    assert "US-TECH" not in {proxy.node_id for proxy in inputs.representations}


def test_weekly_fixture_rejects_dangling_industry_parent(monkeypatch) -> None:
    from market_leadership.infrastructure.fixture_provider import load_acceptance_market_context

    fixture = copy.deepcopy(load_acceptance_market_context())
    fixture["weekly"]["nodes"][2]["parent_node_id"] = "missing"
    monkeypatch.setattr(
        "market_leadership.infrastructure.fixture_provider.load_acceptance_market_context",
        lambda: fixture,
    )

    with pytest.raises(ValueError, match="parent"):
        FixtureProvider().weekly_inputs("US", as_of=date(2026, 10, 28))
