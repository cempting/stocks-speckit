from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.fixtures.catalogs.ui import configure_ui, edit_csv, publish_entry

APP = Path(__file__).parents[2] / "src/market_leadership/ui/workflows/discovery_page.py"


def test_discovery_uses_one_yfinance_path_and_discloses_dates(monkeypatch, catalog_release):
    calls = configure_ui(monkeypatch, catalog_release)
    app = AppTest.from_file(APP).run(timeout=20)
    assert not app.exception
    text = " ".join(str(item.value) for item in (*app.caption, *app.markdown))
    assert "SOURCE YFINANCE" in text
    assert "REQUESTED" in text and "OBSERVED" in text
    assert not any(widget.label in {"Discovery mode", "Data provider"} for widget in app.selectbox)
    assert calls == [("TEST_ETF",)]


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
