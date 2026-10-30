from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_cloud_entrypoint_renders_progressive_tabs_without_routing(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    app_path = Path(__file__).parents[2] / "streamlit_app.py"

    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Sector/Industry Screen"
    assert [tab.label for tab in app.tabs] == [
        "Sector/Industry Screen",
        "Industry Deep-Dive",
        "Fundamental Grading",
    ]
