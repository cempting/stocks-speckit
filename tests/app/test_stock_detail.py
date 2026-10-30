from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.application.score_industry import IndustryScoreResult, StockScoreEvidence
from market_leadership.config import Settings
from market_leadership.domain.peer_scores import (
    BlockPeerScore,
    MetricPeerScore,
    PeerScorecard,
)
from market_leadership.domain.stock_selection import MembershipCatalog, MembershipEntry
from market_leadership.infrastructure.fixture_provider import FixtureProvider

ROOT = Path(__file__).parents[2]


def _catalog() -> MembershipCatalog:
    return MembershipCatalog(
        observed_on=date(2026, 10, 23),
        source_id="controlled-test",
        classification="controlled",
        mode="fixture",
        coverage="two controlled members",
        approval_reference="test-only",
        entries=tuple(
            MembershipEntry(
                f"instrument-{symbol.lower()}",
                f"company-{symbol.lower()}",
                symbol,
                name,
                "NASDAQ",
                "USD",
                "TECH",
                "Information Technology",
                "CLOUD",
                "Cloud Computing",
                date(2026, 1, 1),
                None,
            )
            for symbol, name in (("AAA", "Alpha"), ("BBB", "Beta"))
        ),
        fingerprint="controlled-catalog",
    )


def _score_result(members: tuple[MembershipEntry, ...]) -> IndustryScoreResult:
    metric = MetricPeerScore("metric", 1.0, 75.0, 5, "available")
    quality = BlockPeerScore("Quality", 75.0, "available", (metric, metric))
    growth = BlockPeerScore("Growth", 75.0, "available", (metric, metric))
    cash_flow = BlockPeerScore("Cash Flow", 75.0, "available", (metric, metric))
    stocks = tuple(
        StockScoreEvidence(
            member.instrument_id,
            PeerScorecard(member.instrument_id, quality, growth, cash_flow),
            "available",
        )
        for member in members
    )
    return IndustryScoreResult(
        date(2026, 10, 30),
        tuple(member.instrument_id for member in members),
        stocks,
    )


def _run_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AppTest:
    def build_fixture_provider(*args: object, **kwargs: object) -> FixtureProvider:
        del args, kwargs
        return FixtureProvider()

    def load_test_catalog(path: str) -> MembershipCatalog:
        del path
        return _catalog()

    def validate_test_catalog(catalog: MembershipCatalog, settings: Settings) -> None:
        del catalog, settings

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider", build_fixture_provider
    )
    monkeypatch.setattr(
        "market_leadership.infrastructure.stock_membership.load_membership_catalog",
        load_test_catalog,
    )
    monkeypatch.setattr(
        "market_leadership.infrastructure.stock_membership.validate_live_access",
        validate_test_catalog,
    )
    monkeypatch.setenv("STOCK_MEMBERSHIP_CATALOG", "controlled-test.json")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    return AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )


def _select_cloud_industry(app: AppTest) -> AppTest:
    app.selectbox("market_leadership.progressive_discovery.sector").select("XLK").run(timeout=20)
    return (
        app.selectbox("market_leadership.progressive_discovery.industry")
        .select("US-CLOUD-COMPUTING")
        .run(timeout=20)
    )


def test_stock_detail_uses_stable_identity_and_returns_to_industry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    load_calls = 0

    def score(
        members: tuple[MembershipEntry, ...],
        *,
        cutoff: date,
        refresh: bool = False,
    ) -> IndustryScoreResult:
        nonlocal load_calls
        del cutoff, refresh
        load_calls += 1
        return _score_result(members)

    monkeypatch.setattr("market_leadership.application.score_industry.score_industry", score)
    app = _run_app(monkeypatch, tmp_path)
    app = _select_cloud_industry(app)

    assert not app.exception
    assert load_calls == 0
    next(button for button in app.button if button.label == "Load peer scores").click().run(
        timeout=20
    )
    assert not app.exception
    assert load_calls == 1

    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)

    assert not app.exception
    assert any(item.value == "AAA · Alpha" for item in app.title), (
        f"titles={[item.value for item in app.title]}, "
        f"subheaders={[item.value for item in app.subheader]}, "
        f"errors={[item.value for item in app.error]}"
    )
    assert any(item.value == "Peer scorecard" for item in app.subheader)
    assert [metric.value for metric in app.metric] == ["75.0", "75.0", "75.0"]
    next(button for button in app.button if button.label == "Back to Discovery").click().run(
        timeout=20
    )

    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert app.selectbox("market_leadership.progressive_discovery.sector").value == "XLK"
    assert (
        app.selectbox("market_leadership.progressive_discovery.industry").value
        == "US-CLOUD-COMPUTING"
    )
    assert load_calls == 1


def test_changing_sector_clears_the_stock_and_industry_tape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_app(monkeypatch, tmp_path)
    app = _select_cloud_industry(app)
    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)
    app.selectbox("market_leadership.progressive_discovery.sector").select("XLF").run(timeout=20)

    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Contained stocks" for item in app.subheader)
    assert app.selectbox("market_leadership.progressive_discovery.industry").value is None


def test_selecting_stock_row_opens_its_stable_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_app(monkeypatch, tmp_path)
    app = _select_cloud_industry(app)
    app.session_state["market_leadership.progressive_discovery.stock_tape"] = {
        "selection": {"rows": [1], "columns": [], "cells": []}
    }

    app.run(timeout=20)

    assert not app.exception
    assert any(item.value == "BBB · Beta" for item in app.title)
