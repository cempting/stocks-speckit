# Tasks: Market Structure Service and Persistent Observation Cache

**Input**: Design documents from `/specs/013-market-structure-service/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).
The [constitution](../../.specify/memory/constitution.md) remains binding.

**Refreshed**: 2026-11-04 against all four approved analysis refinements. This backlog
supersedes the earlier 90-task draft; IDs are renumbered in execution order. Checkboxes
record validated implementation progress. The normative [policy schema](contracts/observation-policies.schema.json)
is a design input to package and test, not a second schema to reinvent.

**Tests**: Required by FR-022, the plan's test-first slices, and the constitution.
Write each slice's tests first and demonstrate the expected failure before implementing
missing behavior. Tests use controlled HTTP, injected clocks, temporary roots, and
recording providers; never production data or live acquisition. Existing behavior that
already satisfies a new regression assertion need not be deliberately broken.

**Organization**: Setup, shared prerequisites, five user-story phases in priority order,
then cross-cutting release gates. All tasks start unchecked; these are implementation
tasks, not claims that the planned service or performance results already exist.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies disjoint-file work eligible for the explicit parallel batches below,
  after its prerequisites. It does not waive test-first or phase gates.
- `[US1]` through `[US5]` map to the stories in the specification.
- Paths are repository-relative and name the intended post-move location unless a move
  explicitly names the current location. Preserve canonical Python import identity.
- Constraints in quotation marks reproduce the data model's normative wording;
  transport and cache contracts supply additional exact limits.

## Path Conventions

- Root distribution: `src/market_leadership/`, `pyproject.toml`.
- Shared distribution: `packages/market-data/src/market_data/`.
- Service and offline tools: `services/market-structure/src/market_structure/` and
  `services/market-structure/src/market_data_tools/`.
- Controlled validation: `tests/contract/`, `tests/integration/`, `tests/app/`,
  `tests/support/`, and `tests/fixtures/market_structure/`.

**2026-11-06 integration reconciliation**: Existing tabs are Discovery, Industry Deep-Dive,
Yahoo Classification Preview and Find a stock. 015 owns lookup placement; 012 retains
identity/listing safeguards. All four consume one pinned validated service context, including
preview source permissions and lookup history/evidence actions. Preserve independent widget
namespaces and zero hidden loads. Task IDs, dependencies and completed markers are unchanged;
the following integration work remains unchecked, not implemented by this documentation edit.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish three independently installable distributions without changing
reviewed data or accidentally coupling the service to the app.

- [X] T001 Record the pre-move non-live regression, Ruff, strict Pyright, wheel, and existing CLI baseline in `specs/013-market-structure-service/quickstart.md`; inventory current namespace/resource/entry-point ownership from `pyproject.toml`, keep unrelated dirty work intact, and do not migrate production data.
- [X] T002 Add failing distribution/import-isolation regressions in `tests/contract/test_package_boundaries.py` and `tests/contract/test_service_distribution.py` for shared-only, app-only, service-only, and optional-maintenance installs; cover schema resources, canonical class/alias identity, script ownership, and actionable missing-extra errors.
- [X] T003 [P] Move `src/market_data/` intact to `packages/market-data/src/market_data/` and add `packages/market-data/pyproject.toml`; retain existing v1/v2 resources, public imports, compatibility aliases, and only the shared namespace's actual dependencies, with no UI, acquisition-provider, tools, or server dependency.
- [X] T004 [P] Move `src/market_data_tools/` intact to `services/market-structure/src/market_data_tools/`, create `services/market-structure/src/market_structure/__init__.py`, and add `services/market-structure/pyproject.toml`; own all maintenance scripts and declare Starlette `>=0.47,<1`, Uvicorn `>=0.35,<1`, and `market-data`, without Streamlit/yfinance/Massive.
- [X] T005 Configure workspace members and local dependency sources in `pyproject.toml`, make the root wheel app-only with `market-data` and HTTPX `>=0.28,<1`, add the optional `maintenance` extra, transfer maintenance script ownership to the service distribution, and resolve `uv.lock` only after manifest changes.
- [X] T006 Update pytest source paths, strict Pyright includes, build/resource paths, and source-root assertions in `pyproject.toml` and `tests/contract/test_package_boundaries.py` for all three roots; find and adapt remaining assertions referring to `src/market_data` or `src/market_data_tools` without weakening architecture guards.
- [X] T007 Update optional delegates in `src/market_leadership/catalog_admin.py`, `src/market_leadership/company_evidence_admin.py`, and `src/market_leadership/universe_admin.py` to load tools only on explicit administration and explain installation of the maintenance extra when absent; do not mask unrelated import failures.
- [X] T008 Run the applicable T002 wheel/resource/import checks and existing moved-package tests, and record results in `specs/013-market-structure-service/quickstart.md`; validate namespace and dependency isolation now, reserving new service/cache command execution for their implementation phases.

**Checkpoint**: Three distribution boundaries are real. Ordinary app installation does
not install the server/tools, and service installation does not install the stock app.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Supply reusable, non-production test infrastructure and exact existing
evidence codecs. Do not bury story-specific server or cache implementation here.

- [X] T009 [P] Create `tests/fixtures/market_structure/__init__.py` and `tests/fixtures/market_structure/build_demo.py` with the documented `--output` interface, generating a synthetic reviewed v1/v2 catalog and four explicit registries, nested/overlapping memberships, multiple listings, true indexes, and news metadata; no production fixture-provider option or acquisition.
- [X] T010 [P] Add controlled HTTP transports, recording provider doubles, frozen clocks, fault injection, and cross-process call accounting in `tests/support/market_structure.py`; support empty/partial/failed responses and independent processes without importing test helpers into production.
- [X] T011 [P] Add exact association/assessment round-trip, fingerprint, nullable-identifier, expiry, and reference-only permission regressions in `tests/contract/test_market_structure_evidence.py` using existing company-evidence records and validators.
- [X] T012 Expose or reuse exact typed evidence codecs in `packages/market-data/src/market_data/company_evidence.py` for the T011 cases; preserve financial/disclosure/reference semantics and prohibit reference-only assessments from authorizing acquisition or retention, without adding tools/server imports.

**Checkpoint**: Shared fixtures and existing evidence semantics are ready. Complete this
phase before story implementation; T009-T011 can be authored concurrently.

---

## Phase 3: User Story 1 - Browse a market organized by an independent authority (Priority: P1) - MVP

**Goal**: Publish and independently serve one reviewed, immutable structure revision.

**Independent Test**: Stop the stock app and all live providers. Publish controlled
reviewed bytes, connect a controlled consumer, and verify one coherent hierarchy,
memberships, stock/ETF/index identities, source metadata, permissions, and revision.
Reject incompatible/incomplete candidates without changing current. Full stock-app
composition is the next slice, not part of this standalone service demonstration.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add failing payload/registry contract tests in `tests/contract/test_market_structure_snapshot.py` for every data-model constraint, existing v1/v2 validation, exact bytes/hashes, four registries, safe paths, unknown fields/formats, references and record limits; exercise the normative policy schema with format checking, all status/nullability combinations, integer/boolean/limit boundaries, exact currency/digest/timestamp endings, invalid/future/non-UTC reviews and leap seconds, canonical key-order/precision invariance, array-order sensitivity and Unicode escaping, plus reference-only/news non-authorization.
- [ ] T014 [P] [US1] Add failing shared permission-guard tests in `tests/contract/test_market_structure_permissions.py` for scoped source/provider and legacy source/role matching, renamed policy/assessment IDs, removed grants, shorter scope/expiry/retention, review high-water cutoffs, backdated denials, fresh versus publication-only review, ambiguous same-day legacy review, display-only versus retention removal, and irreversible bounds on previously acquired rows; test syntax separately from current authorization.
- [ ] T015 [P] [US1] Add failing five-route OpenAPI/HTTP tests in `tests/contract/test_market_structure_http.py` for status/error bodies, readiness including missing/corrupt required permission guards, exact representation ETags, RFC weak/list/wildcard conditional matching, bodyless 304, cache headers, authentication, unpublished objects, traversal/symlinks, and rejected HTTP writes; private guard metadata must not change public entry fields, object kinds or endpoint count.
- [ ] T016 [P] [US1] Add failing publication and controlled-consumer tests in `tests/integration/test_market_structure_publication.py` and `tests/integration/test_market_structure_delivery.py` for expected-current conflicts, export review, concurrent writers and fsync/replace uncertainty; test approved-to-revoked-to-obsolete-rollback rejection, fresh qualifying reapproval, historical catalog plus current restrictive registries, guard persistence before a pointer fault, minimum guard generations and restart, zero guard changes on invalid candidates/dry-run, and serving with app/providers blocked.

### Implementation for User Story 1

- [ ] T017 [US1] Add snapshot/entry/object DTOs in `packages/market-data/src/market_data/domain/market_structure.py`: `format` is "Literal `market-structure-snapshot-1`", `created_at` is "Timezone-aware UTC publication time", `catalog` is "Catalog manifest logical path, original format, release ID and computed catalog revision", and `objects` are "Unique logical paths with SHA-256, exact byte size and object kind"; enforce "`snapshot_id = SHA256(exact manifest bytes)`" outside its own manifest, the exact entry format, and the six OpenAPI object-kind values.
- [ ] T018 [US1] Add `SourceRegistry`/`SourceRegistration` to `packages/market-data/src/market_data/domain/market_structure.py` with `format=market-structure-sources-1`, `sources`, and `assessments`; retain `source_id`, `name`, "`kind` (`market_data`, `financial`, `disclosure`, `news`, `reference`)", "`location` (credential-free HTTPS URL or null)", "`region_ids` (explicit applicability; empty means no regional assertion)", "`scope_refs` (explicit existing classification/node scopes)", `provenance_reference`, and "`review_state` (`unreviewed`, `approved`, `denied`, `revoked`)"; enforce "Source IDs are unique." and compatible assessment role/kind, without acquisition grants from registration.
- [ ] T019 [US1] Add `IssuerBindingRegistry` to `packages/market-data/src/market_data/domain/market_structure.py` with `format=market-structure-bindings-1`, `bindings`, and exact serialized `CompanyAssociation` records retaining "independently reviewed nullable issuer identifiers"; enforce "Duplicate association IDs or conflicting active bindings fail." and "Each binding must match a candidate catalog stock/listing and its `catalog_revision`." without rewriting review provenance.
- [ ] T020 [US1] Add `ObservationSourcePolicy` and its registry to `packages/market-data/src/market_data/domain/market_structure.py` with `format=market-structure-observation-policies-1` and `policies`; constrain `policy_id`/`source_id`/`provider_id` to "Unique policy identity and registered observation provider", `status` to "`unreviewed`, `approved`, `denied`, `revoked`", `reviewed_at` to "UTC review timestamp string or null, conditional on status", `review_reference` to "Nonblank review reference or null, conditional on status", `expires_at` to "ISO `YYYY-MM-DD` inclusive UTC expiry date or null, conditional on status", `allowed_uses` to "Unique array drawn from `collection`, `display`, `normalized_retention`; no implicit grant", scope fields `region_ids`/`currencies`/`frequencies`/`return_bases` to "Exact approved scope", `freshness_seconds` to "Approved: integer 1 through 3600; otherwise null or a prior reviewed positive limit", `max_retention_days` to "Approved: explicit positive integer; otherwise null or a prior reviewed positive limit; no default duration", and `fingerprint` to "Lowercase SHA-256 of canonical fields excluding this fingerprint"; enforce "Every listed field is present, including explicit nulls; unknown fields fail.", "IDs/references are nonblank strings without NUL.", unique ordered scope/use arrays and uppercase three-letter currencies; apply the exact approved/denied/revoked/unreviewed nullability rules, UTC timestamp/date expiry boundaries, provider-capability references, and canonical sorted compact ASCII-escaped UTF-8 fingerprint recipe in the data model without changing existing assessment formats.
- [ ] T021 [US1] Add `IndexRegistry`/`IndexReference` to `packages/market-data/src/market_data/domain/market_structure.py` with `format=market-structure-indexes-1`, `indexes`, and `index_id`, `name`, `region_id`, `provider_id`, `provider_symbol`, `calendar_id`, `currency`, `return_basis`, `effective_from`, `effective_to`, `source_id`, `approval_reference`, and "`context_purposes` (explicit informational uses)"; enforce "Stable IDs and active provider aliases are unambiguous." and "Currency/calendar and provider capabilities must match." while preserving the stock/ETF Listing enum and existing ETF selections.
- [ ] T022 [US1] Add typed versioned private guard records in `packages/market-data/src/market_data/domain/market_structure.py` with format `market-structure-permission-guard-1`; preserve "Entries retain source ID, provider ID for observation policies or existing assessment role, affected scope/use bounds, restricting record fingerprint and snapshot ID, review timestamp/date/reference, UTC `observed_at`, review high-water marks/cutoffs, and tighter retention limits."; define validated guard generation/minimum-pointer metadata, match stable source scopes rather than policy IDs, preserve legacy date-only evidence, and keep guards restrictive rather than an authorization or public HTTP object.
- [ ] T023 [US1] Add envelope/entry and registry schemas in `packages/market-data/src/market_data/schemas/market-structure.schema.json`, `packages/market-data/src/market_data/schemas/market-structure-sources.schema.json`, `packages/market-data/src/market_data/schemas/market-structure-bindings.schema.json`, and `packages/market-data/src/market_data/schemas/market-structure-indexes.schema.json`; package the normative `specs/013-market-structure-service/contracts/observation-policies.schema.json` unchanged as `packages/market-data/src/market_data/schemas/market-structure-observation-policies.schema.json`, including exact string bounds and conditional nullability, and verify resource equality; preserve OpenAPI exact fields/digests, 5-256 objects, 64 MiB per object, 1 GiB distinct total, 1 MiB entry/manifest/record and existing stricter catalog bounds.
- [ ] T024 [US1] Implement complete exact-byte bundle capture/materialization/validation in `packages/market-data/src/market_data/structure.py` using existing `load_release` and T012 codecs; require "Exactly one existing reviewed catalog release, source registry, issuer-binding registry, observation-policy registry, and index registry per snapshot.", explicit empty registries, reference/fingerprint integrity, portable contained POSIX paths, and no symlinks, inferred approvals, fetched content, credentials, or weakened catalog grammar.
- [ ] T025 [US1] Implement shared pure guard comparison/merge and effective-rights evaluation in `packages/market-data/src/market_data/structure.py` after T022/T024; enforce "Matching uses those stable identities/scopes, not policy/assessment IDs alone: renaming an ID cannot bypass a restriction.", monotonic scoped review high-water/cutoff rules and "Positive-review high-water marks alone do not relax any bound."; relaxation needs a correctly scoped approved record with different fingerprint/reference and strictly later review time, removed grants use observed-time cutoffs, legacy same-day ambiguity blocks with guidance, and old-row retention caps remain irreversible while display-only restrictions do not shorten authorized retention.
- [ ] T026 [US1] Implement the immutable object/snapshot store and local publisher in `services/market-structure/src/market_structure/store.py`; use explicit export review, bounded captures, digest allowlists of published snapshots, writer locking, expected snapshot or `none`, fsynced staging, atomic CURRENT, preserved history, and truthful `not_published`/`published`/`unknown` outcomes with operation IDs.
- [ ] T027 [US1] Add guarded publication and restart-safe private state to `services/market-structure/src/market_structure/store.py` using T025; enforce "Persist/fsync tightened guard state before any corresponding CURRENT activation.", minimum required guard generations and conservative tightening after pointer failure, reject obsolete historical grants without CURRENT replacement, allow reviewed historical catalogs with current restrictive registries, and block readiness on missing/corrupt required guards; writer-lock all guard updates, learn only fully validated candidates, keep invalid/dry-run inputs mutation-free, preserve guards through rollback, and never treat publication review as source reapproval or expose private state in HTTP entry bytes.
- [ ] T028 [US1] Implement `GET /healthz`, `/readyz`, `/v1/current`, `/v1/snapshots/{snapshot_id}/manifest`, and `/v1/objects/{sha256}` in `services/market-structure/src/market_structure/app.py` against the published store only; match all OpenAPI responses, sanitized errors, exact-byte ETags and RFC conditional semantics, `no-cache` current versus private immutable objects, bearer denial, and no arbitrary file serving, HTTP authoring, compression, or acquisition.
- [ ] T029 [US1] Implement documented `publish` and `serve` commands in `services/market-structure/src/market_structure/cli.py`; require explicit paths/expected snapshot/review reference, versioned JSON and exit 2 on failure/conflict/uncertainty, zero published changes on dry-run, loopback defaults, explicit non-loopback configuration/read token with TLS deployment guidance, eight concurrent responses by default, and read-only serving ownership.
- [ ] T030 [US1] Execute T013/T014/T015/T016 and independent service wheel/CLI checks from `tests/contract/test_service_distribution.py`, verify exact policy grammar/fingerprints, durable guarded rollback, news metadata with zero article requests and additive index identities, and record the US1 result in `specs/013-market-structure-service/quickstart.md` without claiming app integration or observation benchmarks are complete.

**Checkpoint**: Deployable service-contract MVP. Maintenance and serving work without the
stock app, observation cache, or live provider; the consumer verifies exact reviewed bytes.

---

## Phase 4: User Story 2 - Open the stock app with no local observations (Priority: P1)

**Goal**: Consume a validated service revision and automatically retain only the active
view's required observations, with mode/permission gates present from the first integration.

**Independent Test**: Start with empty explicit replica/observation roots, controlled
HTTP, and a recording provider. Open one view; verify correct returned/rendered values,
only necessary price/benchmark/representation calls, durable files, explicit partial
failures, zero automatic financial/research/news acquisition, and no fixture fallback.

### Tests for User Story 2

- [ ] T031 [P] [US2] Add failing client/replica tests in `tests/contract/test_market_structure_client.py` for streamed bounds/timeouts, fixed-origin routes, rejected redirects, hashes, changed-object reuse, usable/unusable 304, incomplete candidates and failed activation; cover durable guard generations, guard-fsync-before-CURRENT faults, newest guard with older CURRENT, missing/corrupt required guards, invalid-candidate non-mutation, and rollback/restart without old approval revival.
- [ ] T032 [P] [US2] Add failing cold-start/target/store tests in `tests/integration/test_observation_bootstrap.py`, `tests/contract/test_observation_targets.py`, and `tests/unit/infrastructure/test_observation_store.py` for empty/unwritable roots, typed stock/ETF/index targets, official sessions, null-volume index versus incomplete stock volume, initial monthly commit and partial success; assert shared reads/exclusive commits, no lock upgrade, bounded total contention, stable lock identity, offline missing-series no-write behavior, malformed output, and exact active-view-only call accounting.
- [ ] T033 [P] [US2] Add failing composition/AppTests in `tests/app/test_market_structure_context.py` for all four root tabs using one service-derived context and pinned revision/date; cover Discovery/Deep-Dive hierarchy, dedicated retained/unassigned lookup with exact listing identity, preview permissions without classification approval, independent widget keys, no alternate local authority, zero hidden history/evidence loads, news metadata only, and initial online/read-only/rejected-update/blocked behavior including 401/403.

### Implementation for User Story 2

- [ ] T034 [US2] Define immutable context, typed targets/series identities, query/result/coverage metadata and injected clock/store/transport/current-guard boundaries in `src/market_leadership/application/ports.py`; include all `StructureReadContext` fields and mode values "`online`, `offline_read_only`, `rejected_update_read_only`, `blocked`", "`subject_kind` (`listing` or `index`)", stable subject IDs, dated provider/source mappings, currency/calendar/frequency/kind/basis/normalization/continuity and separate permission provenance; retain "nullable `volume`" and coverage states "never requested, available, missing, stale, unavailable, error, or basis-invalidated."; unavailable diagnostics must "Persist identity/eligible interval, provider confirmation code/reference, attempt ID, `checked_at`, and applicable policy fingerprint as diagnostic metadata, never price rows or complete coverage."
- [ ] T035 [US2] Add explicit service URL/token/replica/observation-root settings and validation in `src/market_leadership/config.py` for the four documented environment variables; production requires the URL, remote access requires HTTPS/bearer, local files remain maintenance inputs only, and unsupported distributed/NFS cache configurations fail explicitly rather than reactivating local catalog, SQLite, or embedded defaults.
- [ ] T036 [US2] Implement HTTPX conditional streaming in `src/market_leadership/infrastructure/market_structure_client.py` with connect/read/pool timeouts 2/5/2 seconds, a 30-second per-download elapsed budget, at most two concurrent downloads and one bounded transient retry; enforce T023 sizes/hashes and fixed routes, reject redirects, sanitize secrets, and handle unusable 304 with one unconditional retry.
- [ ] T037 [US2] Implement validated replica staging, digest reuse, atomic activation, and separate attempted/successful check metadata in `src/market_leadership/infrastructure/structure_replica.py`; never accept an incomplete candidate or advance successful-check time on failure, preserve prior validated bytes, and never expose the replica as an editable review authority.
- [ ] T038 [US2] Persist/merge/load private replica guards in `src/market_leadership/infrastructure/structure_replica.py` through the T025 comparison rules; enforce "A newer guard remains effective even when CURRENT is older after an activation failure", minimum-generation integrity, writer-locked fsync before activation, no learning from invalid/dry-run inputs or ordinary offline navigation, and no 304/restart/renamed-policy/old-CURRENT reset; preserve conservative restrictions after activation faults, keep failed successful-check time unchanged, and expose typed blocked/recovery outcomes without converting metadata writes into content success.
- [ ] T039 [US2] Implement `src/market_leadership/application/load_market_structure.py` using "Use the injected real clock for permission evaluation even when the requested analysis date is historical." and "Pin the context for an entire view/action."; implement every data-model mode transition, startup/needed-after-300-seconds/explicit checks, no rerun retry loop, and blocked authentication even when bytes are retained.
- [ ] T040 [US2] Implement the first complete per-series monthly Parquet/generation read-write path in `src/market_leadership/infrastructure/observation_store.py` under the contract's `v1/series/<prefix>/<key>/` layout; rows contain `session_date`, `close`, nullable `volume`, `source_available_on`, `retrieved_at`, `last_validated_at`, and `retention_deadline` in UTC, enforcing "Dates are unique and ordered; prices are finite/positive, reported volumes finite/nonnegative."; pin complete manifests with the full month map, hashes/coverage/gaps/epoch/attribution, use locks and fsync-before-atomic-CURRENT, reject incompatible/corrupt state visibly, and retain previous valid coverage on failure.
- [ ] T041 [US2] Complete the initial read/write lock lifecycle in `src/market_leadership/infrastructure/observation_store.py` before production wiring: shared lock before CURRENT through selected rows/attempt-gap metadata materialization, exclusive acquisition/commit, lexical key order and two seconds total action contention including readers; enforce "Release shared locks before requesting exclusive locks; never upgrade in place." and "Committed series retain a stable `.lock` inode even when all price rows are pruned"; readers never create files, missing offline series are explicit missing coverage, committed missing locks are corruption, and no series-lock wait may retain a replica/publication writer lock.
- [ ] T042 [US2] Refactor `src/market_leadership/application/request_market_data.py` to resolve reviewed IDs/continuity from one context before raw symbols, compute stable canonical keys, create storage only on demand, and apply selected-source rights plus current durable guard before retained returns/provider calls/retention/commit/final output; use T041 lock lifecycle, fetch only active eligible targets from the one selected approved provider, withhold guard-invalidated actions for coherent reload, and return typed partial/error outcomes rather than empty success.
- [ ] T043 [US2] Wire the context, replica, store, policy/issuer registries, and gated `build_request_provider` in `src/market_leadership/bootstrap.py`; remove mutable local assessment/binding authority while retaining `CompanyEvidenceFiles` for permitted fetched financials/research/claims and preserving dependency injection for controlled tests.
- [ ] T044 [US2] Adapt canonical provider validation and `src/market_leadership/infrastructure/yfinance_provider.py` for explicitly resolved true-index targets with unavailable official volume; preserve normal stock/ETF volume evidence and selected-provider geography/currency capabilities, reject unsupported targets explicitly, and do not widen the catalog listing enum or invent zero volume.
- [ ] T045 [US2] Replace direct local catalog reads in `src/market_leadership/app.py`, `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/ui/workflows/industry_deep_dive.py`, `src/market_leadership/ui/workflows/stock_lookup.py`, and `src/market_leadership/ui/workflows/yahoo_classification_preview.py` with one injected context; retain all four tabs, 015 lookup placement, 012 identity/listing safeguards, independent widget state and existing navigation/rollups/score formulas, show supplied news metadata without article loading, and render blocked/setup guidance before dependent work.
- [ ] T046 [US2] Route Discovery benchmark/representation and member caches through typed gated queries in `src/market_leadership/ui/cache.py` and `src/market_leadership/ui/workflows/discovery_page.py`; gate explicit preview reads in `src/market_leadership/infrastructure/yahoo_classifications.py` and `src/market_leadership/ui/workflows/yahoo_classification_preview.py` through the same pinned source/mode/permission context without approving classifications or treating preview fields as price-series observations. Retain `st.cache_data` with provider, resolved symbol mappings, requested dates/parameters, identity/policy/observation generations and derived structure revision in appropriate keys, exclude credentials/user selections, and evaluate current guard/mode/rights outside cached functions before a hit or final output returns.
- [ ] T047 [US2] Wire member/selected-listing history in `src/market_leadership/application/load_stock_history.py` and `src/market_leadership/ui/workflows/industry_deep_dive.py` through the same provider/store boundary, preserving `prepare_listing_history_window`, issuer revalidation, listing-period eligibility, and explicit financial/research loading.
- [ ] T048 [US2] Refactor the daily snapshot CLI in `src/market_leadership/application/build_snapshot.py` to obtain service context and exact reviewed targets before the shared request path; reject ambiguous symbol-only ownership and disallowed modes/permissions, preserve pure injectable weekly calculations, and leave no direct production provider bypass or synthetic-seeding option.
- [ ] T049 [US2] Run the T031-T033 selectors and affected provider/history/snapshot AppTests, inspect actual call sets and partial outputs, and record cold-start results in `specs/013-market-structure-service/quickstart.md`; verify directory failures are actionable and offline/blocked entry points issue zero acquisition calls.

**Checkpoint**: A clean stock app consumes the service and creates useful durable data on
demand. Basic outage, denial, and pre-cache permission gates already work; US5 completes
the full fault/recovery matrix rather than introducing these restrictions late.

---

## Phase 5: User Story 3 - Reuse and extend the same observations across views (Priority: P1)

**Goal**: Reuse durable interval coverage across navigation/restarts and update only
relevant gaps, with coherent correction, retention, and cross-process behavior.

**Independent Test**: Browse A -> overlapping B -> A, change request batches, restart,
and extend 252 sessions by five. Inspect values/IDs/row counts/hashes/source calls.
Exercise real concurrent misses, failed waiters, and interrupted commits.

### Tests for User Story 3

- [ ] T050 [P] [US3] Add failing identity/generation/cache semantics tests in `tests/contract/test_observation_cache.py` for key inclusions/exclusions, retained provenance, ordered unique dates, nullable volume, full manifest maps, exact relevant-month reads, incompatible versions, corruption, and per-series generation vectors rather than a fictitious global timestamp.
- [ ] T051 [P] [US3] Add failing A/B/A/restart, extension, stale-tail/revalidation, adjustment/correction and partial/refresh tests in `tests/integration/test_observation_reuse.py`; assert exact sessions/calls/values, <=one eligible overlap and untouched hashes; cover confirmed versus unconfirmed gaps, `checked_at` freshness boundaries, current-tail versus historical/left-tail classification, reconfirmation without retention renewal, failed automatic recheck suppression through restart, explicit retry, and zero offline rechecks or invented coverage.
- [ ] T052 [P] [US3] Add failing real-process lock/coalescing/crash tests in `tests/integration/test_observation_concurrency.py` for one upstream call and shared failure including due no-data rechecks, lexical ordering and two seconds aggregate wait across shared/exclusive multi-series waits, release-before-exclusive/recheck, process-death release and commit faults; pause readers after CURRENT selection while prune competes, verify materialized rows/diagnostics stay pinned, prune contention deletes nothing, the final-row prune preserves the open lock inode, offline misses create nothing, committed missing locks are corruption, and replica/publication writer locks never remain held while waiting for series locks.
- [ ] T053 [P] [US3] Add failing clock-boundary/retention/prune tests in `tests/integration/test_observation_retention.py` for original retrieval/deadline preservation, guard-based tightening/removal versus display-only restrictions, rollback/restart and fresh-review irreversibility for old rows, permitted genuinely new acquisition, expiry before in-memory hits, mixed retained/expired rows, obsolete generations, dry-run, path containment, and actual physical removal without an expired-generation reader workaround.

### Implementation for User Story 3

- [ ] T054 [US3] Complete persistent subset/interval reads in `src/market_leadership/infrastructure/observation_store.py` with direct hashed series lookup and intersecting-month reads; the canonical identity "includes subject IDs, provider/source, currency, frequency, kind, basis, normalization and continuity fingerprint" and "excludes symbol batches, selected sector/industry, catalog revision, requested dates, UI state and secrets."; never glob/reparse the held universe on startup or navigation.
- [ ] T055 [US3] Complete touched-month idempotent merge/publication in `src/market_leadership/infrastructure/observation_store.py`; enforce "A monthly partition belongs to exactly one series identity and adjustment epoch.", preserve unchanged rows' original retrieval/deadlines, attribute changed values anew, reference untouched immutable partitions, fsync the complete generation before CURRENT, and expose the pinned per-series generation vector.
- [ ] T056 [US3] Complete cross-process attempt coordination in `src/market_leadership/infrastructure/observation_store.py` on T041's lock lifecycle: "An OS lock protects each series across processes, acquired in stable key order.", "After waiting, recheck coverage/attempt outcome before fetching.", and "On contention return a loading state after two seconds total across that action's series-lock waits, including shared read locks; on failure share the failed outcome."; persist typed attempts and explicit confirmed-gap identity/interval/code/reference/`checked_at`/policy metadata, share terminal errors across reruns/restarts, and never convert missing rows/empty responses/HTTP failures into confirmation or successful coverage.
- [ ] T057 [US3] Implement official-session missing/stale interval planning and compatible-target grouping in `src/market_leadership/application/request_market_data.py`; dates select coverage, not identity, respect listing/issuer eligibility, and request only actionable gaps/stale sessions plus <=one eligible overlap; reclassify confirmed gaps against the current latest-five-session tail, require explicit refresh for historical/left-tail/unconfirmed gaps and explicit retry after errors, and never fetch incomplete sessions, unrelated instruments or ordinary terminal reruns.
- [ ] T058 [US3] Integrate under-lock coverage/attempt rechecks and mode/permission fences in `src/market_leadership/application/request_market_data.py`; coalesce identical misses into one upstream acquisition, share success/failure with waiters, preserve permitted partial successes and explicit gaps, and expose typed loading rather than duplicate work after contention.
- [ ] T059 [US3] Implement freshness/provenance reconciliation in `src/market_leadership/application/request_market_data.py` and `src/market_leadership/infrastructure/observation_store.py`: latest five completed official sessions use `min(3600, current freshness_seconds)` from `last_validated_at` for rows or `checked_at` for confirmed gaps; older coverage is reusable, "a matching source revalidation advances `last_validated_at`, not their value provenance.", and "A repeated confirmation advances `checked_at`, never observation freshness or retention."; share one due gap recheck and persist its terminal error to suppress further automatic attempts until explicit retry, with mode/rights always taking precedence over freshness.
- [ ] T060 [US3] Implement adjusted-overlap/correction epoch invalidation in `src/market_leadership/application/request_market_data.py` and `src/market_leadership/infrastructure/observation_store.py`; enforce "An overlap adjustment mismatch invalidates the old epoch before any mixed-basis read.", reacquire the selected eligible stale window, mark other held windows basis-invalidated, withhold old-scale results after failure, and document explicit refresh for corrections outside observable overlap rather than inventing a provider revision feed.
- [ ] T061 [US3] Update generation-aware retained/derived caching in `src/market_leadership/ui/cache.py` to reuse the same valid series across different batches/views/restarts, re-evaluate mode/rights before hits, invalidate affected values after commit/epoch change, and avoid using Streamlit TTL as either durable freshness or retention authorization.
- [ ] T062 [US3] Expose source, original retrieval, last validation, actual covered period/gaps, identity, generation vector, and freshness/error/loading states from `src/market_leadership/application/request_market_data.py` through `src/market_leadership/ui/workflows/industry_deep_dive.py` and `src/market_leadership/ui/workflows/discovery_page.py`; incomplete volume or failed targets must not become complete fresh evidence.
- [ ] T063 [US3] Implement retention withholding/pruning in `src/market_leadership/infrastructure/observation_store.py`, `status`/`prune` in `src/market_leadership/observation_admin.py`, and its script in `pyproject.toml`; the original deadline is "the earlier of retrieval time plus the reviewed maximum and the policy's expiry boundary (end of its inclusive UTC expiry date)", renewal/migration "cannot extend this original deadline or reset retrieval timestamps", and "Expired bytes are never served."; apply T025's irreversible known tighter caps to pre-restriction rows, retain no expired-generation escape hatch, exclusively lock through CURRENT replacement and cleanup, preserve the stable lock inode and pinned readers, and use explicit roots/validated replica/guards plus reasoned versioned JSON, read-only status/dry-run and no offline UI prune or universe scan during ordinary guard checks.
- [ ] T064 [US3] Wire explicit selected-window refresh/retry intent in `src/market_leadership/ui/cache.py` and `src/market_leadership/application/request_market_data.py`; enforce "UI explicit retry starts a new attempt; ordinary reruns do not repeatedly retry the failed work.", retain bounded visible provider retry accounting/rate-limit behavior, and permit expired rows to return only through genuinely authorized new acquisition with new provenance.
- [ ] T065 [US3] Run T050-T053 and cold-start regressions; record exact A/B/A/restart zero-call reuse, 252-plus-five sessions, duplicates, matched-tail timestamps, confirmed-gap boundary/restart/failure call counts, real reader/pruner contention and stable-inode evidence, shared failures and crash preservation in `specs/013-market-structure-service/quickstart.md`.
- [ ] T066 [US3] Build the deterministic large retained dataset in `tests/fixtures/market_structure/performance.py` using the real store: at least 10,000 instruments times 252 actual observations, overlapping industries/multiple listings, controlled permissions/clocks, and known-value assertions; expose partition-read/enumeration/call counters without precomputing the selected view.

**Checkpoint**: Durable reads and incremental writes satisfy actual identity, interval,
freshness, retention, and concurrency semantics. The exact large-scale timings remain
release gates, not inferred from a smaller catalog test.

---

## Phase 6: User Story 4 - Apply a structure change without misattributing observations (Priority: P2)

**Goal**: Reorganize navigation/cohorts under a reviewed revision without duplicating
eligible observations, transferring approvals, or linking a reused ticker to a predecessor.

**Independent Test**: Publish controlled membership-only and identity-changing revisions.
Verify correct deduplicated hierarchy/new cohort, zero refetch for unchanged eligible
series, separate histories for distinct listings/issuers, and one pinned context per action.

### Tests for User Story 4

- [ ] T067 [P] [US4] Add failing revision/continuity tests in `tests/integration/test_observation_revisions.py` for membership move/add/remove, nested/overlapping deduplication, explicit candidate bindings, nullable/unverified issuer IDs, multiple listings, alias dates, reused tickers, predecessor exclusion, and unchanged observation keys/hashes/calls when continuity is proven.
- [ ] T068 [P] [US4] Add failing coherent-view/selection tests in `tests/app/test_market_structure_revisions.py` for derived-cohort invalidation, retained compatible navigation, withdrawn selections, a revision arriving mid-action, source-only restrictions, renamed policy IDs and old-CURRENT rollback/restart; a newly learned guard invalidating a pinned action must withhold final output/request coherent reload rather than mix context or display an old in-memory result.

### Implementation for User Story 4

- [ ] T069 [US4] Enforce candidate-revision/identity binding checks in `packages/market-data/src/market_data/structure.py`; require explicit independently reviewed candidate associations, preserve catalog revision versus transport snapshot distinction and original records, and enforce "the app must not rewrite a binding's revision to make it appear reviewed."
- [ ] T070 [US4] Refine target continuity resolution in `src/market_leadership/application/request_market_data.py` and `src/market_leadership/application/load_stock_history.py` so membership-only changes reuse proven stock/ETF/index continuity but issuer/listing changes do not; enforce "Provider alias changes are validated against dated mappings; identical text cannot merge distinct listings or predecessor issuers."
- [ ] T071 [US4] Validate dated symbol/calendar/currency/provider resolution at dispatch in `src/market_leadership/bootstrap.py` and `src/market_leadership/application/request_market_data.py`; keep distinct listings separate, require explicit identity on ambiguity, and preserve reviewed ETF benchmark/representation choices rather than inferring replacements from an index or parent node.
- [ ] T072 [US4] Update revision-bound navigation/cohort caching in `src/market_leadership/ui/cache.py`, `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/ui/workflows/industry_deep_dive.py`, `src/market_leadership/ui/workflows/stock_lookup.py`, and `src/market_leadership/ui/workflows/yahoo_classification_preview.py`; deduplicate ancestor instruments, preserve valid independent selections, explicitly explain withdrawn selections, and invalidate derived hierarchy/cohorts and context-dependent preview results without duplicating/rekeying unchanged observation series.
- [ ] T073 [US4] Complete durable known-restriction fences for pinned actions in `src/market_leadership/application/load_market_structure.py` and `src/market_leadership/application/request_market_data.py`; use T025/T038 at cached return/acquisition/retention/commit/final-output boundaries, including after rollback/restart, withhold invalidated actions for coherent reload, and never splice new rights into old calculations or enumerate observation series to learn a restriction.
- [ ] T074 [US4] Update service-registry association/source resolution in `src/market_leadership/application/load_company_evidence.py` and `src/market_leadership/bootstrap.py` to preserve existing financial/research identity, history-eligibility and independently permitted sharing safeguards across revisions; fetched profiles/financials/claims remain app-owned and never manufacture a binding or review approval.
- [ ] T075 [US4] Surface the pinned structure snapshot/catalog revision, applicable market date, and retained observation context consistently in `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/ui/workflows/industry_deep_dive.py`, `src/market_leadership/ui/workflows/stock_lookup.py`, and `src/market_leadership/ui/workflows/yahoo_classification_preview.py`; preserve all four tabs and dedicated lookup/navigation/score behavior, clear only invalid dependent state, and distinguish classification changes from observation freshness.
- [ ] T076 [US4] Run T067-T068 plus affected existing 010/011/012 membership, issuer, representation, navigation, and scoring regressions; record values/identities/keys/call counts in `specs/013-market-structure-service/quickstart.md` and report unrelated unfinished feature work separately rather than marking it complete.

**Checkpoint**: A reviewed reclassification reorganizes reads rather than ownership.
No automatic association rewriting, ticker-based history transfer, or silent approval.

---

## Phase 7: User Story 5 - Browse retained data honestly during a structure-service outage (Priority: P2)

**Goal**: Complete honest offline/rejected-update/blocked behavior, enforce current
permissions on every entry point, and recover only through complete validation.

**Independent Test**: Warm controlled caches, stop the service, and inspect every market
view and direct acquisition path. All eligible reads identify offline status, revision,
last successful check, and observation freshness. All acquisition/mutation is blocked;
expiry/revocation still applies. Restore service and verify coherent validated recovery.

### Tests for User Story 5

- [ ] T077 [P] [US5] Add failing full outage/recovery tests in `tests/integration/test_market_structure_outage.py` for no replica, transport error, timeout, malformed/oversized/truncated data, invalid references, unsupported formats, corrupt objects, 401/403, failed replacement, explicit retry, successful 304/recovery, and separate attempted/successful check clocks.
- [ ] T078 [P] [US5] Add failing offline AppTests in `tests/app/test_market_structure_offline.py` covering warm in-memory/retained hits across all four tabs, retained/unassigned lookup and listing selection, explicit financial/research/history and preview actions, member/history loaders, refresh/retry controls, and direct daily snapshot calls; assert consistent pinned context and visible state, zero external acquisitions/content writes/pruning, no alternate local catalog authority, and no silent empty-success fallback.
- [ ] T079 [P] [US5] Add failing current-permission fence tests in `tests/contract/test_observation_permissions.py` for historical analysis dates, expiry mid-action, guard-tightened retention, omitted grants and source-only revocation, denied/missing/expired policies, rollback/restart/renamed IDs, high-water versus backdated review, ambiguous legacy same-day reapproval, fresh review allowing new data but never old-row revival, reference-only/news metadata, cached financial/research and final-output fences, plus no credential leakage.

### Implementation for User Story 5

- [ ] T080 [US5] Complete fault-state/revalidation transitions in `src/market_leadership/application/load_market_structure.py` and `src/market_leadership/infrastructure/structure_replica.py`; preserve validated bytes/last success on failure and newer restrictive guards with older CURRENT, block missing/corrupt required guards or auth denial, distinguish offline/rejected-update/blocked, suppress rerun retries inside 300 seconds, and never mutate guards on ordinary offline browsing or confuse validated restrictive safety metadata with successful content activation.
- [ ] T081 [US5] Close every price-data cache/provider/commit bypass in `src/market_leadership/bootstrap.py`, `src/market_leadership/ui/cache.py`, `src/market_leadership/application/load_stock_history.py`, and `src/market_leadership/application/build_snapshot.py`; enforce read-only/blocked capabilities before in-memory hits and side effects, without deleting still-valid cached bytes or sharing credentials/selections.
- [ ] T082 [US5] Enforce current service-registry financial/disclosure/research permissions plus T025/T038's durable source/role/scope restrictions in `src/market_leadership/application/load_company_evidence.py`, `src/market_leadership/ui/components/company_evidence.py`, and both Discovery/dedicated lookup callers before archived/in-memory returns, explicit acquisition/retention and final output; real current time governs rights, legacy date-only fields/fingerprints remain unchanged, same-day ambiguous reapproval explains the required later review, and registration/reference-only approval or rollback cannot authorize restricted work.
- [ ] T083 [US5] Finish consistent status/setup/retry rendering in `src/market_leadership/app.py`, `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/ui/workflows/industry_deep_dive.py`, `src/market_leadership/ui/workflows/stock_lookup.py`, and `src/market_leadership/ui/workflows/yahoo_classification_preview.py`; display mode, revision, applicable date, last successful check, last attempted check/error, and observation freshness separately, disable every forbidden history/evidence/preview action, and keep backend enforcement independent of disabled widgets.
- [ ] T084 [US5] Implement explicit recovery in `src/market_leadership/application/load_market_structure.py` and `src/market_leadership/ui/cache.py`: validate all current bytes and permissions before returning online, atomically select the context, invalidate only affected derived/cache state, retain compatible observations, and never renew rights or mix revisions during recovery.
- [ ] T085 [US5] Resolve adversarial HTTP/disk/permission fault cases from T077-T079 in `src/market_leadership/infrastructure/market_structure_client.py`, `src/market_leadership/infrastructure/structure_replica.py`, and `src/market_leadership/application/request_market_data.py`; use typed actionable sanitized outcomes, preserve prior valid data, and do not add broad catches, silent defaults, or success-shaped partial failures.
- [ ] T086 [US5] Run T077-T079 together with delivery/bootstrap/reuse/revision regressions and record the full state/clock/call/write matrix in `specs/013-market-structure-service/quickstart.md`; demonstrate warm permitted browsing with the service process stopped and expired data withheld before cached display.

**Checkpoint**: Offline UI is genuinely read-only, cached data is not authority to
display expired content, authentication denial blocks access, and recovery is coherent.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Explicit migration and operational guidance, exact performance proof,
distribution/CI isolation, and final regression gates. No production cutover.

- [ ] T087 [P] Add legacy-import/status/prune CLI tests in `tests/integration/test_observation_migration.py` for accepted/ambiguous/expired/failed/unverifiable entries, exact reviewed listing/issuer period proof, original timestamps/deadlines, unknown versions, no ticker inference, dry-run/no-fetch, path containment, and leaving legacy source files unchanged.
- [ ] T088 Implement explicit `import-legacy` and complete versioned maintenance reports in `src/market_leadership/observation_admin.py` and `src/market_leadership/infrastructure/observation_store.py`; require explicit roots/validated replica/current guards/permissions/exclusive mutation locks and review reference, quarantine unsupported/ambiguous entries in place with reasons, preserve guard state and original provenance/irreversible retention caps, and never silently delete/reinterpret/renew old rows, reset known restrictions or acquire provider responses.
- [ ] T089 [P] Add temporary-root service migration/backup/rollback scenarios in `tests/integration/test_market_structure_migration.py` for reviewed inventory/dry-run, expected-current operations, original catalog/assessment/binding bytes, guard preservation across backup/import/restart, obsolete-rights rollback rejection and historical-catalog republishing with compatible restrictive registries, missing/corrupt minimum guards, sanitized uncertainty, and no implicit activation or production cutover; do not claim unseen-history protection on a genuinely new root.
- [ ] T090 Add and execute exact acceptance benchmarks in `tests/integration/test_market_structure_performance.py` using T066: at least 2,520,000 actual observations across 10,000 instruments; cold usable active view <=5 seconds excluding separately measured external wait; 20 correct nonempty warm views of up to 100 stocks with at least 19 <=1 second and zero external acquisition; five-session-by-100-listing update of 500 observations readable <=2 seconds after validation, unchanged unrelated hashes, and no whole-universe reads/CSV reparses/empty-result or catalog-only proxy.
- [ ] T091 Meet the T090 gates by profiling measured bottlenecks in `src/market_leadership/infrastructure/observation_store.py`, `src/market_leadership/application/request_market_data.py`, and `src/market_leadership/ui/cache.py` only as needed; preserve fsync/rights/identity semantics, rerun exact workloads, and record OS/architecture/Python/dependencies/storage/CPU-memory/cache warmth/data shape, elapsed distributions, partition/enumeration/row/call counts in `specs/013-market-structure-service/quickstart.md` without weakening thresholds or changing storage architecture silently.
- [ ] T092 Update `README.md` and `specs/013-market-structure-service/quickstart.md` with verified service/app deployment, four environment variables, HTTPS/bearer, reader/publisher permissions, explicit paths/expected-current, inventory/backup/import/quarantine and guard-preserving permission-safe rollback/reapproval, no unseen-history promise on a new root, confirmed-gap explicit retry rules, stable-inode locking/pruning and scheduled cleanup, local-filesystem limits and original-root preservation; distinguish implemented evidence from remaining gates.
- [ ] T093 Update `.github/workflows/data-contracts.yml` for workspace lock/install, shared/app/service wheel builds, packaged schemas, strict Pyright and Ruff across all source roots, full non-live regressions, independent-install checks, and the exact observation benchmark rather than only catalog timings; no live provider/service credentials in CI.
- [ ] T094 Complete and run isolated installed-wheel/CLI validation in `tests/contract/test_service_distribution.py` and `tests/contract/test_package_boundaries.py`; use independent environments outside workspace import paths, verify service/shared/app dependency exclusions, all new/existing command help and optional delegates, resource loading, and canonical import identity rather than relying on an all-packages development environment.
- [ ] T095 Run `uv run ruff check src packages services tests`, `uv run pyright`, `uv run pytest -m "not live" -q`, and `uv build --all-packages` after focused suites pass; record exact commands/results and independent wheel checks in `specs/013-market-structure-service/quickstart.md`, fixing only feature-caused or tightly coupled regressions.
- [ ] T096 Execute the documented controlled publish/consume/cache/migrate/prune-dry-run/rollback guide with temporary reviewed fixtures, verify all FR/SC evidence and no production changes, and finalize feature status/links in `specs/README.md` and `specs/013-market-structure-service/quickstart.md`; do not mark 013 complete until its gates pass or claim that unfinished 010/012 work is delivered.

**Checkpoint**: Release evidence proves compatibility, exact performance, safe
maintenance, and unchanged intended app behavior. Real deployment/cutover remains an
explicit operator decision.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup T001-T008
  -> Foundation T009-T012
    -> US1 T013-T030
      -> US2 T031-T049
        -> US3 T050-T066
          +-> US4 T067-T076 --+
          +-> US5 T077-T086 --+-> Polish T087-T096
```

The graph shows functional completion prerequisites, not a requirement to defer all
test authoring. US5 does not depend on US4 semantics, but their implementation touches
common loader/bootstrap/cache/UI files: use the listed sequential default or explicitly
coordinate file ownership. Do not run both editing streams against the same files.
US4/US5 tests can be authored in parallel once the US3 contracts are established.

### Task-Level Gates and Safe Batches

| Work | Prerequisite / execution rule |
|---|---|
| T001-T002 | Baseline before move tests; move tests before implementation |
| T003, T004 | Both wait for T002; disjoint moves/manifests can run together |
| T005-T008 | Both moves before workspace integration; configuration/delegates before validation |
| T009, T010, T011 | Setup complete; independent fixture/double/evidence-test files |
| T012 | T011 red regression first; foundation complete before story implementation |
| T013, T014, T015, T016 | Foundation complete; independent payload/guard/HTTP/publication-delivery tests |
| T017-T021, T022, T023-T024, T025 | All four test tasks first; serialize shared DTO edits through guard records, then schemas, bundle validation, shared guard evaluator |
| T026, T027, T028-T030 | T024/T025 before store; guarded publication before routes/CLI and service acceptance |
| T031, T032, T033 | US1 complete; independent client/bootstrap-target-store/AppTest files |
| T034-T037, T038, T039-T040, T041 | US2 tests first; typed boundaries/config before client/replica; T025/T037 before replica guard integration, then loader/store and complete initial lock lifecycle |
| T042-T049 | T038/T041 plus store/context before gated orchestration, bootstrap/provider, all UI/history/CLI callers and acceptance |
| T050, T051, T052, T053 | US2 complete; independent cache/reuse/concurrency/retention test files |
| T054-T056 | T041 lock lifecycle before subset reads/merges; then durable attempt and confirmed-gap coordination |
| T057-T060 | Store primitives before interval planning/coalescing, freshness and correction behavior |
| T061-T065 | Correct generations/epochs before UI caching/outcomes, maintenance, refresh and acceptance |
| T066 | T055's stable store format plus fixture infrastructure; can run alongside later disjoint story-test authoring |
| T067, T068 | US3 functional contracts; independent revision integration/AppTest files |
| T069-T076 | Revision tests first; validator/identity resolution before coherent derived UI/fences/evidence/regressions |
| T077, T078, T079 | US3 functional contracts; independent outage/AppTest/permission test files |
| T080-T086 | Fault tests first; loader transitions and all entry-point gates before rendering/recovery and acceptance |
| T087, T089 | All stories complete; independent migration-test files can run together |
| T088 | T087 tests first; complete importer before final operator guide |
| T090-T091 | T066 plus completed store/UI semantics; run timings alone on a documented host, then fix and repeat |
| T092-T096 | Migration/performance evidence before final docs/CI/isolated installs/full suite/controlled guide |

### User Story Dependencies

- **US1 (P1)**: Foundation only. Independently demonstrates the service contract MVP.
- **US2 (P1)**: US1 delivery; independently tests one empty-cache consumer view.
- **US3 (P1)**: US2 composition/store; independently tests durable reuse and concurrency.
- **US4 (P2)**: US1 reviewed revisions plus US3 identity-safe reuse; independently tests
  reclassification and continuity without changing observation ownership.
- **US5 (P2)**: US2 basic context/modes plus US3 retained-data semantics; independently
  tests outage/permissions/recovery. US4 is a final regression, not a functional blocker.
- **Polish**: All five stories, including controlled migration and exact performance gates.

### Within Each User Story

1. Write tests and observe failures for missing behavior.
2. Implement types/validators before dependent services, then endpoints/composition.
3. Keep primitive adapters injectable but route every production caller through gates.
4. Run the smallest combined selectors; record identities, actual data and source calls.
5. Demonstrate the independent checkpoint before declaring the story complete.

---

## Parallel Examples

### User Story 1

After foundation, author T013 payload tests, T014 guard tests, T015 HTTP tests, and
T016 publication/delivery tests concurrently in their distinct files. Join before T017.
Do not parallelize T017-T022: all edit the shared DTO module.

### User Story 2

After US1, author T031 client tests, T032 bootstrap/target/store tests, and T033 context
AppTests concurrently. All consume the test fixtures read-only. Join before T034;
composition/UI/cache implementation is serialized because callers share modules.

### User Story 3

After US2, author T050 cache contracts, T051 reuse tests, T052 process tests, and T053
retention tests concurrently. Use distinct temporary roots and process ledgers; no
shared live server, cache, source credentials, or user selection. Join before T054.

### User Story 4

After US3's functional contract, author T067 identity/revision tests and T068 revision
AppTests together. T066's separate performance fixture can be prepared concurrently
once the generation format is stable. Serialize T069-T075 integration edits.

### User Story 5

After US3's functional contract, author T077 outage tests, T078 offline AppTests, and
T079 permission tests concurrently. These can also run alongside US4 test authoring,
not overlapping US4 implementation edits. Join before T080.

### Shared and Final Work

T003/T004 and T009/T010/T011 are explicit earlier parallel batches. T087/T089 migration
tests can run together after all stories. Do not run acceptance timing under concurrent
benchmarks, builds, or other known machine-load changes.

---

## Requirement Coverage

IDs below belong to feature 013; older feature requirements remain regression authority.
Each range identifies concrete implementation and tests, not an exemption from the
normative documents.

| Requirement | Primary tasks / evidence |
|---|---|
| FR-001 | T002-T008, T015-T016, T026-T030, T094: independent service/wheels |
| FR-002 | T013, T017-T024, T033, T042-T047: coherent reviewed hierarchy/identities |
| FR-003 | T013-T030, T031, T036-T039: exact immutable snapshots and conditional checks |
| FR-004 | T002-T008, T031-T039, T043-T048, T094: HTTP/shared contracts, no server imports |
| FR-005 | T011-T024, T031-T039, T067-T074, T079: compatible semantics and fail-closed validation |
| FR-006 | T031, T033-T039, T068, T073, T075, T077-T086: validated replica/pinned view |
| FR-007 | T011-T021, T024, T030, T033, T045, T079, T082: source metadata/rights/no secrets or articles |
| FR-008 | T032, T034, T040-T048, T050-T064: app-owned selected-provider observations |
| FR-009 | T032-T033, T040-T049, T090: on-demand cold view without evidence/universe prefill |
| FR-010 | T032, T034, T042, T047, T050, T054, T067-T074: exact identity/continuity |
| FR-011 | T050-T051, T054-T061, T065, T090: cross-view and restart reuse |
| FR-012 | T051, T054-T060, T065: gaps, stale tail and bounded reconciliation overlap |
| FR-013 | T050-T051, T055, T059-T060: idempotence/corrections and untouched history |
| FR-014 | T034, T040, T050-T053, T059, T062-T063, T075: provenance/freshness/retention |
| FR-015 | T036, T051-T052, T056-T060, T064, T078, T081: bounded selected refresh/retries |
| FR-016 | T052, T055-T058, T065: process coordination, atomic commits and shared failures |
| FR-017 | T050, T054-T055, T066, T072, T090-T091: selected lookup and exact observation workload |
| FR-018 | T033, T039, T077-T086: marked read-only, current rights and no mutation |
| FR-019 | T033, T035, T039, T045, T077-T086: blocked empty replica, no local/fixture fallback |
| FR-020 | T001, T011-T012, T044-T048, T067-T076, T082, T095: baseline and existing app/identity/rights safeguards |
| FR-021 | T063, T087-T089, T092, T094-T096: explicit versioned migration and rollback |
| FR-022 | T001, T009-T016, T031-T033, T050-T053, T067-T068, T077-T079, T087-T096: baseline and controlled end-to-end gates |
| SC-001 | T016, T030, T051, T065, T077-T086: independent serving and warm offline reads |
| SC-002 | T032-T033, T049, T066, T090-T091: actual cold active view <=5 seconds |
| SC-003 | T050-T051, T054-T061, T065: A/B/A plus restart, zero extra calls |
| SC-004 | T051, T055, T057-T060, T065: 252 sessions plus five, <=one overlap, zero duplicates |
| SC-005 | T066, T090-T091: >=2,520,000 observations, >=19/20 warm views <=1 second |
| SC-006 | T055, T066, T090-T091: 500 validated observations readable <=2 seconds |
| SC-007 | T016, T031-T033, T051-T052, T067-T086: identity/revision/crash/outage integrity |
| SC-008 | T052, T056-T058, T065: one concurrent acquisition and shared coherent result/error |
| SC-009 | T033, T053, T062-T064, T075, T077-T086: explicit offline status, no calls/renewal |

### Approved Refinement Coverage

These are refinements of the existing requirements, not additional user stories or
changes to public HTTP/catalog formats. Each test gate precedes its implementation.

| Finding | Red-test tasks | Implementation and acceptance |
|---|---|---|
| A1: exact policy grammar/fingerprint | T013 | T020, T023-T024, T030; normative schema equality, nullability and strict string/date boundaries |
| A2: confirmed unavailable retry/reuse | T032, T051-T052 | T034, T056-T059, T064-T065; current-tail due recheck, explicit historical/error retry, durable failure suppression |
| U1: pinned readers versus pruning | T032, T052-T053 | T040, T041, T054-T056, T063, T065; shared/exclusive lifetime, total two-second budget, stable inode and physical cleanup |
| A3: restrictions survive rollback/restart | T014, T015-T016, T031, T053, T068, T079, T089 | T022-T025, T026, T027, T038, T042, T063, T073, T080-T082, T084, T088; early shared/publisher/replica guard with final fences and safe maintenance |

## Implementation Strategy

### MVP First (User Story 1)

1. Complete setup and foundation, with failing package/contract tests first.
2. Deliver T013-T030 and stop to demonstrate independent publication/serving/consumption.
3. This is the service-contract MVP, not a claim that the stock app already has the
   persistent cache or that all US1 integrated-app acceptance scenarios are closed.
   The integrated app demonstration follows in US2.

### Incremental Delivery

1. US1: independent reviewed structure delivery.
2. US2: real stock-app consumer, automatic initial observations and basic mode gates.
3. US3: durable cross-view/restart reuse, incremental correction/concurrency/retention.
4. US4: reviewed revisions reorganize navigation without changing observation ownership.
5. US5: exhaustive offline/permission/recovery behavior across all callers.
6. Final gates: explicit migration/maintenance, exact measured workload, isolated
   distributions, full regression suite, and controlled operator guide.

At each step retain prior checkpoints. No implicit production migration, altered
approvals, background universe prefill, new collector, SQL observation store, Redis,
broker, distributed locking, or sibling-feature completion is authorized.

### Parallel Team Strategy

Use the named disjoint-file batches rather than dividing shared modules arbitrarily.
Merge and validate types before their callers. US4/US5 test authoring can overlap, but
coordinate shared implementation files explicitly; the default single-agent order is
the numeric sequence. Performance timings run without competing implementation checks.

## Completion Gates

All task checkboxes remain implementation work until verified. The requirement-quality
checklist is not a substitute for these runtime gates and must not be rewritten as
implementation progress.

- Every FR-001 through FR-022 and SC-001 through SC-009 has passing evidence above.
- App and service install/run independently and enforce the same shared validators.
- All production entry points use pinned identity/mode/permission boundaries.
- Exact benchmark data, output correctness, thresholds and measurement conditions pass.
- Versioned migration/prune/rollback preserve valid data and do not expand rights.
- Existing non-live behavior, Ruff, strict Pyright, builds and isolated CLI checks pass.
- No production catalog, approval, binding, observation root, or deployment is changed
  merely by completing this backlog.
