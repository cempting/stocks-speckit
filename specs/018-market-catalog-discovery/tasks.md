---

description: "Implementation tasks for US industry and theme ETF discovery"
---

# Tasks: US Industry and Theme ETF Discovery

**Input**: Design documents from `specs/018-market-catalog-discovery/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Include tests first in each story, as required by the project constitution and the
feature's independent acceptance criteria. Live yFinance retrieval remains opt-in.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated
independently.

## Phase 1: Setup

**Purpose**: Provide reusable, deterministic test evidence for multi-classification releases.

- [ ] T001 Add a test-only release-v2 fixture with two simultaneously active custom US classifications, distinct reviewed ETF mappings, and an explicitly empty stock artifact in `tests/membership_helpers.py` and `tests/conftest.py`

---

## Phase 2: Foundational

**Purpose**: Add the typed scope-resolution capability needed by all catalog-backed workflows.

**Checkpoint**: Scope enumeration and legacy single-scope behavior are verified before story work.

- [ ] T002 Add contract tests for zero, one, and multiple active scopes at selected dates in `tests/contract/test_catalog_v2.py`
- [ ] T003 Add typed active-scope enumeration to `CatalogSnapshot` in `packages/market-data/src/market_data/catalog.py`; honor “Scope enumeration returns all active classifications for a region/date.” and “Scope resolution by region/date alone remains valid only when exactly one classification is active; otherwise the caller must supply a selected exact scope.”

---

## Phase 3: User Story 1 - Discover US industries and themes (Priority: P1) 🎯 MVP

**Goal**: Let users select an exact active classification, navigate only its reviewed hierarchy,
and compare every approved ETF mapped to visible categories.

**Independent Test**: Load the synthetic two-classification release and verify isolated hierarchy,
explicit scope selection, dependent-selection clearing, all ETF alternatives, and no inferred stock
membership.

### Tests for User Story 1

- [ ] T004 [P] [US1] Test that a node with multiple approved ETF mappings returns every mapping as a distinct option in `tests/integration/test_catalog_workflows.py`
- [ ] T005 [P] [US1] Test Discovery classification selection, theme-level navigation, and clearing stale descendants when scope or parent changes in `tests/app/test_discovery.py`; honor “Category navigation follows reviewed parent relationships and never matches by display name.”
- [ ] T006 [P] [US1] Test that Industry Deep-Dive explicitly selects between active classifications and resets dependent selections in `tests/app/test_industry_discovery.py`

### Implementation for User Story 1

- [ ] T007 [US1] Preserve all effective mapping options in the representation projection across `packages/market-data/src/market_data/domain/industry_representations.py` and `src/market_leadership/application/industry_representations.py`; honor “A node may have zero or multiple effective approved ETF representation options.”
- [ ] T008 [P] [US1] Add explicit multi-classification selection and render every valid ETF option in `src/market_leadership/ui/workflows/discovery_page.py`; honor “The app displays all valid options; it does not select one based on CSV order or sort order.”
- [ ] T009 [P] [US1] Add explicit classification selection and classification-namespaced state to `src/market_leadership/ui/workflows/industry_deep_dive.py`; honor “State keys are namespaced per workflow and stable IDs, not display labels.” and clear only selections invalidated by classification changes

**Checkpoint**: Discovery and Industry Deep-Dive operate on exact selected scopes, while single-scope
catalogs retain their existing workflow.

---

## Phase 4: User Story 2 - Publish the supplied market data as a governed source (Priority: P1)

**Goal**: Keep the supplied CSVs as candidate authoring data and validate or publish them only as a
complete, reviewed release-v2 catalog.

**Independent Test**: Structurally validate the five candidate CSVs without treating their
references as approval, then verify a controlled complete release can be validated and atomically
activated while invalid or incomplete releases cannot replace the active entry.

### Tests for User Story 2

- [ ] T010 [P] [US2] Add a read-only structural test for `docs/markets/US/hierarchy.csv`, `docs/markets/US/etf_listings.csv`, `docs/markets/US/sector_etfs.csv`, `docs/markets/US/industry_etfs.csv`, and `docs/markets/US/sub_industry_etfs.csv` that checks headers, row shapes, scoped node/listing references, and honors “Mapping approval is not inferred from a category label, ETF name, ticker, or ETF holdings.” in `tests/contract/test_us_catalog_input.py`
- [ ] T011 [P] [US2] Test validate-and-activate CLI behavior for a complete dual-classification release and rejection of an invalid release without changing the active entry in `tests/contract/test_catalog_cli.py`; honor “No release becomes active until all required artifacts and review evidence validate.”

### Implementation for User Story 2

- [ ] T012 [P] [US2] Document release-v2 artifact roles, required evidence and companion artifacts, and the validate-before-activate commands without editing candidate CSVs in `docs/markets/US/README.md`

**Checkpoint**: Reviewers can distinguish structural input checks from approval and follow the
existing manifest, validation, and atomic publication lifecycle. Do not activate the current
candidate files until required source, approval, suitability, audit, benchmark, and stock-artifact
evidence is available.

---

## Phase 5: User Story 3 - See ETF data availability without losing the rest of Discovery (Priority: P2)

**Goal**: Report provider history state per ETF mapping, use exact `ProviderSymbol` values, and
preserve valid results when another symbol has missing or insufficient history.

**Independent Test**: With a controlled batch containing available, empty, insufficient, and failed
history, verify each mapping receives an explicit state and successful mappings remain usable.

### Tests for User Story 3

- [ ] T013 [P] [US3] Test that yFinance receives exact requested provider symbols and that one absent symbol yields empty history without suppressing another symbol's history in `tests/unit/infrastructure/test_market_data_providers.py`; honor “The provider symbol is the exact market-history request identifier; it is not guessed from the ticker.”
- [ ] T014 [P] [US3] Test per-mapping available, no-history, insufficient-history, and request-failed states, including “A missing symbol must not suppress valid symbols in a partial provider response.” and “If no reviewed membership artifact is present, contained-stock data is explicitly unavailable.” in `tests/integration/test_discover_sectors.py` and `tests/app/test_discovery.py`
- [ ] T015 [P] [US3] Add an opt-in live retrieval test that requests every active mapped `ProviderSymbol` from the validated catalog and reports status and date coverage in `tests/live/test_us_catalog_etf_retrieval.py`

### Implementation for User Story 3

- [ ] T016 [US3] Add per-mapping history availability results to `src/market_leadership/application/discover_sectors.py`; use the exact statuses “available”, “no_history”, “insufficient_history”, and “request_failed”, and honor “Failures are not cached or presented as successful stale results.”
- [ ] T017 [US3] Render each ETF option's specific history state in `src/market_leadership/ui/workflows/discovery_page.py`; ensure a missing symbol cannot suppress other valid results and failures are not shown as stale successful data

**Checkpoint**: Every visible mapping has usable performance or a specific unavailable state;
live provider verification is not part of ordinary CI.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Reconcile runnable validation guidance, responsive browser evidence, and repository
quality checks.

- [ ] T018 Update offline, browser, and opt-in live validation commands and expected outcomes in `specs/018-market-catalog-discovery/quickstart.md`
- [ ] T019 Validate Discovery and Industry Deep-Dive at 1440px and 390px, exercise scope changes and ETF alternatives, and record viewport results and remaining gaps in `specs/018-market-catalog-discovery/quickstart.md`
- [ ] T020 Run focused catalog, application, provider, and UI tests plus Ruff and Pyright; record the exact commands and outcomes in `specs/018-market-catalog-discovery/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; provides the controlled multi-classification fixture.
- **Foundational (Phase 2)**: Depends on Setup; blocks both P1 stories and the P2 story.
- **User Story 1 (Phase 3)**: Depends on Foundational scope resolution.
- **User Story 2 (Phase 4)**: Depends on the shared fixture and catalog v2 baseline; independent of
  User Story 1 implementation.
- **User Story 3 (Phase 5)**: Depends on User Story 1's all-options projection and Discovery UI.
- **Polish (Phase 6)**: Depends on all desired stories being implemented.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on another story.
- **US2 (P1)**: Starts after Phase 2; can proceed in parallel with US1.
- **US3 (P2)**: Starts after US1; can proceed in parallel with US2.

### Parallel Opportunities

- After T001-T003, T004-T006 can be implemented in parallel because they cover separate test
  files and acceptance surfaces.
- T008 and T009 can proceed in parallel after T007; they update separate workflows.
- T010-T012 are independent of US1 implementation and can proceed alongside US1.
- After US1, T013-T015 can be prepared in parallel; T016-T017 follow their completion.
- US2 can proceed in parallel with US1, and US3 can proceed in parallel with US2 once US1 is done.

## Parallel Examples

### User Story 1

```text
T004: Mapping projection tests in tests/integration/test_catalog_workflows.py
T005: Discovery scope and reset tests in tests/app/test_discovery.py
T006: Industry Deep-Dive scope tests in tests/app/test_industry_discovery.py
```

### User Story 2

```text
T010: Candidate CSV structural validation in tests/contract/test_us_catalog_input.py
T011: Dual-classification CLI lifecycle tests in tests/contract/test_catalog_cli.py
T012: Reviewer instructions in docs/markets/US/README.md
```

### User Story 3

```text
T013: yFinance batch normalization tests in tests/unit/infrastructure/test_market_data_providers.py
T014: Per-mapping history-state tests in tests/integration/test_discover_sectors.py and tests/app/test_discovery.py
T015: Opt-in live retrieval coverage in tests/live/test_us_catalog_etf_retrieval.py
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Setup and Foundational scope resolution.
2. Complete User Story 1 and validate it with the synthetic reviewed multi-classification release.
3. **Stop and validate** the Discovery workflows independently before starting the other stories.
4. Do not activate the supplied candidate data as part of this MVP; publication remains gated on
   complete review evidence and companion artifacts.

### Incremental Delivery

1. Complete Setup and Foundational phases.
2. Deliver US1 for scope-safe Discovery and all ETF mapping options.
3. Deliver US2 for candidate-data structural checks and reviewer release guidance.
4. Deliver US3 for per-symbol history states and the opt-in live validation.
5. Complete responsive browser checks and repository quality gates.

## Notes

- The existing release-v2 format already supports custom classifications and the required ETF
  artifact roles; do not introduce a catalog-v3 schema or a second runtime loader.
- `docs/markets/US/` remains an authoring location. Tests must not equate resolvable references
  with reviewed approvals or modify the supplied CSV files.
- Exact provider symbols and the existing yFinance request path remain authoritative; no provider
  fallback or ticker reconstruction is permitted.
