import os
from collections.abc import Iterable
from datetime import date
from typing import Any, cast

import pandas as pd
from massive import RESTClient


class MassiveProvider:
    provider_id = "massive"

    def __init__(self, client: Any | None = None, api_key: str | None = None) -> None:
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
        return {
            symbol: self._fetch_symbol(symbol=symbol, start=start, end=end) for symbol in symbols
        }

    def _fetch_symbol(self, *, symbol: str, start: date, end: date) -> pd.DataFrame:
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
        if not records:
            return pd.DataFrame(
                {
                    "close": pd.Series(dtype="float64"),
                    "volume": pd.Series(dtype="float64"),
                }
            )
        return pd.DataFrame.from_records(records).set_index("date").sort_index()
