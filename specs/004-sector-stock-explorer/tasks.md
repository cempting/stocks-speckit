# Tasks: Sector-to-Stock Explorer

**Input**: Design documents from `/specs/004-sector-stock-explorer/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/progressive-discovery.md`

**Tests**: Test tasks are included because the project constitution requires tests first and the plan defines automated acceptance evidence. Each test task must demonstrate the absent behavior before its implementation task begins.

**Organization**: Tasks are grouped by the three prioritized user stories. The feature extends the existing Python/Streamlit application; no new dependencies or project initialization are needed.

## Phase 1: Setup

**Purpose**: Project initialization

No setup tasks are needed. Python dependencies, test runners, and the two-tab Streamlit entrypoint already exist.

## Phase 2: Foundational

**Purpose**: Blocking prerequisites shared by all user stories

No new project-wide framework or persistence layer is required. Stable selection, peer-score calculation, and chart evidence are scoped to their first consuming user story below.

## Phase 3: User Story 1 - Explore Market Leadership by Hierarchy (Priority: P1) 🎯 MVP

**Goal**: Show exactly the sector, industry, or member-stock tape appropriate to the user's current hierarchy selection, without stale child rows.

**Independent Test**: With a controlled sector/industry/member catalog, verify the initial sector-only view, each selection transition, all industry members, and child-selection invalidation after a parent change.

### Tests for User Story 1

- [X] T001 [P] [US1] Add unit tests for initial, valid, and invalid parent/child selection transitions in `tests/unit/domain/test_progressive_selection.py`; verify sector changes clear invalid industries and stocks and industry changes clear invalid stocks.
- [X] T002 [P] [US1] Add AppTest cases for sector-only, sector-to-industry, industry-to-all-members, and stale-row removal behavior in `tests/app/test_sector_stock_explorer.py`.

### Implementation for User Story 1

- [X] T003 [US1] Implement typed progressive selection and parent/child reconciliation in `src/market_leadership/domain/progressive_selection.py` after T001; preserve valid stable IDs, and clear only invalid descendants when the parent changes.
- [X] T004 [US1] Update `src/market_leadership/ui/workflows/discovery_page.py` after T002/T003 to render only sectors with no selected sector and only the selected sector's industries after sector selection; retain the existing two-tab entrypoint.
- [X] T005 [US1] Connect selected industry to the reviewed catalog in `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/infrastructure/stock_membership.py` after T004; show all active member identities and explicit catalog errors/empty states, never stale or fabricated rows.
- [X] T006 [US1] Wire sector, industry, and stock selections through stable identifiers and clear invalid dependent widget state before widgets are rendered in `src/market_leadership/ui/workflows/discovery_page.py` after T003/T005; preserve valid hierarchy state on ordinary reruns.

**Checkpoint**: The user can traverse the hierarchy and see the correct complete member set independently of chart thumbnails and score availability.

## Phase 4: User Story 2 - Compare Sector, Industry, and Stock Evidence (Priority: P1)

**Goal**: Add row-specific chart thumbnails and stock identity, price, and the existing Quality, Growth, and Cash Flow peer scores.

**Independent Test**: Use controlled sector, industry, and stock histories plus a complete peer cohort; verify each chart belongs to its row, every active member is present, scores match the 001 contract, and missing evidence is explicit.

### Tests for User Story 2

- [X] T007 [P] [US2] Add tests for exact peer percentiles, shared tie ranks, all-equal peers, five-valid-peer minimum, required two-metric block completeness, invalid denominators, and cutoff insufficiency in `tests/unit/domain/test_peer_scores.py`; assert formulas against `specs/001-market-leadership-screener/contracts/fundamental-scoring.md`.
- [X] T008 [P] [US2] Add UI component tests in `tests/unit/ui/test_progressive_tape.py` proving sector/industry/stock thumbnails use their own row's series and stock rows show ticker, name, price, three score states, and explicit missing evidence.
- [X] T009 [P] [US2] Add provider/cache integration tests in `tests/integration/test_stock_evidence.py` proving only the selected industry's active symbols are requested, the full eligible peer cohort is scored before display filtering, explicit score-load intent is required, successful cache entries are reused, and failed/unknown evidence is not treated as a successful empty result.

### Implementation for User Story 2

- [X] T010 [US2] Implement pure peer block score calculation in `src/market_leadership/domain/peer_scores.py` after T007, following `specs/001-market-leadership-screener/contracts/fundamental-scoring.md`; use the complete eligible industry cohort before technical filters, display selection, paging, or sorting, require `N >= 5` for each metric and both metrics per block, rank exact unrounded values, and never produce an overall score.
- [X] T011 [US2] Add an industry-scoped member-history request in `src/market_leadership/application/load_stock_history.py` and cache successful results through `src/market_leadership/ui/cache.py` after T009; request only active member symbols, preserve requested/observed session and source, and retain per-symbol unavailable states without substituting another symbol's history.
- [X] T012 [US2] Adapt verified fundamental evidence for peer scoring in `src/market_leadership/domain/fundamentals.py` and `src/market_leadership/infrastructure/yfinance_fundamentals.py` after T009/T010; use only required dated facts available at the analysis cutoff, and represent unknown publication vintage, market-cap date, denominator, or required fact as insufficient rather than estimating it.
- [X] T013 [US2] Add complete-industry score orchestration in `src/market_leadership/application/score_industry.py` after T010/T012; load eligible cohort evidence through the existing `src/market_leadership/bootstrap.py` loader and cache, compute all three blocks before any display filtering, and return explicit per-stock missing, insufficient, and failure reasons.
- [X] T014 [US2] Add first-column entity-specific chart thumbnails and the stock row fields in `src/market_leadership/ui/components/progressive_tape.py` after T008/T011/T013; render ticker, name, latest valid price, and three peer scores or explicit unavailable states (each available block score is a finite value from 0 to 100), and never reuse a parent or sibling chart.
- [X] T015 [US2] Integrate scoped history, explicit score-load action, and progressive tape rendering in `src/market_leadership/ui/workflows/discovery_page.py` after T006/T009/T014; selecting/sorting a tape must not trigger financial retrieval, and display all active members even when their price or score evidence is missing.

**Checkpoint**: Sector and industry tapes show their own chart thumbnails; the stock tape includes every active member, its own chart, ticker, name, price, and available peer scores.

## Phase 5: User Story 3 - Inspect an Individual Stock (Priority: P2)

**Goal**: Open a detail view for the selected stock with that security's price, volume, 50/150-session moving averages, and the same peer scores.

**Independent Test**: Select a known stock ID, verify the detail view keeps the correct security identity and chart values, mark insufficient series explicitly, then return to the same valid sector and industry context.

### Tests for User Story 3

- [X] T016 [P] [US3] Add controlled-history tests for price, volume, 50-session and 150-session simple averages, and per-series insufficiency in `tests/unit/domain/test_stock_chart.py`; assert the averages use exactly 50 and 150 completed sessions.
- [X] T017 [P] [US3] Add AppTest coverage for opening the selected stable stock identity, displaying matching scores, missing chart/score evidence, and returning to the prior valid hierarchy context in `tests/app/test_stock_detail.py`.

### Implementation for User Story 3

- [X] T018 [US3] Implement stock chart evidence calculation in `src/market_leadership/domain/stock_chart.py` after T016; compute simple moving averages from the stock's own completed history, use exactly 50 and 150 observations, and expose an explicit unavailable state for each insufficient series (insufficient history is represented per series, not as zero or a fabricated chart).
- [X] T019 [US3] Implement the detailed stock view in `src/market_leadership/ui/components/stock_detail.py` after T017/T018; identify the stock by stable instrument ID with ticker/name labels, render price, volume, both moving averages, the same three peer scores, and separate unavailable/insufficient evidence states.
- [X] T020 [US3] Wire stock-row activation, detail return, and context preservation in `src/market_leadership/ui/workflows/discovery_page.py` after T015/T017/T019; reject invalid/stale stock IDs and clear only the stock detail selection on return.

**Checkpoint**: The selected member opens its own chart and matching scoreboard, and the user can return without reselecting a valid sector or industry.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Keep validation guidance accurate and verify the feature against its acceptance evidence.

- [X] T021 [P] Update `specs/004-sector-stock-explorer/quickstart.md` to include `tests/unit/ui/test_progressive_tape.py`, `tests/unit/domain/test_stock_chart.py`, and `tests/app/test_stock_detail.py` in focused validation and retain the documented end-to-end outcomes.
- [X] T022 Run the feature validation in `specs/004-sector-stock-explorer/quickstart.md`, then run `uv run ruff check src/market_leadership tests`, `uv run pyright`, and `uv run pytest -m "not live"`; resolve feature-caused failures without weakening existing checks.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependency changes or initialization are needed.
- **Foundational (Phase 2)**: No separate cross-feature foundation is needed; user-story-owned prerequisites are implemented with their first consumer.
- **User Stories**: US1 precedes US2 because the evidence tapes need the hierarchy and selected member set. US2 precedes US3 because the detail view reuses stock history and peer scores. US3 therefore depends on US1 and US2.
- **Polish (Phase 6)**: Depends on all desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts immediately; no dependency on another feature story.
- **US2 (P1)**: Depends on US1's valid sector/industry/member selections and validated membership (T001-T006).
- **US3 (P2)**: Depends on US1's member identities and US2's row history, chart evidence, and peer scores (T001-T015).

### Within Each User Story

- Write the listed tests before implementing their behavior and confirm they fail for the missing feature.
- Domain validation and calculations precede their application/UI integrations.
- AppTest tasks may be developed alongside unit tests only when they use separate files.
- Do not parallelize tasks that edit the same source file; in particular, Discovery workflow integrations T004, T005, T006, T015, and T020 must be applied in sequence.

### Parallel Opportunities

- **US1**: T001 and T002 can be prepared in parallel; T003 follows T001; T004 follows T002/T003; T005 follows T004; T006 follows T003/T005.
- **US2**: T007, T008, and T009 can be prepared in parallel. T010 follows T007; T011 follows T009; T012 follows T009/T010; T013 follows T010/T012; T014 follows T008/T011/T013; T015 follows T006/T009/T014.
- **US3**: T016 and T017 can be prepared in parallel. T018 follows T016; T019 follows T017/T018; T020 follows T015/T017/T019.
- **Polish**: T021 can proceed independently of implementation; T022 follows all implementation and documentation tasks.

## Parallel Examples

### User Story 1

```text
Task: T001 Add selection-transition unit tests in tests/unit/domain/test_progressive_selection.py
Task: T002 Add hierarchy AppTest cases in tests/app/test_sector_stock_explorer.py
```

### User Story 2

```text
Task: T007 Add peer-score formula tests in tests/unit/domain/test_peer_scores.py
Task: T008 Add tape-rendering unit tests in tests/unit/ui/test_progressive_tape.py
Task: T009 Add stock-evidence integration tests in tests/integration/test_stock_evidence.py
```

After T009 and T010:

```text
Task: T011 Add scoped member-history loading in src/market_leadership/application/load_stock_history.py
Task: T012 Adapt verified facts for scoring in src/market_leadership/domain/fundamentals.py and src/market_leadership/infrastructure/yfinance_fundamentals.py
```

### User Story 3

```text
Task: T016 Add moving-average unit tests in tests/unit/domain/test_stock_chart.py
Task: T017 Add stock-detail AppTest cases in tests/app/test_stock_detail.py
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T006.
2. Verify hierarchy states and membership transitions with the focused selection and AppTest cases.
3. Stop at the US1 checkpoint: users can progress from sectors to industries to all contained stock identities, without chart/score enhancements.

### Incremental Delivery

1. Deliver US1 and verify its independent selection journey.
2. Deliver US2 after US1; prove chart identity, complete member coverage, and contract-compliant or explicitly insufficient peer scores.
3. Deliver US3 after US2; prove stock-specific chart evidence and round-trip context.
4. Run all validation commands in the quickstart after the desired stories are complete.

## Notes

- Every task uses the required `- [ ] T### [P?] [US#?] description with file path` format.
- `[P]` appears only where tasks can edit different files without waiting on incomplete work.
- The stock tape and detail view display the existing three peer block scores, not the current eight raw quarterly metrics as a substitute and not a new aggregate.
- User-facing score values remain unavailable unless the peer contract's inputs, cutoff, and cohort requirements are demonstrated by evidence.
