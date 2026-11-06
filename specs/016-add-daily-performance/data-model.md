# Data Model: Add Daily Performance

This is an additive derived-data projection. No persisted entity, catalog revision, public schema,
or legacy five-period return-type migration is required.

## Daily session interval

| Field | Type | Meaning |
|---|---|---|
| start_session | date | Official session immediately before the ending session. |
| end_session | date | Completed session at the effective table cutoff. |
| requested_as_of | date | Existing user's requested date. |
| observed_as_of | date or unavailable | Existing observed table date and stale-data context. |

The application resolves dates through the existing calendar boundary. The cutoff never exceeds
the requested date or the latest actually completed session; stale observed table context remains
visible. Domain helpers receive explicit dates, not clocks or calendar dependencies.

Validation:

- Start is strictly earlier than end; the application guarantees official session adjacency.
- Require both exact endpoint observations. An older available close must not fill a missing
  required session.
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

These are calculation concepts and local projection values, not a required new dataclass.
Expected unavailable evidence raises the existing domain evidence exception and is converted
to a missing cell plus visible reason only at the workflow boundary.

- ETF: `ending_close / starting_close - 1` for its approved symbol.
- Basket: sum of approved weights divided by 100 times each constituent's daily return.
- Existing approval/effectivity and exact 100% weight invariants remain required.
- Every basket constituent supplies both exact endpoints. No constituent dropping, inferred
  membership, weight renormalization, parent return, or fabricated traded-basket chart.
- Relative: `absolute_daily - benchmark_daily`, only when both use identical session dates.
- Absolute mode does not require benchmark daily evidence.

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
- Parent selection changes: follow existing dependent selection invalidation.
- Refresh/catalog changes: follow existing history and context lifecycle, not a daily-specific
  cache or persistence layer.
