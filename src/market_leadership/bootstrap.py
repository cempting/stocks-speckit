from collections.abc import Callable
from typing import Any

from market_leadership.application.ports import (
    MarketDataProvider,
    MarketDataProviderCatalog,
    ProviderCapability,
)
from market_leadership.application.request_market_data import (
    RequestedDailyHistoryProvider,
    RequestMarketData,
)
from market_leadership.config import Settings
from market_leadership.infrastructure.fixture_provider import (
    FixtureProvider,
    load_acceptance_market_context,
)
from market_leadership.infrastructure.market_data_cache import CachedMarketDataProvider
from market_leadership.infrastructure.massive_provider import MassiveProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.provider_catalog import ConfiguredProviderCatalog
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider
from market_leadership.ui.navigation import WorkflowSpec, validate_workflows

_DAILY_HISTORY_CAPABILITY = ProviderCapability(
    data_point="daily_history",
    markets=frozenset({"US"}),
    frequencies=frozenset({"1d"}),
    currencies=frozenset({"USD"}),
    return_bases=frozenset({"adjusted"}),
)


def build_workflow_registry(
    discovery_render: Callable[[], None],
) -> tuple[WorkflowSpec, ...]:
    return validate_workflows(
        (
            WorkflowSpec(
                key="sector-discovery",
                title="US Sector Discovery",
                url_path="discovery",
                icon=":material/monitoring:",
                render=discovery_render,
                default=True,
            ),
        )
    )


def _build_provider_adapter(provider_id: str, retry_limit: int) -> MarketDataProvider:
    if provider_id == "massive":
        return MassiveProvider(retry_limit=retry_limit)
    if provider_id == "yfinance":
        return YFinanceProvider(retry_limit=retry_limit)
    if provider_id == "fixture":
        return FixtureProvider()
    raise ValueError(f"Unknown market data provider: {provider_id}")


def build_provider(
    provider_id: str,
    cache_path: str = ".cache/market-data",
    *,
    retry_limit: int = 2,
) -> MarketDataProvider:
    provider = _build_provider_adapter(provider_id, retry_limit)
    if provider_id == "fixture":
        return provider
    return CachedMarketDataProvider(provider, cache_path)


def _provider_capabilities(provider: MarketDataProvider) -> tuple[ProviderCapability, ...]:
    if provider.provider_id == "fixture" and isinstance(provider, FixtureProvider):
        return provider.capabilities()
    if isinstance(provider, YFinanceProvider):
        return provider.capabilities()
    return (_DAILY_HISTORY_CAPABILITY,)


def build_market_data_catalog(settings: Settings) -> MarketDataProviderCatalog:
    providers = tuple(
        _build_provider_adapter(provider_id, settings.retry_limit)
        for provider_id in settings.provider_ids
    )
    capabilities = {
        provider.provider_id: _provider_capabilities(provider) for provider in providers
    }
    return ConfiguredProviderCatalog(
        providers,
        capabilities,
        dict(settings.provider_priorities),
    )


def build_market_data_request(settings: Settings) -> RequestMarketData:
    return RequestMarketData(
        build_market_data_catalog(settings),
        settings.source_cache_path,
    )


def build_snapshot_repository(settings: Settings) -> ParquetSnapshotRepository:
    return ParquetSnapshotRepository(settings.snapshot_dir)


def build_fixture_market_context() -> dict[str, Any]:
    return load_acceptance_market_context()


def build_request_provider(
    provider_id: str,
    source_cache_path: str,
    *,
    retry_limit: int = 2,
) -> MarketDataProvider:
    provider = _build_provider_adapter(provider_id, retry_limit)
    catalog = ConfiguredProviderCatalog(
        (provider,),
        {provider_id: _provider_capabilities(provider)},
        {},
    )
    return RequestedDailyHistoryProvider(
        provider_id,
        RequestMarketData(catalog, source_cache_path),
    )
