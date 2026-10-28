# Phase 0 Research: Progressive Stock Screener

**Reviewed**: 2026-10-28. This replaces the former snapshot-first architecture decisions.
It is a design record, not a live-provider certification.

## 1. Runtime and Application Shape

**Decision**: Retain Python 3.12 and the constrained dependencies/lockfile in
[pyproject.toml](../../pyproject.toml). Use one app with **Sectors and Industries**,
**Industry Stocks**, and **Stock Detail** tabs and small, separately testable helpers.
Normalize the requested first label's spelling and leading whitespace.

**Rationale**: This directly satisfies the request and constitution v2.0.0 without a new
routing registry. The existing app uses `st.navigation`; replacing the primary journey
is a future implementation task, not something already accomplished by this document.

**Alternatives considered**: A single large function makes calculations and I/O hard to
test. Keeping separate discovery routes contradicts the progressive journey. A backend
API or provider plugin framework adds no required capability.

## 2. Tabs, Loading and Editable Selection

**Decision**: Assume tab bodies execute eagerly. Gate every remote load behind an
explicit load/refresh intent and validated prerequisites. Render already-loaded,
session-private view results on reruns; expired results are labelled expired and require
refresh before reuse as current evidence. Opening a tab alone does not fetch fundamentals.

Use `st.dataframe` single-row industry selection and a fixed-row `st.data_editor` with
only a Boolean selection column editable. All source/calculated columns and the index
are disabled. Store canonical selected instrument IDs separately from editor row numbers.
Keep `st.columns`/`st.metric` scorecards accessible for every matching stock via paging.

**Rationale**: The supported Streamlit minimum is 1.50. Current documentation describes
newer state-tracking tab options, but depending on them would unnecessarily raise the
minimum. Explicit actions work with the existing supported range. Data-editor cell
editing is sufficient; no unverified editor row-selection API is necessary.

**Alternatives considered**: Putting network calls unconditionally inside tab contexts
would load hidden stages. Using the editor's transient row offsets as stock identity
would corrupt selection when sorting, filtering or paginating.

Sources: [tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs),
[dataframe](https://docs.streamlit.io/develop/api-reference/data/st.dataframe),
[data editor](https://docs.streamlit.io/develop/api-reference/data/st.data_editor),
[session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state).

## 3. Single Free Source, Universe and Deployment Rights

**Decision**: Select yfinance for all runtime financial data. Do not select Massive from
an environment key, mix SEC data into missing fundamentals, scrape another site's index
list, or silently switch sources. A future alternative free source requires an explicit
replacement decision and conformance evidence, not a fallback branch.

Use paginated equity screening only as a **candidate discovery** mechanism. Inspect
actual payload totals, deduplicate instruments and validate exchange, common-stock type,
classification and dated market cap. Do not call a screener's returned set exhaustive
without evidence. Verify completion against source metadata; if total coverage cannot
be established, show an unknown total/partial coverage instead of a fabricated percentage.

**Rationale**: yfinance's `Industry`/`Sector` company lists are curated top lists, not
industry membership. The screener exposes exchange/region/sector/industry predicates and
pagination (`offset`, maximum page size 250 in the reviewed source), but this does not
establish exhaustive eligible US-common-stock coverage or historical classifications.
No documented S&P 500/Russell 2000 membership capability was established. Those optional
filters therefore remain unavailable unless the selected source substantiates dated
membership; no substitute exchange universe is selected automatically.

**Alternatives considered**: ETF holdings are not an entire industry's membership.
Present-day classifications do not prove historical membership. An additional free
endpoint is still a second provider and is outside this decision.

Keep the prior ETF review as evidence only: XBI and KRE are possible industry-specific
candidates; XOP spans multiple industries and is rejected as one narrow-industry proxy.
See [the historical review](contracts/us-industry-proxies.md). Source-qualification
metadata does not constitute a second runtime feed or permission to redistribute GICS.

The yfinance project describes research/educational use and warns that Yahoo's API is
intended for personal use. Verify actual deployment rights; a public quote endpoint,
ETF factsheet or this plan is not authorization for hosted display/derived results.

Sources: [yfinance project](https://github.com/ranaroussi/yfinance),
[screen](https://ranaroussi.github.io/yfinance/reference/api/yfinance.screen.html),
[Industry](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Industry.html),
[screener source](https://github.com/ranaroussi/yfinance/blob/main/yfinance/screener/screener.py),
[screener fields](https://github.com/ranaroussi/yfinance/blob/main/yfinance/const.py),
[Yahoo terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html).

## 4. Price Basis, Sessions and Corporate Actions

**Decision**: Request explicit adjusted daily OHLC and corporate actions; use completed
regular sessions from exchange-calendars. Returns use exactly one/five session intervals,
not calendar offsets or a benchmark-relative composite. Missing endpoints do not
forward-fill. Store actual observation dates separately from retrieval times.

**Rationale**: yfinance documents `auto_adjust=True` as split/dividend-adjusted OHLC.
The existing adapter discards high/low/open and does not request actions; it must be
extended for ADX, ATR, corridors and split-boundary verification. Volume must not be
dividend-adjusted or assumed comparable merely because price auto-adjustment is enabled.

Validate the pinned provider's volume units and split handling with mocked action
fixtures before normalizing them. If a split-crossing window's comparability is
unverified, mark affected volume/detector results insufficient while retaining valid
adjusted returns. Preserve the earlier trailing-incomplete-bar fix: incomplete tails
are omitted with an explicit latest-usable date; invalid interior bars remain errors.
Do not silently redate the requested cutoff to hide a stale/missing endpoint.

**Alternatives considered**: Calendar-seven-day returns differ on holidays.
Reusing the existing normalized-slope regime heuristic would not implement Wilder ADX.
Applying the price adjustment factor to volume would introduce dividend-related artifacts.

Source: [yfinance price adjustments](https://ranaroussi.github.io/yfinance/advanced/price_adjustment.html).

## 5. Financial Availability Is a Real Source Limitation

**Decision**: Calculate only the specified ratios from validated raw financial periods.
Keep source period ends, currency, publication/availability timestamps and version
provenance separate. Unknown publication dates or unproven historical vintages make
cutoff-dependent scoring insufficient, not retrospectively valid.

**Rationale**: Reviewed yfinance fundamentals code labels statement columns by `asOfDate`
and notes Yahoo returns at most four years or five quarters regardless of requested
start date. Its trailing mode returns one current TTM column. This cannot guarantee the
eight comparable quarters needed for non-overlapping current/prior TTM growth, nor
the filing dates/revision history required for point-in-time comparisons. Recheck the
locked version's behavior in implementation; the source review is not an immutable API SLA.

Current summary ROE/margins/growth, forward EPS, estimated earnings dates and period-end
dates do not establish the specified accounting definitions or publication timestamps.
Even an apparently sufficient ratio needs evidence that its inputs were available by
the cutoff. Annual figures may only serve a required TTM window if they exactly describe
that same window with valid availability evidence; no silent annual-growth substitution.

**Alternatives considered**: Lowering the history requirement, guessing publication
dates, zero filling, dropping a missing component or adding another provider would
change the agreed specification. Instead expose partial raw facts and explicit missing
reasons. Live Growth/Cash Flow blocks may therefore be unavailable; fixture correctness
does not unblock live financial capability.

Sources: [Ticker API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html),
[financial statement source](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/fundamentals.py).

## 6. Pure Scoring Utility

**Decision**: Keep the user-confirmed 0-100 equal-weight industry-peer percentiles, not
1-100 or letters. Exactly two metrics per block: ROE/net margin, revenue/diluted EPS
YoY, FCF yield/operating cash flow YoY. The utility takes normalized raw facts plus
the entire selected industry's pre-technical-filter universe and explicit cutoff.

**Rationale**: Industry-relative scores need a cohort, not a standalone stock dictionary.
Tied midranks and a minimum of five valid peers per metric are deterministic. Do not
round before ranking or average only the components that happen to be present.
The financial contract specifies formulas, periods and insufficiency.

**Alternatives considered**: Hand-picked thresholds or A-F labels would change the
clarified product. Selected-row or technical-match peers would make the same stock's
score change when only the displayed subset changes. An overall score is not requested.

## 7. Adaptive Consolidation

**Decision**: Implement the spec's versioned `quiet-sideways-v1` rule: Wilder ADX14 <20,
BW20 at most the median of 252 preceding valid BandWidths, and no configured volume
spike. Detect maximal consecutive qualifying runs of at least five sessions, without
a maximum duration. Derive corridor min(low)/max(high); do not impose a universal width.

**Rationale**: ChartSchool supports weak-trend and instrument-relative narrowness
concepts, not this exact combined rule or predictive effectiveness. Explicit formulas,
warm-up and reference fixtures prevent ambiguous library defaults. The previous-session
quiet-run option makes consolidation plus current spike coherent. Charts show the
latest interval by default and let users inspect older ones.

**Alternatives considered**: Fixed 20/60-day boxes and fixed corridor widths contradict
the adaptive requirement. A new technical-analysis dependency is unnecessary before
the existing NumPy/pandas stack is shown inadequate.

Sources: [ADX](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx),
[BandWidth](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth).

## 8. Cache, Load Budget and Failure Policy

**Decision**: In-memory `st.cache_data`, `persist=None`, bounded `max_entries`; initial
TTLs: daily OHLC 15 minutes, universe/membership/cap responses 24 hours, financial
responses 6 hours. Observation dates remain visible regardless of TTL; a cache hit
does not make old source evidence current. Bound source calls to the selected scope;
start with sequential requests and progress/cancel-at-safe-boundary behavior.

Use canonical per-instrument request keys for reusable prices/facts, and complete
query keys for catalog pages. Cache numerical transforms by payload fingerprints,
cutoff and rule version. Filters/row selection never invalidate financial payloads or
the full peer-score calculation. Refresh calls the relevant cached function's
argument-specific `.clear(...)`, not global `st.cache_data.clear()`.

**Rationale**: Default tabs execute eagerly, and Yahoo has no established numeric
request quota/SLA. Explicit loads, shared fresh results and bounded transient retries
reduce accidental rate pressure. Rate-limit failures are shown, not retried in a tight
loop. Cache valid payloads only; missing fields remain typed gaps, exceptions are not
converted into successful empty cached frames.

**Alternatives considered**: Persistent Parquet, SQLite, background workers and stale
success-shaped fallback add complexity or violate the chosen runtime model. Cache TTL
alone is insufficient without correct keys, source dates and clear failure states.

Sources: [cache_data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data),
[caching overview](https://docs.streamlit.io/develop/concepts/architecture/caching),
[provider exceptions](https://github.com/ranaroussi/yfinance/blob/main/yfinance/exceptions.py).

## 9. Evidence and Remaining Release Dependencies

**Decision**: Resolve design choices here; track unavailable source capabilities as
explicit release gates, not unanswered product questions. Tests must prove exact
outputs, cache request counts, full accessibility, state isolation and measured p95.
Do not claim real-time exchange data merely because queries happen on demand.

**Rationale**: Provider timing/entitlement, complete dated membership, financial
availability/history and split-comparable volume remain unverified. If evidence cannot
be supplied by the single selected source, the affected live feature remains unavailable
unless the owner approves a revised source or requirement.

**Alternatives considered**: Treating mocked source success as live certification would
hide the core feasibility limit.

Context7 documentation lookup failed with an invalid-key error. The research used
official Streamlit/yfinance documentation and source instead; no application network
acceptance or live entitlement verification was performed.
