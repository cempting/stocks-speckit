# Consolidation Detection and Chart Contract

**Ruleset**: `quiet-sideways-v1`. Product heuristic, not a standard definition or a
profitability claim. The [specification](../spec.md) is authoritative.

## Input and Indicator Conventions

Use one instrument's ordered completed-session adjusted OHLC and verified comparable
volume, truncated to an explicit cutoff. No future inputs. Missing required observations
break runs; they are not forward-filled. Reinitialize recursive indicators after a
gap and disclose the resulting warm-up insufficiency.

- `TR = max(high-low, abs(high-prev_close), abs(low-prev_close))`.
- Up move = `high-prev_high`; down move = `prev_low-low`. Positive DM is up move only
  when positive and greater than down move; negative DM is down move only when positive
  and greater than up move. Equal moves give zero DM in both directions.
- Wilder14 smoothing starts with the arithmetic mean of the first 14 valid observations,
  then `smooth_t = (13*smooth_prev + value_t)/14`.
- `+DI = 100*smooth(+DM)/smooth(TR)`, likewise `-DI`.
  `DX = 100*abs(+DI - -DI)/(+DI + -DI)`; ADX14 is Wilder14-smoothed DX, seeded
  with the first 14 valid DX values. Zero/undefined denominators are insufficient.
  Require at least **150 prior contiguous sessions** of warm-up before declaring
  a candidate qualifying; a numerical early ADX alone is not enough.
- ATR14 uses the same Wilder-smoothed TR. TR/DM require a previous session;
  a segment's first bar alone cannot invent a previous close.
- Bollinger middle = mean of latest 20 closes; bands = middle +/- twice the
  **population** standard deviation. `BW20 = 100*(upper-lower)/middle`, middle >0.
- Candidate-day BW20 compares to the median of the **preceding 252 valid BW20 values**,
  excluding that day. Earlier values must themselves have valid 20-session windows.
  Do not lower this minimum for short listings or include the candidate in its baseline.
- Volume spike = latest volume >= multiplier times the arithmetic mean of the
  preceding N sessions, excluding latest. Defaults 2 and 20; same parameters as the
  stock criterion. Baseline must be finite/positive. Zero/unknown current trading
  volume does not establish a qualifying quiet session; ordinary spike failure alone
  is not proof of healthy consolidation.

Indicator estimation windows do not prescribe consolidation duration. All relevant
history limits, split-comparability gaps and warm-up constraints remain visible.

## Quiet Sessions and Intervals

A session qualifies only if all required evidence is valid, ADX14 <20, BW20 <= its
historical median, and volume spike is false. ADX=20 fails; BW=median passes; volume
exactly at its spike threshold is a spike and prevents quiet qualification.

Build maximal consecutive qualifying-session runs. Report runs of at least five
sessions, with no maximum duration. A nonqualifying or insufficient session ends a
run; it never bridges an unobserved gap.

For each run, corridor lower = minimum adjusted low, upper = maximum adjusted high;
absolute width = upper-lower; percent width = `100*(upper/lower - 1)` with lower >0.
Show median ATR14 of the run and volume context using the same basis/parameters.

An interval ending at cutoff is ongoing. An older interval is completed. Mark a
possibly boundary-truncated start when the first observable qualifying run cannot
establish what preceded it because history/warm-up is insufficient; report observable
start, not an invented actual historical beginning.

The stock consolidation criterion passes when a reportable run ends at cutoff or
the **immediately preceding trading session**. This permits consolidation plus a
current spike without including that spike inside the quiet run. An older interval
is historical context only. Distinguish sufficient/no qualifying interval from
insufficient detector evidence.

## Output, Chart and Tests

Return typed interval evidence from the pure detector, not chart objects. Calculate
interval bounds/duration separately for each cutoff; appending future data must not
alter the stored earlier-cutoff result. No maximum corridor-width rejection rule.

Charts show at most the latest detected interval by default: subtle shaded time span
and horizontal bounds. Older intervals can be inspected explicitly. Show the data-model
metrics beside/below the chart, including truncation and cutoff. Never transfer an
industry interval to its stocks or label it a predicted breakout.

Controlled fixtures must cover exactly 4/5 sessions; months/years of qualifying
history; a sustained trend; flat/zero-volume data; all equality boundaries; prior-only
BW/volume windows; split/gap/warm-up failure; historical cutoff invariance; latest and
previous-session runs; older-run exclusion; and chart-bound/duration agreement.
Validate recursive indicators against hand/reference sequences, not against themselves.
