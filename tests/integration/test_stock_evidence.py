from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from market_leadership.application.load_stock_history import load_stock_history
from market_leadership.application.score_industry import score_industry
from market_leadership.domain.fundamentals import (
    FundamentalBundle,
    FundamentalRequest,
)
from market_leadership.domain.stock_selection import MembershipEntry
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.ui.cache import load_member_history


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
