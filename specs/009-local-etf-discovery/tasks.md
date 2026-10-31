---
description: "Executable tasks for local ETF mapping discovery"
---

# Tasks: Local ETF Mapping Discovery

**Input**: Design documents from `specs/009-local-etf-discovery/`.

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [CLI contract](./contracts/local-etf-review-cli.md), and [quickstart.md](./quickstart.md).

**Tests**: Included to implement the specification's independent tests and SC-001 through SC-007, following the constitution's tests-first gate. Write each test batch and confirm failures before its implementation; at each checkpoint, run the focused tests and require them to pass.

**Organization**: Three story increments after shared fixture and migration prerequisites. Feature key is `009-local-etf-discovery`; actual Git branch remains `main`. This artifact does not authorize commits, branch switching, production database upgrades, or source-project execution.

## Format: `[ID] [P?] [Story] Description`

- All tasks begin with an unchecked checkbox and sequential task ID.
- `[P]` identifies different-file work that can run together once its listed prerequisites are complete; it does not waive dependencies.
- `[US1]`, `[US2]`, and `[US3]` map to the specification's stories.
- Paths are relative to the repository root. Extend existing modules and fixtures; do not replace unrelated dirty-worktree changes.
- Reuse Python 3.12, pytest, Ruff, strict Pyright, argparse, SQLite, and standard-library parsing. No new dependencies, service, provider, alias subsystem, UI, or recursive scanner.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish deterministic, local-only evidence and reviewed test data without changing the user's resources or database.

- [X] T001 Create synthetic catalogs under `tests/fixtures/local_etf_discovery/` using the contract's four resource aliases and default file/catalog names; include annotated/unannotated assignments, Unicode labels, exchange suffixes, identical/conflicting duplicate keys, empty catalogs, context declarations, unsupported expressions, private-value and execution sentinels, and a missing stockviewer scenario. Add `tests/fixtures/local_etf_discovery/listings.csv` in the existing reviewed import format with test-only source approval, verified SOXX/SMH listings, active industry/sub-industry nodes, an uncovered node, and distinct classification scopes; record exact expected occurrence counts in the fixture descriptions.
- [X] T002 Extend `tests/conftest.py` with opt-in fixture helpers that copy T001 resources into `tmp_path`, inject a UTC observation clock and root overrides, initialize isolated databases, and reuse the existing representation fixture/import boundary. Provide scoped network/side-effect guards and fixture mutation helpers; do not add global behavior that changes unrelated tests or depend on user-owned paths.

**Checkpoint**: Controlled fixtures are ready; no project imports, remote calls, production writes, or new dependencies occurred.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide the single schema-3 migration boundary required by all story increments.

- [X] T003 Add failing migration/integrity tests in `tests/integration/test_local_etf_discovery.py` for fresh initialization, supported schema 1/2 upgrades, repeated initialization, unknown-version rejection before writes, and injected DDL/version failure rollback. Assert existing hierarchy, sources, listings, ETF/basket evidence, memberships, and universe revision survive; verify foreign keys, unique keys, and status/decision constraints.
- [X] T004 Extend `src/market_leadership/infrastructure/region_database.py` to schema 3 through the existing migration chain, atomically creating exactly `etf_collection_runs`, `etf_mapping_evidence`, `etf_collection_evidence`, `etf_candidate_reviews`, `etf_review_evidence`, and `etf_representation_provenance` with the data model's fields. Enforce "composite primary key with foreign keys" for collection/evidence membership, "Enforce foreign keys, unique membership/provenance keys, valid statuses, and non-empty decisions", and "Upgrade supported schema 1/2 atomically, retaining existing rows/revisions; reject unknown versions." Avoid `executescript` transaction auto-commit; keep all SQLite ownership in RegionDatabase and pass T003 without creating sources/listings or changing revision on migration.

**Checkpoint**: Schema 3 initializes/upgrades atomically and retains feature 008 data. All stories depend on T004 passing.

## Phase 3: User Story 1 - Collect Local ETF Mapping Evidence (Priority: P1, MVP)

**Goal**: Produce a persisted, reviewable, provenance-complete local candidate inventory with honest resource outcomes.

**Independent Test**: On controlled catalogs and one missing root, recover 100% of supported occurrences, including duplicates and precise locations; report all four resources and partial exit 2. On complete empty inputs, return complete exit 0; on all failed inputs, return failed exit 2. Unchanged recollection reuses candidate/evidence identities and produces no manual decisions, approvals, source mutations, or network calls.

### Tests for User Story 1

- [X] T005 [P] [US1] Add failing identity/grouping tests in `tests/unit/test_local_etf_evidence.py` for exact original labels, normalized ticker lookup with suffix preservation, null-versus-declared scope, cross-project grouping only for identical identity tuples, separately retained duplicate occurrences, deterministic ordering, location-only movement, and hashes unaffected by unrelated private/configuration values.
- [X] T006 [P] [US1] Add failing static-reader tests in `tests/unit/test_local_etf_sources.py` for the complete accepted/rejected grammar, top-level single-name Assign/AnnAssign only, source encoding, every original AST dictionary occurrence, named context handling, partial sibling retention, missing/unreadable/syntax-invalid catalogs, unsupported catalog names, and root correction. Assert file reads are bounded to one per selected file, traversal/symlink escapes fail, execution/network/write sentinels remain untouched, and diagnostics never expose private values or `SyntaxError.text`.
- [X] T007 [P] [US1] Add failing `collect-etf-candidates` contract tests in `tests/contract/test_local_etf_discovery.py` for root/catalog argument grammar, all four aliases in the manifest, deterministic `local-etf-discovery-1` JSON fields, stdout/stderr separation, complete/partial/failed and legitimate-empty exits, uninitialized/old database errors, and explicit persistence failures rather than success-shaped reports.
- [X] T008 [P] [US1] Extend `tests/integration/test_local_etf_discovery.py` with failing persisted collection tests asserting 100% occurrence/location recovery, cross-source duplicate provenance, immutable evidence reuse and run memberships, partial research retention, complete-baseline comparisons, and zero research-only changes to approved tables/revision. Include changed/removed/unknown support, source recovery, location-only movement, unrelated private edits, and atomic collection rollback.

### Implementation for User Story 1

- [X] T009 [US1] Create immutable collection/evidence records in `src/market_leadership/domain/local_etf_evidence.py`. Preserve the run constraints verbatim: "Unique inspection attempt; timestamps are not candidate identity", "Injected UTC observation clock", "`complete`, `partial`, or `failed`", "All four aliases, canonical roots, requested descriptors and outcomes", and "File/catalog identity, completeness, content identity, counts, bounded diagnostics". Implement resource statuses "`inspected`, `inspected_with_issues`, `missing`, `inaccessible`, `unsupported`". Preserve evidence constraints: "Deterministic source/catalog-snapshot/declaration/location identity", "Grouping identity for industry declarations; context occurrences are distinguishable", "Resource alias, canonical root, relative file, catalog name", "Hash of extracted declarations/allowed metadata, excluding unrelated source values", "Exact decoded literals; no taxonomy rewrite", "Trimmed/uppercase lookup form; retain suffixes and original string", "`industry`, `sector_context`, `index_context`, `commodity_context`", "Source-declared labels where available; otherwise null", "Distinguishes repeated occurrences, including identical duplicate keys", "One-based start/end lines and AST byte-column offsets", "Literal display/category/sector/index claims and qualification annotations only", "Declaration values/scope and relevant qualification evidence used for currentness", and "Original observation clock; immutable evidence is not overwritten".
- [X] T010 [P] [US1] Implement canonical hashing, grouping, deterministic ordering, and semantic comparison in `src/market_leadership/domain/local_etf_evidence.py` after T009. Apply "Identity is a canonical hash of original label, normalized ticker, declared catalog type, and declared region/classification/node-level labels, with null distinct from any declared value." Keep candidates as projections, every occurrence attributable, same-label/different-ticker choices separate, context ineligible for industry coverage, and taxonomy labels unchanged; separate location/snapshot identity from semantic currentness and include relevant allowed qualification context in fingerprints.
- [X] T011 [P] [US1] Implement the bounded AST/tokenize reader in `src/market_leadership/infrastructure/local_etf_sources.py` after T009 using the contract's exact default roots, industry descriptors, and research-listed context catalogs. Read selected files once, ignore annotations, iterate literal dictionary entries without evaluation, and support only the narrow METAL_PROXIES tuple context. Preserve explicit prefix scope and unknown unqualified scope; reject dynamic/nested/numeric forms and unsafe descriptors, retain supported partial siblings with diagnostics, and exclude unselected/private content. Report missing stockviewer or descriptor-less corrected roots explicitly; sanitize read/parse errors without snippets or broad catches.
- [X] T012 [US1] Add atomic collection/evidence persistence and read accessors in `src/market_leadership/infrastructure/region_database.py` after T010/T011, reusing immutable evidence rows and inserting run memberships idempotently. Persist only permitted fields/context/outcomes, retain complete comparison baselines, and expose safe per-catalog observations for projections. Research writes must not populate sources/listings, modify representations/hierarchy, or increment revision; storage errors must roll back rather than return a successful inventory.
- [X] T013 [US1] Create collection orchestration in `src/market_leadership/application/discover_etf_candidates.py` after T012, accepting explicit roots/descriptors and an injected UTC clock. Combine bounded reads, grouping, persistence, deterministic reports, and changed/removed/unknown comparisons; only complete observation of the same catalog proves removal, while missing/partial/failed input means unknown. Distinguish overall complete/partial/failed including empty catalogs and all-root failure, without treating unrelated missing resources as invalidating complete selected support.
- [X] T014 [US1] Wire `collect-etf-candidates` into `src/market_leadership/universe_admin.py` after T013 with the exact optional database/root/catalog arguments and JSON report fields from the contract. Emit versioned JSON only on stdout and actionable diagnostics on stderr; use exit 0 for complete and exit 2 for partial/failed/domain/storage errors. Require initialized schema 3 and leave existing administration/Discovery flows free of implicit collection.
- [X] T015 [US1] Run the focused US1/migration tests in `tests/unit/test_local_etf_evidence.py`, `tests/unit/test_local_etf_sources.py`, `tests/contract/test_local_etf_discovery.py`, and `tests/integration/test_local_etf_discovery.py` with the existing pytest runner, and fix feature-related failures until SC-001/SC-002 and the collection portions of SC-004/SC-006 pass. Demonstrate a persisted useful partial inventory with a missing root and zero source-project execution, remote requests, approvals, or duplicate evidence.

**Checkpoint**: Collection is independently useful research. Stop here for the MVP; candidates do not count as approved coverage.

## Phase 4: User Story 2 - Reconcile Candidates Against Reviewed Classifications (Priority: P2)

**Goal**: Compare all local alternatives against every active exact hierarchy node without inferred aliases, source-order winners, or proxy substitution.

**Independent Test**: A reviewed hierarchy with an industry, sub-industry, and uncovered node retains 100% of its active rows and separate approved status. SOXX/SMH alternatives, unmatched provider labels, unknown/different scope, and sector/index/commodity/thematic claims remain visible. Seed explicit review records in isolated fixtures to verify reviewed binding/selection projections without requiring US3's write CLI.

### Tests for User Story 2

- [X] T016 [P] [US2] Extend `tests/unit/test_local_etf_evidence.py` with failing reconciliation/qualification/selection projection tests: spelling/case/whitespace/punctuation is provisional rather than reviewed equivalence; exact region/classification/node binding does not propagate; source order never chooses a ticker; caret/non-ETF claims are ineligible and other known proxy/scope claims remain warnings. Test all candidate/selection state enums, accepted/rejected event order, changed/removed/unobservable support, original alternatives resolved by explicit selection versus later new conflicts, and unchanged line-only movement.
- [X] T017 [P] [US2] Extend `tests/integration/test_local_etf_discovery.py` with failing coverage tests asserting 100% active industry/sub-industry rows, no-candidate gaps, separate ETF/basket/not-covered/invalid status, unbound and other-scope candidates, and no approved-coverage increase. Use isolated persisted review/evidence fixtures to test exact reviewed equivalences, historical run viewing, latest supporting observation timestamps, and unrelated missing roots without relying on US3 command availability.
- [X] T018 [P] [US2] Extend `tests/contract/test_local_etf_discovery.py` with failing `review-etf-candidates` tests for required region/classification/as-of, optional historical run/database, invalid scope/date/run errors, every hierarchy row, unbound candidates, conflict/qualification states, review selections, resource issues, and explicit observation times. Assert read commands do not rescan files, poll, invoke providers, or mutate database/revision.

### Implementation for User Story 2

- [X] T019 [US2] Implement pure reconciliation, qualification, ordered-selection, and currentness projections in `src/market_leadership/domain/local_etf_evidence.py`. Preserve the model's states "`needs_classification_reconciliation`, `needs_suitability_review`, `conflicting_evidence`, `reviewer_accepted`, `reviewer_rejected`", node state "`no_candidate`", independent approved status "`etf`, `basket`, `not_covered`, or `invalid`", and selected status "`none`, `accepted_current`, `accepted_needs_re_review`". Accept only explicit reviewed equivalences for exact logical label/scope and target identities; preserve alternatives, prohibit known index/non-ETF promotion and parent substitution, derive observability from per-catalog manifests, and flag later new/changed conflicts rather than permanently blocking a selection on alternatives already reviewed.
- [X] T020 [US2] Add read-only review/event/evidence query support in `src/market_leadership/infrastructure/region_database.py` after T019, exposing ordered manual history, selected support, referenced runs, and latest relevant observations without creating a candidate/alias table. Validate requested scope/date and retain unknown/historical evidence; keep database reads distinct from filesystem collection and preserve all approved statuses/revision.
- [X] T021 [US2] Extend `src/market_leadership/application/discover_etf_candidates.py` after T020 to reconcile inventories against the existing `representation_worklist` boundary in `src/market_leadership/application/industry_representations.py`. Return every active reviewed node plus separate unbound candidates, provisional matches, exact reviewed bindings, conflicts, qualifications, and selected-review currentness; support historical run inspection while clearly displaying the latest persisted supporting observation used for currentness, never implying real-time verification.
- [X] T022 [US2] Wire `review-etf-candidates` into `src/market_leadership/universe_admin.py` after T021 with the contract's exact region/classification/as-of and optional run/database arguments, versioned JSON, and explicit error exits. Do not infer unknown source scope from CLI scope, omit uncovered nodes, choose a source-order winner, or alter existing approval/momentum behavior.
- [X] T023 [US2] Run focused reconciliation/read-contract/coverage tests in `tests/unit/test_local_etf_evidence.py`, `tests/contract/test_local_etf_discovery.py`, and `tests/integration/test_local_etf_discovery.py`, fixing feature-related failures until SC-003 and reconciliation portions of SC-004 pass. Verify both ETF alternatives and their occurrences remain reviewable, every active hierarchy node retains approved status, and no read triggers collection or approval.

**Checkpoint**: Reviewers can compare conflicts and gaps without searching each source project. US1 remains unchanged; suitability decisions and approved mappings are still separate.

## Phase 5: User Story 3 - Promote Reviewed Evidence Through Existing Approval (Priority: P3)

**Goal**: Record exact manual research decisions and attach current accepted evidence within the existing governed ETF approval transaction.

**Independent Test**: Collect, compare, explicitly select a candidate for a verified test ETF, and approve it with retained node/listing/date/review/source provenance. Invalid confirmations, scope, instrument identity, listing/source approval, dates, stale support, or link insertion fail without mutation. Recollection/rejection/change never overwrites an existing ETF/basket or resurrects an old selection.

### Tests for User Story 3

- [X] T024 [P] [US3] Extend `tests/unit/test_local_etf_evidence.py` with failing decision/approval-eligibility tests for exact candidate/target/as-of, non-empty reason/reference and supporting set, three acceptance confirmations, applicable non-empty warning resolutions, and known non-ETF rejection. Cover explicit accept/reject event transitions, unknown source scope requiring assessment without rewriting evidence, partial-baseline selections requiring an explicitly reviewed complete occurrence before promotion, complete-support recovery, and root/semantic/new-conflict changes requiring re-review.
- [X] T025 [P] [US3] Extend `tests/integration/test_local_etf_discovery.py` with failing manual-review/provenance tests for evidence belonging to the candidate and referenced run, exact active node at explicit hierarchy date rather than observation date, immutable event/link history, unchanged-collection zero decisions, and selection clearing without fallback. Test end-to-end valid approval, wrong node/ticker/listing/source/reference/interval, changed/removed/unknown/partial support, unrelated missing roots, location-only changes, currentness checks inside the write transaction, idempotent mapping/link attachment, and injected link-failure rollback of mapping/provenance/revision; preserve prior approval evidence.
- [X] T026 [P] [US3] Extend `tests/contract/test_local_etf_discovery.py` with failing `review-etf-candidate` and optional `approve-etf --candidate-review-id` tests for every required argument, evidence/issue-resolution repetitions, accept-only confirmations, explicit as-of, versioned decision JSON, success/error exits, and invalid review IDs. Verify no-flag ETF approval and existing representation/listing/basket commands keep feature 008 behavior and never trigger collection.

### Implementation for User Story 3

- [X] T027 [US3] Add manual decision records and validation to `src/market_leadership/domain/local_etf_evidence.py`, preserving the review constraints verbatim: "Unique explicit manual decision; insertion order identifies later reviewer decisions", "Must identify a persisted industry candidate", "Exact active reviewed target; sub-industries use existing industry node IDs", "Explicit hierarchy date selected by the reviewer; independent of the source observation clock", "Inspection used for this decision", "`accept` or `reject`; never created automatically by collection", "Non-empty classification/suitability rationale and actual review reference", "Acceptance requires ETF identity, exact classification/region scope, industry suitability", "Explicit reviewed rationale for applicable proxy/scope warnings", and "Injected decision clock". Enforce the explicitly selected "non-empty set of supporting occurrences" that "must belong to the candidate and referenced run"; distinguish suitability acceptance from listing/source approval and prohibit known index/non-ETF promotion.
- [X] T028 [US3] Implement atomic append-only candidate-review and review/evidence writes in `src/market_leadership/infrastructure/region_database.py` after T027, validating persisted candidate/run/occurrence consistency and exact active hierarchy scope at the requested as-of date. Keep reason/reference/confirmation/issue evidence immutable, use insertion order for decisions, and never create reviews during collection, approvals/listings/sources during review, or universe-revision increments for research.
- [X] T029 [US3] Extend `src/market_leadership/application/discover_etf_candidates.py` after T028 with explicit accept/reject orchestration and returned selected-review state using T019 projections. Acceptance selects one candidate for the exact node while retaining alternatives/history; rejection of the selected candidate clears it without restoring older acceptance, and other rejections leave the selection intact. Re-review must be explicit for changed scope/semantics/root or new conflicts; currentness is based only on displayed persisted observations, with unknown support distinct from proven removal.
- [X] T030 [P] [US3] Wire `review-etf-candidate` into `src/market_leadership/universe_admin.py` after T029 with all contract arguments, required explicit hierarchy as-of, selected evidence IDs, accept-only ETF/scope/suitability confirmations, and applicable `ISSUE=RATIONALE` resolutions. Return the exact target, review ID, decision, support, confirmations/resolutions, and selected state as versioned JSON; surface domain/storage errors and never fabricate approval prerequisites.
- [X] T031 [P] [US3] Extend `RegionDatabase.add_entity_representation` in `src/market_leadership/infrastructure/region_database.py` after T028/T029 with optional candidate-review validation and provenance attachment inside its existing `BEGIN IMMEDIATE` transaction. Require the current exact-node accepted selection, complete semantically current support with an explicitly reviewed complete supporting occurrence, matching verified listing/provider ticker, and all qualifications resolved; reuse every existing source/reference/listing/hierarchy/interval/overlap check. Apply "Composite representation/review primary key, with foreign keys to representation, review, and current approval inspection." Insert mapping and provenance atomically, including the existing idempotent-return path; additional links are append-only, deterministic mapping identity is unchanged, metadata-only links do not increment revision, and failures roll back mapping/link/revision together.
- [X] T032 [US3] Add optional `--candidate-review-id` to existing `approve-etf` handling in `src/market_leadership/universe_admin.py` after T031, passing it into the same approval boundary without duplicating validators or collecting sources. Preserve existing no-flag arguments, outputs, errors, and feature 008 commands; provenance-linked failures must identify missing/currentness prerequisites explicitly and leave runtime representations unchanged.
- [X] T033 [US3] Run governed-promotion/end-to-end tests in `tests/unit/test_local_etf_evidence.py`, `tests/contract/test_local_etf_discovery.py`, `tests/integration/test_local_etf_discovery.py`, `tests/unit/test_universe_admin.py`, and `tests/integration/test_industry_representations.py`. Fix feature-related failures until SC-004 through SC-007 pass: every local-derived approval has durable exact provenance, unchanged collection creates zero duplicate candidate/review items, every affected reviewed relationship is identified on change/removal, failed approval rolls back, and a complete collect/compare/select/approve journey requires no manual source-project search.

**Checkpoint**: All stories work end-to-end with existing approval governance intact. Accepted research alone still does not change momentum.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Document the implemented interface/migration and verify all affected consumers without adding unrelated functionality.

- [X] T034 [P] Update `README.md` for the implemented local collection/reconciliation/decision workflow, exact default resources and explicit correction, partial exit 2, research-versus-approved coverage, optional provenance-linked ETF approval, and backup/schema 1/2-to-3 migration and older-application incompatibility. Keep source/listing approvals, no-substitution rules, and test-only evidence restrictions explicit; do not claim a complete hierarchy, automatic suitability, or real-time freshness.
- [X] T035 [P] Reconcile `specs/009-local-etf-discovery/quickstart.md`, `specs/009-local-etf-discovery/contracts/local-etf-review-cli.md`, and `specs/009-local-etf-discovery/data-model.md` with implemented schema/commands and remove future-only status where appropriate. Make controlled validation runnable with fixture root overrides and returned IDs, include explicit review as-of and issue resolutions, and demonstrate repeated collection/change/removal/recovery/rollback without permanent tests depending on real user resources or live market data.
- [X] T036 Execute the automated commands and controlled scenarios in `specs/009-local-etf-discovery/quickstart.md`: focused new/existing reviewer tests, Ruff, strict Pyright, whitespace checks, and the existing `.venv/bin/pytest -q -m 'not live'` regression because shared migration/approval code affects existing consumers. Fix only feature-related failures; verify feature 008 approval and Discovery behavior remain unchanged, record measured SC-001 through SC-007 results in the quickstart validation section, and clean up only task-created test artifacts without upgrading a production database.

**Checkpoint**: Implementation is verified, documented, and persistent; no task is checked complete merely because code exists.

## Dependencies & Execution Order

### Phase and Story Graph

```text
Setup (T001 -> T002)
  -> Foundation (T003 -> T004)
  -> US1 (T005-T015): collection MVP
  -> US2 (T016-T023): exact reconciliation/coverage
  -> US3 (T024-T033): explicit decision and governed promotion
  -> Polish (T034-T036)
```

Stories consume the previous increment's persisted evidence/queries and therefore are not parallel implementation tracks. Each has independently verifiable criteria; US2 read projections can be tested with controlled persisted decisions before the US3 write interface exists.

### Task Prerequisites

| Tasks | Actual prerequisites |
|---|---|
| T001 | None |
| T002 | T001 |
| T003 | T002 |
| T004 | T003 failing tests |
| T005, T006, T007, T008 | T004 and shared fixtures; independent test-authoring files |
| T009 | T005-T008 written and relevant absent-behavior failures confirmed |
| T010, T011 | T009; different-file implementation wave |
| T012 | T004, T010, T011 |
| T013 | T012 |
| T014 | T013, T007 |
| T015 | T005-T014 |
| T016, T017, T018 | T015; independent test-authoring files |
| T019 | T016-T018 written and relevant failures confirmed |
| T020 | T019 |
| T021 | T020, T015 |
| T022 | T021, T018 |
| T023 | T016-T022 |
| T024, T025, T026 | T023; independent test-authoring files |
| T027 | T024-T026 written and relevant failures confirmed |
| T028 | T027 |
| T029 | T028, T019 |
| T030 | T029, T026 |
| T031 | T028, T029, T025 |
| T032 | T030, T031, T026 |
| T033 | T024-T032 |
| T034, T035 | T033; separate documentation files |
| T036 | T033, T034, T035 |

The next phase starts only after its preceding checkpoint passes. An implementation dependency on a test task means the tests are written and their intended failures observed, not that missing functionality already passes.

### Shared-File Rules

- Serialize changes to `src/market_leadership/infrastructure/region_database.py`, `src/market_leadership/universe_admin.py`, and each reused domain/application/test file.
- Do not parallelize story phases or same-file tasks just because their concerns differ.
- T030 and T031 can run together after T029: CLI manual decisions and database ETF provenance touch different files; T032 waits for both.
- Keep existing `tests/unit/__init__.py` namespacing and the existing test runner configuration.
- Do not run proposed future test commands during task generation; they become available during implementation.

## Parallel Examples

### User Story 1

After T004, author T005 domain tests, T006 reader tests, T007 contract tests, and T008 integration tests concurrently in four different files. Confirm intended failures before T009.

After T009, T010 identity/grouping in the domain module and T011 static parsing in the infrastructure module can run together. T012 waits for both.

### User Story 2

After T015, author T016 domain projection tests, T017 database/coverage tests, and T018 CLI read-contract tests concurrently in three different files. Implementation then follows T019 -> T020 -> T021 -> T022 -> T023.

### User Story 3

After T023, author T024 domain decision tests, T025 review/provenance integration tests, and T026 command contract tests concurrently in three different files. After T029, T030 manual-decision CLI and T031 database approval/provenance can run together; T032 waits for both.

### Documentation

After T033, T034 README changes and T035 feature-artifact updates can run together. T036 validates the integrated result.

## Requirement and Outcome Coverage

| Requirement/outcome | Implementing and verifying tasks |
|---|---|
| FR-001, FR-002: four roots, supported bounded catalogs | T001-T002, T006-T007, T011, T014-T015 |
| FR-003: exact evidence/scope/location/content identity | T005, T008-T012, T015 |
| FR-004: local/read-only/private-content exclusions | T001-T002, T006-T008, T011, T013-T015, T036 |
| FR-005: explicit resource/overall outcomes | T007-T009, T011-T015 |
| FR-006: exact grouping and all alternatives/occurrences | T005, T008-T010, T016-T023 |
| FR-007: reviewed exact classification equivalence | T016-T022, T024-T030 |
| FR-008: every active hierarchy row and independent approved status | T017-T023 |
| FR-009: qualification warnings, no inferred approval/identity | T006, T010-T011, T016-T019, T024-T033 |
| FR-010: explicit accept/reject and conflict selection | T016-T023, T024-T030 |
| FR-011: existing approval gates and durable provenance | T024-T026, T027-T028, T031-T033 |
| FR-012: stable recollection, changed/removed evidence, retained history | T005, T008, T010-T015, T016-T023, T024-T033 |
| FR-013: runtime evidence unchanged except explicit valid approval | T003-T004, T008, T012-T015, T017-T023, T025-T036 |
| SC-001: all four roots with honest completeness | T007-T008, T014-T015 |
| SC-002: 100% supported occurrence/location recovery | T005-T008, T015 |
| SC-003: 100% active hierarchy row coverage | T017-T018, T023 |
| SC-004: zero automatic mappings across invalid/unreviewed cases | T008, T015-T018, T023-T026, T033 |
| SC-005: every local-derived approval has exact retained provenance | T025-T026, T031-T033 |
| SC-006: zero duplicate candidate/review items; every affected relationship identified | T005, T008, T015-T017, T024-T025, T029, T033 |
| SC-007: consolidated collect/compare/prepare approval journey | T025-T026, T030-T035 |

## Implementation Strategy

### MVP First: User Story 1

Complete T001-T015 and stop at the persisted collection checkpoint. This delivers useful local research and source diagnostics without requiring classification reconciliation or allowing runtime approval. Missing stockviewer remains an explicit recoverable issue, not a blocker to useful partial research.

### Incremental Delivery

1. Fixtures plus atomic schema upgrade establish the shared boundary.
2. US1 collects immutable evidence and honest complete/partial/failed inventories.
3. US2 adds exact-scope conflict/coverage projections without changing approvals.
4. US3 adds explicit research decisions and optional atomic provenance through existing ETF approval.
5. Polish documents actual migration/interfaces and validates existing consumers.

### Completion Rules

Check a task only after its described outcome is implemented and verified. Preserve historical local and approval evidence, distinguish unknown from removed support, and never silently substitute an older acceptance, parent ETF, generated basket, or provider. No speculative abstractions or unrelated cleanup.
