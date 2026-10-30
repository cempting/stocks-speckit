from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.universe_import import import_reviewed_file


def _populate_database(tmp_path: Path) -> Path:
    database_path = tmp_path / "market-universe.sqlite"
    database = RegionDatabase(database_path)
    database.initialize()
    source = tmp_path / "members.csv"
    source.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        source,
        region_id="US",
        classification_id="TEST",
        source_id="controlled-test",
        exchange_id=None,
        coverage="controlled sample",
        approval_reference="test-only",
    )
    return database_path


def test_discovery_uses_one_yfinance_path_and_discloses_dates(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, ...]] = []

    class CountingProvider(FixtureProvider):
        def fetch_daily_history(self, symbols, *, start, end, force=False):
            calls.append(symbols)
            return super().fetch_daily_history(symbols, start=start, end=end, force=force)

    def build_test_provider(provider_id: str, *args, **kwargs) -> CountingProvider:
        del args, kwargs
        assert provider_id == "yfinance"
        return CountingProvider()

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        build_test_provider,
    )
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(_populate_database(tmp_path)))
    app_path = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    text = " ".join(str(item.value) for item in (*app.caption, *app.markdown))
    assert "SOURCE YFINANCE" in text
    assert "REQUESTED" in text and "OBSERVED" in text
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)
    assert not any("snapshot" in item.value.lower() for item in app.info)
    assert len(calls) == 1
