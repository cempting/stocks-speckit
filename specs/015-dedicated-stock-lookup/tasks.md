---

description: "Implementation tasks for the Dedicated Stock Lookup feature"
---

# Tasks: Dedicated Stock Lookup

**Input**: Design documents from `specs/015-dedicated-stock-lookup/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/stock-lookup-ui.md,
quickstart.md

**Tests**: Test-first tasks are included to satisfy the project's constitution and the feature
plan's AppTest validation requirements.

**Organization**: Tasks are grouped by user story so the lookup relocation can be implemented
and verified incrementally.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and has no incomplete
  prerequisite.
- **[Story]**: User-story label for story-phase tasks.
- Every task includes the exact file path it changes or validates.

## Phase 1: Setup

**Purpose**: No package, dependency, or project initialization changes are required.

## Phase 2: Foundational

**Purpose**: Reuse the root-loaded catalog snapshot and existing stock identity/detail contracts;
no separate foundation is needed before User Story 1.

## Phase 3: User Story 1 - Find a Stock on Its Own Page (Priority: P1) 🎯 MVP

**Goal**: Expose stock lookup in its own root tab and remove the lookup workflow from Discovery.

**Independent Test**: Verify the root exposes Find a stock, Discovery no longer renders lookup
controls, and Discovery's remaining controls continue to render.

### Tests for User Story 1

- [X] T001 [P] [US1] Add a root-tab assertion for the Find a stock tab and single catalog load in `tests/app/test_progressive_tabs.py`
- [X] T002 [P] [US1] Assert Discovery does not render lookup search or lookup selection controls in `tests/app/test_discovery.py`

### Implementation for User Story 1

- [X] T003 [US1] Create a dedicated lookup renderer with namespaced session state, retained-identity search, no-match handling, and exact identity selection in `src/market_leadership/ui/workflows/stock_lookup.py`
- [X] T004 [US1] Remove the inline lookup call and lookup-only rendering from `src/market_leadership/ui/workflows/discovery_page.py`
- [X] T005 [US1] Register the fourth Find a stock tab in `src/market_leadership/app.py` and preserve/clear lookup controls in `src/market_leadership/ui/navigation.py`

**Checkpoint**: Find a stock is independently reachable; Discovery no longer contains stock
lookup, and all prior tabs remain available.

## Phase 4: User Story 2 - Verify the Stock Before Opening Its Detail (Priority: P1)

**Goal**: Preserve exact listing selection and explicit detail/history/evidence behavior in the
new tab.

**Independent Test**: With controlled identities and listings, verify exact identity/listing
selection, no history prefetch, explicit history actions, and visible failure/incomplete states.

### Tests for User Story 2

- [X] T006 [P] [US2] Run the existing ambiguous-identity and verified-listing scenarios against the dedicated workflow, and assert no history or evidence prefetch in `tests/app/test_stock_lookup.py`
- [X] T007 [US2] Add context-change coverage proving region, date, and catalog-revision changes invalidate dependent lookup and history state in `tests/app/test_stock_lookup.py`

### Implementation for User Story 2

- [X] T008 [US2] Move exact active-listing selection, stock-detail rendering, and explicit history/evidence actions into `src/market_leadership/ui/workflows/stock_lookup.py`
- [X] T009 [US2] Extract shared company-evidence controls with explicit per-workflow state namespaces in `src/market_leadership/ui/components/company_evidence.py`
- [X] T010 [US2] Add a workflow-specific widget-key prefix and back-button label to `src/market_leadership/ui/components/stock_detail.py`
- [X] T011 [US2] Revalidate detail and history state against the dedicated workflow's region, date, and catalog-revision context in `src/market_leadership/ui/workflows/stock_lookup.py`

**Checkpoint**: Selected details remain tied to an exact active verified listing; no remote
history or issuer-evidence request occurs until its explicit action.

## Phase 5: User Story 3 - Find Retained Stocks Without an Industry Assignment (Priority: P2)

**Goal**: Keep retained unassigned identities discoverable without inventing industry
membership.

**Independent Test**: Search for a retained unassigned identity and a no-match query; verify the
identity remains selectable without membership and stale selections are cleared.

### Tests for User Story 3

- [X] T012 [P] [US3] Verify retained identities without active memberships remain searchable and no-match queries clear stale results in `tests/app/test_stock_lookup.py`

### Implementation for User Story 3

- [X] T013 [US3] Use retained catalog identity lookup without filtering by industry membership or assigning memberships in `src/market_leadership/ui/workflows/stock_lookup.py`

**Checkpoint**: Unassigned retained identities remain accessible subject to listing verification;
lookup never assigns a classification.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Reconcile normative documentation, record the original governance tracking,
and validate the integrated feature. T015 is historical: constitution 4.0.0 now permits
the approved four tabs, and issue #2 is closed. Phase 9 records the later reconciliation.

- [X] T014 Update the feature authority map and reconcile Discovery/identity lookup ownership with feature 015 in `specs/README.md`, `specs/004-sector-stock-explorer/spec.md`, and `specs/012-stock-industry-memberships/spec.md`
- [X] T015 Create the required tracked follow-up issue for the three-step tab-architecture exception and record its URL and owner in `specs/015-dedicated-stock-lookup/plan.md`
- [X] T016 Run the focused regression command from `specs/015-dedicated-stock-lookup/quickstart.md` and resolve failures in the affected source and test files
- [X] T017 Run Ruff and strict Pyright for the changed Python files and resolve findings in those files

## Phase 7: Approved Two-Block Entity Buttons (2026-11-06)

**Scope**: FR-011-FR-013 and SC-006, approved after T001-T017 were completed.
This increment changed only button presentation; Phase 8 subsequently removes the
redundant entity ticker columns. Keep all other chart and control behavior.

- [X] T018 Add failing sector/industry/stock renderer tests in `tests/unit/ui/test_progressive_tape.py` for ticker-first labels, full literal names, unavailable/basket/no-ticker cases, unchanged stable keys/tooltips, and stock selection.
- [X] T019 Update/add failing workflow assertions in `tests/app/test_sector_stock_explorer.py` and `tests/app/test_stock_detail.py` for the two-block entity buttons across all three views while preserving navigation, period/basis/date state, five columns and explicit loading.
- [X] T020 Implement escaped two-block native button labels and narrowly scoped 2:1 typography/wrapping in `src/market_leadership/ui/components/progressive_tape.py`; reuse existing ticker evidence without new acquisition or altered callbacks.
- [X] T021 Reconcile `specs/015-dedicated-stock-lookup/contracts/stock-lookup-ui.md`, `specs/015-dedicated-stock-lookup/quickstart.md`, `specs/004-sector-stock-explorer/spec.md`, `specs/004-sector-stock-explorer/plan.md`, `specs/004-sector-stock-explorer/contracts/progressive-discovery.md`, `specs/006-stock-table-columns/contracts/stock-table.md` and `specs/README.md` with the limited approved presentation amendment.
- [X] T022 Run the focused renderer/workflow/lookup regressions, targeted Ruff and workspace strict Pyright; verify actual font-size ratio >=2, untruncated wrapping, native focusability and selection for all three views in light/dark narrow/wide local browser scenarios and record evidence plus any keyboard-automation limitation in `specs/015-dedicated-stock-lookup/quickstart.md`.

**Order**: T018 and T019 can be authored independently; confirm their changed-label
assertions fail before T020. T020 depends on both test tasks. T021 depends on the
approved design and T022 depends on T018-T021. Preserve completed T001-T017.

## Phase 8: Remove Redundant Entity Ticker Columns

**Scope**: FR-014/SC-007. Preserve completed T001-T022 and the stock table.

- [X] T023 Add/update failing visible-column regressions in `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_sector_stock_explorer.py`: exactly eight sector/industry headings, no separate Ticker/ETF, retained ticker/button/node identity and five stock columns.
- [X] T024 Hide sector Ticker and industry ETF only in the visible projection in `src/market_leadership/ui/components/progressive_tape.py`, preserving backing data, callbacks, charts, returns and explicit loading.
- [X] T025 Reconcile 015 spec/plan/contracts/data-model/research/quickstart, 004 spec/plan/contracts/task guidance and `specs/README.md`; run focused renderer/workflow/detail regressions, Ruff, strict Pyright and documentation-link checks, recording results in `specs/015-dedicated-stock-lookup/quickstart.md`.

**Order**: T023 must demonstrate the old visible-column failure before T024.
T025 follows T023-T024; no existing completed task is reopened or renumbered.

## Phase 9: Constitution 4.0.0 Reconciliation

**Scope**: C2 only. Preserve completed T001-T025; do not change application behavior or claim
new runtime/browser validation.

- [X] T026 Reconcile `specs/015-dedicated-stock-lookup/spec.md`, `specs/015-dedicated-stock-lookup/plan.md`, `specs/015-dedicated-stock-lookup/research.md`, `specs/015-dedicated-stock-lookup/contracts/stock-lookup-ui.md` and `specs/015-dedicated-stock-lookup/quickstart.md` with constitution 4.0.0: record the approved four tabs, remove obsolete active exception gates, verify issue #2 is closed, preserve historical T015, and validate documentation structure, references and whitespace.

**Order**: T026 follows the approved 4.0.0 amendment and verified closure of issue #2.
It is documentation-only; A1 and E1 remain separate follow-ups.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No initialization tasks; no new dependencies are planned.
- **Foundational (Phase 2)**: No separate blocking tasks; the existing root catalog snapshot and
  domain contracts are reused.
- **User Story 1 (Phase 3)**: Starts with T001 and T002; implementation tasks depend on those
  regression tests.
- **User Story 2 (Phase 4)**: Depends on the dedicated workflow and tab from User Story 1.
- **User Story 3 (Phase 5)**: Depends on User Story 2 because its regression coverage shares
  `tests/app/test_stock_lookup.py` and its behavior is implemented in the same workflow module.
- **Polish (Phase 6)**: Depends on all user stories. T014 and T015 may proceed independently of
  each other; validation tasks run after code and documentation changes.

### User Story Dependencies

- **User Story 1 (P1)**: No user-story dependency; it is the MVP.
- **User Story 2 (P1)**: Depends on User Story 1's dedicated tab and renderer.
- **User Story 3 (P2)**: Depends on User Story 2's lookup context and detail flow.

### Within Each User Story

- Write and run regression tests before implementing the corresponding behavior.
- Keep tasks touching `stock_lookup.py` sequential.
- Keep edits to `tests/app/test_stock_lookup.py` sequential across User Story 2 and User Story 3.
- Root-tab and Discovery-absence tests may be written in parallel because they touch different
  files.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- T012 precedes T013; both follow User Story 2, preserving test-first execution.
- No implementation tasks modifying the same workflow or app entrypoint may run in parallel.

## Parallel Example: User Story 1

```text
Task: T001 — Add root-tab and single-catalog-load assertions in tests/app/test_progressive_tabs.py
Task: T002 — Assert lookup controls are absent from tests/app/test_discovery.py
```

## Implementation Strategy

### MVP First (User Story 1)

1. Add the root-tab and Discovery regression tests.
2. Move the search/identity-selection workflow to its own UI workflow.
3. Remove lookup rendering from Discovery and register the fourth tab.
4. Validate that the lookup is separate and the other tabs still render.

### Incremental Delivery

1. Complete User Story 2 to preserve exact verified listings, detail behavior, and explicit data
   requests.
2. Complete User Story 3 to verify unassigned identities and no-match state behavior.
3. Reconcile the specifications, create and record the required architecture follow-up issue,
   then run the focused tests, Ruff, and Pyright.
