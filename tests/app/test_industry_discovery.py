from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_industry_deep_dive_blocks_unreviewed_membership_without_fixture_selector(
    monkeypatch,
) -> None:
    monkeypatch.delenv("STOCK_MEMBERSHIP_CATALOG", raising=False)
    app_path = (
        Path(__file__).parents[2]
        / "src/market_leadership/ui/workflows/industry_deep_dive.py"
    )
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert any("STOCK_MEMBERSHIP_CATALOG" in message.value for message in app.error)
    assert not any(widget.label == "Stock evidence mode" for widget in app.selectbox)
