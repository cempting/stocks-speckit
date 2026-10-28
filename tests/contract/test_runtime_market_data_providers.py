from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from market_leadership.application.ports import (
    DataPointRequest,
    ProviderCapability,
)
from market_leadership.infrastructure.massive_provider import MassiveProvider
from market_leadership.infrastructure.provider_catalog import ConfiguredProviderCatalog
from market_leadership.infrastructure.provider_errors import ProviderRequestError
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider


def _request() -> DataPointRequest:
    return DataPointRequest(
        data_point="daily_history",
        market_id="US",
        identifiers=("SPY", "XLB"),
        frequency="1d",
        start=date(2026, 10, 20),
        end=date(2026, 10, 23),
        currency="USD",
        return_basis="adjusted",
    )


def _capability(
    *,
    market: str = "US",
    return_basis: str = "adjusted",
) -> ProviderCapability:
    return ProviderCapability(
        data_point="daily_history",
        markets=frozenset({market}),
        frequencies=frozenset({"1d"}),
        currencies=frozenset({"USD"}),
        return_bases=frozenset({return_basis}),
        identifiers=frozenset({"SPY", "XLB"}),
    )


class StubHistoryProvider:
    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del symbols, start, end, force
        return {}


def test_catalog_discovers_every_capable_configured_direct_provider() -> None:
    providers = tuple(StubHistoryProvider(provider_id) for provider_id in ("massive", "yfinance"))
    catalog = ConfiguredProviderCatalog(
        providers,
        {provider.provider_id: (_capability(),) for provider in providers},
        {"massive": 2, "yfinance": 3},
    )

    candidates = catalog.discover(_request())

    assert [candidate.provider_id for candidate in candidates] == ["massive", "yfinance"]


def test_catalog_excludes_providers_missing_one_requested_capability() -> None:
    providers = (
        StubHistoryProvider("wrong-market"),
        StubHistoryProvider("wrong-basis"),
        StubHistoryProvider("matches"),
    )
    catalog = ConfiguredProviderCatalog(
        providers,
        {
            "wrong-market": (_capability(market="CA"),),
            "wrong-basis": (_capability(return_basis="official_close"),),
            "matches": (_capability(),),
        },
        {},
    )

    assert [candidate.provider_id for candidate in catalog.discover(_request())] == ["matches"]


def test_massive_maps_daily_request_and_iterates_all_pages() -> None:
    seen_requests: list[dict[str, object]] = []
    yielded_pages: list[int] = []

    class Client:
        def list_aggs(self, **kwargs: object):
            seen_requests.append(kwargs)

            def pages():
                yielded_pages.append(1)
                yield SimpleNamespace(close=100.0, volume=1_000.0, timestamp=1792728000000)
                yielded_pages.append(2)
                yield SimpleNamespace(close=101.0, volume=1_100.0, timestamp=1792814400000)

            return pages()

    history = MassiveProvider(client=Client()).fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 20),
        end=date(2026, 10, 24),
    )["SPY"]

    assert seen_requests == [
        {
            "ticker": "SPY",
            "multiplier": 1,
            "timespan": "day",
            "from_": "2026-10-20",
            "to": "2026-10-24",
            "adjusted": True,
            "sort": "asc",
            "limit": 50_000,
        }
    ]
    assert history.index.tolist() == list(pd.to_datetime(["2026-10-23", "2026-10-24"]))
    assert yielded_pages == [1, 2]
    assert history.attrs["source_id"] == "massive"
    assert list(history.columns) == ["close", "volume"]


def test_yfinance_maps_requested_range_and_uses_explicit_adjusted_prices() -> None:
    calls: list[dict[str, object]] = []
    downloaded = pd.DataFrame(
        {
            "Close": [101.0],
            "Volume": [1_100.0],
        },
        index=pd.to_datetime(["2026-10-23"]),
    )

    def downloader(**kwargs: object) -> pd.DataFrame:
        calls.append(kwargs)
        return downloaded

    history = YFinanceProvider(downloader=downloader).fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 20),
        end=date(2026, 10, 23),
    )["SPY"]

    assert calls == [
        {
            "tickers": ["SPY"],
            "start": "2026-10-20",
            "end": "2026-10-24",
            "interval": "1d",
            "auto_adjust": True,
            "actions": False,
            "progress": False,
            "group_by": "ticker",
            "threads": True,
        }
    ]
    assert history.iloc[-1].to_dict() == {"close": 101.0, "volume": 1_100.0}
    assert history.attrs["source_id"] == "yfinance"


def test_yfinance_missing_ticker_returns_typed_empty_canonical_history() -> None:
    downloaded = pd.DataFrame(
        {
            ("SPY", "Close"): [100.0],
            ("SPY", "Volume"): [1_000.0],
        },
        index=pd.to_datetime(["2026-10-23"]),
    )
    downloaded.columns = pd.MultiIndex.from_tuples(downloaded.columns)

    history = YFinanceProvider(downloader=lambda **kwargs: downloaded).fetch_daily_history(
        ("XLB",),
        start=date(2026, 10, 20),
        end=date(2026, 10, 23),
    )["XLB"]

    assert history.empty
    assert list(history.columns) == ["close", "volume"]
    assert history["close"].dtype == "float64"
    assert history["volume"].dtype == "float64"
    assert history.attrs == {"source_id": "yfinance", "available_on": None}


def test_providers_report_retryable_failures_without_echoing_credentials() -> None:
    secret = "market-key-that-must-not-leak"
    calls = 0

    class TemporaryUpstreamError(RuntimeError):
        status_code = 503

    class Client:
        def list_aggs(self, **kwargs: object) -> list[SimpleNamespace]:
            nonlocal calls
            calls += 1
            raise TemporaryUpstreamError(f"unavailable with key {secret}")

    with pytest.raises(ProviderRequestError, match="massive") as error:
        MassiveProvider(client=Client(), retry_limit=1).fetch_daily_history(
            ("SPY",),
            start=date(2026, 10, 20),
            end=date(2026, 10, 23),
        )

    assert calls == 2
    assert error.value.retryable is True
    assert secret not in str(error.value)
    assert error.value.__cause__ is None


def test_non_retryable_massive_failure_is_not_retried_and_has_safe_message() -> None:
    calls = 0

    class Client:
        def list_aggs(self, **kwargs: object) -> list[SimpleNamespace]:
            nonlocal calls
            calls += 1
            raise ValueError("private response payload")

    with pytest.raises(ProviderRequestError, match="Provider massive failed") as error:
        MassiveProvider(client=Client(), retry_limit=4).fetch_daily_history(
            ("SPY",),
            start=date(2026, 10, 20),
            end=date(2026, 10, 23),
        )

    assert calls == 1
    assert error.value.retryable is False
    assert "private response payload" not in str(error.value)


def test_yfinance_retries_transient_failures_and_sanitizes_errors() -> None:
    secret = "private-yfinance-response"
    calls = 0

    class TemporaryUpstreamError(TimeoutError):
        pass

    def downloader(**kwargs: object) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TemporaryUpstreamError(secret)
        return pd.DataFrame(
            {
                "Close": [100.0],
                "Volume": [1_000.0],
            },
            index=pd.to_datetime(["2026-10-23"]),
        )

    history = YFinanceProvider(downloader=downloader, retry_limit=1).fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 20),
        end=date(2026, 10, 23),
    )

    assert calls == 2
    assert history["SPY"].iloc[-1]["close"] == 100.0
    assert history["SPY"].attrs["source_id"] == "yfinance"


def test_yfinance_exhausted_transient_failure_is_typed_and_secret_safe() -> None:
    secret = "private-yfinance-response"
    calls = 0

    def downloader(**kwargs: object) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        raise TimeoutError(secret)

    with pytest.raises(ProviderRequestError) as error:
        YFinanceProvider(downloader=downloader, retry_limit=1).fetch_daily_history(
            ("SPY",),
            start=date(2026, 10, 20),
            end=date(2026, 10, 23),
        )

    assert calls == 2
    assert error.value.provider_id == "yfinance"
    assert error.value.retryable is True
    assert secret not in str(error.value)


def test_yfinance_returns_index_and_stock_history_without_inventing_missing_volume() -> None:
    columns = pd.MultiIndex.from_product(
        [["^GSPC", "AAPL"], ["Close", "Volume"]], names=["Ticker", "Price"]
    )
    downloaded = pd.DataFrame(
        [[5000.0, 0.0, 150.0, 1200.0]],
        columns=columns,
        index=pd.to_datetime(["2026-10-23"]),
    )
    provider = YFinanceProvider(downloader=lambda **kwargs: downloaded)

    history = provider.fetch_daily_history(
        ("^GSPC", "AAPL"), start=date(2026, 10, 23), end=date(2026, 10, 23)
    )

    assert history["^GSPC"].iloc[0].to_dict() == {"close": 5000.0, "volume": 0.0}
    assert history["AAPL"].iloc[0].to_dict() == {"close": 150.0, "volume": 1200.0}


@pytest.mark.parametrize(
    "columns",
    [
        {"Close": [101.0]},
        {"Close": [101.0], "Volume": [float("nan")]},
        {"Close": [float("nan")], "Volume": [100.0]},
        {"Close": [101.0], "Volume": [-1.0]},
    ],
)
def test_yfinance_rejects_incomplete_or_invalid_observations(
    columns: dict[str, list[float]],
) -> None:
    downloaded = pd.DataFrame(columns, index=pd.to_datetime(["2026-10-23"]))
    provider = YFinanceProvider(downloader=lambda **kwargs: downloaded)

    with pytest.raises(ValueError, match="(volume|close|canonical columns)"):
        provider.fetch_daily_history(("AAPL",), start=date(2026, 10, 23), end=date(2026, 10, 23))


def test_yfinance_does_not_claim_unsupported_canonical_data_points() -> None:
    provider = YFinanceProvider(downloader=lambda **kwargs: pd.DataFrame())
    assert {capability.data_point for capability in provider.capabilities()} == {"daily_history"}
    for data_point in ("fx_rates", "classification", "holdings", "fundamentals", "evidence"):
        request = DataPointRequest(
            data_point=data_point,
            market_id="US",
            identifiers=("AAPL",),
            frequency="1d",
            start=date(2026, 10, 23),
            end=date(2026, 10, 23),
            currency="USD",
            return_basis="adjusted",
        )
        with pytest.raises(NotImplementedError, match=data_point):
            provider.fetch_canonical(request)


def test_yfinance_rejects_requests_outside_its_declared_capability() -> None:
    provider = YFinanceProvider(downloader=lambda **kwargs: pd.DataFrame())
    request = DataPointRequest(
        data_point="daily_history",
        market_id="GB",
        identifiers=("AAPL",),
        frequency="1d",
        start=date(2026, 10, 23),
        end=date(2026, 10, 23),
        currency="GBP",
        return_basis="official_close",
    )
    with pytest.raises(NotImplementedError, match="daily_history"):
        provider.fetch_canonical(request)


def test_yfinance_fetch_canonical_routes_supported_history_request() -> None:
    downloaded = pd.DataFrame(
        {"Close": [101.0], "Volume": [1000.0]},
        index=pd.to_datetime(["2026-10-23"]),
    )
    provider = YFinanceProvider(downloader=lambda **kwargs: downloaded)
    history = provider.fetch_canonical(
        DataPointRequest(
            data_point="daily_history",
            market_id="US",
            identifiers=("SPY",),
            frequency="1d",
            start=date(2026, 10, 23),
            end=date(2026, 10, 23),
            currency="USD",
            return_basis="adjusted",
        )
    )
    assert history["SPY"].iloc[0].to_dict() == {"close": 101.0, "volume": 1000.0}
