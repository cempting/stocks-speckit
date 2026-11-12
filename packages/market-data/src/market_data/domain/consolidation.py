"""Versioned quiet-sideways consolidation evidence from adjusted daily history."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from math import isfinite
from statistics import median
from typing import Literal

import pandas as pd

QUIET_SIDEWAYS_VERSION = "quiet-sideways-v1"
_ATR_ADX_PERIOD = 14
_BOLLINGER_PERIOD = 20
_BANDWIDTH_LOOKBACK = 252
_MINIMUM_WARMUP_SESSIONS = 150
CONSOLIDATION_HISTORY_WARMUP_SESSIONS = _BOLLINGER_PERIOD + _BANDWIDTH_LOOKBACK - 1

DetectorState = Literal["sufficient", "insufficient"]


@dataclass(frozen=True, slots=True)
class VolumeContext:
    lookback_sessions: int
    spike_multiplier: float
    median_session_volume: float
    median_prior_volume: float
    spike_sessions: int


@dataclass(frozen=True, slots=True)
class ConsolidationInterval:
    interval_id: str
    instrument_id: str
    detector_version: str
    start_session: date
    end_session: date
    duration_sessions: int
    approx_calendar_duration: int
    lower: float
    upper: float
    width_absolute: float
    width_pct: float
    median_atr14: float
    volume_context: VolumeContext
    as_of: date
    observable_history_start: date
    start_boundary_truncated: bool
    ongoing: bool
    current_or_previous_session: bool


@dataclass(frozen=True, slots=True)
class ConsolidationResult:
    instrument_id: str
    detector_version: str
    as_of: date
    source_id: str | None
    state: DetectorState
    reason_codes: tuple[str, ...]
    intervals: tuple[ConsolidationInterval, ...]
    observed_through: date | None
    latest_adx14: float | None
    latest_atr14: float | None
    latest_bandwidth: float | None
    latest_bandwidth_median: float | None
    latest_volume_baseline: float | None
    latest_volume_spike: bool | None


def _wilder_smooth(values: Sequence[float | None], period: int) -> list[float | None]:
    if period < 1:
        raise ValueError("Wilder period must be positive")

    result: list[float | None] = [None] * len(values)
    seed: list[float] = []
    previous: float | None = None
    for index, value in enumerate(values):
        if value is None:
            seed.clear()
            previous = None
            continue
        if not isfinite(value):
            raise ValueError("Wilder inputs must be finite or missing")
        if previous is None:
            seed.append(value)
            if len(seed) == period:
                previous = sum(seed) / period
                result[index] = previous
            continue
        previous = ((period - 1) * previous + value) / period
        result[index] = previous
    return result


def _rolling_prior_median(
    values: Sequence[float | None], lookback: int
) -> list[float | None]:
    if lookback < 1:
        raise ValueError("Bandwidth lookback must be positive")
    previous_values: deque[float] = deque(maxlen=lookback)
    result: list[float | None] = []
    for value in values:
        result.append(
            median(previous_values)
            if value is not None and len(previous_values) == lookback
            else None
        )
        if value is not None:
            if not isfinite(value):
                raise ValueError("Bandwidth inputs must be finite or missing")
            previous_values.append(value)
    return result


def _indicators(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
) -> tuple[list[float | None], list[float | None], list[float | None], list[float | None]]:
    true_range: list[float | None] = [None]
    positive_dm: list[float | None] = [None]
    negative_dm: list[float | None] = [None]
    for index in range(1, len(close)):
        up_move = high[index] - high[index - 1]
        down_move = low[index - 1] - low[index]
        true_range.append(
            max(
                high[index] - low[index],
                abs(high[index] - close[index - 1]),
                abs(low[index] - close[index - 1]),
            )
        )
        positive_dm.append(up_move if up_move > 0 and up_move > down_move else 0.0)
        negative_dm.append(down_move if down_move > 0 and down_move > up_move else 0.0)

    atr = _wilder_smooth(true_range, _ATR_ADX_PERIOD)
    smooth_positive = _wilder_smooth(positive_dm, _ATR_ADX_PERIOD)
    smooth_negative = _wilder_smooth(negative_dm, _ATR_ADX_PERIOD)
    dx: list[float | None] = []
    for tr, plus, minus in zip(atr, smooth_positive, smooth_negative, strict=True):
        if tr is None or plus is None or minus is None or tr <= 0:
            dx.append(None)
            continue
        plus_di = 100 * plus / tr
        minus_di = 100 * minus / tr
        denominator = plus_di + minus_di
        dx.append(100 * abs(plus_di - minus_di) / denominator if denominator > 0 else None)
    adx = _wilder_smooth(dx, _ATR_ADX_PERIOD)

    close_series = pd.Series(close, dtype="float64")
    middle = close_series.rolling(_BOLLINGER_PERIOD, min_periods=_BOLLINGER_PERIOD).mean()
    deviation = close_series.rolling(_BOLLINGER_PERIOD, min_periods=_BOLLINGER_PERIOD).std(ddof=0)
    bandwidth = [
        400 * float(std) / float(mean_value)
        if pd.notna(std) and pd.notna(mean_value) and float(mean_value) > 0
        else None
        for mean_value, std in zip(middle, deviation, strict=True)
    ]
    return atr, adx, bandwidth, _rolling_prior_median(bandwidth, _BANDWIDTH_LOOKBACK)


def _numeric_column(history: pd.DataFrame, column: str) -> list[float | None]:
    converted = pd.to_numeric(history[column], errors="coerce")
    values: list[float | None] = []
    for value in converted:
        if pd.isna(value):
            values.append(None)
            continue
        number = float(value)
        if not isfinite(number):
            raise ValueError(f"{column} values must be finite or missing")
        values.append(number)
    return values


def _required_float_slice(
    values: Sequence[float | None], start: int, end: int
) -> list[float]:
    result: list[float] = []
    for value in values[start:end]:
        if value is None:
            raise ValueError("A valid interval cannot contain missing price evidence")
        result.append(value)
    return result


def _result_without_history(
    instrument_id: str,
    as_of: date,
    *,
    source_id: str | None,
    reason_codes: Sequence[str],
) -> ConsolidationResult:
    return ConsolidationResult(
        instrument_id=instrument_id,
        detector_version=QUIET_SIDEWAYS_VERSION,
        as_of=as_of,
        source_id=source_id,
        state="insufficient",
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        intervals=(),
        observed_through=None,
        latest_adx14=None,
        latest_atr14=None,
        latest_bandwidth=None,
        latest_bandwidth_median=None,
        latest_volume_baseline=None,
        latest_volume_spike=None,
    )


def detect_consolidation(
    instrument_id: str,
    history: pd.DataFrame,
    *,
    as_of: date,
    volume_lookback: int | bool = 20,
    volume_multiplier: float | bool = 2.0,
    volume_comparable: bool | None = None,
    history_truncated: bool | None = None,
) -> ConsolidationResult:
    """Detect maximal quiet-sideways intervals from completed adjusted sessions."""
    if not instrument_id.strip():
        raise ValueError("Consolidation evidence requires a stable instrument ID")
    if (
        isinstance(volume_lookback, bool)
        or volume_lookback < 1
        or isinstance(volume_multiplier, bool)
        or not isfinite(volume_multiplier)
        or volume_multiplier <= 0
    ):
        raise ValueError("Invalid volume lookback or spike multiplier")

    source_value = history.attrs.get("source_id")
    source_id = (
        source_value.strip()
        if isinstance(source_value, str) and source_value.strip()
        else None
    )
    if history.empty:
        return _result_without_history(
            instrument_id, as_of, source_id=source_id, reason_codes=("no_completed_history",)
        )

    try:
        sessions = pd.DatetimeIndex(history.index)
    except (TypeError, ValueError) as error:
        raise ValueError("Consolidation sessions must be datetime-indexed") from error
    if sessions.tz is not None:
        sessions = sessions.tz_localize(None)
    sessions = sessions.normalize()
    if sessions.has_duplicates:
        raise ValueError("Consolidation sessions must be unique")

    completed = history.copy()
    completed.index = sessions
    completed = completed.sort_index()
    completed = completed.loc[pd.DatetimeIndex(completed.index).date <= as_of]
    if completed.empty:
        return _result_without_history(
            instrument_id, as_of, source_id=source_id, reason_codes=("no_completed_history",)
        )

    required_ohlc = ("open", "high", "low", "close")
    if any(column not in completed.columns for column in required_ohlc):
        return _result_without_history(
            instrument_id,
            as_of,
            source_id=source_id,
            reason_codes=("missing_adjusted_ohlc",),
        )
    if "volume" not in completed.columns:
        return _result_without_history(
            instrument_id, as_of, source_id=source_id, reason_codes=("volume_history_missing",)
        )
    if "split_ratio" not in completed.columns:
        return _result_without_history(
            instrument_id,
            as_of,
            source_id=source_id,
            reason_codes=("split_evidence_unavailable",),
        )
    comparable = (
        volume_comparable
        if volume_comparable is not None
        else completed.attrs.get("volume_comparable") is True
    )
    truncated = (
        history_truncated
        if history_truncated is not None
        else completed.attrs.get("history_truncated") is True
    )
    if source_id is None:
        return _result_without_history(
            instrument_id, as_of, source_id=None, reason_codes=("source_unidentified",)
        )
    if completed.attrs.get("adjusted_ohlc") is not True:
        return _result_without_history(
            instrument_id, as_of, source_id=source_id, reason_codes=("adjusted_ohlc_unverified",)
        )
    if not comparable:
        return _result_without_history(
            instrument_id, as_of, source_id=source_id, reason_codes=("volume_not_comparable",)
        )

    columns = {
        column: _numeric_column(completed, column)
        for column in (*required_ohlc, "volume", "split_ratio")
    }
    for column in required_ohlc:
        if any(value is not None and value <= 0 for value in columns[column]):
            raise ValueError(f"{column} prices must be positive")
    if any(value is not None and value < 0 for value in columns["volume"]):
        raise ValueError("volume values must not be negative")
    if any(value is not None and value < 0 for value in columns["split_ratio"]):
        raise ValueError("split ratios must not be negative")

    row_count = len(completed)
    atr: list[float | None] = [None] * row_count
    adx: list[float | None] = [None] * row_count
    bandwidth: list[float | None] = [None] * row_count
    bandwidth_median: list[float | None] = [None] * row_count
    candidate_reasons: list[tuple[str, ...]] = [()] * row_count
    volume_baselines: list[float | None] = [None] * row_count
    volume_spikes: list[bool | None] = [None] * row_count
    qualified = [False] * row_count
    gap_present = False

    def finish_segment(start: int, end: int) -> None:
        if start >= end:
            return
        segment_atr, segment_adx, segment_bandwidth, segment_median = _indicators(
            _required_float_slice(columns["high"], start, end),
            _required_float_slice(columns["low"], start, end),
            _required_float_slice(columns["close"], start, end),
        )
        atr[start:end] = segment_atr
        adx[start:end] = segment_adx
        bandwidth[start:end] = segment_bandwidth
        bandwidth_median[start:end] = segment_median

    segment_start: int | None = None
    for index in range(row_count + 1):
        valid_bar = (
            index < row_count
            and all(
                columns[column][index] is not None
                for column in ("open", "high", "low", "close")
            )
        )
        if valid_bar:
            open_raw = columns["open"][index]
            high_raw = columns["high"][index]
            low_raw = columns["low"][index]
            close_raw = columns["close"][index]
            assert open_raw is not None
            assert high_raw is not None
            assert low_raw is not None
            assert close_raw is not None
            open_value = float(open_raw)
            high_value = float(high_raw)
            low_value = float(low_raw)
            close_value = float(close_raw)
            if high_value < max(open_value, low_value, close_value) or low_value > min(
                open_value, high_value, close_value
            ):
                raise ValueError("OHLC bars must satisfy low <= open/close <= high")
            if segment_start is None:
                segment_start = index
            continue
        if segment_start is not None:
            finish_segment(segment_start, index)
            segment_start = None
        if index < row_count:
            gap_present = True
            candidate_reasons[index] = ("history_gap",)

    dates = [timestamp.date() for timestamp in pd.DatetimeIndex(completed.index)]
    volumes = columns["volume"]
    split_ratios = columns["split_ratio"]
    for index in range(row_count):
        if candidate_reasons[index] == ("history_gap",):
            continue
        reasons: list[str] = []
        if index < _MINIMUM_WARMUP_SESSIONS:
            reasons.append("warmup_insufficient")
        if atr[index] is None or adx[index] is None:
            reasons.append("adx_atr_insufficient")
        if bandwidth[index] is None:
            reasons.append("bandwidth_insufficient")
        if bandwidth_median[index] is None:
            reasons.append("bandwidth_baseline_insufficient")
        if index < volume_lookback:
            reasons.append("volume_baseline_insufficient")
        else:
            baseline_values = volumes[index - volume_lookback : index]
            split_window = split_ratios[index - volume_lookback : index + 1]
            if any(value is None for value in split_window):
                reasons.append("split_evidence_incomplete")
            elif any(float(value) > 0 for value in split_window if value is not None):
                reasons.append("split_boundary")
            elif any(value is None for value in baseline_values):
                reasons.append("volume_baseline_insufficient")
            else:
                known_volumes = [value for value in baseline_values if value is not None]
                baseline = sum(known_volumes) / volume_lookback
                if baseline <= 0:
                    reasons.append("volume_baseline_insufficient")
                else:
                    volume_baselines[index] = baseline
                    current_volume = volumes[index]
                    if current_volume is None or current_volume <= 0:
                        reasons.append("current_volume_unavailable")
                    else:
                        volume_spikes[index] = current_volume >= volume_multiplier * baseline
        candidate_reasons[index] = tuple(dict.fromkeys(reasons))
        if not reasons:
            adx_value = adx[index]
            bandwidth_value = bandwidth[index]
            bandwidth_median_value = bandwidth_median[index]
            volume_spike = volume_spikes[index]
            assert adx_value is not None
            assert bandwidth_value is not None
            assert bandwidth_median_value is not None
            assert volume_spike is not None
            qualified[index] = (
                adx_value < 20
                and bandwidth_value <= bandwidth_median_value
                and not volume_spike
            )

    intervals: list[ConsolidationInterval] = []
    run_start: int | None = None
    latest_sessions = set(dates[-2:])
    for index in range(row_count + 1):
        if index < row_count and qualified[index]:
            if run_start is None:
                run_start = index
            continue
        if run_start is None:
            continue
        run_end = index - 1
        duration = run_end - run_start + 1
        if duration >= 5:
            run_atr = [float(value) for value in atr[run_start : run_end + 1] if value is not None]
            run_volumes = [
                float(value) for value in volumes[run_start : run_end + 1] if value is not None
            ]
            run_baselines = [
                float(value)
                for value in volume_baselines[run_start : run_end + 1]
                if value is not None
            ]
            lows = _required_float_slice(columns["low"], run_start, run_end + 1)
            highs = _required_float_slice(columns["high"], run_start, run_end + 1)
            start_date = dates[run_start]
            end_date = dates[run_end]
            lower = min(lows)
            upper = max(highs)
            identity = sha256(
                f"{instrument_id}|{QUIET_SIDEWAYS_VERSION}|{start_date.isoformat()}".encode()
            ).hexdigest()[:24]
            previous_insufficient = (
                run_start > 0 and bool(candidate_reasons[run_start - 1])
            )
            first_reportable_run = not intervals
            intervals.append(
                ConsolidationInterval(
                    interval_id=identity,
                    instrument_id=instrument_id,
                    detector_version=QUIET_SIDEWAYS_VERSION,
                    start_session=start_date,
                    end_session=end_date,
                    duration_sessions=duration,
                    approx_calendar_duration=(end_date - start_date).days + 1,
                    lower=lower,
                    upper=upper,
                    width_absolute=upper - lower,
                    width_pct=100 * (upper / lower - 1),
                    median_atr14=median(run_atr),
                    volume_context=VolumeContext(
                        lookback_sessions=volume_lookback,
                        spike_multiplier=volume_multiplier,
                        median_session_volume=median(run_volumes),
                        median_prior_volume=median(run_baselines),
                        spike_sessions=sum(
                            value is True for value in volume_spikes[run_start : run_end + 1]
                        ),
                    ),
                    as_of=as_of,
                    observable_history_start=dates[0],
                    start_boundary_truncated=(
                        previous_insufficient or (truncated and first_reportable_run)
                    ),
                    ongoing=end_date == as_of,
                    current_or_previous_session=end_date in latest_sessions,
                )
            )
        run_start = None

    latest_index = row_count - 1
    latest_reasons = list(candidate_reasons[latest_index])
    if gap_present and "history_gap" not in latest_reasons:
        latest_reasons.append("history_gap")
    if truncated:
        latest_reasons.append("history_truncated")
    state: DetectorState = "insufficient" if candidate_reasons[latest_index] else "sufficient"
    return ConsolidationResult(
        instrument_id=instrument_id,
        detector_version=QUIET_SIDEWAYS_VERSION,
        as_of=as_of,
        source_id=source_id,
        state=state,
        reason_codes=tuple(dict.fromkeys(latest_reasons)),
        intervals=tuple(intervals),
        observed_through=dates[-1],
        latest_adx14=adx[latest_index],
        latest_atr14=atr[latest_index],
        latest_bandwidth=bandwidth[latest_index],
        latest_bandwidth_median=bandwidth_median[latest_index],
        latest_volume_baseline=volume_baselines[latest_index],
        latest_volume_spike=volume_spikes[latest_index],
    )
