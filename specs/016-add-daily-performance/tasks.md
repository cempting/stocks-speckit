# Tasks: Daily Sector and Industry Performance

**Prerequisites**: [spec](spec.md), [plan](plan.md), [data model](data-model.md),
[research](research.md), [UI contract](contracts/daily-performance-ui.md), [quickstart](quickstart.md).

Checked tasks are historical verified outcomes, not acceptance of later requirements.
All existing IDs and completion states are retained. T031-T034 add the clarified heading/control
work; T035 adds contrast coverage for the updated palette requirement. None of the pending work
is marked complete by task generation.
T007's separate representation helper and original T011/T015 wiring were superseded by T024.
The data model owns calculation invariants; the UI contract owns display/layout rules.
Constitution 4.1.0 requires failing regressions before fixes and desktop/phone browser evidence.

`[P]` permits parallel work only after prerequisites and in separate files.
Paths below are repository-root-relative. No new tooling, sources, tabs, ranking options or daily thumbnails.
Tests are required by the accepted spec/plan and constitution: demonstrate failing regressions
before their source fixes. Pending execution order is defined by dependencies, not historical
ID placement. All new tasks use the existing modules, fixtures and validation tools.

## Phase 1 - Setup and Authority

Reuse the already initialized workspace and accepted design artifacts; no new scaffolding,
dependency installation or service is required.

- [X] T001 Reconcile 004/015 specifications, plans, UI contracts and `specs/README.md` for daily six-return/nine-field entity tapes while preserving stock, identity, loading and historical evidence.

## Phase 2 - Daily Foundation

**Goal**: Supply verified completed-session dates and domain arithmetic before either entity story.

### Tests first

- [X] T002 [P] Test requested-date official session adjacency, weekends/holidays/early close, incomplete sessions, historical dates and future/naive-clock rejection in `tests/integration/test_build_snapshot.py`; prices/observed dates never move endpoints.
- [X] T003 [P] Test fractional gain/loss/zero, exact missing/invalid endpoints, duplicate dates, malformed intervals and unchanged legacy arithmetic/SMA in `tests/unit/domain/test_sector_performance.py`.
- [X] T004 [P] Test approved ETF/basket daily returns, approval/activity errors, exact 100% weights and missing constituent evidence in `tests/unit/test_industry_representations.py`; no dropping or substitution.

### Implementation

- [X] T005 [P] Resolve typed requested-date daily session pairs in `src/market_leadership/application/market_sessions.py` via `src/market_leadership/application/exchange_calendar.py`; preserve clock/future-date errors.
- [X] T006 [P] Implement pure exact-endpoint `calculate_daily_return` in `packages/market-data/src/market_data/domain/sector_performance.py`, retaining contextual errors and five-period defaults.
- [X] T007 Implement the original separate representation daily helper in `packages/market-data/src/market_data/domain/industry_representations.py` with approved ETF/basket invariants. Later consolidated by T024.

## Phase 3 - US1: Sector Performance

**Priority**: P1. **Goal**: Compare exact daily sector returns with five independently available
longer horizons, preserving the current evidence and navigation context.
**Independent test**: With controlled prices, sector 100/102 shows `2.00%`; unavailable rows
retain the six captions. At 390/640px the heading stays beside stacked controls; at 641/1440px
desktop controls remain, with both themes and no stock/data-loading changes.

### Tests first

- [X] T008 [P] [US1] Test sector gain/loss/zero, reviewed/symbol-only paths, daily-only/longer-only history, unavailable rows and Absolute without benchmark in `tests/app/test_sector_stock_explorer.py`; preserve order/metadata.
- [X] T009 [P] [US1] Test independent daily palettes, zero/unavailable styling, both themes and legacy frames in `tests/unit/ui/test_performance_table.py`.
- [X] T010 [P] [US1] Test literal nine-field headings, six returns/24 fixture cells, percentages, unavailable styling, charts, labels, hidden metadata, callbacks and unchanged stock projection in `tests/unit/ui/test_progressive_tape.py`.

### Implementation

- [X] T011 [P] [US1] Project sector daily evidence into nullable `1 day` cells in `src/market_leadership/ui/workflows/discovery_page.py`; convert units once, retain valid other horizons/freshness and avoid extra loads. Original helper wiring superseded by T024.
- [X] T012 [P] [US1] Recognize `1 day` in `src/market_leadership/ui/performance_table.py` and reuse `src/market_leadership/ui/components/progressive_tape.py`; preserve legacy-frame styling, charts and stock columns.
- [X] T035 [P] [US1] Extend `tests/unit/ui/test_performance_table.py` to check every gain/loss/neutral return-text foreground/background pair generated in both themes, including intermediate ramp colors, against WCAG AA contrast of at least 4.5:1 for normal text and 3:1 for large text; verify signed values and zero remain distinguishable without color. If a pair fails, adjust the existing palette in `src/market_leadership/ui/performance_table.py` without changing the visual mapping unnecessarily. Verified both themes; no palette changes were needed.

## Phase 4 - US2: Industry Momentum

**Priority**: P1. **Goal**: Apply the same horizons/layout to each industry's approved evidence.
**Independent test**: ETF 200/198 shows `-1.00%`, a 50/50 +2%/-1% basket shows `0.50%`,
and industry heading/control placement passes the same four widths in both themes.

### Tests first

- [X] T013 [P] [US2] Test industry ETF -1%, basket +0.5%, own-row evidence, unavailable rows, horizon order and navigation/thumbnail invariance in `tests/app/test_sector_stock_explorer.py`.
- [X] T014 [P] [US2] Test deterministic approved ETF/basket endpoints, missing-member rejection, provenance/effectivity and preserved legacy outcomes in `tests/integration/test_industry_representations.py`.

### Implementation

- [X] T015 [US2] Reuse the shared industry daily path in `src/market_leadership/ui/workflows/discovery_page.py`, preserving representation/date/freshness and dependent selections. Original helper wiring superseded by T024.

## Phase 5 - US3: Basis and Evidence

**Priority**: P2. **Goal**: Keep basis, evidence explanations and valid selections trustworthy
through control changes, resizing and navigation.
**Independent test**: Entity +2% minus benchmark +0.5% shows `1.50%`; missing matching endpoints
show uncolored `Unavailable`. Touch/keyboard access, resizing and detail actions preserve valid
state and the existing request baseline; thumbnails change charts, not returns.

### Tests first

- [X] T016 [P] [US3] Test both bases/tables, exact relative intervals, no fallback, stale older pairs and independent short/long availability in `tests/app/test_sector_stock_explorer.py`.
- [X] T017 [P] [US3] Test uncolored unavailable cells and contextual `1d:` failures distinct from neutral zero in `tests/unit/ui/test_progressive_tape.py`; preserve source/status/freshness.
- [X] T018 [P] [US3] Test frozen-clock/date exclusion, request spies, basis/thumbnail/navigation invariance and stock safeguards in `tests/app/test_discovery.py`.

### Implementation

- [X] T019 [US3] Complete matching benchmark subtraction and contextual per-period failures in `src/market_leadership/ui/workflows/discovery_page.py`; preserve valid returns, status and source disclosures.

## Phase 6 - Historical Validation

- [X] T020 Run focused non-live pytest, Ruff and strict Pyright using `specs/016-add-daily-performance/quickstart.md`; fix only coupled regressions.
- [X] T021 Validate both entity tables rendered by `src/market_leadership/ui/workflows/discovery_page.py` at actual 640/1440 CSS pixels in both themes: daily/weekly adjacency, stacked fitting strip, wide layout, colors, 84px charts, navigation and stock projection.
- [X] T022 Record measured automated/browser results and unresolved gaps in `specs/016-add-daily-performance/quickstart.md`, `specs/016-add-daily-performance/plan.md` and `specs/README.md`; do not infer untested success.

## Phase 7 - Unified Representation API

- [X] T023 Add failing six-period/independent-availability API and workflow tests in `tests/unit/test_industry_representations.py`, `tests/unit/domain/test_sector_performance.py` and `tests/app/test_sector_stock_explorer.py`.
- [X] T024 Consolidate daily results into `representation_performance` in `packages/market-data/src/market_data/domain/industry_representations.py`; extend the shared calculator, migrate callers, preserve five-period ranking/snapshots and independent date-context activity.
- [X] T025 Reconcile API shape, migration, independent availability and observed evidence across `specs/016-add-daily-performance/{spec,plan,research,data-model,quickstart}.md` and `specs/016-add-daily-performance/contracts/daily-performance-ui.md`.

## Phase 8 - Current Shared Prerequisites

- [X] T026 Reconcile 016 artifacts and `specs/README.md` with constitution 4.1.0: two-row header, unwrapped local 390px scrolling, complete non-hover details and six width/theme cases. Preserve prior task IDs, states and evidence; later approved consolidation may shorten descriptions.
- [X] T027 Add failing phone/header/detail regressions in `tests/app/test_market_selection.py`, `tests/app/test_discovery.py`, `tests/app/test_sector_stock_explorer.py` and `tests/unit/ui/test_progressive_tape.py`; test unwrapped local scrolling, full text, preserved layouts/state and zero added requests. Depends on T026 and T030.
- [X] T028 Satisfy T027 with scoped native header/scroll/detail fixes in `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/components/progressive_tape.py`; preserve 640/1440px layouts, 84px charts, formatting, keys/callbacks and stock safeguards. Depends on T027.
- [X] T030 Add failing literal `1 year` entity-header/backing-frame and legacy-formatting regressions in `tests/unit/ui/test_performance_table.py`, `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_sector_stock_explorer.py`; then migrate the entity caption in `src/market_leadership/ui/performance_table.py` and `src/market_leadership/ui/workflows/discovery_page.py`. Preserve internal `12m`, arithmetic, legacy-frame formatting and ranking/snapshot outputs. Depends on T025 and T026; execute before T027.

## Phase 9 - US1: Heading/Control Layout (P1, Shared MVP)

**Goal**: Deliver Sector performance's clarified layout using one shared entity implementation.
**Independent test**: At actual 390/640px, heading left spans Thumbnail period upper right and
Performance basis lower right; at 641/1440px, retain the 2:2:2 desktop arrangement, both themes.
Controls remain complete and usable; the main header, table scrolling and stock stage are unchanged.

### Tests first

- [X] T031 [US1] Add failing FR-012/SC-008 regressions in `tests/app/test_market_selection.py`, `tests/app/test_sector_stock_explorer.py` and `tests/app/test_discovery.py`, parameterized for both entity headings and both themes. Check one native entity-only container, unchanged heading/period/basis order and 2:2:2 desktop weights, inclusive 640px scoped rules, absence of the wrapper in Contained stocks, empty/error-state preservation, defaults, navigation/state and request spies. Record the failing targeted command/output in `specs/016-add-daily-performance/quickstart.md`; CSS assertions are not browser acceptance. Depends on T028.
  - Quote and enforce the data-model invariants: heading "Remains left of both controls through 640px; may wrap, not disappear or truncate."; thumbnail "Same native widget/options/key; occupies the upper-right row in narrow layout."; basis "Same native widget/options/key; occupies the lower-right row in narrow layout."; layout "Presentation-only; never stored as user data or used to select market evidence."
  - Keep thumbnail options `1w`, `1m`, `3m`, `6m`, `1y` with default `3m`, and basis `Absolute`, `vs S&P 500` with default `Absolute`. Tests cover existing namespaced keys, empty-choice defaults, all choices, theme reruns, hierarchy/back navigation, and no acquisition added beyond the existing rerun baseline.

### Implementation

- [X] T032 [US1] Satisfy T031 in `src/market_leadership/ui/workflows/discovery_page.py`: reuse the existing heading/period/basis widgets inside one native keyed `entity_performance_controls` container at Sector performance and Industry momentum only. Reuse the scoped header-grid pattern at `max-width: 640px`: shrinkable columns, heading left spanning two rows, period upper right, basis lower right; allow internal wrapping without clipping/hiding options or moving controls below the heading. Above 640px retain existing 2:2:2 columns, keys/defaults/callbacks and data behavior; add no global styles, duplicate mobile widgets, viewport callbacks, persisted state or dependencies. Run the combined T031 selectors and record sector bounds/overflow/touch/keyboard evidence at 390/640/641/1440px in both themes in `specs/016-add-daily-performance/quickstart.md`. Depends on T031.

The shared implementation and pre-fix parameterization cover both headings; do not create
a second industry renderer or defer industry's test-first coverage until after T032.

## Phase 10 - US2: Industry Layout Acceptance (P1)

**Goal**: Verify the shared layout with industry-specific ETF, basket and unavailable evidence.
**Independent test**: Select a sector and verify Industry momentum at all four acceptance widths
in both themes, independently of sector returns and without changing membership/stock behavior.

- [X] T033 [US2] Verify the industry cases established by T031/T032 in `tests/app/test_sector_stock_explorer.py` and exercise Industry momentum using the controlled cases in `specs/016-add-daily-performance/quickstart.md`. At actual 390/640/641/1440px in both themes, measure heading/control placement, complete labels/options and zero page overflow; exercise ETF/basket/unavailable rows, industry/sub-industry selection, empty membership and stock/back navigation. Retain own-row returns, captions, charts, state and the entity-only wrapper scope; fix only coupled regressions in `src/market_leadership/ui/workflows/discovery_page.py` if the existing pre-fix tests expose them. Record dimensions/input/results/gaps in `specs/016-add-daily-performance/quickstart.md`. Depends on T032.

## Phase 11 - US3: Control and Evidence Preservation (P2)

**Goal**: Prove layout changes do not alter return semantics, selected context or acquisition.
**Independent test**: Touch/keyboard selects every option in both tables; resizing across
640/641px preserves selections/returns, basis changes retain matching benchmark semantics,
and details remain accessible without navigation or new fetches.

- [ ] T034 [US3] Run the control/state/request regressions added before implementation in `tests/app/test_discovery.py` and `tests/app/test_sector_stock_explorer.py`, then perform the interaction steps in `specs/016-add-daily-performance/quickstart.md` for both tables and themes. Exercise all five thumbnail choices, both bases, empty-choice defaults, theme reruns, hierarchy/back navigation, and resize across 640/641px; compare selections, returns, requested/observed dates and instrumented request counts. Viewport-only changes add zero requests; ordinary control changes retain the existing per-rerun baseline. At 390px, verify 84 CSS-pixel charts with unclipped plotted content, a visible table-local cue, and touch and keyboard scrolling to the final field without page overflow. Verify full-name/unavailable evidence by touch/keyboard and that main-header/stock controls remain outside the new scope. Record results/gaps in `specs/016-add-daily-performance/quickstart.md`; fix only regressions of the pre-fix tests in the affected UI files. Depends on T033.

## Phase 12 - Polish and Cross-Cutting Acceptance

- [ ] T029 Run the combined focused non-live pytest, Ruff and strict Pyright commands in `specs/016-add-daily-performance/quickstart.md`; include T035's automated contrast regression. Complete any missing checks from the six existing 390/640/1440px width/theme cases and eight heading/control 390/640/641/1440px cases with actual touch/keyboard input. Reuse measured T032-T034 evidence when it matches the final code, rather than repeating unchanged walkthroughs; rerun affected cases after fixes. Verify captions, WCAG AA return-text contrast in both themes, color-independent status, 390px scroll cues/charts, full details, controls/navigation/state/requests and stock preservation. Record commands/dimensions/input/results/gaps, reconcile status in `specs/016-add-daily-performance/{spec,plan,quickstart}.md`, `specs/016-add-daily-performance/contracts/daily-performance-ui.md` and `specs/README.md`, and mark tasks complete only after their own outcomes pass. Stop only owned helpers and remove only their known fixture files. Depends on T030, T028, T034 and T035.

## Dependencies and Execution Order

Historical ordering (IDs reflect creation, not a new execution plan):

- T001 -> T002/T003/T004. T005 requires T002; T006 requires T003; T007 requires T004 and T006.
- Foundation -> T008/T009/T010 -> T011/T012 -> T013/T014 -> T015 -> T016/T017/T018 -> T019.
- T023 follows the daily foundation; T024 requires T023 and replaces the original representation wiring.
  T025 requires T024 and passing automated gates.
- Final historical validation: T019 and T024 -> T020 -> T021 -> T022.
- Current sequence: T025/T026 -> **T030 -> T027 -> T028 -> T031 -> T032 -> T033 -> T034 -> T029**.
  T035 is an independent US1 regression in a distinct test file; complete it before T029.
  T034 and T035 may run in parallel after T033 if their UI-source edits remain separate.

Only `[P]` test batches or distinct-file implementations may run together after these prerequisites.
Neither completed documentation nor historical DOM/hover checks establish phone/touch acceptance.

User-story handoff:

```text
Completed foundation/API
    -> shared caption/phone prerequisites (T030, T027, T028)
    -> US1 shared test-first layout and sector acceptance (T031, T032)
    -> US2 industry acceptance (T033)
    -> US3 state/basis/evidence preservation (T034)
    -> final combined gates and evidence reconciliation (T029)
```

US2 uses the common implementation introduced under US1, not a new industry component.
US3 verifies the existing basis/evidence behavior after both entity layouts.
Historical IDs are retained rather than renumbered into this new execution order.

## Parallel Execution Examples

- **US1**: Historical T008 (workflow), T009 (palette) and T010 (renderer) are distinct-file
  test batches after foundation; they are already complete. T035's automated palette check is in
  a separate unit-test file and can run alongside T034's AppTests/browser acceptance after T033.
  T030/T031 share test files and T032 depends on failing regressions.
- **US2**: Historical T013 (workflow) and T014 (integration) could run together; they are
  complete. T033 depends on the shared T032 implementation and uses the same browser/context,
  so run it serially.
- **US3**: Historical T016, T017 and T018 use distinct test files after prerequisites; they
  are complete. T034 depends on industry acceptance and mutates shared widget state, so
  run it serially. Do not add tooling or duplicate browser sessions just to parallelize it.

## Implementation Strategy

1. Retain all completed work; finish shared caption/phone prerequisites in dependency order.
2. **MVP**: US1's T031/T032 delivers the clarified sector layout with shared industry wiring
   and pre-fix tests for both headings. Sector acceptance is a usable increment, not a claim
   that industry or cross-story acceptance has passed.
3. Verify US2 independently using its own ETF/basket/unavailable rows, then US3's control/state
   and evidence semantics. Reuse the native shared UI and existing data; no new domain model.
4. Run final combined quality gates and finish browser evidence once per final implementation.
   Never replace measured geometry/touch checks with AppTest/CSS assertions or historical results.

## Requirement Coverage

| Requirement | Delivering or verifying tasks |
|---|---|
| FR-001 | T008, T010-T015, T021, T023-T025 |
| FR-002 | T003, T008, T010-T016, T020, T023-T025, T030 |
| FR-003 | T002-T007, T011, T014-T016, T018-T020, T023-T025 |
| FR-004 | T016, T018-T020, T024-T025 |
| FR-005 | T009-T012, T017, T021, T030, T035 |
| FR-006 | T003-T004, T008-T011, T014-T019, T023-T029 |
| FR-007 | T004, T007, T011, T013-T019, T023-T025 |
| FR-008 | T001, T008, T010-T015, T018-T021, T024-T034 |
| FR-009 | T008, T010-T013, T017, T021, T026-T029, T034 |
| FR-010 | T026-T029, T031-T034 |
| FR-011 | T026-T029, T031-T034 |
| FR-012 | T031-T034, T029 |
| SC-001 | T008, T010, T013, T017, T021, T023-T030 |
| SC-002 | T002-T008, T013-T016, T018-T020, T023-T025 |
| SC-003 | T003-T004, T014, T016-T020, T023-T025 |
| SC-004 | T003, T008, T010, T013-T014, T018, T020-T025, T030 |
| SC-005 | T008, T010, T013, T021-T022 |
| SC-006 | T026-T029, T032-T034 |
| SC-007 | T026-T029, T034 |
| SC-008 | T031-T034, T029 |
| SC-009 | T035, T029 |
