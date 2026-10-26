from datetime import date
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    provider_id: str

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]: ...
