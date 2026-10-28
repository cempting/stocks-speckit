import json
from dataclasses import replace
from datetime import date

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from market_leadership.application.ports import (
    DataPointRequest,
    ProviderCandidate,
    ProviderCapability,
    SelectionReason,
    select_provider,
)
from market_leadership.application.request_market_data import (
    RequestedDailyHistoryProvider,
    RequestedMarketData,
    RequestMarketData,
)
from market_leadership.infrastructure.provider_catalog import ConfiguredProviderCatalog


class StubProvider:
    def __init__(
        self,
        provider_id: str,
        result: Exception | None = None,
        history_dates: tuple[date, ...] = (date(2026, 10, 23),),
    ) -> None:
        self.provider_id = provider_id
        self.result = result
        self.history_dates = history_dates
        self.calls = 0
        self.ends: list[date] = []

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del start, force
        self.ends.append(end)
        self.calls += 1
        if self.result is not None:
            raise self.result
        as_of = self.history_dates[min(self.calls - 1, len(self.history_dates) - 1)]
        return {
            symbol: pd.DataFrame(
                {"close": [100.0], "volume": [1_000.0]},
                index=pd.to_datetime([as_of]),
            )
            for symbol in symbols
        }


def _request() -> DataPointRequest:
    return DataPointRequest(
        data_point="daily_history",
        market_id="US",
        identifiers=("SPY",),
        frequency="1d",
        start=date(2026, 10, 1),
        end=date(2026, 10, 23),
        currency="USD",
        return_basis="adjusted",
    )


def _capability() -> ProviderCapability:
    return ProviderCapability(
        data_point="daily_history",
        markets=frozenset({"US"}),
        frequencies=frozenset({"1d"}),
        currencies=frozenset({"USD"}),
        return_bases=frozenset({"adjusted"}),
    )


def test_request_service_returns_matching_providers_and_reuses_fresh_cache(tmp_path) -> None:
    provider = StubProvider("preferred")
    other = StubProvider("alternative")
    catalog = ConfiguredProviderCatalog(
        (provider, other),
        {"preferred": (_capability(),), "alternative": (_capability(),)},
        {"preferred": 1, "alternative": 2},
    )
    service = RequestMarketData(catalog, tmp_path)

    first = service.execute(_request())
    second = service.execute(_request())

    assert first.selected.provider_id == "preferred"
    assert [candidate.provider_id for candidate in first.alternatives] == ["alternative"]
    assert second.data["SPY"].iloc[-1]["close"] == 100.0
    assert provider.calls == 1
    assert other.calls == 0


def test_weekend_request_reuses_completed_session_cache(tmp_path) -> None:
    provider = StubProvider("preferred")
    catalog = ConfiguredProviderCatalog((provider,), {"preferred": (_capability(),)}, {})
    service = RequestMarketData(catalog, tmp_path)
    weekend_request = replace(_request(), end=date(2026, 10, 25))

    first = service.execute(weekend_request)
    second = service.execute(weekend_request)

    assert first.selected.provider_id == second.selected.provider_id == "preferred"
    assert provider.ends == [date(2026, 10, 23)]
    assert provider.calls == 1


def test_request_service_persists_selection_and_source_availability(tmp_path) -> None:
    provider = StubProvider("preferred")
    other = StubProvider("alternative")
    catalog = ConfiguredProviderCatalog(
        (provider, other),
        {"preferred": (_capability(),), "alternative": (_capability(),)},
        {"preferred": 1, "alternative": 2},
    )

    RequestMarketData(catalog, tmp_path).execute(_request())

    manifest_path = next(tmp_path.rglob("manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["selection"] == {
        "selected_provider": "preferred",
        "alternatives": ["alternative"],
        "reason": SelectionReason.CONFIGURED_PRIORITY.value,
    }
    assert manifest["source_availability_by_symbol"] == {"SPY": "2026-10-23"}


def test_daily_history_provider_bridge_maps_request_and_preserves_force() -> None:
    expected = _request()
    selected = ProviderCandidate(
        "preferred",
        StubProvider("preferred"),
        _capability(),
        configured_priority=0,
    )

    class RequestSpy:
        received: DataPointRequest | None = None
        force: bool | None = None

        def execute(self, request: DataPointRequest, *, force: bool = False) -> RequestedMarketData:
            self.received = request
            self.force = force
            return RequestedMarketData(
                data={"SPY": pd.DataFrame()},
                selected=selected,
                alternatives=(),
                selection_reason=SelectionReason.PROVIDER_ID,
            )

    service = RequestSpy()
    provider = RequestedDailyHistoryProvider("preferred", service)
    result = provider.fetch_daily_history(
        expected.identifiers,
        start=expected.start,
        end=expected.end,
        force=True,
    )

    assert provider.provider_id == "preferred"
    assert service.received == expected
    assert service.force is True
    assert tuple(result) == ("SPY",)
    assert_frame_equal(result["SPY"], pd.DataFrame())


def test_provider_selection_is_deterministic_by_schema_coverage_priority_then_id() -> None:
    capability = _capability()
    providers = {
        provider_id: StubProvider(provider_id)
        for provider_id in ("massive", "coverage", "priority", "z-id", "a-id")
    }
    candidates = (
        ProviderCandidate(
            "massive",
            providers["massive"],
            capability,
            configured_priority=-10,
            canonical_schema_compatible=False,
            coverage_days=10_000,
        ),
        ProviderCandidate(
            "coverage",
            providers["coverage"],
            capability,
            configured_priority=-10,
            coverage_days=50,
        ),
        ProviderCandidate(
            "priority",
            providers["priority"],
            capability,
            configured_priority=5,
            coverage_days=120,
        ),
        ProviderCandidate(
            "z-id",
            providers["z-id"],
            capability,
            configured_priority=1,
            coverage_days=120,
        ),
        ProviderCandidate(
            "a-id",
            providers["a-id"],
            capability,
            configured_priority=1,
            coverage_days=120,
        ),
    )

    selected = select_provider(candidates)
    reordered = select_provider(tuple(reversed(candidates)))

    assert selected.selected.provider_id == "a-id"
    assert reordered.selected.provider_id == "a-id"
    assert selected.reason is SelectionReason.PROVIDER_ID
    assert [candidate.provider_id for candidate in selected.alternatives] == [
        "z-id",
        "priority",
        "coverage",
        "massive",
    ]


def test_request_service_exposes_selection_reason_and_all_alternatives(tmp_path) -> None:
    providers = {
        "massive": StubProvider("massive"),
        "yfinance": StubProvider("yfinance"),
    }
    candidates = (
        ProviderCandidate(
            "yfinance",
            providers["yfinance"],
            _capability(),
            configured_priority=20,
            coverage_days=10,
        ),
        ProviderCandidate(
            "massive",
            providers["massive"],
            _capability(),
            configured_priority=1,
            coverage_days=10,
        ),
    )

    class Catalog:
        def discover(self, request: DataPointRequest) -> tuple[ProviderCandidate, ...]:
            assert request == _request()
            return candidates

    result = RequestMarketData(Catalog(), tmp_path).execute(_request())

    assert result.selected.provider_id == "massive"
    assert [candidate.provider_id for candidate in result.alternatives] == ["yfinance"]
    assert result.selection_reason is SelectionReason.CONFIGURED_PRIORITY
    assert providers["massive"].calls == 1
    assert providers["yfinance"].calls == 0


@pytest.mark.parametrize(
    ("include_massive", "massive_supports_request", "expected_provider"),
    [
        (False, True, "yfinance"),
        (True, False, "yfinance"),
        (True, True, "massive"),
    ],
)
def test_massive_is_selected_only_when_configured_and_capable(
    tmp_path,
    include_massive: bool,
    massive_supports_request: bool,
    expected_provider: str,
) -> None:
    yfinance = StubProvider("yfinance")
    providers = [yfinance]
    capabilities = {"yfinance": (_capability(),)}
    priorities = {"yfinance": 5}
    if include_massive:
        massive = StubProvider("massive")
        providers.insert(0, massive)
        capabilities["massive"] = (
            _capability()
            if massive_supports_request
            else ProviderCapability(
                data_point="daily_history",
                markets=frozenset({"CA"}),
                frequencies=frozenset({"1d"}),
                currencies=frozenset({"USD"}),
                return_bases=frozenset({"adjusted"}),
            ),
        )
        priorities["massive"] = 1
    catalog = ConfiguredProviderCatalog(providers, capabilities, priorities)

    result = RequestMarketData(catalog, tmp_path).execute(_request())

    assert result.selected.provider_id == expected_provider
    if expected_provider == "massive":
        assert providers[0].calls == 1
        assert yfinance.calls == 0
    else:
        assert yfinance.calls == 1
        assert all(provider.calls == 0 for provider in providers if provider is not yfinance)


def test_undercovered_entry_refreshes_only_the_selected_provider_once(tmp_path) -> None:
    provider = StubProvider(
        "preferred",
        history_dates=(date(2026, 10, 22), date(2026, 10, 23)),
    )
    other = StubProvider("alternative")
    catalog = ConfiguredProviderCatalog(
        (provider, other),
        {"preferred": (_capability(),), "alternative": (_capability(),)},
        {"preferred": 1, "alternative": 2},
    )
    service = RequestMarketData(catalog, tmp_path)

    service.execute(_request())
    refreshed = service.execute(_request())

    assert refreshed.data["SPY"].index[-1].date() == date(2026, 10, 23)
    assert provider.calls == 2
    assert other.calls == 0


def test_request_service_force_refreshes_only_the_selected_provider(tmp_path) -> None:
    provider = StubProvider("preferred")
    other = StubProvider("alternative")
    catalog = ConfiguredProviderCatalog(
        (provider, other),
        {"preferred": (_capability(),), "alternative": (_capability(),)},
        {"preferred": 1, "alternative": 2},
    )
    service = RequestMarketData(catalog, tmp_path)

    service.execute(_request())
    service.execute(_request(), force=True)

    assert provider.calls == 2
    assert other.calls == 0


def test_request_service_does_not_switch_providers_after_failure(tmp_path) -> None:
    provider = StubProvider("preferred", RuntimeError("request failed"))
    other = StubProvider("alternative")
    catalog = ConfiguredProviderCatalog(
        (provider, other),
        {"preferred": (_capability(),), "alternative": (_capability(),)},
        {"preferred": 1, "alternative": 2},
    )

    with pytest.raises(RuntimeError, match="request failed"):
        RequestMarketData(catalog, tmp_path).execute(_request())

    assert provider.calls == 1
    assert other.calls == 0


def test_request_service_failed_forced_refresh_preserves_cache_and_does_not_publish(
    tmp_path,
) -> None:
    provider = StubProvider("preferred")
    other = StubProvider("alternative")
    catalog = ConfiguredProviderCatalog(
        (provider, other),
        {"preferred": (_capability(),), "alternative": (_capability(),)},
        {"preferred": 1, "alternative": 2},
    )
    service = RequestMarketData(catalog, tmp_path)
    service.execute(_request())
    current_path = next(tmp_path.rglob("CURRENT"))
    generation = current_path.read_text(encoding="ascii")
    provider.result = RuntimeError("refresh failed")

    with pytest.raises(RuntimeError, match="refresh failed"):
        service.execute(_request(), force=True)
    cached = service.execute(_request())

    assert current_path.read_text(encoding="ascii") == generation
    assert cached.data["SPY"].iloc[-1]["close"] == 100.0
    assert provider.calls == 2
    assert other.calls == 0
    assert not list(tmp_path.rglob(".publishing-*"))
