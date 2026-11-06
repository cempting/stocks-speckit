# Fundamental Score Evaluation Data Model

This feature evaluates existing score data and presentation. It does not introduce a new
persisted financial record or replace the rules in [001](../001-market-leadership-screener/spec.md)
and [006](../006-stock-table-columns/spec.md) without an approved, versioned change.

## Entities

### Normalized Financial Facts

Facts for one identified instrument, normalized for scoring from the selected financial source.

| Field | Meaning | Validation and use |
|---|---|---|
| Instrument ID | Stable identity of the stock being scored | Unique in a peer result; never join facts by ticker alone |
| Facts available on | Date the facts were publicly available | Must be known and no later than the analysis cutoff |
| Current TTM start/end | Current trailing-period bounds | Comparable annual window and end no later than cutoff |
| Prior TTM start/end | Previous comparable trailing-period bounds | Non-overlapping with current window and comparable in length |
| Net income, revenue, diluted EPS | Current-period quality/growth facts | Finite; ratios require the appropriate positive denominator |
| Prior revenue, prior diluted EPS | Comparable prior-period growth facts | Positive denominator required for current growth definitions |
| Opening/closing equity | Common equity across current TTM period | Both finite and positive for ROE |
| Operating cash flow, prior operating cash flow | Current and prior cash-flow facts | Negative or zero current values remain valid observations; positive prior denominator required for growth |
| Positive capex outflow | Capital expenditure expressed as a positive outflow | Must be known and non-negative; missing is not zero |
| Market capitalization/date/currency | Valuation denominator for FCF yield | Must be positive, valuation date and currency compatible with financial facts |
| Source/currency/coverage | Provenance and comparability context | Preserve through display; do not silently substitute another source |

Current code boundary: `PeerFacts` in
[peer_scores.py](../../packages/market-data/src/market_data/domain/peer_scores.py).

### Metric Peer Result

A metric's raw value and ranking result for one instrument in a specific peer cohort.

| Field | Meaning |
|---|---|
| Metric key | One of ROE, net margin, revenue growth, diluted EPS growth, FCF yield, or OCF growth |
| Raw value | Calculated comparable metric or unavailable |
| Percentile | Industry-relative 0–100 rank or unavailable |
| Valid peer count | Number of finite comparable values in the cohort |
| State/reason | Available or insufficient, with a reason when no percentile can be produced |
| Evidence context | Source, publication availability, current/prior period bounds, currency, and cutoff when verified; unavailable fields remain explicitly unavailable |

Existing validation requires at least five valid peers per metric. Exact tied values share
midranks; the stock is included in its eligible cohort. Missing observations are never zero-filled.
Metric evidence and its known context must remain inspectable from the stock detail; rendering
must not trigger another provider request. The current live yfinance adapter does not provide
verified publication vintages or matching dated market capitalization, so it leaves peer facts
unavailable rather than filling these fields with inferred values.

### Component Score

One of Quality, Growth, or Cash Flow for an instrument and peer context. Each component
contains exactly two metric results and is available only when both percentile values are
available. Its value is their arithmetic mean. A missing metric does not cause the other metric
to be reweighted.

### Peer Context

The context required to interpret and compare a score:

- Region, classification scope, industry, and effective membership date.
- Complete eligible cohort identity and cohort fingerprint.
- Common information cutoff and financial observation basis.
- Scoring rules revision and source/fact fingerprint where available.

A value from a different cohort, cutoff, or incompatible rules revision is not silently reused
or described as directly comparable.

Existing orchestration boundary: `PeerComparisonContext` and `IndustryScoreResult` in
[score_industry.py](../../src/market_leadership/application/score_industry.py).

### Stock-List Total Score

The one-decimal display value derived from Quality, Growth, and Cash Flow for the same
instrument and peer context. The current rule requires all three finite 0–100 component values
and calculates their equal arithmetic mean. Otherwise the stock list retains the explicit
non-numeric state: Error, Not loaded, Insufficient, or Unavailable.

The score remains the existing Total Score column; component values do not become additional
stock-list columns.

Existing display boundary: `_overall_score_text` and `StockTapeRow` in
[progressive_tape.py](../../src/market_leadership/ui/components/progressive_tape.py).
An application-level available scorecard must retain an available state so the list can
calculate the numeric total; only genuinely insufficient, unavailable, or failed evidence
produces a non-numeric state.

### Cash-Flow Risk Signal

A disclosure derived from dated cash-flow evidence, distinct from a component score:

- **Not assessed/unavailable**: cash-flow facts are unloaded, missing, invalid, stale,
  incomparable, or failed. The reason is stated; it is not interpreted as zero or as good cash
  generation.
- **Reported zero**: a known zero value for the named cash-flow measure and period.
- **Reported negative**: a known negative value; the actual amount, definition, and period
  remain visible as a cash-generation concern.
- **Reported positive**: a known positive value and period; this alone does not establish safety.

The signal does not diagnose insolvency, override component formulae, or alter weights.
Feature [011](../011-company-risk-evidence/spec.md) remains the owner of the detailed issuer
cash-flow warning and provenance behavior.

### Evaluation Finding

A reproducible test case and its conclusion about correctness, interpretation, limitation, or
proposed change. A finding records:

- Input facts, source/cutoff assumptions, cohort, and rules revision.
- Expected and observed metric, component, total, and disclosure states.
- Discrepancy and user-facing risk of retaining the existing behavior.
- Recommendation, tradeoffs, approval disposition, and a new rules revision if approved.

Findings are planning/review evidence, not a new runtime database.

## Relationships and State Flow

```text
Normalized Financial Facts
    └── Metric Peer Results (six metrics, calculated against Peer Context)
          ├── Quality (ROE + net margin)
          ├── Growth (revenue growth + diluted EPS growth)
          └── Cash Flow (FCF yield + OCF growth)
                └── Stock-List Total Score (requires all three components)

Cash-flow facts ──> Cash-Flow Risk Signal (separate from percentile/aggregate)
Evaluation cases ──> Evaluation Findings ──> approved rules revision, if any
```

For an explicit score request, results progress from not loaded to available, insufficient,
unavailable, or error. A failed refresh remains an error with its observation context; an older
result is not presented as newly assessed. Ordinary rendering does not start a financial request.
