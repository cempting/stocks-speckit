# Tasks: Market Leadership Screener

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
in `specs/001-market-leadership-screener/`.

**Baseline**: T001–T026 are completed Phase 1–2 work, retained without renumbering or reopening.
They provide US daily price/volume ingestion, source cache, canonical daily *input* snapshots and
live-provider discovery (development default), not release weekly leadership. The US/JP/GB acceptance
fixture is controlled data only. Do not claim live JP/GB ingestion, non-price feeds or display
licenses from fixture conformance. At release, replace the development default with the latest
completed weekly **SECTOR** scoreboard; preserve live US discovery as a separate development path
until that workflow is ready.

**Architecture**: Pure domain rules; application use cases; explicit provider/repository adapters;
Streamlit workflows through the existing registry. Follow `contracts/deferred-evidence.md` before
implementing story-specific deferred sources. Every new behavior starts with a failing automated
test; no Phase 2 manifest or runtime capability is silently promoted to weekly/non-price support.
`[P]` indicates independent tasks touching separate files.

## Phase 1: Setup

**Purpose**: Initialize package, tooling and controlled acceptance inputs.

- [X] T001 Initialize the Python 3.12 `uv` project, runtime dependencies, and lockfile in `pyproject.toml` and `uv.lock`
- [X] T002 Create the package and test directory skeleton with `src/market_leadership/__init__.py` and `tests/unit/domain/test_models.py`
- [X] T003 Define dated controlled acceptance inputs and expected outputs in `tests/fixtures/acceptance/market_data.json` and `tests/fixtures/acceptance/expected.json`
- [X] T004 Configure Ruff, Pyright, pytest, and test discovery in `pyproject.toml`

---

## Phase 2: Foundational

**Purpose**: Establish shared data contracts, adapters, configuration, and explicit workflow
composition before story implementation.

**Critical**: No user story work begins until this phase is complete.

- [X] T005 [P] Write domain-record and enum contract tests in `tests/unit/domain/test_models.py`
- [X] T006 [P] Write manifest validation tests for every required field, declared format, SHA-256 pattern, and `additionalProperties: false` rule in `tests/contract/test_snapshot_manifest.py`
- [X] T007 [P] Write shared provider conformance tests for as-of filtering, deterministic ordering, typed empty results, duplicate rejection, same-date FX behavior, source traceability, and canonical schemas in `tests/contract/test_market_data_provider.py`
- [X] T008 [P] Write registry tests for one default, unique stable keys and paths, deterministic order, and replacement of any one workflow in `tests/app/test_navigation.py`
- [X] T009 Implement frozen, slotted domain records and enums in `src/market_leadership/domain/models.py`: hierarchy levels `SECTOR`, `INDUSTRY_GROUP`, `INDUSTRY`, `SUB_INDUSTRY`; instrument kinds `STOCK`, `FUND`, `INDEX`; proxy types `FUND`, `INDEX`, `EQUAL_WEIGHT_BASKET`, `NONE`; slope states `RISING`, `FLAT`, `FALLING`, `UNDEFINED`; regimes `BULLISH`, `SIDEWAYS`, `BEARISH`, `INSUFFICIENT`; and release asset category `EQUITY`; keep Company distinct from each listed Instrument
- [X] T010 Define `MarketDataProvider`, `MarketDataProviderCatalog`, and `SnapshotRepository` protocols with explicit typed requests, provider-capability candidates, selection reasons, and results in `src/market_leadership/application/ports.py`
- [X] T011 Implement the deterministic reference adapter with typed empty results, stable ordering, and source availability dates in `src/market_leadership/infrastructure/fixture_provider.py`
- [X] T012 Implement canonical Parquet input validation and `SnapshotNotFound`, `SchemaMismatch`, `IntegrityError`, and `SourceUnavailable` errors in `src/market_leadership/infrastructure/parquet_provider.py`
- [X] T013 Implement read-only snapshot loading and atomic snapshot publication in `src/market_leadership/infrastructure/parquet_repository.py`
- [X] T014 Implement environment and snapshot-path configuration in `src/market_leadership/config.py`; load the ignored local `.env` with `python-dotenv` for development without overriding process environment variables
- [X] T015 Define the frozen `WorkflowSpec` descriptor and `st.Page` conversion in `src/market_leadership/ui/navigation.py`, and assemble the explicit ordered registry with exactly one default in `src/market_leadership/bootstrap.py`; capture dependencies in render callables and do not discover pages dynamically
- [X] T016 Add the Streamlit entrypoint with exactly one `st.navigation` call in `src/market_leadership/app.py`
- [X] T017 [P] Write catalog and adapter contract tests for Massive REST and `yfinance` covering capability enumeration, all matching providers per requested data point, request mapping, pagination, explicit adjusted-price behavior, canonical schema conversion, deterministic ordering, provenance, typed empty results, retryable failures, and secret-safe errors in `tests/contract/test_runtime_market_data_providers.py`
- [X] T018 [P] Write source-cache tests for deterministic request fingerprints, valid fresh hits with zero upstream calls, missing/invalid/schema-incompatible/under-covered misses, checksum rejection, atomic writes, and unconditional `force=True` refresh in `tests/unit/infrastructure/test_market_data_cache.py`
- [X] T019 [P] Write runtime request integration tests proving discovery returns all matching providers, selection is deterministic by canonical-schema compatibility then requested coverage then configured priority then provider ID, Massive is preferred only when configured and capable, `yfinance` selection is explicit, a missing or under-covered entry invokes only the selected provider once, a fresh entry invokes the upstream zero times, force invokes the selected provider once, no failure silently changes providers, and refresh failure preserves prior cache while blocking new publication in `tests/integration/test_refresh_market_data.py`
- [X] T020 [P] Write Streamlit cache tests proving immutable snapshot loads are keyed by snapshot ID and manifest checksum, a new published checksum invalidates the load, session filters do not affect the shared cache key, normal page reruns make no upstream provider requests, and explicit runtime refresh delegates exactly once to the request use case in `tests/app/test_snapshot_cache.py`
- [X] T021 Extend typed configuration with ordered direct provider IDs, provider priorities, source-cache path, retry limits, and external `MASSIVE_API_KEY` credential reference in `src/market_leadership/config.py`; do not store credentials in snapshots, cache metadata, logs, or Streamlit state
- [X] T022 Implement configured capability discovery and canonical US adjusted daily-history access for index and stock price/volume through `yfinance` in `src/market_leadership/infrastructure/yfinance_provider.py`; retain all matching provider candidates and reject unsupported data points explicitly without ranking or eligibility logic
- [X] T023 Implement an atomic canonical daily-history provider source cache in `src/market_leadership/infrastructure/market_data_cache.py`; key entries by provider identity, logical data point, normalized request, schema version, identifiers, date range, frequency, return basis, and currency basis, write canonical records as Parquet plus a JSON manifest, and record retrieval time, coverage start/end, source availability, selected provider, alternatives, selection reason, and SHA-256 checksums
- [X] T024 Implement runtime discovery, deterministic provider selection, request, and refresh orchestration in `src/market_leadership/application/request_market_data.py`; return all matching provider candidates, select by canonical-schema compatibility then requested coverage then configured priority then provider ID, reuse only checksum-valid schema-compatible cache covering the latest required session, bypass every hit when `force=True`, preserve but never publish stale data after upstream failure, and never switch providers implicitly after selection
- [X] T025 Integrate the runtime request service into canonical US daily-history input snapshot construction, configured provider selection, required-session calculation, and `--force-refresh` in `src/market_leadership/application/build_snapshot.py`, and document direct adapters, provider selection, runtime refresh, Parquet/manifest storage, and cache behavior in `specs/001-market-leadership-screener/quickstart.md`; weekly calculated scoreboards are deferred
- [X] T026 Implement immutable `st.cache_data` daily input snapshot loading keyed only by snapshot ID and manifest checksum in `src/market_leadership/ui/cache.py` and wire runtime request and optional snapshot dependencies through `src/market_leadership/bootstrap.py`; keep live-provider discovery the default, upstream clients and refresh state outside the shared data cache, and Phase 2 UI selections in session state (story-level filters, search, sort, and drill-down are deferred)

**Checkpoint**: Contracts, provider discovery, adapters, Parquet/manifest cache, runtime refresh
policy, and composition root are ready. Discovery returns all matching providers and explains the
deterministic selection. A fresh source cache causes no upstream call; missing, invalid,
incompatible, or under-covered data refreshes; force always refreshes; snapshot-mode reruns read
immutable daily input snapshots without upstream calls.

---

## Phase 3: User Story 1 - Select and Compare Markets (P1)

**Goal**: Select one or several markets while keeping independent local benchmark, calendar, regime,
currency, dates and sector context. This phase uses fixture-backed JP/GB; live ingestion remains US
only. US1 can be tested using the fixture's three-month sector outcomes before US2 builds full
weekly rankings. Do not switch the default page to a weekly scoreboard yet.

**Independent test**: Using `tests/fixtures/acceptance/{market_data,expected}.json`, switch US,
JP, GB and multiple selections; assert each regime and top/bottom sector is local, with no pooled
ranking. Missing/late local data is flagged without suppressing valid markets.

### Tests first (confirm failing before implementation)

- [X] T027 [P] [US1] Test effective-dated market/benchmark/catalog capability, currency, calendar, availability, unsupported live JP/GB and optional same-close FX contracts using dated fixture benchmark histories in `tests/contract/test_market_context.py`
- [X] T028 [P] [US1] Test 150-session SMA, normalized OLS slope over 20 latest averages, strict `+0.025%`/`-0.025%` boundaries, bullish/bearish/sideways, undefined slope with present close/average yielding sideways, and missing close or average yielding insufficiency in `tests/unit/domain/test_regimes.py`
- [X] T029 [P] [US1] Test fixture-backed one/many market selection, US/JP/GB expected regimes and local top/bottom sectors, distinct dates/currencies/benchmarks, local/global disagreement and missing FX isolation in `tests/integration/test_compare_markets.py`
- [X] T030 [P] [US1] Test Streamlit market multiselect, retained valid shared selection, per-market local contexts and stale/empty/error states without pooled results in `tests/app/test_market_selection.py`

### Implementation (after T027–T030 fail as intended)

- [X] T031 [US1] Implement effective-dated market definitions, benchmark/optional FX capability records, source availability and fail-closed unsupported requests in `src/market_leadership/application/ports.py` and `src/market_leadership/infrastructure/fixture_provider.py`; extend `tests/fixtures/acceptance/market_data.json` with deterministic dated US/JP/GB benchmark close histories sufficient to calculate the declared regimes; use only fixture data for JP/GB and require rights/source verification before any non-US live adapter
- [X] T032 [P] [US1] Implement 150-session average and 20-average OLS slope normalized by latest average as percent in `src/market_leadership/domain/regimes.py`; `> +0.025%` rising and `< -0.025%` falling, equality flat; fewer than 20 averages yields undefined slope and sideways when close/average exist, while missing close or average yields insufficient regime
- [X] T033 [US1] Implement fixture-backed per-market overview and local sector outcome selection with dates/return basis, benchmark, currency, freshness and optional separately labelled global context in `src/market_leadership/application/compare_markets.py`; preserve valid local result if global FX is absent
- [X] T034 [US1] Implement session-local multiselect and per-market panels without pooled ranks in `src/market_leadership/ui/workflows/discovery_page.py` and `src/market_leadership/bootstrap.py`; keep live US discovery the development default and snapshot mode optional until weekly release workflow exists

**Checkpoint**: US/JP/GB multi-market fixture acceptance passes without suggesting JP/GB live availability.

---

## Phase 4: User Story 2 - Find Sector and Industry Leadership (P1)

**Goal**: Publish/read versioned weekly calculated snapshots; rank SECTOR within each selected
market by default, then drill into dated INDUSTRY children retaining the local and parent contexts.

**Independent test**: Controlled aligned 1w/1m/3m/6m/12m and 50-session histories prove composite,
status, tie order, prior-week deltas, sector default, industry drill-down and missing-history rules.

### Tests first

- [X] T035 [P] [US2] Test `contracts/weekly-leadership.md` effective-dated sector/industry ancestry, representation fund/index/basket composition and qualification, latest completed local week, weekly manifest version and refusal to read Phase 2 daily inputs as calculated results in `tests/contract/test_weekly_leadership.py`
- [X] T036 [P] [US2] Test absolute and local-benchmark-relative 1w/1m/3m/6m/12m returns with shared ending observations, matching currency/return bases, missing twelve-month and 50-session history in `tests/unit/domain/test_relative_strength.py`
- [X] T037 [P] [US2] Test 40%/30%/30% composite, strict positive-above-average gaining, strict negative-below-average declining, equality neutral, sufficient-only within-market rank, 6m/3m/12m/name ties, prior weekly score/rank deltas and strengthening/weakening/stable labels in `tests/unit/domain/test_rankings.py`
- [X] T038 [P] [US2] Test immutable calculated weekly publish/load, market holidays and incomplete weeks, industry versus both parent sector and local benchmark, per-market isolation and missing-proxy insufficiency in `tests/integration/test_build_weekly_leadership.py`
- [X] T039 [P] [US2] Test default completed-week SECTOR rows and industry drill-down preserving market, benchmark, sector, dates, bases, insufficient/empty/error states in `tests/app/test_scoreboard.py`

### Implementation (after T035–T039 fail as intended)

- [X] T040 [US2] Implement dated classification/representation canonical input validation and fixture adapter in `src/market_leadership/application/ports.py` and `src/market_leadership/infrastructure/fixture_provider.py`; require documented fund/index/basket source, type, composition basis and effective dates, without assuming live classification/holdings licenses
- [X] T041 [US2] Implement separately versioned weekly calculated manifest/table validation, atomic publish/read and rejection of daily input manifests in `src/market_leadership/infrastructure/parquet_repository.py`; preserve existing Phase 2 input schema in `contracts/snapshot-manifest.schema.json`
- [X] T042 [P] [US2] Implement matching-basis absolute/local relative returns over 1w/1m/3m/6m/12m and `0.4*RS_3m+0.3*RS_6m+0.3*RS_12m` in `src/market_leadership/domain/relative_strength.py`; no comparison without a shared eligible ending observation
- [X] T043 [P] [US2] Implement dated fund/index/basket representation selection and insufficiency reasons (no unapproved numeric fund thresholds) in `src/market_leadership/domain/proxies.py`
- [X] T044 [US2] Implement 50-session composite average, gaining/declining/neutral, within-market sector/industry ranks, tie-break order, weekly score/rank change and descriptive momentum in `src/market_leadership/domain/rankings.py`; missing twelve-month or 50-session history has no rank/status
- [X] T045 [US2] Extend offline builder for completed local-market weekly calculation and atomic publication in `src/market_leadership/application/build_snapshot.py`; retain existing daily input-build path and never combine markets or publish partial invalid results
- [X] T046 [US2] Implement per-market sector browse query and parent-sector/local-market industry inspection in `src/market_leadership/application/browse_scoreboard.py` and `src/market_leadership/application/inspect_industry.py`; retain active market/benchmark/date/return-basis context
- [X] T047 [US2] Implement supplied-value-only ranking and regime components in `src/market_leadership/ui/components/ranking_table.py` and `src/market_leadership/ui/components/regime_summary.py`; display rank, status, composite, score/rank deltas, proxy, as-of and insufficiency
- [X] T048 [US2] Implement weekly SECTOR default and INDUSTRY drill-down in `src/market_leadership/ui/workflows/scoreboard.py`, `src/market_leadership/ui/workflows/industry_detail.py` and `src/market_leadership/bootstrap.py`; switch default only after weekly fixture-backed acceptance succeeds

**Checkpoint**: A completed weekly sector scoreboard is the release default, not Phase 2 live discovery.

---

## Phase 4a: User Story 2 - Unified Sector Discovery (P1; extends US1)

**Goal**: Replace the two navigation pages with one default Discovery workflow. Offer explicit
Weekly leadership (fixture-backed calculated weekly snapshots), US live daily sectors, and
US acceptance comparison modes; do not conflate their metrics or data sources. Remove only the
user-facing **Published snapshot** daily-input mode, not the weekly snapshot store, builder, or
daily-input publication APIs. The visible market selector is US-only in every mode until authorized
live non-US sources are available. Keep JP/GB fixture data, multi-market use cases, and their
non-UI acceptance tests intact so other markets can be enabled later without redesign. Do not
silently replace a missing weekly result with a live or acceptance result.

**Independent test**: Open the app and see one default Discovery page and US weekly sector
rankings with industry drill-down. Switch to US live daily sectors and US acceptance comparison
explicitly; verify the different dates, bases, and source labels and that live fetch/refresh occurs
only in live mode. JP/GB and Published snapshot are absent from all user-facing options, but the
underlying US/JP/GB fixture comparison and weekly calculations still pass. With no weekly snapshot,
show an actionable missing-weekly state without fetching upstream or displaying a substitute rank.

**ID note**: T001–T075 are retained verbatim (including unfinished T049–T075). New IDs start at
T076 rather than renumbering history; execute this phase after T048 and before pending US3–US5 and
release tasks despite the append-only ID sequence.

### Design alignment

- [ ] T076 [US2] Record the interim US-only visible-market policy, three explicit modes, no daily Published snapshot UI, unchanged weekly snapshot contract, and future non-US enablement gate in `specs/001-market-leadership-screener/spec.md` and `specs/001-market-leadership-screener/plan.md`; distinguish interim UI scope from the existing multi-market acceptance requirement

### Tests first (confirm failing before implementation)

- [ ] T077 [P] [US2] Test one default Discovery registry entry at the existing `discovery` URL, workflow replacement, and no separate `scoreboard` navigation entry in `tests/app/test_navigation.py`; document `/scoreboard` as retired rather than implying it redirects
- [ ] T078 [P] [US2] Test unified app default, weekly US-only selector (JP/GB unavailable), local weekly ranking and industry drill-down, explicit mode changes without leaking prior sector state, and actionable missing/invalid weekly snapshot states without live or fixture fallback in `tests/app/test_scoreboard.py`
- [ ] T079 [P] [US2] Test US-only live daily and acceptance comparison modes, explicit fixture/non-weekly labels, no Published snapshot option, source-specific dates/provider/refresh controls, live error and stale states, and no upstream fetch outside live mode in `tests/app/test_market_selection.py`; retain US/JP/GB multi-market fixture acceptance through `tests/integration/test_compare_markets.py` rather than exposing JP/GB in the UI

### Implementation (after T077–T079 fail as intended)

- [ ] T080 [US2] Extract a callable US daily/acceptance renderer from `src/market_leadership/ui/workflows/discovery_page.py` without its own navigation registration; remove only the Published snapshot UI branch, keep live provider/cache/refresh and fixture comparison behavior, limit visible fixture selection to US, and keep source failures explicit
- [ ] T081 [US2] Add the explicit Weekly leadership (default), US live daily, and US acceptance comparison modes to `src/market_leadership/ui/workflows/scoreboard.py`; reuse the T080 renderer, expose only US in the market selector, label weekly snapshots as controlled fixtures, preserve industry drill-down and independent missing-weekly/error states, and ensure mode changes never trigger an implicit provider request or ranking fallback
- [ ] T082 [US2] Register one default Discovery workflow at URL `discovery` in `src/market_leadership/bootstrap.py` and `src/market_leadership/app.py`; remove the redundant `scoreboard` page entry and preserve workflow replacement semantics
- [ ] T083 [US2] Update the mode and market-availability instructions, weekly build steps, retired daily Published snapshot UI and route migration in `specs/001-market-leadership-screener/quickstart.md` and `specs/001-market-leadership-screener/contracts/workflow.md`; retain daily-input and weekly CLI/storage documentation

**Checkpoint**: One explicitly sourced US-only Discovery page; no misleading live JP/GB option,
no daily Published snapshot UI, and multi-market fixture calculations remain independently tested.

---

## Phase 4b: User Story 2 - Dedicated Industry Discovery (P1; extends US1)

**Goal**: Provide a separately navigable Industry Discovery page, modeled on sector discovery,
with direct entry and selection of one or more parent sectors (the requested "vectors"). A sector
selection in the unified Discovery workflow opens this page prefiltered to that sector and the
same evidence mode: fixture-backed weekly sector → weekly industry, US live daily sector → live
US industry. Weekly and live dates, return bases, and metrics must never be silently combined.
Keep the existing weekly US/JP/GB calculation and fixture tests; only US is user-facing until
authorized non-US live sources are available.

For live US industries, research dated industry-to-ETF matches and permitted display/derived-data
rights first. Prefer a qualified ETF with documented industry composition; otherwise use the
largest **as-of-date market-cap** stock from verified dated industry membership, explicitly
labelled a single-company proxy, not an industry-wide or diversified fund. Missing verified
membership, size, rights, matching price history, or proxy qualification leaves that industry
insufficient, not guessed or silently excluded. This is a new, live-only representation policy;
do not reinterpret existing `weekly-1.0.0` snapshots or advertise live weekly rankings.

**Independent test**: Open Industry Discovery directly, select one or several US parent sectors,
and verify only their dated industries appear with correct sector ancestry and independently
labelled source/basis. Click a sector in weekly Discovery and arrive at weekly industries for its
completed week; click a live sector and arrive at live US industries for the requested/usable
daily observation. Verify a vetted ETF wins over the largest eligible constituent, stock fallback
is explicit, and no-qualified-proxy or stale/misaligned data is insufficient without suppressing
other industries. Navigation back, switching modes, invalid sector IDs, missing snapshots, and
provider failures must not leak selections or fabricate results.

**ID note**: Append T084–T098 without renumbering historical T001–T083. Execute this phase after
T076–T083 and before pending US3–US5 UI integration and release checks.

### Design and source gate

- [ ] T084 [US2] Specify direct-entry and click-through Industry Discovery acceptance, US-only visible scope, multi-sector parent-ID filtering, mode-matched weekly/live navigation, and the live-only single-stock proxy exception in `specs/001-market-leadership-screener/spec.md`, `specs/001-market-leadership-screener/plan.md`, `specs/001-market-leadership-screener/data-model.md`, and `specs/001-market-leadership-screener/contracts/workflow.md`; explicitly preserve weekly snapshot compatibility and clarify that live returns are not weekly ranks
- [ ] T085 [US2] Research dated US industry taxonomy/membership, candidate industry ETFs and their actual constituent exposure, as-of market-cap sources, identifier mappings, source availability and permitted live display/derived-data rights in `specs/001-market-leadership-screener/research.md` and `specs/001-market-leadership-screener/contracts/us-industry-proxies.md`; record a reproducible ETF qualification policy and per-industry source/effective date, reject broad or mismatched funds, and block live enablement for any industry without verified rights and dated membership/capitalization rather than inventing a symbol or using present-day size retrospectively

### Tests first (confirm failing before implementation)

- [ ] T086 [P] [US2] Test dated qualified industry ETF precedence, single-stock fallback to largest verified as-of-date member by market cap, deterministic ties, invalid/expired/misclassified candidates, missing size/rights and explicit no-qualified-proxy reasons in `tests/unit/domain/test_industry_proxies.py`; a stock proxy must never be labelled diversified or silently enter the existing weekly representation contract
- [ ] T087 [P] [US2] Test live US industry catalog provenance, taxonomy/sector ancestry, dated membership/capitalization, effective dates, source availability, duplicate/conflicting candidates, unsupported non-US and license/coverage rejection in `tests/contract/test_industry_catalog.py`; do not accept today's membership or capitalization as historical evidence
- [ ] T088 [P] [US2] Test live industry discovery over one/multiple parent sectors with the same eligible ending US benchmark and parent-sector observations, adjusted 1w/1m/3m/6m/12m absolute/local-relative returns, separately labelled parent-relative evidence, stock-fallback caveat and per-industry stale/insufficient isolation in `tests/integration/test_discover_industries.py`; live mode must not invent composite ranks, weekly status or snapshot data
- [ ] T089 [P] [US2] Test weekly industry browse with one/multiple parent sector IDs, unchanged existing local rank scope, matching sector/industry week, benchmark/currency/return basis, empty/missing/misaligned snapshots and invalid/foreign parent IDs in `tests/integration/test_browse_industries.py`
- [ ] T090 [P] [US2] Test directly opened Industry Discovery weekly default, US-only multi-sector selector, mode-specific source labels, sector filter reset, missing data, invalid handoff and operational errors in `tests/app/test_industry_discovery.py`; unmatched industries must remain visible as insufficient
- [ ] T091 [P] [US2] Test click-through from both weekly and US live sector discovery into the separate Industry Discovery page, preselected stable parent ID, retained source mode/date/market context, valid back-navigation and no cross-mode session-state leakage in `tests/app/test_sector_to_industry.py`

### Implementation (after T086–T091 fail as intended)

- [ ] T092 [US2] Model the **live-only** ETF/single-`STOCK` industry candidate and ETF-first, dated/as-of selection in `src/market_leadership/domain/industry_proxies.py`; keep `src/market_leadership/domain/models.py` and `src/market_leadership/domain/proxies.py` weekly fund/index/basket types unchanged, require verified industry membership plus dated positive market cap for stock fallback, and emit typed insufficiency rather than silently selecting an unqualified proxy
- [ ] T093 [US2] Implement the researched, rights-gated dated US industry candidate catalog and provider capability boundary in `src/market_leadership/application/ports.py` and `src/market_leadership/infrastructure/industry_catalog.py`; use only T085-verified mappings/metadata, fail closed for absent/expired membership or cap evidence and unsupported markets, and do not claim a live ETF or stock when source permission is unverified
- [ ] T094 [US2] Implement on-demand US live industry discovery through existing daily-history request/cache adapters in `src/market_leadership/application/discover_industries.py`; filter by selected sector node IDs before loading candidates, align ETF/stock, parent-sector and SPY observations to a shared eligible session, reuse domain return calculations, preserve per-industry insufficiency, and expose explicit proxy type, source, age, parent-relative and local-relative bases without calculating a fake weekly score
- [ ] T095 [P] [US2] Extend weekly industry inspection for one or more valid parent sector node IDs in `src/market_leadership/application/inspect_industry.py`; reuse the published INDUSTRY snapshot, retain each row's original market/hierarchy rank and local/parent context, reject mismatched sector/industry weeks and never merge weekly rows with live results
- [ ] T096 [US2] Build the separate US-only Industry Discovery workflow and its direct-entry/mode-specific parent-sector selection in `src/market_leadership/ui/workflows/industry_discovery.py` and `src/market_leadership/ui/state.py`; use T094/T095 application results, show weekly fixture versus live ETF/stock sources and dates clearly, display insufficient rows and source failures, and scope/reset handoff state so changing mode cannot reuse an incompatible sector or date
- [ ] T097 [US2] Make sector selections open mode-matched Industry Discovery and register its stable `industry-discovery` URL without changing the existing default `discovery` route in `src/market_leadership/ui/workflows/scoreboard.py`, `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/bootstrap.py`, and `src/market_leadership/app.py`; keep direct entry and back-navigation working and avoid retaining a duplicate inline industry ranking as the only drill-down
- [ ] T098 [US2] Document direct-entry and sector-click journeys, weekly fixture and live proxy limitations, representative-stock caveat, research/rights gate, missing-data states and no live non-US support in `specs/001-market-leadership-screener/quickstart.md` and `specs/001-market-leadership-screener/contracts/workflow.md`; retain existing weekly artifact/build instructions

**Checkpoint**: Direct and sector-linked US Industry Discovery works for matched weekly and live
modes, with dated proxy provenance and explicit insufficiency. Live industry capability cannot be
declared complete without the T085 source and rights gate.

---

## Phase 5: User Story 3 - Assess Participation and Momentum Quality (P2)

**Goal**: Add optional dated constituent breadth, cap/equal-weight disagreement, and explicitly
inferred volume evidence. Missing confirmation never changes US2 leadership.

**Independent test**: Dated memberships, histories and weights yield expected 50/200-session
breadth with at least five eligible members and at least 80% coverage; partial weights/volume are
insufficient only for dependent indicators.

### Tests first

- [ ] T049 [P] [US3] Test effective-dated constituent membership/weights and aligned close/volume contract, duplicate rejection, source availability and partial coverage in `tests/contract/test_participation_inputs.py`
- [ ] T050 [P] [US3] After recording an approved numerical material-disagreement policy in `specs/001-market-leadership-screener/research.md`, test 50/200-session participation percentages, included/eligible counts, `<5` and `<80%` insufficiency, cap/equal-weight comparison and price/breadth divergence in `tests/unit/domain/test_participation.py`
- [ ] T051 [P] [US3] Test relative-volume/volume-pressure missing-history behavior and prohibition on observed-flow terminology in `tests/unit/domain/test_trading_activity.py`
- [ ] T052 [P] [US3] Test missing membership/weight/volume isolation from price rank and separate evidence dates/coverage in `tests/integration/test_confirmation_evidence.py`
- [ ] T053 [P] [US3] Test industry evidence UI for breadth, concentration, inferred activity, divergence and insufficient evidence in `tests/app/test_participation.py`

### Implementation (after T049–T053 fail as intended)

- [ ] T054 [US3] Implement dated constituent/weight canonical fixture inputs and capability rejection for unsupported live holdings in `src/market_leadership/application/ports.py` and `src/market_leadership/infrastructure/fixture_provider.py`; verify sources/rights before enabling live providers
- [ ] T055 [P] [US3] Implement eligible-member 50/200-session breadth, explicit counts/coverage and cap/equal-weight comparison with versioned materiality threshold in `src/market_leadership/domain/participation.py`; never apply present-day membership retrospectively
- [ ] T056 [P] [US3] Implement optional close/volume relative-volume or pressure indicators labelled inferred trading activity in `src/market_leadership/domain/trading_activity.py`; never label volume as actual inflow
- [ ] T057 [US3] Integrate separately dated breadth, concentration, divergence and activity evidence without affecting price leadership in `src/market_leadership/application/inspect_industry.py`
- [ ] T058 [US3] Render confirmation with source, counts, coverage and insufficiency in `src/market_leadership/ui/components/evidence_panel.py` and `src/market_leadership/ui/workflows/industry_detail.py`

---

## Phase 6: User Story 4 - Inspect Observed Fund-Flow Evidence (P3)

**Goal**: Present observed fund flows only when qualified inputs exist, independently of price,
breadth and volume. Missing, stale or overlapping funds do not create synthetic flow totals.

**Independent test**: Positive/negative, conflicting, stale, partial, missing and overlapping fund
records expose monetary value, percent of compatible assets, event/publication dates, source,
represented classification, age and coverage without changing score, rank or status.

### Tests first

- [ ] T059 [P] [US4] Test dated observed net-flow/asset input schema, units, source availability, overlap group, positive compatible assets and unsupported-live capability in `tests/contract/test_observed_flows.py`
- [ ] T060 [P] [US4] Test `100 * net_flow / assets`, invalid/late assets, overlap without aggregation, age, stale/partial/unavailable states and conflict with price in `tests/unit/domain/test_flows.py`
- [ ] T061 [P] [US4] Test flow contextual isolation from score/rank/status/momentum, price-rise/volume/asset-change non-equivalence and divergence in `tests/integration/test_flow_evidence.py`
- [ ] T062 [P] [US4] Test fund-flow UI provenance, positive/negative, stale/partial/unavailable and price divergence in `tests/app/test_observed_flows.py`

### Implementation (after T059–T062 fail as intended)

- [ ] T063 [US4] Implement observed-flow/asset fixture contract, overlap provenance and unsupported-live rejection in `src/market_leadership/application/ports.py` and `src/market_leadership/infrastructure/fixture_provider.py`; require verified rights and coverage before a live adapter is enabled
- [ ] T064 [US4] Implement measured-flow normalization, freshness/coverage and non-aggregation of overlapping funds in `src/market_leadership/application/flows.py`; leave score/rank/status untouched
- [ ] T065 [US4] Render distinct observed-flow panel with monetary value, percent assets, event/availability dates, age, source and warning in `src/market_leadership/ui/components/evidence_panel.py` and `src/market_leadership/ui/workflows/industry_detail.py`

---

## Phase 7: User Story 5 - Filter and Trust Discovery Results (P2)

**Goal**: Filter/sort selected markets' results, clear criteria without clearing market selection,
and expose provenance, definitions and non-advice guidance for every displayed metric.

**Independent test**: Mixed multi-market fixture supports conjunction of all requested filters,
five sorts, one-step reset and empty state; provenance fields are present or explicitly unavailable.

### Tests first

- [ ] T066 [P] [US5] Test conjunctive market/level/status/momentum/proxy/sufficiency filters, name/rank/composite/score-change/rank-change sort, ties and selected-market-preserving reset in `tests/integration/test_browse_filters.py`
- [ ] T067 [P] [US5] Test per-metric observation/comparison period, return/currency basis, benchmark, representation, source, source availability, coverage and freshness or explicit unavailable fields in `tests/contract/test_provenance.py`
- [ ] T068 [P] [US5] Test filter UI active criteria, clear, empty state, unchanged market selection and sort in `tests/app/test_filters.py`
- [ ] T069 [P] [US5] Test required definitions and historical-not-forecast/advice/trade warning, plus stale/misaligned dependent-indicator suppression in `tests/app/test_methodology.py`

### Implementation (after T066–T069 fail as intended)

- [ ] T070 [US5] Implement typed conjunctive filter/sort query and stable local ranking scope in `src/market_leadership/application/queries.py` and `src/market_leadership/application/browse_scoreboard.py`
- [ ] T071 [US5] Implement session-local selected markets, active criteria, clear-to-sector and sorting in `src/market_leadership/ui/state.py` and `src/market_leadership/ui/components/filters.py`; clear filters preserves market selection
- [ ] T072 [P] [US5] Implement source/availability/coverage/basis/freshness display with explicit unavailable fields in `src/market_leadership/ui/components/provenance.py`
- [ ] T073 [US5] Implement metric definitions, historical evidence disclaimer and no personalized advice/trade instruction in `src/market_leadership/ui/workflows/methodology.py` and surface provenance from `src/market_leadership/ui/workflows/scoreboard.py`

---

## Phase 8: Polish and Release Validation

- [ ] T074 Test 20-market controlled filter/sort interactions meet two seconds for at least 95% of trials in `tests/integration/test_browse_performance.py`; optimize only if measured results require it
- [ ] T075 Verify `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, `uv run pytest` and release validation scenarios against `specs/001-market-leadership-screener/quickstart.md`; do not claim unverified live source rights

## Dependency Graph and Parallel Work

- T001–T026 (completed) → US1 T027–T034 → US2 T035–T048 → unified Discovery
  T076–T083 → Industry Discovery T084–T098 → US3 T049–T058 and US4 T059–T065
  → US5 T066–T073 → release T074–T075.
- US1 market definitions/fixture context precede US2 ranking. US2 weekly price rankings are required
  before unified Discovery; its mode-matched sector entry and T085 source/rights research precede
  live Industry Discovery. The separate industry page is required before pending US3/US4 UI integration.
  US3 and US4 can proceed independently after that page. US5 depends on US2 and the unified page
  and Industry Discovery for filters and on US3/US4 for complete provenance and definitions.
- In each story, independent `[P]` tests may be written concurrently; T077–T079 can run in
  parallel after T076, followed by T080 → T081 → T082 → T083. After T084/T085, T086–T091
  are independent test files; T095 can be implemented alongside T092–T094 before T096 → T097
  → T098. Confirm tests fail for absent
  behavior before implementation. Independent implementation files T032 (US1), T042/T043 (US2),
  T055/T056 (US3) can follow their own failing tests in parallel; the integration task follows
  all producers. No task marked `[P]` relies on another unfinished task in its phase.

## Implementation Strategy and Requirement Coverage

MVP: US1 fixture-backed market selection, US2 weekly SECTOR scoreboard, unified US-only Discovery
(T076–T083), then separately navigable, mode-matched Industry Discovery (T084–T098). Live industry
results are gated on verified source rights and dated ETF/stock representation; if those cannot be
established, report the live increment blocked rather than substituting fixture results. US3/US4
add optional, non-ranking evidence; US5 adds filters and trust before release. Preserve the existing
daily input path and multi-market
application contracts throughout even though daily Published snapshot and non-US fixtures are not
user-facing. Validate each checkpoint with its
focused contract/unit/integration/AppTest files and then the full suite.

| Requirements | Tests and implementation |
|---|---|
| FR-001–FR-006 | US1 T027–T034; US2 T035, T038–T048 and unified T076–T083 (non-US fixtures retained but hidden pending live sources) |
| FR-007–FR-014 | US2 T035–T048; unified T078/T081 and industry T084–T098 preserve mode-matched sector-to-industry UX |
| FR-015–FR-018 | US2 T037/T044; US3 T049–T058 |
| FR-019–FR-021 | US4 T059–T065 |
| FR-022–FR-023 | US5 T066/T068/T070/T071 |
| FR-024–FR-027 | US1 T027/T029; US3 T052/T053; US4 T059/T062; US5 T067/T069/T072/T073 |

**Open release gate**: Select and document authorized live non-US market, classification,
membership/weight and observed-flow sources (including permitted display/derived-data rights,
availability and freshness) before enabling those capabilities. Approve a numerical material
cap/equal-weight disagreement policy before T050/T055. Fixtures keep discovery testable without a
provider decision; no such license or live adapter is presumed.
