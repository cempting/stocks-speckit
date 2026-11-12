# Stock Detail UI Contract

**Authority**: [Feature 017 specification](../spec.md). This contract extends the existing
[stock-detail workflow](../../015-dedicated-stock-lookup/spec.md) and preserves
[feature 001 consolidation semantics](../../001-market-leadership-screener/contracts/consolidation.md),
[feature 002 financial metric definitions](../../002-fundamental-grading-layout/contracts/fundamental-data.md),
and [feature 011 company-evidence safeguards](../../011-company-risk-evidence/contracts/company-evidence-acquisition.md).

This is a user-interface contract, not a new HTTP API, root tab, data provider, or persistence
format. Data shapes and state invariants are in [data-model.md](../data-model.md).

## Detail Context and Loading

- The detail remains bound to one explicitly selected, verified stock listing and its existing
  issuer association. Changing listing clears/revalidates all listing-dependent detail state.
- Preserve existing stock lookup/navigation, history load, financial-evidence load, refresh,
  peer scorecard, risk warnings, and evidence controls. Do not fetch history or fundamentals
  merely because a component renders or the viewport changes.
- Keep the selected chart range session-local and namespaced. Initial range is `6m`; ordinary
  reruns preserve a valid selection for the current listing.
- The selected time range is a user action. Reuse any loaded history that covers the new range
  and required warm-up; otherwise request only the missing range and warm-up through the existing
  explicit history-loading boundary and cache.
- Use the current selected provider only. Show source, requested/observed dates, freshness, and
  safe actionable failure/coverage details through the existing evidence disclosure.

## Chart

### Controls

Show exactly six selectable period labels in this order:

`1m` | `3m` | `6m` | `12m` | `18m` | `24m`

Changing the selection updates the visible date range but not the selected listing or any
financial/scorecard result. Each range ends at the latest completed available session and covers
the requested month-based interval; gaps and a listing's actual start remain visible.

### Plot and Overlay

- Keep price history, its 50-session and 150-session simple moving averages, and daily volume in
  one chart view, aligned by trading-session date.
- Keep volume visually distinct and legible without implying that it shares the price-value
  scale. Reuse the current chart composition and visual conventions.
- Moving averages use completed adjusted daily closes. Include warm-up observations before the
  visible start without showing those dates as part of the selected range.
- Draw an average only when its required observations are available. Otherwise identify its
  insufficient/unavailable state; do not draw zeros or substitute another period.
- Identify the selected listing and visible date range. Missing volume does not hide valid prices;
  invalid or incomplete data shows its status and does not masquerade as a complete series.
- Chart labels, selected period, volume, and essential evidence explanations remain accessible
  without hover and readable at phone width.

### Consolidation Annotation

- Use only typed intervals from feature 001's `quiet-sideways-v1` detector, calculated for the
  selected listing and cutoff. Never borrow an industry or parent-security interval.
- Highlight at most the latest detected interval by default with the established subtle time-span
  shading and observed horizontal price corridor. Permit inspection of older intervals without
  changing the selected stock or chart period.
- Make interval dates, duration, corridor, cutoff, and truncation/insufficiency information
  available beside/below the chart or through an accessible detail disclosure.
- Distinguish sufficient history with no qualifying interval from insufficient detector evidence.
  Do not call an annotation a predicted breakout, entry signal, or future return.

## Company Profile and Financial History

- Keep verified listing identity visible. When profile evidence is loaded and verified, show
  company name, listing symbol, exchange, verified sector/industry where available, and market
  capitalization with currency and observation date.
- Use the existing explicit financial-evidence action. Show the latest eight comparable fiscal
  quarters when available; preserve the reporting date and actual fiscal-quarter order.
- Show supported quarterly revenue, net income, diluted EPS, operating cash flow, capital
  expenditures, free cash flow, cash and equivalents, total debt, shareholders' equity, and
  shares outstanding. Do not hide supported facts because a neighboring metric is missing.
- Make supported derived metric definitions, values, units, periods, and status inspectable.
  Reuse established feature 002 formulas for overlapping scorecard metrics; additional ratios are
  descriptive history only and do not enter the score.
- Keep P/E, P/S, EV/EBITDA, and FCF yield optional, dated valuation snapshots; do not place them
  in the quarterly operating series.
- Identify source, reporting currency/scale, fiscal period, reported/derived origin, and
  publication/observation date when known. Distinguish zero, negative, missing, insufficient,
  stale, partial, unresolved identity, and failed acquisition.
- Do not claim that a missing row means the company reported zero. Do not relabel cumulative
  year-to-date cash flow as standalone quarterly cash flow, combine incompatible currencies, or
  present current market value as a historical valuation.

## Responsive and Accessible Behavior

- Preserve the current detail layout and page navigation; do not add a root tab or duplicate
  desktop/mobile controls.
- At 1440 CSS pixels, keep the chart, controls, and financial evidence readable without clipping.
- At 390 CSS pixels, controls remain touch-operable, chart content remains readable, and company
  evidence reflows or stacks without overlapping or page-wide horizontal scrolling.
- A wide financial table may scroll inside its own clearly discoverable container. Important
  evidence and statuses must not depend solely on hover or color.
- Browser acceptance covers the affected detail at 1440px and 390px. Automated rendering or
  AppTest assertions alone do not prove responsive usability.

## Acceptance Cases

| State/action | Expected result |
|---|---|
| Verified listing, complete daily history, default range | `6m` selected; price, 50/150-session averages, and aligned volume appear for the same listing/date context. |
| Each of the six period controls | Visible range updates to the selected period; existing sufficient history is reused and unrelated financial/score results remain unchanged. |
| Short/gapped daily history | Valid series remain visible; only unsupported overlays or evidence are marked insufficient/unavailable. |
| Latest qualifying consolidation | Subtle latest interval and observed bounds appear with dates/duration; no breakout prediction is made. |
| No qualifying interval versus insufficient history | Distinct visible statuses. |
| Verified company with partial quarterly facts | Available values appear with period, units, source/origin, and status; missing metrics are not zero-filled. |
| Current valuation without a historical point-in-time match | No historical valuation series is shown; the limitation is explicit. |
| Failed or unresolved source/identity check | Actionable failure or identity status appears; no unverified company facts attach to the listing. |
| 390px phone and 1440px desktop | Detail controls and evidence remain accessible without clipping/overlap/page-wide horizontal scroll; any wide table scroll remains local. |
