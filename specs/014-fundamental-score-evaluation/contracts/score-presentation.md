# Score Presentation Contract

**Owner**: [Feature 014](../spec.md), in coordination with [001](../../001-market-leadership-screener/spec.md),
[006](../../006-stock-table-columns/spec.md), and [011](../../011-company-risk-evidence/spec.md).

This is a user-visible and internal score-boundary contract for the existing Streamlit app.
It adds no remote endpoint, new provider, persisted score store, or stock-list column.

## Scoring and Context

1. A score result is bound to the instrument, complete eligible industry cohort, membership
   date, analysis cutoff, financial observation basis, and applicable rules revision.
2. The baseline uses the six documented industry-peer metrics in 001; every metric requires
   the existing minimum of five valid peers. Quality, Growth, and Cash Flow each require both
   of their metric percentiles and equally weight the pair.
3. Total Score is the equal arithmetic mean of the three finite, available component scores.
   The displayed precision remains one decimal place. Missing components do not produce a
   partial mean or zero.
4. Component and total scores are relative comparisons, not absolute measures of safety,
   solvency, or investment suitability. Peer context is available wherever the result is
   interpreted.
5. Any changed definition, direction, eligibility rule, threshold, or weight requires an
   evaluation finding, explicit approval, and rules revision before changed values are shown.

## Stock-List Presentation

- Preserve the exact five visible columns and order from the 006 stock-table contract.
- Preserve Total Score's existing display states: numeric calculated, Not loaded, Insufficient,
  Unavailable, and Error.
- The list value and its corresponding component scorecard agree for the same instrument,
  cohort, cutoff, and rules revision.
- Detail sufficient for interpretation appears through the existing scorecard/detail surface;
  do not add mandatory component columns.
- The stock detail exposes all six peer metric results with raw value, percentile, valid-peer
  count, state/reason, and known source, period, currency, and cutoff context. Unknown
  provenance is identified as unavailable; it is never inferred from fetch time or another
  metric view.
- Rendering, selecting, paging, or sorting the list does not initiate a score or financial
  evidence request. Existing explicit load and refresh actions remain the only load triggers.

## Cash-Flow Disclosure

- Not loaded, missing, invalid, stale, incompatible, insufficient, and failed evidence are
  distinct from reported zero or negative values.
- A missing or unassessed cash-flow component is visibly warned and cannot be described as
  healthy. The Total Score remains unavailable when its required component is unavailable.
- Reported zero or negative OCF/FCF retains its actual amount, definition, source, and period.
  A negative value is a cash-generation concern, not proof of insolvency.
- A favorable relative percentile does not hide a negative raw value; a positive value alone
  is not a guarantee of safety.
- Score/risk language is historical decision support, never personalized advice or a trade
  instruction.

## Error, Freshness, and Provenance

- Preserve the selected source, publication availability, fiscal period, currency, cutoff, and
  known coverage limitations where available.
- A failed refresh is visible; a prior successful observation is not labelled fresh.
- Incompatible peer cohorts, cutoffs, or rule revisions are not silently compared or reused.
- Provider changes, provider fallback, and new external data collection are outside this
  contract.
