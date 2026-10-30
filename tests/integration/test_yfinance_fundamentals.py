from datetime import date

import pandas as pd
import pytest

from market_leadership.domain.fundamentals import FundamentalRequest, build_scorecard
from market_leadership.infrastructure.yfinance_fundamentals import (
    FundamentalAcquisitionError,
    read_fundamentals,
)


class FakeTicker:
    info = {"symbol": "TEST", "financialCurrency": "USD"}
    quarterly_financials = pd.DataFrame(
        {pd.Timestamp("2026-06-30"): [100, 40, -5, 5, 10, 1]},
        index=[
            "Total Revenue",
            "Gross Profit",
            "Operating Income",
            "EBIT",
            "Net Income",
            "Diluted EPS",
        ],
    )
    quarterly_cashflow = pd.DataFrame(
        {pd.Timestamp("2026-06-30"): [12, -2]},
        index=["Operating Cash Flow", "Capital Expenditure"],
    )
    quarterly_balance_sheet = pd.DataFrame(
        {pd.Timestamp("2026-06-30"): [200, 100]},
        index=["Total Assets", "Current Liabilities"],
    )


def test_reader_constructs_one_ticker_and_normalizes_all_components():
    calls = []
    evidence = read_fundamentals(
        FundamentalRequest("TEST"),
        lambda symbol: calls.append(symbol) or FakeTicker(),
    )
    assert calls == ["TEST"]
    assert build_scorecard(evidence).metrics[0].value == 0.4


def test_empty_component_is_uncached_acquisition_error_with_safe_partial_evidence():
    class EmptyCash(FakeTicker):
        quarterly_cashflow = pd.DataFrame()

    with pytest.raises(FundamentalAcquisitionError, match="cash") as caught:
        read_fundamentals(FundamentalRequest("TEST"), lambda _: EmptyCash())
    assert caught.value.partial.income
    assert not caught.value.partial.cash


def test_retries_only_transient_component_errors():
    class Transient(FakeTicker):
        attempts = 0

        @property
        def quarterly_cashflow(self):
            self.attempts += 1
            if self.attempts == 1:
                raise TimeoutError("do not expose provider payload")
            return FakeTicker.quarterly_cashflow

    ticker = Transient()
    read_fundamentals(FundamentalRequest("TEST"), lambda _: ticker)
    assert ticker.attempts == 2


def test_historical_live_request_rejected_before_provider_call():
    with pytest.raises(ValueError, match="historical"):
        read_fundamentals(
            FundamentalRequest("TEST", cutoff=date(2020, 1, 1)),
            lambda _: pytest.fail("must not fetch historical live data"),
        )


@pytest.mark.parametrize("kind", ["basis", "currency", "scale", "duplicate", "future", "nat"])
def test_invalid_statement_context_is_explicit_and_localized(kind):
    class Invalid(FakeTicker):
        quarterly_cashflow = FakeTicker.quarterly_cashflow.copy()

    if kind == "basis":
        Invalid.quarterly_cashflow.attrs["period_basis"] = "year_to_date"
    elif kind == "currency":
        Invalid.quarterly_cashflow.attrs["currency"] = "EUR"
    elif kind == "scale":
        Invalid.quarterly_cashflow.attrs["scale"] = 1000
    elif kind == "duplicate":
        Invalid.quarterly_cashflow = pd.concat(
            [Invalid.quarterly_cashflow, Invalid.quarterly_cashflow], axis=1
        )
    elif kind == "future":
        Invalid.quarterly_cashflow.columns = [pd.Timestamp("2099-12-31")]
    else:
        Invalid.quarterly_cashflow.columns = [pd.NaT]
    with pytest.raises(FundamentalAcquisitionError, match="quarterly_cashflow") as caught:
        read_fundamentals(FundamentalRequest("TEST"), lambda _: Invalid())
    assert caught.value.partial.income
    assert not caught.value.partial.cash


def test_ticker_initialization_failure_is_sanitized():
    def broken(_):
        raise RuntimeError("sensitive provider context")

    with pytest.raises(FundamentalAcquisitionError) as caught:
        read_fundamentals(FundamentalRequest("TEST"), broken)
    assert "sensitive" not in str(caught.value)


def test_no_cross_symbol_partial_evidence_on_identity_mismatch():
    class WrongSymbol(FakeTicker):
        info = {"symbol": "OTHER", "financialCurrency": "USD"}

    with pytest.raises(FundamentalAcquisitionError) as caught:
        read_fundamentals(FundamentalRequest("TEST"), lambda _: WrongSymbol())
    assert not caught.value.partial.income
