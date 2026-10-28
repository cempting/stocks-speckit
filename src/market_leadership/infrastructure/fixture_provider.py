import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import exchange_calendars as xcals
import numpy as np
import pandas as pd

from market_leadership.application.ports import (
    ProviderCapability,
    WeeklyMarketInputs,
    WeeklyPriceHistory,
)
from market_leadership.application.weekly_calendar import latest_completed_market_week
from market_leadership.domain.models import (
    ClassificationLevel,
    ClassificationNode,
    Market,
    ProxyType,
)
from market_leadership.domain.proxies import DocumentedRepresentation
from market_leadership.infrastructure.provider_validation import canonicalize_daily_history
from market_leadership.infrastructure.snapshot_errors import SchemaMismatch, SourceUnavailable

_ACCEPTANCE_MARKETS = Path(__file__).parents[3] / "tests/fixtures/acceptance/market_data.json"


def load_acceptance_market_context() -> dict[str, Any]:
    try:
        context = json.loads(_ACCEPTANCE_MARKETS.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SourceUnavailable("market-acceptance", "context") from error
    except json.JSONDecodeError as error:
        raise SchemaMismatch("market-acceptance", "context", "invalid JSON") from error
    if not isinstance(context, dict):
        raise SchemaMismatch("market-acceptance", "context", "expected a JSON object")
    return context


_MARKETS = (
    Market(
        "US", "United States", "USD", "America/New_York", "XNYS", "SPX", "GICS-US", date(2025, 1, 1)
    ),
    Market("JP", "Japan", "JPY", "Asia/Tokyo", "XTKS", "N225", "GICS-JP", date(2025, 1, 1)),
    Market(
        "GB", "United Kingdom", "GBP", "Europe/London", "XLON", "UKX", "GICS-GB", date(2025, 1, 1)
    ),
)


@dataclass(frozen=True, slots=True)
class _BenchmarkHistory:
    market: Market
    first_session: date
    last_session: date
    first_close: float
    close_change_per_session: float
    available_on: date

    def __post_init__(self) -> None:
        if (
            self.first_session < self.market.enabled_from
            or self.last_session < self.first_session
            or self.available_on < self.last_session
            or (self.market.enabled_to is not None and self.last_session > self.market.enabled_to)
        ):
            raise ValueError("fixture benchmark dates conflict with market or source availability")
        if not np.isfinite(self.first_close) or self.first_close <= 0:
            raise ValueError("fixture benchmark close must be positive")
        xcals.get_calendar(self.market.calendar_id)


_BENCHMARKS = (
    _BenchmarkHistory(
        _MARKETS[0], date(2026, 1, 2), date(2026, 10, 23), 5785.0, 5.0, date(2026, 10, 23)
    ),
    _BenchmarkHistory(
        _MARKETS[1], date(2026, 1, 5), date(2026, 10, 23), 51000.0, 0.0, date(2026, 10, 23)
    ),
    _BenchmarkHistory(
        _MARKETS[2], date(2026, 1, 2), date(2026, 10, 23), 11040.0, -8.0, date(2026, 10, 23)
    ),
)


class FixtureProvider:
    provider_id = "fixture"

    def weekly_inputs(self, market_id: str, *, as_of: date) -> WeeklyMarketInputs:
        fixture = load_acceptance_market_context()
        matches = [item for item in fixture["markets"] if item["market_id"] == market_id]
        if len(matches) != 1:
            raise ValueError(f"unknown or duplicate fixture market: {market_id}")
        record = matches[0]
        market = Market(
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
        weekly = fixture["weekly"]
        first = date.fromisoformat(weekly["first_session"])
        last = date.fromisoformat(weekly["last_session"])
        completed = latest_completed_market_week(
            market.calendar_id, min(as_of, last + timedelta(days=1))
        )
        if (
            completed < first
            or completed < market.enabled_from
            or (market.enabled_to is not None and completed > market.enabled_to)
        ):
            raise ValueError(f"no completed fixture week is available for {market_id}")

        nodes = tuple(
            ClassificationNode(
                node_id=item["node_id"],
                scheme_id=market.classification_scheme_id,
                level=ClassificationLevel(item["level"]),
                name=item["name"],
                parent_node_id=item["parent_node_id"],
                effective_from=date.fromisoformat(item["effective_from"]),
                effective_to=(
                    date.fromisoformat(item["effective_to"]) if item["effective_to"] else None
                ),
            )
            for item in weekly["nodes"]
            if item["market_id"] == market_id
            and date.fromisoformat(item["effective_from"]) <= completed
            and (
                item["effective_to"] is None
                or completed <= date.fromisoformat(item["effective_to"])
            )
        )
        by_id = {node.node_id: node for node in nodes}
        if len(by_id) != len(nodes):
            raise ValueError(f"duplicate classification node for {market_id}")
        for node in nodes:
            if node.level is ClassificationLevel.SECTOR:
                continue
            if node.parent_node_id not in by_id:
                raise ValueError(f"industry parent is unavailable for {node.node_id}")
            parent = by_id[node.parent_node_id]
            allowed_parents = {
                ClassificationLevel.INDUSTRY_GROUP: (ClassificationLevel.SECTOR,),
                ClassificationLevel.INDUSTRY: (
                    ClassificationLevel.SECTOR,
                    ClassificationLevel.INDUSTRY_GROUP,
                ),
                ClassificationLevel.SUB_INDUSTRY: (ClassificationLevel.INDUSTRY,),
            }
            if parent.level not in allowed_parents[node.level]:
                raise ValueError(f"industry parent has the wrong hierarchy for {node.node_id}")

        representations = tuple(
            DocumentedRepresentation(
                market_id=item["market_id"],
                node_id=item["node_id"],
                proxy_id=item["proxy_id"],
                proxy_type=ProxyType(item["proxy_type"]),
                instrument_id=item["instrument_id"],
                composition_basis=item["composition_basis"],
                source_id=item["source_id"],
                qualified=item["qualified"],
                effective_from=date.fromisoformat(item["effective_from"]),
                effective_to=(
                    date.fromisoformat(item["effective_to"]) if item["effective_to"] else None
                ),
                member_ids=tuple(item.get("member_ids", ())),
            )
            for item in weekly["representations"]
            if item["market_id"] == market_id
            and date.fromisoformat(item["effective_from"]) <= completed
            and (
                item["effective_to"] is None
                or completed <= date.fromisoformat(item["effective_to"])
            )
        )
        if any(proxy.node_id not in by_id for proxy in representations):
            raise ValueError(f"representation references missing classification for {market_id}")
        if len({proxy.proxy_id for proxy in representations}) != len(representations):
            raise ValueError(f"duplicate representation for {market_id}")

        sessions = xcals.get_calendar(market.calendar_id).sessions_in_range(first, completed)
        histories: dict[str, WeeklyPriceHistory] = {}
        for item in weekly["histories"]:
            if item["market_id"] != market_id:
                continue
            instrument_id = item["instrument_id"]
            if instrument_id in histories:
                raise ValueError(f"duplicate weekly history for {instrument_id}")
            if item["currency"] != market.base_currency or item["return_basis"] != "adjusted":
                raise ValueError(f"incompatible weekly price basis for {instrument_id}")
            closes = float(item["first_close"]) + np.arange(len(sessions)) * float(
                item["change_per_session"]
            )
            if not np.isfinite(closes).all() or (closes <= 0).any():
                raise ValueError(f"invalid weekly fixture closes for {instrument_id}")
            histories[instrument_id] = WeeklyPriceHistory(
                instrument_id=instrument_id,
                currency=item["currency"],
                return_basis=item["return_basis"],
                closes=pd.Series(closes, index=sessions.tz_localize(None)),
                source_id=weekly["source_id"],
                available_on=completed,
            )
        if market.local_benchmark_id not in histories:
            raise ValueError(f"local benchmark history is unavailable for {market_id}")
        return WeeklyMarketInputs(
            market=market,
            as_of=completed,
            classifications=nodes,
            representations=representations,
            histories=histories,
            classification_version=weekly["classification_version"],
            representation_version=weekly["representation_version"],
            source_id=weekly["source_id"],
        )

    @staticmethod
    def markets() -> tuple[Market, ...]:
        return _MARKETS

    @staticmethod
    def capabilities() -> tuple[ProviderCapability, ...]:
        benchmarks = tuple(
            ProviderCapability(
                data_point="daily_history",
                markets=frozenset({history.market.market_id}),
                frequencies=frozenset({"1d"}),
                currencies=frozenset({history.market.base_currency}),
                return_bases=frozenset({"adjusted"}),
                identifiers=frozenset({history.market.local_benchmark_id}),
                effective_from=history.market.enabled_from,
                effective_to=history.market.enabled_to,
                available_on=history.available_on,
            )
            for history in _BENCHMARKS
        )
        return benchmarks + (
            ProviderCapability(
                data_point="daily_history",
                markets=frozenset({"US"}),
                frequencies=frozenset({"1d"}),
                currencies=frozenset({"USD"}),
                return_bases=frozenset({"adjusted"}),
                excluded_identifiers=frozenset(
                    history.market.local_benchmark_id for history in _BENCHMARKS
                ),
            ),
        )

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del force
        index = pd.bdate_range(start=start, end=end)
        session = np.arange(len(index), dtype=float)
        result: dict[str, pd.DataFrame] = {}
        for offset, symbol in enumerate(symbols):
            benchmark = next(
                (history for history in _BENCHMARKS if history.market.local_benchmark_id == symbol),
                None,
            )
            if benchmark is not None:
                if start < benchmark.market.enabled_from or end > benchmark.available_on:
                    raise ValueError(f"{symbol} is outside its fixture benchmark availability")
                sessions = xcals.get_calendar(benchmark.market.calendar_id).sessions_in_range(
                    benchmark.first_session, benchmark.last_session
                )
                closes = benchmark.first_close + (
                    np.arange(len(sessions), dtype=float) * benchmark.close_change_per_session
                )
                result[symbol] = pd.DataFrame(
                    {"close": closes, "volume": np.zeros(len(sessions))},
                    index=sessions,
                )
                continue
            base = 80 + offset * 3
            trend = 0.13 + offset * 0.004
            close = base + session * trend + np.sin(session / 13 + offset) * 2.2
            volume = 8_000_000 + offset * 400_000 + np.cos(session / 9) * 900_000
            result[symbol] = pd.DataFrame(
                {"close": close, "volume": volume},
                index=index,
            )
        return canonicalize_daily_history(
            result,
            symbols,
            start=start,
            end=end,
            source_id=self.provider_id,
        )
