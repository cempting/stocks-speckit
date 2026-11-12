from datetime import date
from pathlib import Path

import pytest
from streamlit.proto.Block_pb2 import Block as BlockProto
from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import DailyProvider, configure_ui

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"

PREFIX = "market_leadership.progressive_discovery."


@pytest.mark.parametrize("dark_mode", [False, True])
@pytest.mark.parametrize("industry", [False, True])
def test_entity_heading_controls_keep_native_scope_and_state(
    monkeypatch, catalog_release, dark_mode, industry
) -> None:
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(APP_PATH)
    app.session_state["dark_mode"] = dark_mode
    app.run(timeout=20)
    if industry:
        app.button(PREFIX + "sector_tape_select_test-sector").click().run()
    assert not app.exception
    heading = next(
        item for item in app.subheader
        if item.value == ("Industry momentum" if industry else "Sector performance")
    )
    row = next(
        block for block in app.get("flex_container")
        if any(child.type == "column" for child in block.children.values())
        and any(item is heading for item in block.subheader)
    )
    columns = list(row.children.values())
    assert len(columns) == 3
    assert [column.proto.weight for column in columns] == pytest.approx([1 / 3] * 3)
    assert columns[0].subheader[0] is heading
    period = columns[1].segmented_control[0]
    basis = columns[2].segmented_control[0]
    assert period.key == PREFIX + "thumbnail_period"
    assert period.label == "Thumbnail period" and period.value == "3m"
    assert period.options == ["1w", "1m", "3m", "6m", "1y"]
    assert basis.key == PREFIX + "performance_basis"
    assert basis.label == "Performance basis" and basis.value == "Absolute"
    assert basis.options == ["Absolute", "vs S&P 500"]
    wrappers = [
        block for block in app.get("flex_container")
        if "entity_performance_controls" in block.proto.id
    ]
    assert len(wrappers) == 1
    style = next(
        element.proto.body for element in app.get("html")
        if ".st-key-entity_performance_controls" in element.proto.body
    )
    assert "@media (max-width: 640px)" in style
    assert "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)" in style
    assert "grid-row: 1 / span 2" in style
    assert "grid-row: 2" in style
    assert "overflow-wrap: anywhere" in style
    assert ".st-key-discovery_header" not in style
    count = len(calls)
    period.set_value("1y").run()
    basis = app.segmented_control(PREFIX + "performance_basis")
    basis.set_value("vs S&P 500").run()
    assert not app.exception and len(calls) == count + 2
    app.button("dark_mode_button").click().run()
    assert app.segmented_control(PREFIX + "thumbnail_period").value == "1y"
    assert app.segmented_control(PREFIX + "performance_basis").value == "vs S&P 500"
    if industry:
        app.button(PREFIX + "industry_tape_select_test-cloud").click().run()
        assert not app.exception
        assert not any(
            "entity_performance_controls" in block.proto.id
            for block in app.get("flex_container")
        )


@pytest.mark.parametrize("app_path", [APP_PATH, APP_PATH.parents[4] / "streamlit_app.py"])
def test_discovery_header_places_dark_mode_to_the_right_of_refresh(
    monkeypatch, catalog_release, app_path
) -> None:
    configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(app_path).run(timeout=20)
    assert not app.exception
    heading = next(item for item in app.title if item.value == "Discovery")
    requested_date = next(widget for widget in app.date_input if widget.label == "As of")
    refresh = next(widget for widget in app.button if widget.label == "Refresh data")
    dark_mode = app.button("dark_mode_button")
    row = next(
        block
        for block in app.get("flex_container")
        if any(child.type == "column" for child in block.children.values())
        and any(item is heading for item in block.title)
    )
    columns = list(row.children.values())
    assert len(columns) == 4
    assert all(column.type == "column" for column in columns)
    assert columns[0].title[0] is heading
    assert columns[1].date_input[0] is requested_date
    assert columns[2].button[0] is refresh
    assert columns[3].button[0] is dark_mode
    assert dark_mode.label == "Switch to dark mode"
    assert dark_mode.proto.icon == ":material/dark_mode:"
    assert not dark_mode.help
    assert not columns[3].markdown
    assert not app.toggle
    assert [column.proto.weight for column in columns] == pytest.approx(
        [4 / 12, 3 / 12, 3 / 12, 2 / 12]
    )
    assert all(column.proto.vertical_alignment == BlockProto.Column.BOTTOM for column in columns)
    header_style = next(
        item.proto.body
        for item in app.get("html")
        if ".st-key-discovery_header" in item.proto.body
    )
    assert "@media (max-width: 640px)" in header_style
    assert (
        "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(2.5rem, auto);"
        in header_style
    )
    assert "grid-row: 1 / span 2;" in header_style
    assert "grid-column: 2 / 4;" in header_style
    assert "grid-column: 3;" in header_style
    assert "grid-row: 2;" in header_style
    assert ".st-key-discovery_header .st-key-theme_action button" in header_style
    assert "min-width: 2.5rem;" in header_style
    assert ".st-key-discovery_header h1" in header_style
    assert "overflow-wrap: anywhere;" in header_style


@pytest.mark.parametrize("app_path", [APP_PATH, APP_PATH.parents[4] / "streamlit_app.py"])
def test_dark_mode_switch_updates_appearance_and_preserves_discovery_controls(
    monkeypatch, catalog_release, app_path
) -> None:
    configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(app_path).run(timeout=20)
    app.date_input[0].set_value(date(2026, 10, 30)).run(timeout=20)
    requested_date = app.date_input[0].value
    assert app.session_state["dark_mode"] is False
    assert app.button("dark_mode_button").proto.icon == ":material/dark_mode:"
    app.button("dark_mode_button").click().run(timeout=20)
    assert not app.exception
    assert app.session_state["dark_mode"] is True
    assert app.button("dark_mode_button").proto.icon == ":material/light_mode:"
    assert app.button("dark_mode_button").label == "Switch to light mode"
    assert app.date_input[0].value == requested_date
    assert any("--app-background: #111820" in item.proto.body for item in app.get("html"))
    charts = app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart")
    assert charts
    assert all('"background": "#111820"' in chart.proto.spec for chart in charts)
    app.run(timeout=20)
    assert app.session_state["dark_mode"] is True
    assert app.button("dark_mode_button").proto.icon == ":material/light_mode:"
    app.button("dark_mode_button").click().run(timeout=20)
    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.button("dark_mode_button").proto.icon == ":material/dark_mode:"
    assert app.button("dark_mode_button").label == "Switch to dark mode"
    assert any("--app-background: #f7f8f6" in item.proto.body for item in app.get("html"))
    assert all(
        '"background": "#f7f8f6"' in chart.proto.spec
        for chart in (app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart"))
    )


@pytest.mark.parametrize("dark_mode", [False, True])
def test_date_field_and_calendar_styles_follow_the_session_theme(
    monkeypatch, catalog_release, dark_mode
) -> None:
    configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(APP_PATH)
    app.session_state["dark_mode"] = dark_mode
    app.run(timeout=20)
    assert not app.exception
    theme = next(
        item.proto.body for item in app.get("html") if "--app-background:" in item.proto.body
    )
    assert ":root {" in theme
    assert '.stApp [data-testid="stDateInputField"]' in theme
    assert '[data-testid="stDateInputCalendar"][role="dialog"]' in theme
    assert '[data-type]:not([data-focused="true"])' in theme
    assert '[role="button"]:not(' in theme
    assert '[data-selected="true"], [data-disabled="true"], [data-focused="true"]' in theme
    assert f"--app-surface: {'#18232d' if dark_mode else '#e9eeea'};" in theme


def test_discovery_uses_yfinance_contract_and_discloses_requested_observed_dates(
    monkeypatch, catalog_release
) -> None:
    configure_ui(monkeypatch, catalog_release)
    provider_requests: list[str] = []

    def build_test_provider(provider_id, *args, **kwargs):
        provider_requests.append(provider_id)
        return DailyProvider([])

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "fixture")
    monkeypatch.setattr("market_leadership.bootstrap.build_request_provider", build_test_provider)
    app = AppTest.from_file(APP_PATH).run(timeout=20)
    assert not app.exception
    assert provider_requests == ["yfinance"]
    text = " ".join(str(item.value) for item in (*app.title, *app.caption, *app.markdown))
    assert "SOURCE YFINANCE" in text
    assert "REQUESTED" in text and "OBSERVED" in text
    assert any(widget.label == "As of" for widget in app.date_input)
    assert any(widget.label == "Refresh data" for widget in app.button)
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)


def test_discovery_provider_failure_is_visible_without_fallback(monkeypatch, catalog_release):
    configure_ui(monkeypatch, catalog_release)

    def fail_provider(*args, **kwargs):
        raise RuntimeError("controlled provider failure")

    monkeypatch.setattr("market_leadership.bootstrap.build_request_provider", fail_provider)
    app = AppTest.from_file(APP_PATH).run(timeout=20)
    assert any("could not be loaded" in item.value for item in app.error)
    assert any("controlled provider failure" in item.message for item in app.exception)
    assert not app.dataframe
    assert not app.get("arrow_vega_lite_chart")
