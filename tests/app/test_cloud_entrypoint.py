from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_cloud_entrypoint_renders_discovery_page(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    app_path = Path(__file__).parents[2] / "streamlit_app.py"

    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "US Sector Discovery"
    assert len(app.dataframe[0].value) == 11
