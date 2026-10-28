import copy
import json
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.snapshot_errors import SourceUnavailable

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/app.py"
ACCEPTANCE_PATH = Path(__file__).parents[1] / "fixtures/acceptance"


@pytest.fixture
def market_app(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_DATA_PROVIDERS", "fixture")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path / "source-cache"))
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "snapshots"))

    def fixture_only(provider_id, retry_limit):
        assert provider_id == "fixture", "the app test must not request a live provider"
        return FixtureProvider()

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", fixture_only)
    app = AppTest.from_file(APP_PATH)
    app.session_state["discovery_source_mode"] = "Acceptance fixture"
    app.run(timeout=20)
    as_of = next((widget for widget in app.date_input if widget.label == "As of"), None)
    if as_of is not None:
        as_of.set_value(date(2026, 10, 23)).run(timeout=20)
    assert not app.exception
    return app


def _market_selector(app):
    assert app.multiselect, "Discovery must expose an explicit market multiselect"
    selector = next(
        (widget for widget in app.multiselect if "market" in widget.label.lower()),
        None,
    )
    assert selector is not None, "The market selection must be labelled"
    return selector


def _choose_markets(app, *market_ids):
    selector = _market_selector(app)
    choices = {}
    market_names = {"US": "United States", "JP": "Japan", "GB": "United Kingdom"}
    for market_id in market_ids:
        matches = [
            option
            for option in selector.options
            if str(option).upper() == market_id
            or f"({market_id})" in str(option).upper()
            or market_names[market_id].lower() in str(option).lower()
        ]
        assert len(matches) == 1, f"{market_id} must be an explicit market option"
        choices[market_id] = matches[0]
    selector.set_value(list(choices.values())).run(timeout=20)
    assert not app.exception
    assert set(_market_selector(app).value) == set(choices.values())
    return app


def _visible_text(app):
    elements = (
        list(app.title)
        + list(app.header)
        + list(app.subheader)
        + list(app.caption)
        + list(app.markdown)
        + list(app.metric)
    )
    return " ".join(str(item.value) for item in elements)


def _sector_tables(app):
    return [frame.value for frame in app.dataframe]


def _contains_local_outcomes(table, outcomes):
    period_columns = [
        column
        for column in table.columns
        if "3 month" in str(column).lower() or "3m" in str(column).lower()
    ]
    if "Sector" not in table or not period_columns:
        return False
    for outcome in outcomes:
        rows = table.loc[table["Sector"] == outcome["sector"]]
        if len(rows) != 1:
            return False
        value = rows.iloc[0][period_columns[0]]
        try:
            observed = float(str(value).strip("%"))
        except (TypeError, ValueError):
            return False
        expected = (outcome["absolute_3m"], outcome["relative_3m"])
        if not any(
            abs(observed - possible * scale) < 0.001 for possible in expected for scale in (1, 100)
        ):
            return False
    return True


def test_fixture_markets_have_local_context_and_separate_sector_results(market_app):
    fixture = json.loads((ACCEPTANCE_PATH / "market_data.json").read_text())
    expected = json.loads((ACCEPTANCE_PATH / "expected.json").read_text())
    markets = {market["market_id"]: market for market in fixture["markets"]}

    for selected in (("US",), ("JP",), ("GB",), ("US", "JP", "GB")):
        _choose_markets(market_app, *selected)
        text = _visible_text(market_app)
        tables = _sector_tables(market_app)
        local_table_indexes = []

        for market_id in selected:
            market = markets[market_id]
            assert market["local_benchmark_id"] in text
            assert market["base_currency"] in text
            assert expected["market_regimes"][market_id] in text
            assert fixture["as_of"] in text
            assert "adjusted" in text.lower()

            top = expected["top_sector_by_local_relative_return"][market_id]
            bottom = expected["bottom_sector_by_local_relative_return"][market_id]
            outcomes = [
                outcome
                for outcome in fixture["sector_outcomes"]
                if outcome["market_id"] == market_id and outcome["sector"] in (top, bottom)
            ]
            assert len(outcomes) == 2
            local_tables = [
                index
                for index, table in enumerate(tables)
                if _contains_local_outcomes(table, outcomes)
            ]
            assert len(local_tables) == 1, f"{market_id} needs its own local sector panel"
            local_table_indexes.extend(local_tables)

        assert len(set(local_table_indexes)) == len(selected), (
            "Markets must not share a pooled table"
        )

        for market_id in markets.keys() - set(selected):
            assert markets[market_id]["local_benchmark_id"] not in text


def test_valid_market_selection_survives_reruns_and_selection_changes(market_app):
    _choose_markets(market_app, "US", "JP")
    before = _visible_text(market_app)
    assert "N225" in before

    market_app.run(timeout=20)
    assert not market_app.exception
    assert len(_market_selector(market_app).value) == 2
    assert "N225" in _visible_text(market_app)

    _choose_markets(market_app, "JP", "GB")
    text = _visible_text(market_app)
    assert "N225" in text and "UKX" in text
    assert "SPX" not in text
    assert len(_sector_tables(market_app)) >= 2


def test_empty_selection_does_not_show_a_default_or_pooled_ranking(market_app):
    _choose_markets(market_app)
    assert not _sector_tables(market_app)
    assert market_app.info or market_app.warning
    assert "SPX" not in _visible_text(market_app)


def test_late_fixture_data_is_not_presented_as_current(market_app):
    as_of = next(widget for widget in market_app.date_input if widget.label == "As of")
    as_of.set_value(date(2026, 10, 26)).run(timeout=20)
    _choose_markets(market_app, "JP")

    text = _visible_text(market_app)
    text += " ".join(item.value for item in (*market_app.warning, *market_app.info))
    assert "N225" in text
    assert "stale" in text.lower() or "insufficient" in text.lower()
    assert not any(
        "Current" in table.to_string(index=False) for table in _sector_tables(market_app)
    )


def test_missing_local_history_keeps_other_market_visible(market_app, monkeypatch):
    fixture = json.loads((ACCEPTANCE_PATH / "market_data.json").read_text())
    altered = copy.deepcopy(fixture)
    altered["benchmark_histories"] = [
        row for row in altered["benchmark_histories"] if row["market_id"] != "JP"
    ]
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_fixture_market_context",
        lambda: altered,
    )
    _choose_markets(market_app, "US", "JP")

    text = _visible_text(market_app)
    assert "SPX" in text and "N225" in text
    assert "Unavailable" in text
    assert any(
        "JP" in warning.value and "insufficient" in warning.value for warning in market_app.warning
    )
    assert len(_sector_tables(market_app)) == 1


def test_unavailable_fixture_reports_error_without_exposing_local_paths(market_app, monkeypatch):
    def unavailable():
        raise SourceUnavailable("private/local/path/market_data.json", "market_context")

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_fixture_market_context",
        unavailable,
    )
    market_app.run(timeout=20)

    assert not market_app.exception
    assert any("could not be loaded" in error.value for error in market_app.error)
    assert "private/local/path" not in _visible_text(market_app)
    assert not _sector_tables(market_app)


def test_missing_published_input_shows_empty_state_without_live_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path / "missing"))

    def unexpected_provider(*args, **kwargs):
        raise AssertionError("missing snapshot must not fall back to a live provider")

    monkeypatch.setattr("market_leadership.bootstrap._build_provider_adapter", unexpected_provider)
    app = AppTest.from_file(APP_PATH)
    app.session_state["discovery_source_mode"] = "Published snapshot"
    app.run(timeout=20)

    assert not app.exception
    assert any("snapshot" in warning.value.lower() for warning in app.warning)
    assert not _sector_tables(app)


def test_snapshot_loading_error_is_visible_without_a_false_current_panel(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path))

    def broken_snapshot(*args, **kwargs):
        raise RuntimeError("fixture snapshot unavailable")

    monkeypatch.setattr(
        "market_leadership.ui.cache.load_published_discovery",
        broken_snapshot,
    )
    app = AppTest.from_file(APP_PATH)
    app.session_state["discovery_source_mode"] = "Published snapshot"
    app.run(timeout=20)

    assert any("could not be loaded" in error.value.lower() for error in app.error)
    assert not _sector_tables(app)
