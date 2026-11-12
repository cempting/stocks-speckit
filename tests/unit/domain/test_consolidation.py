from datetime import date
from math import pi

import numpy as np
import pandas as pd
import pytest

import market_data.domain.consolidation as consolidation_module
from market_data.domain.consolidation import (
    _indicators,
    _rolling_prior_median,
    _wilder_smooth,
    detect_consolidation,
)


def _history(count: int) -> pd.DataFrame:
    positions = np.arange(count, dtype="float64")
    close = 100.0 + 0.5 * np.sin(positions * 2 * pi / 10)
    history = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(count, 100.0),
            "split_ratio": np.zeros(count),
        },
        index=pd.bdate_range("2020-01-02", periods=count, name="date"),
    )
    history.attrs["adjusted_ohlc"] = True
    history.attrs["volume_comparable"] = True
    history.attrs["source_id"] = "fixture"
    return history


def _detect(history: pd.DataFrame, *, as_of: date | None = None):
    cutoff = as_of or history.index[-1].date()
    return detect_consolidation("instrument-a", history, as_of=cutoff)


def _stub_quiet_indicators(
    monkeypatch: pytest.MonkeyPatch,
    *,
    adx: float = 19.0,
    bandwidth: float = 1.0,
    bandwidth_median: float = 1.0,
) -> None:
    def indicators(
        high: list[float], low: list[float], close: list[float]
    ) -> tuple[
        list[float | None],
        list[float | None],
        list[float | None],
        list[float | None],
    ]:
        count = len(close)
        first_candidate = min(271, count)
        return (
            [1.0] * count,
            [adx] * count,
            [bandwidth] * count,
            [None] * first_candidate + [bandwidth_median] * (count - first_candidate),
        )

    monkeypatch.setattr(consolidation_module, "_indicators", indicators)


def test_wilder_smoothing_uses_arithmetic_seed_then_recursive_update():
    actual = _wilder_smooth([float(value) for value in range(1, 16)], period=14)

    assert actual[:13] == [None] * 13
    assert actual[13] == pytest.approx(7.5)
    assert actual[14] == pytest.approx((13 * 7.5 + 15) / 14)


def test_adx_and_atr_reference_values_for_a_steady_rising_sequence():
    close = [100.0 + index for index in range(40)]
    atr, adx, _, _ = _indicators(
        [value + 2 for value in close],
        [value - 2 for value in close],
        close,
    )

    assert atr[13] is None
    assert atr[14] == pytest.approx(4.0)
    assert adx[26] is None
    assert adx[27] == pytest.approx(100.0)


def test_bollinger_width_uses_population_standard_deviation():
    values = [float(value) for value in range(1, 21)]
    _, _, bandwidth, _ = _indicators(
        [value + 1 for value in values],
        [value - 1 for value in values],
        values,
    )

    assert bandwidth[-1] == pytest.approx(
        100 * 4 * np.std(values, ddof=0) / np.mean(values)
    )


def test_prior_bandwidth_median_excludes_candidate_day():
    values = [float(value) for value in range(1, 253)] + [999.0]

    actual = _rolling_prior_median(values, lookback=252)

    assert actual[-2] is None
    assert actual[-1] == pytest.approx(126.5)


def test_detector_requires_271_prior_bandwidth_values_and_sufficient_warmup():
    short = _detect(_history(271))
    enough = _detect(_history(272))

    assert short.state == "insufficient"
    assert "bandwidth_baseline_insufficient" in short.reason_codes
    assert enough.state == "sufficient"
    assert not enough.intervals


@pytest.mark.parametrize(("count", "expected_intervals"), [(275, 0), (276, 1)])
def test_interval_requires_five_sessions_and_has_explicit_boundary(
    monkeypatch: pytest.MonkeyPatch, count: int, expected_intervals: int
):
    _stub_quiet_indicators(monkeypatch)
    result = _detect(_history(count))

    assert result.state == "sufficient"
    assert len(result.intervals) == expected_intervals
    if expected_intervals:
        interval = result.intervals[0]
        assert interval.duration_sessions == 5
        assert interval.start_boundary_truncated
        assert interval.observable_history_start == date(2020, 1, 2)


def test_volume_spike_uses_prior_twenty_sessions_and_threshold_equality_spikes(
    monkeypatch: pytest.MonkeyPatch,
):
    _stub_quiet_indicators(monkeypatch)
    history = _history(276)
    history.iloc[-1, history.columns.get_loc("volume")] = 200.0

    result = _detect(history)

    assert not result.intervals
    assert result.latest_volume_spike is True
    assert result.latest_volume_baseline == pytest.approx(100.0)


@pytest.mark.parametrize(
    ("adx", "bandwidth", "bandwidth_median", "expected_intervals"),
    [(20.0, 1.0, 1.0, 0), (19.0, 1.01, 1.0, 0), (19.0, 1.0, 1.0, 1)],
)
def test_quiet_session_threshold_equality_rules(
    monkeypatch: pytest.MonkeyPatch,
    adx: float,
    bandwidth: float,
    bandwidth_median: float,
    expected_intervals: int,
):
    _stub_quiet_indicators(
        monkeypatch, adx=adx, bandwidth=bandwidth, bandwidth_median=bandwidth_median
    )

    result = _detect(_history(276))

    assert len(result.intervals) == expected_intervals


def test_split_boundary_and_incomplete_split_evidence_are_insufficient():
    split = _history(276)
    split.iloc[-1, split.columns.get_loc("split_ratio")] = 4.0
    incomplete = _history(276)
    incomplete.iloc[-1, incomplete.columns.get_loc("split_ratio")] = np.nan

    assert "split_boundary" in _detect(split).reason_codes
    assert "split_evidence_incomplete" in _detect(incomplete).reason_codes


def test_zero_volume_baseline_is_insufficient_not_a_quiet_run():
    history = _history(300)
    history["volume"] = 0.0

    result = _detect(history)

    assert result.state == "insufficient"
    assert "volume_baseline_insufficient" in result.reason_codes


def test_detector_emits_maximal_run_and_observed_high_low_corridor(
    monkeypatch: pytest.MonkeyPatch,
):
    _stub_quiet_indicators(monkeypatch)
    history = _history(279)
    history.iloc[273, history.columns.get_loc("volume")] = 200.0
    history.iloc[276, history.columns.get_loc("high")] = 103.0
    history.iloc[276, history.columns.get_loc("low")] = 97.0

    result = _detect(history)

    assert len(result.intervals) == 1
    interval = result.intervals[0]
    assert interval.start_session == history.index[274].date()
    assert interval.end_session == history.index[278].date()
    assert interval.duration_sessions == 5
    assert interval.lower == 97.0
    assert interval.upper == 103.0
    assert interval.width_absolute == 6.0
    assert interval.width_pct == pytest.approx(100 * (103 / 97 - 1))
    assert interval.ongoing


def test_detector_has_no_maximum_duration_for_multi_year_runs(
    monkeypatch: pytest.MonkeyPatch,
):
    _stub_quiet_indicators(monkeypatch)
    result = _detect(_history(1100))

    assert len(result.intervals) == 1
    assert result.intervals[0].duration_sessions == 1100 - 271
    assert result.intervals[0].approx_calendar_duration > 365 * 2


def test_gap_resets_indicators_and_leaves_prior_interval_with_latest_insufficiency(
    monkeypatch: pytest.MonkeyPatch,
):
    _stub_quiet_indicators(monkeypatch)
    history = _history(600)
    history.loc[history.index[350], ["open", "high", "low", "close"]] = np.nan

    result = _detect(history)

    assert result.state == "insufficient"
    assert "history_gap" in result.reason_codes
    assert len(result.intervals) == 1
    assert result.intervals[0].end_session == history.index[349].date()


def test_future_rows_do_not_change_the_result_at_an_earlier_cutoff():
    history = _history(300)
    cutoff = history.index[275].date()
    truncated = history.loc[: history.index[275]]

    assert _detect(history, as_of=cutoff) == _detect(truncated, as_of=cutoff)


def test_interval_matching_distinguishes_latest_previous_and_older_runs(
    monkeypatch: pytest.MonkeyPatch,
):
    _stub_quiet_indicators(monkeypatch)
    history = _history(276)
    latest = _detect(history).intervals[0]
    next_sessions = pd.bdate_range(
        history.index[-1] + pd.offsets.BDay(1),
        periods=2,
    )
    missing_volume = pd.DataFrame(
        {
            "open": [100.0, 100.0],
            "high": [100.5, 100.5],
            "low": [99.5, 99.5],
            "close": [100.0, 100.0],
            "volume": [np.nan, np.nan],
            "split_ratio": [0.0, 0.0],
        },
        index=next_sessions,
    )
    missing_volume.attrs["volume_comparable"] = True
    missing_volume.attrs["adjusted_ohlc"] = True
    missing_volume.attrs["source_id"] = "fixture"
    previous_history = pd.concat([history, missing_volume.iloc[:1]])
    previous_history.attrs["volume_comparable"] = True
    previous = _detect(previous_history).intervals[0]
    older_history = pd.concat([history, missing_volume])
    older_history.attrs["volume_comparable"] = True
    older = _detect(older_history).intervals[0]

    assert latest.current_or_previous_session
    assert previous.current_or_previous_session
    assert not older.current_or_previous_session


def test_incomparable_volume_and_missing_ohlc_are_insufficient_not_inferred():
    incomparable = _history(300)
    incomparable.attrs["volume_comparable"] = False
    missing_ohlc = _history(300).drop(columns="high")

    assert "volume_not_comparable" in _detect(incomparable).reason_codes
    assert "missing_adjusted_ohlc" in _detect(missing_ohlc).reason_codes


def test_unverified_adjustment_or_source_is_insufficient():
    unadjusted = _history(300)
    unadjusted.attrs["adjusted_ohlc"] = False
    unidentified = _history(300)
    unidentified.attrs.pop("source_id")

    assert "adjusted_ohlc_unverified" in _detect(unadjusted).reason_codes
    assert "source_unidentified" in _detect(unidentified).reason_codes


def test_truncated_history_is_reported_in_detector_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    _stub_quiet_indicators(monkeypatch)
    history = _history(276)

    result = detect_consolidation(
        "instrument-a",
        history,
        as_of=history.index[-1].date(),
        history_truncated=True,
    )

    assert "history_truncated" in result.reason_codes
    assert result.intervals[0].start_boundary_truncated


@pytest.mark.parametrize(
    ("lookback", "multiplier"),
    [(0, 2.0), (20, 0.0), (20, float("inf"))],
)
def test_detector_rejects_invalid_volume_parameters(lookback: int, multiplier: float):
    with pytest.raises(ValueError, match="volume"):
        detect_consolidation(
            "instrument-a",
            _history(300),
            as_of=date(2021, 1, 1),
            volume_lookback=lookback,
            volume_multiplier=multiplier,
        )
