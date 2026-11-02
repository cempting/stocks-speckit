# Tasks: Industry ETF Momentum

> Consolidated into [008](../008-industry-representation-tools/spec.md) on 2026-11-02.
> Retain task IDs/completion markers as historical evidence, not an independent backlog.
> Reconcile unfinished work with the active owner before execution.

**Input**: Design documents from `/specs/007-industry-etf-momentum/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[industry-etf-momentum-table.md](./contracts/industry-etf-momentum-table.md), and
[quickstart.md](./quickstart.md)

**Tests**: The constitution and implementation plan require focused unit, integration, and AppTest
coverage before implementation.

## Phase 1: Setup

**Purpose**: Reuse the existing Python/Streamlit application, reviewed hierarchy, batched price
history loading, and performance calculation. No dependency or configuration changes are required.

No setup task is needed.

## Phase 2: Foundational

**Purpose**: Define validated reviewed ETF mappings before any table can use them.

- [ ] T001 [P] Create mapping domain tests in `tests/unit/test_industry_etf_mappings.py` for required region/classification/node/ETF fields, normalized symbols, selected-date validity, approved mappings, duplicate identity rejection, and the invariant that a mapping cannot apply to another region, classification, node, or out-of-range date.
- [ ] T002 [P] Create ETF-momentum projection tests in `tests/unit/test_industry_momentum.py` for exact mapped ETF identity, standard-period calculations, and distinct `available`, `insufficient_evidence`, `unavailable_evidence`, `not_covered`, and `invalid_mapping` states.
- [ ] T003 Add `ClassificationEtfMapping` validation and reviewed mapping catalog in `src/market_leadership/domain/industry_etf_mappings.py`; enforce that "`The same ETF symbol may appear in multiple mappings only when each classification mapping is explicitly approved`."

## Phase 3: User Story 1 - View Industry ETF Momentum (Priority: P1) 🎯 MVP

**Goal**: Show industry/sub-industry momentum from each row's exact approved ETF and identify that
ETF in the table.

**Independent Test**: Render a reviewed hierarchy with mapped parent and sub-industry rows; verify
each displayed ETF is the one used for its momentum and differs where mappings differ.

### Tests for User Story 1

- [ ] T004 [P] [US1] Extend `tests/unit/test_industry_momentum.py` with parent/sub-industry fixtures proving each row's displayed ETF equals the sole history symbol used for every displayed momentum value and that approved same-ETF reuse remains explicit.
- [ ] T005 [P] [US1] Extend `tests/app/test_sector_stock_explorer.py` to verify mapped ETF identity and its momentum appear for visible reviewed industry/sub-industry rows without changing the contained-stock table.

### Implementation for User Story 1

- [ ] T006 [US1] Extend `src/market_leadership/domain/industry_momentum.py` to resolve the exact approved mapping for each reviewed hierarchy row and calculate momentum only from that mapped ETF, preserving the selected as-of date.
- [ ] T007 [US1] Update `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/components/progressive_tape.py` to batch-load only distinct valid mapped ETF symbols in the active scope and render the mapped ETF identity beside its momentum.

**Checkpoint**: A visible mapped parent or sub-industry row identifies the exact ETF from which every
shown momentum value was calculated.

## Phase 4: User Story 2 - Trust Mapping Coverage (Priority: P2)

**Goal**: Show truthful mapping/evidence states without proxy substitution.

**Independent Test**: Render valid mappings with insufficient/unavailable history plus unmapped and
invalid mappings; verify their different states, retained identity where mapped, and zero price
requests for unmapped/invalid rows.

### Tests for User Story 2

- [ ] T008 [P] [US2] Extend `tests/unit/test_industry_momentum.py` and `tests/integration/test_stock_evidence.py` for the no-substitution contract: unmapped/invalid rows make no ETF history request; mapped bad-history rows retain the ETF identity and distinguish unavailable from insufficient evidence.
- [ ] T009 [P] [US2] Extend `tests/app/test_sector_stock_explorer.py` to verify `not_covered` and `invalid_mapping` messages are visible and no sector, parent, broad-market, stock-member, or arbitrary ETF momentum is displayed.

### Implementation for User Story 2

- [ ] T010 [US2] Add explicit mapping/evidence state projection in `src/market_leadership/domain/industry_momentum.py` and render those states in `src/market_leadership/ui/components/progressive_tape.py` without fabricating a momentum value or ETF substitute.

**Checkpoint**: Every reviewed hierarchy row remains visible and clearly distinguishes no mapping,
invalid mapping, unavailable evidence, and insufficient evidence.

## Phase 5: Polish & Cross-Cutting Validation

- [ ] T011 Run the focused commands in `specs/007-industry-etf-momentum/quickstart.md`, then run `git diff --check`; confirm existing stock-member discovery, contained-stock charts, and scoring are unchanged.

## Dependencies & Execution Order

### Phase Dependencies

- T001 and T002 may start in parallel.
- T003 depends on T001.
- T004 and T005 may start after T003; T006 depends on T003 and T004; T007 depends on T005 and T006.
- T008 and T009 may start after T007; T010 depends on T008 and T009.
- T011 follows T010.

### User Story Dependencies

- **US1 (P1)**: Requires the foundational reviewed mapping catalog and is the MVP.
- **US2 (P2)**: Uses the finalized US1 mapping resolution/projection but adds independently
  verifiable truthful-state behavior.

### Parallel Opportunities

- T001 and T002 use separate domain-test files and may run in parallel.
- T004 and T005 use unit/AppTest targets and may run in parallel.
- T008 and T009 use integration/unit and AppTest targets and may run in parallel.

## Parallel Examples

```text
Task: T001 Create mapping validation tests in tests/unit/test_industry_etf_mappings.py
Task: T002 Create ETF momentum state tests in tests/unit/test_industry_momentum.py
```

```text
Task: T008 Add no-substitution evidence tests in tests/integration/test_stock_evidence.py
Task: T009 Add coverage-state AppTest in tests/app/test_sector_stock_explorer.py
```

## Implementation Strategy

### MVP First

1. Complete T001-T003 to establish reviewed mapping validity.
2. Complete T004-T007 to render exact mapped ETF momentum.
3. Validate parent/sub-industry ETF identity and as-of behavior.

### Incremental Delivery

1. Deliver exact ETF identity and momentum for approved mapped rows.
2. Add explicit no-coverage, invalid, unavailable, and insufficient evidence states.
3. Run focused regression validation to demonstrate existing stock-member discovery remains intact.

## Notes

- Do not infer ETF mappings from names or add automatic discovery.
- Do not use a parent, sector, broad-market, stock-member, single-stock, or arbitrary ETF as a
  fallback.
- Do not alter the existing stock-member contained-stock, chart, CAP Type, or Total Score behavior.
