# Feature Specification: Market Leadership Screener

**Feature Identifier**: `001-market-leadership-screener`

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "Identify gaining and declining industries and stocks; present market,
sector, industry, and stock data clearly; support filtering; remain adaptable to other assets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find Market Leadership (Priority: P1)

As a self-directed, rules-based investor, I want a weekly view of market regimes and relative
industry leadership so I can quickly identify strong and weak areas for further research.

**Why this priority**: Recognizing leadership and deterioration is the product's primary decision
support value and produces a useful first release by itself.

**Independent Test**: Load a dated dataset containing known market and industry outcomes and verify
that the view shows each market regime, ranks industries, and distinguishes gaining, neutral,
declining, and insufficient-data entries according to the domain rules.

**Acceptance Scenarios**:

1. **Given** complete weekly market and industry data, **When** the user opens the screener,
   **Then** the user sees market regimes and an industry ranking dated to the latest completed week.
2. **Given** industries with known relative-strength values and averages, **When** rankings are
   displayed, **Then** positive values above their averages are gaining, negative values below their
   averages are declining, and all other values are neutral.
3. **Given** an industry with insufficient history, **When** the ranking is displayed, **Then** the
   industry is visibly marked as insufficient data and is not presented as gaining or buy-eligible.
4. **Given** benchmarks above a rising 150-session average, below a falling 150-session average, and
  between those conditions, **When** market regimes are evaluated, **Then** they are respectively
  bullish, bearish, and sideways.
5. **Given** known three-, six-, and twelve-month relative strengths, **When** the composite is
  calculated, **Then** it equals 40%, 30%, and 30% of those components and the rounded-up top 20%
  of entries are marked as the top group.
6. **Given** moving-average slopes at, above, and below the flat-band boundaries, **When** a regime is
  evaluated by ordinary least squares over session indices 0 through 19, **Then** boundary values are
  flat, values above the positive boundary are rising, values below the negative boundary are falling,
  and fewer than 20 values produce an undefined slope.
7. **Given** one company with multiple listed stocks, **When** the hierarchy and stock details are
  displayed, **Then** the company appears once in its classification and each stock retains its own
  symbol, exchange, currency, and market data.
8. **Given** a completed weekly snapshot, **When** the default ranking rows are displayed, **Then**
  every row shows name, rank, status, composite strength, week-over-week composite change, proxy
  type, eligibility state, and as-of date before the user opens any detail view.

---

### User Story 2 - Focus the Market View (Priority: P2)

As an investor reviewing many securities, I want to filter, search, sort, and move through the market
classification hierarchy so I can isolate information relevant to my current research question.

**Why this priority**: Filtering makes a broad market dataset comprehensible without altering the
underlying classification or ranking rules.

**Independent Test**: Apply each supported filter to a mixed dataset and verify that only matching
entries remain, active criteria are visible, and clearing the criteria restores the complete view.

**Acceptance Scenarios**:

1. **Given** entries across multiple markets and classifications, **When** the user selects a market,
   hierarchy level, and leadership status, **Then** only entries matching all selected criteria appear.
2. **Given** an active filtered view, **When** the user searches by name or symbol and changes the sort,
   **Then** the results update without losing the active filters.
3. **Given** one or more active filters, **When** the user clears all filters, **Then** the default
   industry ranking returns and no hidden criteria remain.

---

### User Story 3 - Inspect Leading and Declining Stocks (Priority: P3)

As an investor, I want to inspect stocks in the context of their industry so I can distinguish stock
leadership from broad industry strength and create a focused research list.

**Why this priority**: Industry context prevents isolated stock movement from being mistaken for a
complete entry signal while extending the ranking into actionable research.

**Independent Test**: Open a known industry, inspect its constituent stocks, and verify that stock
relative strength, industry status, eligibility warnings, and data sufficiency are shown separately.

**Acceptance Scenarios**:

1. **Given** a gaining, top-ranked industry with no deterioration flag, **When** the user opens its
   stocks, **Then** stocks with positive three- and six-month strength versus the industry are
   identifiable as research candidates.
2. **Given** a declining industry, **When** a constituent stock is individually strong, **Then** the
   stock remains visible but is marked as blocked from new-buy candidacy by industry status.
3. **Given** a stock with stale required fundamentals or insufficient market history, **When** it is
   inspected, **Then** the missing or stale evidence and resulting eligibility limitation are explicit.
4. **Given** an industry that turns declining, **When** the next weekly review occurs, **Then** new-buy
  candidacy remains blocked and existing holdings receive a review/reduce flag, not an automatic sale.
5. **Given** a stock that passes the strength test but fails its survival check, has extreme volatility,
   represents less than 5% of the proxy and is not a top-10 holding, does not match the represented
   industry, or lacks a written research reason, **When** candidacy is evaluated, **Then** it is not
   presented as a single-stock research candidate.
6. **Given** a stock that passes every strength, survival, freshness, volatility, industry, proxy-weight,
   and written-reason gate, **When** candidacy is evaluated in an eligible industry, **Then** it is
   presented as a single-stock research candidate with each passing gate visible.
7. **Given** an industry outside the top group at one monthly review, **When** it remains outside the
  top group at the next consecutive monthly review, **Then** a deterioration flag blocks new buys and
  raises a review/reduce alert without creating an automatic sell instruction.

---

### User Story 4 - Understand and Trust the Evidence (Priority: P4)

As an investor, I want concise definitions, dates, benchmarks, and source context so I can interpret
the rankings correctly and avoid treating historical evidence as a forecast or trade instruction.

**Why this priority**: Precise provenance and explanations make the screener auditable and reduce
misinterpretation of relative performance.

**Independent Test**: Inspect representative market, industry, and stock entries and verify that each
metric exposes its meaning, comparison basis, as-of date, data sufficiency, and relevant warning.

**Acceptance Scenarios**:

1. **Given** an industry ranking, **When** the user inspects its details, **Then** the three-, six-, and
   twelve-month components, composite, benchmark, proxy type, status, and as-of date are available.
2. **Given** local and global results that disagree, **When** both are shown, **Then** local eligibility
   remains authoritative and the global result appears as contextual warning information.
3. **Given** lagged flow evidence, **When** it is shown, **Then** its event date, availability date,
   age, coverage, and source are visible and it does not change the ranking or eligibility outcome.
4. **Given** multiple funds at or above 60% industry purity, $100 million in assets, and $2 million
  USD-equivalent 20-session average daily traded value, plus stocks at or above the corresponding
  $5 million threshold, **When** a proxy is selected, **Then** the most liquid qualifying fund is
  preferred over an official index and a five-member equal-weight basket, and its proxy type is visible.
5. **Given** any displayed market, classification, company, stock, benchmark, proxy, or evidence item,
  **When** the user inspects its provenance, **Then** the required date, basis, instrument, benchmark,
  source name, and source availability fields are present or explicitly marked unavailable.
6. **Given** a first-time user viewing the scoreboard, **When** the user opens the interpretation help,
  **Then** every term required by FR-021 is defined and the user is told that rankings describe
  historical relative performance and are neither forecasts nor trade instructions.
7. **Given** a fund or stock below any applicable purity, asset, or USD-equivalent 20-session traded-
  value threshold, **When** proxy eligibility is evaluated, **Then** that instrument remains visible
  but is rejected as a buyable proxy or proxy-basket member with the failed threshold identified.
8. **Given** no qualifying industry fund, **When** an official industry index exists, **Then** it is
  selected as a reference-only proxy; otherwise, a qualifying equal-weight basket of at least five
  members is selected, and a node with neither is marked insufficient.

---

### User Story 5 - Preserve Equity Results During Extension (Priority: P5)

As a product owner, I want new asset categories to be introduced without redefining established
equity concepts so users receive consistent historical equity results as the product expands.

**Why this priority**: Extension matters after the equity screener is useful, and explicit compatibility
prevents speculative generalization from weakening the initial domain model.

**Independent Test**: Add an acceptance fixture for one separately specified asset category containing
at least 100 instruments and verify that all baseline equity outputs and controls remain unchanged.

**Acceptance Scenarios**:

1. **Given** a recorded baseline of equity results and filters, **When** a separately specified asset
  category with its own taxonomy and rules is included, **Then** every baseline equity calculation,
  label, historical result, and filter outcome remains identical.
2. **Given** a new asset category without approved ranking semantics, **When** it is introduced,
  **Then** the product does not apply GICS or equity gain/decline rules to it by default.

### Edge Cases

- A value exactly equal to zero or to its comparison average is neutral, not gaining or declining.
- When fewer entries exist than a full ranking percentile, the top group includes the rounded-up 20%.
- A classification node with no qualifying fund, official index, or five-member basket is marked
  insufficient and cannot make its companies eligible through that node.
- Missing twelve-month history or comparison-average history prevents a leadership status.
- A market holiday or incomplete current week leaves the latest completed weekly snapshot in place.
- A missing same-date currency conversion prevents a global comparison but preserves a valid local
  result with an explicit global-data warning.
- A valid filter combination with no matches shows an empty result explanation and a clear reset path.
- A delisted, renamed, or reclassified company retains dated historical context and uses its current
  classification only for current rankings.
- Tied composite values are ordered by six-month strength, then three-month strength, then
  twelve-month strength, then name, without changing the tied composite values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST organize equity information as Market, GICS Sector, Industry Group,
  Industry, Sub-industry, Company, and Stock, preserving the distinction between companies and their
  traded instruments.
- **FR-002**: The default view MUST show a weekly GICS Industry scoreboard and the as-of date of the
  latest completed market week.
- **FR-003**: The product MUST classify a market as bullish when its benchmark is above a rising
  150-session average, bearish when it is below a falling 150-session average, and sideways otherwise.
  The trend MUST use ordinary least squares to fit the latest 20 average values against session indices
  0 through 19, divide the fitted per-session slope by the latest average, and express the result as a
  percentage. Greater than +0.025% is rising, less than -0.025% is falling, and both boundary values and
  the range between them are flat. With fewer than 20 values the trend is undefined and not rising.
  Market regime MUST remain separate from industry status.
- **FR-004**: For every eligible classification entry, the product MUST calculate relative performance
  against the selected benchmark over three, six, and twelve calendar months using matching return
  bases.
- **FR-005**: The product MUST calculate the composite relative-strength score using weights of 40%
  for three months, 30% for six months, and 30% for twelve months.
- **FR-006**: The product MUST classify an entry as gaining only when its composite is greater than
  zero and greater than its 50-session composite average, declining only when its composite is less
  than zero and less than that average, and neutral in all other cases, including equality.
- **FR-007**: The product MUST identify the top 20% of ranked entries at the selected hierarchy level,
  rounded up to the next whole entry.
- **FR-008**: The product MUST provide local-currency benchmark and global benchmark views side by
  side and MUST label the benchmark, currency basis, and return basis for each.
- **FR-009**: The product MUST allow movement from sector through sub-industry and into constituent
  companies and stocks while retaining the user's market and benchmark context.
- **FR-010**: Users MUST be able to filter results by market, hierarchy level, leadership status,
  top-group membership, research eligibility, and proxy type.
- **FR-011**: Users MUST be able to search by classification name, company name, or stock symbol and
  sort visible results by name, rank, composite strength, status, or week-over-week composite change.
- **FR-012**: The product MUST display active filters, provide a single action to clear them, and show
  an explanatory empty state when no entry matches.
- **FR-013**: Each ranking row MUST present name, rank, status, composite strength, week-over-week
  composite change, proxy type, eligibility state, and as-of date without requiring the detail view.
- **FR-014**: A classification proxy MUST use the most liquid qualifying industry fund, otherwise an
  official index, otherwise an equal-weight basket of at least five eligible members; its type MUST
  be visible and filterable. A fund MUST have at least 60% industry purity, $100 million in assets,
  and $2 million USD-equivalent 20-session average daily traded value; a stock used in screening or
  a basket MUST have at least $5 million on the same USD-equivalent 20-session basis.
- **FR-015**: The product MUST mark an industry as research-eligible only when it is locally gaining,
  is in the top group, and has no active deterioration flag; a locally declining status MUST block
  new-buy candidacy immediately.
- **FR-016**: The product MUST flag deterioration when an industry remains outside the top group for
  two consecutive monthly reviews. An industry that turns declining MUST also raise a review/reduce
  flag for existing holdings at the next weekly review. Neither flag is an automatic sell instruction.
- **FR-017**: A single-stock research candidate MUST have positive relative strength versus its
  industry over both three and six months, a passing survival check with fundamentals no older than
  two quarters, non-extreme volatility, a primary classification matching the represented industry,
  at least 5% weight in the industry proxy or a place among its top 10 holdings, and a written research
  reason. Industry eligibility MUST remain separate from stock-level evidence.
- **FR-018**: The product MUST show insufficient, stale, or unavailable data explicitly and MUST NOT
  assign a status or eligibility outcome that depends on missing evidence.
- **FR-019**: Every displayed result MUST expose its as-of date, comparison period, return basis,
  currency basis, proxy or instrument, benchmark, source name, and source availability date.
- **FR-020**: Lagged money-flow evidence MUST show event date, availability date, age, coverage, and
  source, and MUST NOT independently alter scoreboard rank, status, top-group membership, eligibility,
  or trigger a trade instruction. It MAY raise separate watchlist priority or a review flag.
- **FR-021**: The product MUST provide plain-language definitions for market regime, relative strength,
  gaining, declining, neutral, top group, proxy, deterioration, and insufficient data.
- **FR-022**: The product MUST state that rankings describe historical relative performance and are
  neither forecasts nor trade instructions.
- **FR-023**: When a separately specified asset category is added, the product MUST preserve all
  established equity calculations, labels, historical results, and filter outcomes and MUST NOT apply
  GICS or equity ranking semantics to the new category unless its specification explicitly adopts them.

### Requirement Acceptance Coverage

| Requirements | Acceptance Evidence |
|--------------|---------------------|
| FR-001–FR-002 | User Story 1, scenarios 1 and 7; hierarchy and weekly snapshot fixtures |
| FR-003 | User Story 1, scenarios 4 and 6; regime and slope-boundary fixtures |
| FR-004–FR-007 | User Story 1, scenarios 2 and 5; controlled calculation dataset |
| FR-008 | User Story 4, scenario 2; disagreeing local and global results |
| FR-009–FR-012 | User Story 2, scenarios 1–3; navigation and filter acceptance dataset |
| FR-013 | User Story 1, scenario 8; field-by-field default-row inspection |
| FR-014 | User Story 4, scenarios 4, 7, and 8; threshold, rejection, and fallback fixtures |
| FR-015–FR-016 | User Story 3, scenarios 1, 2, 4, and 7; status and review-transition fixtures |
| FR-017–FR-018 | User Story 3, scenarios 1, 3, 5, and 6; pass/fail gate and stale-data fixtures |
| FR-019–FR-022 | User Story 4, scenarios 1–3, 5, and 6; provenance and interpretation review |
| FR-023 | User Story 5, scenarios 1–2; cross-category compatibility fixture |

### Domain Terms

- **GICS**: The shared equity classification that organizes companies into sectors, industry groups,
  industries, and sub-industries.
- **Market regime**: A market benchmark's broad state: bullish, bearish, or sideways.
- **Relative strength**: The percentage-point difference between a proxy's return and its benchmark's
  return over the same period and on the same return basis.
- **Composite strength**: The weighted combination of three-, six-, and twelve-month relative strength.
- **Moving average**: The average of the latest fixed number of daily values; the screener uses it to
  compare current strength with recent history and to describe benchmark direction.
- **Gaining / declining / neutral**: Labels for relative leadership status, not absolute price gains,
  losses, forecasts, or trade instructions.
- **Top group**: The rounded-up highest 20% of ranked entries at the selected classification level.
- **Proxy**: A qualifying fund, official index, or member basket representing a classification node.
- **Deterioration**: A review state caused by immediate declining status or two consecutive monthly
  reviews outside the top group; it is not an automatic sell instruction.
- **Insufficient data**: Required history or evidence is missing, so the affected result receives no
  status or eligibility outcome.

### Scope Boundaries

**In scope**:

- Weekly market regimes and relative leadership across the equity classification hierarchy.
- Local and global benchmark comparison, filtering, drill-down, and stock research candidates.
- Data quality, freshness, provenance, and interpretation warnings needed to understand results.

**Out of scope**:

- Trade execution, order routing, automated buy or sell decisions, and portfolio management.
- Price prediction, return forecasts, personalized financial advice, and automatic sell signals.
- A universal ranking taxonomy for non-equity assets; this release preserves a path for later work.
- Saved screens, alerts, user accounts, and collaborative sharing.

### Key Entities *(include if feature involves data)*

- **Market**: A primary listing venue and its local benchmark, currency, regime, and trading calendar.
- **Classification Node**: A dated GICS sector, industry group, industry, or sub-industry with parent
  and child relationships.
- **Company**: A business assigned to one primary classification path and primary listing market.
- **Instrument**: A tradable representation such as a stock or fund, with symbol, currency, market,
  liquidity, availability, and data coverage.
- **Industry Proxy**: The selected fund, index, or member basket used to represent a classification
  node, including type, composition, qualification, and effective dates.
- **Benchmark**: The local or global comparison series, including currency and return basis.
- **Scoreboard Snapshot**: A dated weekly set of component strengths, composite score, rank, status,
  top-group membership, breadth context, and eligibility state.
- **Deterioration Flag**: A dated review state raised after two consecutive monthly reviews outside
  the top group.
- **Flow Evidence**: Dated contextual evidence with event date, availability date, source, coverage,
  age, and interpretation limits.
- **Filter State**: The user's active market, hierarchy, status, eligibility, proxy, search, and sort
  selections for the current view.

### Dependencies

- Dated daily price and total-return series for stocks, proxies, local benchmarks, and the global
  benchmark, with enough history for twelve-month strength and its 50-session average.
- Same-close currency conversion for global comparisons; when absent, local results remain available
  and the global comparison is marked insufficient.
- Current and historical GICS assignments, company primary listings, proxy holdings, fund purity,
  fund assets, and traded-value measures.
- Dated company fundamentals sufficient for the survival check and stale-data rule.
- Dated money-flow and regulatory evidence with event date, availability date, coverage, and source.
- Rights to calculate and display all required classifications, benchmarks, prices, and evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of representative target users can identify the three strongest and three
  weakest eligible industries in a selected market within 60 seconds on their first attempt.
- **SC-002**: For a controlled acceptance dataset, 100% of market regimes, component values, composite
  values, statuses, ranks, top-group memberships, and eligibility states match the documented rules.
- **SC-003**: At least 95% of filter, search, sort, and hierarchy-navigation actions display updated
  results within two seconds for a dataset covering 20 markets and 10,000 stocks.
- **SC-004**: In usability testing, at least 90% of participants correctly distinguish market regime
  from industry status and relative gains from absolute price gains after using the product.
- **SC-005**: Every displayed ranking and evidence item exposes an as-of date and data sufficiency
  state; 100% of stale, missing, or lagged test records produce the required warning.
- **SC-006**: At least 90% of participants can apply a multi-criterion filter, inspect one matching
  stock in industry context, and restore the default view without assistance.
- **SC-007**: When a separately specified asset category containing at least 100 instruments is added
  to an acceptance dataset, 100% of existing equity calculations, historical results, labels, and
  filter outcomes remain unchanged.

## Assumptions

- The primary user is a self-directed investor who follows a repeatable weekly review process.
- Official regular-session closes are available for prices, benchmarks, proxies, and currency
  conversion; the latest completed week is the default evaluation point.
- GICS is the authoritative equity classification, and each company has one primary current path.
- Total-return comparisons are preferred; price-return data may be used only when both proxy and
  benchmark use the same basis and the basis is labeled.
- The local market view determines research eligibility; global comparison is contextual.
- Industry funds qualify at 60% minimum industry purity, and proxy liquidity rules defined in the
  domain decisions remain authoritative.
- The rounded-up top-group rule, five-member fallback basket, and three-/six-month stock-strength
  condition are accepted practitioner defaults pending later review.
- Data licensing, benchmark access, classification access, and currency conversion are available to
  the product under terms that permit display to the intended users.