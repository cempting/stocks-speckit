# Financial Evidence and Metric Contract

## Retrieval boundary

Internal injected reader: request -> one normalized bundle, or typed acquisition/
validation error with component-level context and safe partial evidence. It is not
an HTTP API. The production reader uses one `yf.Ticker(symbol)` instance and reads
`info`, `quarterly_financials`, `quarterly_cashflow`, `quarterly_balance_sheet`.
Tests inject a fake ticker factory; no live calls are needed for contract tests.

Profile fields such as name, symbol, currency, sector, and industry provide context
and identity checks, not membership authority or a substitute ratio. The three
statements are the authoritative period-aligned inputs for the calculations below.

Normalize documented yfinance pretty row labels to stable internal row IDs.
Absent rows remain absent. Handle `Diluted EPS`/`DilutedEPS` and equivalent
pretty/canonical forms via an explicit mapping, not fuzzy financial-name guessing.
Use reported currency/scale; mismatched periods/units make affected ratios unavailable.

## Metric definitions

Ratios are stored as fractions, rendered once as percent. Use latest completed
reported quarter Q; a usable date is not a guarantee of point-in-time publication.

| ID / label | Formula and required rows | Period / validity |
|------------|---------------------------|-------------------|
| `gross_margin` / Gross Margin | Income `Gross Profit / Total Revenue` | Q; revenue > 0 |
| `operating_margin` / Operating Margin | Income `Operating Income / Total Revenue` | Q; revenue > 0 |
| `roce` / ROCE | Sum of four consecutive quarterly income `EBIT` observations ending Q, divided by balance `Total Assets - Current Liabilities` at Q | TTM EBIT / Q-end capital employed; denominator > 0; all four EBIT quarters and matching balance required |
| `sales_yoy` / Sales YoY | `Total Revenue[Q] / Total Revenue[Q-4] - 1` | Same fiscal quarter prior year; baseline revenue > 0 |
| `eps_yoy` / EPS YoY | `Diluted EPS[Q] / Diluted EPS[Q-4] - 1` | Same fiscal quarter prior year; baseline diluted EPS > 0, current EPS may be negative |
| `eps_consistency` / EPS Consistency | Count of strictly positive `Diluted EPS` over Q-7 through Q | All eight consecutive quarters required; zero does not count |
| `cash_conversion` / Cash Conversion | Cash-flow `Operating Cash Flow /` income `Net Income` | Q; net income > 0; same period/units |
| `fcf_margin` / FCF Margin | Cash-flow `Free Cash Flow /` income `Total Revenue` | Q; revenue > 0; same period/units |

For FCF only, if `Free Cash Flow` is absent but both `Operating Cash Flow` and
`Capital Expenditure` exist for Q, derive `OCF - abs(Capital Expenditure)` and mark
the derived provenance. Never replace missing capex with zero. A reported FCF row
takes precedence; do not combine differently scaled figures or cumulative YTD
cash flows with standalone quarterly income. If period basis cannot be verified,
the affected ratio is unavailable.

Do not substitute net margin for Operating Margin, ROE for ROCE, EBITDA for EBIT,
basic EPS for diluted EPS, or `.info` growth estimates for statement-derived YoY.
Absent latest-quarter evidence does not silently choose an older quarter from a
different component. The scorecard's quarter context and each TTM/YoY period remain
visible. Financial-provider coverage can make some slots unavailable.

## Commentary and availability

- Available negative Operating Margin: `Losing money on operations`.
- A reviewed interpretation supplied with the exact metric/evidence may be used.
- Otherwise use neutral `{exact metric label}: {formatted value}`; no unsupported
  premium-pricing or investment conclusion.
- Invalid/missing/non-finite evidence or invalid denominator: value `None`,
  formatted value `N/A`, commentary `Data not available`. Keep detailed reason
  outside the required exact helper text.
- All percentage metrics: one decimal and `%` unless an established integrated
  formatter already specifies precision. EPS count: exactly `X/8 quarters`.

## History contract

Recompute the same metric at each actual completed quarter; take the most recent
contiguous comparable run, maximum eight. Four is the minimum chart size.
The latest-quarter value can be available while its chart is not.
Retain all returned source quarters until calculations finish; the eight-point
limit applies to plotted output, not raw supporting quarters needed for growth,
TTM, or rolling EPS windows. Do not fetch a second provider to extend the window.

- Five source revenue quarters support one YoY point, not five.
- Four historical EPS-count points need at least eleven complete EPS quarters.
- Four historical TTM ROCE points need seven EBIT quarters and four aligned
  balance-sheet quarters.
- Do not create annual/TTM duplicates, interpolate gaps, pad short series, turn
  missing into zero, or append `.info` ratios as additional quarterly observations.

## Cache and error contract

- Cached function uses `@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)`.
- Hashed inputs include `provider_id`, normalized symbol, cutoff policy/date,
  history window, frequency, bundle schema version. Underscore-injected test
  factories must not permit production provider identity to disappear from keys.
- Successful bundles are serializable, immutable by convention/copy at boundaries,
  and contain no credentials, session identities, or user selections.
- Cache pure transformations using bundle content fingerprint plus calculation
  version; refresh obtains a new bundle/fingerprint, not a stale result.
- Clear only the selected request with cached-function `.clear(*matching_args)`.
  Never call global `st.cache_data.clear()` for a stock refresh.
- Transient retry limit is existing configured `retry_limit` (default two retries);
  non-retryable validation/authorization errors are immediate. Preserve error
  category/provider/component/action without exposing raw sensitive payloads.
- Installed yfinance may swallow statement exceptions into empty frames. Entire
  component emptiness is `unverified_empty`: raise the typed acquisition error,
  show an explicit source limitation/retry action, and do not cache the result.
  Valid data from other components may be rendered in the same failed-request
  response without relabelling that response successful.
- A missing row inside a valid nonempty statement is normal metric insufficiency,
  not necessarily a failed request. Cache validated partial row coverage.
- A failed Refresh must not silently present an older cached bundle as current.

## Membership and source activation

Local catalog JSON has schema version, market, classification scheme, observation
date, source ID, evidence mode, coverage description, approval reference, and dated
entries with instrument/company IDs, symbol/name/exchange/currency, sector and
industry IDs, effective-from/to. Validate the entire catalog before selection.

Missing/invalid catalog -> actionable coverage error; zero members in a valid
catalog -> explicit zero-member result with coverage context. No complete
membership claim from top-company lists, ETF holdings, or `.info` classification.

Live flow requires one selected yfinance provider and a reviewed compatible catalog
and display-rights approval. Multi-provider or Massive-selected configuration
produces an actionable unsupported-source message; do not silently call yfinance.
Fixture mode is entirely offline and never fills gaps with live data.

Historical snapshot contexts cannot use present `.info`/restated statement data as
if it were historically known. Reject unsupported historical live requests; use
matching fixture bundles for deterministic historical demonstrations.
