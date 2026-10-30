import json

import pyarrow.ipc as ipc
import pytest
from streamlit.testing.v1 import AppTest

SCRIPT = """
from dataclasses import replace
import streamlit as st
from market_leadership.domain.fundamentals import build_scorecard
from market_leadership.infrastructure.fixture_provider import load_fundamental_fixture
from market_leadership.ui.components.fundamental_matrix import render_fundamental_matrix
card = build_scorecard(load_fundamental_fixture("SYN-A"))
{modification}
render_fundamental_matrix(card)
"""


def test_exact_matrix_and_native_chart_specifications():
    app = AppTest.from_string(SCRIPT.format(modification="")).run(timeout=20)
    assert not app.exception
    assert [heading.value for heading in app.subheader] == ["Quality", "Growth", "Cash Flow"]
    assert len(app.columns) == 3
    labels = [
        "Gross Margin",
        "Operating Margin",
        "ROCE",
        "Sales YoY",
        "EPS YoY",
        "EPS Consistency",
        "Cash Conversion",
        "FCF Margin",
    ]
    for column, expected in zip(app.columns, (labels[:3], labels[3:6], labels[6:]), strict=True):
        assert [item.value for item in column.markdown if item.value in labels] == expected
    assert any("Losing money on operations" == item.value for item in app.caption)
    charts = app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart")
    assert len(charts) == 8
    for chart in charts:
        specification = json.loads(chart.proto.spec)
        assert specification["height"] == 60
        assert specification["encoding"]["x"]["title"] == ""
        assert specification["encoding"]["y"]["title"] == ""
        data = ipc.open_stream(chart.proto.datasets[0].data.data).read_all().to_pandas()
        assert 4 <= len(data) <= 8
        assert data["Quarter"].is_monotonic_increasing
        assert data["Quarter"].is_unique


@pytest.mark.parametrize("index", range(8))
def test_single_missing_metric_preserves_exact_slots(index):
    modification = (
        f"items = list(card.metrics)\n"
        f"items[{index}] = replace(items[{index}], value=None, formatted='N/A', "
        f"commentary='Data not available', history=())\n"
        f"card = replace(card, metrics=tuple(items))"
    )
    app = AppTest.from_string(SCRIPT.format(modification=modification)).run(timeout=20)
    assert not app.exception
    assert sum(item.value == "Data not available" for item in app.caption) == 1
    assert sum(item.value == "**N/A**" for item in app.markdown) == 1
    assert len(app.subheader) == 3


def test_all_missing_long_commentary_and_short_history():
    modification = """
card = replace(card, metrics=tuple(
    replace(metric, value=None, formatted='N/A', commentary='Data not available', history=())
    for metric in card.metrics
))
"""
    app = AppTest.from_string(SCRIPT.format(modification=modification)).run(timeout=20)
    assert not app.exception
    assert sum(item.value == "Data not available" for item in app.caption) == 8
    assert not app.get("arrow_vega_lite_chart")
    modification = """
card = replace(card, metrics=tuple(
    replace(metric, commentary='Long interpretation ' * 50, history=metric.history[:3])
    for metric in card.metrics
))
"""
    app = AppTest.from_string(SCRIPT.format(modification=modification)).run(timeout=20)
    assert not app.exception
    assert sum(item.value == "Insufficient quarterly history" for item in app.caption) == 8
    assert sum(item.value.startswith("Long interpretation") for item in app.caption) == 8
    assert not any(item.value == "**N/A**" for item in app.markdown)


@pytest.mark.parametrize("count", [3, 4, 5, 8])
def test_native_chart_contains_exact_available_observations(count):
    modification = (
        "items = list(card.metrics)\n"
        f"items[0] = replace(items[0], history=items[0].history[:{count}])\n"
        "card = replace(card, metrics=tuple(items))"
    )
    app = AppTest.from_string(SCRIPT.format(modification=modification)).run(timeout=20)
    assert not app.exception
    charts = app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart")
    gross = [
        chart
        for chart in charts
        if json.loads(chart.proto.spec)["encoding"]["y"]["field"] == "Gross Margin"
    ]
    if count < 4:
        assert not gross
    else:
        points = ipc.open_stream(gross[0].proto.datasets[0].data.data).read_all()
        assert points.num_rows == count


@pytest.mark.parametrize("value", [-1.0, 9.0, 1.5, float("nan")])
def test_invalid_supplied_eps_count_is_never_displayed_as_valid(value):
    literal = "float('nan')" if value != value else repr(value)
    modification = (
        "items = list(card.metrics)\n"
        f"items[5] = replace(items[5], value={literal})\n"
        "card = replace(card, metrics=tuple(items))"
    )
    app = AppTest.from_string(SCRIPT.format(modification=modification)).run(timeout=20)
    assert not app.exception
    assert any(item.value == "**N/A**" for item in app.markdown)
    assert not any(item.value == "**8/8 quarters**" for item in app.markdown)
