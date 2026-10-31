from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import configure_ui


def test_cloud_entrypoint_renders_progressive_tabs_without_routing(
    monkeypatch, catalog_release
) -> None:
    calls = configure_ui(monkeypatch, catalog_release)
    app_path = Path(__file__).parents[2] / "streamlit_app.py"

    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Discovery"
    assert [tab.label for tab in app.tabs] == ["Discovery", "Industry Deep-Dive"]
    assert calls == [("TEST_ETF",)]
