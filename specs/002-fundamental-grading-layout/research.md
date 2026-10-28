# Research: Fundamental Grading Layout

**Date**: 2026-10-28
**Scope**: Phase 0 decisions for [plan.md](./plan.md). No live market-data calls made.

## 1. Missing app foundation and scope

**Decision**: Implement the three-tab shell and stock-selection foundation here.
The user explicitly selected expansion rather than an upstream prerequisite.

**Rationale**: Current `src/market_leadership/app.py` runs `st.navigation`, bootstrap
registers only Discovery and Industry Discovery, and no fundamental scorecard or
stock-member selector exists. Industry live mode intentionally fails closed for
unverified membership and rights. Current discovery includes top-level page config,
`st.stop()`, and page-switch handoffs: it cannot simply be placed inside a tab.

**Alternatives considered**: Wait for parent feature 001 (declined by user); add a
third routed page (violates approved architecture); import current page modules
unchanged (global side effects and stops break subsequent tabs).

**Resolution**: Extract callable renderers, configure once, use local returns and
namespaced state. Build selection against a dated validated catalog; add fixture
catalogs and retain a fail-closed live coverage gate. Do not infer industry members
from ETF holdings or Yahoo's single-company `.info` industry text.

## 2. Compact blocks and chart support

**Decision**: Use one `st.columns(3)` per scorecard, small `st.container()` blocks,
safe Markdown and `st.caption` for text, then `st.bar_chart` with `height=60`.

**Rationale**: Standard `st.metric` cannot supply the requested text hierarchy and
history placement as precisely. Installed Streamlit 1.66.1 supports integer chart
height and keyed containers. Use the supported 1.50 API subset: no new `.open`,
tab tracking, chart `key`, or undocumented HTML/CSS selector requirements.
Basic axes may remain; exact pixel reproduction beyond the textual matrix cannot
be verified because no image attachment is available.

**Alternatives considered**: Custom frontend/HTML component (unnecessary complexity);
Altair-only sparkline (not the requested `st.bar_chart`); hard fixed container
height for commentary (would clip wrapped text); newer lazy-tab APIs (would require
an unnecessary dependency floor change).

**Sources**:
- [Streamlit bar chart API](https://docs.streamlit.io/develop/api-reference/charts/st.bar_chart)
- [Streamlit containers](https://docs.streamlit.io/develop/api-reference/layout/st.container)
- [Streamlit tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs)
- Installed Streamlit signatures inspected without network; lockfile is 1.66.1.

## 3. Unified source bundle and ROCE

**Decision**: One `yf.Ticker(symbol)` per cache miss reads `.info`,
`.quarterly_financials`, `.quarterly_cashflow`, and `.quarterly_balance_sheet`.
All eight metric slots are generated together; availability is per metric.

**Rationale**: EBIT and capital employed are not both available from the originally
requested three components. User explicitly approved the extra balance sheet.
Do not substitute ROE, ROA, or Yahoo's unrelated return ratios for ROCE.

**Alternatives considered**: Keep ROCE N/A by source restriction (not chosen);
approximate capital employed from cash flow (financially invalid); add another API
or provider fallback (out of scope and against single-provider constraint).

**Sources**:
- [Ticker reference](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html)
- [Ticker usage and financial properties](https://ranaroussi.github.io/yfinance/reference/yfinance.ticker_tickers.html)
- [yfinance financial field definitions](https://github.com/ranaroussi/yfinance/blob/0.2.66/yfinance/const.py)

## 4. Quarterly coverage and historical charts

**Decision**: Treat four to eight bars as the allowed display range, not a provider
coverage guarantee. Render only actual comparable observations, latest eight in
chronological order; below four show a history limitation. Eight-quarter EPS
Consistency requires all eight quarters; each rolling historical count also
requires its own complete window.

**Rationale**: The installed yfinance 0.2.66 scraper comments that Yahoo returns a
maximum of four years or five quarters regardless of requested start date. Actual
per-symbol coverage can be less. A five-quarter revenue series supports at most
one latest-quarter YoY point, not four or five YoY bars. TTM ROCE needs four EBIT
quarters per observation. Do not mix quarterly, annual, and TTM points to fill bars.

**Alternatives considered**: Pad with zero, forward-fill, duplicate annual values,
or count five EPS quarters out of eight (all misleading); build a persistent
history collector or new provider (outside approved scope).

**Sources**:
- [Installed-version fundamentals scraper](https://github.com/ranaroussi/yfinance/blob/0.2.66/yfinance/scrapers/fundamentals.py)
- [Quarterly cash-flow reference](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.quarterly_cashflow.html)

## 5. Formula and commentary choices

**Decision**: Use explicit formulas and periods in
[fundamental-data.md](./contracts/fundamental-data.md): latest-quarter gross and
operating margins, same-quarter-prior-year Sales/EPS growth, TTM EBIT divided by
latest quarter-end capital employed for ROCE, quarterly OCF/net income Cash
Conversion, quarterly FCF/revenue, and positive diluted EPS quarter count.

**Rationale**: No existing implementation defines these eight raw metrics.
Quarterly formulas align chart slices with statements; TTM ROCE avoids presenting
unannualized quarterly EBIT as an annual return. Cash Conversion uses a positive
earnings denominator to avoid an apparently attractive ratio for a loss maker.
Negative valid numerators remain negative, not missing.

**Alternatives considered**: Mix `.info` TTM margins with quarterly charts without
disclosure; use quarter-on-quarter growth for YoY; treat negative baseline EPS as
ordinary percentage growth; infer premium pricing from gross margin alone.

**Commentary**: Negative operating margin can state "Losing money on operations";
otherwise use evidence-provided reviewed interpretations or neutral label/value
text. No industry-independent premium-margin threshold is introduced.

## 6. Failure visibility, cache, and active-view requests

**Decision**: Cache validated successful bundles for one hour, 256 entries. Clear
only the matching function arguments on refresh. Gate all financial calls behind
explicit Load/Refresh actions for the requested page of selected stocks.

**Rationale**: At manifest minimum, tab bodies run eagerly. Installed yfinance
0.2.66 statement internals catch `YFException` and also swallow some exceptions
inside `_create_financials_table`, ultimately returning empty DataFrames. No
per-call `raise_errors` parameter exists on the relevant statement getters.
Therefore an entirely empty statement is not proof of confirmed business absence:
flag acquisition uncertainty and do not cache it as successful empty data.
Nonempty statements with absent metric rows may be valid partial coverage.

**Failure path**: Attempt all four components with explicit statuses. If a fetch
fails or a whole component is ambiguously empty, raise a typed bundle acquisition
error carrying safe partial evidence. Streamlit caches no raised result; the UI
displays actionable error context and may still show the surviving metrics for
that action. Do not monkey-patch yfinance internals, mutate global debug settings,
or cache errors as data. Use bounded transient retries and user-triggered retry,
not automatic retry on every widget rerun.

**Alternatives considered**: A broad catch returning an empty dictionary (hides
errors); separate per-metric requests (duplicate traffic/inconsistent evidence);
global cache clear (affects unrelated users/symbols); trusting newer main-branch
debug configuration (not present in installed 0.2.66).

**Sources**:
- [Streamlit cache_data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [Caching overview](https://docs.streamlit.io/develop/concepts/architecture/caching)
- Installed yfinance 0.2.66 source/signatures and the tagged scraper above.

## 7. Data rights and temporal context

**Decision**: Current yfinance statements/profile are current observations, not
historical point-in-time evidence. Historical fixture contexts use fixture bundles;
unsupported historical live requests are rejected. Live membership/hosted display
requires reviewed provenance, coverage, and source permissions.

**Rationale**: Filing period alone does not establish historical public availability
or protect against restatements. Existing repository live-industry restrictions
must not be bypassed by the UI migration.

**Alternatives considered**: Attach current fundamentals to an old weekly snapshot
as if historically known (look-ahead); enable live lists without coverage review
(misleading and contrary to governance).

**Source**: [yfinance project usage disclaimer](https://github.com/ranaroussi/yfinance#readme).

## Research limitations and resolution status

Context7 was attempted but returned an invalid-API-key error. Public official docs,
tagged yfinance source, and installed API/source inspection were used instead.
A focused research agent verified public source feasibility; local implementation
tracing and final decisions were performed in the main workflow.

No live coverage or display permission is claimed. No unresolved design questions
remain; the explicitly documented live activation gate is not a promise of approved
rights or a future provider capability.
