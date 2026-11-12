from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogSnapshot
from market_data.company_evidence import CompanyEvidenceFiles
from market_data.domain.company_evidence import (
    CompanyEvidenceRequest,
    CompanyEvidenceSnapshot,
    SourceAssessment,
    company_association_fingerprint,
)
from market_data.domain.fundamentals import (
    FundamentalBundle,
    FundamentalRequest,
)
from market_leadership.application.load_company_evidence import (
    CompanyEvidenceLoadResult,
    FinancialLoader,
    load_company_evidence,
)
from market_leadership.application.load_stock_history import (
    StockHistoryBatch,
    StockHistorySeries,
)
from market_leadership.application.ports import (
    MarketDataProvider,
    MarketDataProviderCatalog,
    ProviderCapability,
)
from market_leadership.application.request_market_data import (
    RequestedDailyHistoryProvider,
    RequestMarketData,
)
from market_leadership.config import Settings, load_settings
from market_leadership.infrastructure.market_data_cache import CachedMarketDataProvider
from market_leadership.infrastructure.massive_provider import MassiveProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.provider_catalog import ConfiguredProviderCatalog
from market_leadership.infrastructure.yfinance_fundamentals import (
    TickerFactory,
    ticker_factory,
)
from market_leadership.infrastructure.yfinance_provider import YFinanceProvider
from market_leadership.ui.cache import (
    load_cached_company_snapshot,
    load_company_financial_bundle,
    load_fundamental_bundle,
    refresh_fundamental_bundle,
)
from market_leadership.ui.navigation import WorkflowSpec, validate_workflows

_DAILY_HISTORY_CAPABILITY = ProviderCapability(
    data_point="daily_history",
    markets=frozenset({"US"}),
    frequencies=frozenset({"1d"}),
    currencies=frozenset({"USD"}),
    return_bases=frozenset({"adjusted"}),
)


def load_selected_fundamentals(
    request: FundamentalRequest, *, refresh: bool = False
) -> FundamentalBundle:
    if request.provider_id != "yfinance":
        raise ValueError(
            "Runtime fundamentals require yfinance; synthetic evidence is test-only"
        )
    if refresh:
        return refresh_fundamental_bundle(request)
    return load_fundamental_bundle(request)


def load_selected_company_evidence(
    request: CompanyEvidenceRequest,
    catalog: CatalogSnapshot,
    *,
    refresh: bool = False,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    _factory: TickerFactory = ticker_factory,
) -> CompanyEvidenceLoadResult:
    settings = load_settings()
    store = CompanyEvidenceFiles(Path(settings.company_evidence_root))
    current_binding = store.load_association(request.association.association_id)
    if company_association_fingerprint(current_binding, request.scope) != (
        request.binding_fingerprint
    ):
        raise ValueError("The reviewed issuer binding changed; reload before using cached evidence")
    assessments: tuple[SourceAssessment, ...] = tuple(
        store.load_source_assessment(source_id) for source_id in request.source_ids
    )
    if request.scope == "research" and (refresh or request.refresh):
        raise ValueError("Research refresh is unavailable; this feature only reuses stored claims")

    financial_loader: FinancialLoader | None = None
    if request.scope == "financial" and request.mode == "current":
        def load_financial_bundle(
            fundamental_request: FundamentalRequest,
        ) -> FundamentalBundle:
            if fundamental_request.provider_id != "yfinance":
                raise ValueError(
                    "Runtime fundamentals require yfinance; synthetic evidence is test-only"
                )
            return load_company_financial_bundle(
                fundamental_request,
                binding_fingerprint=request.binding_fingerprint,
                assessment_fingerprint=request.assessment_fingerprint,
                source_ids=request.source_ids,
                as_of=request.as_of,
                mode=request.mode,
                normalization_revision=request.normalization_revision,
                schema_revision=request.schema_revision,
                refresh=refresh or request.refresh,
                _factory=_factory,
                now=clock(),
            )

        financial_loader = load_financial_bundle

    archive_snapshot = None
    archive_snapshots: tuple[CompanyEvidenceSnapshot, ...] = ()
    financial_snapshots: tuple[CompanyEvidenceSnapshot, ...] | None = None
    if request.scope == "research":
        permission_date = clock().date()
        archive_permitted = any(
            assessment.role == "disclosure"
            and assessment.source_id in request.source_ids
            and assessment.fingerprint == request.assessment_fingerprint
            and assessment.permits("display", permission_date, role="disclosure")
            and assessment.permits(
                "normalized_retention", permission_date, role="disclosure"
            )
            for assessment in assessments
        )
        if archive_permitted:
            archive_snapshots = tuple(
                load_cached_company_snapshot(
                    settings.company_evidence_root,
                    relative_path,
                    revision,
                )
                for _, relative_path, revision in store.list_latest_snapshot_references(
                    "research"
                )
            )
    elif request.scope == "financial":
        permission_date = clock().date()
        financial_permission_granted = any(
            assessment.role == "financial"
            and assessment.source_id in request.source_ids
            and assessment.fingerprint == request.assessment_fingerprint
            and assessment.permits("display", permission_date, role="financial")
            and assessment.permits(
                "normalized_retention", permission_date, role="financial"
            )
            for assessment in assessments
        )
        archive_permitted = request.mode == "historical" and financial_permission_granted
        if financial_permission_granted:
            financial_snapshots = tuple(
                load_cached_company_snapshot(
                    settings.company_evidence_root,
                    relative_path,
                    revision,
                )
                for _, relative_path, revision in store.list_latest_snapshot_references(
                    "financial"
                )
            )
    else:
        archive_permitted = False
    if archive_permitted:
        if request.scope == "financial":
            reference = store.latest_snapshot_reference(
                request.association.association_id, request.scope
            )
            if reference is not None:
                relative_path, revision = reference
                archive_snapshot = load_cached_company_snapshot(
                    settings.company_evidence_root, relative_path, revision
                )
    return load_company_evidence(
        request,
        catalog=catalog,
        assessments=assessments,
        store=store,
        clock=clock,
        financial_loader=financial_loader,
        archive_snapshot=archive_snapshot,
        archive_snapshots=archive_snapshots,
        financial_snapshots=financial_snapshots,
        retry_limit=settings.retry_limit,
    )


def load_selected_stock_history(
    catalog: CatalogSnapshot,
    *,
    region_id: str,
    instrument_id: str,
    listing_id: str,
    as_of: date,
    require_primary: bool,
    lookback_days: int = 550,
    refresh: bool = False,
) -> StockHistoryBatch:
    settings = load_settings()
    store = CompanyEvidenceFiles(Path(settings.company_evidence_root))
    association = store.find_active_association(
        instrument_id=instrument_id,
        listing_id=listing_id,
        provider_id="yfinance",
        as_of=as_of,
    )
    if association is None or association.region_id != region_id:
        listing = next(
            (
                item
                for item in (*catalog.listings, *catalog.regional_listings)
                if item.instrument_id == instrument_id and item.listing_id == listing_id
            ),
            None,
        )
        return StockHistoryBatch(
            "yfinance",
            as_of,
            (
                StockHistorySeries(
                    symbol=listing.provider_symbol if listing and listing.provider_symbol else "",
                    history=pd.DataFrame(columns=["close", "volume"], dtype="float64"),
                    observed_on=None,
                    state="unavailable",
                    reason="No dated reviewed issuer-continuity binding is available.",
                    unverifiable_intervals=(
                        (as_of - timedelta(days=lookback_days), as_of),
                    ),
                ),
            ),
        )
    from market_leadership.ui.cache import load_selected_listing_history

    return load_selected_listing_history(
        settings.source_cache_path,
        catalog,
        association,
        as_of,
        retry_limit=settings.retry_limit,
        lookback_days=lookback_days,
        require_primary=require_primary,
        force_refresh=refresh,
    )


def build_workflow_registry(
    discovery_render: Callable[[], None],
    industry_discovery_render: Callable[[], None],
) -> tuple[WorkflowSpec, ...]:
    return validate_workflows(
        (
            WorkflowSpec(
                key="discovery",
                title="Discovery",
                url_path="discovery",
                icon=":material/monitoring:",
                render=discovery_render,
                default=True,
            ),
            WorkflowSpec(
                key="industry-discovery",
                title="Industry Discovery",
                url_path="industry-discovery",
                icon=":material/schema:",
                render=industry_discovery_render,
                default=False,
            ),
        )
    )


def _build_provider_adapter(provider_id: str, retry_limit: int) -> MarketDataProvider:
    if provider_id == "massive":
        return MassiveProvider(retry_limit=retry_limit)
    if provider_id == "yfinance":
        return YFinanceProvider(retry_limit=retry_limit)
    raise ValueError(f"Unknown market data provider: {provider_id}")


def build_provider(
    provider_id: str,
    cache_path: str = ".cache/market-data",
    *,
    retry_limit: int = 2,
) -> MarketDataProvider:
    provider = _build_provider_adapter(provider_id, retry_limit)
    return CachedMarketDataProvider(provider, cache_path)


def _provider_capabilities(provider: MarketDataProvider) -> tuple[ProviderCapability, ...]:
    if isinstance(provider, YFinanceProvider):
        return provider.capabilities()
    return (_DAILY_HISTORY_CAPABILITY,)


def build_market_data_catalog(settings: Settings) -> MarketDataProviderCatalog:
    providers = tuple(
        _build_provider_adapter(provider_id, settings.retry_limit)
        for provider_id in settings.provider_ids
    )
    capabilities = {
        provider.provider_id: _provider_capabilities(provider) for provider in providers
    }
    return ConfiguredProviderCatalog(
        providers,
        capabilities,
        dict(settings.provider_priorities),
    )


def build_market_data_request(settings: Settings) -> RequestMarketData:
    return RequestMarketData(
        build_market_data_catalog(settings),
        settings.source_cache_path,
    )


def build_snapshot_repository(settings: Settings) -> ParquetSnapshotRepository:
    return ParquetSnapshotRepository(settings.snapshot_dir)


def build_request_provider(
    provider_id: str,
    source_cache_path: str,
    *,
    retry_limit: int = 2,
) -> MarketDataProvider:
    provider = _build_provider_adapter(provider_id, retry_limit)
    catalog = ConfiguredProviderCatalog(
        (provider,),
        {provider_id: _provider_capabilities(provider)},
        {},
    )
    return RequestedDailyHistoryProvider(
        provider_id,
        RequestMarketData(catalog, source_cache_path),
    )
