import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    default_provider: str
    massive_available: bool


def load_settings() -> Settings:
    load_dotenv(override=False)
    configured = os.getenv("MARKET_DATA_PROVIDER")
    massive_available = bool(os.getenv("MASSIVE_API_KEY"))
    default_provider = configured or "yfinance"
    return Settings(default_provider=default_provider, massive_available=massive_available)
