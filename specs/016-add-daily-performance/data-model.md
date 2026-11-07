# Data Model: Add Daily Performance

This is an additive derived-data projection. No persisted entity, catalog revision, public schema,
or legacy `PerformanceResult` migration is required. The representation function's in-memory
return shape changes as documented below; its callers are explicitly migrated.

## Daily session interval

| Field | Type | Meaning |
|---|---|---|
| start_session | date | Official session immediately before the ending session. |
| end_session | date | Latest completed official session on or before requested_as_of. |
| requested_as_of | date | Existing user's requested date. |
| observed_as_of | date or unavailable | Existing observation/freshness disclosure, never a daily endpoint selector. |

The application resolves one pair from requested_as_of and a timezone-aware evaluation clock
through the existing calendar boundary. The ending session is the latest completed official
session on or before requested_as_of; the starting session is its exact official predecessor.
Price availability and observed_as_of must not select or move either daily endpoint.
Observed dates and stale-data context remain visible. Domain helpers receive explicit dates,
not clocks or calendar dependencies.

Validation:

- Start is strictly earlier than end; the application guarantees official session adjacency.
- Require both exact endpoint observations. An older available close must not fill a missing
  required session.
- Missing either required close makes the daily value unavailable; an older valid daily pair
  must not substitute for the requested-date interval.
- Ignore future/incomplete-session data and unrelated old observations when evaluating daily
  endpoint validity.
- Require unique observation dates and finite strictly positive endpoint prices.

## Daily representation return

| Field | Type | Meaning |
|---|---|---|
| representation | existing ReviewedRepresentation | Approved ETF or weighted basket belonging to this row. |
| absolute_daily | float or unavailable | Fractional entity return; 0.02 means 2%. |
| benchmark_daily | float or unavailable | Fractional benchmark return over the exact same interval. |
| daily_reason | text or absent | Actionable missing/invalid endpoint or representation explanation. |

The scalar daily calculator raises contextual evidence exceptions. The unified representation
function converts expected per-period failures into explicit value/reason results; the workflow
projects missing values plus visible reasons.

- ETF: `ending_close / starting_close - 1` for its approved symbol.
- Basket: sum of approved weights divided by 100 times each constituent's daily return.
- Existing approval/effectivity and exact 100% weight invariants remain required.
- Validate the selected row's representation at requested_as_of; do not substitute an older
  representation when required daily evidence is missing.
- Every basket constituent supplies both exact endpoints. No constituent dropping, inferred
  membership, weight renormalization, parent return, or fabricated traded-basket chart.
- Relative: `absolute_daily - benchmark_daily`, only when both use identical session dates.
- Absolute mode does not require benchmark daily evidence.

## Six-period representation result

`representation_performance` returns an ordered dictionary keyed by
`1d`, `1w`, `1m`, `3m`, `6m`, and `12m`. Every entry is a `RepresentationPeriodResult`:

| Field | Type | Meaning |
|---|---|---|
| value | float or None | Fractional return, independently available for this period. |
| reason | text or None | Explicit failure context when value is None; absent for valid values. |

Supply explicit daily endpoints; omitted dates yield an unavailable `1d` with a reason, never
an inferred pair. `as_of` governs daily approval/effectivity, while optional `performance_as_of`
preserves the existing longer-period observed-date cutoff/effectivity. Invalid shared approval
evidence remains an explicit domain error. A representation inactive in both contexts also raises.

The user approved six periods by default and independent availability, including longer horizons.
Supported weekly/monthly returns may now remain visible with insufficient yearly history.
All valid longer-period arithmetic, endpoint selection, and basket alignment rules are preserved.
Ranking and snapshot callers explicitly require only their original five horizons and retain
their existing all-required behavior and float dictionaries.

## Entity tape projection

Add numeric nullable `1d` immediately before `1 week` in the existing backing frame.
Convert fractional daily returns to percentage units once: `absolute_daily * 100`, or
`(absolute_daily - benchmark_daily) * 100`. Preserve existing longer-period values unchanged.

Existing identity, Ticker/ETF, representation/type, chart-series, and Status fields remain.
Daily failure context is appended to the existing tooltip/context with a `1d:` prefix; it
does not overwrite freshness or other evidence reasons. Missing numeric values render as
`Unavailable`, not a string stored in a numeric column.

## State transitions

- Table rerender: derive daily values from existing history; no new loading action or stored
  selection is introduced.
- Performance basis changes: recompute only the displayed projection; reuse histories and keep
  sector/industry selections.
- Thumbnail period changes: alter chart cropping only; all six return values remain unchanged.
- Daily endpoint failure: mark only the daily value unavailable; retain valid legacy metrics.
- Stale observation: keep the requested-date daily interval fixed and retain freshness
  disclosures. Existing chart/long-period observed-date cropping remains unchanged.
- Parent selection changes: follow existing dependent selection invalidation.
- Refresh/catalog changes: follow existing history and context lifecycle, not a daily-specific
  cache or persistence layer.
