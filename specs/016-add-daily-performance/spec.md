# Feature Specification: Add Daily Performance

**Feature Branch**: `main` (no branch-creation hook configured)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "the sector performance and industry momentum tables show the performanc over 1w 1m 3m 6m 1y, I would like to add 1day performance in front of 1w as well, indicate the column as 1d."

## Clarifications

### Session 2026-11-06

- Q: When prices are stale, should `1d` use the latest completed trading session on or before your selected date, or show an older daily return? → A: Use the latest completed trading session on or before the selected as-of date and its immediately preceding trading session. Missing either exact close produces `Unavailable`; do not move the interval back to an older observed date. Retain freshness warnings and valid longer-period returns.
- Q: How should `representation_performance` expose `1d`? → A: Return all six periods by default; update callers to handle unavailable periods independently. Valid longer-period return arithmetic remains unchanged, but supported horizons may display even when another horizon lacks history. Preserve ranking/snapshot contracts.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Daily Sector Performance (Priority: P1)

As a user reviewing Sector performance, I want to see each sector's one-day return immediately before its one-week return so I can compare the latest daily movement with longer-term performance.

**Why this priority**: Daily movement adds the requested shortest performance horizon to the first stage of market discovery.

**Independent Test**: Open Sector performance with known completed-session prices and verify the `1d` column's position, percentages, and treatment of unavailable evidence without selecting an industry.

**Acceptance Scenarios**:

1. **Given** Sector performance is displayed, **When** the user reads the performance columns, **Then** `1d` appears immediately before the existing one-week column, followed by the unchanged one-month, three-month, six-month, and one-year columns.
2. **Given** a sector's two latest eligible adjusted completed-session closes are 100 and 102, **When** Absolute performance is displayed, **Then** its `1d` cell displays a positive 2.00% return using the existing gain formatting.
3. **Given** the one-day return is negative or zero, **When** the sector table is displayed, **Then** the cell uses the existing loss or neutral formatting, respectively.

---

### User Story 2 - Compare Daily Industry Momentum (Priority: P1)

As a user reviewing Industry momentum, I want the same one-day performance column so I can compare industries within my selected sector using the same horizons as the sector table.

**Why this priority**: Both named tables are required for a complete and consistent daily-performance feature.

**Independent Test**: Select a sector and view Industry momentum with known industry price histories; verify `1d` independently of sector-return values.

**Acceptance Scenarios**:

1. **Given** a sector is selected, **When** Industry momentum is displayed, **Then** `1d` appears immediately before the existing one-week column and all five longer-term columns remain available in their existing order.
2. **Given** an industry's approved representation has adjusted completed-session closes of 200 and 198, **When** Absolute performance is displayed, **Then** its `1d` cell displays -1.00%, based on that industry's evidence rather than its parent sector.
3. **Given** a user navigates between sector and industry tables or changes the thumbnail period, **When** the active table is displayed, **Then** `1d` remains present and its return is independent of the thumbnail period.

---

### User Story 3 - Interpret Daily Returns Consistently (Priority: P2)

As a user, I want daily returns to follow the selected performance basis and identify insufficient evidence so I do not mistake missing or incomplete prices for valid daily movement.

**Why this priority**: Consistent basis and availability semantics make the new column trustworthy without introducing new controls.

**Independent Test**: Exercise both tables with Absolute and vs S&P 500 performance, missing endpoints, and incomplete-session observations.

**Acceptance Scenarios**:

1. **Given** an entity's one-day return is 2.00% and the benchmark's return over the matching completed-session interval is 0.50%, **When** the user selects vs S&P 500, **Then** `1d` displays 1.50% with the existing percentage formatting.
2. **Given** either required entity endpoint is missing or invalid, **When** the table is displayed, **Then** `1d` displays `Unavailable` without gain/loss coloring while valid longer-period results remain visible.
3. **Given** the benchmark lacks a required matching endpoint, **When** vs S&P 500 is selected, **Then** the affected `1d` cell displays `Unavailable` rather than an absolute return.
4. **Given** prices include an incomplete current session or observations after the selected as-of date, **When** daily performance is displayed, **Then** only eligible completed sessions on or before that date determine `1d`.
5. **Given** stale evidence ends before the latest completed trading session on or before the selected as-of date, **When** either table displays daily performance, **Then** `1d` displays `Unavailable` rather than an older daily return, while existing observed-date/freshness disclosures and valid longer-period results remain unchanged.

### Edge Cases

- Weekends and market holidays: one day means one completed trading-session interval, not one calendar day.
- Insufficient history: fewer than two valid eligible completed-session endpoints yields `Unavailable`, not zero.
- Missing representation or missing intervening session evidence: do not use a parent sector, another instrument, or a multi-session interval as a daily-return substitute.
- Invalid endpoints, including a zero or negative starting price: identify the return as unavailable rather than displaying an invalid percentage.
- Zero return: display a neutral two-decimal percentage, distinct from unavailable evidence.
- Stale evidence: retain the existing observation-date and freshness disclosures, but do not move the daily interval back to an older observed date. Missing either required close produces `Unavailable` while valid longer-period results remain visible; do not imply that historical daily movement is current or intraday performance.
- Narrow viewports: keep `1d` adjacent to the one-week column and accessible through the table's existing responsive behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sector performance and Industry momentum MUST each display an additional performance column labeled exactly `1d`, immediately before the existing one-week column.
- **FR-002**: Both tables MUST retain all five existing longer-term performance columns, in their existing order and with their existing labels, valid values, and calculation semantics. Each horizon MUST be independently available; missing yearly history MUST NOT suppress a supported weekly or monthly return.
- **FR-003**: Absolute `1d` MUST represent the percentage change between consecutive adjusted completed-session closes: `100 * (ending close / starting close - 1)`. The ending session MUST be the latest completed official trading session on or before the selected as-of date, excluding any session not yet completed when evaluated; the starting session MUST be its immediately preceding official trading session. These session dates MUST be determined independently of price availability or an older observed date. Missing either exact required close MUST produce `Unavailable`, not an older daily interval. Weekends and holidays MUST NOT be counted as trading sessions.
- **FR-004**: `1d` MUST follow the existing Performance basis selection. Absolute MUST show the entity's daily return; vs S&P 500 MUST subtract the benchmark's daily return over the matching session interval from the entity's daily return.
- **FR-005**: Valid daily returns MUST use the existing right-aligned two-decimal percentage presentation and readable light/dark gain, loss, and neutral palettes. Daily gain/loss color scaling MUST be independent of the longer-period columns, consistent with existing per-period scaling.
- **FR-006**: Missing, invalid, or insufficient entity evidence, or insufficient matching benchmark evidence when benchmark-relative performance is selected, MUST produce `Unavailable` without gain/loss coloring. The affected evidence failure MUST remain identifiable through existing table context or tooltips; no fabricated zero, alternate representation, or silent absolute-return fallback is permitted.
- **FR-007**: Each row's daily return MUST use its own approved representation and completed observations, with the existing source, requested-date, observed-date, and freshness disclosures preserved.
- **FR-008**: Adding `1d` MUST NOT change existing navigation, valid selections, default ranking or sorting, thumbnail periods, charts, other columns, or stock-table behavior. Both performance bases MUST continue to persist across hierarchy navigation, and thumbnail-period changes MUST NOT alter daily returns.
- **FR-009**: `1d` MUST remain visible whenever either named table is rendered with rows, including rows with unavailable daily evidence, and MUST remain accessible and adjacent to the one-week column on supported viewport sizes.

### Key Entities *(include if feature involves data)*

- **Performance row**: A sector or industry and its approved market representation, existing longer-period returns, daily return, and evidence-availability context.
- **Daily performance interval**: The latest completed official trading session on or before the selected as-of date and its immediately preceding official trading session, with adjusted closing prices when available. An older observed date does not change these required session dates; missing exact closing-price evidence makes the daily return unavailable.
- **Performance basis**: The existing Absolute or vs S&P 500 choice; benchmark-relative daily performance requires benchmark evidence for the same interval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tested sector and industry table states containing rows, the six performance horizons appear in order: one day, one week, one month, three months, six months, and one year; the daily header is exactly `1d`.
- **SC-002**: For controlled positive, negative, zero, weekend/holiday, and historical as-of examples, 100% of available daily cells match the expected completed-session return to two decimal places under both performance bases.
- **SC-003**: In 100% of controlled missing or invalid endpoint cases, the affected daily cell displays `Unavailable` without gain/loss coloring and never displays a fabricated return.
- **SC-004**: For the same observations and selections, all previously valid longer-period values and labels, default ordering, chart choices, and valid navigation selections remain unchanged across the tested before/after comparisons. The approved independent-availability change MUST retain supported horizons when another lacks history; ranking/snapshot behavior remains unchanged.
- **SC-005**: Users can compare daily and weekly movement directly in either table without opening another view or changing a period control; acceptance walkthroughs confirm both gaining and declining entities are identifiable from adjacent values.

## Assumptions

- "1day" means one completed trading-session interval, consistent with the existing industry daily-return definition, rather than intraday movement or a trailing 24-hour return.
- The request adds a table column only. It does not add a daily thumbnail option, a period selector, a tab, or a new ranking default.
- Existing market evidence, approved representations, performance-basis controls, and availability/freshness conventions remain dependencies.
- This approved feature supersedes only the five-visible-period limitation and corresponding column-count/order statements in [004's presentation baseline](../004-sector-stock-explorer/spec.md), specifically FR-029, FR-031, and FR-035. All other accepted presentation and evidence constraints remain in force; related planning and contracts must reconcile this narrowly scoped amendment before implementation.
- No changes to Contained stocks, Find a stock, or other stock-detail/table horizons are requested.
