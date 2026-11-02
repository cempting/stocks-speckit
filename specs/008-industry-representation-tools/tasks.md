# Tasks: Industry Representation Tools

> Consolidation notice (2026-11-02): [008](spec.md) owns former 007's ETF momentum/evidence.
> Reconcile unfinished work with the active scope and 010/012 publication/migration boundaries.
> Preserve task IDs/completion markers and prior tests; this merge is not a new implementation.

## Phase 1: Setup

No dependency or configuration changes are required.

## Phase 2: Foundational

- [X] T001 [P] Add database/model tests for reviewed representation status, effective dates, source approval, verified listings, and the constraint that basket weights total exactly 100% in `tests/unit/test_industry_representations.py`.
- [X] T002 [P] Add basket momentum and no-substitution tests in `tests/unit/test_industry_momentum.py` for active ETF, active basket, invalid basket, and not-covered states.
- [X] T003 Extend reviewed schema and accessors for basket alternatives and constituents in `src/market_leadership/infrastructure/region_database.py`, requiring positive weights, verified active listings, source/approval evidence, and a 100% total.

## Phase 3: User Story 1 - Review Industry Representations (P1)

**Goal**: Reviewers can find unrepresented classifications and approve auditable ETF mappings.

**Independent Test**: A test hierarchy produces a complete worklist; approving an ETF removes the
item and makes that ETF the active representation.

- [X] T004 [P] [US1] Add worklist and approved-ETF CLI tests in `tests/integration/test_industry_representations.py` and `tests/unit/test_universe_admin.py`.
- [X] T005 [US1] Implement worklist queries and reviewed ETF representation operations in `src/market_leadership/infrastructure/region_database.py` and `src/market_leadership/application/industry_representations.py`.
- [X] T006 [US1] Add review worklist and ETF approval commands in `src/market_leadership/universe_admin.py`.

## Phase 4: User Story 2 - Use Reviewed Stock-Basket Alternatives (P2)

**Goal**: Reviewers can approve a truthful basket only where no active ETF exists.

**Independent Test**: An ETF-less classification with verified constituents and weights totaling
100% renders as a stock-basket alternative; bad weights or missing evidence do not render momentum.

- [X] T007 [P] [US2] Add basket approval, effective-date, verified-constituent, exact-100%-weight, and no-active-ETF prerequisite tests in `tests/integration/test_industry_representations.py`.
- [X] T008 [P] [US2] Add ETF/basket/not-covered display and momentum-source AppTest coverage in `tests/app/test_sector_stock_explorer.py`.
- [X] T009 [US2] Implement basket administration commands and validation in `src/market_leadership/universe_admin.py` and `src/market_leadership/infrastructure/region_database.py`.
- [X] T010 [US2] Implement active ETF-or-basket resolution and weighted basket momentum in `src/market_leadership/domain/industry_representations.py`, `src/market_leadership/application/discover_sectors.py`, and `src/market_leadership/ui/workflows/discovery_page.py`.

## Phase 5: Polish & Validation

- [X] T011 Run the commands in `specs/008-industry-representation-tools/quickstart.md`, then `git diff --check`; confirm no inactive, invalid, or unreviewed representation produces momentum.

## Dependencies

- T001 and T002 may run in parallel; T003 follows them.
- US1: T004 → T005 → T006.
- US2: T007/T008 may run in parallel after T003; T009 → T010.
- T011 follows both stories.

## Parallel Examples

```text
T001 tests database representation invariants
T002 tests momentum state resolution
```

```text
T007 tests basket approval invariants
T008 tests user-visible representation states
```

## Implementation Strategy

Deliver the reviewed ETF worklist first, then add the basket fallback. Never infer mappings,
substitute a parent/sector ETF, or calculate momentum for invalid/inactive evidence.
