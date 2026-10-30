import pytest

from market_leadership.config import load_settings


def test_runtime_provider_is_always_yfinance(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "massive")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "fixture,massive")
    monkeypatch.setenv("MASSIVE_API_KEY", "test-key")

    settings = load_settings()

    assert settings.default_provider == "yfinance"
    assert settings.provider_ids == ("yfinance",)
    assert settings.provider_priorities == ()
    assert settings.massive_available is False


def test_market_data_cache_path_can_be_configured(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_CACHE_PATH", "/tmp/market-cache")

    settings = load_settings()

    assert settings.market_data_cache_path == "/tmp/market-cache"
    assert settings.source_cache_path == "/tmp/market-cache"


def test_source_cache_path_can_override_legacy_cache_path(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_CACHE_PATH", "/tmp/legacy-cache")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", "/tmp/source-cache")

    assert load_settings().source_cache_path == "/tmp/source-cache"


def test_retry_limit_remains_configurable(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_RETRY_LIMIT", "3")

    settings = load_settings()

    assert settings.retry_limit == 3


@pytest.mark.parametrize(
    ("name", "value"),
    [
    ("MARKET_DATA_RETRY_LIMIT", "-1"),
    ],
)
def test_invalid_provider_configuration_fails_explicitly(
    monkeypatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError):
        load_settings()
