from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider

ROOT = Path(__file__).parents[2]


def test_entrypoint_has_only_live_discovery_and_reviewed_membership_tabs(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: FixtureProvider(),
    )
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))

    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Discovery", "Industry Deep-Dive"]
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)
    assert any("Initialize and populate" in message.value for message in app.info)


def test_discovery_does_not_read_the_legacy_experimental_catalog(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: FixtureProvider(),
    )
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(tmp_path / "missing.sqlite"))
    monkeypatch.setenv("EXPERIMENTAL_UNIVERSE_CATALOG", str(tmp_path / "legacy-catalog.json"))

    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)

    assert not app.exception
    assert not any("Experimental provider-label" in item.value for item in app.subheader)
    assert any("Initialize and populate" in item.value for item in app.info)
