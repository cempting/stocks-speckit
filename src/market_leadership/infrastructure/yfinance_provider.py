from collections.abc import Callable
from datetime import date, timedelta
from importlib import import_module
from typing import Any, cast

import pandas as pd

from market_leadership.application.ports import DataPointRequest, ProviderCapability
from market_leadership.infrastructure.provider_errors import (
    ProviderRequestError,
    is_retryable_provider_failure,
    retryable_status_code,
)
from market_leadership.infrastructure.provider_validation import canonicalize_daily_history

yf = import_module("yfinance")


class YFinanceProvider:
    provider_id = "yfinance"

    @staticmethod
    def capabilities() -> tuple[ProviderCapability, ...]:
        return (
            ProviderCapability(
                data_point="daily_history",
                markets=frozenset({"US"}),
                frequencies=frozenset({"1d"}),
                currencies=frozenset({"USD"}),
                return_bases=frozenset({"adjusted"}),
            ),
        )

    def fetch_canonical(self, request: DataPointRequest) -> dict[str, pd.DataFrame]:
        if not any(capability.covers(request) for capability in self.capabilities()):
            raise NotImplementedError(
                f"yfinance does not provide verified canonical {request.data_point} "
                "for the requested market, frequency, currency and return basis"
            )
        return self.fetch_daily_history(request.identifiers, start=request.start, end=request.end)

    def __init__(
        self,
        downloader: Callable[..., pd.DataFrame] | None = None,
        retry_limit: int = 2,
    ) -> None:
        if retry_limit < 0:
            raise ValueError("retry_limit must be non-negative")
        self._retry_limit = retry_limit
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
        downloaded: pd.DataFrame | None = None
        for attempt in range(self._retry_limit + 1):
            try:
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
                break
            except Exception as error:
                retryable = is_retryable_provider_failure(error)
                status_code = retryable_status_code(error)
                if retryable and attempt < self._retry_limit:
                    continue
                raise ProviderRequestError(
                    self.provider_id,
                    "daily history",
                    retryable=retryable,
                    status_code=status_code,
                ) from None
        assert downloaded is not None
        result = {symbol: self._extract_symbol(downloaded, symbol, symbols) for symbol in symbols}
        return canonicalize_daily_history(
            result,
            symbols,
            start=start,
            end=end,
            source_id=self.provider_id,
        )

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

        normalized = symbol_frame.copy()
        normalized.columns = [str(column).lower() for column in normalized.columns]
        if not {"close", "volume"}.issubset(normalized.columns):
            raise ValueError(f"Daily history for {symbol} lacks canonical columns")
        result = normalized.loc[:, ["close", "volume"]].dropna(how="all").sort_index().copy()
        complete = result.notna().all(axis=1)
        if complete.any():
            result = result.loc[: result.index[complete][-1]]
        result.index = pd.DatetimeIndex(result.index).tz_localize(None)
        return result

    @staticmethod
    def _empty_history() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "close": pd.Series(dtype="float64"),
                "volume": pd.Series(dtype="float64"),
            }
        )
