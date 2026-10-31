# Tasks: Sector-to-Stock Explorer

**2026-11-01 presentation amendment**: Current regression tests cover clickable sector and
industry names, stable node identity despite duplicate names, hidden industry Status and
Representation columns, and navigation to uncovered/empty cohorts with preserved controls.
The historical tasks below retain their original completion evidence; the current spec and
contract supersede the earlier entity-column presentation.

**Input**: Design documents from `/specs/004-sector-stock-explorer/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Tests**: Tests are included because the project constitution requires tests first and the plan defines automated acceptance evidence. Write each behavior test before its implementation and confirm it fails for the missing behavior.

**Organization**: Tasks are grouped by the three prioritized user stories. Existing application dependencies and test tooling are reused; SQLite uses Python's standard library.

## Phase 1: Setup

**Purpose**: Project initialization

No setup tasks are needed. Python dependencies, test runners, and the two-tab Streamlit entrypoint already exist.

## Phase 2: Foundational

**Purpose**: Blocking prerequisites shared by all user stories

No separate project-wide framework is required. The database and its first consumer belong to User Story 1; chart and score evidence remain in their respective stories.

## Phase 3: User Story 1 - Explore Market Leadership by Hierarchy (Priority: P1) 🎯 MVP

**Goal**: Replace the required `STOCK_MEMBERSHIP_CATALOG` runtime configuration with a populated SQLite regional universe and show the correct region, sector, industry, and member-stock hierarchy with truthful coverage and setup states.

**Independent Test**: Using a temporary database and controlled imports, verify database initialization, atomic validation/import, US region coverage, deduplicated multi-listing membership, placeholder handling, conflict reporting, and sector-to-industry-to-stock selection without stale rows. With no valid database, verify Discovery explains how to initialize and populate it.

### Tests for User Story 1

- [X] T001 [P] [US1] Add schema and repository tests in `tests/unit/infrastructure/test_region_database.py` for foreign keys, effective-date queries, region-scoped deduplication, chart representations, and the exact states `coverage_state` (`complete | partial | unverified`), `resolution_state` (`identified | placeholder`), and `classification_state` (`classified | unclassified | conflict`); verify at most one active primary listing per provider and region.
- [X] T002 [P] [US1] Add CSV/JSON validation and atomic-import tests in `tests/unit/infrastructure/test_universe_import.py` for missing classification, placeholders, duplicate listings, local-source conflicts, idempotency, and the exact import statuses `validated | committed | committed_partial | rejected`; prove rejected imports preserve the last valid database state.
- [X] T003 [P] [US1] Add CLI contract tests in `tests/integration/test_universe_admin.py` for `init`, `validate`, `import`, and approval-gated `refresh`, including nonzero failures, actionable reports, and no provider call before review approval.
- [X] T004 [P] [US1] Extend region and parent/child transition tests in `tests/unit/domain/test_progressive_selection.py` to prove stable-ID selection, region scoping, invalid-descendant clearing, and database-revision reconciliation.
- [X] T005 [P] [US1] Extend hierarchy AppTest cases in `tests/app/test_sector_stock_explorer.py` to cover database-missing/invalid/unpopulated setup guidance, region coverage disclosure, US sector-to-industry-to-stock views, and no stale rows after changing parents.

### Implementation for User Story 1

- [X] T006 [US1] Implement the SQLite schema, initialization, and focused repository queries in `src/market_leadership/infrastructure/region_database.py`; persist region, classification, sector, industry, stock, listing, membership, representation, provenance, import-run, and issue records with foreign keys, stable IDs, and the data-model effective-date and uniqueness rules.
- [X] T007 [US1] Implement reviewed CSV and JSON parsing, validation, conflict reporting, placeholder/unclassified handling, coverage updates, and atomic/idempotent writes in `src/market_leadership/infrastructure/universe_import.py`; preserve local classifications as authoritative and record live differences without overwriting them.
- [X] T008 [US1] Implement `init`, `validate`, `import`, and gated `refresh` commands in `src/market_leadership/universe_admin.py`; use `.data/market-universe.sqlite` by default, support `--database`, require reviewed source/coverage metadata for imports, and keep refresh disabled until the single selected provider's coverage, terms, and display rights are approved.
- [X] T009 [US1] Adapt membership loading in `src/market_leadership/infrastructure/stock_membership.py` and `src/market_leadership/application/discover_sectors.py` to read active region/classification/industry records from SQLite instead of requiring `STOCK_MEMBERSHIP_CATALOG`; return each `instrument_id` once and preserve explicit missing-database, invalid-database, empty-membership, and coverage states.
- [X] T010 [P] [US1] Extend typed selection and reconciliation in `src/market_leadership/domain/progressive_selection.py` to carry stable `region_id` and `database_revision` context and clear only descendants invalidated by a region, sector, or industry change.
- [X] T011 [US1] Update `src/market_leadership/ui/workflows/discovery_page.py` to select the US region initially, show a region control when multiple regions are populated, render only the valid hierarchy stage, display reviewed coverage scope/as-of/completeness, and show actionable initialization/import guidance rather than a valid-empty-market state.
- [X] T012 [US1] Update `src/market_leadership/ui/workflows/industry_deep_dive.py` to obtain the same region-scoped memberships from the SQLite repository while retaining its current evidence and review gates.

**Checkpoint**: A reviewed local import can populate a US regional database, and Discovery can show its sector/industry/member hierarchy without requiring `STOCK_MEMBERSHIP_CATALOG`; setup, coverage, conflicts, and unresolved records remain explicit.

## Phase 4: User Story 2 - Compare Sector, Industry, and Stock Evidence (Priority: P1)

**Goal**: Show each sector, industry, and stock's own price thumbnail beside an adjacent volume thumbnail, with directional bars and existing peer scores where available.

**Independent Test**: With a populated test database and controlled completed histories, verify all three tapes bind both thumbnails to the row's identity and same sessions, show the 50-session average when supported, color volume bars by close direction, and retain explicit unavailable/insufficient evidence. Verify scores use the complete eligible industry cohort and load only after explicit user intent.

**Dependency**: Requires User Story 1's database-backed hierarchy and active-member query.

### Tests for User Story 2

- [X] T013 [P] [US2] Add or extend domain tests in `tests/unit/domain/test_stock_chart.py` for row-bound preview series, 50-session averages over exactly 50 completed closes, identical price/volume sessions, and `up`/`down`/`neutral` direction including first, unchanged, and indeterminate observations.
- [X] T014 [P] [US2] Extend component tests in `tests/unit/ui/test_progressive_tape.py` to verify separate adjacent price and volume columns for sector, industry, and stock rows, the directional-color explanation, and independent missing-price, missing-volume, and insufficient-average states.
- [X] T015 [P] [US2] Extend provider/cache integration tests in `tests/integration/test_stock_evidence.py` to prove only verified active listings in the selected region/industry are requested, placeholders are skipped, histories are not borrowed across rows, and financial evidence loads only on explicit intent for the complete eligible cohort.
- [X] T016 [US2] Extend AppTest coverage in `tests/app/test_sector_stock_explorer.py` to verify chart-column adjacency and row identity in all three stages, directional legend wording, and visible unavailable states without hiding otherwise valid rows.

### Implementation for User Story 2

- [X] T017 [US2] Extend chart evidence calculation in `src/market_leadership/domain/stock_chart.py` to produce each entity's same-session close, 50-session average, volume, and close-to-close direction series; compute averages from exactly 50 completed closes and retain available evidence when another series is insufficient.
- [X] T018 [US2] Update `src/market_leadership/ui/components/progressive_tape.py` to render row-specific price and separate adjacent volume thumbnails for all tape types, use green for up, red for down, and neutral for unchanged/unknown direction, and identify the colors as price-direction indications rather than verified buyer/seller activity.
- [X] T019 [US2] Scope member price-history loading in `src/market_leadership/application/load_stock_history.py` and successful response caching in `src/market_leadership/ui/cache.py` to verified active listings for the selected region and industry; preserve per-instrument failures and do not request unresolved placeholders.
- [X] T020 [US2] Connect database-backed eligible memberships to score loading in `src/market_leadership/application/score_industry.py` and `src/market_leadership/ui/workflows/discovery_page.py`; retain the existing 001 Quality, Growth, and Cash Flow peer-score contract, load only after explicit user intent, score the full eligible cohort before display filtering, and expose partial/insufficient/error states.

**Checkpoint**: Each visible row has its own adjacent price and volume evidence, with correct 50-session and direction semantics; stock scores remain contract-compliant and are not fetched implicitly.

## Phase 5: User Story 3 - Inspect an Individual Stock (Priority: P2)

**Goal**: Open the selected stable stock identity in a detailed view with its own price/volume chart, 50/150-session averages, and the same three peer scorecards.

**Independent Test**: Select a known instrument from a controlled regional database, verify detail identity and chart values/states, then return to the same valid region, sector, and industry context.

**Dependency**: Requires User Story 1's stable member identities and User Story 2's stock histories and peer-score evidence.

### Tests for User Story 3

- [X] T021 [P] [US3] Extend chart-domain tests in `tests/unit/domain/test_stock_chart.py` to verify 50- and 150-session simple averages use exactly that many completed observations and each insufficient series is represented independently, not as zero.
- [X] T022 [P] [US3] Extend detail AppTest cases in `tests/app/test_stock_detail.py` to verify activation opens the same stable `instrument_id`, presents the matching three peer scores and explicit missing-evidence states, and returns to the prior valid hierarchy context.

### Implementation for User Story 3

- [X] T023 [US3] Update `src/market_leadership/ui/components/stock_detail.py` to render the selected instrument's own completed price/volume history and 50/150-session averages, identify each unavailable series independently, and show the same Quality, Growth, and Cash Flow score states as the stock tape.
- [X] T024 [US3] Wire stable stock-row activation, stale-ID validation, detail return, and context preservation in `src/market_leadership/ui/workflows/discovery_page.py`; retain valid region/sector/industry selections and clear only the stock-detail selection on return.

**Checkpoint**: Activating a stock opens that exact security's detail view, and returning restores its valid Discovery context.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Keep operational guidance and regression evidence aligned with the implementation.

- [X] T025 [P] Update `specs/004-sector-stock-explorer/contracts/universe-management-cli.md` and `specs/004-sector-stock-explorer/quickstart.md` to document the implemented reviewed-file inputs, database lifecycle, import/validation commands, approval gate, and focused verification workflow.
- [X] T026 Run the focused feature tests and quality checks from `specs/004-sector-stock-explorer/quickstart.md`, then run `uv run ruff check src/market_leadership tests`, `uv run pyright`, and `uv run pytest -m "not live"`; resolve feature-caused failures without weakening existing checks.

## Phase 7: Preserve the Accepted Sector Performance Baseline

**Scope**: Reverse-document the existing implementation under FR-025-FR-032 / SC-012-SC-015,
not rebuild it. Completed items record inspected implementation and existing evidence, not
newly executed code changes. Preserve all earlier task IDs and completion history.

### Completed implementation and reconciliation

- [X] T027 [US2] Record the accepted heading/controls, labels/order, chart size, period/basis behavior, colors, ETF basis, and explicit change-approval rule in `specs/004-sector-stock-explorer/spec.md`, `specs/004-sector-stock-explorer/plan.md`, and `specs/004-sector-stock-explorer/contracts/progressive-discovery.md`; retain this feature and leave runtime code unchanged during reconciliation.
- [X] T028 [US2] Preserve the implemented left/middle/right header and namespaced control persistence in `src/market_leadership/ui/workflows/discovery_page.py`; existing defaults/options/navigation checks are in `tests/app/test_sector_stock_explorer.py`.
- [X] T029 [US2] Preserve inclusive calendar-window cropping after SMA/direction calculation in `src/market_leadership/ui/components/progressive_tape.py`; all five windows, warmup, first-visible direction, and empty-window behavior are covered by `tests/unit/ui/test_progressive_tape.py`.
- [X] T030 [US2] Preserve 84-pixel height and nominal 135-pixel width for price with/without SMA and volume in `src/market_leadership/ui/components/progressive_tape.py`; exact chart-spec dimensions are covered by `tests/unit/ui/test_progressive_tape.py`.
- [X] T031 [US2] Preserve shared light/dark per-period/per-sign colors, two-decimal percentages, neutral zero, and uncolored missing values in `src/market_leadership/ui/performance_table.py` and `src/market_leadership/ui/components/progressive_tape.py`; existing checks are in `tests/unit/ui/test_progressive_tape.py` and `tests/unit/ui/test_performance_table.py`.
- [X] T032 [US2] Preserve Ticker and the independence of preview windows from the five returns in `src/market_leadership/ui/workflows/discovery_page.py`; existing tests in `tests/app/test_sector_stock_explorer.py` prove the heading and unchanged sufficient returns for short/long windows.
- [X] T033 [US2] Document reviewed ETF setup and implemented controls/formatting in `specs/004-sector-stock-explorer/quickstart.md`; reconcile `specs/004-sector-stock-explorer/checklists/requirements.md` without treating ignored local database contents as clean-checkout defaults.

### Remaining regression protection (no presentation changes)

- [X] T034 [US2] Extend `tests/app/test_sector_stock_explorer.py` and `tests/integration/test_region_discovery.py` with deterministic baseline assertions for complete ordered sector/industry columns, cleared-control defaults, and all 11 FR-032 mappings; use temporary databases to prove effective-date filtering, missing-mapping states, and unchanged membership counts. Do not seed runtime fallback mappings or modify UI behavior to pass tests.
- [X] T035 [US2] After T034, run focused tests from `specs/004-sector-stock-explorer/quickstart.md` and verify a fresh browser session at a wide viewport retains heading/period/basis order, both 84-pixel plots, colored percentages, and all five selectable windows. Record observed results in `specs/004-sector-stock-explorer/quickstart.md`; report discrepancies rather than redesigning the baseline.

**Dependencies**: T027 records accepted behavior from T028-T032 and follows original US2 work
(T017-T020). T033 follows T027. T034 follows T027-T033; T035 follows T034.
T028-T032 are completed implementation history, not instructions to replace the UI.
The original reconciliation implemented no runtime changes. T034-T035 were subsequently
completed during convergence implementation; the quickstart records automated and browser evidence.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependency installation or project initialization is needed.
- **Foundational (Phase 2)**: No separate cross-feature foundation is needed.
- **User Stories**: US1 has no feature-story dependency. US2 depends on US1's database-backed membership and selection context. US3 depends on US1's stable stock identity and US2's chart history and score evidence.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after the existing project setup; database, ingestion, and hierarchy work form the MVP.
- **US2 (P1)**: Starts after US1's database repository and hierarchy integration are available.
- **US3 (P2)**: Starts after US1 and US2 provide stable identities, member histories, and score states.

### Within Each User Story

- Tests are written first and confirmed to fail before implementation.
- In US1, database schema/repository precedes ingestion and CLI; database membership and selection precede Discovery integration.
- In US2, chart calculation precedes rendering; scoped history and database membership precede stock evidence integration.
- In US3, chart evidence and score availability precede detail rendering; detail rendering precedes workflow navigation integration.
- Do not parallelize tasks that edit the same file.

### Parallel Opportunities

- **US1 tests**: T001-T005 can be authored in parallel because they use separate test files. After tests, T006 and T010 can proceed in parallel; T007 follows T006, and T008 follows T006/T007. T009 follows T006/T007; T011/T012 follow the repository and selection integrations.
- **US2 tests**: T013-T015 can be authored in parallel. T016 follows US1's AppTest work because it extends the same test file. After tests, T017 and T019 can proceed in parallel; T018 follows T017; T020 follows the database membership and score evidence interfaces.
- **US3 tests**: T021 and T022 can be authored in parallel. T023 follows the chart and score evidence work; T024 follows T023.
- **Cross-story**: Stories are delivered sequentially because US2 consumes US1's database membership and US3 consumes evidence from both earlier stories.

## Parallel Examples

### User Story 1

```text
Task: T001 Add SQLite repository tests in tests/unit/infrastructure/test_region_database.py
Task: T002 Add import validation tests in tests/unit/infrastructure/test_universe_import.py
Task: T003 Add CLI contract tests in tests/integration/test_universe_admin.py
Task: T004 Extend region selection tests in tests/unit/domain/test_progressive_selection.py
Task: T005 Extend hierarchy AppTest cases in tests/app/test_sector_stock_explorer.py
```

### User Story 2

```text
Task: T013 Add chart-preview domain tests in tests/unit/domain/test_stock_chart.py
Task: T014 Extend tape component tests in tests/unit/ui/test_progressive_tape.py
Task: T015 Extend history and score-loading integration tests in tests/integration/test_stock_evidence.py
```

### User Story 3

```text
Task: T021 Extend stock moving-average tests in tests/unit/domain/test_stock_chart.py
Task: T022 Extend stock-detail AppTest cases in tests/app/test_stock_detail.py
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T012.
2. Verify reviewed local-file initialization/import, region coverage, unique industry membership, and all hierarchy transitions independently.
3. Stop at the US1 checkpoint: the industry membership configuration error is replaced by a working database-backed path and actionable setup guidance.

### Incremental Delivery

1. Deliver US1 and verify the database-backed hierarchy and CLI independently.
2. Deliver US2 and verify row-specific adjacent chart evidence, provider request scope, and explicit peer-score loading.
3. Deliver US3 and verify stock-specific detail and context return.
4. Run all validation commands in the quickstart after the desired stories are complete.

## Notes

- Every task uses the required checklist format: unchecked checkbox, sequential ID, optional `[P]`, story label for story tasks, and exact file path(s).
- The live membership refresh remains disabled until the single selected provider passes the required coverage, terms, and display-rights review; tasks must not select or substitute an unreviewed provider.
- No source-priority merge, fabricated classification, proxy-chart substitution, or score aggregate is introduced.

## Phase 8: Convergence

Assessment date: 2026-10-30. These tasks address verified implementation gaps; they do not
authorize a redesign of FR-025-FR-032. Retain all earlier task IDs, checkbox states, and the
accepted Sector performance layout, dimensions, controls, labels, palettes, and calculations.
The existing feature suite passed 74 tests, but targeted temporary-database/provider checks
reproduced the gaps below. Live membership refresh remains approval-gated as planned; this
phase does not authorize enabling it or selecting a new provider.

- [X] T036 [US2] CRITICAL — Fix unsuccessful member-history caching and refresh persistence in `src/market_leadership/ui/cache.py`: an empty provider response is cached as an unavailable batch, a forced refresh returns recovered evidence, and the next ordinary call returns the old unavailable batch. Cache only successful evidence, keep per-member failures explicit and retryable, and replace/invalidate the matching successful-cache entry on refresh without clearing unrelated scopes. Add recovering-provider, partial-batch, and refresh-then-rerun regressions in `tests/integration/test_stock_evidence.py` per Constitution application constraint on successful-only caching and scoped refresh, T019 (contradicts). Finding F1.

- [X] T037 [US2] CRITICAL — Remove hidden industry-proxy history requests when the stock tape/detail is active in `src/market_leadership/ui/workflows/discovery_page.py`; a controlled stock-tape navigation currently requests `('SPY', 'PPP')` for an invisible industry proxy before requesting member symbols `('AAA', 'BBB')`. Restrict requests to evidence required by the active view, retaining any benchmark request needed for the visible provenance/freshness contract, all explicit score-load gates, and the accepted header/control presentation. Add recording-provider tests for stock-tape/detail navigation in `tests/app/test_sector_stock_explorer.py` and `tests/integration/test_stock_evidence.py` per Constitution IV and the application active-view request constraint, plan: Phase 1 data flow steps 2-5 (contradicts). Finding F2.

- [X] T038 [US1] Deduplicate effective-dated membership results by stable `instrument_id` in `src/market_leadership/infrastructure/region_database.py` and reconcile accepted overlapping same-industry records in `src/market_leadership/infrastructure/universe_import.py` without losing listing/source history. Two reviewed listings for the same instrument, with membership starts in 2020 and 2021, currently return two member rows on 2026-10-30 because `SELECT DISTINCT` includes membership dates. Add differing-start/overlapping-period and multi-listing tests in `tests/unit/infrastructure/test_region_database.py` and `tests/integration/test_region_discovery.py`; prove each stock is returned/scored once and historical queries remain correct per FR-016, SC-006, US1/AC7, T001/T006/T009 (partial). Finding F3.

- [X] T039 [US1] Make row quarantine and rejected publication atomic in `src/market_leadership/infrastructure/universe_import.py`: validate identity/listing conflicts before publishing dependent records or use transactional row isolation, and preserve the prior published hierarchy, stocks, memberships, coverage, and revision when no rows are accepted. A rejected conflicting listing currently leaves an orphan stock and new sector, while rejected classification input changes region coverage metadata. Keep actionable import-run/issues audit records without publishing rejected data. Add database-snapshot regressions for all-rejected and mixed accepted/quarantined inputs in `tests/unit/infrastructure/test_universe_import.py` per T002/T007, plan: atomic import/publication decision and referenced data-model rejection invariant (contradicts). Finding F4.

- [X] T040 [US1] Reconcile stored stock states after reviewed imports in `src/market_leadership/infrastructure/universe_import.py` rather than leaving the first `INSERT OR IGNORE` state forever: a placeholder receiving a verified listing remains `placeholder` and is still excluded from live requests; likewise an unclassified stock receiving reviewed membership must reflect its accepted classification. Preserve stable identity, report conflicting changes, and do not downgrade already verified/classified evidence on an incomplete later row. Add promotion/state-coherence tests in `tests/unit/infrastructure/test_universe_import.py` and request-eligibility tests in `tests/integration/test_stock_evidence.py` per FR-021, US1/AC8, T006/T007/T019 (partial). Finding F5.

- [X] T041 [US1] Make reviewed-file validation detect existing local-source conflicts using the target `--database` in `src/market_leadership/universe_admin.py` and `src/market_leadership/infrastructure/universe_import.py`. Currently the validate command accepts a database option but never consults it, so a file that conflicts with stored reviewed membership reports zero conflicts before import rejects it. Share conflict checks with import, also detect inconsistent identity/name/parent values within input, and keep validation read-only and usable before database initialization. Add CLI and importer regressions in `tests/integration/test_universe_admin.py` and `tests/unit/infrastructure/test_universe_import.py` per FR-023, US1/AC11, T002/T003/T007 (partial). Finding F6.

- [X] T042 [US1] Restore persisted conflict diagnostics and enforce matching review/import context on idempotent replay in `src/market_leadership/infrastructure/universe_import.py` and, if required, `src/market_leadership/infrastructure/region_database.py`. A repeated database-conflicting file currently keeps `rejected` status but returns zero conflicts and no issues because only fresh parse issues are returned. Validate source/approval/region/classification context before the early return; preserve accurate original row issues/counts with `inserted_rows=0`, and document any necessary schema migration without overwriting existing databases. Add repeat-partial/rejected and changed-context tests in `tests/unit/infrastructure/test_universe_import.py` and `tests/integration/test_universe_admin.py` per T002/T007/T025 and plan: idempotent imports with reviewed provenance (partial). Finding F7.

- [X] T043 [US2] Preserve independent price/volume evidence end-to-end in `src/market_leadership/application/load_stock_history.py`, `src/market_leadership/domain/stock_chart.py`, and `src/market_leadership/ui/components/stock_detail.py`, with necessary wiring in `src/market_leadership/ui/workflows/discovery_page.py`. Valid closes with missing volume currently become an empty insufficient history, hiding both price and latest-price evidence; detail also gates all chart rendering on price availability. Preserve validated available series, identify only affected series as unavailable/insufficient, and show independently usable volume without fabricating prices. Add pipeline/detail tests in `tests/integration/test_stock_evidence.py`, `tests/unit/domain/test_stock_chart.py`, and `tests/app/test_stock_detail.py` per FR-011/FR-017, US2/AC5, US3/AC4, T014/T019/T023 (partial). Finding F8.

- [X] T044 [US2] Expose insufficient/unavailable 50-session SMA state within existing price-chart cells in `src/market_leadership/ui/components/progressive_tape.py` while retaining the available price line, 84-pixel plot height, current column order, and all baseline controls/colors. Currently `build_price_thumbnail` silently returns a price-only chart when no SMA exists, with no row-specific insufficiency indication despite the shared SMA heading. Add component/AppTest coverage for short histories and cropped windows with/without valid warmup in `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_sector_stock_explorer.py` per FR-019, US2/AC5, T014/T018 (partial). Finding F9.

- [X] T045 [US1] Select active classifications by the requested as-of date in `src/market_leadership/infrastructure/region_database.py` and wire that date consistently through `src/market_leadership/infrastructure/stock_membership.py`, `src/market_leadership/ui/workflows/discovery_page.py`, and `src/market_leadership/ui/workflows/industry_deep_dive.py`. `get_classification_id` currently selects the newest classification without effective-date filtering; a future 2030 classification hides valid 2026 sectors and can make historical membership look empty. Add future/expired/current classification and historical-navigation tests in `tests/unit/infrastructure/test_region_database.py`, `tests/integration/test_region_discovery.py`, and `tests/app/test_sector_stock_explorer.py` per FR-014/FR-016, T001/T006/T009, plan: dated database-query semantics (partial). Finding F10.

- [X] T046 [US1] Preserve truthful region-wide coverage scope across accepted imports in `src/market_leadership/infrastructure/universe_import.py` and `src/market_leadership/infrastructure/region_database.py`: source-specific provenance must not unconditionally replace the region's combined reviewed scope, especially when importing the 11 unclassified chart ETF listings after exchange memberships. Retain source coverage records, preserve partial/unverified completeness semantics, and add sequential exchange/chart-only import tests in `tests/unit/infrastructure/test_universe_import.py` plus coverage-disclosure checks in `tests/integration/test_region_discovery.py` per FR-024, SC-011, US1/AC12, T007/T011 (contradicts). Finding F11.

- [X] T047 [US2] Complete the already-pending T034 then T035 preservation checks rather than creating a parallel redesign: add exact ordered sector/industry label, cleared-control default, and all-11-reviewed-mapping assertions in `tests/app/test_sector_stock_explorer.py` and `tests/integration/test_region_discovery.py`, including effective-date/missing-mapping behavior and unchanged stock memberships. After relevant convergence fixes, run the focused quality gates, verify the existing wide-screen header/controls, both 84-pixel plots, colored percentages, and all five periods in a fresh browser session, and record actual results in `specs/004-sector-stock-explorer/quickstart.md`. Use temporary reviewed test inputs, not runtime fallback mappings; report any baseline discrepancy without silently redesigning it per T034/T035, FR-025-FR-032, SC-014/SC-015, plan: preservation evidence (partial). Finding F12.

### Convergence dependencies and validation

- T039 precedes T040-T042 and T046 because accepted/quarantined publication boundaries must be
  correct before state, replay, and coverage reconciliation. T038 can be assessed independently,
  but coordinate edits to the same importer/repository files.
- T036 and T043 must be validated together for partial-series caching and refresh behavior;
  neither is permission to hide failed members or repeat successful requests unnecessarily.
- T037, T044, and T045 must preserve FR-025-FR-032 while correcting data/request/state behavior.
- T047 follows T036-T046 and completes existing T034 before existing T035. Keep the original
  T034/T035 entries and update their checkboxes only when their evidence is actually complete.
- Write reproducing tests before fixes. Run focused importer/repository/CLI, cache/history,
  component, and AppTest selectors for each affected behavior, then Ruff, Pyright, and the
  non-live regression suite. Use temporary databases and injected providers/clocks; never
  delete or rebuild a user's populated database as a test shortcut.
