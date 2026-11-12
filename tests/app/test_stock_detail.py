from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from market_data.domain.peer_scores import (
    BlockPeerScore,
    MetricPeerScore,
    PeerScorecard,
)
from market_data.domain.stock_selection import MembershipEntry
from market_leadership.application.score_industry import IndustryScoreResult, StockScoreEvidence
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
    return app.button(
        "market_leadership.progressive_discovery.industry_tape_select_test-cloud"
    ).click().run(timeout=20)


def _select_stock(app: AppTest, instrument_id: str) -> AppTest:
    return app.button(
        f"market_leadership.progressive_discovery.stock_tape_select_{instrument_id}"
    ).click().run(timeout=20)


@pytest.mark.parametrize(
    "return_key", [None, "market_leadership.progressive_discovery.breadcrumb_industry"]
)
def test_stock_detail_uses_stable_identity_and_returns_to_industry(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path, return_key: str | None
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)

    assert not app.exception
    assert not any(button.label == "Load peer scores" for button in app.button)
    app = _select_stock(app, "instrument-aaa")

    assert not app.exception
    assert any(item.value == "AAA · Alpha" for item in app.title), (
        f"titles={[item.value for item in app.title]}, "
        f"subheaders={[item.value for item in app.subheader]}, "
        f"errors={[item.value for item in app.error]}"
    )
    assert any(item.value == "Peer scorecard" for item in app.subheader)
    assert [metric.value for metric in app.metric] == ["Not loaded", "Not loaded", "Not loaded"]
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
    assert not any(
        widget.key
        in {
            "market_leadership.progressive_discovery.industry",
            "market_leadership.progressive_discovery.stock_picker",
        }
        for widget in app.selectbox
    )
    assert not any(widget.label == "Performance basis" for widget in app.segmented_control)
    assert not any(button.label == "Load peer scores" for button in app.button)


def test_changing_sector_clears_the_stock_and_industry_tape(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)
    app = _select_stock(app, "instrument-aaa")
    app.button("market_leadership.progressive_discovery.breadcrumb_sectors").click().run(
        timeout=20
    )
    app.button(
        "market_leadership.progressive_discovery.sector_tape_select_test-financials"
    ).click().run(timeout=20)

    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Contained stocks" for item in app.subheader)
    assert any(
        button.key
        == "market_leadership.progressive_discovery.industry_tape_select_test-hardware"
        for button in app.button
    )


def test_selecting_stock_row_opens_its_stable_identity(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)
    next(button for button in app.button if button.label == "**BBB**  \nBeta").click().run(
        timeout=20
    )

    assert not app.exception
    assert any(item.value == "BBB · Beta" for item in app.title)


def test_stock_detail_scores_remain_not_loaded_without_peer_score_action(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    app = _run_app(monkeypatch, catalog_release)
    app = _select_cloud_industry(app)
    app = _select_stock(app, "instrument-aaa")

    assert not app.exception
    assert not any(button.label == "Load peer scores" for button in app.button)
    assert [metric.value for metric in app.metric] == [
        "Not loaded",
        "Not loaded",
        "Not loaded",
    ]


def test_local_stock_lookup_opens_exact_listing_without_industry_prefetch(
    monkeypatch: pytest.MonkeyPatch, catalog_release: Path
) -> None:
    history_calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        "market_leadership.bootstrap.load_selected_stock_history",
        lambda *_args, **_kwargs: history_calls.append(("selected history",)),
    )
    configure_ui(monkeypatch, detail_release(catalog_release))
    app = AppTest.from_file(ROOT / "streamlit_app.py").run(timeout=20)
    app = _select_cloud_industry(app)
    app = _select_stock(app, "instrument-aaa")
    app.text_input("market_leadership.stock_lookup.lookup_query").set_value("AAA").run(
        timeout=20
    )
    app.selectbox("market_leadership.stock_lookup.lookup_instrument").select(
        "instrument-aaa"
    ).run(timeout=20)
    listing_picker = app.selectbox("market_leadership.stock_lookup.lookup_listing")
    assert listing_picker.options
    listing_picker.select(listing_picker.options[0]).run(timeout=20)
    next(button for button in app.button if button.label == "Open stock detail").click().run(
        timeout=20
    )

    assert not app.exception
    assert any(item.value == "AAA · Alpha" for item in app.title)
    assert any("industry membership is not required" in item.value for item in app.caption)
    assert history_calls == []


@pytest.mark.parametrize("missing", ["close", "volume"])
def test_detail_renders_available_series_when_other_series_is_missing(
    missing: str,
) -> None:
    def app_script(missing: str) -> None:
        from datetime import date

        import pandas as pd

        from market_data.domain.stock_chart import build_stock_chart_evidence
        from market_data.domain.stock_selection import MembershipEntry
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


def test_chart_period_choices_and_selection_reset_for_new_listing() -> None:
    def app_script() -> None:
        from datetime import date

        import pandas as pd
        import streamlit as st

        from market_data.domain.stock_chart import build_stock_chart_evidence
        from market_data.domain.stock_selection import MembershipEntry
        from market_leadership.ui.components.stock_detail import render_stock_detail

        instrument_id = st.selectbox("Selected listing", ["instrument-aaa", "instrument-bbb"])
        symbol = "AAA" if instrument_id.endswith("aaa") else "BBB"
        history = pd.DataFrame(
            {"close": range(1, 801), "volume": [1000.0] * 800},
            index=pd.bdate_range("2023-01-02", periods=800),
        )
        member = MembershipEntry(
            instrument_id,
            f"company-{symbol.lower()}",
            symbol,
            f"Company {symbol}",
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
            build_stock_chart_evidence(
                instrument_id, history, as_of=date(2026, 10, 23)
            ),
            scorecard=None,
            score_state="not_loaded",
            score_reason=None,
            dark_mode=False,
            on_return=lambda: None,
            widget_key_prefix="test.stock_detail.",
        )

    app = AppTest.from_function(app_script).run()
    assert not app.exception
    period = app.selectbox("test.stock_detail.chart_range")
    assert period.options == ["1m", "3m", "6m", "12m", "18m", "24m"]
    assert period.value == "6m"

    app = period.select("1m").run()
    assert not app.exception
    assert app.session_state["test.stock_detail.chart_range"] == "1m"

    app = app.selectbox[0].select("instrument-bbb").run()
    assert not app.exception
    assert app.selectbox("test.stock_detail.chart_range").value == "6m"
    assert app.session_state["test.stock_detail.chart_range"] == "6m"


def test_consolidation_selection_defaults_to_latest_and_does_not_change_chart_period() -> None:
    import json

    from market_data.domain.consolidation import (
        ConsolidationInterval,
        ConsolidationResult,
        VolumeContext,
    )

    history_index = pd.bdate_range(end="2026-10-23", periods=800)

    def interval(interval_id: str, start: date, end: date) -> ConsolidationInterval:
        return ConsolidationInterval(
            interval_id=interval_id,
            instrument_id="instrument",
            detector_version="quiet-sideways-v1",
            start_session=start,
            end_session=end,
            duration_sessions=5,
            approx_calendar_duration=(end - start).days + 1,
            lower=95.0,
            upper=105.0,
            width_absolute=10.0,
            width_pct=10.5,
            median_atr14=2.0,
            volume_context=VolumeContext(20, 2.0, 1000.0, 900.0, 0),
            as_of=date(2026, 10, 23),
            observable_history_start=history_index[0].date(),
            start_boundary_truncated=False,
            ongoing=False,
            current_or_previous_session=False,
        )

    older = interval(
        "older",
        history_index[50].date(),
        history_index[54].date(),
    )
    latest = interval(
        "latest",
        history_index[-5].date(),
        history_index[-1].date(),
    )
    result = ConsolidationResult(
        "instrument",
        "quiet-sideways-v1",
        date(2026, 10, 23),
        "synthetic",
        "sufficient",
        (),
        (older, latest),
        date(2026, 10, 23),
        10.0,
        2.0,
        1.0,
        1.2,
        1000.0,
        False,
    )

    def app_script(result) -> None:
        from datetime import date

        import pandas as pd

        from market_data.domain.stock_chart import build_stock_chart_evidence
        from market_data.domain.stock_selection import MembershipEntry
        from market_leadership.ui.components.stock_detail import render_stock_detail

        history_index = pd.bdate_range(end="2026-10-23", periods=800)
        history = pd.DataFrame(
            {
                "close": range(100, 900),
                "volume": [1000.0] * 800,
            },
            index=history_index,
        )
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
        chart = build_stock_chart_evidence(
            "instrument",
            history,
            as_of=date(2026, 10, 23),
            consolidation_result=result,
        )
        render_stock_detail(
            member,
            chart,
            scorecard=None,
            score_state="not_loaded",
            score_reason=None,
            dark_mode=False,
            on_return=lambda: None,
            widget_key_prefix="test.stock_detail.",
        )

    app = AppTest.from_function(app_script, args=(result,)).run()
    assert not app.exception
    interval_picker = app.selectbox("test.stock_detail.consolidation_interval")
    assert interval_picker.value == 0
    assert len(interval_picker.options) == 2
    assert interval_picker.options[0].startswith("Latest")
    assert any(latest.start_session.isoformat() in item.value for item in app.caption)
    chart_spec = json.loads(app.get("vega_lite_chart")[0].proto.spec)
    assert any(
        layer["mark"]["type"] == "rect" for layer in chart_spec["vconcat"][0]["layer"]
    )

    app = interval_picker.select(1).run()
    assert not app.exception
    assert app.selectbox("test.stock_detail.chart_range").value == "6m"
    assert any("outside the visible chart period" in item.value for item in app.info)
    chart_spec = json.loads(app.get("vega_lite_chart")[0].proto.spec)
    assert not any(
        layer["mark"]["type"] == "rect"
        for layer in chart_spec["vconcat"][0].get("layer", [])
    )


@pytest.mark.parametrize(
    ("state", "reason", "message_kind", "message"),
    [
        ("sufficient", (), "info", "No qualifying consolidation interval"),
        ("insufficient", ("volume_not_comparable",), "warning", "volume_not_comparable"),
    ],
)
def test_consolidation_distinguishes_no_interval_from_insufficient_evidence(
    state: Literal["sufficient", "insufficient"],
    reason: tuple[str, ...],
    message_kind: str,
    message: str,
) -> None:
    from market_data.domain.consolidation import ConsolidationResult

    def app_script(result) -> None:
        from datetime import date

        import pandas as pd

        from market_data.domain.stock_chart import build_stock_chart_evidence
        from market_data.domain.stock_selection import MembershipEntry
        from market_leadership.ui.components.stock_detail import render_stock_detail

        history = pd.DataFrame(
            {"close": [10.0, 11.0], "volume": [100.0, 110.0]},
            index=pd.date_range("2026-10-22", periods=2),
        )
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
        chart = build_stock_chart_evidence(
            "instrument",
            history,
            as_of=date(2026, 10, 23),
            consolidation_result=result,
        )
        render_stock_detail(
            member,
            chart,
            scorecard=None,
            score_state="not_loaded",
            score_reason=None,
            dark_mode=False,
            on_return=lambda: None,
            widget_key_prefix="test.stock_detail.",
        )

    detector_result = ConsolidationResult(
        "instrument",
        "quiet-sideways-v1",
        date(2026, 10, 23),
        "synthetic",
        state,
        reason,
        (),
        date(2026, 10, 23),
        None,
        None,
        None,
        None,
        None,
        None,
    )
    app = AppTest.from_function(app_script, args=(detector_result,)).run()

    assert not app.exception
    messages = app.info if message_kind == "info" else app.warning
    assert any(message in item.value for item in messages)
    assert not any(
        item.key == "test.stock_detail.consolidation_interval" for item in app.selectbox
    )


def test_company_evidence_controls_render_research_provenance_independently() -> None:
    def app_script() -> None:
        from datetime import UTC, date, datetime

        import pandas as pd

        from market_data.domain.company_evidence import CompanyEvidenceOutcome
        from market_data.domain.stock_chart import build_stock_chart_evidence
        from market_data.domain.stock_selection import StockIdentitySelection
        from market_leadership.application.load_company_evidence import (
            CompanyEvidenceLoadResult,
        )
        from market_leadership.ui.components.stock_detail import render_stock_detail
        from tests.company_evidence_helpers import research_claim, verified_association

        association = verified_association()
        captured_at = datetime(2026, 1, 2, 12, tzinfo=UTC)
        outcome = CompanyEvidenceOutcome(
            state="complete",
            observations=(),
            claims=(research_claim(association),),
            failures=(),
            started_at=captured_at,
            captured_at=captured_at,
            completed_at=captured_at,
            verified_association=association,
        )
        result = CompanyEvidenceLoadResult(association, outcome, None)
        selection = StockIdentitySelection(
            association.instrument_id,
            association.company_id,
            association.region_id,
            "Synthetic issuer",
            association.listing_id,
            association.provider_symbol,
            association.exchange,
            association.trading_currency,
        )
        render_stock_detail(
            selection,
            build_stock_chart_evidence(
                association.instrument_id,
                pd.DataFrame(columns=["close", "volume"]),
                as_of=date(2026, 1, 2),
            ),
            scorecard=None,
            score_state="not_loaded",
            score_reason=None,
            dark_mode=False,
            on_return=lambda: None,
            research_evidence=result,
            on_load_financial=lambda: None,
            on_load_research=lambda: None,
        )

    app = AppTest.from_function(app_script).run()
    assert not app.exception
    assert any(button.label == "Load financial evidence" for button in app.button)
    assert any(button.label == "Load stored business and moat claims" for button in app.button)
    assert any(
        "Synthetic management-reported subscription revenue" in item.value
        for item in app.markdown
    )
    assert any("management_claim" in item.value for item in app.caption)
    assert any("Business / Revenue model" in item.value for item in app.caption)
    assert any("https://issuer.example/annual-report" in item.value for item in app.caption)


def test_financial_history_shows_verified_size_eight_quarters_and_data_states() -> None:
    def app_script() -> None:
        from datetime import UTC, date, datetime
        from hashlib import sha256

        import pandas as pd

        from market_data.domain.company_evidence import (
            CompanyEvidenceOutcome,
            EvidenceProvenance,
            FinancialObservation,
        )
        from market_data.domain.stock_chart import build_stock_chart_evidence
        from market_data.domain.stock_selection import StockIdentitySelection
        from market_leadership.application.load_company_evidence import (
            CompanyEvidenceLoadResult,
        )
        from market_leadership.ui.components.stock_detail import render_stock_detail
        from tests.company_evidence_helpers import verified_association

        association = verified_association(
            instrument_id="instrument-a",
            listing_id="listing-a",
            provider_symbol="SYNTHETIC",
        )
        captured_at = datetime(2026, 4, 2, 12, tzinfo=UTC)
        period_ends = (
            date(2024, 3, 31),
            date(2024, 6, 30),
            date(2024, 9, 30),
            date(2024, 12, 31),
            date(2025, 3, 31),
            date(2025, 6, 30),
            date(2025, 9, 30),
            date(2025, 12, 31),
            date(2026, 3, 31),
        )
        rows = {
            "revenue": 100.0,
            "gross_profit": 40.0,
            "operating_income": 10.0,
            "ebit": 12.0,
            "net_income": 5.0,
            "diluted_eps": 1.0,
            "ocf": 12.0,
            "capex": -2.0,
            "fcf": 10.0,
            "assets": 200.0,
            "current_assets": 150.0,
            "current_liabilities": 100.0,
            "total_debt": 80.0,
            "shareholders_equity": 100.0,
            "cash_and_equivalents": 25.0,
            "shares_outstanding": 100.0,
        }
        observations = []
        for period in period_ends:
            for metric_key, value in rows.items():
                if metric_key == "shares_outstanding" and period == period_ends[1]:
                    continue
                if metric_key == "cash_and_equivalents":
                    value = 0.0
                if metric_key == "net_income" and period == period_ends[-1]:
                    value = -5.0
                observations.append(
                    FinancialObservation(
                        observation_id=f"{metric_key}:{period.isoformat()}",
                        association_id=association.association_id,
                        metric_key=metric_key,
                        value=value,
                        unit="currency" if metric_key != "diluted_eps" else "currency_per_share",
                        currency="USD",
                        source_scale=1.0,
                        period_start=None,
                        period_end=period,
                        basis="quarterly",
                        origin="source_supplied",
                        definition=f"Source-provided {metric_key}",
                        derivation_input_ids=(),
                        provenance=EvidenceProvenance(
                            source_id="yfinance",
                            provider_id="yfinance",
                            assessment_fingerprint="a" * 64,
                            source_url=None,
                            locator=metric_key,
                            publication_date=None,
                            publication_precision="unknown",
                            observed_at=captured_at,
                            period_start=None,
                            period_end=period,
                            payload_sha256=sha256(b"synthetic financial observation").hexdigest(),
                            schema_revision="company-evidence-1",
                            limitations=(),
                        ),
                        state="available",
                        reason=None,
                    )
                )
        observations.append(
            FinancialObservation(
                observation_id="market-capitalization:2026-04-02",
                association_id=association.association_id,
                metric_key="market_capitalization",
                value=1_000_000_000.0,
                unit="currency",
                currency="USD",
                source_scale=1.0,
                period_start=None,
                period_end=date(2026, 4, 2),
                basis="unknown",
                origin="source_supplied",
                definition="Current market capitalization",
                derivation_input_ids=(),
                provenance=EvidenceProvenance(
                    source_id="yfinance",
                    provider_id="yfinance",
                    assessment_fingerprint="a" * 64,
                    source_url=None,
                    locator="marketCap",
                    publication_date=None,
                    publication_precision="unknown",
                    observed_at=captured_at,
                    period_start=None,
                    period_end=date(2026, 4, 2),
                    payload_sha256=sha256(b"synthetic market cap").hexdigest(),
                    schema_revision="company-evidence-1",
                    limitations=(),
                ),
                state="available",
                reason=None,
            )
        )
        observations.append(
            FinancialObservation(
                observation_id="derived:net_margin:2026-03-31",
                association_id=association.association_id,
                metric_key="net_margin",
                value=-0.05,
                unit="ratio",
                currency=None,
                source_scale=1.0,
                period_start=None,
                period_end=date(2026, 3, 31),
                basis="quarterly",
                origin="derived",
                definition="Net income / revenue",
                derivation_input_ids=("net_income:2026-03-31", "revenue:2026-03-31"),
                provenance=EvidenceProvenance(
                    source_id="yfinance",
                    provider_id="yfinance",
                    assessment_fingerprint="a" * 64,
                    source_url=None,
                    locator="derived/net_margin",
                    publication_date=None,
                    publication_precision="unknown",
                    observed_at=captured_at,
                    period_start=None,
                    period_end=date(2026, 3, 31),
                    payload_sha256=sha256(b"synthetic derived observation").hexdigest(),
                    schema_revision="company-evidence-1",
                    limitations=(),
                ),
                state="available",
                reason=None,
            )
        )
        outcome = CompanyEvidenceOutcome(
            state="partial",
            observations=tuple(observations),
            claims=(),
            failures=("Quarterly cash-flow coverage is partial",),
            started_at=captured_at,
            captured_at=captured_at,
            completed_at=captured_at,
            verified_association=association,
        )
        result = CompanyEvidenceLoadResult(association, outcome, None)
        selection = StockIdentitySelection(
            association.instrument_id,
            association.company_id,
            association.region_id,
            "Synthetic issuer",
            association.listing_id,
            association.provider_symbol,
            association.exchange,
            association.trading_currency,
        )
        render_stock_detail(
            selection,
            build_stock_chart_evidence(
                association.instrument_id,
                pd.DataFrame(columns=["close", "volume"]),
                as_of=date(2026, 4, 2),
            ),
            scorecard=None,
            score_state="not_loaded",
            score_reason=None,
            dark_mode=False,
            on_return=lambda: None,
            financial_evidence=result,
            on_load_financial=lambda: None,
        )

    app = AppTest.from_function(app_script).run()
    assert not app.exception
    rendered = "\n".join(
        [item.value for item in app.markdown]
        + [item.value for item in app.caption]
        + [item.value for item in app.warning]
        + [item.value for item in app.info]
    )
    assert "Market capitalization" in rendered
    assert "2026-04-02" in rendered
    assert "Derived" in rendered
    assert "Not reported" in rendered
    assert "-5" in rendered
    assert "Quarterly cash-flow coverage is partial" in rendered
    assert rendered.index("2026-03-31") < rendered.index("2025-12-31")
    assert "2024-03-31" not in rendered


@pytest.mark.parametrize("missing", ["close", "volume"])
def test_member_detail_does_not_use_unfiltered_batch_history(
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
    app = _select_stock(app, "instrument-aaa")
    assert not app.exception
    assert not app.get("vega_lite_chart")
    assert not app.get("arrow_vega_lite_chart")
    assert any(
        button.label == "Load continuity-filtered history" for button in app.button
    )
    assert any(item.value == "Price: Unavailable" for item in app.caption)
    assert any(item.value == "Volume: Unavailable" for item in app.caption)
