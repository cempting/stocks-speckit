import pytest

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
    assert settings.source_cache_path == "/tmp/market-cache"


def test_source_cache_path_can_override_legacy_cache_path(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_CACHE_PATH", "/tmp/legacy-cache")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", "/tmp/source-cache")

    assert load_settings().source_cache_path == "/tmp/source-cache"


def test_provider_configuration_is_ordered_and_keeps_secret_as_environment_reference(
    monkeypatch,
) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "massive,yfinance")
    monkeypatch.setenv("MARKET_DATA_PROVIDER_PRIORITIES", "massive:1,yfinance:2")
    monkeypatch.setenv("MARKET_DATA_RETRY_LIMIT", "3")
    monkeypatch.setenv("MASSIVE_API_KEY", "do-not-copy-this-value")

    settings = load_settings()

    assert settings.provider_ids == ("massive", "yfinance")
    assert settings.provider_priorities == (("massive", 1), ("yfinance", 2))
    assert settings.retry_limit == 3
    assert settings.massive_api_key_reference == "MASSIVE_API_KEY"
    assert "do-not-copy-this-value" not in repr(settings)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MARKET_DATA_PROVIDERS", "fixture,fixture"),
        ("MARKET_DATA_PROVIDER_PRIORITIES", "massive:high"),
        ("MARKET_DATA_RETRY_LIMIT", "-1"),
    ],
)
def test_invalid_provider_configuration_fails_explicitly(
    monkeypatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError):
        load_settings()
