# Feature Specification: Market Screening

**Feature Identifier**: `001-market-leadership-screener`

**Created**: 2026-10-26

**Updated**: 2026-10-27

**Status**: Draft

**Input**: User description: "Focus the MVP on discovery. Let users select one or several equity
markets, identify gaining and declining sectors and industries, drill into the sources of leadership,
and assess money-flow momentum using clearly distinguished price, participation, trading-activity,
and observed fund-flow evidence. Postpone watchlists and portfolio tracking."

## Clarifications

### Session 2026-10-27

- Q: For Phase 2, should non-price data such as classifications, holdings, fundamentals, and fund flows need live provider support, or is a canonical fixture/snapshot contract enough until those sources are available? → A: Narrow Phase 2 to price/volume only; defer other contracts.
- Q: What must the Phase 2 snapshot and Streamlit checkpoint actually display: only verified daily price/volume inputs, or a calculated weekly sector-and-industry scoreboard? → A: Canonical daily input snapshots and basic loading; weekly scoreboard later.
- Q: During Phase 2, should the discovery page read published input snapshots by default, or keep requesting live data on page visits? → A: Keep live-data discovery as the default, with an optional snapshot mode.
- Q: How many equity markets must have working live daily-history ingestion at the Phase 2 checkpoint? → A: US only; additional markets later.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select and Compare Markets (Priority: P1)

As a self-directed investor, I want to select one or several equity markets so I can see where
leadership and weakness are developing without losing each market's local context.

**Why this priority**: Market selection is the entry point to discovery and prevents a fixed US-only
view from being mistaken for a global market view.

**Independent Test**: Load a dated dataset containing at least three markets with different regimes
and sector outcomes, select one market and then several markets, and verify that the displayed
benchmarks, regimes, dates, currency bases, and sector results correspond to the active selection.

**Acceptance Scenarios**:

1. **Given** multiple supported markets, **When** the user opens discovery, **Then** the user can
   select one or several markets before reviewing sector or industry results.
2. **Given** one selected market, **When** its overview is displayed, **Then** the user sees its
   local benchmark, regime, observation date, currency basis, return basis, and data coverage.
3. **Given** several selected markets, **When** the comparison is displayed, **Then** each market
   retains its own benchmark, regime, currency, dates, and sector results rather than being silently
   pooled into one global ranking.
4. **Given** local and global benchmark results that disagree, **When** both are available, **Then**
   they are shown separately and the local-market result remains the primary discovery context.
5. **Given** a market with stale or incomplete required data, **When** it is selected, **Then** its
   affected results are marked stale or insufficient and are not represented as current.

---

### User Story 2 - Find Sector and Industry Leadership (Priority: P1)

As an investor, I want to rank gaining and declining sectors and drill into their industries so I can
identify which areas are driving market leadership or deterioration.

**Why this priority**: Sector-to-industry discovery is the MVP's primary decision-support value.

**Independent Test**: Load known market, sector, and industry histories and verify the calculated
relative-strength components, composite scores, statuses, rankings, changes, and hierarchy.

**Acceptance Scenarios**:

1. **Given** a completed weekly snapshot, **When** the sector scoreboard is displayed, **Then** each
   sector shows rank, status, composite strength, week-over-week composite change, rank change,
   proxy type, as-of date, and data sufficiency.
2. **Given** known three-, six-, and twelve-month relative strengths, **When** the composite is
   calculated, **Then** it equals 40%, 30%, and 30% of those components respectively.
3. **Given** entries with known composite values and 50-session composite averages, **When** status
   is assigned, **Then** positive values above their averages are gaining, negative values below
   their averages are declining, and all other values are neutral.
4. **Given** a selected sector, **When** the user drills into it, **Then** its industries are ranked
   and the active market, local benchmark, sector, dates, and return basis remain visible.
5. **Given** an industry detail view, **When** its evidence is displayed, **Then** the industry is
   compared with both its parent sector and its local market benchmark.
6. **Given** current and prior weekly snapshots, **When** a scoreboard is displayed, **Then** the user
   can distinguish established leaders, strengthening entries, weakening entries, and persistent
   laggards from score and rank changes without those descriptions becoming forecasts.
7. **Given** an entry with insufficient required history, **When** the scoreboard is displayed,
   **Then** it has no leadership status or rank and shows the missing evidence.

---

### User Story 3 - Assess Participation and Momentum Quality (Priority: P2)

As an investor, I want evidence about participation, concentration, and trading activity so I can
judge whether apparent sector or industry momentum is broad, narrow, strengthening, or weakening.

**Why this priority**: Price leadership alone can hide narrow moves driven by a few large companies.
Confirming evidence makes discovery more useful without claiming to measure investor fund flows.

**Independent Test**: Load classifications with known constituent price histories, weights, and
volume outcomes and verify breadth, concentration, coverage, and divergence labels.

**Acceptance Scenarios**:

1. **Given** sufficient constituent histories, **When** a sector or industry is inspected, **Then**
   the percentage of eligible members above their 50-session and 200-session averages is shown with
   the included-member count, eligible-member count, and observation date.
2. **Given** a rising proxy with weakening breadth, **When** its momentum evidence is displayed,
   **Then** the price/breadth divergence is visible and the entry is not described as broadly
   participated.
3. **Given** cap-weighted and equal-weight evidence for the same classification, **When** their
   outcomes differ materially, **Then** the view identifies possible concentration rather than
   treating the cap-weighted move as broad participation.
4. **Given** sufficient close and volume history, **When** volume pressure or relative-volume
   confirmation is shown, **Then** it is labelled as inferred trading-activity evidence rather than
   actual investor inflow or outflow.
5. **Given** insufficient constituent, weight, or volume coverage, **When** confirmation evidence
   cannot be calculated reliably, **Then** the affected indicator is marked insufficient without
   changing the price-leadership result.

---

### User Story 4 - Inspect Observed Fund-Flow Evidence (Priority: P3)

As an investor, I want observed fund-flow evidence, when available, kept separate from price and
volume indicators so I can use it as supporting context without confusing estimates with measured
fund creations or redemptions.

**Why this priority**: Fund flows can strengthen the interpretation of rotation, but their coverage is
partial and they must not redefine the core leadership ranking.

**Independent Test**: Load dated fund-flow evidence with positive, negative, stale, partial, and
unavailable cases and verify its values, normalization, provenance, coverage, and separation from
leadership calculations.

**Acceptance Scenarios**:

1. **Given** observed net flow and asset data for a qualifying fund, **When** flow evidence is shown,
   **Then** both the monetary flow and flow relative to assets are displayed.
2. **Given** observed flow evidence, **When** the user inspects it, **Then** its event period,
   availability date, age, source, represented classification, and coverage are visible.
3. **Given** a price increase without positive observed flows, **When** both are displayed, **Then**
   the product does not label the asset-value increase or trading volume as a fund inflow.
4. **Given** stale, partial, or unavailable flow evidence, **When** discovery results are displayed,
   **Then** the limitation is explicit and the leadership rank, status, and momentum evidence remain
   independently available.
5. **Given** flow evidence that conflicts with price leadership, **When** the classification is
   inspected, **Then** both outcomes remain visible as a divergence and neither is silently discarded.

---

### User Story 5 - Filter and Trust Discovery Results (Priority: P2)

As an investor, I want to filter, sort, and understand discovery results so I can answer a focused
research question and verify the evidence behind every result.

**Why this priority**: Multi-market discovery is only useful when the result set remains navigable,
auditable, and resistant to misinterpretation.

**Independent Test**: Apply each supported filter to a mixed dataset, inspect representative results,
and verify filtering, reset behavior, definitions, provenance, dates, and interpretation warnings.

**Acceptance Scenarios**:

1. **Given** entries across several markets and classifications, **When** the user applies market,
   hierarchy, leadership-status, momentum-state, and data-sufficiency filters, **Then** only entries
   matching all active criteria remain.
2. **Given** active filters, **When** the user changes sorting, **Then** the filter context remains and
   the results can be sorted by name, rank, composite strength, score change, or rank change.
3. **Given** one or more active filters, **When** the user clears them, **Then** the selected markets'
   default sector comparison returns and no hidden criteria remain.
4. **Given** a valid filter combination with no matches, **When** results are evaluated, **Then** an
   explanatory empty state and a clear reset action are shown.
5. **Given** any displayed metric, **When** the user inspects its definition and provenance, **Then**
   the comparison basis, observation date, source availability date, coverage, and interpretation
   limits are available or explicitly marked unavailable.
6. **Given** a first-time user, **When** interpretation help is opened, **Then** the user is told that
   discovery describes historical relative performance and supporting evidence, not forecasts,
   personalized advice, or trade instructions.

### Edge Cases

- A value exactly equal to zero or to its comparison average is neutral, not gaining or declining.
- A market holiday or incomplete current week leaves the latest completed weekly snapshot in place.
- Markets with different holidays or latest observations show their own dates; no common date is
  implied unless all compared observations actually share it.
- If a proxy and its benchmark do not share an eligible ending observation, the comparison uses the
  latest shared observation and exposes that date, or is marked insufficient.
- A missing same-date currency conversion prevents a global comparison but preserves a valid local
  result with an explicit global-data warning.
- Missing twelve-month history or 50-session composite history prevents leadership status and rank.
- Breadth excludes constituents without sufficient history but reports both included and eligible
  counts; no breadth value is shown with fewer than five eligible constituents or below 80% coverage.
- A classification represented by overlapping funds does not sum those funds' flows as if they were
  independent without an explicit overlap and coverage treatment.
- Reclassified constituents retain dated historical membership so current classifications are not
  applied retrospectively.
- Tied composite values are ordered by six-month strength, then three-month strength, then
  twelve-month strength, then name, without changing the tied values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST organize discovery as Market, Sector, and Industry, preserving dated
  parent-child relationships and the distinction between a classification and the instrument or
  basket used to represent it.
- **FR-002**: Users MUST be able to select one or several supported equity markets at the start of
  discovery and change the selection without losing valid shared filters.
- **FR-003**: Each market MUST identify its local benchmark, currency, trading calendar, observation
  date, return basis, data freshness, and market regime.
- **FR-004**: The product MUST classify a market as bullish when its benchmark is above a rising
  150-session average, bearish when it is below a falling 150-session average, and sideways otherwise.
  The trend MUST use ordinary least squares over the latest 20 average values, normalize the fitted
  per-session slope by the latest average, and express it as a percentage. Greater than +0.025% is
  rising, less than -0.025% is falling, and the boundaries and values between them are flat. Fewer
  than 20 average values produce an undefined trend.
- **FR-005**: The default discovery result MUST show a sector scoreboard for the selected markets
  using the latest completed weekly snapshot available for each market.
- **FR-006**: Multi-market discovery MUST preserve each market's local benchmark, currency, calendar,
  dates, regime, and rankings and MUST NOT silently pool entries into a cross-market ranking.
- **FR-007**: For every eligible sector and industry, the product MUST calculate absolute performance
  and local-benchmark-relative performance over one week, one month, three months, six months, and
  twelve months using matching return bases and shared ending observations.
- **FR-008**: The product MUST calculate composite relative strength using 40% of three-month, 30% of
  six-month, and 30% of twelve-month local-benchmark-relative performance.
- **FR-009**: The product MUST classify an entry as gaining only when its composite is greater than
  zero and greater than its 50-session composite average, declining only when its composite is less
  than zero and less than that average, and neutral otherwise, including equality.
- **FR-010**: Sectors MUST be ranked within their market and industries MUST be ranked within their
  selected market and hierarchy context. Ranking scope MUST be visible.
- **FR-011**: Each scoreboard row MUST show name, rank, status, composite strength, week-over-week
  composite change, rank change, proxy type, data-sufficiency state, and as-of date.
- **FR-012**: Users MUST be able to drill from a market's sectors into a sector's industries while
  retaining market, benchmark, date, return-basis, and active-filter context.
- **FR-013**: Industry evidence MUST include performance relative to both its parent sector and its
  local market benchmark and MUST label each comparison basis.
- **FR-014**: A classification proxy MUST use a documented representative fund, official index, or
  constituent basket; the proxy type, composition basis, qualification state, and effective dates
  MUST be visible.
- **FR-015**: For every classification with sufficient constituent data, the product MUST show the
  percentage of eligible constituents above their 50-session and 200-session moving averages,
  included-member count, eligible-member count, coverage percentage, and observation date. Breadth
  is sufficient only with at least five eligible constituents and histories for at least 80% of them.
- **FR-016**: When both cap-weighted and equal-weight evidence are available, the product MUST show
  their relative outcomes and identify material disagreement as possible concentration.
- **FR-017**: The product MAY show volume-pressure and relative-volume indicators, but MUST label them
  as inferred trading-activity evidence and MUST NOT describe them as actual capital inflow or outflow.
- **FR-018**: Leadership-momentum descriptions MUST be derived from current and prior composite scores
  and ranks, distinguish strengthening from weakening, and remain separate from market regime,
  breadth, trading activity, and observed flows.
- **FR-019**: Observed fund-flow evidence, when available, MUST show monetary net flow, flow relative
  to assets, event period, availability date, age, source, represented classification, and coverage.
- **FR-020**: Observed flow evidence MUST remain contextual and MUST NOT independently alter the core
  leadership score, rank, or status.
- **FR-021**: Changes in asset value, trading volume, on-balance volume, and price-range volume
  indicators MUST NOT be labelled as observed fund flows.
- **FR-022**: Users MUST be able to filter by market, hierarchy level, leadership status,
  momentum state, proxy type, and data sufficiency, and sort by name, rank, composite strength,
  score change, or rank change.
- **FR-023**: The product MUST display active filters, provide a single clear-filter action, and show
  an explanatory empty state when no result matches.
- **FR-024**: Every displayed result and evidence item MUST expose its observation date, comparison
  period, return basis, currency basis, benchmark, representation, source, source availability date,
  coverage, and freshness, or explicitly mark an unavailable field.
- **FR-025**: Missing, stale, misaligned, or insufficient evidence MUST be explicit and MUST NOT
  produce a status or indicator that depends on the missing evidence.
- **FR-026**: The product MUST provide plain-language definitions for market regime, relative
  strength, composite strength, gaining, declining, neutral, strengthening, weakening, breadth,
  concentration, inferred trading activity, observed fund flow, proxy, and insufficient data.
- **FR-027**: The product MUST state that discovery results describe historical evidence and are
  neither forecasts, personalized financial advice, nor trade instructions.

### Requirement Acceptance Coverage

| Requirement | Acceptance coverage |
|-------------|---------------------|
| FR-001–FR-006 | User Story 1; User Story 2, scenarios 1 and 4 |
| FR-007–FR-011 | User Story 2, scenarios 1–3 and 6–7 |
| FR-012–FR-014 | User Story 2, scenarios 4–5 |
| FR-015–FR-018 | User Story 3, scenarios 1–5 |
| FR-019–FR-021 | User Story 4, scenarios 1–5 |
| FR-022–FR-023 | User Story 5, scenarios 1–4 |
| FR-024–FR-027 | User Story 1, scenario 5; User Story 5, scenarios 5–6 |

### Domain Terms

- **Market**: An equity investment universe with a local benchmark, currency, trading calendar, and
  dated membership; it is not determined solely by the exchange where a proxy fund trades.
- **Market regime**: A local market benchmark's broad state: bullish, bearish, or sideways.
- **Relative strength**: The percentage-point difference between a classification's return and its
  named benchmark's return over the same period, return basis, and ending observation.
- **Composite strength**: The weighted combination of three-, six-, and twelve-month relative strength.
- **Leadership status**: Gaining, declining, neutral, or insufficient according to the composite and
  its comparison average; it is distinct from absolute gain or loss.
- **Leadership momentum**: The direction and persistence of changes in a classification's composite
  score and rank, described as strengthening, weakening, stable, or insufficient.
- **Breadth**: The proportion of eligible constituents participating in a move, with coverage shown.
- **Concentration evidence**: A difference between cap-weighted and equal-weight outcomes that may
  indicate a move is driven disproportionately by larger constituents.
- **Inferred trading activity**: Price-and-volume evidence that estimates buying or selling pressure
  but does not directly observe investor subscriptions, creations, redemptions, or withdrawals.
- **Observed fund flow**: Dated fund creation, redemption, subscription, or withdrawal evidence from
  a stated source, normalized by assets when possible and limited to its represented coverage.
- **Proxy**: A documented fund, official index, or constituent basket representing a classification.
- **Insufficient data**: Required history, alignment, freshness, or coverage is absent, so the affected
  result receives no dependent status or indicator.

### Scope Boundaries

**In scope**:

- Discovery across one or several supported equity markets.
- Local market regimes and weekly sector and industry leadership.
- Sector-to-industry drill-down with retained market and benchmark context.
- Absolute performance, relative strength, composite leadership, rank and score changes.
- Breadth, concentration, and labelled trading-activity confirmation where data permits.
- Separately labelled observed fund-flow evidence where reliable coverage is available.
- Filters, sorting, provenance, freshness, coverage, and interpretation guidance.

**Out of scope for this release**:

- Saved watchlists, watchlist alerts, and watchlist prioritization.
- Portfolio creation, holdings, transactions, performance, allocation, risk, or tax tracking.
- Stock selection, buy candidacy, trade execution, order routing, automatic buy or sell decisions,
  price forecasts, personalized financial advice, and automatic sell signals.
- A single pooled cross-market ranking without a separately specified comparison methodology.
- Assuming that price returns, traded volume, or asset-value changes are measured capital flows.
- Non-equity asset discovery and a universal taxonomy for future asset categories.
- User accounts, collaborative sharing, and saved screens.

### Key Entities

- **Market**: A dated investment universe with local benchmark, currency, trading calendar, regime,
  observation date, freshness, and supported classification coverage.
- **Classification Node**: A dated sector or industry with parent-child relationships and membership.
- **Representation**: A fund, official index, or constituent basket used to represent a classification,
  including its type, composition basis, qualification, and effective dates.
- **Benchmark**: A local or global comparison series with currency, return basis, calendar, and dates.
- **Leadership Snapshot**: A dated weekly set of absolute and relative returns, composite strength,
  status, rank, prior values, score change, rank change, and data sufficiency.
- **Breadth Snapshot**: Dated constituent participation measures with included count, eligible count,
  coverage, and classification-membership date.
- **Concentration Evidence**: Dated cap-weighted and equal-weight outcomes with comparison basis.
- **Trading-Activity Evidence**: Dated price-and-volume indicators explicitly identified as inferred.
- **Observed Flow Evidence**: Dated fund flows with monetary value, asset-normalized value, event
  period, availability date, source, represented classification, age, and coverage.
- **Filter State**: The active market, hierarchy, status, momentum, proxy, sufficiency, and sort choices.

### Dependencies

- Dated daily price and matching return series for representations and benchmarks with sufficient
  history for twelve-month strength and its 50-session average.
- Market definitions, local benchmarks, currencies, trading calendars, and dated sector and industry
  classifications.
- Dated constituent membership, weights, and price histories for breadth and concentration evidence.
- Same-close currency conversion for global comparisons; absent conversion does not invalidate the
  local result.
- Dated observed fund-flow and asset data for any classification where flow evidence is offered.
- Source availability timestamps and freshness policies for every displayed dataset.
- Rights to calculate and display classifications, benchmarks, prices, constituents, and flow evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability testing, at least 90% of first-time users can select one or several markets
  and identify the strongest and weakest sectors in each selected market within 60 seconds.
- **SC-002**: At least 90% of users can drill from a selected sector to its industries and correctly
  identify whether an industry is outperforming its parent sector and local market within 90 seconds.
- **SC-003**: For a controlled acceptance dataset, 100% of regimes, returns, composite scores,
  statuses, ranks, score changes, rank changes, breadth values, coverage values, and insufficiency
  outcomes match the specified rules.
- **SC-004**: At least 90% of users correctly distinguish relative outperformance from an absolute
  gain and inferred trading activity from observed fund flow after reviewing the in-product guidance.
- **SC-005**: Every displayed ranking and supporting indicator exposes or explicitly marks unavailable
  all required dates, benchmarks, bases, sources, freshness, and coverage fields.
- **SC-006**: In a comparison of 20 markets, filter and sort changes present the updated discovery
  result to the user within two seconds for at least 95% of measured interactions.
- **SC-007**: In controlled tests, stale, misaligned, or insufficient inputs produce no falsely current
  leadership status, breadth value, trading-activity signal, or observed-flow claim.
- **SC-008**: In usability testing, no more than 10% of participants interpret discovery results as a
  personalized trade instruction after viewing a representative market-to-industry workflow.

## Assumptions

- Phase 2 foundation is limited to direct daily price and volume ingestion. Canonical contracts for
  FX, classifications, holdings, fundamentals, and observed flows are deferred; this staging does
  not remove their applicable release requirements or authorize unsupported provider claims.
- Phase 2 publishes and loads immutable canonical daily input snapshots. Weekly sector-and-industry
  scoreboards, rankings, and their UI belong to subsequent user-story implementation; input
  snapshots alone do not satisfy the completed-weekly-snapshot discovery requirements.
- In Phase 2, the discovery page defaults to live daily history and offers an explicit mode for
  reading a published input snapshot. Repeated viewing in snapshot mode makes no external data
  requests; switching modes does not imply an automatic switch to a different source.
- Phase 2 live ingestion supports the US market only. Additional live markets require their own
  benchmark, calendar, currency, classification, and source contracts before being advertised.
- The first implementation may support only a subset of markets, but the available set is explicit
  and the selection behavior supports both one and several markets.
- GICS or an equivalently documented sector-and-industry taxonomy is available for each supported
  market; taxonomy differences are not silently merged.
- After weekly scoreboards are introduced, the latest completed weekly snapshot is the default
  analysis point. Daily observations may support moving averages, breadth, volume evidence, and
  freshness checks.
- Local-market relative strength is authoritative for local discovery. Global-benchmark comparison is
  optional context and requires an aligned currency basis.
- Breadth and concentration are supporting evidence and do not replace the core leadership ranking.
- Observed fund-flow coverage is partial, fund-specific, and contextual; unavailable flow data does
  not prevent price-based discovery.
- Breadth requires at least five eligible constituents and sufficient histories for at least 80% of
  them; the included count, eligible count, and resulting coverage remain visible.
- Watchlists and portfolio tracking will be specified as separate future features and add no storage,
  controls, terminology, or acceptance obligations to this release.
