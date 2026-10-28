import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import exchange_calendars as xcals
import numpy as np
import pandas as pd

from market_leadership.application.ports import ProviderCapability
from market_leadership.domain.models import Market
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
