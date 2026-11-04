import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_data.catalog import CatalogReader
from streamlit_app import configure_default_catalog
from tests.support.fixture_provider import FixtureProvider

ROOT = Path(__file__).parents[2]
DEFAULT_ENTRY = ROOT / "data" / "catalog-us-etf-clusters" / "CURRENT.json"


def test_default_catalog_is_a_complete_app_readable_us_release() -> None:
    snapshot = CatalogReader().read(DEFAULT_ENTRY)

    assert snapshot.release.release_id
    assert any(region.region_id == "US" for region in snapshot.release.regions)
    assert len(snapshot.nodes) > 0
    assert len(snapshot.stocks) > 0
    assert len(snapshot.listings) > 0


def test_runner_selects_bundled_default_when_no_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MARKET_CATALOG_MANIFEST_PATH", raising=False)
    monkeypatch.setattr("streamlit_app.load_dotenv", lambda **kwargs: None)

    selected = configure_default_catalog()

    assert selected == DEFAULT_ENTRY
    assert os.environ["MARKET_CATALOG_MANIFEST_PATH"] == str(DEFAULT_ENTRY)


def test_runner_preserves_explicit_catalog_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    override = tmp_path / "CURRENT.json"
    monkeypatch.setenv("MARKET_CATALOG_MANIFEST_PATH", str(override))
    monkeypatch.setattr("streamlit_app.load_dotenv", lambda **kwargs: None)

    assert configure_default_catalog() == override
    assert os.environ["MARKET_CATALOG_MANIFEST_PATH"] == str(override)


def test_app_starts_with_default_catalog_without_live_provider(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    import dotenv

    monkeypatch.delenv("MARKET_CATALOG_MANIFEST_PATH", raising=False)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda **kwargs: None)
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path / "source-cache"))
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: FixtureProvider(),
    )

    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=30)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Discovery", "Industry Deep-Dive"]
    assert os.environ["MARKET_CATALOG_MANIFEST_PATH"] == str(DEFAULT_ENTRY)
