from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_discovery_page_renders_all_sectors_and_refresh(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    app_path = Path(__file__).parents[2] / "src/market_leadership/app.py"
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "US Sector Discovery"
    assert any("S&P 500 sentiment" in item.value for item in app.markdown)
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 11
    assert "1 week" in app.dataframe[0].value.columns
    assert "1 month" in app.dataframe[0].value.columns

    theme_button = next(button for button in app.button if button.label == "")
    theme_button.click().run(timeout=20)

    assert not app.exception
    theme_css = app.markdown[0].value
    assert "#111820" in theme_css
    assert 'button[kind="secondary"]' in theme_css
    assert '[data-variant="segmented_control"]' in theme_css
    assert "--gdg-bg-cell: #18232d" in theme_css
    assert sum(button.label == "" for button in app.button) == 1

    refresh = next(button for button in app.button if button.label == "Refresh data")
    refresh.click().run(timeout=20)

    assert not app.exception
    assert len(app.dataframe[0].value) == 11
