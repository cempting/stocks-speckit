# Tasks: Stock Table Columns

**2026-11-01 presentation amendment**: The user approved five visible columns, with the company
name retained in the Ticker button rather than a separate Name column. The completed six-column
tasks below preserve historical implementation evidence; the current contract and regression
tests supersede that presentation. Catalog name fields, details, and selection identity are unchanged.

**Input**: Design documents from `/specs/006-stock-table-columns/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[stock-table.md](./contracts/stock-table.md), and [quickstart.md](./quickstart.md)

**Tests**: Tests are required by the constitution and plan. Write focused tests before each
behavioral change and confirm they reject the old table/evidence contract.

## Phase 1: Setup

**Purpose**: Reuse the existing application, explicit score-load action, provider, and test
fixtures.

No setup task is needed. This feature adds no dependency, configuration, provider, or persistence
layer.

## Phase 2: Foundational

**Purpose**: Supply current capitalization through the existing explicit fundamental-score flow.

- [X] T001 [P] Add current-capitalization extraction/validation tests in `tests/unit/test_fundamentals.py` and `tests/integration/test_yfinance_fundamentals.py` for numeric finite positive profile values and the exact unavailable cases: missing, non-numeric, non-finite, and non-positive values.
- [X] T002 [P] Add evidence-handoff tests in `tests/integration/test_stock_evidence.py` for preserving current capitalization/as-of evidence from the explicit score load and for retaining no value after failed or incomplete evidence.

## Phase 3: User Story 1 - Compare Stock Table Columns (Priority: P1) 🎯 MVP

**Goal**: Render exactly Price chart + 50 MA, Volume chart, Ticker, Name, CAP Type, and Total
Score, with deterministic capitalization classification and no hidden loads.

**Independent Test**: Use controlled current-capitalization values at $10B, $2B, and below $2B,
alongside unloaded/invalid values. Verify the exact six-column order, Large/Mid/Small/Unavailable
mapping, unchanged Total Score states, and no score request until the existing explicit action.

### Tests for User Story 1

- [X] T003 [P] [US1] Add table-projection tests in `tests/unit/ui/test_progressive_tape.py` for the exact six visible columns and CAP Type boundaries: "`Large`: capitalization >= $10,000,000,000", "`Mid`: capitalization >= $2,000,000,000 and < $10,000,000,000", "`Small`: capitalization > 0 and < $2,000,000,000", and `Unavailable` for invalid/missing values.
- [X] T004 [P] [US1] Extend `tests/app/test_sector_stock_explorer.py` to verify the contained-stocks table headings/order, renamed Total Score, CAP Type unavailable before loading, and no implicit score or capitalization request.

### Implementation for User Story 1

- [X] T005 [US1] Extend current fundamental evidence in `src/market_leadership/domain/fundamentals.py` and `src/market_leadership/infrastructure/yfinance_fundamentals.py` to retain only valid current profile capitalization with its fetch date, without changing historical peer-score market-cap rules.
- [X] T006 [US1] Extend `src/market_leadership/application/score_industry.py` and `src/market_leadership/ui/workflows/discovery_page.py` to pass optional current capitalization from the existing explicit score-load result into each stock table row without issuing a new request.
- [X] T007 [US1] Update `src/market_leadership/ui/components/progressive_tape.py` to classify CAP Type and render the exact six-column order; rename Score to Total Score while preserving the existing three-component calculation and explicit states.

**Checkpoint**: Investors can compare every selected-industry stock using the required six columns;
CAP Type is accurate for valid loaded evidence and explicit otherwise.

## Phase 4: User Story 2 - Preserve Stock Table Evidence States (Priority: P2)

**Goal**: Keep chart, placeholder, and unavailable-evidence disclosures visible in the concise
six-column table.

**Independent Test**: Render unavailable/insufficient chart evidence and an unresolved placeholder
with missing capitalization. Verify required chart captions, placeholder identity, CAP Type
Unavailable, and Total Score's explicit state remain visible.

**Dependency**: Requires T007's finalized column projection.

### Tests for User Story 2

- [X] T008 [US2] Extend `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_sector_stock_explorer.py` with unavailable/insufficient chart, placeholder, invalid-capitalization, and non-numeric Total Score cases; confirm no required chart-cell disclosure is hidden by the column change.

### Implementation for User Story 2

- [X] T009 [US2] Preserve chart-cell unavailable/insufficient captions and unresolved-placeholder identity in `src/market_leadership/ui/components/progressive_tape.py` while applying CAP Type/Total Score columns; do not fabricate capitalization or score values.

**Checkpoint**: The reduced column set remains truthful for incomplete evidence and placeholders.

## Phase 5: Polish & Cross-Cutting Validation

- [X] T010 Run the focused contract validation in `specs/006-stock-table-columns/quickstart.md`: fundamental, tape, stock-evidence, and app tests; Ruff; and Pyright. Confirm no new provider call occurs during ordinary table rendering and stock-detail/sector/industry presentations are unchanged.

## Dependencies & Execution Order

### Phase Dependencies

- T001 and T002 may start immediately.
- T003 and T004 may start immediately, but their final assertions depend on T005-T007.
- T005 depends on T001; T006 depends on T002 and T005; T007 depends on T003, T004, and T006.
- T008 follows T007; T009 follows T008; T010 follows T009.

### User Story Dependencies

- **US1 (P1)**: Independent MVP after the foundational evidence handoff.
- **US2 (P2)**: Depends on US1's finalized table projection.

### Parallel Opportunities

- T001 and T002 modify independent evidence test targets and can proceed in parallel.
- T003 and T004 modify independent projection/AppTest targets and can proceed in parallel.

## Parallel Examples

```text
Task: T001 Add current-capitalization validation tests in tests/unit/test_fundamentals.py
Task: T002 Add explicit score-load capitalization-handoff tests in tests/integration/test_stock_evidence.py
```

```text
Task: T003 Add CAP threshold and column-order projection tests in tests/unit/ui/test_progressive_tape.py
Task: T004 Add table heading/no-hidden-load AppTest in tests/app/test_sector_stock_explorer.py
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T004 to define evidence and table contracts.
2. Complete T005-T007.
3. Validate the six columns, CAP thresholds, and no-hidden-load behavior.

### Incremental Delivery

1. Deliver the current-capitalization evidence handoff and six-column MVP.
2. Add the P2 incomplete-evidence/placeholder regression protection.
3. Complete cross-cutting validation in T010.

## Notes

- Do not add a new capitalization request, provider, cache family, persistence record, currency
  conversion, historical CAP Type, configurable thresholds, or partial Total Score.
- Do not alter the peer-score Cash Flow historical market-cap validation, stock detail, or sector
  and industry presentations.
