from market_leadership.application.ports import MarketDataProvider
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.market_data_cache import CachedMarketDataProvider
from market_leadership.infrastructure.massive_provider import MassiveProvider
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider


def build_provider(
    provider_id: str, cache_path: str = ".cache/market-data"
) -> MarketDataProvider:
    if provider_id == "massive":
        return CachedMarketDataProvider(MassiveProvider(), cache_path)
    if provider_id == "yfinance":
        return CachedMarketDataProvider(YFinanceProvider(), cache_path)
    if provider_id == "fixture":
        return FixtureProvider()
    raise ValueError(f"Unknown market data provider: {provider_id}")
