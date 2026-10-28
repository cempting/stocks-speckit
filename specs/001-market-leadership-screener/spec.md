# Feature Specification: Progressive Stock Screener

**Feature Identifier**: `001-market-leadership-screener`

**Short Name**: `progressive-stock-screener`

**Created**: 2026-10-26

**Updated**: 2026-10-28

**Status**: Draft — revised scope; ready for implementation planning

**Input**: Update the existing specification for three progressive stages: rank gaining and
declining industries by one-day or one-week price performance; inspect and filter their member
stocks; and compare each matching stock's Quality, Growth, and Cash Flow scorecards. Support
combinable consolidation, above-50-session-average, above-150-session-average, and volume-spike
criteria. Detect consolidation duration and corridor adaptively and show subtle annotations and
metrics on sector, industry, and stock charts.

## Scope and Revision Authority

This specification replaces the previous active requirements for this feature, in alignment with
constitution v2.0.0. The experience is one progressive screening journey, not separately routed
sector and industry workflows. The initial market is US equities. Persistent weekly artifacts,
three-/six-/twelve-month composite leadership scores, 50-session composite status, market-regime
classification, multi-market comparison, constituent breadth, and observed fund flows are not MVP
requirements. They MUST NOT be substituted for the short-period returns or fundamental blocks
specified here.

Existing implementation, prior task completion records, and data contracts are historical work,
not evidence that the revised feature is implemented. Existing plan, research, data-model,
quickstart, contracts, and tasks must be reconciled in subsequent planning/task-generation
workflows before further implementation. This revision does not instruct deletion of old artifacts
or renumbering of completed tasks.

## Clarifications

### Session 2026-10-28 — Current Decisions

- The three stages are Sector/Industry Screen, Industry Deep-Dive, and Fundamental Grading.
  Selection progresses within the same experience and retains valid parent context.
- Quality, Growth, and Cash Flow use equal-weight industry-peer percentile scores on a 0–100
  scale, with raw metrics, periods, and sufficiency visible.
- Stock criteria are independently selectable and combine using **AND**. No enabled criteria
  means all available members of the selected industry and universe.
- Criteria are consolidation/heartbeat, close above the 50-session simple moving average, close
  above the 150-session simple moving average, and volume spike.
- Volume spike defaults to latest completed-session volume at least twice the mean of the
  preceding 20 completed sessions; lookback and multiplier are configurable.
- Consolidation can last weeks, months, or years. Its duration and corridor MUST be inferred from
  the instrument's own price/volatility/volume history, not chosen from fixed duration presets or
  a universal corridor percentage. The detected interval and corridor are shown subtly on charts,
  with duration, dates, width and detection context adjacent to or below the chart.
- The US universe supports large-, mid-, and small-cap discovery, NYSE and Nasdaq listings, and
  S&P 500 and Russell 2000 membership filters where documented dated coverage is available.
  Additional named sources may be supported only with explicit provenance and coverage.
- Industry representations prefer a documented adequate ETF; if none is qualified, use the
  largest verified market-cap member stock at the observation date, labelled single-company proxy.
  Neither representation determines the industry stock-membership list.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover Gaining and Declining Industries (Priority: P1)

As a self-directed investor, I want to compare industries within selected sectors and a clearly
defined US universe over one day or one week, so I can identify areas worth investigating.

**Why this priority**: Industry screening provides useful discovery before stock selection or
fundamental grading is available.

**Independent Test**: Use dated US industry memberships and known representation prices, select
sectors and the return period, and verify ordering, positive/negative/neutral labels, proxy
disclosures, and explicit unavailable results.

**Acceptance Scenarios**:

1. **Given** supported US industries, **When** discovery opens, **Then** a ranked industry table
   defaults to one-week absolute price performance, with name, parent sector, representation,
   period, return, direction, observation date, and sufficiency.
2. **Given** one-day and one-week prices, **When** the user switches the period, **Then** returns,
   ranks, and direction labels update consistently; zero return is neutral.
3. **Given** selected sectors and universe filters, **When** discovery is filtered, **Then** only
   eligible industries appear, the ranking scope is visible, and tied returns have deterministic
   name/identifier order.
4. **Given** an industry selection, **When** the user proceeds, **Then** its member-stock stage
   retains industry, sector, universe, return period, and observation context.
5. **Given** a missing qualified representation, **When** the table is displayed, **Then** the
   industry is shown as insufficient without a return/rank and without a guessed fund or stock.
6. **Given** a sector or industry chart, **When** consolidation evidence exists, **Then** the chart
   and adjacent metrics describe the detected interval/corridor without implying a future breakout.

---

### User Story 2 - Filter an Industry's Member Stocks (Priority: P1)

As an investor, I want an interactive table of industry members and combinable technical criteria,
so I can narrow the available stocks without losing membership or coverage context.

**Why this priority**: This turns industry discovery into a usable stock screen.

**Independent Test**: Open a known industry directly as controlled input; verify its complete
available member list, the four criteria independently and together, selection state, and
consolidation charts against controlled price and volume histories.

**Acceptance Scenarios**:

1. **Given** an industry and selected universe, **When** no criteria are enabled, **Then** all
   available member stocks appear once with coverage counts and membership date/source.
2. **Given** enabled technical criteria, **When** the table is filtered, **Then** only stocks
   satisfying every enabled condition appear; unknown required evidence is not treated as a pass.
3. **Given** a completed closing price exactly equal to its moving average, **When** the relevant
   above-average criterion is applied, **Then** that criterion fails.
4. **Given** a known quiet sideways history followed by a volume spike, **When** both consolidation
   and spike criteria are enabled, **Then** the prior detected consolidation and current spike can
   both match without treating the spike as part of the quiet interval.
5. **Given** histories with different volatilities and sideways intervals, **When** charts are
   inspected, **Then** detected durations and corridor widths depend on each history, not a
   single fixed duration or percentage; weeks-, months-, and years-long intervals can be represented.
6. **Given** selected rows or changed criteria, **When** the experience updates, **Then** valid
   selections persist, excluded/invalid selections are cleared with visible context, and source
   financial/price data cannot be overwritten by table edits.
7. **Given** an empty result or incomplete source coverage, **When** filtering finishes, **Then**
   the user can distinguish no matches, missing evidence, and missing membership coverage.

---

### User Story 3 - Compare Fundamental Scorecards (Priority: P2)

As an investor, I want a unified scorecard for each matching stock with Quality, Growth, and Cash
Flow blocks, so I can compare underlying financial evidence without mistaking missing data for
poor performance.

**Why this priority**: Fundamental grading adds a consistent comparison to the usable price-based
screen without changing its industry membership or technical matches.

**Independent Test**: Supply at least five industry peers with known accounting metrics and verify
raw values, percentile ties, block scores, period labels, invalid denominators, and missing data.

**Acceptance Scenarios**:

1. **Given** matching stocks with sufficient data, **When** grading is opened, **Then** every stock
   has the same three labelled blocks and comparable raw metrics, including via pagination.
2. **Given** ROE and net margin, **When** Quality is calculated, **Then** its value is the equal
   mean of the two valid industry-peer percentile scores.
3. **Given** revenue and diluted EPS growth, **When** Growth is calculated, **Then** its value is
   the equal mean of those two valid industry-peer percentiles.
4. **Given** free-cash-flow yield and operating-cash-flow growth, **When** Cash Flow is calculated,
   **Then** its value is the equal mean of those two valid industry-peer percentiles.
5. **Given** missing financial periods, non-comparable metrics, or invalid growth denominators,
   **When** a block depends on them, **Then** it is insufficient with a reason; other valid blocks
   remain visible.
6. **Given** a changed technical stock filter but unchanged industry/universe/financial cutoff,
   **When** scorecards update, **Then** peer scores for retained stocks do not change merely
   because fewer stocks are displayed.
7. **Given** scorecards, **When** a user reads their definitions, **Then** it is clear that the
   scores are relative historical comparisons, not buy/sell instructions or absolute quality grades.

### Edge Cases

- Non-trading days and open sessions use the latest completed US trading session; one week means
  five completed trading-session intervals, not a presumed calendar Friday.
- Missing starting/ending observations make the affected return insufficient; no forward-filled
  or misaligned benchmark prices are silently used.
- IPOs and thin histories can support a one-day return while lacking an SMA or consolidation
  history. Missing one criterion does not hide other known metrics.
- Splits require consistently adjusted price histories and comparable volume units; artificial
  corporate-action jumps must not become corridor breaks or volume spikes.
- Flat prices, zero volume, suspended trading, and undefined trend/volatility calculations are
  not automatically evidence of healthy consolidation.
- A trending low-volatility series is not sufficient merely because its volatility is low.
  Quiet volume alone is not consolidation.
- A detected interval may begin before available history or remain open at the current cutoff.
  These limits are marked rather than presented as exact historical boundaries.
- Index, exchange, or classification membership changes retain their effective dates. Missing
  index coverage is not replaced with the full exchange universe without an explicit user change.
- Duplicate symbols/listings are reconciled by stable instrument identity; a primary listing is
  not confused with an ETF, ADR, preferred share, or another class of the same company.
- Negative equity makes ROE non-comparable. A zero/negative prior EPS or operating cash flow
  makes its percentage-growth metric unavailable, not an extreme positive percentile.
- Genuine negative margins, revenue growth, and free cash flow remain negative values; absent
  fields are never replaced with zero.
- Rate limiting, interrupted loads, or partial failures expose affected coverage and preserve
  valid independent results without a success-shaped fallback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST provide three progressive stages within one screening experience:
  Sector/Industry Screen, Industry Deep-Dive, and Fundamental Grading. Each stage MUST show the
  active selection and explain unavailable prerequisites.
- **FR-002**: Initial runtime discovery MUST support US-listed common stocks, NYSE/Nasdaq exchange
  filters, and large-/mid-/small-cap filters. Available exchanges, instruments, index universes,
  sources, dates, and actual coverage MUST be visible.
- **FR-003**: S&P 500 and Russell 2000 universe filters MUST use documented membership with an
  effective date. Unavailable memberships MUST be labelled unavailable rather than implied
  complete or substituted with current/other-universe data.
- **FR-004**: Multiple selected indices MUST form a deduplicated union; selected exchanges and cap
  bands MUST then intersect that union. Without an index selection, the available US common-stock
  universe applies. Multiple sectors form a union within that universe.
- **FR-005**: Industry ranking MUST use the selected representation's absolute adjusted price
  return over one completed-session interval or five completed-session intervals:
  `100 * (ending close / starting close - 1)`. The default period MUST be one week.
- **FR-006**: Positive returns MUST be labelled gaining, negative declining, and zero neutral.
  Ranking MUST default to descending return within the displayed, labelled industry selection;
  ascending return and gaining/declining/neutral/all filters MUST be available. Exact ties share
  rank and use name then stable identifier for display order; insufficient rows have no rank.
- **FR-007**: Every industry row MUST show parent sector, representation symbol/type, period,
  return/direction, rank, observation date, source and sufficiency. A representation's membership
  and exposure limitations MUST be accessible.
- **FR-008**: Prefer a documented industry-specific ETF; otherwise use the largest verified
  market-cap stock among dated industry members, breaking equal caps by stable identifier.
  Stock proxies MUST be labelled single-company proxies; absent qualified evidence leaves the
  industry insufficient. A broad or mismatched fund MUST NOT be presented as one industry's proxy.
- **FR-009**: The member-stock table MUST show all available matching members of the selected
  industry and universe, without a silent top-N cap. Pagination is permitted. It MUST show stock
  identity, industry, market cap, selected-period return, technical criterion states and coverage.
- **FR-010**: Table interaction MUST permit stock selection and sorting, not alteration of
  retrieved prices, fundamentals, classifications, or calculated scores. All matching stocks
  MUST have access to scorecards; row selection may focus comparison, not silently exclude others.
- **FR-011**: Consolidation, above-SMA50, above-SMA150, and volume spike MUST each be optional.
  Enabled criteria combine with AND; no enabled criteria means all available members. Each
  criterion MUST report pass, fail, or insufficient; insufficient does not pass.
- **FR-012**: Above-SMA50 and above-SMA150 MUST require the latest completed close strictly greater
  than the arithmetic mean of the latest 50 or 150 completed-session closes, respectively,
  including the ending close. Short histories are insufficient.
- **FR-013**: Volume spike MUST require ending-session volume at least a configurable multiple
  of mean volume over the preceding configurable number of sessions, excluding the ending one.
  Defaults are 2 times and 20 sessions. Lookback must be a positive whole number and multiplier
  positive; missing or nonpositive baseline volume is insufficient.
- **FR-014**: Consolidation detection MUST infer quiet sideways intervals and their price corridor
  from each instrument's own history. It MUST NOT require a user-selected fixed duration or apply
  a universal corridor width. The initial reproducible heuristic is defined below.
- **FR-015**: Sector, industry, and stock charts MUST expose available consolidation intervals with
  subtle horizontal price boundaries and a lightly shaded detected time span. The default chart
  MUST show at most the latest detected interval; older intervals may be inspected on request.
  No additional indicator panels are required to understand the annotation.
- **FR-016**: Beside/below each annotated chart, show interval start/end, ongoing/completed state,
  duration in trading sessions and approximate calendar time, lower/upper corridor bounds, width
  in price units and percent, typical volatility, volume context, detection cutoff and whether
  history truncates the interval. A missing interval and insufficient evidence MUST be distinct.
- **FR-017**: Changing sector, industry, universe, or criteria MUST retain valid selections and
  clear only invalid dependent industry/stock choices. User selection state MUST remain private
  to the session and survive ordinary reruns.
- **FR-018**: Fundamental grading MUST display the same Quality, Growth and Cash Flow blocks for
  every matching stock, with 0–100 values, raw inputs/units, fiscal periods, publication dates,
  peer-group definition/count and explicit insufficiency.
- **FR-019**: Quality MUST equally weight ROE and net profit margin; Growth MUST equally weight
  revenue YoY growth and diluted EPS YoY growth; Cash Flow MUST equally weight free-cash-flow
  yield and operating-cash-flow YoY growth. Metric definitions and percentile rules below apply.
- **FR-020**: Peer groups MUST contain the selected industry's members in the selected universe
  before technical filters or row selection, evaluated at the same information cutoff. Each
  metric needs at least five valid peers; each block needs both constituent metric scores.
  Missing values MUST NOT be zero-filled or cause weights to be silently redistributed.
- **FR-021**: Financial comparisons MUST use information published by the analysis cutoff, matching
  accounting-period definitions and currency bases. Incompatible, missing, or invalid financial
  observations MUST be insufficient with a reason; other valid stock blocks remain visible.
- **FR-022**: Data MUST be requested on demand from the single selected free source. Repeated
  interactions within the displayed freshness window MUST reuse unchanged results without
  repeated remote requests. Expired data/failed refreshes MUST NOT be shown as freshly retrieved.
- **FR-023**: Every stage MUST expose data source, observation/fiscal period, availability or
  retrieval date where known, freshness, coverage and limitations. User-visible errors and empty
  states MUST distinguish no matches, missing data, unsupported coverage and provider failure.
- **FR-024**: Results MUST be presented as descriptive historical screening evidence, not forecasts,
  personalized advice or trade instructions. Consolidation MUST NOT imply a guaranteed breakout.
  Permitted data/classification display and derived-use rights MUST be verified for the deployment.

### Consolidation / Heartbeat Heuristic

The initial method is a **versioned product heuristic**, not a universal financial definition or
validated prediction. Its defaults are planning assumptions grounded in weak-trend, relative
volatility and volume concepts; record any calibration change explicitly and protect it with
controlled examples before changing screening behavior.

- Use consistently adjusted daily high/low/close and comparable volume for the represented
  sector, industry, or stock. Never transfer an industry's corridor to its member stocks.
- A candidate quiet sideways session requires all three:
  (1) 14-session Wilder ADX below 20, indicating weak trend strength;
  (2) 20-session Bollinger BandWidth at or below its own trailing 252-valid-session median;
  (3) no volume spike under FR-013 for that session.
- Bollinger bands use the 20-close arithmetic mean plus/minus two population standard deviations.
  BandWidth is `100 * (upper band - lower band) / middle band`; a nonpositive middle band is invalid.
  The historical comparison uses only earlier valid observations, excluding the candidate session.
  ADX requires at least 150 prior sessions of warm-up before declaring a qualifying session.
- Intervals are maximal consecutive runs of qualifying completed sessions within the available
  history. Five sessions is the minimum reportable run, not a preset period or maximum duration;
  runs can continue through months or years. Missing required data breaks the interval rather
  than bridging an unobserved span.
- The corridor is the observed minimum adjusted low and maximum adjusted high within the
  detected interval. Report absolute width and `100 * (upper / lower - 1)`; a nonpositive lower
  bound is invalid. No universal percentage-width rejection threshold applies. Also report
  median 14-session ATR over the interval as typical price volatility.
- Consolidation screening matches a qualifying interval ending on the latest completed session
  **or immediately preceding it**. The second case permits a current volume spike after a quiet
  interval; show that the quiet interval ended and do not claim a breakout unless separately
  specified. Older completed intervals remain historical chart context, not current filter matches.
- Results calculated as of any session MUST use only data available by that session. Historical
  intervals may be extended later but earlier detections MUST NOT use future highs/lows or volume.
  Show the available-history start and flag boundary-truncated intervals.
- The fixed indicator estimation windows are not fixed consolidation durations. Comparison to an
  instrument's own BandWidth history adapts the volatility test to that instrument; corridor
  boundaries and duration are outputs. Short historical coverage is explicitly insufficient.

Research basis:
[ChartSchool ADX](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/average-directional-index-adx)
describes ADX below 20 as weak/non-trending and notes smoothing/warm-up limitations.
[ChartSchool Bollinger BandWidth](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth)
explains that narrowness is relative to each instrument's own history, not a universal width.
Neither source establishes the combined rule, median cutoff, quiet-volume requirement, or
five-session reporting minimum as an industry standard or guarantees that a detected run captures
every visually apparent sideways period.

### Fundamental Metric and Score Definitions

- **Quality inputs**: ROE is `100 * trailing-12-month net income / average opening-and-closing
  common equity` with positive opening and closing equity; net margin is
  `100 * trailing-12-month net income / trailing-12-month revenue` with positive revenue.
- **Growth inputs**: Revenue YoY growth and diluted EPS YoY growth are
  `100 * (current trailing-12-month value / prior comparable trailing-12-month value - 1)`.
  The prior value must be positive; use non-overlapping comparable trailing-year periods.
  A negative current value with positive prior value is valid negative growth.
- **Cash Flow inputs**: Free cash flow is trailing-12-month operating cash flow minus capital
  expenditure expressed as a positive cash outflow. FCF yield is `100 * FCF / market cap` at the
  displayed valuation date, in a matching currency and with positive market cap. Operating cash
  flow YoY growth uses the same growth definition and positive prior-period requirement.
- **Percentiles**: Higher is better for each of the six metrics. For a stock with a valid value,
  `score = 100 * (L + 0.5 * (E - 1)) / (N - 1)`, where N is the number of valid industry peers
  including that stock, L counts peers with strictly lower values, and E counts equal values
  including that stock. Require N ≥ 5; all-equal valid values score 50.
- **Blocks**: Each block is the arithmetic mean of its two percentile scores, displayed to one
  decimal place. Calculate from unrounded inputs and round only for presentation. Do not combine
  the three blocks into a new overall grade or use them to change price-performance direction.

### Requirement Acceptance Coverage

| Requirements | Acceptance coverage |
|---|---|
| FR-001–FR-008 | US1 scenarios 1–5; return/direction/ranking and universe edge cases |
| FR-009–FR-013 | US2 scenarios 1–4, 6–7; insufficient history and exact-boundary examples |
| FR-014–FR-016 | US1 scenario 6; US2 scenarios 4–5; heuristic boundary/truncation examples |
| FR-017 | US1 scenario 4; US2 scenario 6; parent/universe changes |
| FR-018–FR-021 | US3 scenarios 1–7; invalid denominators and missing fiscal periods |
| FR-022–FR-024 | US1 scenario 5; US2 scenario 7; US3 scenarios 5–7; freshness/error edge cases |

### Key Entities

- **US Screening Universe**: Included exchanges, cap bands, optional index memberships, effective
  date/source, included instrument identities, total known members and missing coverage.
- **Sector / Industry**: Dated classification identity and parent relationship, member stock
  identities, source and membership coverage.
- **Classification Representation**: Qualified industry ETF or verified largest-member stock,
  composition basis, effective/availability dates and limitations; distinct from member universe.
- **Price / Volume Observation**: Instrument, completed session, adjusted price basis, volume,
  source, observation/availability dates and corporate-action consistency.
- **Screening Criteria**: Enabled technical rules, shared volume parameters, selected period,
  universe constraints, pass/fail/insufficient evidence, and observation cutoff.
- **Consolidation Interval**: Instrument, detection version/cutoff, start/end, duration, corridor
  bounds/width, volatility, volume context, ongoing state and truncated-history indicators.
- **Fundamental Observation**: Stock, metric, value/units, comparable fiscal period, publication
  date, source, valuation date where applicable and sufficiency.
- **Stock Scorecard**: Stock identity, industry peer group, six metric percentiles and raw inputs,
  three block scores, valid peer counts and insufficiency reasons.
- **Session Selection**: Chosen sectors/industry, universe, criteria, stock list and current stage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of first-time test users identify the strongest and weakest eligible
  industry for the selected period within 60 seconds.
- **SC-002**: At least 90% can progress from an industry to its member stocks, combine two technical
  criteria, and inspect a matching stock's three score blocks within three minutes.
- **SC-003**: Controlled cases match 100% of specified returns, direction labels, tie ranks,
  criterion truth states, percentile ties, block values and insufficiency outcomes.
- **SC-004**: Controlled histories covering short, multi-month and multi-year quiet sideways
  runs, sustained trends, volume spikes, missing data and truncation match the versioned detection
  rule; 100% of displayed corridors and durations agree with their labelled source intervals.
- **SC-005**: In a controlled universe of 2,500 stocks with previously loaded data, 95% of
  filter/sort/selection interactions display the updated result within two seconds. Initial remote
  loads show progress and coverage; the measurement does not conceal first-load provider limits.
- **SC-006**: Every available matching member is accessible in the table and scorecards without a
  silent row cap; all known membership gaps and insufficient metrics are disclosed.
- **SC-007**: Identical interactions within the stated freshness window repeat no remote data
  request for unchanged data, and retained-stock peer scores remain unchanged by technical filters.
- **SC-008**: At least 90% of test users correctly identify a chart's consolidation dates/width,
  distinguish insufficient data from a low score, and understand that results are not predictions.

## Assumptions

- This is a specification revision, not an implementation completion claim. Existing architecture,
  weekly contracts, and unfinished tasks need reconciliation under the current constitution.
- Initial coverage is US common stocks. Large cap means at least USD 10 billion; mid cap means
  at least USD 2 billion and below USD 10 billion; small cap means at least USD 300 million and
  below USD 2 billion. Below-USD-300-million and unknown-cap stocks are labelled separately and
  remain visible with no cap-band filter; they are not silently assigned to small cap.
- S&P 500/Russell 2000 are optional dated membership filters, not guaranteed free-provider
  capabilities. The selected source must substantiate them. Comprehensive member enumeration
  is a dependency; search results or an ETF's holdings alone do not prove complete coverage.
- Classification membership is evaluated at the displayed date; proxy identity does not define
  all industry members, and a stock proxy's return is not an equal-weight industry return.
- The prior quiet interval may end immediately before the current signal session, allowing a
  consolidation-plus-spike conjunction. This is a documented default adopted to avoid contradictory
  filters, not a trade signal.
- The proposed adaptive detector can miss or split visually apparent ranges. Its reproducibility,
  limitations and detected metrics are explicit; it does not promise every human-identified range.
- Peer groups contain members of the selected universe in the same industry, including stocks
  failing technical filters, so scores remain comparable when technical criteria change.
- No extra fundamental-threshold filters or overall recommendation grade are implied.
  Raw values remain accessible, including for stocks whose scores are insufficient.
- Price/volume, classification/index membership and fundamentals require an authorized source with
  explicit observation/publication dates and adequate history. Unavailable free-source coverage
  is a visible dependency, not permission to fabricate data or add unapproved providers.
- Saved watchlists, alerts, portfolio tracking, trade execution, forecasts, observed fund flows,
  multi-market comparison and persistent account storage remain outside this MVP. Session stock
  selections do not introduce a saved-watchlist feature.
