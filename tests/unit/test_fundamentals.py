from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from market_leadership.domain.fundamentals import (
    FinancialQuarter,
    FundamentalBundle,
    build_scorecard,
)


def bundle(count=12, **overrides):
    quarters = tuple(date(2023 + index // 4, (index % 4 + 1) * 3, 28) for index in range(count))
    income = tuple(
        FinancialQuarter(
            period,
            tuple(
                {
                    "revenue": 100.0,
                    "gross_profit": 40.0,
                    "operating_income": -5.0,
                    "ebit": 5.0,
                    "net_income": 10.0,
                    "diluted_eps": 1.0,
                    **overrides,
                }.items()
            ),
        )
        for period in quarters
    )
    cash = tuple(FinancialQuarter(period, (("ocf", 12.0), ("capex", -2.0))) for period in quarters)
    balance = tuple(
        FinancialQuarter(period, (("assets", 200.0), ("current_liabilities", 100.0)))
        for period in quarters
    )
    return FundamentalBundle("TEST", "fixture", datetime.now(UTC), "USD", income, cash, balance)


def metrics(evidence):
    return {metric.key: metric for metric in build_scorecard(evidence).metrics}


def test_exact_financial_formulas_and_provenance():
    result = metrics(bundle())
    assert len(result) == 8
    for key, value in {
        "gross_margin": 0.4,
        "operating_margin": -0.05,
        "roce": 0.2,
        "sales_yoy": 0.0,
        "eps_yoy": 0.0,
        "eps_consistency": 8,
        "cash_conversion": 1.2,
        "fcf_margin": 0.1,
    }.items():
        assert result[key].value == pytest.approx(value)
    assert result["eps_consistency"].formatted == "8/8 quarters"
    assert result["cash_conversion"].formatted == "120.0%"
    assert result["operating_margin"].commentary == "Losing money on operations"
    assert "derived" in result["fcf_margin"].detail


@pytest.mark.parametrize("positive_count", range(9))
def test_all_eps_counts(positive_count):
    evidence = bundle(8)
    income = tuple(
        replace(q, values=(*q.values[:-1], ("diluted_eps", 1.0 if i < positive_count else 0.0)))
        for i, q in enumerate(evidence.income)
    )
    assert metrics(replace(evidence, income=income))["eps_consistency"].formatted == (
        f"{positive_count}/8 quarters"
    )


@pytest.mark.parametrize("count", [3, 5, 7])
def test_incomplete_eps_window(count):
    assert metrics(bundle(count))["eps_consistency"].formatted == "N/A"


@pytest.mark.parametrize("value", [None, float("nan"), float("inf")])
def test_missing_nonfinite_values_are_localized(value):
    result = metrics(bundle(gross_profit=value))
    assert result["gross_margin"].formatted == "N/A"
    assert result["gross_margin"].commentary == "Data not available"
    assert result["operating_margin"].value == -0.05


@pytest.mark.parametrize("net_income", [0.0, -1.0])
def test_cash_conversion_denominator_does_not_hide_fcf(net_income):
    result = metrics(bundle(net_income=net_income))
    assert result["cash_conversion"].value is None
    assert result["fcf_margin"].value == 0.1


@pytest.mark.parametrize("source_count,expected", [(3, 3), (4, 4), (5, 5), (12, 8)])
def test_history_limits_and_raw_lookback(source_count, expected):
    result = metrics(bundle(source_count))
    assert len(result["gross_margin"].history) == expected
    assert len(result["sales_yoy"].history) == max(0, min(8, source_count - 4))
    assert len(result["eps_consistency"].history) == max(0, min(8, source_count - 7))
    assert len(result["roce"].history) == max(0, min(8, source_count - 3))


def test_gap_breaks_comparability_and_missing_latest_does_not_use_older_values():
    evidence = bundle(8)
    gapped = replace(evidence, income=(*evidence.income[:3], *evidence.income[4:]))
    assert metrics(gapped)["eps_consistency"].value is None
    assert metrics(gapped)["sales_yoy"].value is None
    assert metrics(replace(evidence, cash=evidence.cash[:-1]))["cash_conversion"].value is None


def test_negative_eps_baseline_is_unavailable_and_zero_numerator_is_valid():
    assert metrics(bundle(diluted_eps=-1.0))["eps_yoy"].value is None
    assert metrics(bundle(gross_profit=0.0))["gross_margin"].value == 0.0
