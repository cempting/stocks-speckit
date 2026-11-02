---
description: "Executable, test-first tasks for company risk evidence"
---

# Tasks: Company Risk Evidence Scoreboard

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md),
[data-model.md](./data-model.md), [UI contract](./contracts/company-risk-ui.md),
[acquisition contract](./contracts/company-evidence-acquisition.md), and
[quickstart.md](./quickstart.md).

**Prerequisites**: Existing Python 3.12 development environment and accepted feature 011 design.
No dependency addition, new root workflow, financial-source replacement, catalog mutation,
production activation, or real source approval is authorized by this task list.

**Tests**: Required by the constitution and accepted test-first plan. Add each test group and
confirm it fails for the missing behavior before its implementation. Reuse existing helpers;
use synthetic companies, simulated permissions, injected clocks/transport and temporary stores.
Test approval records must never be copied into production.

**Organization**: Setup -> shared foundations -> US1 (P1) -> US2 (P1) -> US3 (P2) -> US4 (P2)
-> cross-cutting acceptance. All boxes start unchecked; generation is not implementation.

## Format: `[ID] [P?] [Story] Description`

- `[P]` denotes a disjoint-file task that can run with the listed peers once all prerequisites
  are complete. It never overrides a dependency or permits concurrent edits to shared files.
- `[US1]` through `[US4]` map to the numbered specification stories.
- Paths are repository-relative. `Depends on` names actual prerequisites; phase ordering is
  the recommended sequence, not an excuse to invent dependencies.

## Path Conventions

Extend `src/market_leadership/` and existing `tests/` conventions. New planned files appear
explicitly below; reuse existing pytest fixtures and argparse patterns where applicable.
The small shared fixture helper/config test support deterministic validation, not a new framework.

## Cross-feature ownership: feature 012

Feature 012 owns the narrow shared identity, stored-claim, listing-continuity, and
issuer-fact reuse slices listed in
[its shared ownership table](../012-stock-industry-memberships/tasks.md). Those
feature-012 task IDs are the execution prerequisites for the corresponding shared
code; do not build a second implementation or treat the slice as completion of an
entire feature-011 task. All feature-011 checkboxes and broader story gates remain
unchanged until their complete requirements are implemented and verified.

## Phase 1: Setup (Shared Infrastructure)

**Goal**: Establish a protected baseline and reusable offline test inputs.

- [ ] T001 Run the existing regression selectors in `specs/011-company-risk-evidence/quickstart.md`, capture the actual branch/worktree and baseline outcomes there, and define temporary-root validation so active catalogs/settings/approvals and unrelated work are preserved; record pre-existing failures rather than fixing unrelated code.
- [ ] T002 Create synthetic financial/profile/identity/permission cases in `tests/fixtures/acceptance/company_evidence/financial_cases.json` and a small reusable injected ticker/UTC-clock/temporary-store/root-AppTest helper in `tests/company_evidence_helpers.py`; cover positive/zero/negative/missing cash, similar names, multiple listings, same-ticker/same-exchange predecessor/successor issuers with conflicting dated issuer evidence, absent/failed/inconclusive profiles and missing independent references, valid reviewed-domain corroboration with company ID/CIK null, ADR currencies and isolated simulated approvals. Depends on T001.

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Provide shared identity, permission, typed acquisition and persistence needed by all
four stories. Financial acquisition belongs here because both US1 warnings and US2 inspection
must operate on real structured inputs; qualitative extraction remains in US3.

**Test-first gate**: T003-T005 must fail before their corresponding production changes.

- [ ] T003 [P] Add failing shared-record validation tests in `tests/unit/domain/test_company_evidence.py` for frozen records, ISO dates versus UTC timestamps, identity/effective periods, nullable IDs, source-use/role states, provenance, finite observations, claim/envelope schemas and unknown-version rejection. Depends on T002.
- [ ] T004 [P] Add failing shared acquisition/store/cache tests in `tests/integration/test_company_evidence.py` for denial before transport, one-ticker metadata retention, independent dated issuer-reference corroboration per FR-009, same-ticker/same-exchange successor mismatch, absent/failed/inconclusive profiles and missing independent references remaining unresolved, and valid domain-corroborated attachment with company ID/CIK null and no invented IDs/research grants/catalog mutation. Assert mismatched/unresolved facts never attach or publish as verified snapshots/latest pointers on fresh, cache/cohort and archive paths; cached predecessor success cannot resolve a failed current profile or attach to a successor. Retain partial component facts only after identity verification, exact identity-aware financial cache keys/expiry, immutable hashes/atomic pointers/revision conflicts and historical capture filtering; inject all services and paths. Depends on T002.
- [ ] T005 [P] Add failing additive settings tests in `tests/unit/test_company_evidence_config.py` for explicit evidence-root override and a publisher contact header that never enters repr/log/cache/report outputs, while existing provider/catalog settings remain unchanged. Depends on T002.
- [ ] T006 [P] Implement shared CompanyAssociation, SourceAssessment and EvidenceProvenance records/validation in `src/market_leadership/domain/company_evidence.py`; enforce "Use frozen typed records and narrow literal states, matching domain conventions.", association "Hash of instrument/listing/source/effective binding, not a fabricated company ID.", company ID "Existing nullable issuer ID; never synthesized.", listing "eligible verified primary stock listing.", and "Optional reviewed regulator/issuer identity; CIK is ten digits."; use association states `verified`, `unresolved`, `mismatch`, `expired`, source roles `financial`, `disclosure`, `reference`, statuses `unreviewed`, `approved`, `denied`, `revoked`, independent collection/display/normalized-retention/raw-retention uses, mandatory observation time and "Period end never becomes publication date; missing dates/locators remain explicitly unavailable." Depends on T003.
- [ ] T007 Implement shared FinancialObservation, CompanyResearchClaim, CompanyEvidenceRequest/Outcome/Snapshot envelopes in `src/market_leadership/domain/company_evidence.py`; enforce "JSON formats start at v1; finite numbers only.", "Booleans, NaN and infinity are not monetary observations.", "URLs contain no credentials/private request data.", nullable period start, bases `quarterly`, `annual`, `ytd`, `unknown`, origins `source_supplied`, `derived`, observation states `available`, `not_loaded`, `insufficient`, `unavailable`, `not_comparable`, `stale`, `error`, request financial/research scopes and current/historical modes, "history 4-8", outcome states `complete`, `partial`, `blocked`, `error`, and "No private stock list or credential."; define claim topics/kinds and underscore state literals from the model, leaving story-specific normalization to US3. Depends on T006.
- [ ] T008 [P] Implement shared versioned assessment/binding/snapshot/entry serialization and immutable hash-checked atomic publication in `src/market_leadership/infrastructure/company_evidence_files.py`; keep `.data/company-evidence` separate from catalogs, validate safe relative paths and required versions, preserve review history, compare expected revisions, expose corruption/interruption/concurrent-write errors, and block missing/unknown grants rather than returning empty success. Depends on T004, T007.
- [ ] T009 [P] Add `COMPANY_EVIDENCE_ROOT` (default `.data/company-evidence`) and `SEC_EDGAR_USER_AGENT` settings in `src/market_leadership/config.py`; add only the planned root/contact configuration, suppress header values in representations, and do not alter selected provider/catalog settings or create/approve production sources. Depends on T005.
- [ ] T010 [P] Add optional immutable public profile/provenance/component metadata to `src/market_leadership/domain/fundamentals.py` and retain it through the existing reader in `src/market_leadership/infrastructure/yfinance_fundamentals.py`; preserve old callers, one ticker, safe partial errors and historical-live rejection. Retain returned regulator/domain issuer discriminators, observation provenance and distinct absent/failed/inconclusive profile states so T011 can corroborate an independent dated reviewed issuer reference; source symbol/exchange matching is necessary but not sufficient, including same-label successors. Preserve null company ID/CIK for the valid domain route without synthesizing IDs, refetching profiles or granting research access. Distinguish reporting from trading currency without FX eligibility expansion. Depends on T004, T007.
- [ ] T011 Implement the shared current-financial and historical-archive paths of `load_company_evidence` in `src/market_leadership/application/load_company_evidence.py`, with injected financial loader/store/clock; validate captured catalog/dated primary listing, current grants and independent issuer-reference/profile corroboration per FR-009 before attachment or verified persistence. Reject conflicting same-ticker/same-exchange successors as mismatches; missing/failed/inconclusive profiles or missing independent references remain unresolved with actionable reasons, not partial verified facts. Accept conflict-free reviewed-domain corroboration while preserving null company ID/CIK, existing catalog identity and separate research gates. Apply the gate on cache/cohort and archived outcomes against their applicable dated binding; never attach predecessor captures to successors or hide a failed current profile with previous success. Produce structured compatible cash observations with honest missing metadata, preserve independent partial facts only under verified identity, and persist permitted outcomes; historical capture must be "no later than the requested UTC day's end" and cannot fetch historical Yahoo or promote peer vintages. Keep research unavailable until its US3 reader exists. Depends on T008, T009, T010.
- [ ] T012 Extend financial response/transform caching in `src/market_leadership/ui/cache.py` with richer schema revision and provider/symbol/history/frequency/date/mode/normalization plus relevant identity/permission context; expire at exactly 3,600 seconds, recheck rights outside cache hits, isolate fake/live readers, never cache failed outcomes as success and invalidate only matching requests. Depends on T004, T011.
- [ ] T013 Compose the narrow injected acquisition/store/cache boundary in `src/market_leadership/bootstrap.py`; keep domain/application independent of Streamlit/legacy route internals, reuse the single selected financial reader and no fallback, and expose a callable usable by actual root workflows and the offline helper in `tests/company_evidence_helpers.py`. Depends on T012.
- [ ] T014 Run the shared domain/integration/config tests and affected existing fundamental/cache regressions, recording red-to-green evidence and foundation readiness in `specs/011-company-risk-evidence/quickstart.md`; do not start stories with unresolved shared identity, permission or persistence failures. Depends on T008, T009, T010, T013.

**Checkpoint**: Shared current acquisition works with simulated approved sources; production
sources remain unapproved. Historical/identity/permission limitations remain explicit.

## Phase 3: User Story 1 - Recognize Cash-Flow Risk and Evidence Gaps (Priority: P1) - MVP

**Goal**: Make unassessed/missing cash and actual cash consumption unmistakable before scores.

**Independent Test**: From a root AppTest with controlled source inputs, open a stock and verify
unloaded, positive, zero, negative, missing, failed, stale and incomparable cash states, including
simultaneous OCF concern/FCF gap, without any business-model or backlog collection.

### Tests for User Story 1 (Required)

- [ ] T015 [P] [US1] Add failing cash assessment/warning tests in `tests/unit/domain/test_company_evidence.py` for all cash states, zero versus absence, negative OCF/FCF, concurrent concerns/gaps, newest-quarter mismatch, 135/136-day reporting age, exact 3,600-second retrieval expiry, historical age basis and evidence-backed comparability exceptions; assert no weight change, zero imputation or distress inference. Depends on T014.
- [ ] T016 [P] [US1] Add failing actual-root banner/control tests in `tests/app/test_company_risk.py`; assert "Cash flow not assessed" before peer numbers, explicit financial load/current-date choice, affected measure/period/reason/action, independently visible valid scores, partial/stale handling, no added root/table columns or qualitative requests, and unchanged breadcrumbs. Depends on T014.

### Implementation for User Story 1

- [ ] T017 [US1] Implement CashFlowAssessment/CashFlowWarning and deterministic warning evaluation in `src/market_leadership/domain/company_evidence.py`; use categories `evidence_gap`, `cash_generation_concern`, retain "Concerns and gaps can coexist; positive quality/growth cannot hide them.", "Comparability exceptions require evidence/review, not a sector-name heuristic.", "Financial retrieval expires at >=3,600 seconds." and reporting age >135 days; require latest comparable OCF/FCF, preserve zero/negative observations and use historical assessment date for archival reporting age, not today's date. Depends on T015.
- [ ] T018 [P] [US1] Implement the shared cash banner in `src/market_leadership/ui/components/company_risk.py` with dated values/definitions and actionable gap/concern text; keep unavailable distinct from zero, never label negative FCF insolvency or positive cash investment suitability, and show missing capex independently when valid defined OCF/FCF exists. Depends on T016, T017.
- [ ] T019 [P] [US1] Implement explicit financial load/refresh and current/historical controls in `src/market_leadership/ui/workflows/company_evidence.py` using `market_leadership.company_evidence.` stable instrument/listing/context keys; resolve the listing at the actual evidence date, block unresolved identities, reuse valid data on reruns and clear only dependent assessment when context/mode changes. Depends on T013, T016, T017.
- [ ] T020 [US1] Wire the controls and banner into `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/ui/components/stock_detail.py`; pass captured snapshot/stock/listing/settings/chart date, place warnings before the chart/peer-score row, preserve valid peer/cohort and breadcrumb controls, and do not revive retired grading actions. Depends on T018, T019.
- [ ] T021 [US1] Run US1 domain/root tests and affected navigation/detail regressions, recording the controlled-state results in `specs/011-company-risk-evidence/quickstart.md`; verify SC-001 and MVP correctness with zero company-research requests and no production approval/activation. Depends on T020.

**Checkpoint**: Cash-risk warnings and explicit financial loading are independently usable.
Raw financial inspection/history refinements follow in US2; research remains separate.

## Phase 4: User Story 2 - Inspect Structured Financial Evidence for the Correct Company (Priority: P1)

**Goal**: Display inspectable, comparable financial facts, the existing eight metrics and their
provenance for the correct company without changing peer-score eligibility.

**Independent Test**: Explicitly load two controlled companies/listings and verify financial
identity, cash overview, periods/units/source/derivation, exact metric slots, partial failures and
current versus captured historical evidence; no qualitative source is required.

### Tests for User Story 2 (Required)

- [ ] T022 [P] [US2] Add failing detailed financial-contract cases in `tests/integration/test_company_evidence.py` for currency/scale/quarter/YTD/restatement conflicts, missing capex and definition, FCF derivation inputs, duplicate/non-finite values, similar-name/multiple-listing/reused-ticker identity, old metadata compatibility, historical cutoffs and partial error persistence. Depends on T021.
- [ ] T023 [P] [US2] Add failing financial overview/matrix/provenance root cases in `tests/app/test_company_risk.py`; require dated OCF/capex/FCF, source-supplied/derived labels, inspectable references, unknown publication dates explicitly disclosed, exact eight slots/4-8 histories and unchanged unavailable peer scores. Depends on T021.
- [ ] T024 [P] [US2] Add metadata/normalization regression cases in `tests/unit/test_fundamentals.py` and `tests/unit/domain/test_peer_scores.py` proving accepted legacy inputs retain all metric/aggregate formulas, missing values are not zero and richer Yahoo/disclosure metadata never invents vintage or capitalization eligibility. Depends on T021.

### Implementation for User Story 2

- [ ] T025 [US2] Complete detailed financial normalization/definition/provenance validation in `src/market_leadership/domain/company_evidence.py` and `src/market_leadership/infrastructure/yfinance_fundamentals.py`; enforce "Derived FCF requires finite aligned OCF/capex and verified outflow semantics, never zero defaults.", "source-supplied is not automatically issuer-reported.", "no FX conversion, invented start date or YTD-as-quarter substitution.", and "older cash is not forward-filled."; preserve source FCF independently and derive missing FCF as OCF minus verified positive capex outflow, retaining input IDs, original units and incompatible states. Depends on T022, T024.
- [ ] T026 [P] [US2] Add raw cash overview and financial provenance rendering to `src/market_leadership/ui/components/company_risk.py`; show values/state, period/basis, currency/scale, definition/origin and source references, retaining explicitly unknown original publication dates and old observations as limited evidence. Depends on T023, T025.
- [ ] T027 [US2] Reuse `src/market_leadership/ui/components/fundamental_matrix.py` beneath the existing chart/peer row in `src/market_leadership/ui/components/stock_detail.py`; keep its exact eight-slot/native-history/missing-data contract and warning precedence, and do not reactivate the retired grading workflow. Depends on T026.
- [ ] T028 [P] [US2] Reuse matching acquired rich financial bundles between company detail and existing cohort scoring through `src/market_leadership/ui/cache.py` and `src/market_leadership/application/score_industry.py`; match source/date/schema/context, avoid duplicate profile/ticker requests, never fetch qualitative research for peers, and preserve current historical guard and insufficient-vintage behavior. Depends on T022, T024, T025.
- [ ] T029 [US2] Complete current-versus-archive selection/disclosure in `src/market_leadership/ui/workflows/company_evidence.py`; label today's observations separately from old chart dates, filter captures through the requested UTC day's end, assess archival reporting age against that date and never erase history using live TTL or promise end-of-day completeness. Depends on T025, T027, T028.
- [ ] T030 [US2] Complete independent-component error/partial handling in `src/market_leadership/application/load_company_evidence.py` and its financial UI result path in `src/market_leadership/ui/workflows/company_evidence.py`; retain permitted valid facts, expose affected failures/definition limits and never attach wrong-profile partials, cache an error as complete, or silently replace current failure with old success. Depends on T022, T025, T029.
- [ ] T031 [US2] Run US2 acquisition/root and existing metric/cache/peer regressions, recording complete/incomplete financial provenance and zero cross-company attachment results in `specs/011-company-risk-evidence/quickstart.md`; verify SC-003/SC-004 and financial SC-008 behavior. Depends on T030.

**Checkpoint**: The P1 financial assessment is complete offline; actual source use remains
permission-gated. Unverified Yahoo vintages still yield insufficient peer scores.

## Phase 5: User Story 3 - Understand Business Model, Competitive Advantages, and Orders (Priority: P2)

**Goal**: Independently collect/display structured, attributable business and order evidence
without fabricating competitive durability or treating incompatible orders as one measure.

**Independent Test**: Controlled submissions, issuer documents/facts and reviewed claims produce
business fields, management claims/opinions and defined backlog/bookings/RPO. Denied, absent,
unmapped and conflicting evidence retain distinct limitations without financial-provider blending.

### Tests for User Story 3 (Required)

- [ ] T032 [US3] Create synthetic submissions, issuer HTML/tagged-fact/table documents, reviewed mappings and reviewed-claim inputs in `tests/fixtures/acceptance/company_evidence/disclosures/`; include annual 10-K/20-F, quarterly 10-Q, amended/future/conflicting contexts, no comparable foreign quarter, nonstandard backlog, separate bookings/RPO, business/competitive claims and accessible-unmapped versus genuinely inspected absence. Depends on T014.
- [ ] T033 [P] [US3] Add failing disclosure transport/extraction/permission cases in `tests/integration/test_company_evidence.py` using the US3 fixtures; verify exact issuer/accession/period/context/unit matching, source locators/mapping revision, request/time/size/retry limits, denial before requests, and no alternate-host or scored-financial fallback. Depends on T032.
- [ ] T034 [P] [US3] Add failing research-field/state/claim validation in `tests/unit/domain/test_company_evidence.py` for separate order definitions/qualifications, zero versus absence, independent opinion versus management claim, absent source/date limitations, 450/451-day annual and 135/136-day quarter age, unsupported structure and inspected-disclosure scope. Depends on T032.
- [ ] T035 [P] [US3] Add failing research root-control/rendering cases in `tests/app/test_company_risk.py`; load research independently with financial evidence unloaded, check citations and source-kind labels, preserve cash warnings, and prohibit invented moat/order values or complete-cohort qualitative requests. Depends on T021, T032.

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement research semantics in `src/market_leadership/domain/company_evidence.py`; enforce topics `business_model`, `competitive_advantage`, `orders`, kinds `reported_fact`, `management_claim`, `independent_opinion`, "Business keys: products/services, revenue model, customers/markets, segments.", and "backlog, bookings and remaining performance obligations are separate, definition-qualified fields."; use states `not_loaded`, `available`, `not_disclosed`, `unsupported_structure`, `not_comparable`, `stale`, `blocked`, `error`, require "Independent opinion requires a named source.", preserve "unmapped/inaccessible content is not absence.", annual age >450 days and quarterly >135 days with actual basis visible. Depends on T034.
- [ ] T037 [P] [US3] Implement bounded standard-library disclosure transport in `src/market_leadership/infrastructure/company_disclosures.py`; require approved source/issuer/domain and publisher contact, validate HTTPS/redirects/public destinations, enforce <=1 request/second, <=6 HTTP requests per operation, <=10 MiB/document, <=30-second attempts and <=10-second socket waits within remaining time, at most two transient retries inside budget, and Retry-After/deferred-retry behavior; never evade 401/403 or disclose headers. Depends on T033.
- [ ] T038 [US3] Implement approved CIK submissions/accession discovery and registered issuer-document selection in `src/market_leadership/infrastructure/company_disclosures.py`; choose at most latest eligible 10-K/20-F and 10-Q, retain filing/report/publication precision, handle amendments/foreign-quarter limitations explicitly, and reject issuer/future/mismatched metadata rather than crawl or guess mappings. Depends on T037.
- [ ] T039 [US3] Implement exact reviewed concept/context/unit/table extraction and short factual normalization in `src/market_leadership/infrastructure/company_disclosures.py`; retain accession/locator/mapping/definition/qualification, support approved Company Facts order research and issuer-specific backlog mappings without scored metrics, and return unsupported-structure versus successfully inspected absence honestly; no LLM, copied report body or keyword moat inference. Depends on T036, T038.
- [ ] T040 [US3] Add separately gated research scope to `src/market_leadership/application/load_company_evidence.py`; require reviewed CIK/domain binding, reuse already acquired permitted profile fields without requesting financial/cohort data merely for research, accept validated reviewed claims where interpretation is needed, and compose/persist source-specific partial/conflicting results without provider pooling. Depends on T039.
- [ ] T041 [US3] Render structured business/competitive/order sections in `src/market_leadership/ui/components/company_risk.py` with short factual fields, source-kind/date/definition/cancellation/coverage references, explicit not-loaded/unsupported/not-disclosed/stale/conflict states and no automatic moat badge or undisclosed order estimate. Depends on T035, T036, T040.
- [ ] T042 [US3] Add independent research load/refresh controls and actual-detail result wiring in `src/market_leadership/ui/workflows/company_evidence.py` and `src/market_leadership/ui/components/stock_detail.py`; preserve financial/breadcrumb state, source limitations and public reference links, and make root/table/cohort reruns produce no unsolicited research. Depends on T021, T041.
- [ ] T043 [US3] Run US3 domain/transport/root tests and P1 regressions, recording real structured-fixture collection, claim/definition distinctions and limitations in `specs/011-company-risk-evidence/quickstart.md`; verify SC-005 and source-separated SC-003/SC-006 behavior without real approvals or live traffic. Depends on T042.

**Checkpoint**: Useful partial research works against deterministic sources. Unsupported
disclosure structures are visible; coverage/permissions are never assumed market-wide.

## Phase 6: User Story 4 - Evaluate Sources and Refresh Evidence Safely (Priority: P2)

**Goal**: Provide reviewer operations and truthful refresh/cache/history behavior, including
permission changes after data was previously loaded.

**Independent Test**: Temporary-root CLI and root AppTests exercise approved/unapproved/revoked/
expired/blocked/conflicting sources, targeted refresh, immutable history and identity revisions,
with zero sensitive transmission, catalog writes or unauthorized cached display.

### Tests for User Story 4 (Required)

- [ ] T044 [P] [US4] Add failing reviewer CLI/cache/history integration cases in `tests/integration/test_company_evidence.py` for actual recorded IDs, required options/enum/date validation, explicit creation/revisions, no URL fetch on registration, verified claim import, expiration/revocation after cache hits, parser revision reuse, failures/atomic concurrency and catalog-hash invariance. Depends on T031, T043.
- [ ] T045 [P] [US4] Add failing source/history/privacy root cases in `tests/app/test_company_risk.py` for ordinary navigation reuse, one-company/scope refresh, new error over prior success, source/identity revision invalidation, retained dated conflict/history, safe references, mode changes and unchanged chart/breadcrumb/peer selection. Depends on T031, T043.
- [ ] T046 [P] [US4] Add failing current-permission/retention/safe-output tests in `tests/unit/domain/test_company_evidence.py` for unknown/expired/revoked independent grants, research versus financial roles, public identifiers only and no credentials/contact header/private selections in evidence or reports. Depends on T031, T043.

### Implementation for User Story 4

- [ ] T047 [P] [US4] Implement file-only `review-source` and `bind-issuer` argparse commands in `src/market_leadership/company_evidence_admin.py` with all acquisition-contract options, actual publisher/coverage/authority/structured-capability/terms/review records, source-role/use validation, ten-digit CIK/domain/effective-listing checks, `--evidence-root` and required `--expected-revision` (`none` only for creation); emit safe versioned JSON/nonzero errors and never grant rights by default or touch SQL/catalog activation. Depends on T044, T046.
- [ ] T048 [US4] Implement `register-document` and `import-claims` in `src/market_leadership/company_evidence_admin.py`; require verified binding/source/public references and review, accept `--published-on` or explicit `--publication-limitation` without invented dates, keep registered document metadata in the versioned binding registry, validate `company-reviewed-claims-1` input/locators/definitions, preserve revisions/history, and do not fetch URLs on registration. Depends on T047.
- [ ] T049 [US4] Enforce mutable assessment/binding/document eligibility and safe retained-history reads in `src/market_leadership/infrastructure/company_evidence_files.py` and `src/market_leadership/application/load_company_evidence.py`; recheck current grants on cached/archived/display paths, preserve "Research roles cannot authorize another scored feed.", expire/revoke affected uses with actionable context and never repair bad state through old success. Depends on T044, T046, T048.
- [ ] T050 [P] [US4] Complete targeted financial/research response/transform refresh in `src/market_leadership/ui/cache.py`; use exact 3,600/86,400-second TTLs, bounded keys including source/CIK/URL/accession/date/binding/assessment/content/mapping/schema, reuse successful payloads for permitted remapping, never cache failed normalized outcomes, and retain raw bodies only with raw-retention permission; otherwise cache only permitted normalized data and block incompatible retention/cache grants. Depends on T044, T046.
- [ ] T051 [US4] Complete new partial/error refresh publication and concurrent/interrupted-write handling in `src/market_leadership/infrastructure/company_evidence_files.py` and `src/market_leadership/application/load_company_evidence.py`; preserve "Failed refresh replaces the visible current operation status;" and "previous good data remains labelled history, never silent current fallback.", immutable predecessors and expected-pointer revisions; respect normalized/raw retention and expose persistence limitations without claiming success. Depends on T049, T050.
- [ ] T052 [US4] Add current source/identity revalidation, safe reference/conflict/history inspection and scope-specific refresh state handling in `src/market_leadership/ui/workflows/company_evidence.py` and `src/market_leadership/ui/components/company_risk.py`; protect session-local selections, retain historical-date age/labels without mutating snapshots and keep contact only in the required publisher transport header, not output/cache/logs. Depends on T045, T051.
- [ ] T053 [US4] Run US4 temporary-root CLI/integration/root tests and prior-story regressions, recording zero unauthorized collection/cached display, silent fallback, sensitive transmission, provenance overwrite and catalog mutation in `specs/011-company-risk-evidence/quickstart.md`; verify SC-006 and ordinary-navigation request reuse. Depends on T052.

**Checkpoint**: Reviewer tooling records actual evidence of permission, not permission itself.
Financial/research refresh and retained history are explicit and safe; live candidates stay disabled.

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Reconcile operating guidance and verify exact feature outcomes without manufacturing
live source approval, usability results or release readiness.

- [ ] T054 [P] Update `README.md` and `specs/011-company-risk-evidence/quickstart.md` with implemented controls/CLI/settings/test selectors (including config tests), isolated offline workflow, schema/cache compatibility, separate currencies/current-history meaning, source-access/retention restrictions, no FX/weight/peer-vintage changes, and persistent-directory requirements/limitations for hosted history. Depends on T053.
- [ ] T055 [P] Add and run warmed ordinary-navigation measurement cases in `tests/app/test_company_risk.py` covering actual root stock/ancestor navigation with loaded evidence, request counters and at least ten measured reruns; require every recorded redisplay <=1 second and zero extra research requests, report hardware/versions/sample sizes/elapsed values and iterate on tightly coupled causes if the exact SC-007 threshold fails. Depends on T053.
- [ ] T056 Conduct the five-user recognition exercise using controlled complete/incomplete company views and record anonymous case timings/outcomes in `specs/011-company-risk-evidence/quickstart.md`; require at least four of five identify cash assessment/main warning within ten seconds for SC-002; do not replace humans with agents or fabricate results, and leave this task blocked/unchecked if participants or verified measurements are unavailable. Depends on T054, T055.
- [ ] T057 Run combined focused feature/regression tests, Ruff and strict Pyright with the project interpreter, then the full offline suite when practical; record exact commands/outcomes and pre-existing versus introduced failures in `specs/011-company-risk-evidence/quickstart.md`, resolving only task-related regressions. Depends on T053, T055.
- [ ] T058 Reconcile additive evidence format/cache compatibility and the release-version decision with the then-current package baseline in `pyproject.toml`, `uv.lock` and `README.md`; preserve assigned release versions or select the next minor for an unassigned additive release, synchronize metadata through existing tooling if a bump is due, document version impact and do not migrate catalog data or add dependencies. Depends on T054, T057.
- [ ] T059 Review changed implementation against the pre/post-design constitution gates in `specs/011-company-risk-evidence/plan.md` and record related corrections/validation in `specs/011-company-risk-evidence/quickstart.md`; verify scoped single-source behavior, narrow ownership, cache/session privacy, no speculative services/collectors or legacy revival, and no unrelated fixes. Depends on T058.
- [ ] T060 Record operational source-access/rights/extraction-coverage and target-host persistence readiness in `specs/011-company-risk-evidence/quickstart.md`; unverified sources remain blocked/reference-only and a live one-company smoke test remains conditional on separate explicit authorization and genuine grants; do not activate catalogs, approve sources, retry blocked hosts or claim live coverage merely to close this task. Depends on T054, T059.
- [ ] T061 Record the final FR/SC acceptance summary and any blocked manual/operational gates in `specs/011-company-risk-evidence/quickstart.md`, and reconcile only genuinely verified checkboxes in `specs/011-company-risk-evidence/tasks.md`; no complete-release claim while SC-002/SC-007 or required deployment permission/persistence evidence is missing. Depends on T056, T057, T060.

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup T001-T002
  -> Foundations T003-T014
      -> US1 T015-T021
          -> US2 T022-T031 ----+
          -> US3 T032-T043 ----+-> US4 T044-T053
                                   -> Polish T054-T061
```

Every story requires the shared foundation checkpoint. US2 uses the US1 actual-root financial
controls/banner. US3's root integration uses US1, but its fixtures/reader/domain work can begin
after foundations and does not depend on US2's matrix. US4 full acceptance requires US2 and US3;
its reviewer helpers can be prepared earlier against the shared store, but cannot be marked
complete before their contract tests and dependencies are satisfied.

The two P1 phases precede P2 in the recommended delivery sequence. Shared domain, integration
and root test files prohibit whole-story concurrent edits even where the logical graph branches.

### User Story Dependencies

| Story | Required completion | Independent result |
|-------|---------------------|--------------------|
| US1 | T014 | Dated cash gaps/concerns before scores; financial load, no research. |
| US2 | T021 | Correct-company financial overview/matrix/provenance and guarded history. |
| US3 | T014 for reader/domain; T021 for root integration | Independently loaded cited business/competitive/order facts with honest limits. |
| US4 | T031 and T043 | Reviewer operations, current permission, scoped refresh and immutable history. |

### Within Each User Story

Explicit task dependencies are authoritative. Tests fail first; domain validation precedes
reader/use-case/rendering; actual-root wiring precedes story checkpoint. Source/clock/store
boundaries are injected; partial/error states remain observable. No implementation task may
skip its red test or mark a later manual acceptance criterion completed by proxy.

### Parallel Opportunities

Safe batches once their prerequisites are complete:

- Foundation tests T003/T004/T005 (three distinct test files).
- T006/T009, then T008/T010 after T007 (distinct domain/config/store/reader files).
- US1 tests T015/T016; UI component/workflow T018/T019 after T017.
- US2 tests T022/T023/T024; component T026 and cache/cohort work T028 after T025.
- US3 tests T033/T034/T035; research domain T036 and transport T037.
- US4 tests T044/T045/T046; reviewer CLI T047 and cache work T050.
- Polish documentation T054 and measurement code T055; merge recorded measurements into
  quickstart serially through T056/T061.

Do not run these batches across unrelated phases while another task edits the same file.
The `[P]` markers mean readiness-conditioned parallelism, not all tasks launching immediately.

## Parallel Example: User Story 1

After T014, add T015 domain tests and T016 root tests concurrently. After both are red and
T017 is complete, T018 component and T019 workflow edits are disjoint. Join at T020/T021.

## Parallel Example: User Story 2

After T021, T022 integration, T023 root and T024 legacy-metric/peer tests have separate files.
After T025, T026 component and T028 cache/cohort work can proceed independently; coordinate
the root/history integration tasks afterward.

## Parallel Example: User Story 3

After T032 and US1 root readiness, T033 integration, T034 domain and T035 root tests are
disjoint. T036 research semantics and T037 HTTP transport can proceed independently; T038/T039
share the disclosure reader and must be sequential.

## Parallel Example: User Story 4

After T031/T043, T044 integration, T045 root and T046 domain tests are disjoint.
T047 CLI and T050 cache implementation do not edit the same files; current-policy/history/UI
tasks join their dependencies before T053 acceptance.

## Implementation Strategy

### MVP First (User Story 1)

Finish T001-T014, then T015-T021. This produces useful, correctly attached cash warnings with
explicit financial loading, without waiting for disclosure extraction or reviewer CLI.
Use only simulated approvals for verification; unknown production use remains blocked.

### Incremental Delivery

1. US1: warning-first risk visibility.
2. US2: full financial inspection/provenance/history while preserving current score formulas.
3. US3: source-linked business/competitive/orders research with explicit coverage gaps.
4. US4: reviewer administration and safe changing-permission/refresh/history operations.
5. Cross-cutting measured/human/release checks; separate operational permission from offline readiness.

### Parallel Team Strategy

Use only ready disjoint-file batches above. Keep a single owner for shared domain/test/workflow
files during each batch. Do not commit or switch branches automatically; preserve user work.

## Requirement and Outcome Coverage

| Requirements | Implementing / verifying tasks | Outcomes |
|--------------|--------------------------------|----------|
| FR-001, FR-002 | T020, T024, T027, T028, T031, T057 | SC-008 |
| FR-003, FR-007 | T007, T010, T011, T022, T025-T027 | SC-003 |
| FR-004, FR-005, FR-006 | T015-T021, T023, T056 | SC-001, SC-002 |
| FR-008 | T006, T010, T023, T026, T039, T041, T052 | SC-003 |
| FR-009 | T003, T006, T010, T011, T022, T029, T031, T038 | SC-004 |
| FR-010, FR-011, FR-012 | T032-T043, T048 | SC-003, SC-005 |
| FR-013 | T006, T008, T044, T047-T049, T060 | SC-006 |
| FR-014, FR-015 | T011-T013, T024, T028, T033, T037-T040, T046-T050 | SC-006 |
| FR-016, FR-017 | T012, T019, T028, T042, T045, T049-T053, T055 | SC-006, SC-007 |
| FR-018 | T017, T025, T029, T030, T034, T036, T039-T043, T051, T052 | SC-003, SC-005, SC-006 |
| FR-019, FR-020 | T001, T004-T013, T044-T053, T059 | SC-006 |
| FR-021 | T016-T021, T035, T041, T045, T059 | SC-008 |

## Notes

- 61 pending tasks: setup 2, foundations 12, US1 7, US2 10, US3 12, US4 10, polish 8.
- No implementation or test execution occurred during task generation.
- Live rights/access cannot be manufactured. Human recognition is a real manual gate; leave
  blocked tasks unchecked instead of asserting success.
- Generation validates syntax/coverage/dependencies, not implementation correctness. Run
  `/speckit-analyze` before `/speckit-implement` for cross-artifact quality review if desired.
