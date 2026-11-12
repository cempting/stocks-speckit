from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import DailyProvider, configure_ui, edit_csv, publish_entry

APP = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"


def test_discovery_uses_one_yfinance_path_and_discloses_dates(monkeypatch, catalog_release):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(APP).run(timeout=20)
    assert not app.exception
    text = " ".join(str(item.value) for item in (*app.caption, *app.markdown))
    assert "SOURCE YFINANCE" in text
    assert "REQUESTED" in text and "OBSERVED" in text
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)
    assert not any(widget.label == "Search retained stock identities" for widget in app.text_input)
    assert calls == [("TEST_ETF",)]


def test_entity_details_expose_dates_without_changing_state_or_requests(
    monkeypatch, catalog_release
):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(APP).run(timeout=20)
    before = list(calls)
    details = app.get("expander")
    assert details
    text = "\n".join(element.value for details_row in details for element in details_row.text)
    assert "SOURCE YFINANCE" in text and "REQUESTED" in text and "OBSERVED" in text
    assert calls == before
    period = app.segmented_control("market_leadership.progressive_discovery.thumbnail_period")
    assert period.value == "3m"


def test_missing_purpose_benchmarks_are_explicit_and_never_defaulted(monkeypatch, catalog_release):
    calls = configure_ui(monkeypatch, catalog_release)
    edit_csv(catalog_release, "benchmarks", lambda rows: rows.clear())
    publish_entry(catalog_release)
    app = AppTest.from_file(APP).run(timeout=20)
    assert not app.exception
    messages = " ".join(item.value for item in (*app.error, *app.warning))
    assert "sp500_comparison" in messages and "market_sentiment" in messages
    assert all("SPY" not in symbols for symbols in calls)


def test_comparison_and_sentiment_use_independent_file_listings(monkeypatch, catalog_release):
    def listings(rows):
        original = dict(rows[0])
        for purpose in ("COMPARISON", "SENTIMENT"):
            rows.append(
                dict(
                    original,
                    ListingId=f"test-{purpose.lower()}",
                    InstrumentId=f"test-{purpose.lower()}-instrument",
                    Ticker=f"TEST_{purpose}",
                    ProviderSymbol=f"TEST_{purpose}",
                )
            )

    edit_csv(catalog_release, "etf_listings", listings)
    edit_csv(
        catalog_release,
        "benchmarks",
        lambda rows: [
            row.update(
                ListingId="test-comparison"
                if row["Purpose"] == "sp500_comparison"
                else "test-sentiment"
            )
            for row in rows
        ],
    )
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(APP).run(timeout=20)
    assert not app.exception
    assert set(calls[0]) == {"TEST_COMPARISON", "TEST_SENTIMENT", "TEST_ETF"}


@pytest.mark.parametrize("stale", [False, True])
def test_daily_controls_reuse_existing_requests_and_ignore_incomplete_future_prices(
    monkeypatch, catalog_release, stale
):
    from market_leadership.application import market_sessions
    from market_leadership.ui.workflows import discovery_page

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            current = datetime(2026, 10, 30, 19, tzinfo=UTC)
            return current.astimezone(tz) if tz is not None else current.replace(tzinfo=None)

    class EvidenceProvider(DailyProvider):
        def fetch_daily_history(self, symbols, *, start, end, force=False):
            frames = super().fetch_daily_history(symbols, start=start, end=end, force=force)
            for symbol, frame in frames.items():
                frame.loc[pd.Timestamp("2026-10-28"), "close"] = 100.0
                frame.loc[pd.Timestamp("2026-10-29"), "close"] = 102.0
                frame.loc[pd.Timestamp("2026-10-30"), "close"] = 10000.0
                if stale:
                    frame = frame.loc[frame.index.date <= date(2026, 10, 28)].copy()
                frame.loc[pd.Timestamp("2026-11-02")] = [10000.0, 1000]
                frames[symbol] = frame
            return frames

    calls = configure_ui(monkeypatch, catalog_release)
    monkeypatch.setattr(market_sessions, "datetime", FrozenDatetime)
    monkeypatch.setattr(discovery_page, "datetime", FrozenDatetime)
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: EvidenceProvider(calls),
    )
    prefix = "market_leadership.progressive_discovery."

    def render():
        from market_leadership.ui.workflows.discovery_page import render_discovery

        render_discovery()

    app = AppTest.from_function(render).run(timeout=20)
    assert not app.exception
    assert app.date_input[0].value == date(2026, 10, 30)
    assert calls == [("TEST_ETF",)]

    def cells():
        return [
            element.proto.body
            for element in app.get("html")
            if "font-variant-numeric: tabular-nums" in element.proto.body
        ]

    if stale:
        assert "Unavailable" in cells()[0]
        assert "1d:" in app.button(prefix + "sector_tape_select_test-sector").help
        assert "2026-10-29" in app.button(prefix + "sector_tape_select_test-sector").help
    else:
        assert "2.00%" in cells()[0]
    assert any("stale or insufficient" in item.value for item in app.warning)
    for level in ("sector", "industry"):
        original = cells()
        symbols = calls[-1]
        for period in ("1w", "1m", "3m", "6m", "1y"):
            count = len(calls)
            app.segmented_control(prefix + "thumbnail_period").set_value(period).run()
            assert not app.exception
            assert len(calls) == count + 1
            assert calls[-1] == symbols
            assert cells() == original
        count = len(calls)
        app.segmented_control(prefix + "performance_basis").set_value("vs S&P 500").run()
        assert not app.exception
        assert len(calls) == count + 1 and calls[-1] == symbols
        if level == "sector" and not stale:
            assert "0.00%" in cells()[0]
        app.segmented_control(prefix + "performance_basis").set_value("Absolute").run()
        assert cells() == original
        assert calls[-1] == symbols
        if level == "sector":
            app.button(prefix + "sector_tape_select_test-sector").click().run()
            assert not app.exception
            assert app.session_state[prefix + "sector"] == "test-sector"
            assert set(calls[-1]) == {"TEST_ETF", "TEST_INVENTORY"}
    app.button(prefix + "breadcrumb_sectors").click().run()
    assert not app.exception
    assert calls[-1] == ("TEST_ETF",)
    assert app.segmented_control(prefix + "thumbnail_period").value == "1y"
    assert app.segmented_control(prefix + "performance_basis").value == "Absolute"
