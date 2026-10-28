import json
from datetime import date
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import pytest

from market_leadership import bootstrap
from market_leadership.application.ports import DataPointRequest
from market_leadership.config import Settings
from market_leadership.domain.models import Market
from market_leadership.infrastructure.massive_provider import MassiveProvider
from market_leadership.infrastructure.provider_validation import canonicalize_fx_rates

_ACCEPTANCE = Path(__file__).resolve().parents[1] / "fixtures" / "acceptance" / "market_data.json"


@pytest.fixture(scope="module")
def market_data() -> dict:
    return json.loads(_ACCEPTANCE.read_text(encoding="utf-8"))


def _market(record: dict) -> Market:
    return Market(
        **{
            **record,
            "enabled_from": date.fromisoformat(record["enabled_from"]),
            "enabled_to": (
                date.fromisoformat(record["enabled_to"]) if record["enabled_to"] else None
            ),
        }
    )


def _request(market: Market, *, as_of: date) -> DataPointRequest:
    return DataPointRequest(
        data_point="daily_history",
        market_id=market.market_id,
        identifiers=(market.local_benchmark_id,),
        frequency="1d",
        start=as_of,
        end=as_of,
        currency=market.base_currency,
        return_basis="adjusted",
    )


def _catalog(tmp_path, *provider_ids: str):
    settings = Settings(
        default_provider=provider_ids[0],
        massive_available=False,
        market_data_cache_path=str(tmp_path),
        source_cache_path=str(tmp_path),
        provider_ids=provider_ids,
        provider_priorities=(),
        retry_limit=0,
    )
    return bootstrap.build_market_data_catalog(settings)


def test_fixture_market_definitions_have_distinct_effective_local_contexts(market_data) -> None:
    markets = [_market(record) for record in market_data["markets"]]
    assert {market.market_id for market in markets} == {"US", "JP", "GB"}
    assert {market.market_id: market.base_currency for market in markets} == {
        "US": "USD",
        "JP": "JPY",
        "GB": "GBP",
    }
    assert {market.market_id: market.calendar_id for market in markets} == {
        "US": "XNYS",
        "JP": "XTKS",
        "GB": "XLON",
    }
    assert {market.market_id: market.local_benchmark_id for market in markets} == {
        "US": "SPX",
        "JP": "N225",
        "GB": "UKX",
    }
    assert all(market.enabled_from == date(2025, 1, 1) for market in markets)
    assert all(market.enabled_to is None for market in markets)


@pytest.mark.parametrize(
    ("market_id", "expected_regime", "expected_close"),
    [
        ("US", "BULLISH", 6800.0),
        ("JP", "SIDEWAYS", 51000.0),
        ("GB", "BEARISH", 9400.0),
    ],
)
def test_fixture_benchmark_histories_use_dated_local_sessions_and_available_sources(
    market_data, market_id: str, expected_regime: str, expected_close: float
) -> None:
    market = _market(next(row for row in market_data["markets"] if row["market_id"] == market_id))
    history = next(
        row for row in market_data["benchmark_histories"] if row["market_id"] == market_id
    )
    benchmark = next(row for row in market_data["benchmarks"] if row["market_id"] == market_id)
    sessions = xcals.get_calendar(market.calendar_id).sessions_in_range(
        history["first_session"], history["last_session"]
    )
    closes = pd.Series(
        [
            history["first_close"] + i * history["close_change_per_session"]
            for i in range(len(sessions))
        ],
        index=sessions,
    )

    assert len(sessions) >= 169  # 150-session average and 20 latest averages.
    assert sessions[0].date() == date.fromisoformat(history["first_session"])
    assert sessions[-1].date() == date.fromisoformat(history["last_session"])
    assert history["benchmark_id"] == market.local_benchmark_id == benchmark["symbol"]
    assert history["currency"] == market.base_currency
    assert history["calendar_id"] == market.calendar_id
    assert history["return_basis"] == "adjusted"
    assert date.fromisoformat(history["effective_from"]) <= sessions[0].date()
    assert history["effective_to"] is None
    assert history["source_id"] == "fixture"
    assert (
        sessions[-1].date()
        <= date.fromisoformat(history["available_on"])
        <= date.fromisoformat(market_data["as_of"])
    )
    assert closes.iloc[-1] == expected_close == benchmark["close"]
    average = closes.tail(150).mean()
    if expected_regime == "BULLISH":
        assert closes.iloc[-1] > average
    elif expected_regime == "BEARISH":
        assert closes.iloc[-1] < average
    else:
        assert closes.iloc[-1] == average
    assert benchmark["regime"] == expected_regime


@pytest.mark.parametrize("market_id", ["US", "JP", "GB"])
def test_fixture_catalog_exposes_only_effective_local_benchmark_history(
    market_data, tmp_path, market_id: str
) -> None:
    market = _market(next(row for row in market_data["markets"] if row["market_id"] == market_id))
    catalog = _catalog(tmp_path, "fixture")

    active = catalog.discover(_request(market, as_of=date.fromisoformat(market_data["as_of"])))
    assert [candidate.provider_id for candidate in active] == ["fixture"]
    assert catalog.discover(_request(market, as_of=date(2024, 12, 31))) == ()


@pytest.mark.parametrize("market_id", ["JP", "GB"])
def test_fixture_markets_do_not_grant_live_provider_coverage(
    market_data, tmp_path, monkeypatch, market_id: str
) -> None:
    market = _market(next(row for row in market_data["markets"] if row["market_id"] == market_id))
    original_adapter = bootstrap._build_provider_adapter
    monkeypatch.setattr(
        bootstrap,
        "_build_provider_adapter",
        lambda provider_id, retry_limit: (
            MassiveProvider(client=object(), retry_limit=retry_limit)
            if provider_id == "massive"
            else original_adapter(provider_id, retry_limit)
        ),
    )
    catalog = _catalog(tmp_path, "yfinance", "massive")

    assert catalog.discover(_request(market, as_of=date.fromisoformat(market_data["as_of"]))) == ()


def test_optional_fx_requires_same_close_and_availability_without_hiding_local_history(
    market_data, tmp_path
) -> None:
    jp = _market(next(row for row in market_data["markets"] if row["market_id"] == "JP"))
    as_of = date.fromisoformat(market_data["as_of"])
    fx = pd.DataFrame(
        row for row in market_data["fx_rates"] if row["base_currency"] == jp.base_currency
    )
    rates = canonicalize_fx_rates(
        fx[["date", "close", "available_on"]],
        base_currency=jp.base_currency,
        quote_currency="USD",
        as_of=as_of,
        source_id=fx["source_id"].iloc[0],
    )

    assert rates["date"].dt.date.tolist() == [date(2026, 10, 22)]
    assert rates["source_id"].tolist() == ["fixture-fx"]
    assert rates.loc[rates["date"].dt.date == as_of].empty
    assert [
        candidate.provider_id
        for candidate in _catalog(tmp_path, "fixture").discover(_request(jp, as_of=as_of))
    ] == ["fixture"]


def test_late_fx_cannot_supply_global_comparison_on_observation_date(market_data) -> None:
    gb_fx = pd.DataFrame(row for row in market_data["fx_rates"] if row["base_currency"] == "GBP")
    available = canonicalize_fx_rates(
        gb_fx[["date", "close", "available_on"]],
        base_currency="GBP",
        quote_currency="USD",
        as_of=date.fromisoformat(market_data["as_of"]),
        source_id=gb_fx["source_id"].iloc[0],
    )

    assert available.empty
    gb_benchmark = next(row for row in market_data["benchmarks"] if row["market_id"] == "GB")
    assert (gb_benchmark["symbol"], gb_benchmark["close"]) == ("UKX", 9400.0)
