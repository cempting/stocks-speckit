import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import load_fundamental_fixture
from market_leadership.infrastructure.stock_membership import FIXTURE_CATALOG
from market_leadership.infrastructure.yfinance_fundamentals import FundamentalAcquisitionError

ROOT = Path(__file__).parents[2]


def test_fixture_loading_pagination_and_evidence_invalidation(monkeypatch, tmp_path):
    monkeypatch.setenv("MARKET_LEADERSHIP_SNAPSHOT_DIR", str(tmp_path))
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    stocks = [f"SYN-{letter}" for letter in "ABCDEF"]
    app.multiselect(key="market_leadership.screening.stocks").set_value(stocks).run(timeout=20)
    assert not app.exception
    assert not any(item.value == "#### SYN-A" for item in app.markdown)
    app.button(key="market_leadership.fundamentals.load").click().run(timeout=20)
    assert not app.exception
    assert sum(item.value.startswith("#### SYN-") for item in app.markdown) == 5
    assert not any(item.value == "#### SYN-F" for item in app.markdown)
    app.run(timeout=20)
    assert sum(item.value.startswith("#### SYN-") for item in app.markdown) == 5
    app.selectbox(key="market_leadership.fundamentals.page").select(2).run(timeout=20)
    assert not any(item.value.startswith("#### SYN-") for item in app.markdown)
    app.button(key="market_leadership.fundamentals.load").click().run(timeout=20)
    assert [item.value for item in app.markdown if item.value.startswith("#### SYN-")] == [
        "#### SYN-F"
    ]
    app.button(key="market_leadership.fundamentals.refresh").click().run(timeout=20)
    assert not app.exception
    assert any(item.value == "#### SYN-F" for item in app.markdown)
    app.selectbox(key="market_leadership.screening.industry").select("CHIPS").run(timeout=20)
    assert not any(item.value.startswith("#### SYN-") for item in app.markdown)
    app.selectbox(key="market_leadership.screening.mode").select("live").run(timeout=20)
    assert not app.exception
    assert app.error
    assert not any(item.value.startswith("#### SYN-") for item in app.markdown)


@pytest.mark.parametrize("expired", [False, True])
def test_live_actions_errors_and_expiry_do_not_silently_reuse_success(
    monkeypatch, tmp_path, expired
):
    document = json.loads(FIXTURE_CATALOG.read_text())
    document.update(
        evidence_mode="live",
        observation_date=date.today().isoformat(),
        approval_reference="reviewed-test",
        source_id="injected-test-only",
    )
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document))
    for key, value in {
        "MARKET_DATA_PROVIDER": "yfinance",
        "MARKET_DATA_PROVIDERS": "yfinance",
        "STOCK_MEMBERSHIP_CATALOG": str(path),
        "FUNDAMENTAL_DISPLAY_APPROVAL": "reviewed-test",
        "MARKET_LEADERSHIP_SNAPSHOT_DIR": str(tmp_path / "snapshots"),
    }.items():
        monkeypatch.setenv(key, value)
    calls = []
    failing = False

    def injected(request, *, refresh=False):
        calls.append((request.symbol, refresh))
        evidence = replace(
            load_fundamental_fixture(request.symbol),
            provider_id="yfinance",
            fetched_at=datetime.now(UTC) - timedelta(hours=2 if expired else 0),
        )
        if failing and request.symbol == "SYN-A":
            raise FundamentalAcquisitionError(
                ("quarterly_financials: test failure",),
                replace(evidence, income=(), warnings=("Partial failed request",)),
            )
        return evidence

    monkeypatch.setattr(
        "market_leadership.ui.workflows.fundamental_grading.load_selected_fundamentals",
        injected,
    )
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    app.selectbox(key="market_leadership.screening.mode").select("live").run(timeout=20)
    app.multiselect(key="market_leadership.screening.stocks").set_value(["SYN-A", "SYN-B"]).run(
        timeout=20
    )
    assert not calls
    app.button(key="market_leadership.fundamentals.load").click().run(timeout=20)
    assert not app.exception
    assert calls == [("SYN-A", False), ("SYN-B", False)]
    app.run(timeout=20)
    assert len(calls) == 2
    if expired:
        assert any("expired" in item.value for item in app.warning)
        assert not any(item.value.startswith("#### SYN-") for item in app.markdown)
    else:
        failing = True
        app.button(key="market_leadership.fundamentals.refresh").click().run(timeout=20)
        assert calls[-2:] == [("SYN-A", True), ("SYN-B", True)]
        assert app.error
        app.run(timeout=20)
        assert len(calls) == 4
        assert not any(item.value == "#### SYN-A" for item in app.markdown)
        assert any(item.value == "#### SYN-B" for item in app.markdown)
        assert app.error
