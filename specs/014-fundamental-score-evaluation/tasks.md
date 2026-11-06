---
description: "Implementation tasks for Fundamental Score Evaluation"
---

# Tasks: Fundamental Score Evaluation

**Input**: Design documents from `specs/014-fundamental-score-evaluation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/score-presentation.md`, `quickstart.md`

**Tests**: Required by the feature's reproducible evaluation requirements and the project test-first workflow.

**Organization**: Tasks are grouped by the three P1 user stories. No new project setup or shared infrastructure is needed.

## Phase 1: Setup

**Purpose**: Reuse the existing Python 3.12 workspace, `uv`, pytest, Ruff, and Pyright configuration. No setup tasks are required.

## Phase 2: Foundational

**Purpose**: The existing scoring domain, explicit evidence loading, and stock-detail surfaces provide the required foundation. No blocking infrastructure tasks are required.

## Phase 3: User Story 1 - Evaluate Score Methodology (Priority: P1)

**Goal**: Verify the current six metric calculations, peer rules, component combination, and evidence limitations without changing user-visible scoring rules.

**Independent Test**: Apply the current rules to controlled positive, zero, negative, missing, stale, extreme, and incomparable facts; verify exact metric values, percentiles, component/total states, and explanations.

### Tests for User Story 1

- [ ] T001 [P] [US1] Extend controlled calculation and edge-case coverage in `tests/unit/domain/test_peer_scores.py` for all six metrics, zero/negative cash flow, missing or invalid facts, ties, extreme values, minimum peer counts, and cutoff/period/currency comparability; assert no missing-value zero fill or partial component average.

### Implementation for User Story 1

- [ ] T002 [US1] Record the verified case outcomes, retained formula baseline, remaining limitations, and rationale for any proposed change in `specs/014-fundamental-score-evaluation/research.md` without changing score definitions, directions, eligibility, thresholds, or weights.

## Phase 4: User Story 2 - Interpret Stock-List Scores (Priority: P1)

**Goal**: Keep the stock-list Total Score consistent with its component scorecard, expose the underlying six peer metrics and known context, and preserve explicit non-numeric states.

**Independent Test**: Score controlled stocks for one fixed cohort and cutoff; compare list totals and states with the scorecard, inspect each metric's raw value and peer context in stock detail, and verify incomplete/error cases remain explicit.

### Tests for User Story 2

- [ ] T003 [P] [US2] Add application-level regression cases in `tests/app/test_score_industry.py` proving that a valid three-component scorecard produces application state `available`, a genuinely incomplete scorecard remains `insufficient`, and a loader failure remains `error`.
- [ ] T004 [US2] Extend `tests/unit/domain/test_peer_scores.py` to verify that each metric result preserves its verified source, publication availability, current/prior period bounds, currency, and cutoff context, while unknown provenance remains unavailable rather than inferred.
- [ ] T005 [P] [US2] Extend `tests/app/test_stock_detail.py` to assert that stock detail shows all six peer metric values, percentiles, valid-peer counts, states/reasons, and known provenance without initiating another score or financial-data load.
- [ ] T006 [P] [US2] Extend `tests/unit/ui/test_progressive_tape.py` to assert that three available components produce their equal mean to one decimal and that Not loaded, Insufficient, Unavailable, and Error remain non-numeric.

### Implementation for User Story 2

- [ ] T007 [P] [US2] Derive each `StockScoreEvidence.state` and reason from its actual result in `src/market_leadership/application/score_industry.py`: preserve loader errors, mark fully available scorecards available, and mark only incomplete scorecards insufficient.
- [ ] T008 [P] [US2] Carry only verified metric provenance from `PeerFacts` into score results in `packages/market-data/src/market_data/domain/peer_scores.py`, `packages/market-data/src/market_data/domain/fundamentals.py`, and `src/market_leadership/infrastructure/yfinance_fundamentals.py`; retain the existing yfinance evidence gate and leave unavailable publication dates or periods explicit.
- [ ] T009 [US2] Render the six metric results and their known peer/source/period/currency/cutoff context through the existing detail flow in `src/market_leadership/ui/components/stock_detail.py` and `src/market_leadership/ui/workflows/discovery_page.py`, without adding stock-list columns or hidden loads.

## Phase 5: User Story 3 - Recognize Cash-Flow and Evidence Risk (Priority: P1)

**Goal**: Keep unassessed cash flow distinct from reported zero, positive, and negative values, and make cash-generation concerns visible without treating them as proof of insolvency.

**Independent Test**: Display controlled stocks with unloaded, missing, zero, positive, and negative OCF/FCF alongside favorable and unfavorable Quality/Growth scores; verify the values, warnings, periods, and aggregate states remain distinct.

### Tests for User Story 3

- [ ] T010 [P] [US3] Extend `tests/unit/domain/test_peer_scores.py` with controlled zero and negative current cash-flow cases that remain numeric observations, alongside missing or invalid cases that remain unavailable/insufficient and do not alter component weights.
- [ ] T011 [P] [US3] Extend `tests/app/test_stock_detail.py` to verify that unloaded/missing cash flow differs from reported zero or negative OCF/FCF, that actual amounts, definitions, and periods remain visible, and that negative FCF is not described as insolvency even when other components are favorable.

### Implementation for User Story 3

- [ ] T012 [US3] Add a prominent cash-flow risk disclosure in `src/market_leadership/ui/components/stock_detail.py` using the existing score and `CompanyEvidenceLoadResult` surfaces: distinguish not assessed/unavailable from reported zero/positive/negative values, retain actual amount/definition/period/provenance, and describe negative FCF only as a cash-generation concern without adding a provider request.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Keep the focused validation guide aligned with the implementation and run the prescribed quality gates.

- [ ] T013 [P] Update `specs/014-fundamental-score-evaluation/quickstart.md` to include `tests/app/test_score_industry.py` in the focused pytest command and retain the expected state, provenance, and cash-flow scenarios.
- [ ] T014 Validate the focused pytest, Ruff, Pyright, and non-live test commands documented in `specs/014-fundamental-score-evaluation/quickstart.md`; resolve failures caused by this feature before completion.

## Dependencies

```text
T001 -> T002
T003 -> T007
T004 -> T008
T005 + T007 + T008 -> T009
T011 + T009 -> T012
T010 + T011 + T012 -> T013 -> T014
```

User Story 1 and User Story 2 have no cross-story dependency: methodology evaluation and score-state/detail work can proceed independently. User Story 3 builds on the detail evidence surface completed in User Story 2.

## Parallel Execution Examples

- Run T001 with T003, T005, and T006: they target separate test modules and cover independent requirements. T004 shares `tests/unit/domain/test_peer_scores.py` with T001 and should follow it.
- After their tests pass, run T007 and T008 in parallel; the state producer and domain provenance changes have separate owners/files.
- Run T010 and T011 in parallel; they cover separate domain and application test modules.

## Implementation Strategy

1. **MVP - User Story 1**: Establish deterministic coverage and record the methodology findings while retaining the existing scoring rules.
2. **User Story 2**: Correct state propagation, preserve verified metric context, and make the scorecard explainable from the existing detail surface.
3. **User Story 3**: Add cash-flow risk disclosure using existing evidence, preserving explicit-load behavior and distinguishing gaps from reported values.
4. **Final validation**: Run the focused quickstart suite, then Ruff, Pyright, and the non-live test suite.
