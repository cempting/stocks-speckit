from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.application.build_snapshot import build_weekly_snapshot
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/app.py"


@pytest.fixture
def weekly_app(monkeypatch, tmp_path):
    root = tmp_path / "snapshots"
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(root))
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "fixture")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path / "source-cache"))
    repository = ParquetSnapshotRepository(root)
    provider = FixtureProvider()
    for market in ("US", "JP", "GB"):
        build_weekly_snapshot(
            provider,
            repository,
            snapshot_id=f"{market.lower()}-sector",
            market_id=market,
            level="SECTOR",
            as_of=date(2026, 10, 28),
        )
    build_weekly_snapshot(
        provider,
        repository,
        snapshot_id="us-industry",
        market_id="US",
        level="INDUSTRY",
        as_of=date(2026, 10, 28),
    )
    app = AppTest.from_file(APP_PATH).run(timeout=20)
    assert not app.exception
    return app


def _text(app: AppTest) -> str:
    return " ".join(
        str(element.value)
        for element in (
            *app.title,
            *app.subheader,
            *app.caption,
            *app.markdown,
            *app.warning,
            *app.info,
            *app.error,
        )
    )


def test_completed_week_sector_scoreboard_is_default_and_locally_ranked(weekly_app) -> None:
    assert any("Weekly Sector Leadership" in title.value for title in weekly_app.title)
    markets = next(widget for widget in weekly_app.multiselect if widget.label == "Markets")
    markets.set_value(["US", "JP", "GB"]).run(timeout=20)
    assert not weekly_app.exception
    assert len(weekly_app.dataframe) == 3
    context = _text(weekly_app)
    for benchmark, currency in (("SPX", "USD"), ("N225", "JPY"), ("UKX", "GBP")):
        assert benchmark in context and currency in context
    assert "2026-10-23" in context
    assert [metric.value for metric in weekly_app.metric] == ["BULLISH", "SIDEWAYS", "BEARISH"]
    for table in weekly_app.dataframe:
        columns = table.value.columns
        assert {
            "Rank",
            "Status",
            "Composite",
            "Score change",
            "Rank change",
            "Proxy",
            "As of",
            "Observed",
            "Available on",
            "Coverage since",
            "Source",
            "Missing evidence",
        }.issubset(columns)
        assert table.value["Rank"].notna().all()
    markets.set_value(["JP"]).run(timeout=20)
    assert len(weekly_app.dataframe) == 1
    assert "SPX" not in _text(weekly_app)


def test_sector_drilldown_keeps_local_and_parent_context(weekly_app) -> None:
    sector = next(widget for widget in weekly_app.selectbox if widget.label == "Sector")
    sector.set_value("Information Technology").run(timeout=20)
    assert not weekly_app.exception
    text = _text(weekly_app)
    assert weekly_app.dataframe[1].value["Industry"].tolist() == ["Software"]
    assert "SPX" in text and "USD" in text and "2026-10-23" in text
    assert "parent sector" in text.lower()
    assert "local benchmark" in text.lower()
    assert len(weekly_app.dataframe) == 2


def test_weekly_missing_snapshot_has_explanatory_empty_state_without_live_fallback(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "empty"))
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "fixture")

    def no_live_provider(*args, **kwargs):
        raise AssertionError("weekly view must never fetch upstream data")

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", no_live_provider)
    app = AppTest.from_file(APP_PATH).run(timeout=20)

    assert not app.exception
    assert not app.dataframe
    assert any("weekly" in message.value.lower() for message in (*app.warning, *app.info))


def test_empty_market_selection_has_no_pooled_results(weekly_app) -> None:
    markets = next(widget for widget in weekly_app.multiselect if widget.label == "Markets")
    markets.set_value([]).run(timeout=20)
    assert not weekly_app.dataframe
    assert any("Select" in message.value for message in weekly_app.info)


def test_missing_one_market_snapshot_keeps_valid_market_panel(monkeypatch, tmp_path) -> None:
    root = tmp_path / "snapshots"
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(root))
    build_weekly_snapshot(
        FixtureProvider(),
        ParquetSnapshotRepository(root),
        snapshot_id="us-only",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    app = AppTest.from_file(APP_PATH).run(timeout=20)
    markets = next(widget for widget in app.multiselect if widget.label == "Markets")
    markets.set_value(["US", "JP"]).run(timeout=20)

    assert not app.exception
    assert len(app.dataframe) == 1
    assert "SPX" in _text(app)
    assert any("JP" in message.value and "weekly" in message.value for message in app.info)


def test_invalid_weekly_snapshot_shows_error_without_false_ranking(monkeypatch, tmp_path) -> None:
    root = tmp_path / "snapshots"
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(root))
    repository = ParquetSnapshotRepository(root)
    build_weekly_snapshot(
        FixtureProvider(),
        repository,
        snapshot_id="corrupt",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    path = root / "weekly/corrupt/entries.parquet"
    path.write_bytes(path.read_bytes() + b"bad")

    app = AppTest.from_file(APP_PATH).run(timeout=20)
    assert not app.exception
    assert not app.dataframe
    assert any("failed validation" in message.value for message in app.error)


def test_missing_twelve_month_history_has_no_rank_or_status(monkeypatch, tmp_path) -> None:
    from dataclasses import replace

    root = tmp_path / "snapshots"
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(root))
    fixture = FixtureProvider()

    class ShortHistoryProvider:
        provider_id = "fixture"

        def weekly_inputs(self, market_id, *, as_of):
            context = fixture.weekly_inputs(market_id, as_of=as_of)
            histories = dict(context.histories)
            short = histories["US-TECH-FUND"]
            histories["US-TECH-FUND"] = replace(short, closes=short.closes.iloc[-180:])
            return replace(context, histories=histories)

    build_weekly_snapshot(
        ShortHistoryProvider(),
        ParquetSnapshotRepository(root),
        snapshot_id="short-history",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    app = AppTest.from_file(APP_PATH).run(timeout=20)

    assert not app.exception
    table = app.dataframe[0].value
    tech = table.loc[table["Sector"] == "Information Technology"].iloc[0]
    utilities = table.loc[table["Sector"] == "Utilities"].iloc[0]
    assert tech["Sufficiency"] == "INSUFFICIENT"
    assert "missing_12m" in tech["Missing evidence"]
    assert tech["Rank"] is None or bool(pd.isna(tech["Rank"]))
    assert tech["Status"] is None or bool(pd.isna(tech["Status"]))
    assert pd.notna(utilities["Rank"])
