from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.universe_import import import_reviewed_file

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"


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


def test_discovery_uses_yfinance_contract_and_discloses_requested_observed_dates(
    monkeypatch, tmp_path
) -> None:
    provider_requests: list[str] = []

    def build_test_provider(provider_id: str, *args, **kwargs) -> FixtureProvider:
        del args, kwargs
        provider_requests.append(provider_id)
        return FixtureProvider()

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path / "source-cache"))
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(_populate_database(tmp_path)))
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        build_test_provider,
    )

    app = AppTest.from_file(APP_PATH).run(timeout=20)

    assert not app.exception
    assert provider_requests == ["yfinance"]
    text = " ".join(str(item.value) for item in (*app.title, *app.caption, *app.markdown))
    assert "SOURCE YFINANCE" in text
    assert "REQUESTED" in text and "OBSERVED" in text
    assert any(widget.label == "As of" for widget in app.date_input)
    assert any(widget.label == "Refresh data" for widget in app.button)
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)


def test_discovery_provider_failure_is_visible_without_fallback(monkeypatch, tmp_path) -> None:
    def fail_provider(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("controlled provider failure")

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        fail_provider,
    )
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(_populate_database(tmp_path)))

    app = AppTest.from_file(APP_PATH).run(timeout=20)

    assert any("could not be loaded" in item.value for item in app.error)
    assert any("controlled provider failure" in item.message for item in app.exception)
    assert not app.dataframe
    assert not app.get("arrow_vega_lite_chart")
