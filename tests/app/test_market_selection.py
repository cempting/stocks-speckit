from pathlib import Path

import pytest
from streamlit.proto.Block_pb2 import Block as BlockProto
from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import DailyProvider, configure_ui

APP_PATH = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"


@pytest.mark.parametrize("app_path", [APP_PATH, APP_PATH.parents[4] / "streamlit_app.py"])
def test_discovery_header_evenly_distributes_heading_date_and_refresh(
    monkeypatch, catalog_release, app_path
) -> None:
    configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(app_path).run(timeout=20)
    assert not app.exception
    heading = next(item for item in app.title if item.value == "Discovery")
    requested_date = next(widget for widget in app.date_input if widget.label == "As of")
    refresh = next(widget for widget in app.button if widget.label == "Refresh data")
    row = next(
        block for block in app.get("flex_container") if any(item is heading for item in block.title)
    )
    columns = list(row.children.values())
    assert len(columns) == 3
    assert all(column.type == "column" for column in columns)
    assert columns[0].title[0] is heading
    assert columns[1].date_input[0] is requested_date
    assert columns[2].button[0] is refresh
    assert [column.proto.weight for column in columns] == pytest.approx([1 / 3] * 3)
    assert all(column.proto.vertical_alignment == BlockProto.Column.BOTTOM for column in columns)


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
