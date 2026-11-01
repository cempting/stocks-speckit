from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.application.score_industry import IndustryScoreResult, StockScoreEvidence
from market_leadership.domain.peer_scores import (
    BlockPeerScore,
    MetricPeerScore,
    PeerScorecard,
)
from market_leadership.domain.stock_selection import MembershipEntry
from tests.fixtures.catalogs.ui import DailyProvider, configure_ui, detail_release

ROOT = Path(__file__).parents[2]


def _score_result(members: tuple[MembershipEntry, ...]) -> IndustryScoreResult:
    metric = MetricPeerScore("metric", 1.0, 75.0, 5, "available")
    quality = BlockPeerScore("Quality", 75.0, "available", (metric, metric))
    growth = BlockPeerScore("Growth", 75.0, "available", (metric, metric))
    cash_flow = BlockPeerScore("Cash Flow", 75.0, "available", (metric, metric))
    stocks = tuple(
        StockScoreEvidence(
            member.instrument_id,
            PeerScorecard(member.instrument_id, quality, growth, cash_flow),
            "available",
        )
        for member in members
    )
    return IndustryScoreResult(
        date(2026, 10, 30),
        tuple(member.instrument_id for member in members),
        stocks,
    )


def _run_app(monkeypatch: pytest.MonkeyPatch, catalog_release: Path) -> AppTest:
    configure_ui(monkeypatch, detail_release(catalog_release))
    return AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )


def _select_cloud_industry(app: AppTest) -> AppTest:
    app.button(
        "market_leadership.progressive_discovery.sector_tape_select_test-technology"
    ).click().run(timeout=20)
    return (
        app.selectbox("market_leadership.progressive_discovery.industry")
        .select("test-cloud")
        .run(timeout=20)
    )


@pytest.mark.parametrize(
    "return_key", [None, "market_leadership.progressive_discovery.breadcrumb_industry"]
)
def test_stock_detail_uses_stable_identity_and_returns_to_industry(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path, return_key: str | None
) -> None:
    load_calls = 0

    def score(
        members: tuple[MembershipEntry, ...],
        *,
        cutoff: date,
        refresh: bool = False,
        cohort_fingerprint: str | None = None,
    ) -> IndustryScoreResult:
        nonlocal load_calls
        del cutoff, refresh, cohort_fingerprint
        load_calls += 1
        return _score_result(members)

    monkeypatch.setattr("market_leadership.application.score_industry.score_industry", score)
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)

    assert not app.exception
    assert load_calls == 0
    next(button for button in app.button if button.label == "Load peer scores").click().run(
        timeout=20
    )
    assert not app.exception
    assert load_calls == 1

    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)

    assert not app.exception
    assert any(item.value == "AAA · Alpha" for item in app.title), (
        f"titles={[item.value for item in app.title]}, "
        f"subheaders={[item.value for item in app.subheader]}, "
        f"errors={[item.value for item in app.error]}"
    )
    assert any(item.value == "Peer scorecard" for item in app.subheader)
    assert [metric.value for metric in app.metric] == ["75.0", "75.0", "75.0"]
    return_button = (
        app.button(return_key)
        if return_key
        else next(button for button in app.button if button.label == "Back to Discovery")
    )
    return_button.click().run(timeout=20)

    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert (
        app.session_state["market_leadership.progressive_discovery.sector"] == "test-technology"
    )
    assert app.selectbox("market_leadership.progressive_discovery.industry").value == "test-cloud"
    assert load_calls == 1


def test_changing_sector_clears_the_stock_and_industry_tape(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)
    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)
    app.button("market_leadership.progressive_discovery.breadcrumb_sectors").click().run(
        timeout=20
    )
    app.button(
        "market_leadership.progressive_discovery.sector_tape_select_test-financials"
    ).click().run(timeout=20)

    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Contained stocks" for item in app.subheader)
    assert app.selectbox("market_leadership.progressive_discovery.industry").value is None
    assert app.selectbox("market_leadership.progressive_discovery.industry").options == [
        "test-hardware"
    ]


def test_selecting_stock_row_opens_its_stable_identity(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)
    next(button for button in app.button if button.label == "BBB · Beta").click().run(timeout=20)

    assert not app.exception
    assert any(item.value == "BBB · Beta" for item in app.title)


def test_stock_detail_discloses_scores_until_explicitly_loaded(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)
    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run(timeout=20)

    assert not app.exception
    assert [metric.value for metric in app.metric] == [
        "Not loaded",
        "Not loaded",
        "Not loaded",
    ]


@pytest.mark.parametrize("missing", ["close", "volume"])
def test_detail_renders_available_series_when_other_series_is_missing(
    missing: str,
) -> None:
    def app_script(missing: str) -> None:
        from datetime import date

        import pandas as pd

        from market_leadership.domain.stock_chart import build_stock_chart_evidence
        from market_leadership.domain.stock_selection import MembershipEntry
        from market_leadership.ui.components.stock_detail import render_stock_detail

        history = pd.DataFrame(
            {"close": [10.0, 11.0], "volume": [100.0, 110.0]},
            index=pd.date_range("2026-10-22", periods=2),
        )
        history[missing] = float("nan")
        member = MembershipEntry(
            "instrument",
            "company",
            "AAA",
            "Alpha",
            "NASDAQ",
            "USD",
            "sector",
            "Sector",
            "industry",
            "Industry",
            date(2020, 1, 1),
            None,
        )
        render_stock_detail(
            member,
            build_stock_chart_evidence("instrument", history, as_of=date(2026, 10, 23)),
            scorecard=None,
            score_state="not_loaded",
            score_reason=None,
            dark_mode=False,
            on_return=lambda: None,
        )

    app = AppTest.from_function(app_script, args=(missing,)).run()
    assert not app.exception
    assert len(app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart")) == 1
    missing_label = "Price" if missing == "close" else "Volume"
    assert any(f"{missing_label}: Insufficient" == item.value for item in app.caption)


@pytest.mark.parametrize("missing", ["close", "volume"])
def test_independent_history_survives_member_tape_to_detail_pipeline(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path, missing: str
) -> None:
    class PartialProvider(DailyProvider):
        def fetch_daily_history(
            self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False
        ) -> dict[str, pd.DataFrame]:
            history = super().fetch_daily_history(symbols, start=start, end=end, force=force)
            for symbol in ("AAA", "BBB"):
                if symbol in history:
                    history[symbol][missing] = float("nan")
            return history

    app = _run_app(monkeypatch, catalog_release)
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: PartialProvider([]),
    )
    app = _select_cloud_industry(app)
    assert not app.exception
    available_label = "Price" if missing == "volume" else "Volume"
    missing_label = "Volume" if missing == "volume" else "Price"
    assert not any(item.value == f"{available_label} unavailable" for item in app.caption)
    assert sum(item.value == f"{missing_label} unavailable" for item in app.caption) == 2
    app.selectbox("market_leadership.progressive_discovery.stock_picker").select(
        "instrument-aaa"
    ).run()
    assert not app.exception
    assert len(app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart")) == 1
    assert any(item.value == f"{missing_label}: Insufficient" for item in app.caption)
