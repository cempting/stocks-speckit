# Tasks: Daily Sector and Industry Performance

**Prerequisites**: [spec](spec.md), [plan](plan.md), [data model](data-model.md),
[research](research.md), [UI contract](contracts/daily-performance-ui.md), [quickstart](quickstart.md).

Checked tasks are historical verified outcomes, not acceptance of later requirements.
All existing IDs and completion states are retained; descriptions are consolidated.
T007's separate representation helper and original T011/T015 wiring were superseded by T024.
The data model owns calculation invariants; the UI contract owns display/layout rules.
Constitution 4.1.0 requires failing regressions before fixes and desktop/phone browser evidence.

`[P]` permits parallel work only after prerequisites and in separate files.
Paths below are repository-root-relative. No new tooling, sources, tabs, ranking options or daily thumbnails.

## Phase 1 - Authority

- [X] T001 Reconcile 004/015 specifications, plans, UI contracts and `specs/README.md` for daily six-return/nine-field entity tapes while preserving stock, identity, loading and historical evidence.

## Phase 2 - Daily Foundation

### Tests first

- [X] T002 [P] Test requested-date official session adjacency, weekends/holidays/early close, incomplete sessions, historical dates and future/naive-clock rejection in `tests/integration/test_build_snapshot.py`; prices/observed dates never move endpoints.
- [X] T003 [P] Test fractional gain/loss/zero, exact missing/invalid endpoints, duplicate dates, malformed intervals and unchanged legacy arithmetic/SMA in `tests/unit/domain/test_sector_performance.py`.
- [X] T004 [P] Test approved ETF/basket daily returns, approval/activity errors, exact 100% weights and missing constituent evidence in `tests/unit/test_industry_representations.py`; no dropping or substitution.

### Implementation

- [X] T005 [P] Resolve typed requested-date daily session pairs in `src/market_leadership/application/market_sessions.py` via `src/market_leadership/application/exchange_calendar.py`; preserve clock/future-date errors.
- [X] T006 [P] Implement pure exact-endpoint `calculate_daily_return` in `packages/market-data/src/market_data/domain/sector_performance.py`, retaining contextual errors and five-period defaults.
- [X] T007 Implement the original separate representation daily helper in `packages/market-data/src/market_data/domain/industry_representations.py` with approved ETF/basket invariants. Later consolidated by T024.

## Phase 3 - US1: Sector Performance

### Tests first

- [X] T008 [P] [US1] Test sector gain/loss/zero, reviewed/symbol-only paths, daily-only/longer-only history, unavailable rows and Absolute without benchmark in `tests/app/test_sector_stock_explorer.py`; preserve order/metadata.
- [X] T009 [P] [US1] Test independent daily palettes, zero/unavailable styling, both themes and legacy frames in `tests/unit/ui/test_performance_table.py`.
- [X] T010 [P] [US1] Test literal nine-field headings, six returns/24 fixture cells, percentages, unavailable styling, charts, labels, hidden metadata, callbacks and unchanged stock projection in `tests/unit/ui/test_progressive_tape.py`.

### Implementation

- [X] T011 [P] [US1] Project sector daily evidence into nullable `1 day` cells in `src/market_leadership/ui/workflows/discovery_page.py`; convert units once, retain valid other horizons/freshness and avoid extra loads. Original helper wiring superseded by T024.
- [X] T012 [P] [US1] Recognize `1 day` in `src/market_leadership/ui/performance_table.py` and reuse `src/market_leadership/ui/components/progressive_tape.py`; preserve legacy-frame styling, charts and stock columns.

## Phase 4 - US2: Industry Momentum

### Tests first

- [X] T013 [P] [US2] Test industry ETF -1%, basket +0.5%, own-row evidence, unavailable rows, horizon order and navigation/thumbnail invariance in `tests/app/test_sector_stock_explorer.py`.
- [X] T014 [P] [US2] Test deterministic approved ETF/basket endpoints, missing-member rejection, provenance/effectivity and preserved legacy outcomes in `tests/integration/test_industry_representations.py`.

### Implementation

- [X] T015 [US2] Reuse the shared industry daily path in `src/market_leadership/ui/workflows/discovery_page.py`, preserving representation/date/freshness and dependent selections. Original helper wiring superseded by T024.

## Phase 5 - US3: Basis and Evidence

### Tests first

- [X] T016 [P] [US3] Test both bases/tables, exact relative intervals, no fallback, stale older pairs and independent short/long availability in `tests/app/test_sector_stock_explorer.py`.
- [X] T017 [P] [US3] Test uncolored unavailable cells and contextual `1d:` failures distinct from neutral zero in `tests/unit/ui/test_progressive_tape.py`; preserve source/status/freshness.
- [X] T018 [P] [US3] Test frozen-clock/date exclusion, request spies, basis/thumbnail/navigation invariance and stock safeguards in `tests/app/test_discovery.py`.

### Implementation

- [X] T019 [US3] Complete matching benchmark subtraction and contextual per-period failures in `src/market_leadership/ui/workflows/discovery_page.py`; preserve valid returns, status and source disclosures.

## Phase 6 - Historical Validation

- [X] T020 Run focused non-live pytest, Ruff and strict Pyright using `specs/016-add-daily-performance/quickstart.md`; fix only coupled regressions.
- [X] T021 Validate both entity tables at actual 640/1440 CSS pixels in both themes: daily/weekly adjacency, stacked fitting strip, wide layout, colors, 84px charts, navigation and stock projection.
- [X] T022 Record measured automated/browser results and unresolved gaps in `specs/016-add-daily-performance/quickstart.md`, `specs/016-add-daily-performance/plan.md` and `specs/README.md`; do not infer untested success.

## Phase 7 - Unified Representation API

- [X] T023 Add failing six-period/independent-availability API and workflow tests in `tests/unit/test_industry_representations.py`, `tests/unit/domain/test_sector_performance.py` and `tests/app/test_sector_stock_explorer.py`.
- [X] T024 Consolidate daily results into `representation_performance` in `packages/market-data/src/market_data/domain/industry_representations.py`; extend the shared calculator, migrate callers, preserve five-period ranking/snapshots and independent date-context activity.
- [X] T025 Reconcile API shape, migration, independent availability and observed evidence across `specs/016-add-daily-performance/{spec,plan,research,data-model,quickstart}.md` and `specs/016-add-daily-performance/contracts/daily-performance-ui.md`.

## Phase 8 - Current Documentation and Acceptance

- [X] T026 Reconcile 016 artifacts and `specs/README.md` with constitution 4.1.0: two-row header, unwrapped local 390px scrolling, complete non-hover details and six width/theme cases. Preserve prior task IDs, states and evidence; later approved consolidation may shorten descriptions.
- [ ] T027 Add failing phone/header/detail regressions in `tests/app/test_market_selection.py`, `tests/app/test_discovery.py`, `tests/app/test_sector_stock_explorer.py` and `tests/unit/ui/test_progressive_tape.py`; test unwrapped local scrolling, full text, preserved layouts/state and zero added requests. Depends on T026 and T030.
- [ ] T028 Satisfy T027 with scoped native header/scroll/detail fixes in `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/components/progressive_tape.py`; preserve 640/1440px layouts, 84px charts, formatting, keys/callbacks and stock safeguards. Depends on T027.
- [ ] T029 Run focused pytest, Ruff and strict Pyright, then all six browser width/theme cases from `specs/016-add-daily-performance/quickstart.md` with actual touch/keyboard input. Verify captions, scroll cues, charts, full details, controls/navigation/state/requests and stock preservation; record dimensions/input/results/gaps and update artifact status only after acceptance passes. Depends on T028 and T030.
- [ ] T030 Add failing literal `1 year` entity-header/backing-frame and legacy-formatting regressions in `tests/unit/ui/test_performance_table.py`, `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_sector_stock_explorer.py`; then migrate the entity caption in `src/market_leadership/ui/performance_table.py` and `src/market_leadership/ui/workflows/discovery_page.py`. Preserve internal `12m`, arithmetic, legacy-frame formatting and ranking/snapshot outputs. Depends on T025 and T026; execute before T027.

## Dependencies

Historical ordering (IDs reflect creation, not a new execution plan):

- T001 -> T002/T003/T004. T005 requires T002; T006 requires T003; T007 requires T004 and T006.
- Foundation -> T008/T009/T010 -> T011/T012 -> T013/T014 -> T015 -> T016/T017/T018 -> T019.
- T023 follows the daily foundation; T024 requires T023 and replaces the original representation wiring.
  T025 requires T024 and passing automated gates.
- Final historical validation: T019 and T024 -> T020 -> T021 -> T022.
- Current sequence: T025/T026 -> **T030 -> T027 -> T028 -> T029**.
  These pending tasks share files and must not run in parallel.

Only `[P]` test batches or distinct-file implementations may run together after these prerequisites.
Neither completed documentation nor historical DOM/hover checks establish phone/touch acceptance.

## Requirement Coverage

| Requirement | Delivering or verifying tasks |
|---|---|
| FR-001 | T008, T010-T015, T021, T023-T025 |
| FR-002 | T003, T008, T010-T016, T020, T023-T025, T030 |
| FR-003 | T002-T007, T011, T014-T016, T018-T020, T023-T025 |
| FR-004 | T016, T018-T020, T024-T025 |
| FR-005 | T009-T012, T017, T021, T030 |
| FR-006 | T003-T004, T008-T011, T014-T019, T023-T029 |
| FR-007 | T004, T007, T011, T013-T019, T023-T025 |
| FR-008 | T001, T008, T010-T015, T018-T021, T024-T030 |
| FR-009 | T008, T010-T013, T017, T021, T026-T029 |
| FR-010 | T026-T029 |
| FR-011 | T026-T029 |
| SC-001 | T008, T010, T013, T017, T021, T023-T030 |
| SC-002 | T002-T008, T013-T016, T018-T020, T023-T025 |
| SC-003 | T003-T004, T014, T016-T020, T023-T025 |
| SC-004 | T003, T008, T010, T013-T014, T018, T020-T025, T030 |
| SC-005 | T008, T010, T013, T021-T022 |
| SC-006 | T026-T029 |
| SC-007 | T026-T029 |
