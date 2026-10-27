from market_leadership.config import load_settings


def test_massive_key_does_not_implicitly_change_provider(monkeypatch) -> None:
    monkeypatch.delenv("MARKET_DATA_PROVIDER", raising=False)
    monkeypatch.setenv("MASSIVE_API_KEY", "test-key")

    settings = load_settings()

    assert settings.default_provider == "yfinance"
    assert settings.massive_available is True


def test_explicit_massive_provider_is_respected(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "massive")
    monkeypatch.setenv("MASSIVE_API_KEY", "test-key")

    settings = load_settings()

    assert settings.default_provider == "massive"


def test_market_data_cache_path_can_be_configured(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_CACHE_PATH", "/tmp/market-cache")

    settings = load_settings()

    assert settings.market_data_cache_path == "/tmp/market-cache"
