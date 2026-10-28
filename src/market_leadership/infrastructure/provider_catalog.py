from collections.abc import Mapping, Sequence

from market_leadership.application.ports import (
    DataPointRequest,
    MarketDataProvider,
    MarketDataProviderCatalog,
    ProviderCandidate,
    ProviderCapability,
)


class ConfiguredProviderCatalog(MarketDataProviderCatalog):
    def __init__(
        self,
        providers: Sequence[MarketDataProvider],
        capabilities: Mapping[str, tuple[ProviderCapability, ...]],
        priorities: Mapping[str, int],
    ) -> None:
        provider_ids = [provider.provider_id for provider in providers]
        if len(set(provider_ids)) != len(provider_ids):
            raise ValueError("provider IDs must be unique")
        if set(provider_ids) != set(capabilities):
            raise ValueError("each configured provider must declare capabilities")
        self._providers = {provider.provider_id: provider for provider in providers}
        self._capabilities = dict(capabilities)
        self._priorities = dict(priorities)

    def discover(self, request: DataPointRequest) -> tuple[ProviderCandidate, ...]:
        candidates = [
            ProviderCandidate(
                provider_id=provider_id,
                provider=provider,
                capability=capability,
                configured_priority=self._priorities.get(provider_id, 0),
            )
            for provider_id, provider in self._providers.items()
            for capability in self._capabilities[provider_id]
            if capability.covers(request)
        ]
        return tuple(
            sorted(
                candidates,
                key=lambda candidate: (candidate.configured_priority, candidate.provider_id),
            )
        )
