# Tasks: Industry Momentum Table Spike

**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), and
[quickstart.md](./quickstart.md)

**Scope**: Deliver the safe, snapshot-backed industry-performance-table increment. Live industry
coverage and industry-owned chart data remain fail-closed until qualified representations,
membership, price history, volume, and display rights can be published together.

## Phase 1: Snapshot-Backed Performance Table

**Goal**: Replace the generic weekly industry ranking grid in Discovery with a short-period
performance table that preserves the source and sufficiency evidence of the validated snapshot.

**Independent Test**: Using fixture weekly snapshots, select a sector in Discovery and confirm its
industry rows show one-week and one-month outcomes, gain/decline direction, parent sector,
representation, date, source, sufficiency, and missing evidence.

- [X] T001 Add a deterministic industry-table projection test with gaining, declining, and
  insufficient rows in `tests/unit/ui/test_performance_table.py`.
- [X] T002 Implement stable industry projection, one-week direction labels, and required evidence
  columns in `src/market_leadership/ui/performance_table.py`.
- [X] T003 Render the styled short-period industry performance table in the weekly Discovery drill
  down in `src/market_leadership/ui/workflows/industry_detail.py`.
- [X] T004 Verify the weekly Discovery drill-down uses the table through
  `tests/app/test_scoreboard.py`.

## Phase 2: Documentation and Validation

- [X] T005 Document the weekly industry performance table and evidence disclosures in `README.md`.
- [X] T006 Run the focused unit and Discovery workflow validation in
  `tests/unit/ui/test_performance_table.py`, `tests/app/test_scoreboard.py`, and
  `tests/app/test_industry_discovery.py`.

## Dependencies & Execution Order

T001 precedes T002; T002 precedes T003; T003 precedes T004. Documentation and focused validation
follow the completed table behavior.

## Deferred Follow-Up

The full specification's multi-sector filtering and industry-owned chart evidence require an
approved, persisted industry daily-history contract. They are intentionally not approximated in
this spike: substituting sector data or unverified live data would violate the documented
fail-closed data rules.

## Phase 3: Convergence

- [X] T007 CRITICAL Replace the three-tab, multi-mode runtime with the two-tab, yfinance-only,
  fail-closed Discovery journey per FR-015, FR-016, and plan: live-only Discovery
  (contradicts).
- [X] T008 Implement selectable one-day/one-week, direction, and multi-sector industry momentum
  filtering with scoped recalculated tie ranks, sorting, disclosures, and deterministic coverage
  per FR-001–FR-009, US1/AC1–AC4, US2/AC1–AC3, SC-002, and SC-003 (partial).
- [X] T009 Implement qualified industry selection and industry-owned price, moving-average, trend,
  and volume chart evidence with explicit insufficiency and historical-not-predictive disclosures
  per FR-010–FR-013, US3/AC1–AC3, SC-004, and SC-006 (missing).
- [X] T010 Restrict Industry Deep-Dive to validated reviewed live membership catalogs and reconcile
  only dependent selections when catalog evidence changes or becomes invalid per FR-017 and
  plan: reviewed live membership (contradicts).
- [X] T011 Replace obsolete multi-mode AppTest coverage with deterministic live-only,
  yfinance-source, fail-closed Discovery and reviewed-live-membership workflow tests per
  plan: AppTest validation and Constitution development workflow (partial).
