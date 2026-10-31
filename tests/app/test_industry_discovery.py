from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import configure_ui


def test_industry_deep_dive_explains_missing_catalog(monkeypatch, catalog_release) -> None:
    calls = configure_ui(monkeypatch, catalog_release)
    (catalog_release.parent / "CURRENT.json").unlink()
    app_path = (
        Path(__file__).parents[2] / "src/market_leadership/ui/workflows/industry_deep_dive.py"
    )
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert any("catalog is unavailable" in message.value for message in app.error)
    assert calls == []
    assert not any(widget.label == "Stock evidence mode" for widget in app.selectbox)
