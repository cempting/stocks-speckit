# Fundamental Grading UI Contract

## Entrypoint and selection journey

- Keep `streamlit_app.py` as the entrypoint. Configure Streamlit once.
- Exactly three primary `st.tabs` labels: `Sector/Industry Screen`,
  `Industry Deep-Dive`, `Fundamental Grading`.
- Remove routed page transitions from the active flow. Existing discovery and
  weekly evidence retain their true labels and meanings, not a relabelled return.
- Tab 1 selects industry within sector/evidence context; Tab 2 shows dated member
  rows with coverage/source and selects stable stock identities.
- Tab 3 displays selected stocks, five per page, with explicit Load fundamentals
  and Refresh displayed stocks actions. Pagination alone never fetches.
- No selection -> explain how to select stocks, no provider calls.
- Inactive/eagerly rendered tabs do not cause financial requests. Explicit actions
  and current request context authorize calls, not merely `with tab:`.
- Widget keys are namespaced and stable per context/instrument. Validate and clear
  invalid dependent state before widgets are created; display why it changed.
- Changes to industry/mode/cutoff invalidate loaded results and dependent selection.
  Ordinary reruns retain valid selections and successful evidence via cache.

## Per-stock matrix

One stock heading with symbol/name and evidence cutoff/source/fetch time, then one
`st.columns(3)` call. No per-metric structural columns.

| Column 1: Quality | Column 2: Growth | Column 3: Cash Flow |
|-------------------|------------------|---------------------|
| Gross Margin | Sales YoY | Cash Conversion |
| Operating Margin | EPS YoY | FCF Margin |
| ROCE | EPS Consistency | No ninth slot |

Each metric sits in its own small `st.container()`:

1. Exact metric label using Markdown.
2. Formatted value, prominent but compact, not `st.metric`.
3. Metric-specific commentary directly beneath the value, inside the same block.
4. Small nested container containing `st.bar_chart` with `height=60`, or separate
   `Insufficient quarterly history` caption when fewer than four points exist.
5. Period/definition/source detail remains accessible through captions/details
   without interposing unrelated content between value and commentary.

Use safe built-in Markdown/captions. Do not inject unescaped provider text through
`unsafe_allow_html`, add chart libraries, or rely on undocumented DOM selectors.
Only chart height is fixed; metric containers allow wrapped commentary without
clipping. Shared styles must not alter discovery charts or unrelated legacy metrics.
Chronological chart x-values are actual quarter-end dates; y-values match metric
units, including valid negatives. Preserve basic axis/hover labels as supported.

## Missing-data and failure display

- Unavailable slot: label, exactly `N/A`, then exactly `Data not available`.
- Keep all three headings and eight slots even when all are unavailable.
- A missing history chart is not missing current financial data; do not replace a
  valid current value/comment with the metric fallback merely because history is short.
- Detailed insufficiency reasons and operational errors appear separately. Failed
  or uncertain fetches show a visible warning/error with component and retry
  context; valid partial metrics may remain readable.
- A symbol/context change never leaves another stock's text or chart in place.
- Valid zero/negative performance is not missing. EPS counts render exactly
  `0/8 quarters` through `8/8 quarters`; incomplete eight-quarter evidence is N/A.
- Live coverage/rights/source restrictions remain explicit; fixture labels are
  conspicuous and no financial calls occur from fixture mode.

## Intentional migration

The root three-tab experience replaces `/discovery` and `/industry-discovery`
routes. Update README with new entrypoint/selection instructions and retired-link
guidance. No extra routing layer is added to preserve obsolete page paths.
Do not change existing discovery calculations or introduce new aggregate scoring.

## Acceptance evidence

- AppTest: entrypoint has three tab labels, exact 3/3/2 metric grouping/order,
  eight label/value/commentary slots per stock, selection state transitions, and
  zero eager network calls.
- Parameterized tests: eight single-missing cases, all-missing, finite negative/zero,
  all nine valid EPS counts, invalid/incomplete EPS, long comments, and stock switch.
- Inspect chart specifications/captured chart data for exactly 60 height, periods
  ascending, four-to-eight points, no padded values; use browser check for actual
  nesting/wrapping and desktop/narrow layouts because AppTest alone is not visual proof.
