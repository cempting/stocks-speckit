from datetime import date

import numpy as np
import pandas as pd

from market_leadership.infrastructure.provider_validation import canonicalize_daily_history


class FixtureProvider:
    provider_id = "fixture"

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
