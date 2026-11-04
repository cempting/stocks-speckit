from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import load_release
from market_data.company_evidence import CompanyEvidenceFiles
from market_data.domain.company_evidence import (
    CompanyAssociation,
    company_association_id,
)
from market_data.domain.fundamentals import (
    FundamentalBundle,
    FundamentalRequest,
)
from market_data.domain.stock_selection import MembershipEntry
from market_data_tools.legacy.region_database import (
    ListingRecord,
    RegionDatabase,
    StockMembershipRecord,
)
from market_data_tools.legacy.stock_membership import verified_primary_provider_symbols
from market_data_tools.legacy.universe_import import import_reviewed_file
from market_leadership.application.load_stock_history import (
    load_selected_listing_history,
    load_stock_history,
)
from market_leadership.application.score_industry import score_industry
from market_leadership.ui.cache import load_member_history
from tests.membership_helpers import build_v2_release, membership_fixture
from tests.support.fixture_provider import FixtureProvider


class RecordingProvider(FixtureProvider):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[tuple[str, ...]] = []

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        self.requests.append(symbols)
        return super().fetch_daily_history(symbols, start=start, end=end, force=force)


class MixedTickerReuseProvider:
    provider_id = "yfinance"

    def __init__(self) -> None:
        self.requests: list[tuple[tuple[str, ...], date, date]] = []

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        del force
        self.requests.append((symbols, start, end))
        return {
            "FIXTURE": pd.DataFrame(
                {
                    "close": [10.0, 20.0, 21.0, 30.0],
                    "volume": [100.0, 200.0, 210.0, 300.0],
                },
                index=pd.DatetimeIndex(
                    ["2026-10-22", "2026-10-23", "2026-10-24", "2026-10-25"]
                ),
            )
        }


def _reviewed_continuity_association(catalog_revision: str) -> CompanyAssociation:
    effective_from = date(2026, 10, 23)
    effective_to = date(2026, 10, 24)
    return CompanyAssociation(
        association_id=company_association_id(
            instrument_id="share-class-a",
            listing_id="listing-a-primary",
            source_id="yfinance",
            effective_from=effective_from,
            effective_to=effective_to,
        ),
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        region_id="US",
        company_id=None,
        provider_id="yfinance",
        provider_symbol="FIXTURE",
        exchange="FIXTUREEX",
        trading_currency="USD",
        catalog_revision=catalog_revision,
        effective_from=effective_from,
        effective_to=effective_to,
        issuer_key="domain:issuer.example",
        cik=None,
        issuer_domain="issuer.example",
        binding_reference="reviewed-continuity-reference",
        identity_evidence=None,
        state="unresolved",
        reason="Financial profile corroboration is not required for price history",
    )


def _listing_association(
    catalog_revision: str,
    *,
    instrument_id: str,
    listing_id: str,
    provider_symbol: str,
    effective_from: date = date(2020, 1, 1),
    effective_to: date | None = None,
) -> CompanyAssociation:
    return CompanyAssociation(
        association_id=company_association_id(
            instrument_id=instrument_id,
            listing_id=listing_id,
            source_id="yfinance",
            effective_from=effective_from,
            effective_to=effective_to,
        ),
        instrument_id=instrument_id,
        listing_id=listing_id,
        region_id="US",
        company_id=None,
        provider_id="yfinance",
        provider_symbol=provider_symbol,
        exchange="FIXTUREEX",
        trading_currency="USD",
        catalog_revision=catalog_revision,
        effective_from=effective_from,
        effective_to=effective_to,
        issuer_key="domain:issuer.example",
        cik=None,
        issuer_domain="issuer.example",
        binding_reference="reviewed-continuity-reference",
        identity_evidence=None,
        state="unresolved",
        reason="Financial profile corroboration is not required for price history",
    )


def test_reviewed_placeholder_promotion_enables_only_accepted_verified_listing(
    tmp_path: Path,
) -> None:
    database = RegionDatabase(tmp_path / "universe.sqlite")
    for source_id, row in (
        ("placeholder", "stock-a,,Alpha,NASDAQ,Technology,Cloud,placeholder"),
        ("resolved", "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud,identified"),
    ):
        source = tmp_path / f"{source_id}.csv"
        source.write_text(
            "InstrumentId,Ticker,Name,Exchange,Sector,Industry,ResolutionState\n" + row + "\n"
        )
        import_reviewed_file(
            database, source, region_id="US", classification_id="TEST", source_id=source_id,
            exchange_id=None, coverage="test", approval_reference="test-only",
        )
        members = database.get_industry_members(
            "US", "TEST", "test-cloud", as_of=date(2026, 10, 30)
        )
        symbols = verified_primary_provider_symbols(members)
        if source_id == "placeholder":
            assert symbols == ()
        else:
            assert symbols == ("AAA",)
            provider = RecordingProvider()
            load_stock_history(provider, symbols, as_of=date(2026, 10, 30))
            assert provider.requests == [("AAA",)]


def test_member_history_requests_only_active_selected_industry_members():
    provider = RecordingProvider()
    members = ("AAA", "BBB")

    result = load_stock_history(provider, members, as_of=date(2026, 10, 23))

    assert provider.requests == [members]
    assert tuple(series.symbol for series in result.series) == members
    assert all(series.state == "available" for series in result.series)
    assert all(
        series.observed_on is not None and series.observed_on <= result.requested_as_of
        for series in result.series
    )


def test_selected_history_filters_predecessor_and_successor_rows_to_reviewed_continuity(
    catalog_release: Path, tmp_path: Path
) -> None:
    fixture = membership_fixture(deep_levels=4)
    expired_memberships = replace(
        fixture,
        stocks=tuple(
            {**row, "MembershipEffectiveTo": "2024-12-31"}
            if row["RowKind"] == "membership"
            else row
            for row in fixture.stocks
        ),
    )
    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        expired_memberships,
    )
    catalog = load_release(manifest)
    as_of = date(2026, 10, 24)
    scope = catalog.scope_on("US", as_of)
    assert catalog.members(scope, "industry-a", as_of) == ()
    association = _reviewed_continuity_association(catalog.catalog_revision)
    provider = MixedTickerReuseProvider()

    result = load_selected_listing_history(
        provider,
        catalog,
        association,
        as_of=date(2026, 10, 24),
        lookback_days=10,
    )

    series = result.series[0]
    assert provider.requests == [
        (("FIXTURE",), date(2026, 10, 23), date(2026, 10, 24))
    ]
    assert list(series.history["close"]) == [20.0, 21.0]
    assert list(series.history["volume"]) == [200.0, 210.0]
    assert series.observed_on == date(2026, 10, 24)
    assert series.unverifiable_intervals == (
        (date(2026, 10, 14), date(2026, 10, 22)),
    )


def test_selected_history_rechecks_stored_binding_and_targets_cache_refresh(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_leadership.bootstrap import load_selected_stock_history

    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    catalog = load_release(manifest)
    association = _reviewed_continuity_association(catalog.catalog_revision)
    root = tmp_path / "company-evidence"
    monkeypatch.setenv("COMPANY_EVIDENCE_ROOT", str(root))
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path / "market-cache"))
    store = CompanyEvidenceFiles(root)
    first_revision = store.save_association(association, expected_revision=None)
    provider = MixedTickerReuseProvider()
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *_args, **_kwargs: provider,
    )
    arguments = {
        "catalog": catalog,
        "region_id": "US",
        "instrument_id": "share-class-a",
        "listing_id": "listing-a-primary",
        "as_of": date(2026, 10, 24),
        "require_primary": True,
    }

    first = load_selected_stock_history(**arguments)
    again = load_selected_stock_history(**arguments)
    assert first.series[0].history.equals(again.series[0].history)
    assert len(provider.requests) == 1

    changed_binding = replace(association, binding_reference="updated-reviewed-reference")
    store.save_association(changed_binding, expected_revision=first_revision)
    rebound = load_selected_stock_history(**arguments)
    refreshed = load_selected_stock_history(**arguments, refresh=True)
    assert rebound.series[0].history.equals(refreshed.series[0].history)
    assert len(provider.requests) == 3


def test_selected_history_keeps_share_class_listings_in_separate_cache_entries(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_leadership.ui.cache import load_selected_listing_history

    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    catalog = load_release(manifest)

    class DistinctListingProvider:
        provider_id = "yfinance"

        def __init__(self) -> None:
            self.requests: list[tuple[str, ...]] = []

        def fetch_daily_history(
            self,
            symbols: tuple[str, ...],
            *,
            start: date,
            end: date,
            force: bool = False,
        ) -> dict[str, pd.DataFrame]:
            del start, force
            self.requests.append(symbols)
            return {
                symbol: pd.DataFrame(
                    {
                        "close": [10.0 if symbol == "FIXTURE" else 20.0],
                        "volume": [100.0],
                    },
                    index=pd.DatetimeIndex([end]),
                )
                for symbol in symbols
            }

    provider = DistinctListingProvider()
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *_args, **_kwargs: provider,
    )
    source_path = str(tmp_path / "separate-listing-cache")
    as_of = date(2026, 10, 24)
    primary = _listing_association(
        catalog.catalog_revision,
        instrument_id="share-class-a",
        listing_id="listing-a-primary",
        provider_symbol="FIXTURE",
    )
    other_class = _listing_association(
        catalog.catalog_revision,
        instrument_id="share-class-b",
        listing_id="listing-b",
        provider_symbol="FIXTURE_B",
    )

    first = load_selected_listing_history(
        source_path,
        catalog,
        primary,
        as_of,
        retry_limit=1,
    )
    reused = load_selected_listing_history(
        source_path,
        catalog,
        primary,
        as_of,
        retry_limit=1,
    )
    second_class = load_selected_listing_history(
        source_path,
        catalog,
        other_class,
        as_of,
        retry_limit=1,
    )

    assert provider.requests == [("FIXTURE",), ("FIXTURE_B",)]
    assert first.series[0].history["close"].tolist() == [10.0]
    assert reused.series[0].history["close"].tolist() == [10.0]
    assert second_class.series[0].history["close"].tolist() == [20.0]


def test_selected_history_blocks_expired_nonprimary_and_unverified_listings_before_provider(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_leadership.ui.cache import load_selected_listing_history

    manifest = build_v2_release(
        catalog_release,
        tmp_path / "catalog-v2",
        membership_fixture(deep_levels=4),
    )
    catalog = load_release(manifest)
    calls: list[tuple[str, ...]] = []

    class FailIfFetched:
        provider_id = "yfinance"

        def fetch_daily_history(self, symbols: tuple[str, ...], **_kwargs):
            calls.append(symbols)
            raise AssertionError("Ineligible listings must not request history")

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *_args, **_kwargs: FailIfFetched(),
    )
    arguments = {
        "source_cache_path": str(tmp_path / "blocked-listing-cache"),
        "catalog": catalog,
        "as_of": date(2026, 10, 24),
        "retry_limit": 1,
    }
    ineligible = (
        _listing_association(
            catalog.catalog_revision,
            instrument_id="share-class-a",
            listing_id="listing-a-secondary",
            provider_symbol="FIXTURE.A2",
        ),
        _listing_association(
            catalog.catalog_revision,
            instrument_id="unverified-listing",
            listing_id="listing-unverified",
            provider_symbol="FIXTURE_UNVERIFIED",
        ),
        _listing_association(
            catalog.catalog_revision,
            instrument_id="share-class-a",
            listing_id="listing-a-primary",
            provider_symbol="FIXTURE",
            effective_to=date(2020, 12, 31),
        ),
    )

    for association in ineligible:
        result = load_selected_listing_history(association=association, **arguments)
        assert result.series[0].state == "unavailable"
    assert calls == []


def test_successful_member_history_is_cached_by_membership_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    provider = RecordingProvider()

    def build_provider(
        provider_id: str, source_cache_path: str, *, retry_limit: int
    ) -> RecordingProvider:
        del provider_id, source_cache_path, retry_limit
        return provider

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        build_provider,
    )
    source_path = str(tmp_path / "source-cache")

    first = load_member_history(
        source_path,
        ("AAA", "BBB"),
        date(2026, 10, 23),
        retry_limit=1,
    )
    second = load_member_history(
        source_path,
        ("AAA", "BBB"),
        date(2026, 10, 23),
        retry_limit=1,
    )

    assert first.provider_id == second.provider_id
    assert first.requested_as_of == second.requested_as_of
    assert [series.symbol for series in first.series] == [series.symbol for series in second.series]
    assert provider.requests == [("AAA", "BBB")]


def test_missing_member_response_is_explicit_not_a_successful_empty_row():
    class PartialProvider(RecordingProvider):
        def fetch_daily_history(
            self,
            symbols: tuple[str, ...],
            *,
            start: date,
            end: date,
            force: bool = False,
        ) -> dict[str, pd.DataFrame]:
            del symbols
            super().fetch_daily_history(("AAA",), start=start, end=end, force=force)
            return {
                "AAA": pd.DataFrame(
                    {"close": [10.0], "volume": [100.0]},
                    index=pd.DatetimeIndex(["2026-10-23"]),
                )
            }

    result = load_stock_history(
        PartialProvider(),
        ("AAA", "BBB"),
        as_of=date(2026, 10, 23),
    )

    assert result.series[0].state == "available"
    assert result.series[1].state == "unavailable"
    assert result.series[1].reason is not None


def test_provider_failure_is_not_cached_as_empty_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    calls = 0

    def fail_provider(
        provider_id: str, source_cache_path: str, *, retry_limit: int
    ) -> FixtureProvider:
        nonlocal calls
        calls += 1
        raise OSError("controlled provider failure")

    monkeypatch.setattr("market_leadership.bootstrap.build_request_provider", fail_provider)
    for _ in range(2):
        with pytest.raises(OSError, match="controlled provider failure"):
            load_member_history(
                str(tmp_path / "failed-cache"),
                ("AAA",),
                date(2026, 10, 23),
                retry_limit=1,
            )
    assert calls == 2


def test_partial_history_retries_failed_members_and_refresh_replaces_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class RecoveringProvider(RecordingProvider):
        def fetch_daily_history(
            self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False
        ) -> dict[str, pd.DataFrame]:
            self.requests.append(symbols)
            return {
                symbol: pd.DataFrame(
                    {"close": [30.0 if force else 20.0], "volume": [100.0]},
                    index=pd.DatetimeIndex(["2026-10-23"]),
                )
                for symbol in symbols
                if symbol != "BBB" or len(self.requests) > 1
            }

    provider = RecoveringProvider()
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider", lambda *args, **kwargs: provider
    )
    arguments = (str(tmp_path), ("AAA", "BBB"), date(2026, 10, 23))
    first = load_member_history(*arguments, retry_limit=1)
    second = load_member_history(*arguments, retry_limit=1)
    assert first.series[1].state == "unavailable"
    assert all(item.state == "available" for item in second.series)
    assert provider.requests == [("AAA", "BBB"), ("BBB",)]
    refreshed = load_member_history(*arguments, retry_limit=1, force_refresh=True)
    ordinary = load_member_history(*arguments, retry_limit=1)
    assert provider.requests == [("AAA", "BBB"), ("BBB",), ("AAA", "BBB")]
    assert refreshed.series[0].history["close"].iloc[-1] == 30.0
    assert ordinary.series[0].history["close"].iloc[-1] == 30.0
    assert ordinary.provider_id == provider.provider_id


def test_unavailable_history_recovers_and_failed_refresh_invalidates_only_matching_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class RecoveringProvider(RecordingProvider):
        fail = True

        def fetch_daily_history(
            self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False
        ) -> dict[str, pd.DataFrame]:
            self.requests.append(symbols)
            if self.fail:
                return {}
            return super().fetch_daily_history(symbols, start=start, end=end, force=force)

    provider = RecoveringProvider()
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider", lambda *args, **kwargs: provider
    )
    arguments = (str(tmp_path), ("AAA",), date(2026, 10, 23))
    assert load_member_history(*arguments, retry_limit=1).series[0].state == "unavailable"
    provider.fail = False
    assert load_member_history(*arguments, retry_limit=1).series[0].state == "available"
    load_member_history(str(tmp_path), ("BBB",), date(2026, 10, 23), retry_limit=1)
    provider.fail = True
    assert load_member_history(
        *arguments, retry_limit=1, force_refresh=True
    ).series[0].state == "unavailable"
    calls = len(provider.requests)
    assert load_member_history(
        str(tmp_path), ("BBB",), date(2026, 10, 23), retry_limit=1
    ).series[0].state == "available"
    assert len(provider.requests) == calls
    assert load_member_history(*arguments, retry_limit=1).series[0].state == "unavailable"
    assert len(provider.requests) > calls


@pytest.mark.parametrize("missing", ["close", "volume"])
def test_member_history_preserves_independent_series(missing: str) -> None:
    class IndependentProvider(RecordingProvider):
        def fetch_daily_history(
            self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False
        ) -> dict[str, pd.DataFrame]:
            frame = pd.DataFrame(
                {"close": [10.0, 11.0], "volume": [100.0, 110.0]},
                index=pd.date_range("2026-10-22", periods=2),
            )
            frame[missing] = float("nan")
            return {"AAA": frame}

    item = load_stock_history(
        IndependentProvider(), ("AAA",), as_of=date(2026, 10, 23)
    ).series[0]
    assert len(item.history) == 2
    available = "volume" if missing == "close" else "close"
    assert item.history[available].notna().all()
    assert item.history[missing].isna().all()
    assert (item.price_state if missing == "close" else item.volume_state) == "insufficient"
    assert (item.volume_state if missing == "close" else item.price_state) == "available"


def test_score_orchestration_loads_the_complete_active_industry_cohort():
    members = tuple(
        MembershipEntry(
            f"instrument-{index}",
            f"company-{index}",
            f"S{index}",
            f"Stock {index}",
            "NASDAQ",
            "USD",
            "TECH",
            "Information Technology",
            "CLOUD",
            "Cloud Computing",
            date(2020, 1, 1),
            None if index < 5 else date(2025, 1, 1),
        )
        for index in range(6)
    )
    loaded: list[str] = []

    def loader(request: FundamentalRequest, *, refresh: bool = False) -> FundamentalBundle:
        del refresh
        loaded.append(request.symbol)
        return FundamentalBundle(
            request.symbol,
            "yfinance",
            datetime(2026, 10, 30, tzinfo=UTC),
            "USD",
            (),
            (),
            (),
            market_cap=2_000_000_000,
            market_cap_as_of=date(2026, 10, 30),
        )

    result = score_industry(
        members,
        cutoff=date(2026, 10, 30),
        loader=loader,
    )

    assert loaded == ["S0", "S1", "S2", "S3", "S4"]
    assert result.eligible_instrument_ids == tuple(f"instrument-{index}" for index in range(5))
    assert all(stock.state == "insufficient" for stock in result.stocks)
    assert all(stock.scorecard.quality.value is None for stock in result.stocks)
    assert result.stocks[0].reason is not None
    assert "publication vintages" in result.stocks[0].reason
    assert all(stock.market_cap == 2_000_000_000 for stock in result.stocks)
    assert all(stock.market_cap_as_of == date(2026, 10, 30) for stock in result.stocks)


def test_provider_symbols_exclude_unresolved_and_nonprimary_listings():
    members = (
        StockMembershipRecord(
            "instrument-a",
            None,
            "Alpha",
            "identified",
            "classified",
            "sector-a",
            "Technology",
            "industry-a",
            "Cloud",
            date(2020, 1, 1),
            None,
            (
                ListingRecord("listing-primary", "NASDAQ", "AAA", "AAA", "USD", True, "verified"),
                ListingRecord("listing-other", "NYSE", "AAA.A", "AAA.A", "USD", False, "verified"),
            ),
        ),
        StockMembershipRecord(
            "instrument-placeholder",
            None,
            "Unresolved company",
            "placeholder",
            "classified",
            "sector-a",
            "Technology",
            "industry-a",
            "Cloud",
            date(2020, 1, 1),
            None,
            (),
        ),
        StockMembershipRecord(
            "instrument-no-primary",
            None,
            "Unverified company",
            "identified",
            "classified",
            "sector-a",
            "Technology",
            "industry-a",
            "Cloud",
            date(2020, 1, 1),
            None,
            (ListingRecord("listing-unverified", "NYSE", "CCC", "CCC", "USD", False, "verified"),),
        ),
    )

    assert verified_primary_provider_symbols(members) == ("AAA",)
