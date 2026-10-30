from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"


@pytest.fixture
def discovery_app(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "fixture")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path / "source-cache"))
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "snapshots"))

    def fixture_only(provider_id, retry_limit):
        assert provider_id == "fixture", "the app test must not request an unconfigured provider"
        return FixtureProvider()

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", fixture_only)
    app = AppTest.from_file(APP_PATH).run(timeout=20)
    assert not app.exception
    return app


def _text(app: AppTest) -> str:
    elements = (
        *app.title,
        *app.header,
        *app.subheader,
        *app.caption,
        *app.markdown,
        *app.metric,
        *app.info,
        *app.warning,
        *app.error,
    )
    return " ".join(str(item.value) for item in elements)


def test_default_weekly_mode_does_not_request_live_data(discovery_app) -> None:
    mode = next(
        widget for widget in discovery_app.segmented_control if widget.label == "Discovery mode"
    )
    assert mode.value == "Weekly leadership"
    assert any("Discovery" in title.value for title in discovery_app.title)
    assert not discovery_app.exception


def test_acceptance_comparison_is_us_only_and_explicitly_fixture_backed(discovery_app) -> None:
    mode = next(
        widget for widget in discovery_app.segmented_control if widget.label == "Discovery mode"
    )
    mode.set_value("US acceptance comparison").run(timeout=20)

    assert not discovery_app.exception
    text = _text(discovery_app)
    assert "Market Comparison" in text
    assert "controlled us sample" in text.lower()
    assert "SPX" in text and "USD" in text
    assert "N225" not in text and "UKX" not in text
    assert not any(widget.label == "Markets" for widget in discovery_app.multiselect)


def test_live_mode_uses_explicit_provider_and_daily_as_of_controls(discovery_app) -> None:
    mode = next(
        widget for widget in discovery_app.segmented_control if widget.label == "Discovery mode"
    )
    mode.set_value("US live daily").run(timeout=20)

    assert not discovery_app.exception
    assert any(widget.label == "Data provider" for widget in discovery_app.selectbox)
    assert any(widget.label == "As of" for widget in discovery_app.date_input)
    assert any(widget.label == "Refresh data" for widget in discovery_app.button)
    assert "ADJUSTED DAILY BARS" in _text(discovery_app)
    assert not any("Published snapshot" in value for value in _text(discovery_app).split())


def test_missing_weekly_snapshot_does_not_fall_back_to_provider(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "fixture")
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "missing"))

    def unexpected_provider(*args, **kwargs):
        raise AssertionError("weekly view must not request a live provider")

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", unexpected_provider)
    app = AppTest.from_file(APP_PATH).run(timeout=20)
    assert not app.exception
    assert any("weekly" in message.value.lower() for message in app.info)
    assert not app.dataframe


def test_acceptance_fixture_failure_is_visible_without_local_path(
    discovery_app, monkeypatch
) -> None:
    from market_leadership.infrastructure.snapshot_errors import SourceUnavailable

    def unavailable():
        raise SourceUnavailable("private/local/path/market_data.json", "market_context")

    monkeypatch.setattr("market_leadership.bootstrap.build_fixture_market_context", unavailable)
    mode = next(
        widget for widget in discovery_app.segmented_control if widget.label == "Discovery mode"
    )
    mode.set_value("US acceptance comparison").run(timeout=20)

    assert not discovery_app.exception
    assert any("could not be loaded" in error.value for error in discovery_app.error)
    assert "private/local/path" not in _text(discovery_app)
    assert not discovery_app.dataframe


def test_historical_fixture_date_is_explicit(discovery_app) -> None:
    mode = next(
        widget for widget in discovery_app.segmented_control if widget.label == "Discovery mode"
    )
    mode.set_value("US acceptance comparison").run(timeout=20)
    as_of = next(widget for widget in discovery_app.date_input if widget.label == "As of")
    as_of.set_value(date(2026, 10, 26)).run(timeout=20)
    assert as_of.value == (date(2026, 10, 26),)
