from datetime import date

import pytest

from market_data.domain.fundamentals import FundamentalRequest
from market_leadership import bootstrap
from market_leadership.application.ports import (
    DataPointRequest,
    ProviderCandidate,
    ProviderCapability,
    SelectionReason,
    select_provider,
)
from market_leadership.config import Settings
from market_leadership.infrastructure.provider_catalog import ConfiguredProviderCatalog
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider
from tests.support.fixture_provider import FixtureProvider


@pytest.mark.parametrize("factory", [bootstrap.build_provider, bootstrap.build_request_provider])
def test_runtime_factories_reject_synthetic_provider_without_writing_cache(
    factory, tmp_path
) -> None:
    with pytest.raises(ValueError, match="Unknown market data provider: fixture"):
        factory("fixture", str(tmp_path / "cache"))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("refresh", [False, True])
def test_runtime_fundamentals_reject_synthetic_evidence_before_cache_or_network(
    refresh, monkeypatch
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("Synthetic requests must not access runtime caches or providers")

    monkeypatch.setattr(bootstrap, "load_fundamental_bundle", forbidden)
    monkeypatch.setattr(bootstrap, "refresh_fundamental_bundle", forbidden)
    with pytest.raises(ValueError, match="synthetic evidence is test-only"):
        bootstrap.load_selected_fundamentals(
            FundamentalRequest("SYN-A", provider_id="fixture"), refresh=refresh
        )


def _capability() -> ProviderCapability:
    return ProviderCapability(
        data_point="daily_history",
        markets=frozenset({"US"}),
        frequencies=frozenset({"1d"}),
        currencies=frozenset({"USD"}),
        return_bases=frozenset({"adjusted"}),
    )


def _request() -> DataPointRequest:
    return DataPointRequest(
        data_point="daily_history",
        market_id="US",
        identifiers=("SPY",),
        frequency="1d",
        start=date(2026, 1, 1),
        end=date(2026, 10, 23),
        currency="USD",
        return_basis="adjusted",
    )


def test_catalog_returns_every_matching_provider_in_deterministic_order() -> None:
    first = FixtureProvider()
    second = type("SecondProvider", (), {"provider_id": "second"})()
    catalog = ConfiguredProviderCatalog(
        (first, second),
        {"fixture": (_capability(),), "second": (_capability(),)},
        {"fixture": 2, "second": 1},
    )

    candidates = catalog.discover(_request())

    assert [candidate.provider_id for candidate in candidates] == ["second", "fixture"]


def test_catalog_filters_by_each_requested_capability() -> None:
    provider = FixtureProvider()
    catalog = ConfiguredProviderCatalog(
        (provider,),
        {"fixture": (_capability(),)},
        {},
    )

    request = _request()
    unsupported = DataPointRequest(
        data_point=request.data_point,
        market_id="CA",
        identifiers=request.identifiers,
        frequency=request.frequency,
        start=request.start,
        end=request.end,
        currency="CAD",
        return_basis=request.return_basis,
    )

    assert catalog.discover(unsupported) == ()


def test_provider_selection_uses_schema_then_coverage_priority_and_id() -> None:
    capability = _capability()
    providers = []
    for provider_id, compatible, coverage, priority in (
        ("z-provider", False, 100, 1),
        ("b-provider", True, 50, 5),
        ("a-provider", True, 50, 2),
    ):
        provider = FixtureProvider()
        provider.provider_id = provider_id
        providers.append(
            ProviderCandidate(
                provider_id,
                provider,
                capability,
                priority,
                canonical_schema_compatible=compatible,
                coverage_days=coverage,
            )
        )

    selected = select_provider(tuple(providers))

    assert selected.selected.provider_id == "a-provider"
    assert [candidate.provider_id for candidate in selected.alternatives] == [
        "b-provider",
        "z-provider",
    ]
    assert selected.reason is SelectionReason.CONFIGURED_PRIORITY


def test_bootstrap_catalog_discovers_only_configured_direct_providers(
    monkeypatch, tmp_path
) -> None:
    providers = {
        provider_id: FixtureProvider() for provider_id in ("massive", "yfinance", "fixture")
    }
    for provider_id, provider in providers.items():
        provider.provider_id = provider_id
    factory_calls: list[tuple[str, int]] = []

    def build_adapter(provider_id: str, retry_limit: int) -> FixtureProvider:
        factory_calls.append((provider_id, retry_limit))
        return providers[provider_id]

    monkeypatch.setattr(bootstrap, "_build_provider_adapter", build_adapter)
    settings = Settings(
        default_provider="massive",
        massive_available=True,
        market_data_cache_path=str(tmp_path),
        source_cache_path=str(tmp_path),
        provider_ids=("massive", "yfinance"),
        provider_priorities=(("massive", 2), ("yfinance", 1)),
        retry_limit=4,
    )

    candidates = bootstrap.build_market_data_catalog(settings).discover(_request())

    assert [candidate.provider_id for candidate in candidates] == ["yfinance", "massive"]
    assert {candidate.provider_id for candidate in candidates} == {"massive", "yfinance"}
    assert all(candidate.capability.data_point == "daily_history" for candidate in candidates)
    assert factory_calls == [("massive", 4), ("yfinance", 4)]


def test_bootstrap_catalog_exposes_only_supported_daily_history_capabilities(
    monkeypatch, tmp_path
) -> None:
    provider = FixtureProvider()
    provider.provider_id = "yfinance"
    monkeypatch.setattr(
        bootstrap, "_build_provider_adapter", lambda provider_id, retry_limit: provider
    )
    settings = Settings(
        default_provider="yfinance",
        massive_available=False,
        market_data_cache_path=str(tmp_path),
        source_cache_path=str(tmp_path),
        provider_ids=("yfinance",),
        provider_priorities=(),
        retry_limit=2,
    )
    catalog = bootstrap.build_market_data_catalog(settings)
    request = _request()
    unsupported = DataPointRequest(
        data_point="fundamentals",
        market_id=request.market_id,
        identifiers=request.identifiers,
        frequency=request.frequency,
        start=request.start,
        end=request.end,
        currency=request.currency,
        return_basis=request.return_basis,
    )

    assert len(catalog.discover(request)) == 1
    assert catalog.discover(unsupported) == ()


def test_bootstrap_uses_yfinance_declared_capabilities(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(YFinanceProvider, "capabilities", staticmethod(lambda: ()))
    settings = Settings(
        default_provider="yfinance",
        massive_available=False,
        market_data_cache_path=str(tmp_path),
        source_cache_path=str(tmp_path),
        provider_ids=("yfinance",),
        provider_priorities=(),
        retry_limit=2,
    )

    assert bootstrap.build_market_data_catalog(settings).discover(_request()) == ()
