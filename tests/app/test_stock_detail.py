from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.application.score_industry import IndustryScoreResult, StockScoreEvidence
from market_leadership.domain.peer_scores import (
    BlockPeerScore,
    MetricPeerScore,
    PeerScorecard,
)
from market_leadership.domain.stock_selection import MembershipEntry
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.universe_import import import_reviewed_file

ROOT = Path(__file__).parents[2]


def _create_database(tmp_path: Path) -> Path:
    database_path = tmp_path / "market-universe.sqlite"
    database = RegionDatabase(database_path)
    database.initialize()
    members = tmp_path / "members.csv"
    members.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom\n"
        "instrument-aaa,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n"
        "instrument-bbb,BBB,Beta,NASDAQ,Technology,Cloud,2020-01-01\n"
        "instrument-ccc,CCC,Gamma,NYSE,Financials,Banks,2020-01-01\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        members,
        region_id="US",
        classification_id="TEST",
        source_id="controlled-test",
        exchange_id=None,
        coverage="controlled sample",
        approval_reference="test-only",
    )
    return database_path


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

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider", build_fixture_provider
    )
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(_create_database(tmp_path)))
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    return AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )


def _select_cloud_industry(app: AppTest) -> AppTest:
    app.selectbox("market_leadership.progressive_discovery.sector").select("test-technology").run(
        timeout=20
    )
    return (
        app.selectbox("market_leadership.progressive_discovery.industry")
        .select("test-cloud")
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
    assert (
        app.selectbox("market_leadership.progressive_discovery.sector").value == "test-technology"
    )
    assert app.selectbox("market_leadership.progressive_discovery.industry").value == "test-cloud"
    assert load_calls == 1


def test_changing_sector_clears_the_stock_and_industry_tape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_app(monkeypatch, tmp_path)
    app = _select_cloud_industry(app)
    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)
    app.selectbox("market_leadership.progressive_discovery.sector").select("test-financials").run(
        timeout=20
    )

    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Contained stocks" for item in app.subheader)
    assert app.selectbox("market_leadership.progressive_discovery.industry").value is None


def test_selecting_stock_row_opens_its_stable_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_app(monkeypatch, tmp_path)
    app = _select_cloud_industry(app)
    next(button for button in app.button if button.label == "BBB · Beta").click().run(timeout=20)

    assert not app.exception
    assert any(item.value == "BBB · Beta" for item in app.title)


def test_stock_detail_discloses_scores_until_explicitly_loaded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_app(monkeypatch, tmp_path)
    app = _select_cloud_industry(app)
    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)

    assert not app.exception
    assert [metric.value for metric in app.metric] == [
        "Not loaded",
        "Not loaded",
        "Not loaded",
    ]
