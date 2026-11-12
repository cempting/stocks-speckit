# Feature Specification: Stock Detail Analysis

**Feature Branch**: `main` (spec key `017-stock-detail-analysis`; no branch hook registered)

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "The stock detail view shall display the stock chart, the 50 MA and the 150 MA. The volume shall be displayed in the same chart as well. Research whether consolidation phases may be detected and highlighted in the chart. The time period of the chart shall be adjustable: 1m, 3m, 6m, 12m, 18m, 24m. The stock detail shall also provide company information (size) and historical data, preferably quarterly (earnings, revenue, cash flow, and further measurable metrics). Research which other metrics are important fundamentals."

## Scope and Existing Feature Ownership

This feature enriches the existing stock detail with a time-adjustable price/volume chart,
consolidation context, company profile, and quarterly financial history. It does not change stock
identity, listing verification, lookup navigation, industry membership, existing score formulas,
or the financial-risk assessment. [015](../015-dedicated-stock-lookup/spec.md) owns lookup and
listing selection; [001](../001-market-leadership-screener/spec.md) owns the existing technical
screening and consolidation heuristic; [002](../002-fundamental-grading-layout/spec.md) owns its
eight-metric scorecard; [011](../011-company-risk-evidence/spec.md) owns cash-flow risk warnings
and company enrichment; and [014](../014-fundamental-score-evaluation/spec.md) owns score
interpretation. This feature presents compatible context in stock detail without duplicating or
redefining those contracts.

### Research Findings

- **Consolidation is detectable as historical evidence, not as a universal fact or forecast.**
  Feature 001 already defines a versioned, instrument-specific heuristic and its chart treatment:
  a subtle shaded interval with horizontal observed price boundaries, interval context, and no
  implied breakout prediction. Reuse that contract for the selected stock rather than introducing
  a second definition. Its research basis and limitations are documented in
  [feature 001](../001-market-leadership-screener/spec.md) and its
  [consolidation contract](../001-market-leadership-screener/contracts/consolidation.md).
- **A balanced fundamental view needs earnings, cash generation, and balance-sheet context.**
  In addition to revenue, net income, and diluted EPS, the proposed quarterly core includes
  operating cash flow, capital expenditures, free cash flow, cash, debt, equity, and shares
  outstanding. Useful derived context includes revenue/EPS growth, gross/operating/net margins,
  FCF margin, current ratio, debt-to-equity, and return on equity or invested capital when the
  underlying facts support comparable calculations. Market capitalization is the primary company
  size measure. Valuation multiples (P/E, P/S, EV/EBITDA, and FCF yield) are useful as dated
  snapshot context, but are not substitutes for quarterly operating history.
- These are evidence for comparison, not stand-alone investment recommendations. The existing
  [fundamental matrix](../002-fundamental-grading-layout/spec.md),
  [company evidence contract](../011-company-risk-evidence/spec.md), and
  [score research](../014-fundamental-score-evaluation/research.md) require metric periods,
  units, provenance, explicit gaps, and separation of peer-relative scores from absolute
  financial condition. Those safeguards also apply here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Price, Trend, and Volume Together (Priority: P1)

As an investor reviewing a selected stock, I want one chart to show its price history, 50- and
150-session moving averages, and corresponding volume, so I can assess recent price and trading
activity in context.

**Why this priority**: The chart is the primary requested stock-detail capability and should work
independently of optional consolidation and financial-history evidence.

**Independent Test**: Open a verified stock detail with controlled daily observations, select each
supported period, and verify the displayed price dates, both moving averages, and aligned volume.

**Acceptance Scenarios**:

1. **Given** a stock with sufficient daily price and volume history, **When** its detail opens,
   **Then** a single chart view shows the price series, a 50-session moving average, a
   150-session moving average, and volume aligned to the same dates.
2. **Given** the stock chart is displayed, **When** the user selects 1m, 3m, 6m, 12m, 18m, or
   24m, **Then** the visible date range changes to that period and the selected period is apparent.
3. **Given** an average has enough preceding data to calculate but its warm-up begins before the
   visible range, **When** the chart opens, **Then** the average is available from the start of
   the visible range without extending the displayed date range.
4. **Given** insufficient history for one or both averages, **When** the chart opens, **Then**
   the unavailable average is identified as insufficient and is not drawn as zero or guessed data.
5. **Given** price or volume history is missing or a request fails, **When** detail is displayed,
   **Then** the gap or failure is explicit and is not presented as complete data.

### User Story 2 - Identify a Consolidation Interval (Priority: P2)

As an investor examining a stock chart, I want eligible consolidation intervals highlighted with
their price corridor, so I can recognize historical sideways periods without mistaking them for
predictions.

**Why this priority**: The interval annotation adds useful technical context but is secondary to
the basic price, moving-average, and volume chart.

**Independent Test**: Use controlled stock history with a known qualifying interval and verify the
annotation and its dates, bounds, duration, and evidence status against the established detector
contract.

**Acceptance Scenarios**:

1. **Given** sufficient stock history contains a qualifying consolidation interval, **When** its
   detail chart opens, **Then** the latest interval is subtly highlighted with its own observed
   price boundaries and its dates and duration are available beside or below the chart.
2. **Given** there are several detected intervals, **When** the chart opens, **Then** only the
   latest interval is highlighted by default and the user can inspect older intervals.
3. **Given** no interval qualifies or history is insufficient, **When** consolidation context is
   shown, **Then** "none detected" and "insufficient evidence" are distinguishable.
4. **Given** an interval is highlighted, **When** the user interprets it, **Then** its presentation
   identifies it as historical price/volume evidence and does not imply a breakout or future return.

### User Story 3 - Understand Company Size and Financial History (Priority: P1)

As an investor assessing a stock's business and financial condition, I want its size and recent
quarterly financial evidence in the stock detail, so I can compare operating results, cash
generation, and balance-sheet position over time.

**Why this priority**: Financial history and company size are explicit parts of the requested
detail view and provide value independently of the technical chart.

**Independent Test**: Open controlled company data containing multiple quarters, missing values,
and reported versus derived metrics; verify company identity, size, quarter ordering, values,
periods, units, and explicit data limitations.

**Acceptance Scenarios**:

1. **Given** a verified stock has company profile data, **When** its detail is displayed, **Then**
   the company name, selected listing symbol, verified sector/industry when available, and market
   capitalization with its currency and observation date are visible.
2. **Given** quarterly financial history is available, **When** the user views fundamentals,
   **Then** the latest eight quarters are shown when available, including revenue, net income,
   diluted EPS, operating cash flow, capital expenditures, and free cash flow.
3. **Given** balance-sheet history is available, **When** the user views fundamentals, **Then**
   cash and equivalents, total debt, shareholders' equity, and shares outstanding are shown for
   their reported quarter-end periods when available.
4. **Given** compatible underlying facts exist, **When** derived context is displayed, **Then**
   supported revenue and EPS growth, gross/operating/net margins, FCF margin, current ratio,
   debt-to-equity, and return-on-equity or invested-capital measures are labeled and traceable to
   their period and inputs.
5. **Given** reliable market and financial inputs exist, **When** valuation context is displayed,
   **Then** supported P/E, P/S, EV/EBITDA, or FCF-yield values are marked as dated snapshots and
   are not represented as quarterly operating metrics.
6. **Given** a financial value is missing, reported as zero, negative, or derived, **When** it is
   displayed, **Then** those states remain distinguishable and the value is not imputed or
   described as missing solely because it is non-positive.

## Edge Cases

- A stock has fewer than 150 prior completed trading sessions, a recent listing, or a gap in
  history; the chart still shows available prices and volume while identifying unavailable
  averages or consolidation evidence.
- The selected period begins before the stock's first available observation; the actual coverage
  start is disclosed rather than filled with invented history.
- Price history is available but volume is missing or incomparable; the chart identifies the
  volume gap without suppressing valid price data.
- The stock has no verified sector/industry, company profile, or market capitalization; available
  stock identity remains visible and missing profile values are explicit.
- Quarterly sources provide year-to-date cash-flow figures, restatements, inconsistent currencies,
  or non-calendar fiscal quarters; values retain the reported basis or are marked unavailable
  rather than mislabeled as comparable standalone quarters.
- A ratio's denominator is zero, negative, missing, or not comparable; that ratio is unavailable
  with a reason while its valid underlying reported metrics remain visible.
- A data source fails, returns partial history, or provides stale evidence; the user sees the
  affected data status and an actionable limitation, not a success-shaped empty value.
- On a narrow viewport, chart controls and company/financial evidence remain usable without
  page-wide horizontal scrolling; charts may resize and financial tables may scroll within their
  own clearly discoverable container.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The existing stock detail MUST show one price chart with price history, daily volume
  aligned to the same dates, a 50-session simple moving average, and a 150-session simple moving
  average when the required observations are available.
- **FR-002**: The chart MUST offer exactly these visible date-range choices: 1m, 3m, 6m, 12m, 18m,
  and 24m. The initial selection MUST be 6m.
- **FR-003**: The averages MUST use completed daily observations and the same adjusted-price basis
  as the displayed stock-price history. Sufficient pre-range observations MUST be used for
  average warm-up without expanding the selected visible range.
- **FR-004**: The chart MUST distinguish unavailable or insufficient price, moving-average, and
  volume data from a valid zero value, a period with no observations, and a failed request.
- **FR-005**: The stock detail MUST use the existing versioned consolidation detector and chart
  conventions defined by feature 001. It MUST evaluate only the selected stock's own history,
  show at most the latest interval by default, permit inspection of older intervals, and distinguish
  no qualifying interval from insufficient evidence.
- **FR-006**: An interval annotation MUST present its observed time span and price corridor, with
  duration and detection limitations available beside or below the chart. It MUST NOT be presented
  as a forecast, guaranteed breakout, or investment instruction.
- **FR-007**: The chart MUST identify the stock, selected date range, observation dates, and
  available-data coverage. Changing the selected stock MUST NOT leave another stock's chart or
  interval annotation visible.
- **FR-008**: The company profile MUST show the verified company name and selected listing identity,
  verified sector/industry where available, and market capitalization with currency and observation
  date. Unsupported profile data MUST remain explicitly unavailable.
- **FR-009**: The financial-history view MUST show the latest eight quarters when available and
  include reported revenue, net income, diluted EPS, operating cash flow, capital expenditures,
  free cash flow, cash and equivalents, total debt, shareholders' equity, and shares outstanding
  when the selected source provides comparable observations.
- **FR-010**: Derived fundamental context MUST include supported revenue and diluted-EPS growth,
  gross/operating/net margins, FCF margin, current ratio, debt-to-equity, and return on equity or
  invested capital. A derived metric MUST identify its applicable period and MUST remain
  unavailable when its inputs or calculation basis are insufficient.
- **FR-011**: Supported P/E, P/S, EV/EBITDA, and FCF-yield values MAY be displayed as latest
  valuation context only when inputs are date- and currency-compatible; they MUST be distinguished
  from quarterly reported facts.
- **FR-012**: Each reported or derived financial observation MUST identify its fiscal period,
  currency or unit, reported/derived status, and source/date context when known. Cumulative,
  restated, incompatible, or incomplete observations MUST NOT be silently labeled as comparable
  standalone quarters.
- **FR-013**: Missing, zero, negative, stale, partial, and failed financial evidence MUST remain
  distinguishable. Missing values MUST NOT be zero-filled, and a failed request MUST NOT be
  presented as successful retrieval.
- **FR-014**: This feature MUST preserve the existing scorecard, peer-score formulas, cash-flow
  warning semantics, verified identity rules, and stock-detail navigation owned by features 001,
  002, 011, 014, and 015.
- **FR-015**: The stock detail MUST remain usable at desktop and phone widths. Essential chart
  controls and financial context MUST be accessible without hover; any horizontally scrollable
  data table MUST scroll within its own discoverable region.
- **FR-016**: Market and financial observations MUST come from the application's currently selected
  permitted data source. The feature MUST disclose unavailable coverage or source limitations and
  MUST NOT silently substitute another provider.

### Key Entities

- **Stock Detail Context**: The verified selected company/listing and the date range currently
  under review.
- **Daily Market Observation**: A dated adjusted price and comparable volume observation used by
  the chart and its overlays.
- **Moving Average**: A 50- or 150-session simple average tied to the selected stock's daily
  observations and visible chart range.
- **Consolidation Interval**: A historically detected interval, observed price corridor, duration,
  cutoff, and evidence sufficiency for the selected stock.
- **Company Profile**: The verified company identity and dated size and classification facts.
- **Quarterly Financial Observation**: A reported or derived company fact with fiscal period,
  value, unit/currency, source, and availability status.
- **Fundamental Metric**: A comparable raw or derived measure whose formula inputs, period, and
  evidence status are identifiable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all supported-history test cases, users can select each of the six specified
  periods and see the requested range reflected in the chart without changing the selected stock.
- **SC-002**: In all chart test cases with sufficient data, price, both moving averages, and
  volume use the same selected stock and date context; insufficient series are explicitly
  identified rather than fabricated.
- **SC-003**: In all financial-history test cases, every displayed quarterly observation has an
  identifiable period and unit/currency, and 100% of missing, zero, negative, and failed states
  are represented distinctly.
- **SC-004**: At least 90% of representative users can locate a company's market capitalization,
  a requested quarterly revenue/cash-flow value, and the displayed consolidation status within
  one minute without mistaking missing data for zero or a consolidation annotation for a forecast.
- **SC-005**: Users can complete the chart and financial-history review at both 1440px and 390px
  viewport widths without clipped essential controls, overlapping content, or page-wide
  horizontal scrolling.

## Assumptions

- The initial supported stock universe and listing verification are the same as the existing
  application; this feature does not add markets or unverified listings.
- Six months is the default chart range. Each month-based range represents the available trading
  observations ending at the latest completed session, not a fixed number of trading days.
- The chart uses daily completed price and volume observations. Moving averages use the established
  50- and 150-session simple-average definitions, with earlier observations fetched as needed for
  warm-up.
- Quarterly fundamentals default to the latest eight comparable fiscal quarters; shorter coverage
  remains useful when shown with explicit dates and limitations.
- Market capitalization is the primary company-size measure. Valuation multiples are supplemental
  snapshots and are shown only when their inputs and dates are sufficiently comparable.
- Existing feature contracts and the single selected financial-data source govern calculations,
  availability, freshness, caching, permissions, and source failures.
- The view provides historical research evidence, not personalized investment advice or a
  prediction of future performance.
