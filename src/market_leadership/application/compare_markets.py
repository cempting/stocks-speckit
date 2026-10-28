"""Fixture-backed local market comparison before weekly rankings are available."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, cast

import exchange_calendars as xcals  # pyright: ignore[reportMissingTypeStubs]
import numpy as np
import pandas as pd

from market_leadership.domain.models import Market
from market_leadership.domain.regimes import calculate_market_sentiment


@dataclass(frozen=True, slots=True)
class SectorOutcome:
    sector: str
    absolute_3m: float
    relative_3m: float


@dataclass(frozen=True, slots=True)
class GlobalContext:
    benchmark_id: str
    currency: str
    top_sector: SectorOutcome


@dataclass(frozen=True, slots=True)
class MarketOverview:
    market_id: str
    name: str
    benchmark_id: str
    currency: str
    calendar_id: str
    as_of: date | None
    return_basis: str
    freshness: str
    regime: str
    top_sector: SectorOutcome | None
    bottom_sector: SectorOutcome | None
    sector_outcomes: tuple[SectorOutcome, ...]
    sector_outcome_basis: str
    source_id: str
    source_available_on: date | None
    coverage_start: date | None
    global_context: GlobalContext | None
    global_unavailable_reason: str | None


@dataclass(frozen=True, slots=True)
class MarketComparison:
    markets: tuple[MarketOverview, ...]


def _insufficient_market(market: Market, reason: str) -> MarketOverview:
    return MarketOverview(
        market_id=market.market_id,
        name=market.name,
        benchmark_id=market.local_benchmark_id,
        currency=market.base_currency,
        calendar_id=market.calendar_id,
        as_of=None,
        return_basis="adjusted",
        freshness="insufficient",
        regime="INSUFFICIENT",
        top_sector=None,
        bottom_sector=None,
        sector_outcomes=(),
        sector_outcome_basis="three_month_local_relative_proxy",
        source_id="unavailable",
        source_available_on=None,
        coverage_start=None,
        global_context=None,
        global_unavailable_reason=reason,
    )


def _record(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    matches = [row for row in rows if row[key] == value]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {key} record for {value}")
    return matches[0]


def _market(record: dict[str, Any]) -> Market:
    return Market(
        market_id=record["market_id"],
        name=record["name"],
        base_currency=record["base_currency"],
        timezone=record["timezone"],
        calendar_id=record["calendar_id"],
        local_benchmark_id=record["local_benchmark_id"],
        classification_scheme_id=record["classification_scheme_id"],
        enabled_from=date.fromisoformat(record["enabled_from"]),
        enabled_to=(date.fromisoformat(record["enabled_to"]) if record["enabled_to"] else None),
    )


def _history(record: dict[str, Any], *, as_of: date) -> pd.DataFrame:
    first = date.fromisoformat(record["first_session"])
    last = min(date.fromisoformat(record["last_session"]), as_of)
    if last < first:
        return pd.DataFrame({"close": pd.Series(dtype="float64")})
    sessions = xcals.get_calendar(record["calendar_id"]).sessions_in_range(first, last)
    closes = float(record["first_close"]) + np.arange(len(sessions)) * float(
        record["close_change_per_session"]
    )
    if not np.isfinite(closes).all() or (closes <= 0).any():
        raise ValueError("benchmark history contains invalid closes")
    return pd.DataFrame({"close": closes}, index=sessions)


def _global_context(
    *,
    market: Market,
    as_of: date,
    outcomes: tuple[SectorOutcome, ...],
    benchmark: Mapping[str, Any] | None,
    fx_rates: list[dict[str, Any]],
) -> tuple[GlobalContext | None, str | None]:
    if benchmark is None:
        return None, None
    if (
        date.fromisoformat(benchmark["as_of"]) != as_of
        or date.fromisoformat(benchmark["available_on"]) > as_of
        or benchmark["return_basis"] != "adjusted"
    ):
        return None, "Global benchmark is unavailable for the local observation date and basis"
    currency = benchmark["currency"]
    if market.base_currency != currency:
        aligned = [
            row
            for row in fx_rates
            if row["base_currency"] == market.base_currency
            and row["quote_currency"] == currency
            and date.fromisoformat(row["date"]) == as_of
            and date.fromisoformat(row["available_on"]) <= as_of
        ]
        if not aligned:
            return None, "Same-date currency conversion is unavailable"
        return None, "Currency conversion for the full comparison period is unavailable"
    global_returns = tuple(
        SectorOutcome(
            sector=outcome.sector,
            absolute_3m=outcome.absolute_3m,
            relative_3m=outcome.absolute_3m - float(benchmark["return_3m"]),
        )
        for outcome in outcomes
    )
    if not global_returns:
        return None, "No aligned sector outcomes are available"
    return (
        GlobalContext(
            benchmark_id=benchmark["benchmark_id"],
            currency=currency,
            top_sector=max(global_returns, key=lambda outcome: outcome.relative_3m),
        ),
        None,
    )


def compare_markets(
    selected_market_ids: tuple[str, ...],
    *,
    market_data: dict[str, Any],
    as_of: date,
    global_benchmark: Mapping[str, Any] | None = None,
) -> MarketComparison:
    if not selected_market_ids or len(set(selected_market_ids)) != len(selected_market_ids):
        raise ValueError("select one or more distinct markets")

    markets = market_data["markets"]
    histories = market_data["benchmark_histories"]
    sectors = market_data["sector_outcomes"]
    fx_rates = market_data["fx_rates"]
    fixture_as_of = date.fromisoformat(market_data["as_of"])
    overviews: list[MarketOverview] = []
    for market_id in selected_market_ids:
        market = _market(_record(markets, "market_id", market_id))
        if as_of < market.enabled_from or (
            market.enabled_to is not None and as_of > market.enabled_to
        ):
            raise ValueError(f"market {market_id} is not active on the requested date")
        if not any(row["market_id"] == market_id for row in histories):
            overviews.append(_insufficient_market(market, "Local benchmark history is unavailable"))
            continue
        benchmark = _record(histories, "market_id", market_id)
        if (
            benchmark["benchmark_id"] != market.local_benchmark_id
            or benchmark["currency"] != market.base_currency
            or benchmark["calendar_id"] != market.calendar_id
            or benchmark["return_basis"] != "adjusted"
        ):
            raise ValueError(f"market {market_id} has incompatible benchmark metadata")
        history = _history(benchmark, as_of=as_of)
        if history.empty:
            overviews.append(
                _insufficient_market(market, "No benchmark observations are available")
            )
            continue
        sentiment = calculate_market_sentiment(history, benchmark=market.local_benchmark_id)
        observed_on = cast(datetime, history.index[-1]).date()
        available_on = date.fromisoformat(benchmark["available_on"])
        if available_on > as_of:
            regime = "INSUFFICIENT"
        else:
            regime = sentiment.regime.upper()
        required_session = (
            xcals.get_calendar(market.calendar_id)
            .date_to_session(as_of.isoformat(), direction="previous")
            .date()
        )
        freshness = (
            "current" if observed_on == required_session and available_on <= as_of else "stale"
        )
        outcomes = (
            tuple(
                sorted(
                    (
                        SectorOutcome(
                            row["sector"],
                            float(row["absolute_3m"]),
                            float(row["relative_3m"]),
                        )
                        for row in sectors
                        if row["market_id"] == market_id
                    ),
                    key=lambda outcome: outcome.sector,
                )
            )
            if fixture_as_of <= as_of and available_on <= as_of
            else ()
        )
        top = max(outcomes, key=lambda item: item.relative_3m) if outcomes else None
        bottom = min(outcomes, key=lambda item: item.relative_3m) if outcomes else None
        global_context, unavailable_reason = _global_context(
            market=market,
            as_of=as_of,
            outcomes=outcomes,
            benchmark=global_benchmark,
            fx_rates=fx_rates,
        )
        overviews.append(
            MarketOverview(
                market_id=market.market_id,
                name=market.name,
                benchmark_id=market.local_benchmark_id,
                currency=market.base_currency,
                calendar_id=market.calendar_id,
                as_of=observed_on,
                return_basis=benchmark["return_basis"],
                freshness=freshness,
                regime=regime,
                top_sector=top,
                bottom_sector=bottom,
                sector_outcomes=outcomes,
                sector_outcome_basis="three_month_local_relative_proxy",
                source_id=benchmark["source_id"],
                source_available_on=available_on,
                coverage_start=cast(datetime, history.index[0]).date(),
                global_context=global_context,
                global_unavailable_reason=unavailable_reason,
            )
        )
    return MarketComparison(tuple(overviews))
