from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.application.build_snapshot import build_weekly_snapshot
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/industry_discovery.py"


@pytest.fixture
def industry_app(monkeypatch, tmp_path):
    root = tmp_path / "snapshots"
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(root))
    for level in ("SECTOR", "INDUSTRY"):
        build_weekly_snapshot(
            FixtureProvider(),
            ParquetSnapshotRepository(root),
            snapshot_id=f"us-{level.lower()}",
            market_id="US",
            level=level,
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
            *app.info,
            *app.warning,
            *app.error,
        )
    )


def test_industry_page_defaults_to_weekly_us_and_filters_multiple_parent_sectors(
    industry_app,
) -> None:
    assert any("Industry Discovery" in title.value for title in industry_app.title)
    mode = next(widget for widget in industry_app.selectbox if widget.label == "Evidence mode")
    assert mode.value == "Weekly snapshot"
    sectors = next(widget for widget in industry_app.multiselect if widget.label == "Sectors")
    sectors.set_value(["Information Technology", "Utilities"]).run(timeout=20)
    assert not industry_app.exception
    assert {widget.value for widget in industry_app.subheader} >= {
        "Information Technology industries",
        "Utilities industries",
    }
    assert all(
        frame.value["Industry"].isin(["Software", "Utilities"]).all()
        for frame in industry_app.dataframe
    )


def test_live_industry_mode_fails_closed_when_membership_and_rights_are_unverified(
    industry_app,
) -> None:
    mode = next(widget for widget in industry_app.selectbox if widget.label == "Evidence mode")
    mode.select("Live US").run(timeout=20)
    assert not industry_app.exception
    text = _text(industry_app).lower()
    assert "not enabled" in text
    assert "dated" in text and "rights" in text
    assert not industry_app.dataframe


def test_handoff_filters_to_parent_sector_and_mode(industry_app) -> None:
    industry_app.session_state["market_leadership.industry_handoff"] = {
        "market_id": "US",
        "mode": "weekly",
        "sector_node_ids": ["US-TECH"],
        "as_of": "2026-10-23",
    }
    industry_app.run(timeout=20)
    sectors = next(widget for widget in industry_app.multiselect if widget.label == "Sectors")
    assert sectors.value == ["Information Technology"]
    assert len(industry_app.dataframe) == 1
    assert set(industry_app.dataframe[0].value["Industry"]) == {"Software"}
