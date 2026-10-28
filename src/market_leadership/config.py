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


def _items(environment_key: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(environment_key, "").split(",") if item.strip())


def _priorities() -> tuple[tuple[str, int], ...]:
    priorities: list[tuple[str, int]] = []
    for entry in _items("MARKET_DATA_PROVIDER_PRIORITIES"):
        provider_id, separator, priority = entry.partition(":")
        if not separator:
            raise ValueError("MARKET_DATA_PROVIDER_PRIORITIES entries must use provider_id:integer")
        try:
            parsed_priority = int(priority)
        except ValueError as error:
            raise ValueError(
                "MARKET_DATA_PROVIDER_PRIORITIES priorities must be integers"
            ) from error
        priorities.append((provider_id, parsed_priority))
    if len({provider_id for provider_id, _ in priorities}) != len(priorities):
        raise ValueError("provider priority IDs must be unique")
    return tuple(priorities)


def load_settings() -> Settings:
    load_dotenv(override=False)
    configured = os.getenv("MARKET_DATA_PROVIDER", "").strip()
    massive_available = bool(os.getenv("MASSIVE_API_KEY"))
    default_provider = configured or "yfinance"
    market_data_cache_path = os.getenv("MARKET_DATA_CACHE_PATH", ".cache/market-data")
    source_cache_path = os.getenv("MARKET_DATA_SOURCE_CACHE_PATH", market_data_cache_path)
    provider_ids = _items("MARKET_DATA_PROVIDERS") or (default_provider,)
    if len(set(provider_ids)) != len(provider_ids):
        raise ValueError("MARKET_DATA_PROVIDERS must not contain duplicates")
    try:
        retry_limit = int(os.getenv("MARKET_DATA_RETRY_LIMIT", "2"))
    except ValueError as error:
        raise ValueError("MARKET_DATA_RETRY_LIMIT must be a non-negative integer") from error
    if retry_limit < 0:
        raise ValueError("MARKET_DATA_RETRY_LIMIT must be a non-negative integer")
    return Settings(
        default_provider=default_provider,
        massive_available=massive_available,
        market_data_cache_path=market_data_cache_path,
        source_cache_path=source_cache_path,
        provider_ids=provider_ids,
        provider_priorities=_priorities(),
        retry_limit=retry_limit,
        snapshot_dir=os.getenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", ".data/snapshots"),
    )
