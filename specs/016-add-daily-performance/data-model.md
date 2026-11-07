# Data Model: Daily Performance

Derived in-memory results only; no persisted entity, catalog, snapshot schema or legacy
`PerformanceResult` migration. The Python representation return shape changes as below.

## Daily Interval

| Field | Type | Meaning |
|---|---|---|
| `requested_as_of` | date | User's requested date; determines the daily context. |
| `end_session` | date | Latest completed official session on/before requested date. |
| `start_session` | date | Exact official predecessor of ending session. |
| `observed_as_of` | date or unavailable | Existing freshness disclosure and longer-period/chart cutoff, not a daily selector. |

The application resolves the pair with its calendar and timezone-aware clock; domain functions
receive explicit dates. Require ordered distinct sessions, unique observation dates and both
exact finite positive adjusted closes. Ignore incomplete/future observations and unrelated old
prices for endpoint validity. Never fill a missing endpoint from an older observed pair.

## Daily Arithmetic

- ETF fraction: `ending_close / starting_close - 1`.
- Basket fraction: sum of each constituent return multiplied by its approved weight / 100.
  All approved constituents provide the same endpoints; exact weights total 100%.
  Preserve approval/effectivity; no dropping, inferred membership, renormalization, parent
  substitution, older representation or fabricated traded-basket chart.
- Relative fraction: entity minus benchmark over identical sessions.
  Absolute daily does not require benchmark evidence.

The scalar helper raises contextual evidence exceptions; malformed dates/indexes remain input
errors. Representation calculation converts expected period insufficiency into explicit reasons.

## Six-Period Results

`representation_performance` returns an ordered dictionary with keys
`1d`, `1w`, `1m`, `3m`, `6m`, `12m`. Each `RepresentationPeriodResult` has:

| Field | Type | Meaning |
|---|---|---|
| `value` | float or None | Independently available fractional return; 0.02 means 2%. |
| `reason` | text or None | Actionable failure explanation when unavailable, absent for valid values. |

Explicit daily endpoints are required for a usable `1d`; omitted dates produce an unavailable
entry, not inferred sessions. `as_of` governs daily activity; optional `performance_as_of`
preserves longer-period observed-date activity/cutoffs. Invalid shared approval evidence raises
a domain error. Inactivity in one context makes only its periods unavailable; both inactive raises.

`calculate_performance_periods` prepares calendar history once and returns six typed results;
benchmark results are reused across rows. Preserve valid calendar-offset arithmetic and full
basket alignment. Ranking/snapshots require only their five legacy horizons, retaining float
dictionaries and all-required behavior. See [migration guidance](plan.md#python-api-migration).

## Tape Projection and State

Map keys to the [UI captions](contracts/daily-performance-ui.md#fields-and-captions), including
`1 day` for `1d` and `1 year` for `12m`. The final-caption implementation is pending T030.
Insert nullable numeric daily percentages before weekly: multiply the fractional absolute or
entity-minus-benchmark return by 100 exactly once. Missing values render `Unavailable`, not
strings stored in numeric cells. Preserve identity, ticker/ETF, representation, charts and status;
append `1d:` reasons without overwriting source/freshness explanations.

- Rerender/basis/detail actions reuse loaded histories; no new acquisition or persistence.
- Thumbnail changes crop charts only; all returns remain unchanged.
- Daily failure affects only daily availability; stale observations retain warnings, not older daily intervals.
- Parent changes clear only invalid descendants. Refresh/catalog changes use existing lifecycle.
- Details wrap full names/evidence without navigation, lost valid selections or extra requests.
