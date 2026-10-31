# Feature Specification: Contained Stock Score Summary

**Feature Branch**: `005-contained-stock-score`

**Created**: 2026-10-30

**Status**: Draft

**Updated**: 2026-10-31 (aligned with feature 010)

**Input**: User description: "adjust the contained stocks table, replace Quality, Growth,
CashFlow, Score Status by an overall Score; remove Observed and Chart Status"

## Catalog Authority and Preserved Scope

The [feature 010 specification](../010-manifest-csv-catalogs/spec.md) governs stock identity and
membership: one stock CSV per region, exact reviewed industry/hierarchy references, and a
manifest-backed file-only release. No catalog database, embedded stock list, or runtime fixture
may supply comparison rows. This storage change does not alter component-score formulas,
complete-cohort peer populations, explicit score loading, or missing-evidence states.
Feature 006 supersedes this feature's column label/order with Total Score and its six-column table.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Stocks by Overall Score (Priority: P1)

As an investor viewing the contained-stocks table, I want one overall Score for each stock instead
of separate Quality, Growth, Cash Flow, and score-status columns, so I can compare the stocks in
an industry more quickly.

**Why this priority**: The table's primary purpose is to support concise comparison of stocks in
the selected industry.

**Independent Test**: Display stocks with complete, incomplete, unavailable, and not-yet-loaded
score evidence and verify that each row shows exactly one overall Score with an explicit state
when a score cannot be calculated.

**Acceptance Scenarios**:

1. **Given** a contained-stocks table with complete score evidence for a stock, **When** the
   table is shown, **Then** the stock displays one overall Score and does not display separate
   Quality, Growth, Cash Flow, or score-status columns.
2. **Given** a stock with incomplete or unavailable score evidence, **When** the table is shown,
   **Then** its overall Score explicitly communicates that it is unavailable or insufficient and
   is not presented as a numeric score.
3. **Given** score evidence has not been requested, **When** the table is shown, **Then** the
   overall Score indicates that it has not been loaded without triggering an implicit score load.
4. **Given** a newly activated reviewed stock/hierarchy release, **When** the table is rebuilt,
   **Then** only effective members appear, invalid selections and affected peer results are
   reconciled, and unchanged valid score evidence is retained without an implicit reload.

### User Story 2 - Focus the Contained-Stocks Table (Priority: P2)

As an investor reviewing contained stocks, I want non-comparison metadata removed from the table,
so the remaining columns emphasize charts, identity, current price, and overall Score.

**Why this priority**: Observed date and chart-status columns duplicate information or distract
from the intended comparison workflow.

**Independent Test**: Open the contained-stocks table with rows that have available and
unavailable chart evidence and verify that neither Observed nor Chart Status is shown while
unavailable chart evidence remains visibly identified in the chart cells.

**Acceptance Scenarios**:

1. **Given** any contained-stocks table state, **When** the table is shown, **Then** it has no
   Observed or Chart Status column.
2. **Given** a stock with missing or insufficient price or volume evidence, **When** the table is
   shown, **Then** the relevant chart cell continues to disclose the condition after the two
   columns are removed.

### Edge Cases

- Stocks without sufficient underlying evidence do not receive a fabricated, zero, or stale
  overall Score.
- A score that has not been loaded remains distinct from an unavailable or insufficient score.
- Placeholder stocks retain their unresolved identity and do not obtain an overall Score merely
  because the other columns have been simplified.
- Removing the two metadata columns does not remove existing chart-level error or insufficiency
  disclosures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The contained-stocks table MUST replace the Quality, Growth, Cash Flow, and Score
  Status columns with exactly one column named Score.
- **FR-002**: The Score column MUST use a single, consistent overall-score calculation for every
  eligible stock in the selected industry.
- **FR-003**: The Score MUST equal the equally weighted average of the Quality, Growth, and Cash
  Flow scores only when all three component scores are available; otherwise, the Score MUST be
  unavailable.
- **FR-004**: The Score column MUST distinguish a calculated numeric score from not loaded,
  insufficient, unavailable, and error states without representing any of those states as a
  numeric score.
- **FR-005**: Showing the contained-stocks table MUST NOT initiate score loading unless the user
  explicitly requests it.
- **FR-006**: The contained-stocks table MUST remove the Observed and Chart Status columns.
- **FR-007**: Removing Observed and Chart Status MUST NOT remove existing chart-cell disclosures
  for unavailable, insufficient, or placeholder evidence.
- **FR-008**: The contained-stocks table MUST retain its existing price chart, volume chart,
  ticker, stock name, price, and placeholder identity presentation.
- **FR-009**: Comparison rows and peer membership MUST resolve from the activated regional stock
  CSV and hierarchy, with exact stable identities and effective dates. Catalog changes MUST
  reconcile affected selections/peer results without changing score meaning; absent/invalid
  sources MUST NOT produce guessed members or trigger a legacy database/listing fallback.

### Key Entities *(include if feature involves data)*

- **Overall Score**: One comparison value for a contained stock, derived from the stock's
  available score evidence using the confirmed calculation rule, or represented by an explicit
  non-numeric state.
- **Contained Stock Row**: The displayed stock record containing chart evidence, identity, price,
  and its overall Score.
- **Score Evidence State**: The state that distinguishes calculated, not-loaded, insufficient,
  unavailable, and error score outcomes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In controlled table states, 100% of rows display exactly one Score column and no
  Quality, Growth, Cash Flow, or Score Status column.
- **SC-002**: In controlled complete, not-loaded, insufficient, unavailable, and error cases,
  100% of Score cells display the correct equally weighted three-component average or explicit
  non-numeric state.
- **SC-003**: In controlled table states, 100% of contained-stocks tables omit Observed and Chart
  Status while retaining chart-cell evidence disclosures.
- **SC-004**: Users can identify a stock's price and overall Score from a contained-stocks table
  in under 10 seconds in a representative comparison scenario.
- **SC-005**: In controlled file-release changes with the catalog database unavailable, 100% of
  comparison rows and peer cohorts match effective reviewed membership, zero invalid selections
  remain, and unchanged cohorts retain identical aggregate scores and explicit load behavior.

## Assumptions

- The change applies only to the contained-stocks table, not to sector, industry, or stock-detail
  presentations.
- The existing explicit user action for loading score evidence remains unchanged.
- Overall Score is displayed at the precision already used for score values unless the confirmed
  scoring rule requires a different presentation.
- No historical score data is modified; this feature changes only the contained-stocks
  comparison presentation and the displayed aggregate.
