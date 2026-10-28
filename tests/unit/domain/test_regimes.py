import numpy as np
import pandas as pd
import pytest

from market_leadership.domain.regimes import calculate_market_sentiment


def _frame(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"close": closes},
        index=pd.bdate_range("2025-01-02", periods=len(closes)),
    )


@pytest.mark.parametrize(
    ("closes", "expected_slope", "expected_state", "expected_regime"),
    [
        ([100.0] * 150 + [90.0] * 20 + [110.0] * 20, 1 / 15, "Rising", "Bullish"),
        ([100.0] * 150 + [110.0] * 20 + [90.0] * 20, -1 / 15, "Falling", "Bearish"),
    ],
)
def test_sma150_and_ols_use_latest_twenty_averages(
    closes: list[float],
    expected_slope: float,
    expected_state: str,
    expected_regime: str,
) -> None:
    result = calculate_market_sentiment(_frame(closes), benchmark="LOCAL")

    assert result.benchmark == "LOCAL"
    assert result.close == closes[-1]
    assert result.sma150 == pytest.approx(100.0)
    assert result.normalized_slope_pct == pytest.approx(expected_slope, rel=1e-10)
    assert result.slope_state == expected_state
    assert result.regime == expected_regime


@pytest.mark.parametrize(
    ("step", "expected_slope", "expected_state", "expected_regime"),
    [
        (0.96, 0.024, "Flat", "Sideways"),
        (1.04, 0.026, "Rising", "Bullish"),
        (-0.96, -0.024, "Flat", "Sideways"),
        (-1.04, -0.026, "Falling", "Bearish"),
    ],
)
def test_trends_on_either_side_of_strict_thresholds(
    step: float,
    expected_slope: float,
    expected_state: str,
    expected_regime: str,
) -> None:
    closes = [4000.0 + step * (session - 93.5) for session in range(169)]

    result = calculate_market_sentiment(_frame(closes))

    assert result.sma150 == pytest.approx(4000.0)
    assert result.normalized_slope_pct == pytest.approx(expected_slope, rel=1e-10)
    assert result.slope_state == expected_state
    assert result.regime == expected_regime


@pytest.mark.parametrize("slope", [1.0, -1.0])
def test_exact_threshold_is_flat_even_when_close_crosses_average(
    monkeypatch: pytest.MonkeyPatch,
    slope: float,
) -> None:
    closes = [4000.0] * 169
    closes[19] -= 100.0 if slope > 0 else -100.0
    closes[-1] += 100.0 if slope > 0 else -100.0

    # Force an exact fitted slope so floating-point OLS noise cannot move an equality case.
    monkeypatch.setattr(
        "market_leadership.domain.regimes.np.polyfit",
        lambda x, y, degree: np.array([slope, 0.0]),
    )
    result = calculate_market_sentiment(_frame(closes))

    assert result.sma150 == 4000.0
    assert result.normalized_slope_pct == (0.025 if slope > 0 else -0.025)
    assert result.slope_state == "Flat"
    assert result.regime == "Sideways"


@pytest.mark.parametrize("count", [150, 168])
def test_undefined_slope_with_close_and_average_is_sideways(count: int) -> None:
    result = calculate_market_sentiment(_frame([100.0] * count))

    assert result.close == 100.0
    assert result.sma150 == 100.0
    assert result.normalized_slope_pct is None
    assert result.slope_state == "Undefined"
    assert result.regime == "Sideways"


def test_missing_interior_close_does_not_compress_sma_sessions() -> None:
    closes = [100.0] * 170
    closes[19] = float("nan")

    result = calculate_market_sentiment(_frame(closes))

    assert result.close == 100.0
    assert result.sma150 == 100.0
    assert result.normalized_slope_pct is None
    assert result.slope_state == "Undefined"
    assert result.regime == "Sideways"


@pytest.mark.parametrize(
    "closes",
    [
        [],
        [100.0] * 149,
        [float("nan")] * 169,
        [100.0] * 149 + [float("nan")],
        [100.0] * 169 + [float("nan")],
    ],
    ids=[
        "empty",
        "no-150-session-average",
        "missing-all-closes",
        "missing-close-and-average",
        "missing-latest-close",
    ],
)
def test_missing_close_or_average_is_insufficient(closes: list[float]) -> None:
    result = calculate_market_sentiment(_frame(closes))

    assert result.close is None
    assert result.sma150 is None
    assert result.normalized_slope_pct is None
    assert result.slope_state == "Undefined"
    assert result.regime == "Insufficient"
