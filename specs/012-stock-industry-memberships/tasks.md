---
description: "Test-first implementation tasks for stock identities and reviewed overlapping industry memberships"
---

# Tasks: Stock Identity and Industry Membership Revision

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).
**Created**: 2026-11-02
**Status**: In progress; implementation and acceptance tasks are checked individually.
**Refinement**: 2026-11-02 approved per-request acquisition accounting, stored
qualitative reuse and listing observation ownership; task IDs/dependencies retained.

**Tests**: Required by the specification and constitution. Add the tests first,
confirm a failure caused by the absent behavior (not merely a missing dependency),
then implement and run the relevant red-to-green group. Use captured synthetic
catalogs, independently simulated review permissions, injected clocks/providers,
and temporary evidence/catalog roots. No production activation, source approval,
network collection, branch creation, or commit is authorized by this task list.

**Organization**: Setup -> foundations -> US1 (P1), US2 (P1), US3 (P2), US4 (P2)
-> cross-cutting validation. Story sections are in priority order, not an instruction
to block independent catalog work on the company-evidence integration.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies disjoint-file tasks with the same completed prerequisite frontier.
  It does not override `Depends on` or authorize concurrent edits of shared files.
- `[US1]` through `[US4]` match specification stories, not feature 011 story numbers.
- Paths are repository-relative; all mentioned new files are deliberate targets.
  Use the existing Python 3.12 environment and tools; no dependency additions.
- `Depends on` lists direct prerequisite tasks. Their transitive dependencies also
  apply. The dependency list, not numeric proximity, determines readiness.
- The final coverage tables identify every FR/SC and each acceptance scenario.

## Path Conventions

Extend `packages/market-data/src/market_data/` for shared catalog/domain/schema code,
`services/market-structure/src/market_data_tools/` for administration and the planned
membership converter, and `src/market_leadership/` for app/cache/UI changes.
Completed paths below preserve original evidence; pending paths target current owners,
not compatibility aliases. Lookup placement follows 015 and all four root workflows
share 013's validated context on adoption; 012 identity/listing/peer safeguards remain.
Extend `tests/unit/`, `tests/contract/`,
`tests/integration/`, and `tests/app/`. Use one small catalog fixture helper at
`tests/membership_helpers.py`, alongside the existing 011 company-evidence helper;
do not create a replacement fixture framework or production seed catalog.

## Phase 1: Setup (Shared Infrastructure)

**Goal**: Protect existing work, establish the baseline, and reconcile shared work
with feature 011 before assigning implementation ownership.

- [X] T001 Record the actual branch/worktree and run the existing baseline selectors from `specs/012-stock-industry-memberships/quickstart.md`; retain measured outcomes and pre-existing failures there, isolate all authoring/evidence paths to temporary roots, and protect active catalogs/settings/approvals and unrelated work. Do not repair unrelated baseline failures.
- [X] T002 Add deterministic v1/v2 release builders and loader/call-counter helpers in `tests/membership_helpers.py`, reusing `tests/conftest.py`; include null CompanyId, unassigned/placeholder instruments, two listings, two share classes, sibling/cross-sector overlap, direct parent-plus-child assertions, empty nodes, inclusive-date boundaries, four-level and beyond-recursion-depth branches, reparenting, original approvals and retained history. Reconcile only the narrow shared task dependencies in `specs/011-company-risk-evidence/tasks.md` as described in the cross-feature ownership table below; preserve unchecked status and broader story gates. Depends on T001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Provide versioned parsing and independent identity projections used by all
stories. This phase does not implement company evidence, arbitrary-depth behavior,
migration preparation, or the new UI.

**Test-first gate**: T003-T004 must fail before their corresponding implementation.
No story implementation begins until T009 confirms foundation readiness.

- [X] T003 [P] Add failing schema/header/version tests in `tests/contract/test_catalog_v2.py` for unchanged entry v1, explicit release v1/v2 dispatch, required `scheme_kind=custom`, one stocks artifact per region with null artifact-level classification fields in v2, exact RowKind/header grammar, unknown fields/formats, duplicate JSON keys/headers, invalid Booleans/dates/currencies and 64 MiB/1 MiB bounds; assert malformed v2 is never retried as v1. Depends on T002.
- [X] T004 [P] Add failing projection/identity tests in `tests/unit/test_catalog_memberships.py`; cover instrument-only rows, multiple listing copies, null IDs, unique RowId and assertion/listing pairings, conflicting repeated metadata, missing/unverified listings, primary/symbol conflicts, and strict v1 single-assignment/rank validation. Require typed immutable instruments, listings and memberships without inventing an unassigned node. Depends on T002.
- [X] T005 Implement frozen instrument, explicit membership and CatalogMember projections in `src/market_leadership/domain/catalog.py`; enforce instrument ID "Stable nonempty security identity; separate share classes differ", region "Exact retained regional identity", CompanyId "Nullable reviewed identifier/hint, not issuer-attachment proof", name "Nonempty display label, not a join key", resolution "identified or placeholder; lookup requires identified", membership identity "Stable logical association identity, shared by listing copies", scope "Exact region/classification/version", instrument "Existing retained instrument", target "One exact non-sector target at any supported depth", period "Inclusive reviewed period covered by hierarchy/classification", source/approval "Valid reviewed source and approval", and review state "reviewed for operational membership"; retain existing Listing fields and conflict checks without relaxing v1. Depends on T004.
- [X] T006 Add the strict v2 manifest resource `src/market_leadership/infrastructure/catalog-manifest-v2.schema.json` and package it in `pyproject.toml`; require release v2/custom classifications and membership_migration role, retaining exact legacy metadata/source fields. Extend `src/market_leadership/infrastructure/catalog-manifest.schema.json` only for the explicitly typed nonoperational migration-report history role needed by restored v1 releases; do not loosen v1 operational data/header rules or accept arbitrary roles. Depends on T003.
- [X] T007 Implement trusted format dispatch and exact v2 stock parsing in `src/market_leadership/infrastructure/catalog_files.py`; enforce "MembershipId, ClassificationId/Version, IndustryId and every membership period/source/approval/review cell must be empty" for RowKind=instrument, require reviewed scoped assertions for RowKind=membership with optional end date/listing, preserve nullable cells and existing captured-byte/hash/path/row diagnostics, and feed v1/v2 policy explicitly to domain validation rather than trusting row-controlled flags. Depends on T005, T006.
- [X] T008 Build independent instrument/listing/membership registries and basic local lookup/listing projections in `src/market_leadership/infrastructure/catalog_files.py`; provide the contract operations for exact regional identities, preserve historical/unassigned identified instruments without membership dependence, return explicit eligibility reasons and all assertion provenance, and retain v1 behavior through shared typed adapters rather than manufacturing a representative sole industry. Adapt the immediately affected `src/market_leadership/infrastructure/stock_membership.py` entry points so existing simple-tree consumers remain usable while later stories add deep/context behavior. Depends on T007.
- [X] T009 Run T003-T004 and affected existing `tests/unit/test_catalog.py`, `tests/unit/test_catalog_files.py`, `tests/contract/test_catalog_files.py` and `tests/integration/test_catalog_workflows.py` selectors; record red-to-green results in `specs/012-stock-industry-memberships/quickstart.md`. Confirm all foundation identity/version checks and unchanged v1 semantics before starting stories. Depends on T008.

**Checkpoint**: A basic valid v2 release can be read into independent typed identities;
v1 remains readable with its original validation; no production catalog is changed.

---

## Phase 3: User Story 1 - Understand a Stock Without Conflating Its Identities (Priority: P1) - MVP

**Goal**: Open retained stock details without requiring an active industry, keep
listing histories distinct, and attach reusable company facts only through the
independently reviewed issuer boundary.

**Independent Test**: Root AppTest plus injected production acquisition/store/cache
composition opens an unassigned stock, an unlisted stock, two share classes with
reviewed common issuer, and two listings. Verify separate histories, independently
eligible evidence, null identifiers and blocked successor/unresolved issuer attachment.
Prove positive stored business-model/moat reuse with separate research permissions,
historical cutoffs and observation-level exclusion of predecessor price/volume.
US2 overlap and US4 migration need not be implemented to exercise this story.

### Tests for User Story 1 (Required)

- [X] T010 [P] [US1] Add failing issuer association/permission/observation, CompanyResearchClaim/research-scope envelope and shared-fact projection cases in `tests/unit/domain/test_company_evidence.py`, reusing the 011 data model; require nullable company/CIK, per-listing dated association identity, independent grants, finite values, original reporting basis/currency/scale/provenance, no guessed common issuer and no shared capitalization/trading currency. Cover scope-independent reattachment without losing acquisition identity; validate stored business_model/competitive_advantage claim topics, kinds, source/qualifications/provenance, explicit states and historical capture limits. Financial approval must not authorize research. Depends on T009.
- [X] T011 [P] [US1] Create/reuse synthetic inputs in `tests/company_evidence_helpers.py`, `tests/fixtures/acceptance/company_evidence/financial_cases.json` and `tests/fixtures/acceptance/company_evidence/disclosures/reviewed_claim_snapshots.json`, then add failing integration/CLI/cache/archive tests in `tests/integration/test_company_evidence.py` and settings cases in `tests/unit/test_company_evidence_config.py`; exercise profile corroboration, same-ticker successor, absent/failed/inconclusive profile, missing independent reference, valid verified-domain route with null IDs, immutable store/revision conflicts, normalization and targeted expiry. Attach permitted stored business-model/moat claims to two independently verified share classes with original provenance; reject financial-only grants, denied/revoked/expired research uses and post-cutoff captures on fresh/stored/cache reuse. Include review-source/bind-issuer validation without grants by default, new collectors or catalog writes. Depends on T009.
- [X] T012 [P] [US1] Add failing root lookup/detail cases in `tests/app/test_stock_lookup.py`; query retained identified stocks before missing-classification/empty-sector early returns, explicitly choose ambiguous names/symbols by InstrumentId, open unassigned/unlisted details, show independent missing states, and assert lookup makes zero provider/research calls and does not prefetch unrelated industry histories. After explicit loading, verify both share classes display permitted stored business-model/moat claims with original provenance, while denied/revoked research and future captures remain blocked without suppressing eligible financials. Preserve tabs, columns, chart controls and explicit loading. Depends on T009.
- [X] T013 [P] [US1] Extend `tests/integration/test_stock_evidence.py` and `tests/integration/test_fundamental_cache.py` with failing two-listing, expired/nonprimary/unverified listing, reused-symbol successor, cache-key identity and membership-expiry cases; return a mixed predecessor/successor response plus unverifiable dates and assert exact eligible close/volume rows used by chart/calculation, including on cache hits and immediately before/on/after inclusive continuity boundaries. Exclude predecessor/out-of-window observations, explain unknown intervals without zero filling, preserve valid history outside membership dates and never merge/substitute listings; cache-key separation alone must fail the test. Failed acquisitions are not cached as success. Depends on T009.

### Implementation for User Story 1

- [X] T014 [US1] Implement/reuse 011 CompanyAssociation, SourceAssessment, EvidenceProvenance, FinancialObservation, CompanyResearchClaim and financial/research-scope request/outcome/snapshot records in `src/market_leadership/domain/company_evidence.py` (011 T006-T007 and stored business/competitive claim subset of T036); retain association states `verified`, `unresolved`, `mismatch`, `expired`, source roles `financial`, `disclosure`, `reference`, statuses `unreviewed`, `approved`, `denied`, `revoked`, independent collection/display/retention uses, "Existing nullable issuer ID; never synthesized.", per-listing "Hash of instrument/listing/source/effective binding, not a fabricated company ID.", optional ten-digit CIK, UTC observation times, finite observations and explicit unknown publication/basis states. For stored claims enforce topics `business_model`, `competitive_advantage`, kinds `reported_fact`, `management_claim`, `independent_opinion`, "Independent opinion requires a named source.", original provenance/qualifications/capture, and states `not_loaded`, `available`, `not_disclosed`, `unsupported_structure`, `not_comparable`, `stale`, `blocked`, `error`; retain 011 annual research age >450 days, research-scope validation and historical cutoff semantics without new collectors. Neither membership nor financial approval establishes research eligibility. Depends on T010.
- [X] T015 [US1] Implement/reuse 011 versioned source/binding/snapshot/entry serialization and atomic immutable publication in `src/market_leadership/infrastructure/company_evidence_files.py` (011 T008); keep evidence separate from catalogs, validate formats/path containment/hashes/expected revisions, retain history and structured safe failures, and round-trip typed stored financial/research snapshots with original claim provenance. Preserve independently scoped grants and reject unreviewed/denied/expired/revoked research uses on fresh/cached/archive paths; stored claims after the requested UTC day's end cannot resolve historical requests. No new collectors or claims import tool. Depends on T011, T014.
- [X] T016 [US1] Implement/reuse 011 optional profile/provenance metadata in `src/market_leadership/domain/fundamentals.py` and the existing `src/market_leadership/infrastructure/yfinance_fundamentals.py` reader (011 T010), plus the tested additive evidence-root/contact settings in `src/market_leadership/config.py` (011 T009); preserve one-ticker acquisition and historical-live rejection, retain issuer discriminators/profile failure states, distinguish reporting/trading currencies, and keep configured contact out of repr/log/cache/report values. No additional feed or second profile fetch. Depends on T011, T014.
- [X] T017 [US1] Implement/reuse 011 `load_company_evidence` in `src/market_leadership/application/load_company_evidence.py` (011 T011 plus stored-research attachment slice); verify an eligible dated listing and independent reviewed issuer-reference/profile corroboration before attaching financial components or publishing a verified financial snapshot. Add typed stored-claim attachment for each independently verified share class using separately reviewed research identity/permissions; financial approval must not grant research access. Allow unassigned instruments without membership proof, retain original financial/claim provenance and captured identity, block successor/missing/inconclusive references and denied/revoked/expired uses before fresh/cache/archive attachment, exclude captures after the requested UTC day's end, and preserve explicit failures without predecessor-success fallback or new collectors. Depends on T015, T016.
- [X] T018 [US1] Implement/reuse file-only review-source and bind-issuer commands in `src/market_leadership/company_evidence_admin.py` (011 T047 financial/issuer slice); enforce the acquisition-contract source/role/use/terms/review fields, dated verified-listing/CIK-or-domain binding, evidence-root and expected-revision checks, safe versioned output/nonzero errors, no URL fetch on registration and no automatic source/issuer/classification approval. Keep document collection/import extensions outside this task. Depends on T011, T015.
- [X] T019 [US1] Compose the shared production acquisition/store/cache callable through `src/market_leadership/bootstrap.py` and `src/market_leadership/ui/cache.py` (011 T012-T013 plus cached stored-research projection); keep domain/application independent of Streamlit, use exact financial/research TTLs 3,600/86,400 seconds where applicable, recheck independently scoped current binding/permissions outside cache hits, key provider/symbol/history/frequency/date/mode/normalization/schema and relevant identity/policy context, target refresh narrowly and isolate fixture/live inputs without success-shaped error caching. Retained historical claims are not erased by live TTL; no new research collection is introduced. Depends on T017, T018.
- [X] T020 [US1] Implement normalized issuer-owned statement projection and per-consumer attachment in `src/market_leadership/domain/company_evidence.py` and `src/market_leadership/application/load_company_evidence.py`, retaining original acquisition listing/source and every reporting-currency/scale/period/basis/definition/provenance field; reuse 011 T025 normalization prerequisites, including "Derived FCF requires finite aligned OCF/capex and verified outflow semantics, never zero defaults." and "no FX conversion, invented start date or YTD-as-quarter substitution." Reuse an approved common issuer reference only after each listing's gate passes; do not rewrite bundle symbols, coalesce null IDs, share cap/trading currency or fetch qualitative research. Depends on T010, T011, T019.
- [X] T021 [US1] Add local retained-stock lookup and independent instrument/listing detail selection to `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/components/stock_detail.py`; execute the lookup path before classification early returns, resolve ambiguous matches explicitly, retain unassigned/unlisted stock detail access and missing-state messages, and bypass industry-wide prefetch for lookup detail without new root tabs or arbitrary remote ticker requests. Depends on T012, T009.
- [X] T022 [US1] Wire listing-identity-aware selected-history requests through `src/market_leadership/application/load_stock_history.py` and `src/market_leadership/ui/cache.py`, using the independent projections from `src/market_leadership/infrastructure/catalog_files.py`; intersect requested history with reviewed dated listing/issuer continuity, never membership dates, bound requests where possible and validate every returned observation before charting/calculation, including after cache reuse. Exclude predecessor/out-of-window rows from mixed symbol responses and expose unverifiable intervals without zero filling or bridging. Preserve provider/range/parameter/continuity identity and targeted refresh; missing continuity blocks affected history rather than guessing or requiring financial-profile collection. Permit eligible lookup history without membership, keep member requests gated by verified primary listing, and never silently substitute a listing. Depends on T013, T021, T019.
- [X] T023 [US1] Integrate the shared eligible company-evidence callable with existing stock detail in `src/market_leadership/ui/components/stock_detail.py` and `src/market_leadership/ui/workflows/discovery_page.py`; retain explicit load controls, original company/listing provenance, null IDs and independent available/limited/blocked component states. Use the typed stored CompanyResearchClaim/research envelope implemented in T014-T017 for positive business-model/moat sharing between independently verified share classes; display original source/kind/qualifications/capture/provenance, enforce separate research permission and historical cutoff, and keep financial-only/denied/revoked claims blocked without hiding eligible financials. No new collectors or invented ratings; membership absence must not suppress eligible evidence. Depends on T020, T021, T022.
- [X] T024 [US1] Run the issuer/store/config/normalization/cache tests and `tests/app/test_stock_lookup.py`, checking the composed production gate rather than only fakes at the application boundary; verify 011 T022/T024 normalization regression slices with `tests/unit/test_fundamentals.py` and `tests/unit/domain/test_peer_scores.py`, positive stored business/moat sharing with separate grants/provenance, research-denial/revocation/expiry and historical-cutoff cases, exact permitted price/volume rows after ticker reuse, zero unsolicited research and catalog-hash invariance after enrichment. Record exact request/observation counters and red-to-green evidence in `specs/012-stock-industry-memberships/quickstart.md`. Depends on T023, T018.
- [X] T025 [US1] Validate all five US1 acceptance scenarios and SC-001 using `tests/app/test_stock_lookup.py`, `tests/integration/test_stock_evidence.py` and `tests/integration/test_company_evidence.py`; reconcile only fully verified shared 011 task portions in `specs/011-company-risk-evidence/tasks.md` without checking partially implemented tasks, and record remaining qualitative-feature work separately in `specs/012-stock-industry-memberships/quickstart.md`. Missing production issuer gates block US1 completion; they are not waived by successful lookup. Depends on T024.

**Checkpoint / MVP**: Stock-first access and identity-correct company/listing evidence
work on a simple reviewed fixture without US2/US4. Actual source permissions stay
unapproved unless separately reviewed by an authorized maintainer.

---

## Phase 4: User Story 2 - Review Overlapping Memberships and Nested Industries (Priority: P1)

**Goal**: Validate dated overlapping memberships and an arbitrary-depth single-parent
forest without changing classifications during enrichment.

**Independent Test**: Load controlled v2 candidates with concurrent sibling/cross-sector
memberships and dated three/four/deeper-level trees; reject exact invalid edges,
scope/date gaps and assertion conflicts. Use file authoring plus read-only validation;
the migration CLI and company collectors are not prerequisites.

### Tests for User Story 2 (Required)

- [X] T026 [P] [US2] Extend `tests/unit/test_catalog_memberships.py` with failing v2 overlap/temporal-forest cases: same-scope concurrent industries versus strict v1 rejection, compatible independent sources, conflicting MembershipId, inclusive reassignment, disjoint reviewed reparenting, same-date multiple parents/cycles/self-parent/orphans/cross-sector references, uncovered ancestor periods, empty nodes and depth beyond recursion limits. Include a union-of-historical-edges cycle that is not contemporaneous and must remain valid. Depends on T009.
- [X] T027 [P] [US2] Add failing query/provenance/representation integration cases in `tests/integration/test_catalog_workflows.py` and `tests/integration/test_industry_representations.py`; assert exact effective direct/descendant sets, direct versus inherited approval distinction, duplicate listing/assertion deduplication, separate share classes, retained prior releases, exact-scope ETF applicability and explicitly weighted baskets without automatic parent substitution. Depends on T009.

### Implementation for User Story 2

- [X] T028 [US2] Implement v2 dated iterative forest validation in `src/market_leadership/domain/catalog.py`; enforce "Sector: self SectorId, no parent.", "Root industry: one sector, no industry parent.", nested parent in identical scope with inherited sector, "A sub_industry has a parent; either type may parent a non-sector node in v2.", disjoint parent periods with consistent identity/type, and period-covered ancestors. Check active edges at interval boundaries, report affected identities, and retain strict v1 constructor defaults with no row-controlled policy or semantic depth cap. Depends on T026.
- [X] T029 [US2] Implement v2 association validation in `src/market_leadership/domain/catalog.py`; permit concurrent different industries across sectors, require agreement of every field for copies of MembershipId, preserve compatible independent assertions and nullable identities, and validate target/classification period coverage. Never infer direct ancestor/child membership or allow unreviewed assertions; keep legacy v1 conflicting-assignment behavior intact. Depends on T026, T028.
- [X] T030 [US2] Implement iterative active-subtree traversal and direct/descendant instrument unions in `src/market_leadership/infrastructure/catalog_files.py`; index direct memberships and dated children, preserve all relevant assertion provenance in CatalogMember, include empty nodes, deduplicate instruments before listing/peer eligibility, and avoid recursion or materializing full ancestor/member closure. Date-specific reassignment/reparenting must not mutate retained snapshots. Depends on T027, T029.
- [X] T031 [US2] Expose complete effective membership/ancestor/sector paths and independently eligible provider-symbol collection through `src/market_leadership/infrastructure/catalog_files.py` and `src/market_leadership/infrastructure/stock_membership.py`; use selected scoped node as explicit adapter context rather than a representative child's IndustryId, retain direct assertions separately from inherited rollup inclusion and preserve explicit inactive/historical-unavailable states. Depends on T030.
- [X] T032 [US2] Adapt snapshot representation worklists/resolution in `src/market_leadership/application/industry_representations.py` and their catalog validation in `src/market_leadership/infrastructure/catalog_files.py`; retain exact node type/scope/date/suitability approval, historical references and explicit ETF/basket/gap states at every depth, without automatically copying old-scope approvals or populating/rewighting baskets from descendant membership. Depends on T027, T031.
- [X] T033 [US2] Run T026-T027 plus existing catalog/representation regressions and verify all five US2 scenarios and SC-002/SC-003/history portions of SC-008; use loader fixtures to prove enrichment-only operations leave classification bytes unchanged and mark missing US1 enrichment integration as pending until T025, not silently passed. Record exact expected/actual sets, invalid-node diagnostics and red-to-green results in `specs/012-stock-industry-memberships/quickstart.md`. Depends on T032.

**Checkpoint**: Overlap/deeper trees and date-specific sets are usable in reviewed
temporary candidates; no migration or new ETF approval has occurred.

---

## Phase 5: User Story 3 - Browse Deduplicated Stocks and Contextual Peer Evidence (Priority: P2)

**Goal**: Render full membership paths and exact rollups while keeping raw facts,
listing evidence and industry-specific comparisons correctly separated.

**Independent Test**: A controlled parent/child hierarchy with overlap, two listings,
two share classes and true/insufficient point-in-time financial cases returns exact
sets and A -> B -> A comparison results with zero repeats per unchanged, still-valid
issuer/evidence request; previously unrequested peers load only explicitly.
No production migration is required.

### Tests for User Story 3 (Required)

- [X] T034 [P] [US3] Extend `tests/unit/domain/test_peer_scores.py` and add context adapter cases in `tests/integration/test_stock_membership.py`; require unique instrument cohorts for parent/sector unions, explicit selected industry/scope/version/date/observation basis, unchanged five-peer/tie/TTM/publication/currency/capitalization rules, fact-sensitive result keys and stable cohort fingerprints for physical-row/research-only edits. Two share classes count twice; duplicated listings do not. Depends on T025, T033.
- [ ] T035 [P] [US3] Add failing deep-path/selection/result AppTests in `tests/app/test_sector_stock_explorer.py`, `tests/app/test_stock_detail.py` and `tests/app/test_progressive_tabs.py`; cover duplicate names, empty nodes, all direct membership paths, parent context, A -> B -> A results, no arbitrary sector score, overlapping selection intersection, expired membership with valid singleton detail, isolated sessions and unchanged root/table/chart baseline. Depends on T025, T033.
- [ ] T036 [P] [US3] Add failing composed evidence reuse tests in `tests/integration/test_fundamental_cache.py`; use overlapping but different A -> B -> A cohorts and per-issuer/evidence-request counters, requiring zero repeats for already acquired requests while reviewed issuer, requested evidence/date, source permissions and freshness remain valid. Previously unrequested peers must incur zero calls before explicit loading and only necessary active-view first calls afterward; returning to A reuses valid requests. Separately count unrelated calls and reject eager whole-universe/both-cohort prefetch on navigation as a passing strategy. Change source/issuer/binding/permissions/fact vintage to test revalidation/invalidation; keep distinct listing bundles/cap, insufficient vintage and zero qualitative peer collection. Depends on T025, T033.

### Implementation for User Story 3

- [X] T037 [US3] Add explicit PeerComparisonContext/result provenance in `src/market_leadership/application/score_industry.py` and selected-context adapters in `src/market_leadership/infrastructure/stock_membership.py`; include selected scope/non-sector node, membership_as_of, unique eligible instrument/listing identities, cohort fingerprint, rules revision and observation/vintage basis. Do not change `src/market_leadership/domain/peer_scores.py` arithmetic or use a direct child's IndustryId as parent context. Depends on T034.
- [X] T038 [US3] Implement canonical cohort fingerprints in `src/market_leadership/infrastructure/catalog_files.py` from selected scope/node/date, eligible identity set and relevant eligibility/approval inputs; omit physical row/assertion multiplicity, migration transport and unrelated research changes while retaining source/integrity checks. Fact/vintage changes must alter result keys even when cohort identity is unchanged. Depends on T034.
- [ ] T039 [US3] Reuse the production issuer-fact acquisition/attachment boundary from T019-T020 in `src/market_leadership/application/score_industry.py` and `src/market_leadership/ui/cache.py` (011 T028 compatible slice); compose full context-keyed results without averaging industries, cross-listing bundle substitution, new research collection, hidden errors or synthetic historical eligibility. Reuse each unchanged valid issuer/request across A -> B -> A; acquire previously unrequested peers only through explicit active-view loading, never context-switch or whole-universe prefetch. Missing not-yet-loaded peers remain explicit until loaded. Depends on T036, T037, T038.
- [ ] T040 [US3] Separate instrument/listing selections from comparison context in `packages/market-data/src/market_data/domain/stock_selection.py` and `src/market_leadership/ui/navigation.py`; retain valid IDs/intersections across dates, parents and compatible revisions, clear only invalid dependents with reasons, preserve valid singleton lookup detail and namespaced session state, and never cache user selections or silently choose the first option. Depends on T035, T037.
- [ ] T041 [US3] Render complete ancestor paths, custom-scheme coverage labels, direct versus inherited memberships, explicit context controls and separately retained valid A/B peer results in `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/components/stock_detail.py`; show unavailable peers for sector/unassigned context without suppressing eligible chart/company facts. Preserve mandatory columns, chart controls and formulas. Depends on T035, T039, T040.
- [ ] T042 [US3] Wire the same projections, deep path labels, valid selection intersection and explicit industry context into `src/market_leadership/ui/workflows/industry_deep_dive.py` and `src/market_leadership/ui/workflows/fundamental_grading.py` where currently consumed; retain explicit data loading and do not reactivate retired root workflows or duplicate filtering/scoring logic. Reconcile remaining direct StockRow/snapshot.stocks consumers against `contracts/catalog-v2.md`. Depends on T041.
- [ ] T043 [US3] Run T034-T036 and affected root/financial/stock-selection regressions, checking all seven US3 scenarios, exact SC-004 sets, SC-005 contexts, SC-007 applicable selection cases and SC-009 per-request zero-repeat counts; distinguish necessary first loads for new peers from repeats and prove zero new loads before explicit action or unrelated prefetch. Record production-composition counters/red-to-green evidence and remaining migration-cutover cases in `specs/012-stock-industry-memberships/quickstart.md`. Depends on T042.

**Checkpoint**: Lookup, rollups and separately contextualized industry comparisons
work with shared eligible facts and no duplicated instruments or arbitrary scores.

---

## Phase 6: User Story 4 - Adopt the Revised Mapping Without Losing History or Navigation (Priority: P2)

**Goal**: Prepare and explicitly review a complete migration, publish only a validated
candidate, and restore prior data semantics without losing current governance history.

**Independent Test**: Temporary CLI/store walkthrough prepares v1 -> v2, rejects a
draft/invalid/stale candidate, approves compatible unchanged mappings, separately
reviews changed assignments, activates v2 and explicitly restores v1 with complete
audit/archive/report retention. No production data, rights or source approvals.

### Tests for User Story 4 (Required)

- [ ] T044 [P] [US4] Add failing schema and complete source-to-target reconciliation tests in `tests/integration/test_membership_migration.py`; validate every captured source artifact record, natural keys/record hashes, original scoped IDs, all four dispositions, unique summary/source-key pairs, exact counts, target reference resolution and digest exclusions. Include missing/duplicate records, corrupt hashes, fake approval strings, incompatible carry-forward, changed/unreviewed assignments and historical-report retention without reapplication. Depends on T033.
- [ ] T045 [P] [US4] Add failing prepare/validate CLI cases in `tests/contract/test_catalog_cli.py`; cover all migration-contract required flags, absolute safe new output roots, existing/published destination refusal, unsupported multi-region/source scopes, deterministic leaf targeting and IDs, target-period intersection, prepared/activation_ready=false output, optional validation source manifest, safe failures/nonzero exit and zero CURRENT/network/issuer/approval mutation. Depends on T033.
- [ ] T046 [P] [US4] Extend `tests/integration/test_catalog_publication.py` with failing reviewed migration/restoration cases: source/current hash checks at commit, candidate edits, expected-release/writer races, stage interruptions, audit-prefix/immutable archive/report retention, historical NodeReview/representation provenance, v1 -> v2 -> restored-v1 original data semantics, native v2 edits without reapplying old reports, and explicit refusal of corrupt/missing history without silent rollback. Depends on T033.

### Implementation for User Story 4

- [ ] T047 [US4] Implement deterministic preparation in `services/market-structure/src/market_data_tools/membership_migration.py`; capture strict source bytes, group listing copies by MembershipId, target exact SubIndustryId or original IndustryId without adding a direct parent assertion, retain unchanged instrument/listing identities, derive changed logical IDs only from original/target scope/node/period, intersect target periods and retain original records/approvals/nulls/unassigned inventory. Refuse unsupported conversion/output paths and create no approvals, issuer identities or extra industries. Depends on T044, T030.
- [ ] T048 [US4] Implement typed report serialization and semantic validation in `services/market-structure/src/market_data_tools/membership_migration.py` using `specs/012-stock-industry-memberships/contracts/membership-migration.schema.json` as the contract; package the matching runtime resource `packages/market-data/src/market_data/schemas/membership-migration.schema.json` in `pyproject.toml` and test contract/resource agreement. Preserve exact summary/record required fields, 64-lowercase-hex hashes, unique/nonempty keys, nonnegative counts, dispositions `preserved`, `transformed`, `retained_historical`, `unresolved`, states `prepared`, `approved` and modes `unchanged_reviewed`, `new_reviewed`, `not_operational`. Prepared review fields must be null; approved summary/operational records require valid sources/references; not_operational has no target membership IDs. Check full source accounting, target digest and compatible approval lineage beyond schema shape. Depends on T044, T047.
- [ ] T049 [US4] Add registered immutable membership_migration artifact loading/retention and historical governance projection in `packages/market-data/src/market_data/catalog.py` and `packages/market-data/src/market_data/domain/catalog.py`; validate old-scope ledger references against captured source or explicitly retained checksum-verified parent-chain snapshots, project only applicable current approvals, retain legacy archive bytes, never scan directories or retarget old representation approvals, and treat old report digests as historical proofs rather than current-data constraints. Depends on T046, T048.
- [ ] T050 [US4] Add prepare-membership-migration and validate-catalog --source-release-manifest support to `services/market-structure/src/market_data_tools/catalog_admin.py`; implement the exact interface/output/exit semantics in `specs/012-stock-industry-memberships/contracts/membership-migration.md`, distinguish prepared from validated/published, require captured source and reviewed report for new migrations, and report separate physical-row/instrument/membership counts without issuing approvals or changing the active entry. Depends on T045, T048, T049.
- [ ] T051 [US4] Integrate newly applying migration validation with activate_release/publication in `packages/market-data/src/market_data/catalog.py`; recheck known source/current manifest checksums, target digest, every disposition/approval, captured candidate bytes, report/archive retention and ledger prefix under the existing writer lock before atomic commit. Preserve existing expected-release and truthful failed/conflict/indeterminate semantics; drafts, stale/corrupt sources and competing publishers must not change CURRENT. Depends on T046, T050.
- [ ] T052 [US4] Extend explicit recover_release composition in `packages/market-data/src/market_data/catalog.py` to publish the target's original format/data/approval semantics with complete current audit plus recovery event and retained archives/reports; validate the composition before commit, keep strict v1 data and only its typed nonoperational report-history extension, retain original snapshots and exact target/entry checksum arguments, and reject unsafe history/binary assumptions instead of direct entry editing or silent fallback. Depends on T051.
- [ ] T053 [US4] Extend `tests/app/test_progressive_tabs.py` and the shared reconciliation use in `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/ui/workflows/industry_deep_dive.py`, `src/market_leadership/ui/workflows/stock_lookup.py`, and `src/market_leadership/ui/workflows/yahoo_classification_preview.py` for compatible migration/restoration cutovers; retain all four tabs and one catalog/context, preserve valid independent instrument/listing/chart controls, explain only invalid dependent comparisons/selections, reuse unchanged price/company facts, clear incompatible preview results without approving classification, and prove neither the evidence store nor original approvals are rewritten by adoption. Depends on T035, T052, T043.
- [ ] T054 [US4] Update `specs/012-stock-industry-memberships/quickstart.md`, `specs/012-stock-industry-memberships/contracts/membership-migration.md` and the affected authority notes in `specs/README.md` with the implemented v1/v2 compatibility boundary, record dispositions/review procedure, safe preparation/activation/restoration commands, old-binary limitation, changed filtering/context behavior and unchanged listing/issuer/calculation rules; do not change historical approvals or claim a production migration. Depends on T053.
- [ ] T055 [US4] Execute the temporary-root preparation -> reviewed validation -> activation -> rejection/race -> explicit restoration guide and T044-T046/T053 tests; verify all seven US4 scenarios, 100% SC-006 source reconciliation and SC-007/SC-008 cutover/history outcomes, including separately reviewed ETF/basket applicability. Record actual before/after hashes, exact record/set counts, failure statuses and red-to-green evidence in `specs/012-stock-industry-memberships/quickstart.md`. Depends on T054.

**Checkpoint**: A synthetic reviewed migration and restoration are reproducible.
No production catalog cutover, auto-reclassification or source permission is implied.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Prove the complete bounded behavior, performance and unchanged baselines;
document only verified implementation results.

- [ ] T056 [P] Extend `tests/integration/test_catalog_performance.py` first with the 10,000-instrument/500-node overlap/depth variants, exact set checks, input limits and no warm reparse; run cold <=5 s/warm <=1 s phase assertions and record separate timings/memory in `specs/012-stock-industry-memberships/quickstart.md`. If the new workload fails, address only measured catalog traversal/index costs in `packages/market-data/src/market_data/catalog.py` without arbitrary thresholds, transitive-closure storage or a new framework. Depends on T043, T055.
- [ ] T057 [P] Add and execute source-free end-to-end invariance cases in `tests/integration/test_membership_acceptance.py` using actual catalog/acquisition/cache/publication composition and injected transports; cover all SC-001-SC-009, current/historical A/B contexts, eligible cross-share-class statement and stored business/moat claim reuse with separate research grants/provenance/cutoff, denied/revoked attachment, wrong-issuer rejection, exact allowed close/volume observations from a mixed predecessor/successor response, lookup with no active scope and zero classification/approval mutations after enrichment/refresh. Verify unchanged chart/source/formula/aggregate/table behavior, per-request zero repeats, explicit-only necessary first peer loads and zero universe prefetch, not screenshots or test stubs alone. Depends on T043, T055.
- [ ] T058 Run the focused acceptance/regression selectors together, then `.venv/bin/python -m pytest -m "not live"`, `.venv/bin/ruff check src tests` and `.venv/bin/pyright` using `pyproject.toml`; record outcomes in `specs/012-stock-industry-memberships/quickstart.md`, resolve only introduced/tightly coupled failures and distinguish pre-existing issues. Do not install dependencies unless the configured command reports a missing dependency. Depends on T056, T057.
- [ ] T059 Refresh implemented commands/test selectors and limitations in `specs/012-stock-industry-memberships/quickstart.md`, `specs/012-stock-industry-memberships/plan.md` and `specs/README.md`; reconcile the shared interface/ownership notes in `specs/011-company-risk-evidence/plan.md` and `specs/011-company-risk-evidence/tasks.md` only where implemented and tested, retaining distinct listing-bound bundles, pending qualitative work and unapproved production sources. Depends on T058.
- [ ] T060 Audit the FR/SC/scenario coverage tables in `specs/012-stock-industry-memberships/tasks.md` against recorded test evidence in `specs/012-stock-industry-memberships/quickstart.md`; mark implementation tasks complete only after verification, preserve reviewer-owned quality checklist markers, and explicitly block full acceptance if issuer attachment/reuse or any mandatory migration/selection case remains absent. Remove only task-owned temporary fixtures/processes, leave active catalogs/configuration and unrelated work unchanged. Depends on T059.

---

## Dependencies & Execution Order

### Phase and story graph

```text
T001 -> T002 -> T003/T004 -> T005/T006 -> T007 -> T008 -> T009
                                                           |
                       +-----------------------------------+------------------+
                       |                                                      |
                  US1 T010-T025                                          US2 T026-T033
                       |                                                      |
                       +------------------> US3 T034-T043 <--------------------+
                                                                              |
                                      US4 tests/preparation T044-T052 <---------+
                                                 |
                         US3 T043 --------------> T053 -> T054 -> T055
                                                                  |
                                                T056/T057 -> T058 -> T059 -> T060
```

- Foundations block story implementation; they do not depend on 011 collectors.
- US1 and US2 are independently testable after T009. They share catalog/adapter
  files at some steps, so schedule edits serially even if their dependency graph
  permits concurrent work.
- US3 needs verified US1 identity/reuse and US2 deep membership queries.
- US4 tests/preparation/publication can begin after US2; its selection cutover
  validation T053 additionally needs US3. US4 does not need new qualitative collectors.
- Retained snapshots remain usable during development. Do not publish a partially
  implemented runtime format into production or relax old data rules to pass tests.
- Direct task dependencies are specified on every task other than the initial
  baseline. No external `Tnnn` reference is an undeclared scheduling dependency.

### Shared feature 011 ownership and dependency reconciliation

This list includes executable work, not an instruction to wait for all 011 stories.
The same shared modules are implemented once. In T002, add an explicit prerequisite
reconciliation note to [011 tasks](../011-company-risk-evidence/tasks.md) and split
only necessary test portions/dependencies as follows; retain original task IDs,
unchecked markers and later full-story completion criteria. Do not mark an entire
011 task complete merely because its financial/identity subset passes.

| 011 work / old broad prerequisite | Owner in this task list | Reconciled boundary |
|---|---|---|
| T001-T005 fixture/shared validation | T001-T002, T010-T011 | Reuse existing helpers/tests; add membership cases and the minimal reviewed stored-claim snapshots |
| T006-T010 domain/store/settings/profile | T014-T016 | Same modules, including CompanyResearchClaim and research-scope envelopes; no duplicate implementation |
| T011-T014 acquisition/cache/composition | T017-T019, T024-T025 | Adapt membership-independent lookup and eligible stored-research attachment; preserve separate financial/research grants and per-listing proof |
| T022/T024 tests formerly gated by T021 cash-warning story | T010-T011, T024 | Financial normalization/formula/identity subset can run after shared foundation, without requiring cash-banner UI |
| T025 normalization | T020 | Reuse reviewed normalization needed for statement sharing, not new financial metrics |
| T028 detail/cohort reuse | T039 | Wait for T020 and explicit 012 comparison context; do not require financial matrix UI or fetch qualitative peers |
| T044/T046 tests formerly gated by T031/T043 | T010-T011 | Reviewer/identity/permission subset can run after shared records/store, without disclosure extraction |
| T047 review-source/bind-issuer | T018 | Actual file-only reviewed financial/issuer administration; no automatic grants |
| T034/T036 business/competitive stored-claim validation | T010-T011, T014, T023-T024 | Only required claim topics/kinds/provenance/state/age and separate research gates; no disclosure extraction, orders or new collectors |

011's collectors, narrative/order extraction, cash-warning presentation, full
document/import UI, and their complete story checkpoints remain separate work.
US1 must demonstrate independently eligible stored business-model/moat reuse with
positive and blocked cases; these tasks do not promise new qualitative acquisition.
The stored-claim subset does not complete all original 011 T034/T036 requirements.
Full 012 identity/reuse acceptance still requires
the production shared gate/composition, not mock-only or symbol-only attachment.

### Within each story

Tests -> domain/contracts -> acquisition/query adapters -> UI/CLI integration ->
independent verification. Never run implementation ahead of its listed failing
test prerequisite. Preserve type safety and repository error/notification patterns.

## Parallel Execution Examples

Only launch after the stated dependency frontier is complete; serialize shared
source-file edits and result-log updates.

| Story / phase | Safe parallel tasks | Completed frontier |
|---|---|---|
| Foundations | T003 schema tests + T004 projection tests | T002 |
| US1 | T010 domain tests + T011 acquisition tests + T012 AppTests + T013 price/cache tests | T009 |
| US2 | T026 domain/temporal tests + T027 query/representation tests | T009 |
| US3 | T034 peer/adapter tests + T035 root AppTests + T036 cache tests | T025, T033 |
| US4 | T044 reconciliation tests + T045 CLI tests + T046 publication tests | T033 |
| Cross-cutting | T056 performance + T057 end-to-end | T043, T055 |

For T056/T057, keep temporary stores independent; defer the shared quickstart
result edit to T058. Test tasks in different stories may still touch the same
existing files: do not infer cross-story parallelism beyond this table.

## Implementation Strategy

### MVP first: US1

Complete setup/foundations, then US1. Demonstrate retained/unassigned lookup,
nullable issuer identity, independent histories and verified reusable facts using
controlled approved fixtures. Stop and validate T025 before calling it a usable
US1 MVP. Lookup alone without the production issuer gate is only a development
slice, not completed US1 or a deployable reviewed migration.

### Incremental delivery

1. Foundations preserve v1 and establish explicit v2 identity grammar.
2. US1 supplies stock-first access and correct issuer/listing evidence.
3. US2 supplies reviewed overlap and dated deeper industry trees; it may be
   developed independently of US1 once the foundation is verified.
4. US3 integrates exact rollups, comparisons and identity-aware reuse.
5. US4 supplies complete guarded migration/restoration and compatible UI cutover.
6. Cross-cutting tests measure exact outcomes and unchanged behavior before full
   acceptance. Production source approvals and catalog activation remain separate.

## Requirement and Outcome Coverage

Task references are planned coverage, not implementation or a claim that tests pass.

| Requirement | Implementing tasks | Test / verification tasks |
|---|---|---|
| FR-001 | T005, T014-T020, T022-T023 | T004, T010-T013, T024-T025 |
| FR-002 | T014-T020, T023, T039 | T010-T011, T024-T025, T036, T057 |
| FR-003 | T005, T007-T008, T014, T020 | T004, T010-T011, T025 |
| FR-004 | T008, T016, T022 | T013, T024-T025 |
| FR-005 | T006-T007, T028-T029, T041 | T003, T026, T035 |
| FR-006 | T005, T029-T031 | T026-T027, T033 |
| FR-007 | T005, T007-T008, T029-T030 | T004, T026-T027 |
| FR-008 | T028, T030-T031 | T026-T027, T033 |
| FR-009 | T028-T029, T051 | T026, T046, T055 |
| FR-010 | T028-T031, T049, T052 | T026-T027, T046, T055 |
| FR-011 | T030-T031 | T027, T034, T043 |
| FR-012 | T030, T037-T039 | T027, T034, T043 |
| FR-013 | T031, T041-T042 | T027, T035, T043 |
| FR-014 | T037-T039, T041 | T034-T036, T043 |
| FR-015 | T020, T037-T039 | T024, T034, T036, T043, T057 |
| FR-016 | T017, T021-T023, T039-T042 | T011-T013, T035-T036, T043 |
| FR-017 | T017-T020, T023, T047 | T024, T033, T057 |
| FR-018 | T006-T007, T047-T054 | T003, T044-T046, T055 |
| FR-019 | T047-T049, T051 | T044-T046, T055 |
| FR-020 | T047-T051 | T044-T045, T055 |
| FR-021 | T049, T051-T053 | T046, T053, T055 |
| FR-022 | T032, T049, T051 | T027, T046, T055 |
| FR-023 | T008, T021-T023, T040-T042, T053 | T012, T035, T043, T053 |
| FR-024 | T016, T021-T023, T037-T042, T054 | T013, T024, T035, T043, T057-T058 |
| SC-001 | T005, T014-T023 | T004, T010-T013, T025, T057 |
| SC-002 | T029-T031 | T026-T027, T033, T057 |
| SC-003 | T028-T030 | T026, T033, T056-T057 |
| SC-004 | T030-T031, T037-T039 | T027, T034, T043, T056-T057 |
| SC-005 | T037-T041 | T034-T036, T043, T057 |
| SC-006 | T047-T051 | T044-T046, T055, T057 |
| SC-007 | T021, T040-T042, T053 | T012, T035, T043, T053, T055 |
| SC-008 | T028-T031, T049, T052-T053 | T024, T026-T027, T033, T046, T055, T057 |
| SC-009 | T019-T020, T039 | T036, T043, T057 |

### Acceptance scenario coverage

Numbers below refer to the numbered scenarios in each specification story.

| Story scenarios | Direct acceptance tests / final gate |
|---|---|
| US1.1 shared issuer facts | T010-T011, T024-T025, T057 |
| US1.2 distinct listing histories | T013, T024-T025 |
| US1.3 null ID and independent review | T010-T011, T025 |
| US1.4 unassigned lookup | T012, T025 |
| US1.5 unusable listing | T012-T013, T025 |
| US2.1 concurrent cross-sector membership | T026-T027, T033 |
| US2.2 deeper single-parent nesting | T026-T027, T033, T056 |
| US2.3 invalid edge/period activation | T026, T046, T055 |
| US2.4 historical reassignment | T026-T027, T033 |
| US2.5 enrichment cannot reclassify | T024, T033, T057 |
| US3.1 descendant union | T027, T034, T043 |
| US3.2 sibling deduplication | T027, T034, T043 |
| US3.3 listing/share-class count | T027, T034, T043 |
| US3.4 separate industry results | T034-T036, T043 |
| US3.5 eligible fact reuse | T036, T043, T057 |
| US3.6 no arbitrary sector score | T035, T043 |
| US3.7 unchanged migration baseline | T035, T055, T057-T058 |
| US4.1 complete migration/version guidance | T044-T045, T054-T055 |
| US4.2 rejected candidate unchanged | T045-T046, T055 |
| US4.3 stable valid selection | T035, T053, T055 |
| US4.4 historical hierarchy/cohort | T046, T053, T055 |
| US4.5 explicit restoration | T046, T053, T055 |
| US4.6 exact ETF/basket applicability | T027, T046, T055 |
| US4.7 compatible approval carry-forward | T044-T046, T055 |

## Notes

Tasks remain unchecked until implementation and verification. Shared 011 portions
must not be double-built or incorrectly marked complete. Reviewer-owned quality
checklists are not implementation tracking. All tests are source-free; production
catalog mappings, company identifiers and permission decisions remain unchanged.
