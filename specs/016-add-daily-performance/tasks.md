# Tasks: Add Daily Performance

**Input**: Design documents in `specs/016-add-daily-performance/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [UI contract](contracts/daily-performance-ui.md), and
[quickstart.md](quickstart.md). Constitution 4.0.1 requires test-first implementation.

**Regenerated**: 2026-11-06 after the selected-date clarification and design reconciliation.
The daily session pair is determined from the requested as-of date and completion clock.
Price availability and stale observed dates must not move either endpoint; missing exact
closes produce `Unavailable`, never an older daily return.

**Working context**: Feature identifier `016-add-daily-performance`; actual working branch
`main`. These tasks do not create a branch. Preserve pre-existing worktree changes.

**Organization**: Three independently verifiable user stories, shared prerequisites, and
cross-cutting acceptance. Checked markers record verified implementation outcomes, not planning
or historical validation of other features.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies tasks that can run together at the documented dependency checkpoint.
  It does not waive prerequisites or permit simultaneous writes to the same file.
- `[US1]`, `[US2]`, and `[US3]` identify the specification's user stories.
- Paths in task descriptions are exact repository-root-relative paths.
- Tests precede corresponding source changes. Demonstrate the new behavior fails before
  implementing it; later regression assertions may already pass through shared earlier work.
- Use existing modules, fixtures, and tooling. No new dependency, provider, runtime fixture
  selector, data schema, ranking option, tab, or daily thumbnail period is authorized.

## Phase 1: Setup (Scope and Authority)

**Purpose**: Establish the additive presentation boundary before implementation; existing
application scaffolding and dependencies already exist.

- [X] T001 Verify and complete narrowly scoped 016 precedence notes in `specs/004-sector-stock-explorer/spec.md`, `specs/004-sector-stock-explorer/plan.md`, `specs/004-sector-stock-explorer/contracts/progressive-discovery.md`, `specs/015-dedicated-stock-lookup/spec.md`, `specs/015-dedicated-stock-lookup/plan.md`, `specs/015-dedicated-stock-lookup/contracts/stock-lookup-ui.md`, and `specs/README.md`: six returns/nine visible entity columns supersede only the five-return/eight-column baseline (004 FR-029/FR-031/FR-035 and 015 FR-014/SC-007); retain hidden ticker metadata, existing thumbnail options, stock columns, and historical completed task/validation evidence, leaving already-correct amendment notes intact.

**Checkpoint**: Accepted scope is consistent; no runtime functionality has been claimed.

## Phase 2: Foundational (Shared Daily Evidence)

**Purpose**: Provide exact completed-session dates and independent pure daily arithmetic for
both named tables. Complete this phase before story implementation.

### Tests First

- [X] T002 [P] Extend the completed-session tests in `tests/integration/test_build_snapshot.py` for an explicit requested-date daily session pair: normal sessions, weekends, holidays, early-close boundaries, historical requested dates, incomplete current sessions, and rejected future/naive-clock inputs; prove an older observed date or missing price does not move either endpoint, enforce "Start is strictly earlier than end; the application guarantees official session adjacency." and "Price availability and observed_as_of must not select or move either daily endpoint.", and verify existing snapshot session behavior is unchanged.
- [X] T003 [P] Add daily-helper tests in `tests/unit/domain/test_sector_performance.py` for fractional +0.02/-0.01/zero results, two-point history, missing exact endpoints despite older available closes, NaN/infinity/zero/negative endpoints, duplicate observation dates, and reversed/equal interval dates; enforce "Require both exact endpoint observations. An older available close must not fill a missing required session.", "Ignore future/incomplete-session data and unrelated old observations when evaluating daily endpoint validity.", and "Require unique observation dates and finite strictly positive endpoint prices."; assert existing five-period keys, values, error behavior, and SMA output remain unchanged.
- [X] T004 [P] Add approved daily ETF/basket tests in `tests/unit/test_industry_representations.py`: ETF endpoints 200/198 produce -0.01, an approved 50/50 basket of +0.02/-0.01 produces +0.005, and absent/unapproved/inactive/invalid representations or missing constituent endpoints fail explicitly; enforce "Existing approval/effectivity and exact 100% weight invariants remain required." and "Every basket constituent supplies both exact endpoints. No constituent dropping, inferred membership, weight renormalization, parent return, or fabricated traded-basket chart."

### Implementation

- [X] T005 [P] Add an explicit typed daily-session interval resolver beside `latest_completed_us_session` in `src/market_leadership/application/market_sessions.py`, using `latest_completed_us_session(requested_as_of, now=...)` for the ending session and the typed calendar in `src/market_leadership/application/exchange_calendar.py` for its `previous_session`; return `start_session`/`end_session` as date values, enforce "Latest completed official session on or before requested_as_of.", "Official session immediately before the ending session.", "Price availability and observed_as_of must not select or move either daily endpoint.", and "Domain helpers receive explicit dates, not clocks or calendar dependencies."; observed_as_of remains "Existing observation/freshness disclosure, never a daily endpoint selector.", not a resolver input; preserve existing callers and future-date/clock errors.
- [X] T006 [P] Implement `calculate_daily_return(closes, *, start_session, end_session) -> float` in `packages/market-data/src/market_data/domain/sector_performance.py`, returning `end / start - 1` and enforcing "Fractional entity return; 0.02 means 2%.", "Require both exact endpoint observations. An older available close must not fill a missing required session.", and "Require unique observation dates and finite strictly positive endpoint prices."; use existing `InsufficientHistoryError` for missing/invalid evidence and contextual `ValueError` for malformed dates/indexes, validate only relevant endpoint prices, and leave `PerformancePeriod`, `PerformanceResult`, five-period functions, and `with_sma50` unchanged.
- [X] T007 Implement `representation_daily_return` alongside `representation_performance` in `packages/market-data/src/market_data/domain/industry_representations.py`, receiving the explicit requested-date session pair and reusing existing representation validity/effectivity checks and T006; enforce "ETF: `ending_close / starting_close - 1` for its approved symbol.", "Basket: sum of approved weights divided by 100 times each constituent's daily return.", "Existing approval/effectivity and exact 100% weight invariants remain required.", "Validate the selected row's representation at requested_as_of; do not substitute an older representation when required daily evidence is missing.", and "Every basket constituent supplies both exact endpoints. No constituent dropping, inferred membership, weight renormalization, parent return, or fabricated traded-basket chart."; keep legacy representation calculations unchanged.

**Checkpoint**: Session and daily helpers pass their tests without broadening legacy return
types or introducing acquisition. T005 and T006 can run together after their tests; T007
requires T004 and T006.

## Phase 3: User Story 1 - Compare Daily Sector Performance (Priority: P1)

**Goal**: Sector performance presents the daily return before the five unchanged longer
periods, using existing percentage and gain/loss/neutral presentation.

**Independent Test**: Render Sector performance from controlled completed-session prices
without selecting an industry. Assert nine visible columns and literal horizon order,
`2.00%`, `-1.00%`, and `0.00%`, and unchanged longer-period values/chart behavior.

### Tests First

- [X] T008 [P] [US1] Add sector daily AppTest/frame regressions in `tests/app/test_sector_stock_explorer.py` for known gain/loss/zero, symbol-only and reviewed sector representation paths, daily-only short history, unavailable-only rows, and Absolute without benchmark history; assert literal `1d` insertion before `1 week`, existing backing metadata/order, and before/after equality of all five longer-period values and default row ordering.
- [X] T009 [P] [US1] Extend `tests/unit/ui/test_performance_table.py` with positive/negative/zero daily percentages in both themes, an independent daily gain/loss scale unaffected by weekly/monthly extrema, and absent daily values receiving no gain/loss style; retain tests for existing frames that omit `1d` and for the legacy industry frame.
- [X] T010 [P] [US1] Extend `tests/unit/ui/test_progressive_tape.py` to assert the literal nine visible entity headings in order, six formatted returns per row (24 cells for the existing four-row fixture), right-aligned two-decimal daily values, and uncolored `Unavailable`; preserve chart dimensions, full two-block entity labels, hidden Ticker/ETF/Node ID fields, selection callbacks/keys, and the five-column stock projection without deriving expected headings only from `PERFORMANCE_COLUMNS`.

### Implementation

- [X] T011 [P] [US1] Integrate sector daily evidence independently of legacy metrics in `_build_entity_tape` and the existing symbol path in `src/market_leadership/ui/workflows/discovery_page.py`, using T005's requested-date completed-session pair and T006/T007 for the row's approved representation; look up daily endpoints in loaded histories, not chart/legacy series cropped at observed_as_of, while retaining that existing crop for charts and longer periods; enforce "Add numeric nullable `1d` immediately before `1 week` in the existing backing frame.", "Convert fractional daily returns to percentage units once: `absolute_daily * 100`, or `(absolute_daily - benchmark_daily) * 100`.", and "Missing numeric values render as `Unavailable`, not a string stored in a numeric column."; retain independently valid daily-only/legacy-only results and freshness/status disclosures without extra data loads.
- [X] T012 [P] [US1] Prepend literal `1d` to `PERFORMANCE_COLUMNS` in `src/market_leadership/ui/performance_table.py` and reuse the existing recognized-column formatting/rendering in `src/market_leadership/ui/components/progressive_tape.py`; adjust the renderer only if required by T010, without new styling architecture, chart geometry changes, daily thumbnail options, stock columns, or changes to frames that contain only legacy periods.

**Checkpoint**: US1's Sector Absolute acceptance passes. T011 and T012 are separate-file
implementation work after T008-T010. Benchmark-relative and complete negative-evidence
acceptance remain release gates in US3; this checkpoint is not full feature completion.

## Phase 4: User Story 2 - Compare Daily Industry Momentum (Priority: P1)

**Goal**: Industry momentum uses each industry's own approved representation and keeps
daily returns independent of thumbnail periods and parent sector returns.

**Independent Test**: Select a sector with controlled industry evidence. An industry's
200/198 pair displays `-1.00%` even when its parent gains; a 50/50 approved basket displays
`0.50%`. Changing the thumbnail period does not change any return.

### Tests First

- [X] T013 [P] [US2] Add industry AppTest/frame cases in `tests/app/test_sector_stock_explorer.py` for literal nine-column order, approved ETF -1.00%, approved basket +0.50%, an industry return distinct from its parent, uncovered/unavailable rows, and stable `1d` across every existing thumbnail period and sector/industry navigation; compare all longer-period values and chart geometry with the same pre-change inputs.
- [X] T014 [P] [US2] Extend `tests/integration/test_industry_representations.py` with deterministic approved ETF/basket histories over the requested-date daily pair and assert no fallback to another instrument, parent, or older observed interval, no weight renormalization when a constituent endpoint is absent despite an older valid pair, and preserved approval/provenance/effectivity and legacy-period outcomes.

### Implementation

- [X] T015 [US2] Wire the industry reviewed-representation path in `_build_entity_tape` in `src/market_leadership/ui/workflows/discovery_page.py` to the shared independent daily calculation from T007/T011, rather than copying sector arithmetic or using the old standalone industry frame; preserve the row's source, representation/type, requested/observed dates, and freshness context, and enforce "Thumbnail period changes: alter chart cropping only; all six return values remain unchanged." and "Parent selection changes: follow existing dependent selection invalidation."

**Checkpoint**: Both named tables pass their Absolute daily acceptance. Shared work already
covering an industry path should be reused, not duplicated to satisfy a task marker.

## Phase 5: User Story 3 - Interpret Daily Returns Consistently (Priority: P2)

**Goal**: Both tables obey the selected basis and expose daily-specific failures without
fabricated values, skipped sessions, or loss of valid longer-period returns.

**Independent Test**: Exercise both tables under Absolute and vs S&P 500: entity +2% and
benchmark +0.5% over the same pair show `1.50%`; missing/invalid entity or required benchmark
endpoints show uncolored `Unavailable` with identifiable context. An older valid observed
pair never replaces missing requested-date evidence; valid longer returns and warnings remain.

### Tests First

- [X] T016 [P] [US3] Add parameterized basis/evidence regressions in `tests/app/test_sector_stock_explorer.py` for both tables: matched +2%/+0.5% gives 1.50%, mismatched/missing benchmark sessions have no Absolute fallback, Absolute works without benchmark evidence, daily failure preserves valid longer returns, and short valid daily history survives insufficient yearly history; exercise stale entity/benchmark histories with older valid pairs and enforce "Missing either required close makes the daily value unavailable; an older valid daily pair must not substitute for the requested-date interval.", "Relative: `absolute_daily - benchmark_daily`, only when both use identical session dates.", "Absolute mode does not require benchmark daily evidence.", and "Daily failure context is appended to the existing tooltip/context with a `1d:` prefix; it does not overwrite freshness or other evidence reasons."
- [X] T017 [P] [US3] Add unavailable-context renderer regressions in `tests/unit/ui/test_progressive_tape.py` for missing/non-finite/non-positive endpoints, missing representation, invalid basket and missing matching benchmark, checking an uncolored daily cell plus a `1d:` reason identifying relevant symbol/session or representation while retaining existing stale/uncovered status and source/observation disclosures; distinguish valid neutral `0.00%` from unavailable evidence.
- [X] T018 [P] [US3] Extend `tests/app/test_discovery.py` with frozen-clock requested-date/stale/incomplete/future-observation cases and request-spy checks across basis changes, all existing thumbnail periods, sector/industry/back navigation, and stock selection; enforce "Stale observation: keep the requested-date daily interval fixed and retain freshness disclosures. Existing chart/long-period observed-date cropping remains unchanged.", "Performance basis changes: recompute only the displayed projection; reuse histories and keep sector/industry selections.", and "Refresh/catalog changes: follow existing history and context lifecycle, not a daily-specific cache or persistence layer."; assert zero added provider/catalog requests, stable sorting/chart choices, and unchanged stock behavior.

### Implementation

- [X] T019 [US3] Complete matched-session benchmark-relative calculation and daily-specific expected-error handling in `src/market_leadership/ui/workflows/discovery_page.py`: resolve one requested-date pair and evaluation clock per table context, reuse its benchmark result across rows, compute entity minus benchmark then multiply by 100 once, and never require benchmark evidence in Absolute; enforce "Fractional benchmark return over the exact same interval.", "Actionable missing/invalid endpoint or representation explanation.", "Expected unavailable evidence raises the existing domain evidence exception and is converted to a missing cell plus visible reason only at the workflow boundary.", "Daily failure context is appended to the existing tooltip/context with a `1d:` prefix; it does not overwrite freshness or other evidence reasons.", and "Daily endpoint failure: mark only the daily value unavailable; retain valid legacy metrics."; catch only expected contextual evidence errors, never substitute an older daily interval, preserve existing failure notification/status behavior, and leave `_calculate_discovery` cache schema, request parameters, and selection keys unchanged.

**Checkpoint**: All three stories satisfy the complete UI contract under both bases; no
missing/invalid daily case is represented as zero, an alternate return, or a successful load.

## Phase 6: Polish & Cross-Cutting Acceptance

**Purpose**: Validate the actual output and unchanged behavior, then record observed evidence.

- [X] T020 Run the focused non-live pytest command and existing Ruff/strict Pyright gates in `specs/016-add-daily-performance/quickstart.md`, including its existing `tests/integration/test_build_snapshot.py` selectors for T002; fix only regressions caused by or tightly coupled to this feature in the changed source/test files, and expand selectors/full-suite coverage only for demonstrated coupling rather than installing or changing tooling.
- [ ] T021 Execute the browser walkthrough in `specs/016-add-daily-performance/quickstart.md` for Sector performance and Industry momentum in both themes at representative wide and narrow widths (1440 and 640 CSS pixels), verifying nine visible columns, literal `1d` adjacency to `1 week`, two-decimal alignment/readability, independent gain/loss/zero/unavailable colors, all-column access, full entity labels, preserved chart dimensions, and native navigation/selection; validate numeric edge cases through deterministic tests when live evidence cannot supply them.
- [ ] T022 Record actual command results, controlled-case coverage including stale histories with older valid pairs, before/after preservation comparisons, request-spy outcomes, and browser viewport/theme evidence in `specs/016-add-daily-performance/quickstart.md`; update `specs/016-add-daily-performance/plan.md` and `specs/README.md` only where pending/implemented wording is now supported by evidence, and mark `specs/016-add-daily-performance/tasks.md` tasks complete only after their expected outcomes pass, explicitly retaining any unresolved acceptance gaps.

**Final checkpoint**: FR-001-FR-009 and SC-001-SC-005 are supported by observed implementation
and acceptance results, not merely a new header or historical feature-015 evidence.

## Dependencies & Execution Order

### User-approved implementation follow-up: unified representation API

The user requested extending `representation_performance` itself and selected all six periods
by default with independent unavailable-period handling. This supersedes T007's separate
representation daily helper and T011/T015's original helper wiring without erasing their
completed historical test evidence. Daily dates remain requested-date/calendar anchored.

- [X] T023 Add failing six-period API tests in `tests/unit/test_industry_representations.py` for literal key order, approved ETF/basket returns, daily/longer-period independent availability, and contextual failures; extend `tests/unit/domain/test_sector_performance.py` and `tests/app/test_sector_stock_explorer.py` for isolated longer horizons and short entity/benchmark history.
- [X] T024 Consolidate daily computation into `representation_performance` in `packages/market-data/src/market_data/domain/industry_representations.py`, using typed value/reason entries and the exact-session scalar calculator; allow one existing horizon in `calculate_absolute_performance` without changing its five-period default. Migrate all production/test callers, preserve ranking/snapshot all-required five-period outputs, and keep daily/longer-period effectivity independent. Depends on T023 and the completed daily foundation.
- [X] T025 Reconcile this API decision, intentional independent longer-period availability, migration/versioning impact, and observed validation in `specs/016-add-daily-performance/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/daily-performance-ui.md`, and `quickstart.md`. Depends on T024's implementation and passing automated gates.

T024 also precedes T020's final automated gate; T025 does not establish T021 browser acceptance
or T022 final feature completion. Final focused validation passed 243 tests and Ruff/Pyright.
The broader offline suite passed 1041 tests with one confirmed pre-existing tab-count assertion
failure. T021/T022 remain unchecked: browser viewport/theme evidence has not been collected.

### Phase and Story Dependencies

```text
T001 scope gate
  -> T002, T003, T004 (independent failing foundation tests)
  -> T005, T006, T007 (shared helpers, prerequisite edges below)
  -> US1: T008-T012
  -> US2: T013-T015
  -> US3: T016-T019
  -> T020 automated gates -> T021 browser acceptance -> T022 evidence
```

- Foundation: T005 requires T002; T006 requires T003; T007 requires T004 and T006.
  All foundation tasks require T001. T005-T007 must be complete before story work begins.
- US1: T008, T009, and T010 share only the completed foundation. T011 and T012 follow
  all three test tasks. US1 completes when both implementations and its independent tests pass.
- US2: T013 and T014 follow US1; T015 follows both tests. The story reuses US1's column
  integration, and shares its workflow/AppTest file, so source work is not parallel with US1.
- US3: T016-T018 follow US2 and can run together in distinct files; T019 follows all three
  and completes common basis/failure handling. US3 is tested independently in both tables.
- Cross-cutting acceptance: T020 follows US3; T021 follows T020; T022 follows T020/T021.
  Do not claim browser success when the environment cannot exercise a requirement.

The story order reflects shared existing files and the specification's priorities, not a
requirement to select an industry to test sector behavior. Tests are independently meaningful
even when earlier shared work already supplies part of their implementation.

### Parallel Opportunities

- After T001: T002, T003, and T004 use three separate test files.
- After their required test checkpoints: T005 and T006 use separate application/domain files;
  T007 waits for T006 and cannot run alongside edits to its own domain test implementation.
- After foundation: T008, T009, and T010 use three separate test files.
- After US1 tests: T011 and T012 use distinct workflow/style files. If T012 needs a renderer
  edit, keep that edit separate from any still-running renderer test authoring.
- After US1: T013 and T014 use separate AppTest/integration files.
- After US2: T016, T017, and T018 use three separate test files.
- Do not parallelize story implementations: T011, T015, and T019 modify the same workflow.

## Parallel Example: User Story 1

After foundation, author T008 sector AppTest cases, T009 daily palette cases, and T010
literal-heading/cell-count renderer cases together. Once all three test tasks are complete
and the new behavior fails as expected, implement T011 workflow projection and T012 shared
column styling together. Run the combined relevant pytest selectors once for this checkpoint.

## Parallel Example: User Story 2

After US1, author T013 industry workflow tests and T014 approved-representation integration
tests together. Both precede the single T015 workflow integration task; do not race a sector
workflow edit against the industry edit.

## Parallel Example: User Story 3

After US2, author T016 basis/evidence AppTest cases, T017 unavailable-tooltip renderer cases,
and T018 clock/state/request-spy cases together. T019 follows all three; each file is owned
by one test task during the parallel batch.

## Implementation Strategy

### MVP First

1. Complete authority reconciliation and the shared test-first daily/session helpers.
2. Deliver and independently validate US1's Sector Absolute daily column as an internal
   demonstration. Do not advertise the full feature or introduce a temporary runtime mode.
3. Complete US2 and US3 before release: both named tables, both existing bases, and all
   unavailable-evidence cases are mandatory, not optional polish.

### Incremental Delivery

1. Preserve default five-period arithmetic and snapshots; migrate representation callers to
   the user-approved six-period value/reason API described in T023-T025.
2. Add the shared derived daily projection and renderer, then the industry representation path.
3. Complete matching benchmark/error contexts and state/load regressions.
4. Run the focused acceptance matrix, inspect actual browser output, and record only measured
   outcomes. A missing environment capability remains a named gap rather than a fabricated pass.

## Requirement Coverage

| Requirement | Delivering or verifying tasks |
|---|---|
| FR-001: literal daily header/position in both tables | T008, T010-T015, T021 |
| FR-002: unchanged five longer periods | T003, T008, T010-T016, T020 |
| FR-003: exact adjusted completed-session return | T002-T007, T011, T014-T016, T018-T020 |
| FR-004: existing basis and matching benchmark | T016, T018-T020 |
| FR-005: two decimals/alignment/per-period palettes | T009-T012, T017, T021 |
| FR-006: explicit uncolored unavailable, no fallback | T003-T004, T008-T011, T014-T019 |
| FR-007: own approved evidence and disclosures | T004, T007, T011, T013-T019 |
| FR-008: unchanged navigation/state/sorting/charts/stocks | T001, T008, T010-T015, T018-T021 |
| FR-009: visible even with unavailable rows/narrow access | T008, T010-T013, T017, T021 |
| SC-001: literal six-horizon order in every tested row state | T008, T010, T013, T017, T021 |
| SC-002: 100% correct controlled returns under both bases | T002-T007, T008, T013-T016, T018-T020 |
| SC-003: 100% explicit missing/invalid endpoints | T003-T004, T014, T016-T020 |
| SC-004: measured before/after behavior preservation | T003, T008, T010, T013-T014, T018, T020-T022 |
| SC-005: adjacent daily/weekly comparison without another view | T008, T010, T013, T021-T022 |

## Notes

- Keep data-model constraints quoted in task descriptions as implementation invariants.
- The unified-API follow-up supersedes the original helper/exception-only result descriptions:
  expected per-period failures now carry an explicit typed reason, and supported longer
  horizons are independently available. Historical completed task evidence is retained.
- Absence of a benchmark invalidates only relative daily evidence; do not silently change
  the existing long-period Absolute path as part of this feature.
- Session adjacency comes from the calendar, never from the last two non-null observations.
- Resolve daily endpoints from requested_as_of and the completion clock, not observed_as_of;
  older valid daily pairs must not replace missing required evidence.
- Keep observed_as_of as disclosure context and as the existing chart/long-period cutoff only.
- Do not inspect unrelated old prices to decide whether valid daily endpoints are usable.
- Keep source/requested/observed/freshness and representation context; append daily reasons.
- No commits, remote publication, or change to historical completed task status is requested
  by this task-generation document.
