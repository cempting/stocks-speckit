import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    default_provider: str
    massive_available: bool
    market_data_cache_path: str


def load_settings() -> Settings:
    load_dotenv(override=False)
    configured = os.getenv("MARKET_DATA_PROVIDER")
    massive_available = bool(os.getenv("MASSIVE_API_KEY"))
    default_provider = configured or "yfinance"
    market_data_cache_path = os.getenv("MARKET_DATA_CACHE_PATH", ".cache/market-data")
    return Settings(
        default_provider=default_provider,
        massive_available=massive_available,
        market_data_cache_path=market_data_cache_path,
    )
