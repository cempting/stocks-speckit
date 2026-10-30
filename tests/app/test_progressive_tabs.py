from datetime import UTC, datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.experimental_universe_catalog import (
    UniverseSource,
    build_experimental_catalog,
    write_experimental_catalog,
)
from market_leadership.infrastructure.fixture_provider import FixtureProvider

ROOT = Path(__file__).parents[2]


def test_entrypoint_has_only_live_discovery_and_reviewed_membership_tabs(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "market_leadership.ui.workflows.discovery_page.build_request_provider",
        lambda *args, **kwargs: FixtureProvider(),
    )
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))

    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Discovery", "Industry Deep-Dive"]
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)
    assert any("STOCK_MEMBERSHIP_CATALOG" in message.value for message in app.error)


def test_discovery_discloses_the_experimental_provider_catalog(monkeypatch, tmp_path):
    source = tmp_path / "sp500.csv"
    source.write_text(
        "Ticker,Name,Sector,Industry\n"
        "AAA,Alpha,Information Technology,Application Software\n"
    )
    catalog_path = tmp_path / "experimental-catalog.json"
    write_experimental_catalog(
        build_experimental_catalog(
            (UniverseSource("wikipedia-sp500-gics", source, 0),),
            generated_at=datetime(2026, 10, 30, tzinfo=UTC),
        ),
        catalog_path,
    )
    monkeypatch.setattr(
        "market_leadership.ui.workflows.discovery_page.build_request_provider",
        lambda *args, **kwargs: FixtureProvider(),
    )
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    monkeypatch.setenv("EXPERIMENTAL_UNIVERSE_CATALOG", str(catalog_path))

    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)

    assert not app.exception
    assert any(
        item.value == "Experimental provider-label industry catalog"
        for item in app.subheader
    )
    assert any(
        "not the GICS momentum catalog" in item.value
        for item in app.caption
    )
