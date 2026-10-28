# Data Model: Progressive Stock Screener

These are planned typed Python records/dataframes, not database tables or new persisted
schemas. Use existing identifiers/helpers where their meaning matches. Immutable result
records and copied cached frames prevent accidental mutation of shared source data.

## Common Types and Provenance

Stable IDs identify instruments, sectors and industries; symbols/names are display
attributes. UTC timestamps describe retrieval/publication; exchange-local dates identify
completed sessions and fiscal periods. Never infer publication from period end/retrieval.

`EvidenceState = sufficient | insufficient | unsupported | error`.
`CriterionState = pass | fail | insufficient`.
Operational exceptions are surfaced, not silently mapped to a successful empty result.

### SourceEvidence

Fields: `source_id`, `dataset`, `retrieved_at`, `observed_at?`, `available_at?`,
`effective_from?`, `effective_to?`, `expires_at`, `payload_fingerprint`,
`source_version?`, `coverage_state`, `rights_scope`, `limitations`, `reason_codes`.

Invariants: source is the one selected runtime provider; retrieval is not evidence of
historical availability. Unknown dates remain unknown. Freshness describes cache age
and source age separately. An expired value cannot be displayed as current.

## Universe and Classification

### Instrument

`instrument_id`, `company_id?`, `symbol`, `name`, `exchange`, `security_type`,
`primary_listing`, `currency`, `active_from?`, `active_to?`, `source_evidence`.

Only verified US common-stock listings enter the stock universe. Keep distinct share
classes/listings distinct; collapse duplicate records for the same instrument. Unverified
type/exchange/classification is a visible eligibility gap, not an assumed common stock.
ETF/index instruments may represent a classification but never become member stocks.

### Classification and Membership

Classification: `node_id`, `name`, `level` (`sector | industry`), `parent_sector_id?`,
`taxonomy_id`, `effective_from?`, `effective_to?`, `source_evidence`.

Membership: `industry_id`, `instrument_id`, `effective_from`, `effective_to?`,
`available_at`, `source_evidence`. IndexMembership adds `index_id`.

An industry has one valid parent at a given date; no conflicting overlapping assignments.
Do not assign a proprietary taxonomy name to unverified provider labels. Effective
periods and known availability must cover the analysis cutoff; current top-company lists
or ETF holdings do not constitute full industry membership.

### UniverseSelection and UniverseResult

Selection: sorted unique `index_ids`, `exchange_ids`, `cap_bands`, `sector_ids`,
`analysis_cutoff`, `membership_date`.

Result: ordered `instrument_ids`, `industry_members`, `expected_total?`, `returned_count`,
`eligible_count`, `excluded_count`, `unclassified_count`, `gap_reasons`, `source_evidence`,
`universe_fingerprint`.

Union selected dated index memberships first, then intersect exchanges/cap bands; no
index selection means the available verified US-common-stock set. Sectors form a union.
An unsupported selected index is an unavailable request, never equivalent to no filter.

MarketCapObservation: `instrument_id`, `value`, `currency`, `valuation_at`,
`available_at?`, `source_evidence`. Classify USD values: large >=10B; mid >=2B and <10B;
small >=300M and <2B. Below-300M/unknown are separate; include with no cap-band filter
but exclude from explicitly selected bands. Unknown total implies no coverage percentage.

### ClassificationRepresentation

`node_id`, `instrument_id?`, `kind` (`industry_etf | single_company | unavailable`),
`qualification`, `composition_basis`, `effective_from`, `effective_to?`, `available_at`,
`market_cap_evidence?`, `membership_evidence?`, `source_evidence`, `limitations`.

Select one explicitly qualified industry ETF first. Without one, select the largest
verified dated industry-member stock with positive comparable cap, tie by instrument
ID. Incomplete membership/cap coverage cannot establish a largest-member claim.
Representation identity never defines the member-stock set. Sector chart representations
also require qualification; an industry corridor is never applied to a different stock.

## Market Observations and Screening

### PriceHistory

Key: `instrument_id`, `session`. Fields: adjusted `open`, `high`, `low`, `close`,
`volume`, `price_basis`, `volume_basis`, `corporate_actions`, `source_evidence`,
`history_start`, `history_truncated`, `requested_cutoff`, `latest_usable_session`.

Prices must be finite/positive with consistent OHLC bounds. Volume is finite and
nonnegative; zero/undefined windows do not automatically qualify as healthy quiet volume.
Sessions are ordered/unique. Do not bridge missing required sessions. Omit an incomplete
trailing observation explicitly; invalid interior data is an adapter fault. Keep validated
independent price evidence when volume comparability alone is insufficient.

### ScreeningCriteria

`period_intervals` (1 or 5, default 5), four enabled flags, positive whole-number
`volume_lookback` (default 20), finite positive `volume_multiplier` (default 2),
`cutoff_session`, `detector_version` (`quiet-sideways-v1`).

Invalid parameters produce visible validation errors without an upstream call.
Consolidation uses these same volume parameters, even when the spike filter is disabled.

### CriterionResult and ScreeningRow

Criterion: `name`, `state`, `observed_value?`, `comparison_value?`, `required_sessions`,
`available_sessions`, `reason_codes`.

Row: stock/industry IDs, cap, period return, four criterion results, `matches`,
`source_evidence`, `consolidation_interval_ids`.

Enabled criteria AND together. Only all-pass matches; disabled criteria do not exclude.
No enabled criteria means all available members, even with insufficient technical history.
Retain diagnostic rows/counts for failures and insufficient evidence.

### IndustryPerformanceRow

`industry_id`, `parent_sector_id`, `representation`, `period_intervals`, `start_session`,
`end_session`, `return_pct?`, `direction?`, `rank?`, `evidence_state`, `source_evidence`.

Return = `100*(end/start - 1)` at exact completed-session endpoints. Positive/negative/zero
is gaining/declining/neutral. Rank over sufficient industries in the visibly selected
scope using competition ranks (1, 1, 3); reverse ordering when ascending. Exact ties
share rank, sort by name/ID. A direction-filtered view retains its declared ranking scope;
insufficient rows have no return/rank.

### ConsolidationInterval

`interval_id`, `instrument_id`, `detector_version`, `cutoff_session`, `start_session`,
`end_session`, `duration_sessions`, `approx_calendar_duration`, `lower`, `upper`,
`width_absolute`, `width_pct`, `median_atr14`, `volume_context`, `ongoing`,
`observable_history_start`, `start_boundary_truncated`, `reason_codes`.

Interval ID derives from instrument/version/start, not chart position. Duration >=5;
no maximum. Bounds derive only from interval OHLC available at cutoff. Current criterion
passes only if the latest qualifying interval ends at cutoff or its immediately preceding
session. Insufficient detector evidence differs from sufficient evidence with no interval.
See [detector contract](contracts/consolidation.md).

## Financial Facts and Relative Scores

### FinancialFact

`instrument_id`, `field`, `value?`, `unit`, `currency?`, `period_start`, `period_end`,
`period_kind`, `accounting_basis`, `available_at?`, `revision_available_at?`,
`share_adjustment_basis?`, `source_evidence`, `reason_codes`.

Fields include revenue, net income, common equity, diluted EPS, operating cash flow
and capex. Distinguish flow periods from point-in-time balances. Preserve reported
capex sign; normalize to a documented positive outflow for FCF. Do not use absolute
value blindly. Current/prior TTM flows are non-overlapping comparable windows.

### MetricObservation

`instrument_id`, `metric_id`, `value?`, `unit`, `current_period`, `prior_period?`,
`valuation_at?`, `input_fact_ids`, `available_at?`, `state`, `reason_codes`.

Six metrics/formulas follow [the financial contract](contracts/fundamental-scoring.md).
An invalid denominator or missing publication/vintage evidence invalidates only dependent
metrics. Genuine negative current values remain negative; missing is never zero.

### PeerCohort and StockScorecard

Cohort: `industry_id`, `universe_fingerprint`, sorted member IDs **before** technical
filters/row selection, `financial_cutoff`, `membership_evidence`, `facts_fingerprint`.

Scorecard: instrument/cohort IDs; six raw metrics, percentile scores and per-metric
valid-peer counts; Quality/Growth/Cash Flow block scores; periods, cutoff, sufficiency
and reasons. Peer-valid N varies per metric, includes the stock, and must be >=5.
Each block requires both metric percentiles. No overall score and no automatic trade label.

The cohort identity excludes technical flags, sorting, paging and selected rows.
A changed financial cutoff, membership/universe or raw-fact version changes its identity.

## Session State and Transitions

Use the `screener.*` namespace: universe/criteria, selected sector IDs, industry ID,
selected stock IDs, focused stock ID, stage load intents, page/sort state, editor generation,
loaded view records and their request signatures/freshness. Store no credentials/shared
cross-user source cache here. Loaded view records are private display copies, not a database.

| Event | Preserve | Reconcile/invalidate |
|---|---|---|
| Ordinary rerun/sort/page | All still-valid stable selections and loaded data | Editor row positions remap to IDs; no remote request |
| Sector/universe/membership change | Overlapping valid IDs and reusable source cache | Validate industry/stock eligibility; recompute cohort if universe changes |
| Industry change | Universe, criteria, cache | Clear only stock choices not valid in the new industry; require new stock/scorecard load |
| Technical criterion change | Membership, full cohort scores, valid selected stocks | Recompute matches; clear excluded stock choices/focus with a message |
| Period/cutoff change | Valid parent/instrument selections | Invalidate dependent returns/detector results; financial cutoff changes invalidate scores |
| Successful refresh | Valid selections | Replace affected source/view fingerprints; recompute dependents only |
| Failed refresh/expiry | Selections and valid independent results | Mark affected old view stale/error; never mark it fresh or a successful empty result |

Widget keys are separate from canonical state where widgets may be recreated. A changed
editor dataset/page resets editor generation but rehydrates still-valid selected IDs.
Changing visible tabs never resets parent context or triggers a source request.
