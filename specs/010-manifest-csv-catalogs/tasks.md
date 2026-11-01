# Tasks: Manifest-Managed CSV Catalogs

**Input**: Design documents in `specs/010-manifest-csv-catalogs/`.
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts](contracts/), [quickstart.md](quickstart.md).
**Branch**: `main`, unchanged; feature key `010-manifest-csv-catalogs`.
**Tests**: Required by the constitution's test-first quality gate and the feature's controlled
acceptance scenarios. Add/update tests before their implementation and demonstrate the intended
failure; do not accept a missing dependency or unrelated failure as the red result.
**Organization**: Shared setup/foundation, four independently verifiable story increments, final gates.
No implementation, user-data export/activation, branch switch, or commit is performed by generation.

## Format and Path Conventions

- Every task uses `- [ ] Tnnn [P?] [USn?] Description with exact repository-relative paths`.
- `[P]` means a task can share a ready execution wave with another task touching different files;
  prerequisites in the dependency table must already be complete.
- Story labels appear only in story phases. Unmarked tasks sharing a module are serialized.
- New source/test paths below are intentional planned additions, not claims of existing files.
- Preserve user-owned inputs, unrelated dirty work, existing completed task histories and market
  response caches. No production approved seed, hardcoded instrument roster or real-resource test.
- Every domain-field group implements the full referenced model/header, not only the quoted examples.
  Verbatim constraints in task descriptions remove discretion about nullability, enums and validation.
- Diagnostic/report errors stay observable and bounded; never include source snippets, credentials
  or full private payloads. No silent defaults, source-order approval or successful-empty error fallback.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Provide deterministic offline evidence and installable contract resources without
changing the existing dependency set or prematurely cutting over user data.

- [X] T001 Create controlled release/invalid/research fixture factories in `tests/conftest.py` and `tests/fixtures/catalogs/`, including `tests/fixtures/catalogs/reviewed-us/manifest.json`, `TEST_CLASSIFICATION`/`TEST_VERSION` effective on 2026-10-30, exact contract headers, resolved/unresolved members, empty nodes, explicit approvals and non-primary/listing-only basket inventory; reuse bounded local-project fixtures, inject paths/clocks/providers and prohibit real-project reads or network calls.
- [X] T002 [P] Add failing production-boundary regression guards in `tests/contract/test_catalog_boundaries.py` for embedded instrument/default benchmark lists, reachable runtime fixture modes and SQL outside explicit migration; scope monkeypatches to each scenario rather than disabling unrelated tests, and assert exact requested symbols from controlled data absent from legacy rosters.
- [X] T003 [P] Package an exact copy of `specs/010-manifest-csv-catalogs/contracts/catalog-manifest.schema.json` as `src/market_leadership/infrastructure/catalog-manifest.schema.json`, configure its distribution inclusion in `pyproject.toml` using the existing backend, and make `tests/contract/test_catalog_files.py` check semantic equality/installable resource access; retain existing constrained dependencies and Python `>=3.12,<3.13`.

**Checkpoint**: Test-only factories and schema packaging exist; no fixture is a runtime default.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extract SQL-independent records and shared validation before any story implementation.
These tasks do not introduce `FileRegionDatabase`, generic CRUD or a query database.

- [X] T004 [P] Add failing shape contracts in `tests/contract/test_catalog_files.py` for strict entry/release schemas, duplicate/unknown keys, UTC/date formats, exactly 64 lowercase hex hash characters, nullable versus blank scopes, one audit artifact, nonnegative counts, required artifacts versus optional research, unsupported versions and contained relative paths; use existing `jsonschema` Draft 2020-12 plus format checks.
- [X] T005 [P] Add failing pure-domain cases in `tests/unit/test_catalog.py` covering every constrained entity in `specs/010-manifest-csv-catalogs/data-model.md`, exact scope/source ownership, inclusive overlap boundaries, inherited node review, stock/listing consistency, verified-primary ETF rules, unresolved members, benchmark uniqueness and exact basket weights; reuse existing validation tests to prove intended behavior is unchanged.
- [X] T006 Extract shared scope, region/classification, evidence-source, artifact and entry/release records into `src/market_leadership/domain/catalog.py` with SQL-independent imports: preserve `"Nonempty immutable release identity; agrees with selected manifest"`, `"UTC publication time; not an observation date or approval"`, `"Null for bootstrap, otherwise prior release ID and manifest checksum"` and `"Derived digest of catalog artifacts, region/classification/coverage, and relevant approval metadata"`; implement region `"active/inactive"` and `"complete/partial/unverified"`, nullable `last_reviewed_at`, classification `"inclusive effective_from, nullable effective_to"`, source `"local_file/live"` and `"nullable coverage, authority, approval_reference, and reviewed_at"`, artifact `"nullable region_id, classification_id, classification_version"` and `"Exactly one stocks artifact per operational region; never one per industry."` as specified, without inventing source review or a missing classification version.
- [X] T007 Extract hierarchy records/validation into `src/market_leadership/domain/catalog.py`, implementing `NodeType` `"sector/industry/sub_industry"`, `"nullable ParentIndustryId"`, `"nullable EffectiveTo"`, `"nullable node SourceId/ApprovalReference"` and `ApprovalOrigin` `"own/classification_inherited"`; enforce `"SectorId = NodeId"`, identical-scope/type parents, covered inclusive periods, no cycles/name joins, empty own review fields for inherited approval, and stable node identity across nonconflicting historical intervals.
- [X] T008 Extract regional assertion/stock/listing records and eligibility validation into `src/market_leadership/domain/catalog.py`, implementing `RowId` `"Unique physical row; stable identity of membership/listing pairing"`, `MembershipId` `"Stable logical assertion ID, shared by its distinct listing rows"`, `"nullable CompanyId"`, stock `"identified/placeholder"`, `"Required IndustryId; nullable exact SubIndustryId belonging to that industry"`, `"nullable MembershipEffectiveTo"`, `"MembershipReviewState=reviewed"`, `"Nullable ListingId, Ticker, ProviderSymbol, Exchange, Currency"`, `"Nullable IsPrimary, ListingResolutionState (verified/unverified)"`, `"Nullable ListingEffectiveFrom/ListingEffectiveTo"` and `"Nullable ListingSourceId, ListingApprovalReference"`; require all-empty listing fields on no-listing rows, exact shared-ID attributes, independent membership/listing/source periods, no conflicting primary/symbol/industry/sub-industry identities, and deduplicated instruments for compatible same-industry assertions.
- [X] T009 Extract ETF listing/representation and benchmark validation into `src/market_leadership/domain/catalog.py`, retaining explicit `RegionId`, `"InstrumentType=etf"`, inclusive `EffectiveFrom`, `"nullable EffectiveTo"`, mandatory `SuitabilityReference`, `"nullable CandidateReviewId"`, exact role/node/source/listing periods and verified primary ETF selection; enforce `"Duplicate/conflicting mapping periods fail; sharing an ETF across nodes requires independent approvals."` and benchmark purposes `"sp500_comparison"`/`"market_sentiment"` with `"A purpose resolves to at most one approved effective listing."`, no symbol defaults or inferred ETF identity.
- [X] T010 Extract typed ledger/inventory/basket records and reusable research decoding into `src/market_leadership/domain/catalog.py`, reusing `src/market_leadership/domain/local_etf_evidence.py` and `src/market_leadership/domain/industry_representations.py`: implement `"immutable record_id"`, `"nullable UTC recorded_at"`, `"typed payload"` and `"nullable origin"` for all twelve declared record kinds in data-model section 7, separate transport/collection/review order, exact links and unknown declarations, and `"finite positive decimal weights totaling exactly 100%"`; preserve raw decimal strings, verified non-primary/unclassified inventory basket eligibility, ETF precedence, no overlapping ETF/basket approval, no renormalization/artificial OHLC, and unsupported operational payload errors.
- [X] T011 Run the foundational pure-domain/schema selectors in `tests/unit/test_catalog.py` and `tests/contract/test_catalog_files.py` after T006-T010, proving every declared field/header/enum/reference rule and domain imports are SQL-independent; keep full consumer guards in `tests/contract/test_catalog_boundaries.py` red until cutover rather than weakening them, and fix tightly coupled extraction regressions before proceeding.

**Checkpoint**: Typed record and validation contracts pass independently of a file reader or SQL.

## Phase 3: User Story 1 - Maintain One Authoritative File-Based Catalog Release (Priority: P1)

**Goal**: Validate and coherently activate a single registered file release.
**Independent Test**: Initialize an empty isolated store, validate/activate the reviewed fixture,
reject invalid references/counts/bytes, and exercise competing writers, tampering and explicit
recovery. A pre-commit fault preserves the prior entry; post-commit uncertainty is reconciled.
**MVP**: This isolated administration workflow only, not a partial production cutover.

### Tests for User Story 1

- [X] T012 [P] [US1] Add failing captured-file/content contracts in `tests/contract/test_catalog_files.py` and publication integration cases in `tests/integration/test_catalog_publication.py` for exact CSV/JSONL grammar and limits, all required regional roles, duplicate identities/declared coverage, symlink/traversal escapes, before/after-read edits, same-size restored-mtime tampering, copy-not-hardlink behavior, lock contention/expected parent mismatch, interrupted commit and verified recovery without automatic orphan selection.
- [X] T013 [P] [US1] Add failing lifecycle/report CLI contracts in `tests/contract/test_catalog_cli.py` for `catalog-init`, `validate-catalog`, `activate-catalog` and `recover-catalog`, explicit entry selection, expected release `none`/ID, bootstrap without seeds, read-only validation and common envelope `"market-catalog-cli-1"`; assert exit 0 only for complete outcomes, exit 2 for partial/failed/conflict/indeterminate, bounded stderr and truthful not_published/published/unknown state.

### Implementation for User Story 1

- [X] T014 [US1] Implement captured-byte manifest/CSV/JSONL loading in `src/market_leadership/infrastructure/catalog_files.py` using the packaged schema, exact headers from `specs/010-manifest-csv-catalogs/contracts/catalog-files.md`, UTF-8/BOM/CRLF handling, ISO inclusive dates, true/false/nullable booleans, `"64 MiB per CSV/JSONL artifact and 1 MiB per manifest/record"`, raw-byte hashes, duplicate-key/header/count/role/scope checks and explicit file/row/reference errors; canonical containment plus `(device, inode, size, mtime_ns, ctime_ns)` before/after capture must prevent concurrent edits or successful cached corruption.
- [X] T015 [US1] Build immutable `CatalogSnapshot` indexes/projections and recomputed revision dependencies in `src/market_leadership/infrastructure/catalog_files.py`, implementing `"immutable typed records/indexes, release identity, catalog revision, artifact fingerprints, exact scope/date membership projections, listing eligibility, and review/representation views"` and `"It contains no credentials or user selections."`; index all nodes and shared listing/ledger links, reject unregistered/conflicting evidence, distinguish empty/partial/unconfigured/invalid coverage, and exclude research/archive/transport history from catalog revision while retaining catalog-relevant approvals.
- [X] T016 [US1] Implement complete-generation publication in `src/market_leadership/infrastructure/catalog_files.py`: persistent nonblocking exclusive `fcntl.flock`, required expected active release, revalidation under lock, captured copies with prior ledger prefix plus publication record, computed release/parent/revision, fsync files/directories, complete-directory rename then atomic entry replacement; retain prior releases, never unlink the lock or mutate authoring/user files, and report known pre-commit failure versus verified/uncertain post-commit outcome per clarified FR-008.
- [X] T017 [US1] Implement explicit recovery in `src/market_leadership/infrastructure/catalog_files.py` using a known reviewed target manifest checksum and expected raw entry checksum under the same lock, validating all selected files/references and recording a recovery receipt; never choose newest/orphan staging, discard prior audit history, use stale/SQL fallback or claim an unverified rollback after commit uncertainty.
- [X] T018 [US1] Wire lifecycle/selection/report commands in `src/market_leadership/universe_admin.py` and `src/market_leadership/config.py` per `specs/010-manifest-csv-catalogs/contracts/catalog-cli.md`: `--manifest` overrides `MARKET_CATALOG_MANIFEST_PATH`, then `.data/catalog/CURRENT.json`; init creates only store structure, validation is read-only, activation assigns reviewed complete generations, recovery verifies explicit hashes, and typed errors yield truthful bounded versioned reports without default instruments or SQL initialization.
- [X] T019 [US1] Execute US1 domain/file/CLI/publication tests in `tests/unit/test_catalog.py`, `tests/contract/test_catalog_files.py`, `tests/contract/test_catalog_cli.py` and `tests/integration/test_catalog_publication.py`, including the quickstart bootstrap and corrupted-entry recovery against disposable paths; assert coherent old/new bytes, expected release/operation links and unchanged user inputs, not merely successful command exit.

**Checkpoint**: US1 is independently usable with controlled files and no database. Do not switch
the existing user's deployment while later production consumers/retirement/migration are unfinished.

## Phase 4: User Story 2 - Screen Stocks and ETF Representations from CSV References (Priority: P1)

**Goal**: Wire both root tabs, scoped requests and stable selections to one validated snapshot.
**Independent Test**: Filter two industries and an explicit sub-industry, retain empty/gap nodes,
activate one assignment/ETF change, and assert exact stock/provider sets and unrelated valid state.

### Tests for User Story 2

- [X] T020 [P] [US2] Add failing membership/worklist/request/cache integration scenarios in `tests/integration/test_catalog_workflows.py` for exact sector-to-industry filtering, explicit-only sub-industry membership, instrument deduplication, unresolved/non-primary no-request members, benchmark purpose changes, no parent substitution, and changed-versus-unchanged source/cohort fingerprints; assert exact scopes, dates, symbol sets and zero unnecessary requests.
- [X] T021 [P] [US2] Update/add failing AppTest scenarios in `tests/app/test_discovery.py`, `tests/app/test_sector_stock_explorer.py` and `tests/app/test_progressive_tabs.py` using the controlled file fixtures and injected providers: exactly two tabs, one release per rerun, active zero-member/gap nodes, preserved date controls/five windows/84-pixel thumbnails/colors/two-decimal returns/six stock columns/50 MA/explicit Total Score load, plus valid-state preservation and invalid-source clearing.
- [X] T022 [P] [US2] Add the exact SC-004 benchmark in `tests/integration/test_catalog_performance.py` with generated test-only release data under `tests/fixtures/catalogs/`: 10,000 stock rows, 500 industry/sub-industry nodes and 11 sectors, valid listing/review/ledger links, three truly cold reads/hash/parse/validate/index/navigation runs and ten warm filter/navigation runs; assert each cold <= 5 seconds and each warm <= 1 second, record environment/full output counts and guard remote calls/reparses so empty/preloaded proxy results cannot pass.

### Implementation for User Story 2

- [X] T023 [US2] Replace database/independent JSON membership resolution in `src/market_leadership/infrastructure/stock_membership.py` with explicit snapshot/scope/version/date projections, preserving instrument/listing identities, placeholders and source diagnostics; wire membership/cohort fingerprints into `src/market_leadership/application/score_industry.py` so peer cohorts use effective reviewed membership before display filters, compatible assertions deduplicate and only eligible primary member listings cause requests.
- [X] T024 [P] [US2] Refactor `src/market_leadership/application/discover_sectors.py` and `src/market_leadership/domain/regimes.py` to require file-derived sector representations and purpose-specific benchmark identity instead of `BENCHMARK`, `SECTOR_PROXIES` or a `"SPY"` argument default; preserve request scope, matching-period subtraction/session anchoring and regime calculations while reporting missing/unverified benchmark or representation evidence explicitly.
- [X] T025 [P] [US2] Refactor `src/market_leadership/domain/industry_momentum.py` and `src/market_leadership/application/industry_representations.py` to consume reviewed snapshot nodes and exact ETF/basket listings rather than static thematic/industry catalogs or SQL worklists; show every active reviewed node, retain ETF-first explicit basket resolution and distinguish missing/invalid/insufficient/unavailable evidence without parent/stock/index substitutes or fabricated basket charts.
- [X] T026 [US2] Wire one snapshot per root rerun in `src/market_leadership/app.py`, `src/market_leadership/bootstrap.py`, `src/market_leadership/ui/cache.py` and `src/market_leadership/ui/navigation.py`, passing it to both existing tabs with their preserved date contexts; validate active signatures before cached reuse, reuse unchanged content indexes/raw provider evidence, key derived results by exact scope/date/cohort/listing fingerprints and clear only invalid descendants rather than reset unrelated selections.
- [X] T027 [P] [US2] Integrate explicit snapshot/benchmark/representation/membership inputs into `src/market_leadership/ui/workflows/discovery_page.py`, removing local `RegionDatabase` construction and constant imports; retain existing progressive controls/layout/columns/score loading and source/gap states, including invalid active data without stale selected rows or fabricated momentum.
- [X] T028 [P] [US2] Integrate the same root snapshot into `src/market_leadership/ui/workflows/industry_deep_dive.py`, removing independent database/catalog selection and preserving exact reviewed memberships, version/date context, stock/history/fundamental eligibility and detail-return session behavior; reuse the shared cache/selection helpers rather than duplicate file loading.
- [X] T029 [US2] Run US2 integration/AppTest/performance selectors in `tests/integration/test_catalog_workflows.py`, `tests/integration/test_catalog_performance.py` and the T021 AppTest files with two controlled activations; prove changed request sets, unaffected selection/cache reuse, all three Quality/Growth/Cash Flow components and explicit missing states, and actual timing budgets without live retrieval or user data.

**Checkpoint**: Both tabs screen using registered files; earlier UI/calculation/provider invariants
still hold. US3 review mutation and US4 retirement/cutover remain separate completion gates.

## Phase 5: User Story 3 - Retain File-Based Review and Approval Governance (Priority: P2)

**Goal**: Preserve local observation, exact decisions, reviewed ETF/basket changes and durable provenance.
**Independent Test**: Collect a partially observable controlled source set, review exact evidence,
publish one valid mapping atomically and flag later mutations without overwriting prior approvals.

### Tests for User Story 3

- [ ] T030 [P] [US3] Add failing manifest-root/currentness regressions in `tests/unit/test_local_etf_sources.py` and `tests/unit/test_local_etf_evidence.py` for optional missing/unsupported/partial sources, safe registered literal extraction, unchanged evidence identity, changed label/ticker/context/removed/new conflict/unobservable relationships, separate event streams and latest rejection without reviving earlier acceptance; prohibit unregistered/private-source extraction and project execution/network.
- [ ] T031 [P] [US3] Add failing file-ledger/governed CLI integration and contract scenarios in `tests/integration/test_catalog_governance.py` and `tests/contract/test_catalog_governance.py` for observation-only publication, exact candidate/run/evidence/scope/version decisions, source/listing/suitability/full-period qualification, approval-run versus review-run links, basket eligibility/weights/history, same-parent conflicts and interrupted mapping-plus-provenance publication.

### Implementation for User Story 3

- [ ] T032 [US3] Replace `DEFAULT_ROOTS`/`DEFAULT_CATALOGS` configuration in `src/market_leadership/infrastructure/local_etf_sources.py` with snapshot `research_sources` descriptors: retain `"resource_id"`, explicit `"root"`, `"required=false"` and catalogs `"path"`, `"name"`, `"catalog_type"` from the contract, with industry/sector_context/index_context/commodity_context roles; preserve bounded approved parser grammar/path exclusions, canonical root containment and read-once source observations, without default home paths, arbitrary private dictionaries, execution or online transmission.
- [ ] T033 [US3] Implement governed ledger read/append projections in `src/market_leadership/infrastructure/catalog_files.py`, decoding existing local domain payloads and keeping `"Transport order is not a fabricated legacy observation chronology."`, immutable IDs/previous byte prefix, exact listing/review/evidence/run/provenance relationships and unknown claims; same-ID different-content or unsupported records fail, research-only append preserves catalog revision, and archived extensions never become operational approval fallback.
- [ ] T034 [US3] Refactor collection/candidate worklist/accept-reject flows in `src/market_leadership/application/discover_etf_candidates.py` to use explicit snapshot/expected-release and the coherent publisher, preserving existing domain identity/currentness/issue-resolution algorithms; unchanged recollection adds observations but no duplicate evidence/reviews, explicit selected run/evidence and latest decisions remain binding, and incomplete inspection cannot prove removal or create source/listing/ETF approval.
- [ ] T035 [US3] Implement reviewed node updates through snapshot validation and coherent publication in `src/market_leadership/application/industry_representations.py`, preserving exact source/reference/node/parent/version/period checks and append-only node review links; whole-release authoring remains the explicit source/classification/stock-update route, and no name-based node/source authorization or inferred classification version is introduced.
- [ ] T036 [US3] Implement explicit ETF and basket approvals in `src/market_leadership/application/industry_representations.py` with candidate-backed coordination in `src/market_leadership/application/discover_etf_candidates.py`: require unique verified regional primary ETF listing, exact target/version/source/approval/suitability/full period and current selected review/evidence where supplied, publish mapping/review/provenance together, and preserve `"Later rejection clears selection without reviving an older acceptance."`; basket constituents may use verified non-primary/unclassified inventory explicitly but need unique identities, finite positive exact-100 weights, no overlapping approved ETF or missing-history reweighting.
- [ ] T037 [US3] Wire `review-representations`, `review-listings`, `review-node`, `approve-etf`, `approve-basket`, `collect-etf-candidates`, `review-etf-candidates` and `review-etf-candidate` in `src/market_leadership/universe_admin.py` to the file workflows with required scope/version/as-of/period/source/reference/expected release inputs, explicit `--suitability-reference` and existing confirmations/issues; retire transient `--root`/`--catalog` overrides with registration guidance, wrap retained `local-etf-discovery-1` domain results in the common report, and report durable partial research as exit 2/published/catalog_changed=false without approval.
- [ ] T038 [US3] Run governed contract/integration and existing local evidence/basket regressions in `tests/contract/test_catalog_governance.py`, `tests/integration/test_catalog_governance.py`, `tests/integration/test_local_etf_discovery.py` and `tests/unit/test_industry_representations.py` after replacing their database-backed workflow fixtures where relevant; assert exact provenance/order/IDs, zero unintended approvals, all mutation-affected decisions, shared listing conflict rejection and coherent pre-/post-commit outcomes.

**Checkpoint**: Review history and valid explicit ETF/basket approval operate through files only.
Missing optional research never invalidates unrelated approved data or silently approves evidence.

## Phase 6: User Story 4 - Migrate and Retire Database/Hardcoded Catalog Paths (Priority: P3)

**Goal**: Export/reconcile all legacy evidence and eliminate every alternative production catalog authority.
**Independent Test**: Export controlled schema-1/2/3 sources without upgrade, compare original values/
links/dispositions, activate only reviewed eligible data, then run all workflows with SQL unavailable.

### Tests for User Story 4

- [ ] T039 [P] [US4] Add controlled schema-1/2/3 factories in `tests/conftest.py` and failing migration tests in `tests/integration/test_catalog_migration.py` containing every schema-3 table from data-model section 8, WAL-visible committed rows, arbitrary catalog metadata, expired/empty nodes, inherited reviews, multiple/placeholder/unclassified listings, sub-industry and compatible historical memberships, valid non-primary baskets, raw/nested research payloads and import/review/provenance links; assert no initialization/upgrade or source DB/WAL content changes and honest absent-column/quarantine/limit outcomes.
- [ ] T040 [P] [US4] Add failing retirement/installed-entry contracts in `tests/contract/test_catalog_retirement.py` for old init/validate/import/refresh/database flags and independent settings, and extend `tests/contract/test_catalog_boundaries.py` to all production consumers/fixture routes; permit SQLite only in explicit `export-database`, require actionable errors before data requests and test imports/entry behavior outside the repository working directory without weakening existing provider/cache contracts.

### Implementation for User Story 4

- [ ] T041 [US4] Implement the isolated explicit-path read-only SQLite exporter in `src/market_leadership/infrastructure/catalog_migration.py`, detecting actual schemas 1/2/3 and taking a consistent committed snapshot including WAL rather than hashing only the main file; preserve schema/column presence and canonical typed key/value digests, reject unsupported schemas, never initialize/upgrade/replay imports, and keep SQL imports/connection setup inaccessible to ordinary app/CLI paths.
- [ ] T042 [US4] Implement lossless JSONL archive/reconciliation output in `src/market_leadership/infrastructure/catalog_migration.py` for all twenty tables in data-model section 8, preserving original PK objects, column presence/typed values including raw JSON TEXT/decimal TEXT, safe reasons and target mappings; enforce `"Every source row is stored losslessly, even if also projected into operational CSV/ledger data."`, disposition `"transferred/quarantined/archived"`, `"Disposition accounting counts each original row once, not each duplicated listing/membership CSV row."`, exact logical links/counts/digests and complete/blocked readiness separate from archive completion; oversized records fail explicitly without truncation or complete-lossless claims.
- [ ] T043 [US4] Project eligible legacy source/region/classification/hierarchy/stock/listing/ETF records into registered candidate artifacts in `src/market_leadership/infrastructure/catalog_migration.py`, preserving stored IDs, periods/primary flags/source ownership, inherited review and `"derived legacy membership/row IDs use canonical original keys, not file order/clock."`; map legacy sub-industry assignments to exact industry parent plus original sub-industry ID, retain unclassified/unknown listings as typed inventory, quarantine unresolved/conflicting/unreviewed data and never infer GICS version, name aliases, suitability, hardcoded sector/benchmark mappings or USD/1970 defaults.
- [ ] T044 [US4] Transfer valid baskets and all research/review relationships into the candidate ledger in `src/market_leadership/infrastructure/catalog_migration.py`, keeping positive decimal strings, constituent eligibility, original candidate/evidence/run/review/representation IDs, collection versus review event order, nested payload claims, approval-run versus review-run links, import fingerprints/issues and regional coverage history; preserve missing original rejected rows as explicit absence, keep unusable dependencies archived/quarantined and derive optional root registrations only from explicit retained evidence rather than code defaults.
- [ ] T045 [US4] Wire `export-database --database PATH --output DIR` in `src/market_leadership/universe_admin.py` with lazy exporter import and no retired-environment path inference, returning draft files/archive/reconciliation without source mutation or active entry switch; unsupported/failure/blocked readiness produces exit 2 with retained truthful diagnostics, complete safe export requires separate validation/activation, and recover/normal commands never open SQL.
- [ ] T046 [US4] Move synthetic provider/catalog definitions from `src/market_leadership/infrastructure/fixture_provider.py` into `tests/fixture_provider.py`, update test-only imports in `tests/conftest.py` and affected existing tests, and retire production synthetic construction in `src/market_leadership/application/build_snapshot.py` and `src/market_leadership/bootstrap.py` before any instrument request; keep unrelated historical snapshot readers/calculations/provider cache formats and no replacement runtime fixture switch or approved seed.
- [ ] T047 [US4] Remove production catalog authority from `src/market_leadership/infrastructure/region_database.py` and `src/market_leadership/infrastructure/universe_import.py` after shared validation/export extraction, isolating any needed legacy schema-building fixtures under `tests/conftest.py`; adapt `tests/unit/infrastructure/test_region_database.py`, `tests/unit/infrastructure/test_universe_import.py` and affected administration/membership/review tests to file contracts or explicit migration fixtures instead of retaining a SQL-backed compatibility facade or silently deleting meaningful behavioral assertions.
- [ ] T048 [US4] Refactor or explicitly retire remaining catalog consumers in `src/market_leadership/ui/workflows/industry_discovery.py`, `src/market_leadership/infrastructure/experimental_universe_catalog.py`, `src/market_leadership/infrastructure/provider_catalog.py`, `src/market_leadership/domain/industry_etf_mappings.py` and `src/market_leadership/domain/industry_proxies.py` where they select independent/static instrument authority; complete retirement errors in `src/market_leadership/config.py` and `src/market_leadership/universe_admin.py` for nonempty old database/membership/experimental/display-approval settings and old mutation flags, keep empty template values unset, and audit `src/market_leadership/app.py`/`streamlit_app.py` entry wiring without removing unrelated provider/cache/domain functionality.
- [ ] T049 [US4] Execute migration/retirement/boundary tests in `tests/integration/test_catalog_migration.py`, `tests/contract/test_catalog_retirement.py` and `tests/contract/test_catalog_boundaries.py`, then repeat screening/research/review/ETF/basket workflows with controlled migrated files and SQL guarded unavailable; compare every original row/value/order/link/disposition and prove only explicitly reviewed resolutions enable activation, no former constant is imported as approval, and all production modes have file authority or explicit retirement.

**Checkpoint**: Migration evidence is accounted for and every affected production path is file-only
or deliberately retired. No real database/source has been exported, activated or deleted automatically.

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Make the complete cutover package/documentation accurate and verify all required outcomes.

- [ ] T050 Update breaking package version to `0.2.0` in `pyproject.toml` and synchronized `uv.lock` package metadata using existing package tooling, keeping Python/dependency constraints unchanged; build the distribution with the declared backend and verify `src/market_leadership/infrastructure/catalog-manifest.schema.json` resource/CLI behavior outside the source working directory without adding unnecessary dependencies.
- [ ] T051 Update `README.md`, `.env.example`, `specs/010-manifest-csv-catalogs/contracts/catalog-cli.md` and `specs/010-manifest-csv-catalogs/quickstart.md` to distinguish implemented file commands from explicitly retired APIs and historical references, document backup/export/quarantine/review/activation/recovery/uncertain-commit/version/hosting guidance and manual optional registration of the four original research roots; include the new governance/retirement/boundary selectors in the focused runner, never edit `.env` or ship approved ticker seeds, and preserve earlier completed tasks.
- [ ] T052 Run and record exact SC-004 timing/complete-result measurements from `tests/integration/test_catalog_performance.py` in `specs/010-manifest-csv-catalogs/quickstart.md` on the stated environment; if any cold run exceeds five seconds or warm operation exceeds one second, fix measured loader/index/cache work in `src/market_leadership/infrastructure/catalog_files.py` or `src/market_leadership/ui/cache.py` while retaining signature/hash/domain checks, exact cohort output and zero remote/proxy shortcuts.
- [ ] T053 Run the updated focused quickstart selectors, full `uv run pytest -q -m "not live"`, `uv run ruff check src tests`, strict `uv run pyright`, distribution checks and `git diff --check`; record observed acceptance and justified skips in `specs/010-manifest-csv-catalogs/quickstart.md`, verify every FR/SC and unchanged two-tab/UI/calculation/provider behavior, and use targeted browser validation only with safe provisioned reviewed data if available, reporting any unavailable manual deployment check rather than claiming real cutover.

**Checkpoint**: Full offline/type/lint/package/format and measured acceptance gates pass.
Any real user-data cutover remains an explicit administrator operation with reviewed prerequisites.

## Dependencies and Execution Order

### Phase and Story Graph

```text
Setup T001-T003
  -> Foundation T004-T011
      -> US1 T012-T019 (isolated MVP)
          -> US2 T020-T029 (screening)
          -> US3 T030-T038 (governance)
      -> US4 export tests may be prepared once types/fixtures are ready
US1 + US2 + US3 -> US4 integrated completion T039-T049
US1 + US2 + US3 + US4 -> Polish T050-T053 -> explicit administrator cutover
```

US2 and US3 independently consume the completed US1 file boundary; neither needs the other's
business workflow to demonstrate its independent acceptance. They share reader/admin/representation
files, so default implementation order is US2 then US3. Do not run concurrent writers on those
shared files. US4's exporter core can be developed after typed/read/publication contracts exist,
but its no-SQL/full-consumer acceptance necessarily depends on both screening and governance.

### Task Prerequisites

These are actual prerequisites, not inferred from ID order. Ready tasks sharing files still serialize.
Story gate tasks also require their phase's tests and implementations to be complete.

| Task | Prerequisites |
|---|---|
| T001 | None |
| T002 | None |
| T003 | None |
| T004 | T001, T003 |
| T005 | T001 |
| T006 | T004, T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T009 |
| T011 | T002, T004, T005, T006, T007, T008, T009, T010 |
| T012 | T011 |
| T013 | T011 |
| T014 | T012, T013 |
| T015 | T014 |
| T016 | T015 |
| T017 | T016 |
| T018 | T017 |
| T019 | T012, T013, T014, T015, T016, T017, T018 |
| T020 | T019 |
| T021 | T019 |
| T022 | T019 |
| T023 | T020, T021, T022 |
| T024 | T020, T021, T022 |
| T025 | T020, T021, T022 |
| T026 | T023, T024, T025 |
| T027 | T026 |
| T028 | T026 |
| T029 | T020, T021, T022, T023, T024, T025, T026, T027, T028 |
| T030 | T019 |
| T031 | T019 |
| T032 | T030, T031 |
| T033 | T032 |
| T034 | T033 |
| T035 | T033, T025 |
| T036 | T034, T035 |
| T037 | T036 |
| T038 | T030, T031, T032, T033, T034, T035, T036, T037 |
| T039 | T019 |
| T040 | T019 |
| T041 | T039, T040 |
| T042 | T041 |
| T043 | T042 |
| T044 | T043 |
| T045 | T044, T037 |
| T046 | T029, T038, T045 |
| T047 | T046 |
| T048 | T047 |
| T049 | T029, T038, T039, T040, T041, T042, T043, T044, T045, T046, T047, T048 |
| T050 | T049 |
| T051 | T050 |
| T052 | T051 |
| T053 | T050, T051, T052 |

The T025 -> T035 edge serializes the shared representation-worklist contract before its governed
writes; US3 can use that read projection with controlled fixtures independently of US2 UI completion.
The default numbered order avoids shared-file conflicts even where the graph permits earlier
read-only test preparation/export work. Do not launch agents or install dependencies solely because
a task is parallel-capable.

## Parallel Execution Examples

Only start these waves once the listed prerequisite checkpoint is complete:

| Scope | Ready parallel wave | Why safe |
|---|---|---|
| Setup | T001 + T002 + T003 | Fixture helpers, boundary tests, schema/package resource have separate owners |
| Foundation | T004 + T005 after setup | Shape contracts versus pure domain tests |
| US1 | T012 + T013 after T011 | File/publication tests versus lifecycle/report CLI tests |
| US2 | T020 + T021 + T022 after T019 | Workflow tests, AppTest files, performance test/fixture data |
| US2 | T024 + T025 after its test wave | Sector/regime versus industry/worklist implementations |
| US2 | T027 + T028 after T026 | Separate pages consume the already shared root/cache/selection contract |
| US3 | T030 + T031 after T019 | Existing parser/evidence tests versus new governed file/CLI tests |
| US4 | T039 + T040 after T019 | Migration fixtures/integration versus retirement/boundary contracts |

Example execution requests, not extra tasks:

```text
US1: Add captured-file/publication tests (T012) alongside lifecycle CLI tests (T013).
US2: Implement Discovery (T027) alongside Deep-Dive (T028), after shared root/cache wiring.
US3: Add parser/currentness regressions (T030) alongside governed publication contracts (T031).
US4: Build controlled legacy migration tests (T039) alongside retired-entry/boundary tests (T040).
```

## Requirement and Acceptance Coverage

| Requirement group | Main task coverage | Independent acceptance |
|---|---|---|
| FR-001, FR-009, FR-018 | T002, T023-T028, T032-T037, T040-T049 | SC-006/SC-007; no SQL/static/fixture authority |
| FR-002, FR-003 | T003-T010, T012-T019, T024-T025 | SC-001/SC-002; strict consolidated files/level mappings/benchmarks |
| FR-004, FR-005, FR-006 | T005-T009, T014-T015, T020-T029, T043 | SC-001/SC-003; exact regional/temporal hierarchy and unresolved members |
| FR-007, FR-008 | T004-T005, T012-T019, T031, T036, T038, T040 | SC-001/SC-005; tamper/conflict/commit/recovery |
| FR-010, FR-011, FR-019 | T020-T029, T049, T052-T053 | SC-002/SC-003/SC-004; same snapshot, scoped requests, preserved UI/state |
| FR-012, FR-013, FR-015 | T010, T030-T034, T037-T038, T044 | SC-008; optional research, stable identity, exact decisions/currentness |
| FR-014, FR-016 | T009-T010, T025, T031, T035-T038, T044 | SC-005; explicit valid ETF/basket/provenance, no substitution/reweighting |
| FR-017 | T017, T039-T045, T049, T051 | SC-006; every table/row/link disposition, source preserved, explicit cutover |
| Performance acceptance | T022, T029, T052-T053 | SC-004; actual three cold/ten warm thresholds and full correct output |

## Implementation Strategy

### MVP First: US1 Only

Complete setup, foundation and US1; demonstrate controlled init/validate/activate/recover with no
database. Stop and verify the isolated workflow. This is a developer/reviewer MVP, not permission
to publish incomplete files or deploy while legacy runtime authorities remain reachable.

### Incremental Delivery

1. Complete US1's typed file/publication boundary.
2. Complete US2 screening/benchmark/state handoff while preserving the accepted UI/calculations.
3. Complete US3 local observations, decisions and coherent approval/basket publication.
4. Complete US4 controlled export, lossless accounting and removal/retirement of alternative authorities.
5. Complete package/docs, measured performance and full validation before any real deployment switch.
6. The administrator separately supplies reviewed classification/source/listing/suitability evidence,
   backs up original data, resolves quarantine and deliberately validates/activates a reviewed release.

### Completion Evidence

Check tasks only after their described behavior passes, not because files exist. Retain exact
row/request/state/order/identity comparisons and measured timings. Do not mark manual deployment
or real-data migration performed when only controlled offline scenarios ran. No automatic commit,
branch change, production CSV rewrite, dependency expansion or database cutover is implied.

## Phase 8: Convergence

**Assessment**: 2026-11-01. These tasks record current implementation gaps, not checkbox-based
completion claims. Follow the existing dependency table and test-first prerequisites, especially
T030/T031 and T039/T040. Complete and verify the referenced original work rather than duplicate
behavior already satisfied by the time this phase is reached. Do not activate, export, mutate,
or delete real user data as part of these tasks.

- [ ] T054 CRITICAL: Retire reachable synthetic market/fundamental/catalog construction in `src/market_leadership/bootstrap.py`, `src/market_leadership/application/build_snapshot.py`, and `src/market_leadership/infrastructure/fixture_provider.py` by completing T046 after its existing prerequisites; retain synthetic definitions only in test helpers and require actionable retirement before instrument requests, preserving unrelated historical snapshot readers and calculations per Constitution: Application and Data Constraints (selected runtime data source), FR-009, SC-007, and T046 (contradicts).
- [ ] T055 Complete T047-T049 retirement of production SQL authority in `src/market_leadership/infrastructure/region_database.py`, `src/market_leadership/infrastructure/universe_import.py`, `src/market_leadership/universe_admin.py`, and remaining catalog consumers; make nonempty legacy settings in `src/market_leadership/config.py` and old mutation/database flags fail with migration guidance before SQL or provider access, while keeping SQL exclusively in the explicit read-only exporter and preserving meaningful legacy test assertions per FR-001, FR-018, SC-007, T040, and T047-T049 (contradicts).
- [ ] T056 Replace embedded `DEFAULT_ROOTS`/`DEFAULT_CATALOGS` and transient research overrides in `src/market_leadership/infrastructure/local_etf_sources.py` with explicit snapshot research registrations by completing T030/T032; preserve bounded static extraction, canonical containment, source-project read-only behavior, occurrence/context identity, and honest missing/partial/unobservable outcomes without reading unregistered inputs per FR-012, US3/AC1, and T030/T032 (contradicts).
- [ ] T057 Complete T033-T034 file-ledger observation, candidate, decision, and currentness workflows in `src/market_leadership/infrastructure/catalog_files.py` and `src/market_leadership/application/discover_etf_candidates.py`; reuse existing typed decoding/domain algorithms, immutable prior ledger prefixes, exact scope/version/run/evidence links, expected-release publication, separate event order, latest rejection, and mutation-affected re-review without duplicate evidence/reviews or inferred removal from incomplete inspection per FR-013, FR-015, SC-008, US3/AC3-AC4, and T033-T034/T038 (partial).
- [ ] T058 Implement the missing governed file-based node-update workflow in `src/market_leadership/application/industry_representations.py` by completing T035; validate exact node/parent/scope/version/source/reference/effective-period evidence against the snapshot and publish the hierarchy change with append-only node-review links through the coherent publisher, never by name authorization or guessed classification version per plan: reviewed node updates, FR-006, and T035 (missing).
- [ ] T059 Complete T036 file-based ETF and explicit basket approval in `src/market_leadership/application/industry_representations.py` and `src/market_leadership/application/discover_etf_candidates.py`; publish mapping, selected candidate review, approval, and provenance as one expected-parent operation, retaining exact verified listing/source/suitability/full-period checks, latest rejection, qualified inventory/non-primary basket constituents, exact positive 100% weights, ETF precedence, and no missing-history reweighting or fabricated basket charts per FR-014, FR-016, US3/AC2/AC4/AC5, and T036 (partial).
- [ ] T060 Wire the eight governed review/collection/approval commands in `src/market_leadership/universe_admin.py` to file workflows by completing T037; require the planned classification-version, suitability, expected-release, date, source, and selected-evidence inputs, retire unregistered research overrides, and wrap domain results in truthful versioned publication reports including durable partial-research exit 2 without catalog approval, rather than opening `RegionDatabase` or emitting success-shaped legacy reports per plan: CLI contract, FR-008, FR-013, FR-014, and T037 (partial).
- [ ] T061 Implement `src/market_leadership/infrastructure/catalog_migration.py` and lazy `export-database` wiring in `src/market_leadership/universe_admin.py` by completing T039/T041-T045; support explicit read-only schema-1/2/3 committed snapshots including WAL, losslessly archive/account for every row across all twenty tables, preserve typed original keys/values/order/provenance and exact safe operational projections, and report transfer/quarantine/archive readiness without inferred approval, source mutation, source deletion, database upgrade, or automatic activation per FR-017, SC-006, US4/AC1-AC3, and T039/T041-T045 (missing).
- [ ] T062 Add the absent controlled file-governance, migration, and retirement acceptance suites in `tests/contract/test_catalog_governance.py`, `tests/integration/test_catalog_governance.py`, `tests/integration/test_catalog_migration.py`, and `tests/contract/test_catalog_retirement.py` by completing T031/T039/T040; retain and adapt meaningful SQL-backed evidence tests, demonstrate the intended failures before corresponding implementation, and verify exact history/currentness, coherent fault/conflict outcomes, twenty-table dispositions, installed entry behavior, and all workflows with SQL unavailable before closing T038/T049 per SC-005, SC-006, SC-007, SC-008, and T031/T038-T040/T049 (missing).
- [ ] T063 Finish T050/T051/T053 after migration/retirement acceptance: synchronize the planned `0.2.0` package metadata in `pyproject.toml` and `uv.lock`, verify the built schema resource and CLI outside the source working directory, finalize truthful implemented-versus-retired operational guidance in `README.md`, `.env.example`, `specs/010-manifest-csv-catalogs/contracts/catalog-cli.md`, and `specs/010-manifest-csv-catalogs/quickstart.md`, and record passing focused/full offline, lint/type, and distribution gates without claiming real deployment cutover; preserve the already-satisfied SC-004 benchmark instead of introducing speculative optimization per plan: versioning and final acceptance, FR-017, FR-019, and T050/T051/T053 (partial).
- [ ] T064 Resolve the explicit six-stock-column expectation in T021 against the current five-column projection and its tests in `src/market_leadership/ui/components/progressive_tape.py`, `tests/unit/ui/test_progressive_tape.py`, and `tests/app/test_sector_stock_explorer.py`; obtain an explicit feature-intent resolution before changing presentation or acceptance expectations, retaining the current ticker/company-name button and five-column UI until approved rather than automatically restoring the redundant Name column per T021 and FR-019 (contradicts).
