import os
from collections.abc import Iterable
from datetime import date
from typing import Any, cast

import pandas as pd
from massive import RESTClient

from market_leadership.infrastructure.provider_errors import (
    ProviderRequestError,
    is_retryable_provider_failure,
    retryable_status_code,
)
from market_leadership.infrastructure.provider_validation import canonicalize_daily_history


class MassiveProvider:
    provider_id = "massive"

    def __init__(
        self,
        client: Any | None = None,
        api_key: str | None = None,
        retry_limit: int = 2,
    ) -> None:
        if retry_limit < 0:
            raise ValueError("retry_limit must be non-negative")
        self._retry_limit = retry_limit
        self._client: Any
        if client is not None:
            self._client = client
            return

        resolved_key = api_key or os.getenv("MASSIVE_API_KEY")
        if not resolved_key:
            raise ValueError("MASSIVE_API_KEY is required for the Massive provider")
        self._client = RESTClient(api_key=resolved_key)

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del force
        result = {
            symbol: self._fetch_symbol(symbol=symbol, start=start, end=end) for symbol in symbols
        }
        return canonicalize_daily_history(
            result,
            symbols,
            start=start,
            end=end,
            source_id=self.provider_id,
        )

    def _fetch_symbol(self, *, symbol: str, start: date, end: date) -> pd.DataFrame:
        for attempt in range(self._retry_limit + 1):
            try:
                aggregates = cast(
                    Iterable[Any],
                    self._client.list_aggs(
                        ticker=symbol,
                        multiplier=1,
                        timespan="day",
                        from_=start.isoformat(),
                        to=end.isoformat(),
                        adjusted=True,
                        sort="asc",
                        limit=50_000,
                    ),
                )
                records = [
                    {
                        "date": pd.to_datetime(item.timestamp, unit="ms", utc=True)
                        .tz_convert("America/New_York")
                        .tz_localize(None)
                        .normalize(),
                        "close": float(item.close),
                        "volume": float(item.volume),
                    }
                    for item in aggregates
                    if item.close is not None and item.timestamp is not None
                ]
                break
            except Exception as error:
                retryable = is_retryable_provider_failure(error)
                status_code = retryable_status_code(error)
                if retryable and attempt < self._retry_limit:
                    continue
                raise ProviderRequestError(
                    self.provider_id,
                    f"daily history for {symbol}",
                    retryable=retryable,
                    status_code=status_code,
                ) from None
        if not records:
            return pd.DataFrame(
                {
                    "close": pd.Series(dtype="float64"),
                    "volume": pd.Series(dtype="float64"),
                }
            )
        return pd.DataFrame.from_records(records).set_index("date").sort_index()
