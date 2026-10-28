from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

import pandas as pd

from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.ports import (
    DataPointRequest,
    MarketDataProvider,
    MarketDataProviderCatalog,
    ProviderCandidate,
    SelectionReason,
    select_provider,
)
from market_leadership.infrastructure.market_data_cache import CachedMarketDataProvider


@dataclass(frozen=True, slots=True)
class RequestedMarketData:
    data: dict[str, pd.DataFrame]
    selected: ProviderCandidate
    alternatives: tuple[ProviderCandidate, ...]
    selection_reason: SelectionReason


class RequestMarketData:
    def __init__(
        self,
        catalog: MarketDataProviderCatalog,
        source_cache_path: str | Path,
    ) -> None:
        self._catalog = catalog
        self._source_cache_path = Path(source_cache_path)

    def execute(
        self,
        request: DataPointRequest,
        *,
        force: bool = False,
    ) -> RequestedMarketData:
        if request.data_point != "daily_history" or request.frequency != "1d":
            raise ValueError(
                "the configured daily-history service only accepts daily_history requests"
            )
        if request.market_id == "US":
            required_session = latest_completed_us_session(request.end)
            if required_session < request.start:
                raise ValueError("request start date must not follow the required session")
            request = replace(request, end=required_session)
        candidates = self._catalog.discover(request)
        selection = select_provider(candidates)
        cached_provider = CachedMarketDataProvider(
            selection.selected.provider,
            self._source_cache_path,
            alternatives=tuple(candidate.provider_id for candidate in selection.alternatives),
            selection_reason=selection.reason.value,
        )
        result = cached_provider.fetch_daily_history(
            request.identifiers,
            start=request.start,
            end=request.end,
            force=force,
        )
        return RequestedMarketData(
            data=result,
            selected=selection.selected,
            alternatives=selection.alternatives,
            selection_reason=selection.reason,
        )


class RequestedDailyHistoryProvider(MarketDataProvider):
    def __init__(self, provider_id: str, request_market_data: RequestMarketData) -> None:
        self.provider_id = provider_id
        self._request_market_data = request_market_data

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        requested = self._request_market_data.execute(
            DataPointRequest(
                data_point="daily_history",
                market_id="US",
                identifiers=symbols,
                frequency="1d",
                start=start,
                end=end,
                currency="USD",
                return_basis="adjusted",
            ),
            force=force,
        )
        if requested.selected.provider_id != self.provider_id:
            raise RuntimeError(
                "selected provider does not match the configured daily-history provider"
            )
        return requested.data
