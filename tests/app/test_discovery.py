from pathlib import Path

from streamlit.testing.v1 import AppTest

from market_leadership.application.build_snapshot import build_daily_history_snapshot
from market_leadership.application.discover_sectors import BENCHMARK, SECTOR_PROXIES
from market_leadership.bootstrap import build_market_data_request
from market_leadership.config import load_settings
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository


def test_discovery_page_renders_all_sectors_and_refresh(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    upstream_force_values: list[bool] = []
    fixture = FixtureProvider()

    class CountingProvider:
        provider_id = "fixture"

        def fetch_daily_history(self, symbols, *, start, end, force=False):
            upstream_force_values.append(force)
            return fixture.fetch_daily_history(
                symbols,
                start=start,
                end=end,
                force=force,
            )

    monkeypatch.setattr(
        "market_leadership.bootstrap._build_provider_adapter",
        lambda provider_id, retry_limit: CountingProvider(),
    )
    app_path = Path(__file__).parents[2] / "src/market_leadership/app.py"
    app = AppTest.from_file(app_path).run(timeout=20)

    assert not app.exception
    assert upstream_force_values == [False]
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
    assert upstream_force_values == [False]

    refresh = next(button for button in app.button if button.label == "Refresh data")
    refresh.click().run(timeout=20)

    assert not app.exception
    assert len(app.dataframe[0].value) == 11
    assert upstream_force_values == [False, True]


def test_snapshot_mode_loads_published_input_without_upstream_calls(monkeypatch, tmp_path) -> None:
    from dataclasses import replace
    from datetime import date

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    settings = replace(
        load_settings(),
        provider_ids=("fixture",),
        source_cache_path=str(tmp_path / "source-cache"),
    )
    repository = ParquetSnapshotRepository(tmp_path / "snapshots")
    build_daily_history_snapshot(
        build_market_data_request(settings),
        repository,
        snapshot_id="daily-2026-10-23",
        as_of=date(2026, 10, 23),
        start=date(2025, 5, 1),
        symbols=(BENCHMARK, *(symbol for _, symbol in SECTOR_PROXIES)),
    )

    def unexpected_upstream(*args, **kwargs):
        raise AssertionError("snapshot mode must not construct a runtime provider")

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", unexpected_upstream)
    app_path = Path(__file__).parents[2] / "src/market_leadership/app.py"
    app = AppTest.from_file(app_path)
    app.session_state["discovery_source_mode"] = "Published snapshot"
    app.run(timeout=20)

    assert not app.exception
    assert len(app.dataframe[0].value) == 11
    assert "daily-2026-10-23" in " ".join(item.value for item in app.markdown)
    assert not any(button.label == "Refresh data" for button in app.button)
    app.run(timeout=20)
    assert not app.exception
    assert len(app.dataframe[0].value) == 11


def test_snapshot_mode_reports_missing_snapshot_without_upstream_call(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "missing"))

    def unexpected_upstream(*args, **kwargs):
        raise AssertionError("snapshot mode must not construct a runtime provider")

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", unexpected_upstream)
    app_path = Path(__file__).parents[2] / "src/market_leadership/app.py"
    app = AppTest.from_file(app_path)
    app.session_state["discovery_source_mode"] = "Published snapshot"
    app.run(timeout=20)

    assert not app.exception
    assert any("No published daily-history snapshot" in warning.value for warning in app.warning)
