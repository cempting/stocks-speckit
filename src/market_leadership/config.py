import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    default_provider: str
    massive_available: bool
    market_data_cache_path: str
    source_cache_path: str
    provider_ids: tuple[str, ...]
    provider_priorities: tuple[tuple[str, int], ...]
    retry_limit: int
    massive_api_key_reference: str = "MASSIVE_API_KEY"
    snapshot_dir: str = ".data/snapshots"
    stock_membership_catalog: str = ""
    fundamental_display_approval: str = ""
    experimental_universe_catalog: str = ".data/experimental-us-industry-catalog.json"


def load_settings() -> Settings:
    load_dotenv(override=False)
    market_data_cache_path = os.getenv("MARKET_DATA_CACHE_PATH", ".cache/market-data")
    source_cache_path = os.getenv("MARKET_DATA_SOURCE_CACHE_PATH", market_data_cache_path)
    try:
        retry_limit = int(os.getenv("MARKET_DATA_RETRY_LIMIT", "2"))
    except ValueError as error:
        raise ValueError("MARKET_DATA_RETRY_LIMIT must be a non-negative integer") from error
    if retry_limit < 0:
        raise ValueError("MARKET_DATA_RETRY_LIMIT must be a non-negative integer")
    return Settings(
        default_provider="yfinance",
        massive_available=False,
        market_data_cache_path=market_data_cache_path,
        source_cache_path=source_cache_path,
        provider_ids=("yfinance",),
        provider_priorities=(),
        retry_limit=retry_limit,
        snapshot_dir=os.getenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", ".data/snapshots"),
        stock_membership_catalog=os.getenv("STOCK_MEMBERSHIP_CATALOG", ""),
        fundamental_display_approval=os.getenv("FUNDAMENTAL_DISPLAY_APPROVAL", ""),
        experimental_universe_catalog=os.getenv(
            "EXPERIMENTAL_UNIVERSE_CATALOG", ".data/experimental-us-industry-catalog.json"
        ),
    )
