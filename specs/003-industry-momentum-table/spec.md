# Feature Specification: Industry Momentum Table

**Feature Branch**: `003-industry-momentum-table`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "industries shall be display within the discovery page in form of perfomance table. the goal is to find industries that recently gain momentum. review the document references for mor edetail on gaining and declining industries. the same criteria as for sectors with respect to chart analysis hold for industires."

## Simplification Decision

### Session 2026-10-29 — Live-Only Interface

- The root experience contains only **Discovery** and **Industry Deep-Dive**. Fundamental Grading
  is removed from the current interface.
- Discovery has one live-data experience using yfinance. It does not expose a provider selector,
  weekly leadership, published snapshots, acceptance comparison, or synthetic-fixture modes.
- The product does not fall back to snapshots, fixture data, or another provider when live data is
  unavailable. It shows an actionable error instead.
- Industry Deep-Dive accepts only a reviewed live membership catalog. Synthetic fixture catalog
  selection is removed from the interface.
- Test doubles may remain test-only so automated tests do not require network access; they are not
  selectable runtime evidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify Emerging Industry Momentum (Priority: P1)

As an investor, I want to see industries in the Discovery page ranked by recent performance, so I
can quickly identify industries gaining or losing momentum.

**Why this priority**: A ranked industry view lets investors move from broad sector performance to
the more actionable industries driving or weakening within those sectors.

**Independent Test**: Provide industries with known recent returns, including positive, negative,
zero, tied, and insufficient values; verify that the table presents the correct order, direction,
and data-quality state.

**Acceptance Scenarios**:

1. **Given** a completed observation period with industry data, **When** the user opens Discovery,
   **Then** they see an industry performance table that defaults to recent one-week performance.
2. **Given** industries with positive, negative, and zero returns, **When** the table is displayed,
   **Then** positive returns are labelled gaining, negative returns declining, and zero returns
   neutral.
3. **Given** a selected sector or sectors, **When** the table is refreshed, **Then** it contains
   only industries belonging to those sectors and identifies each parent sector.
4. **Given** tied performance values, **When** industries are ranked, **Then** tied industries
   share a rank and have a stable, predictable display order.

---

### User Story 2 - Focus the Momentum View (Priority: P2)

As an investor, I want to select a recent-performance period, direction, and parent sectors, so I
can focus on newly strong industries or investigate declining groups without losing the comparison
context.

**Why this priority**: Momentum is time-sensitive and the useful comparison set depends on the
investor's current sector focus.

**Independent Test**: Change the period, direction, and sector selections using a known industry
set, then verify every visible row meets all selected filters and that ranks are calculated within
the visible scope.

**Acceptance Scenarios**:

1. **Given** available one-day and one-week observations, **When** the user changes the period,
   **Then** returns, ranks, directions, and observation details update to the selected period.
2. **Given** industries in every direction, **When** the user filters for gaining, declining,
   neutral, or all industries, **Then** only rows in the selected direction are shown.
3. **Given** several selected sectors, **When** the user views the table, **Then** industries from
   all selected sectors are compared together and the displayed ranking scope is clear.

---

### User Story 3 - Validate Momentum With Industry Charts (Priority: P3)

As an investor, I want each industry to have the same chart-analysis evidence available as a
sector, so I can assess whether recent performance is supported by price trend and trading activity
rather than treating the table as a prediction.

**Why this priority**: The performance table identifies where to look; comparable chart evidence
helps users judge the quality and context of that recent move.

**Independent Test**: Choose an industry with adequate history and compare its displayed chart
evidence with its sector's analytic criteria; verify the industry result uses the same criteria,
labels unavailable evidence explicitly, and does not imply a forecast.

**Acceptance Scenarios**:

1. **Given** an industry row with adequate history, **When** the user inspects its chart, **Then**
   the chart provides the same price, moving-average, trend, and volume analysis available for a
   sector.
2. **Given** inadequate industry history or unavailable observations, **When** the user inspects
   the chart, **Then** the affected analysis is identified as insufficient rather than estimated.
3. **Given** a gaining or declining industry, **When** its chart is displayed, **Then** the
   performance direction is presented as historical evidence and not as a recommendation or
   prediction.

### Edge Cases

- An industry without a qualified representation or sufficient completed-session history is shown
  as insufficient, with no fabricated return, rank, direction, or chart conclusion.
- An industry return exactly equal to zero is neutral and is not included in gaining or declining
  results.
- If an observation date is stale relative to the selected period, the table identifies the date
  and freshness state rather than presenting it as current.
- When a selected sector has no available industries, the table explains that no eligible industry
  data is available while preserving the user's sector selection.
- If an industry changes parent-sector classification at the observation date, the displayed
  parent sector and ranking use the dated classification rather than a current replacement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Discovery MUST include an industry performance table alongside the existing sector
  discovery evidence, without removing sector performance information.
- **FR-002**: The industry table MUST default to ranking eligible industries by descending absolute
  adjusted price return across five completed trading sessions, and MUST support a one completed
  trading-session view.
- **FR-003**: The table MUST calculate return as the percentage change between the selected
  period's starting and ending completed-session adjusted closing prices, using the same price
  basis for all displayed industries.
- **FR-004**: The table MUST label a positive return as gaining, a negative return as declining,
  and a zero return as neutral. It MUST support gaining, declining, neutral, and all-direction
  views.
- **FR-005**: Each eligible industry row MUST show industry name, parent sector, representation,
  selected period, return, direction, rank, observation date, source, and data sufficiency.
- **FR-006**: The table MUST support filtering by one or more parent sectors and MUST visibly state
  the active sector, period, and direction scope. Multiple selected sectors form one comparison
  set.
- **FR-007**: Ranking MUST be recalculated for the displayed eligible set. Equal returns share the
  same rank; ties are ordered by industry name and then stable industry identifier. Insufficient
  industries have no rank.
- **FR-008**: An industry representation MUST be documented as appropriate for that industry.
  When no qualified representation or adequate history exists, the product MUST show the industry
  as insufficient and MUST NOT substitute a broad, mismatched, or guessed representation.
- **FR-009**: Users MUST be able to sort the visible industry rows by the displayed table fields
  without altering the underlying observations or calculated values.
- **FR-010**: Selecting an industry MUST make its corresponding chart analysis available and retain
  the user's current Discovery filters and observation context.
- **FR-011**: Industry chart analysis MUST apply the same criteria and interpretations as sector
  chart analysis for price history, 50-session and 150-session moving averages, average trend,
  and official-session volume. A criterion that cannot be calculated from the industry's own
  completed-session history MUST be marked insufficient.
- **FR-012**: The industry chart MUST present the active performance period, observation date, and
  analytic evidence clearly enough for a user to distinguish historical momentum from a forecast.
- **FR-013**: Industry and sector charts MUST use their own respective observations; an industry's
  result MUST NOT inherit a sector's return, trend, moving-average value, or volume evidence.
- **FR-014**: The feature MUST preserve the existing treatment of source, requested date, observed
  date, freshness, and unavailable data so users can assess whether table and chart evidence is
  current.
- **FR-015**: The root interface MUST expose only Discovery and Industry Deep-Dive. It MUST NOT
  expose Fundamental Grading, a synthetic-fixture mode, published-snapshot mode, acceptance mode,
  weekly-leadership mode, or a provider selector.
- **FR-016**: Discovery MUST request live yfinance data only. It MUST identify yfinance and the
  requested/observed dates, and MUST show a clear error without fallback when the live request
  fails or is incomplete.
- **FR-017**: Industry Deep-Dive MUST accept only a reviewed live membership catalog. Missing,
  invalid, stale, or unapproved catalog evidence MUST block member display and clear only
  dependent stock selections.

### Key Entities *(include if feature involves data)*

- **Industry Performance Observation**: A dated performance result for an industry representation,
  including period return, direction, rank eligibility, source, and sufficiency.
- **Industry Representation**: The documented instrument or basket used to represent an industry,
  distinct from its member-stock list and identified with its scope limitations.
- **Dated Industry Classification**: The industry identity, stable identifier, parent sector, and
  effective date used to filter and rank table rows.
- **Industry Chart Evidence**: The industry's completed-session price, moving-average, trend, and
  volume observations, with their availability and freshness state.
- **Discovery Filter Context**: The selected sectors, performance period, direction view, and
  observation date that define the visible comparison set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of first-time test users identify the strongest gaining and weakest
  declining eligible industry in a selected scope within 60 seconds.
- **SC-002**: Controlled cases match 100% of specified one-day and one-week returns, direction
  labels, ranks, tied-row order, parent-sector filters, and insufficiency outcomes.
- **SC-003**: At least 90% of test users can change sector, period, and direction filters and
  correctly explain the resulting ranking scope within two minutes.
- **SC-004**: For every industry with adequate history in controlled data, its chart displays all
  applicable sector-equivalent analysis criteria; 100% of unavailable criteria are labelled
  insufficient rather than shown as calculated values.
- **SC-005**: With previously available data for 100 industries, 95% of table sorting, filtering,
  selection, and chart-opening interactions present their updated result within two seconds.
- **SC-006**: At least 90% of test users correctly describe a gaining or declining label as a
  historical performance result rather than a prediction after inspecting an industry chart.

## Assumptions

- The feature extends the existing Discovery experience for the initial US market and does not add
  saved screens, alerts, recommendations, trading, portfolio functions, or multi-market coverage.
- "Recently" defaults to five completed trading sessions, with one completed trading session
  available for short-term comparison, matching the existing short-period industry-discovery
  specification.
- The project’s documented industry-representation rules remain the authority for deciding whether
  an industry can be ranked or charted; visible insufficiency is preferable to inferred coverage.
- The sector chart analysis criteria named in this specification are the current sector criteria.
  If those criteria change, industry chart analysis changes in the same way to remain consistent.
- Existing sector performance, source, freshness, and unavailable-data disclosures remain
  available and are not redesigned by this feature.
- yfinance is the sole configured runtime provider for this simplified experience. Provider
  configuration outside this single choice is out of scope.
- Synthetic data may remain in automated tests but is not a user-visible or runtime data mode.
