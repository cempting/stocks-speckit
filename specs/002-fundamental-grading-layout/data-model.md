# Data Model: Fundamental Grading Layout

Use frozen typed dataclasses/finite enums following existing domain patterns.
These are internal contracts, not a new persistence schema or public service.

## MembershipCatalog and MembershipEntry

- Catalog: schema version, market `US`, classification scheme, source ID,
  observation date, coverage description, evidence mode (`fixture` or `live`),
  source/display approval reference, entries.
- Entry: stable instrument/company IDs, symbol, name, exchange, currency,
  sector ID, industry ID, effective-from/to dates.
- Relationships: one industry has many dated entries; selected stock IDs must
  identify active entries within the exact chosen catalog context.
- Validation: nonempty IDs and metadata, valid dates/currency, stock instruments
  only, unique active instrument IDs, no ambiguous duplicate symbols/listings,
  valid sector/industry parent relationship. Invalid catalog reports an error;
  missing catalog reports missing coverage, never an empty successful universe.
- Live catalogs require reviewed provenance and rights references. Test fixtures
  are visibly labelled synthetic and do not activate live provider access.

## ScreeningContext and StockSelection

- Context: market, evidence mode, provider, sector/industry IDs, membership catalog
  fingerprint/date, observation cutoff, and existing filter/universe identity if any.
- Selection: ordered unique instrument IDs belonging to the current context,
  current page, and the context fingerprint for which the displayed result was loaded.
- Session keys begin `market_leadership.screening.` or
  `market_leadership.fundamentals.`; financial data caches do not include selections.
- Transition: parent change -> validate catalog -> intersect selection with valid
  members, or clear on incompatible mode/cutoff -> clear invalid displayed results.
  Clear all old stock selections when switching industry, even if symbols overlap.
- Ordinary rerun preserves valid selections. Pagination does not authorize requests;
  switching page invalidates the displayed load token until the next Load action.

## FundamentalRequest

- Provider ID fixed to `yfinance` in live mode; normalized nonempty symbol,
  stable instrument ID for UI association, current cutoff policy, requested window
  (maximum eight displayed quarters), quarterly frequency, schema version.
- Cache identity excludes UI instrument selection but includes provider, symbol,
  cutoff/window, frequency, and schema version. Reject unsupported historical live
  cutoffs rather than caching misleading present-day evidence under a past date.

## FundamentalBundle and ComponentOutcome

- Bundle: symbol/provider, requested context, UTC fetch timestamp, schema version,
  normalized profile, quarterly income/cash-flow/balance-sheet tables,
  component statuses, content fingerprint and coverage warnings.
- Component status: `available`, `partial_coverage`, `unverified_empty`, or `failed`;
  a successful table can have absent rows without being an acquisition failure.
- Tables: finite numeric cells where usable, normalized row names, completed
  reporting dates ascending and unique, original provenance/scale retained.
  Duplicate conflicting dates or units are explicit validation errors.
- Do not infer eight consecutive quarters from eight arbitrary dates. Validate
  fiscal-year/quarter sequence, allowing documented non-calendar fiscal years.
  Reconcile shared statement dates by reporting period, not nearest date.
- Entirely empty profile/statements are uncertain at this yfinance version.
  A typed acquisition exception carries component errors and safe partial evidence;
  it does not produce a cacheable successful bundle.
- Valid success -> shared TTL cache; TTL expiry -> fetch on explicit request;
  targeted refresh -> invalidate matching request -> new fetch.
- Failure -> no cached result; show source error plus usable partial metrics in
  the current render. Retry is explicit; never store error objects as snapshots.

## FundamentalMetric

- Stable ID, exact label, group, units (`percent` or `quarter_count`), value,
  formatted display, period description, source rows, availability state/reason,
  commentary, and ordered history observations.
- Percent values are stored as ratios and formatted once as percentages, normally
  one decimal place in this new surface. Count values are integers zero to eight.
- Available values must be finite. Zero and negative values are valid unless a
  specific denominator/comparability rule excludes them.
- Unavailable values are `None`, display `N/A`, commentary `Data not available`;
  internal reason and provenance are separately accessible.
- Commentary: supplied reviewed metric interpretation, defensible negative
  operating-margin rule, otherwise neutral exact label plus formatted value.
  Never carry commentary across symbols, evidence fingerprints, or unavailable values.

## QuarterlyObservation and EPSConsistency

- Observation: fiscal reporting period/end date, metric value/unit, sufficiency,
  source reference; periods ascending and unique, values finite, no interpolations.
- Each history point uses the same formula/units as its current metric. Formulas
  requiring earlier quarters need a full valid window at every history date.
- Chart contains latest four to eight valid consecutive comparable points; gaps
  break the contiguous run rather than being silently bridged. Less than four
  yields separate `Insufficient quarterly history` status.
- EPS count: latest eight consecutive completed quarters, positive diluted EPS
  count, number of observed quarters, and period range. Available only with eight
  comparable EPS observations; historical counts require rolling eight-quarter
  windows (four historical count points require at least eleven source quarters).

## FundamentalScorecard

- Instrument identity, context/fetch fingerprint, evidence metadata/errors, and
  exactly eight ordered FundamentalMetric objects grouped 3/3/2.
- Aggregate grades are not part of this new raw-metric schema; preserve any
  implemented existing grades separately with their own definitions and provenance.
- Never combine one stock's profile with another stock's statements or historical
  fixture data with current live data.

Detailed field mappings and formulas are in
[the data contract](./contracts/fundamental-data.md); display order is in
[the UI contract](./contracts/fundamental-ui.md).
