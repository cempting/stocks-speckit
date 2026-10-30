from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider


def test_discovery_uses_one_yfinance_path_and_discloses_dates(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, ...]] = []

    class CountingProvider(FixtureProvider):
        def fetch_daily_history(self, symbols, *, start, end, force=False):
            calls.append(symbols)
            return super().fetch_daily_history(symbols, start=start, end=end, force=force)

    monkeypatch.setattr(
        "market_leadership.ui.workflows.discovery_page.build_request_provider",
        lambda *args, **kwargs: CountingProvider(),
    )
    app_path = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    text = " ".join(str(item.value) for item in (*app.caption, *app.markdown))
    assert "SOURCE YFINANCE" in text
    assert "REQUESTED" in text and "OBSERVED" in text
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)
    assert not any("snapshot" in item.value.lower() for item in app.info)
