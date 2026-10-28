# Pure Fundamental Scoring Contract

**Design version**: `industry-peer-v1`; scale **0-100** (user-confirmed).
Exactly two metrics per block; no A-F labels or overall recommendation score.

## Boundary

The pure Python utility accepts normalized raw financial facts, dated market caps,
the complete selected industry's eligible member IDs in the selected universe, and an
information cutoff. It returns per-stock raw metric evidence, valid-peer counts,
percentiles, three block scores and reasons. It performs no network, filesystem,
Streamlit, cache or session-state access. Clocks/cutoffs are supplied, not read globally.

Normalization of provider field names and reported cash-flow signs happens upstream;
the utility still validates units, periods, values, denominators and availability.
Do not force a missing value into a numeric type. Reject malformed requests explicitly;
expected missing financial evidence produces typed insufficiency.

## Metric Definitions

All formula values below are percentages. Higher is better for each metric.

| Block | Metric | Formula and required evidence |
|---|---|---|
| Quality | ROE | `100 * current_TTM_net_income / mean(opening_common_equity, closing_common_equity)`; both equity balances positive and bracket the same TTM window |
| Quality | Net margin | `100 * current_TTM_net_income / current_TTM_revenue`; revenue positive |
| Growth | Revenue YoY | `100 * (current_TTM_revenue / prior_TTM_revenue - 1)`; prior positive |
| Growth | Diluted EPS YoY | `100 * (current_TTM_diluted_EPS / prior_TTM_diluted_EPS - 1)`; prior positive |
| Cash Flow | FCF yield | `100 * (current_TTM_OCF - current_TTM_positive_capex_outflow) / market_cap`; cap positive, currency/valuation date compatible |
| Cash Flow | OCF YoY | `100 * (current_TTM_OCF / prior_TTM_OCF - 1)`; prior positive |

TTM flows cover four comparable quarters or an equivalent source-verified exact
twelve-month window. Current/prior TTM windows must be comparable and non-overlapping.
Do not sum YTD cumulative cash flows as independent quarters; derive discrete quarters
only when sufficient verified periods permit it. Diluted EPS must use consistent
split/dilution definitions, not forward EPS or net income substituted without share data.
Fiscal-year differences and changed accounting definitions require explicit comparability.

Every contributing fact/version must have been available by the common analysis cutoff.
Unknown publication/vintage evidence is insufficient. Report fiscal periods and known
publication dates; do not fabricate them from report period ends or download timestamps.
Market cap needs a matching displayed valuation date/currency.

Negative current net income, growth, margin, OCF or FCF is valid if the respective
denominator requirements hold. Zero/negative prior growth denominators and negative/
zero opening or closing equity are insufficient, not low scores or extreme growth.

## Cohort and Percentiles

Peer cohort = industry members within the selected universe **before** technical
filters, row selection, paging or display sorting. Keep every eligible peer ID even
when some facts are missing; disclose known universe gaps and per-metric valid counts.
Changing technical criteria alone must not change any retained stock's score.

For each metric, include the stock among the N finite, comparable valid peer values.
Require `N >= 5`. Let L be the number strictly lower and E the equal-value count:

`percentile = 100 * (L + 0.5 * (E - 1)) / (N - 1)`.

Use exact normalized values for ranking, not display-rounded strings or epsilon-created
ties. Five distinct ascending inputs produce `0, 25, 50, 75, 100`. Five equal inputs
produce 50 each. Inputs `[1, 2, 2, 4, 5]` produce `0, 37.5, 37.5, 75, 100`.
N=4 produces insufficient metric scores, even if a raw value is available.

Quality/Growth/Cash Flow are arithmetic means of their respective two percentiles.
Require both; never reweight one surviving metric. Keep full precision internally and
round only presentation to one decimal. A missing block does not hide independent
valid blocks or raw facts. These are relative historical comparisons, not absolute
quality labels, forecasts or trade advice.

## Required Evidence

Tests cover exact formulas; capex signs; period/currency and YTD mismatches; equity/
growth denominators; negative current values; publication after cutoff; unknown dates;
revision vintages; missing quarters; N=4/5 boundaries; distinct/tied/all-equal peers;
rounding; missing block members; and unchanged scores after technical/row filtering.
Show deliberately sufficient and insufficient stock cases in the same fixture.
