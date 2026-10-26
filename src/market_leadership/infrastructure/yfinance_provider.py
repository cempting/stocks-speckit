from collections.abc import Callable
from datetime import date, timedelta
from typing import Any, cast

import pandas as pd
import yfinance as yf


class YFinanceProvider:
    provider_id = "yfinance"

    def __init__(self, downloader: Callable[..., pd.DataFrame] | None = None) -> None:
        self._downloader: Callable[..., pd.DataFrame] = downloader or cast(
            Callable[..., pd.DataFrame], yf.download
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
        downloaded = self._downloader(
            tickers=list(symbols),
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=True,
            actions=False,
            progress=False,
            group_by="ticker",
            threads=True,
        )
        return {symbol: self._extract_symbol(downloaded, symbol, symbols) for symbol in symbols}

    @staticmethod
    def _extract_symbol(
        downloaded: pd.DataFrame,
        symbol: str,
        requested_symbols: tuple[str, ...],
    ) -> pd.DataFrame:
        if downloaded.empty:
            return YFinanceProvider._empty_history()

        symbol_frame: Any
        if isinstance(downloaded.columns, pd.MultiIndex):
            if symbol in downloaded.columns.get_level_values(0):
                symbol_frame = downloaded[symbol]
            elif symbol in downloaded.columns.get_level_values(1):
                symbol_frame = downloaded.xs(symbol, axis=1, level=1)
            else:
                return YFinanceProvider._empty_history()
        elif len(requested_symbols) == 1:
            symbol_frame = downloaded
        else:
            return YFinanceProvider._empty_history()

        normalized = symbol_frame.rename(columns=lambda column: str(column).lower())
        if not {"close", "volume"}.issubset(normalized.columns):
            return YFinanceProvider._empty_history()
        result = normalized.loc[:, ["close", "volume"]].dropna(subset=["close"])
        result.index = pd.DatetimeIndex(result.index).tz_localize(None)
        return result.sort_index().astype({"close": "float64", "volume": "float64"})

    @staticmethod
    def _empty_history() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "close": pd.Series(dtype="float64"),
                "volume": pd.Series(dtype="float64"),
            }
        )
