from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_industry_deep_dive_explains_missing_database(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("STOCK_MEMBERSHIP_CATALOG", raising=False)
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(tmp_path / "missing.sqlite"))
    app_path = (
        Path(__file__).parents[2] / "src/market_leadership/ui/workflows/industry_deep_dive.py"
    )
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert any("Initialize and populate" in message.value for message in app.info)
    assert not any(widget.label == "Stock evidence mode" for widget in app.selectbox)
