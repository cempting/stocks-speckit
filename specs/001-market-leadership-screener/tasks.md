# Tasks: Technical Screening and Component Score Definitions

**Input**: [spec.md](spec.md), the active reconciliation in [plan.md](plan.md),
[quickstart.md](quickstart.md), and [contracts](contracts/).
**Reconciled**: 2026-11-06. Documentation only; no new implementation is claimed.

## Scope and Preserved Evidence

[The consolidated ledger](../task-history.md) preserves T001-T098 and links original
completed evidence in Git. All 50 formerly unchecked historical tasks
are superseded, not completed. New IDs start at T099; do not renumber or reopen
historical completed work, or infer acceptance of current requirements from it.

001 owns technical predicates, adaptive consolidation and component-score formulas.
004 owns live progressive navigation/returns, 006 owns the five-column table,
008 owns representations, 010/012 own catalog and membership safeguards, 011 owns
issuer evidence/warnings, 014 owns methodology evaluation and score interpretation,
and 015 owns lookup placement. No new tab, provider, catalog authority or runtime
mode is authorized by this backlog.

Pure shared code lives in `packages/market-data/src/market_data/`; application,
provider and UI code stays in `src/market_leadership/`. New screening/consolidation
modules below are deliberate planned additions. Reuse existing implementations
when they meet the exact requirement; add failing tests before changing behavior.

## Phase 1: Baseline and Contract Reconciliation

- [ ] T099 Validate the current feature-001 formulas and heuristic against `specs/001-market-leadership-screener/contracts/fundamental-scoring.md`, `contracts/consolidation.md`, and `contracts/market-data-provider.md`; run affected existing tests, record baseline results in `specs/001-market-leadership-screener/quickstart.md`, and distinguish already-satisfied behavior, missing behavior and source limitations. Preserve 010/012 version boundaries and 013's pinned-context contract on adoption; do not activate or migrate real catalogs.

## Phase 2: Technical Criteria and Complete Member Access (US2)

- [ ] T100 Add failing tri-state/AND and boundary tests in `tests/unit/domain/test_screening.py` for optional criteria, no criteria, strict SMA50/SMA150 equality, short histories, ending-close inclusion, preceding-only volume means, exact 2x/20-session defaults, invalid parameters and missing/nonpositive baselines; include all matching members beyond one page and assert filtering cannot change the eligible peer cohort.
- [ ] T101 Implement or reuse pure predicates in `packages/market-data/src/market_data/domain/screening.py`, with explicit pass/fail/insufficient reasons and complete member inclusion under 001 FR-009-FR-013; keep acquisition, UI and session state outside the shared domain.
- [ ] T102 Add failing parent/date/revision/filter transition and complete-member tests in `tests/app/test_sector_stock_explorer.py` and `tests/app/test_grading_actions.py`; verify stable IDs, session isolation, selection-only interaction, sorting/pagination without top-N loss, exact reviewed membership, and no score/history requests from ordinary filtering.

## Phase 3: Adaptive Consolidation and Source Evidence (US1/US2)

- [X] T103 Add failing reference tests in `tests/unit/domain/test_consolidation.py` for Wilder ADX/ATR, 150-prior-session warm-up, population-standard-deviation Bollinger bands, the preceding 252-valid-session median, no-spike quiet sessions, maximal runs, 4/5-session and multi-year boundaries, observed high/low corridors, truncation, gaps, no future leakage and current versus preceding versus older interval matching.
- [X] T104 Add failing OHLC/comparable-volume contract tests in `tests/contract/test_runtime_market_data_providers.py` and `tests/integration/test_stock_evidence.py`; verify exact identity/source/date/cache keys, unsupported or incomplete history, targeted refresh failure and compatibility with existing close/volume consumers. Do not infer adjusted highs/lows or comparable volume from unsupported source data.
- [X] T105 Implement the versioned detector and interval evidence in `packages/market-data/src/market_data/domain/consolidation.py` under 001 FR-014-FR-016; preserve the specified heuristic, use each instrument's own observations and distinguish no interval from insufficient data.
- [X] T106 Extend only the required request records, yfinance normalization and cache handoff in `src/market_leadership/application/ports.py`, `src/market_leadership/infrastructure/yfinance_provider.py`, and `src/market_leadership/ui/cache.py`; supply verified detector inputs on explicit relevant loads, preserve current listing/issuer/permission gates and legacy response compatibility, and document any changed schema/cache revision in `specs/001-market-leadership-screener/contracts/market-data-provider.md`.
- [ ] T107 Add failing chart/tooltip tests in `tests/unit/ui/test_progressive_tape.py` and `tests/app/test_stock_detail.py` for subtle latest-interval boundaries/shading, explicit older-interval inspection and exact dates, session/calendar duration, bounds/width, ATR, volume, cutoff and truncation; preserve five columns, thumbnail geometry and distinct empty/insufficient states.
- [ ] T108 Wire shared interval evidence through `packages/market-data/src/market_data/domain/stock_chart.py`, `src/market_leadership/ui/components/progressive_tape.py`, and `src/market_leadership/ui/components/stock_detail.py`; do not invent fund-style charts for unsupported baskets or transfer a parent corridor to another instrument.

## Phase 4: Component Formula and Cohort Contracts (US3)

- [ ] T109 Extend `tests/unit/domain/test_peer_scores.py` only for uncovered 001 FR-018-FR-021 cases: six metric definitions, same-cutoff comparable periods/currencies, publication eligibility, five-peer minimum, midranks/ties, both-required equal component weights and explicit insufficiency. Coordinate with 014 T001/T004/T010 rather than duplicating their evaluation cases; record cross-feature evidence in `specs/001-market-leadership-screener/quickstart.md`.
- [ ] T110 Add failing complete-cohort invariance tests in `tests/app/test_score_industry.py` and `tests/integration/test_stock_evidence.py`; technical filters, selected rows and pagination must not change a retained stock's percentiles or cause hidden recollection. Reuse 012's contextual peer contracts and 014's state/provenance work; fix only uncovered formula or cohort defects in `packages/market-data/src/market_data/domain/peer_scores.py` and `src/market_leadership/application/score_industry.py`, without changing approved metric definitions or weights.

## Phase 5: Integration and Explicit Evidence

- [ ] T111 Integrate the predicates and explicit detector evidence into `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/workflows/industry_deep_dive.py`; retain current navigation, mandatory table columns and namespaced state, keep all eligible members accessible, explain insufficiency and clear only invalid descendants. Dedicated lookup remains in 015 and must not gain an inferred default peer industry.
- [ ] T112 Add failing integration/cache regressions in `tests/app/test_grading_actions.py`, `tests/integration/test_fundamental_cache.py`, and `tests/integration/test_stock_evidence.py` for complete cohort loads, unchanged-context zero-repeat calls, TTL expiry, failed refresh, missing/unsupported data and source/revision changes; resolve only feature-caused failures in the affected request/cache/workflow boundaries.
- [ ] T113 Reuse existing detail/tape disclosure surfaces in `src/market_leadership/ui/components/stock_detail.py` and `src/market_leadership/ui/components/progressive_tape.py` for technical/score input units, periods, source, cutoff, peer count and actionable missing/error states; retain historical/non-advice/non-guaranteed-breakout language and 011's separate cash-risk ownership. Verify the corresponding assertions in `tests/app/test_stock_detail.py` and `tests/app/test_discovery.py`.

## Phase 6: Measured Acceptance and Quality Gates

- [ ] T114 Execute and record the controlled browser/user protocol in `specs/001-market-leadership-screener/quickstart.md`: 2,500 loaded stocks, at least 100 filter/sort/selection interactions, visible-update p95 <=2 seconds and zero unchanged-input remote requests; separately measure the specified first-time-user outcomes for SC-001/SC-002/SC-008. Do not replace browser timing or observed user outcomes with helper timing; leave unperformed human/live-rights gates explicitly outstanding.
- [ ] T115 Run the affected offline tests, Ruff and strict Pyright, then the full non-live suite when practical; reconcile results and source/display-rights limitations in `specs/001-market-leadership-screener/quickstart.md`. Preserve existing behavior under 004/006/008/010/011/012/014/015 and 013 on adoption; do not claim implementation or production approval from documentation changes.

## Dependencies and Execution Order

All tasks follow T099. T100 -> T101; T102 gates UI integration.
T103 -> T105; T104 -> T106; T107 + T105 + T106 -> T108.
T109 precedes any formula correction in T110.
T101 + T102 + T108 + T110 -> T111 -> T112 -> T113 -> T114 -> T115.

Test authoring for distinct files may proceed independently after T099. Tasks sharing
provider, cache, detail or tape files are serialized. Cross-feature implementation
must also respect the corresponding 012/014/013 prerequisites; a completed historical
task is not a substitute for an unsatisfied current contract.

## Requirement and Outcome Coverage

IDs in this table belong to current feature 001, not the archived weekly specification.

| Requirement | Tasks or active owner |
|---|---|
| FR-001, FR-002 | 004 FR-001-FR-004/FR-015/FR-024/FR-033; 015 placement |
| FR-003, FR-004 | Retired controls; 010/012 dated membership; T099, T102 |
| FR-005, FR-006, FR-007 | 004 FR-004/FR-029/FR-035/FR-036/FR-038 |
| FR-008 | 008 FR-011-FR-016 |
| FR-009, FR-010 | T100, T102, T110-T111 |
| FR-011, FR-012, FR-013 | T100-T101, T111 |
| FR-014 | T103-T106 |
| FR-015, FR-016 | T103, T105, T107-T108, T113 |
| FR-017 | T102, T111-T112 |
| FR-018, FR-019, FR-020, FR-021 | T109-T110, T112-T113; 012 peer context and 014 evaluation |
| FR-022 | T104, T106, T112 |
| FR-023, FR-024 | T102, T106, T113-T115 |
| FR-025 | T099, T102, T112; 010/012 catalog authority |
| SC-001 | T114; 004 owns momentum/navigation acceptance |
| SC-002 | T100-T102, T111, T114 |
| SC-003 | T100, T103, T109-T112; 004 owns returns/ranks |
| SC-004 | T103, T105, T107-T108 |
| SC-005 | T114 |
| SC-006 | T100, T102, T110-T112 |
| SC-007 | T104, T106, T112 |
| SC-008 | T107-T108, T113-T114 |
