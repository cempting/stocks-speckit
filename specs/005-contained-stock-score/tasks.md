# Tasks: Contained Stock Score Summary

> Consolidated into [006](../006-stock-table-columns/spec.md) on 2026-11-02.
> Retain task IDs/completion markers as historical evidence, not an independent backlog.
> Reconcile unfinished work before execution; old column labels/order are superseded.

**Input**: Design documents from `/specs/005-contained-stock-score/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contained-stock-table.md](./contracts/contained-stock-table.md), and
[quickstart.md](./quickstart.md)

**Tests**: Tests are required by the project constitution and plan. Add the focused tests before
the corresponding projection changes and confirm they distinguish the prior table contract.

## Phase 1: Setup

**Purpose**: Confirm the existing focused UI test targets are available.

No setup task is needed. The existing Streamlit application, peer-scorecard model, and pytest
test targets are reused without new dependencies or configuration.

## Phase 2: Foundational

**Purpose**: Preserve the existing score-loading and chart-evidence boundaries.

No foundational task is needed. The feature extends the existing contained-stock projection and
must not modify score acquisition, persistence, provider access, session state, or stock-detail
rendering.

## Phase 3: User Story 1 - Compare Stocks by Overall Score (Priority: P1) 🎯 MVP

**Goal**: Replace component scores with one trustworthy overall Score that is calculated only
when all three existing score components are available.

**Independent Test**: Build controlled contained-stock rows with complete, not-loaded,
insufficient, unavailable, error, and placeholder evidence. Verify the table has exactly one
Score column, displays the correctly rounded equal-weight mean only for complete evidence, never
uses a numeric fallback, and performs no implicit score load.

### Tests for User Story 1

- [X] T001 [P] [US1] Add frame-projection tests in `tests/unit/ui/test_progressive_tape.py` for one decimal Score values and explicit `Not loaded`, `Error`, `Insufficient`, and `Unavailable` states; quote the invariant that "`available` requires all three component blocks to be `available` with finite values from 0 to 100 inclusive" and that "`value` is `(quality + growth + cash_flow) / 3`".
- [X] T002 [P] [US1] Add contained-stock AppTest assertions in `tests/app/test_sector_stock_explorer.py` that only one Score column is rendered after explicit score loading, Quality/Growth/Cash Flow/Score Status are absent, and opening or rerendering the tape does not invoke the existing score-load action.

### Implementation for User Story 1

- [X] T003 [US1] Implement the Overall Score projection in `src/market_leadership/ui/components/progressive_tape.py`; replace component-score/status output with Score, calculate the equally weighted three-component average only for three available finite 0–100 values, and preserve explicit non-numeric states without changing score loading.

**Checkpoint**: Investors can compare the selected industry's stocks by one accurate Score, while
every incomplete evidence case remains explicit.

## Phase 4: User Story 2 - Focus the Contained-Stocks Table (Priority: P2)

**Goal**: Remove redundant row metadata while retaining the direct chart-evidence disclosures
needed to understand missing or insufficient data.

**Independent Test**: Render contained-stock rows with unavailable, insufficient, and placeholder
chart evidence. Verify Observed and Chart Status are absent while the corresponding chart-cell
captions and placeholder identity remain visible.

**Dependency**: Requires T003 because the same contained-stock projection owns the retained and
removed column contract.

### Tests for User Story 2

- [X] T004 [US2] Extend projection and AppTest coverage in `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_sector_stock_explorer.py` to assert the visible order Price chart, Volume chart, Ticker, Name, Price, Score; assert Observed and Chart Status are absent; and prove price/volume chart-cell insufficient/unavailable disclosures and placeholder identity remain.

### Implementation for User Story 2

- [X] T005 [US2] Remove Observed and Chart Status from the contained-stock frame in `src/market_leadership/ui/components/progressive_tape.py` without changing the existing chart-cell disclosure paths, internal Instrument ID/Resolution selection fields, or price/volume/ticker/name/price presentation.

**Checkpoint**: The contained-stocks table is focused on comparison data without hiding chart
evidence or breaking stock selection.

## Phase 5: Polish & Cross-Cutting Validation

**Purpose**: Validate the complete table contract and guard unrelated views against regression.

- [X] T006 Run the focused contract validation from `specs/005-contained-stock-score/quickstart.md`: `tests/unit/ui/test_progressive_tape.py`, `tests/app/test_sector_stock_explorer.py`, Ruff, and Pyright; confirm sector, industry, and stock-detail score presentations remain outside this feature's diff.

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 and Phase 2 contain no implementation work.
- T001 and T002 may start immediately.
- T003 depends on T001 and T002.
- T004 depends on T003's Score-column contract.
- T005 depends on T004.
- T006 depends on T005.

### User Story Dependencies

- **US1 (P1)**: Independent and forms the MVP.
- **US2 (P2)**: Depends on US1 because both changes share the contained-stock projection.

### Parallel Opportunities

- T001 and T002 may proceed in parallel because they modify different test files.

## Parallel Example: User Story 1

```text
Task: T001 Add Overall Score frame-projection tests in tests/unit/ui/test_progressive_tape.py
Task: T002 Add rendered Score-column/no-implicit-load AppTest in tests/app/test_sector_stock_explorer.py
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 and T002.
2. Complete T003.
3. Validate that one Score replaces the four component/status columns without new data loading.

### Incremental Delivery

1. Deliver the US1 Score projection and evidence-state contract.
2. Deliver US2 column removal while retaining chart-cell evidence.
3. Complete T006 before presenting the feature as finished.

## Notes

- Do not create a persisted aggregate, configurable weights, partial averages, or score-triggered
  provider requests.
- Do not change scorecard formulas, peer eligibility, sector/industry tables, or stock-detail
  scorecard presentation.
