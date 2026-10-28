from datetime import date

import pandas as pd
import pytest

from market_leadership.domain.relative_strength import (
    MissingStrengthReason,
    calculate_relative_strength,
)


def _closes(start: str = "2025-10-24", end: str = "2026-10-26") -> pd.Series:
    return pd.Series(100.0, index=pd.bdate_range(start, end))


def _strength(entry: pd.Series, benchmark: pd.Series, **kwargs: str):
    return calculate_relative_strength(
        entry,
        benchmark,
        as_of=date(2026, 10, 26),
        currency=kwargs.get("currency", "USD"),
        benchmark_currency=kwargs.get("benchmark_currency", "USD"),
        return_basis=kwargs.get("return_basis", "ADJUSTED_CLOSE"),
        benchmark_return_basis=kwargs.get("benchmark_return_basis", "ADJUSTED_CLOSE"),
    )


def test_five_aligned_returns_and_weighted_composite() -> None:
    entry, benchmark = _closes(), _closes()
    targets = {
        "1w": "2026-10-19",
        "1m": "2026-09-26",
        "3m": "2026-07-26",
        "6m": "2026-04-26",
        "12m": "2025-10-26",
    }
    for period, target in targets.items():
        index = entry.loc[:target].index[-1]
        entry.loc[index] = {"1w": 80, "1m": 75, "3m": 50, "6m": 40, "12m": 25}[period]
        benchmark.loc[index] = 50
    result = _strength(entry, benchmark)
    assert result.missing_reasons == ()
    assert result.ending_on == date(2026, 10, 26)
    for period, target in targets.items():
        start = entry.loc[:target].index[-1]
        assert result.starting_on[period] == start.date()
        absolute = 100 / entry.loc[start] - 1
        assert result.absolute[period] == pytest.approx(absolute)
        assert result.relative[period] == pytest.approx(absolute - (100 / 50 - 1))
    assert result.composite == pytest.approx(
        0.4 * result.relative["3m"] + 0.3 * result.relative["6m"] + 0.3 * result.relative["12m"]
    )


def test_no_shared_latest_ending_observation_does_not_compare_stale_prices() -> None:
    entry = _closes()
    benchmark = _closes().drop(pd.Timestamp("2026-10-26"))
    result = _strength(entry, benchmark)
    assert result.composite is None
    assert result.ending_on is None
    assert result.missing_reasons == (MissingStrengthReason.NO_SHARED_END,)


def test_lookback_uses_last_shared_start_not_separate_start_dates() -> None:
    entry, benchmark = _closes(), _closes()
    benchmark = benchmark.drop(pd.Timestamp("2026-10-19"))
    entry.loc["2026-10-16"] = 80
    benchmark.loc["2026-10-16"] = 50
    result = _strength(entry, benchmark)
    assert result.starting_on["1w"] == date(2026, 10, 16)
    assert result.absolute["1w"] == pytest.approx(0.25)
    assert result.relative["1w"] == pytest.approx(-0.75)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("benchmark_currency", "JPY", MissingStrengthReason.CURRENCY_MISMATCH),
        ("benchmark_return_basis", "CLOSE", MissingStrengthReason.RETURN_BASIS_MISMATCH),
    ],
)
def test_mismatched_comparison_basis_is_not_calculated(
    field: str, value: str, reason: MissingStrengthReason
) -> None:
    result = _strength(_closes(), _closes(), **{field: value})
    assert result.absolute == {}
    assert result.relative == {}
    assert result.composite is None
    assert result.missing_reasons == (reason,)


def test_missing_twelve_month_start_keeps_shorter_returns_but_no_composite() -> None:
    result = _strength(_closes("2026-01-01"), _closes("2026-01-01"))
    assert set(result.absolute) == {"1w", "1m", "3m", "6m"}
    assert result.composite is None
    assert result.missing_reasons == (MissingStrengthReason.MISSING_12M,)


def test_missing_shared_start_excludes_only_affected_period() -> None:
    entry, benchmark = _closes(), _closes()
    entry = entry.loc["2026-08-01":]
    benchmark = benchmark.loc["2026-08-01":]
    result = _strength(entry, benchmark)
    assert "3m" not in result.relative
    assert MissingStrengthReason.MISSING_3M in result.missing_reasons


def test_invalid_prices_and_ambiguous_dates_are_rejected() -> None:
    entry = _closes()
    entry.iloc[-1] = 0
    with pytest.raises(ValueError, match="positive"):
        _strength(entry, _closes())
    with pytest.raises(ValueError, match="unique"):
        _strength(pd.concat([_closes(), _closes().iloc[-1:]]), _closes())
