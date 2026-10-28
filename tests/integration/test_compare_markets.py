"""US1 fixture overview contract; sector outcomes are 3m proxies, not US2 weekly ranks.

compare_markets(selected_market_ids, *, market_data, as_of, global_benchmark=None)
returns an object with ordered ``markets``. Each market carries its own local
benchmark, observation date, currency, calendar, return basis, freshness, regime,
and top/bottom three-month local-relative sector outcomes. ``global_context`` is
optional and separately labelled; it never replaces the local results.
"""

import copy
import json
from datetime import date
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "acceptance"


@pytest.fixture(scope="module")
def acceptance() -> tuple[dict, dict]:
    return tuple(
        json.loads((_FIXTURES / name).read_text(encoding="utf-8"))
        for name in ("market_data.json", "expected.json")
    )


def _compare(selected: tuple[str, ...], data: dict, **kwargs):
    # Import on invocation so a missing T033 module produces a red test, not a skip
    # or a collection error that hides the fixture-backed acceptance cases.
    from market_leadership.application.compare_markets import compare_markets

    return compare_markets(
        selected, market_data=data, as_of=date.fromisoformat(data["as_of"]), **kwargs
    )


@pytest.mark.parametrize("market_id", ["US", "JP", "GB"])
def test_single_market_preserves_local_context_and_three_month_proxy(
    acceptance: tuple[dict, dict], market_id: str
) -> None:
    data, expected = acceptance
    result = _compare((market_id,), data)
    assert [market.market_id for market in result.markets] == [market_id]

    overview = result.markets[0]
    market = next(row for row in data["markets"] if row["market_id"] == market_id)
    history = next(row for row in data["benchmark_histories"] if row["market_id"] == market_id)
    outcomes = [row for row in data["sector_outcomes"] if row["market_id"] == market_id]
    top = max(outcomes, key=lambda row: row["relative_3m"])
    bottom = min(outcomes, key=lambda row: row["relative_3m"])

    assert overview.benchmark_id == market["local_benchmark_id"] == history["benchmark_id"]
    assert overview.currency == market["base_currency"] == history["currency"]
    assert overview.calendar_id == market["calendar_id"] == history["calendar_id"]
    assert overview.as_of == date.fromisoformat(history["last_session"])
    assert overview.return_basis == history["return_basis"] == "adjusted"
    assert overview.freshness == "current"
    assert overview.regime == expected["market_regimes"][market_id]
    assert overview.top_sector.sector == expected["top_sector_by_local_relative_return"][market_id]
    assert (
        overview.bottom_sector.sector
        == expected["bottom_sector_by_local_relative_return"][market_id]
    )
    assert overview.top_sector.relative_3m == pytest.approx(top["relative_3m"])
    assert overview.bottom_sector.relative_3m == pytest.approx(bottom["relative_3m"])
    assert overview.top_sector.absolute_3m == pytest.approx(top["absolute_3m"])
    assert overview.bottom_sector.absolute_3m == pytest.approx(bottom["absolute_3m"])
    assert overview.sector_outcome_basis == "three_month_local_relative_proxy"
    assert overview.global_context is None


def test_multiple_markets_are_separate_and_selection_order_is_preserved(
    acceptance: tuple[dict, dict],
) -> None:
    data, expected = acceptance
    selected = ("GB", "US", "JP")
    result = _compare(selected, data)
    assert [market.market_id for market in result.markets] == list(selected)
    assert {market.currency for market in result.markets} == {"GBP", "USD", "JPY"}
    assert {market.benchmark_id for market in result.markets} == {"UKX", "SPX", "N225"}
    assert {market.regime for market in result.markets} == set(expected["market_regimes"].values())
    assert {
        market.market_id: (market.top_sector.sector, market.bottom_sector.sector)
        for market in result.markets
    } == {
        market_id: (
            expected["top_sector_by_local_relative_return"][market_id],
            expected["bottom_sector_by_local_relative_return"][market_id],
        )
        for market_id in selected
    }
    assert all(
        market.sector_outcome_basis == "three_month_local_relative_proxy"
        for market in result.markets
    )


def test_regime_comes_from_dated_history_not_fixture_regime_label(
    acceptance: tuple[dict, dict],
) -> None:
    data, expected = acceptance
    altered = copy.deepcopy(data)
    for benchmark in altered["benchmarks"]:
        benchmark["regime"] = "SIDEWAYS" if benchmark["market_id"] != "JP" else "BULLISH"

    result = _compare(("US", "JP", "GB"), altered)
    assert {market.market_id: market.regime for market in result.markets} == expected[
        "market_regimes"
    ]


def test_local_observation_dates_and_staleness_are_independent(
    acceptance: tuple[dict, dict],
) -> None:
    data, expected = acceptance
    altered = copy.deepcopy(data)
    jp = next(row for row in altered["benchmark_histories"] if row["market_id"] == "JP")
    jp["last_session"] = "2026-10-22"

    result = _compare(("JP", "US"), altered)
    jp_result, us_result = result.markets
    assert jp_result.as_of == date(2026, 10, 22)
    assert jp_result.freshness == "stale"
    assert us_result.as_of == date(2026, 10, 23)
    assert us_result.freshness == "current"
    assert us_result.regime == expected["market_regimes"]["US"]
    assert us_result.top_sector.sector == expected["top_sector_by_local_relative_return"]["US"]


def test_missing_local_history_does_not_hide_valid_other_market(
    acceptance: tuple[dict, dict],
) -> None:
    data, expected = acceptance
    altered = copy.deepcopy(data)
    altered["benchmark_histories"] = [
        row for row in altered["benchmark_histories"] if row["market_id"] != "JP"
    ]

    us, jp = _compare(("US", "JP"), altered).markets

    assert us.regime == expected["market_regimes"]["US"]
    assert us.top_sector.sector == expected["top_sector_by_local_relative_return"]["US"]
    assert jp.benchmark_id == "N225"
    assert jp.regime == "INSUFFICIENT"
    assert jp.freshness == "insufficient"
    assert jp.as_of is None
    assert jp.top_sector is None
    assert jp.sector_outcomes == ()


def test_local_and_optional_global_outcomes_can_disagree_without_changing_local(
    acceptance: tuple[dict, dict],
) -> None:
    data, expected = acceptance
    global_benchmark = {
        "benchmark_id": "ACWI",
        "currency": "USD",
        "return_basis": "adjusted",
        "as_of": data["as_of"],
        "return_3m": 0.20,
        "source_id": "fixture",
        "available_on": data["as_of"],
    }
    overview = _compare(("US",), data, global_benchmark=global_benchmark).markets[0]

    assert overview.benchmark_id == "SPX"
    assert overview.top_sector.sector == expected["top_sector_by_local_relative_return"]["US"]
    assert overview.top_sector.relative_3m > 0
    assert overview.global_context is not None
    assert overview.global_context.benchmark_id == "ACWI"
    assert overview.global_context.currency == "USD"
    assert overview.global_context.top_sector.relative_3m < 0
    assert overview.global_context.top_sector.sector == overview.top_sector.sector
    assert overview.sector_outcome_basis == "three_month_local_relative_proxy"


@pytest.mark.parametrize("market_id", ["JP", "GB"])
def test_missing_or_late_fx_only_blocks_optional_global_comparison(
    acceptance: tuple[dict, dict], market_id: str
) -> None:
    data, expected = acceptance
    fx = next(
        row
        for row in data["fx_rates"]
        if row["base_currency"] == ("JPY" if market_id == "JP" else "GBP")
    )
    assert fx["date"] != data["as_of"] or fx["available_on"] > data["as_of"]
    global_benchmark = {
        "benchmark_id": "ACWI",
        "currency": "USD",
        "return_basis": "adjusted",
        "as_of": data["as_of"],
        "return_3m": 0.20,
        "source_id": "fixture",
        "available_on": data["as_of"],
    }
    result = _compare(("US", market_id), data, global_benchmark=global_benchmark)
    us, local = result.markets

    assert us.global_context is not None
    assert local.global_context is None
    assert local.currency == ("JPY" if market_id == "JP" else "GBP")
    assert local.freshness == "current"
    assert local.regime == expected["market_regimes"][market_id]
    assert local.top_sector.sector == expected["top_sector_by_local_relative_return"][market_id]
    assert (
        local.bottom_sector.sector == expected["bottom_sector_by_local_relative_return"][market_id]
    )


@pytest.mark.parametrize("selected", [(), ("XX",)])
def test_empty_or_unsupported_market_selection_is_rejected(
    acceptance: tuple[dict, dict], selected: tuple[str, ...]
) -> None:
    data, _ = acceptance
    with pytest.raises(ValueError, match="market"):
        _compare(selected, data)
