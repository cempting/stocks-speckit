from datetime import date
from pathlib import Path

import pandas as pd

from market_leadership.application.ports import MarketDataProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.provider_validation import canonicalize_daily_history
from market_leadership.infrastructure.snapshot_errors import SchemaMismatch, SnapshotNotFound


class ParquetSnapshotProvider(MarketDataProvider):
    provider_id = "parquet"

    def __init__(self, snapshot_root: str | Path, snapshot_id: str) -> None:
        self._repository = ParquetSnapshotRepository(snapshot_root)
        self._snapshot_id = snapshot_id

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del force
        tables = self._repository.load(self._snapshot_id)
        prices = tables.get("prices")
        if prices is None:
            raise SnapshotNotFound(self._snapshot_id, "prices")
        required = {"symbol", "date", "close", "volume"}
        if not required.issubset(prices.columns):
            raise SchemaMismatch(
                self._snapshot_id,
                "prices",
                "required columns are symbol, date, close, and volume",
            )
        normalized = prices.loc[:, ["symbol", "date", "close", "volume"]].copy()
        normalized["symbol"] = normalized["symbol"].astype(str)
        normalized["date"] = pd.to_datetime(normalized["date"], errors="raise")
        result: dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            selected = normalized.loc[normalized["symbol"] == symbol]
            result[symbol] = selected.set_index("date").loc[:, ["close", "volume"]]
        return canonicalize_daily_history(
            result,
            symbols,
            start=start,
            end=end,
            source_id=self.provider_id,
        )
