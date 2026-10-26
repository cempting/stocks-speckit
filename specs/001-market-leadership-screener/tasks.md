# Tasks: Market Leadership Screener

**Input**: Design documents in `specs/001-market-leadership-screener/`

**Generation context**: Add a Streamlit discovery mode for all 11 US GICS sectors. It shows the
current S&P 500 market regime as sentiment, a three/six/twelve-month performance table switchable
between absolute sector returns and returns relative to the S&P 500, and one chart per sector with
official-session close, 50-session SMA, and volume. The existing weekly Industry scoreboard remains
the default required by FR-002.

Discover providers for required index and stock data points through a configured
`MarketDataProviderCatalog`. Direct adapters include Massive REST, preferred when
`MASSIVE_API_KEY` is configured, and an explicitly selected `yfinance` adapter for development and
personal-use deployments; configured financial-market MCP sources may contribute additional
providers without becoming the deployed application's credential path. Runtime discovery returns
every provider whose declared capabilities cover the requested data point, market, identifiers,
frequency, date range, currency, and return basis, then deterministic policy selects one and records
the alternatives and selection reason. Provider failures do not silently switch vendors. Persist
canonical provider responses as Parquet tables with JSON manifest metadata in an atomic source
cache. Reuse an entry only when its schema and checksum are valid and its coverage reaches the
request's latest required completed market session; refresh missing, invalid, incompatible, or
under-covered entries, and always refresh on explicit force. Normal Streamlit reruns read immutable
published snapshots; upstream calls occur only through the runtime request use case for
stale/missing data or an explicit refresh action.

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and contracts.

**Architecture constraint**: Preserve the four layers: pure domain, application use cases,
infrastructure adapters, and Streamlit UI. The UI calls domain behavior only through application use
cases. Use an explicit `WorkflowSpec` registry; do not add dynamic plugins, a backend service, or a
database.

## Phase 1: Setup

**Purpose**: Initialize the Python package, tools, and deterministic acceptance data.

- [ ] T001 Initialize the Python 3.12 `uv` project, runtime dependencies, and lockfile in `pyproject.toml` and `uv.lock`
- [ ] T002 Create the package and test directory skeleton with `src/market_leadership/__init__.py` and `tests/unit/domain/test_models.py`
- [ ] T003 Define dated controlled acceptance inputs and expected outputs in `tests/fixtures/acceptance/market_data.json` and `tests/fixtures/acceptance/expected.json`
- [ ] T004 Configure Ruff, Pyright, pytest, and test discovery in `pyproject.toml`

---

## Phase 2: Foundational

**Purpose**: Establish shared data contracts, adapters, configuration, and explicit workflow
composition before story implementation.

**Critical**: No user story work begins until this phase is complete.

- [ ] T005 [P] Write domain-record and enum contract tests in `tests/unit/domain/test_models.py`
- [ ] T006 [P] Write manifest validation tests for every required field, declared format, SHA-256 pattern, and `additionalProperties: false` rule in `tests/contract/test_snapshot_manifest.py`
- [ ] T007 [P] Write shared provider conformance tests for as-of filtering, deterministic ordering, typed empty results, duplicate rejection, same-date FX behavior, source traceability, and canonical schemas in `tests/contract/test_market_data_provider.py`
- [ ] T008 [P] Write registry tests for one default, unique stable keys and paths, deterministic order, and replacement of any one workflow in `tests/app/test_navigation.py`
- [ ] T009 Implement frozen, slotted domain records and enums in `src/market_leadership/domain/models.py`: hierarchy levels `SECTOR`, `INDUSTRY_GROUP`, `INDUSTRY`, `SUB_INDUSTRY`; instrument kinds `STOCK`, `FUND`, `INDEX`; proxy types `FUND`, `INDEX`, `EQUAL_WEIGHT_BASKET`, `NONE`; slope states `RISING`, `FLAT`, `FALLING`, `UNDEFINED`; regimes `BULLISH`, `SIDEWAYS`, `BEARISH`, `INSUFFICIENT`; and release asset category `EQUITY`; keep Company distinct from each listed Instrument
- [ ] T010 Define `MarketDataProvider`, `MarketDataProviderCatalog`, and `SnapshotRepository` protocols with explicit typed requests, provider-capability candidates, selection reasons, and results in `src/market_leadership/application/ports.py`
- [ ] T011 Implement the deterministic reference adapter with typed empty results, stable ordering, and source availability dates in `src/market_leadership/infrastructure/fixture_provider.py`
- [ ] T012 Implement canonical Parquet input validation and `SnapshotNotFound`, `SchemaMismatch`, `IntegrityError`, and `SourceUnavailable` errors in `src/market_leadership/infrastructure/parquet_provider.py`
- [ ] T013 Implement read-only snapshot loading and atomic snapshot publication in `src/market_leadership/infrastructure/parquet_repository.py`
- [ ] T014 Implement environment and snapshot-path configuration in `src/market_leadership/config.py`; load the ignored local `.env` with `python-dotenv` for development without overriding process environment variables
- [ ] T015 Define the frozen `WorkflowSpec` descriptor and `st.Page` conversion in `src/market_leadership/ui/navigation.py`, and assemble the explicit ordered registry with exactly one default in `src/market_leadership/bootstrap.py`; capture dependencies in render callables and do not discover pages dynamically
- [ ] T016 Add the Streamlit entrypoint with exactly one `st.navigation` call in `src/market_leadership/app.py`
- [ ] T017 [P] Write catalog and adapter contract tests for Massive REST, `yfinance`, and configured MCP sources covering capability enumeration, all matching providers per requested data point, request mapping, pagination, explicit adjusted-price behavior, canonical schema conversion, deterministic ordering, provenance, typed empty results, retryable failures, and secret-safe errors in `tests/contract/test_runtime_market_data_providers.py`
- [ ] T018 [P] Write source-cache tests for deterministic request fingerprints, valid fresh hits with zero upstream calls, missing/invalid/schema-incompatible/under-covered misses, checksum rejection, atomic writes, and unconditional `force=True` refresh in `tests/unit/infrastructure/test_market_data_cache.py`
- [ ] T019 [P] Write runtime request integration tests proving discovery returns all matching providers, selection is deterministic by canonical-schema compatibility then requested coverage then configured priority then provider ID, Massive is preferred only when configured and capable, `yfinance` selection is explicit, a missing or under-covered entry invokes only the selected provider once, a fresh entry invokes the upstream zero times, force invokes the selected provider once, no failure silently changes providers, and refresh failure preserves prior cache while blocking new publication in `tests/integration/test_refresh_market_data.py`
- [ ] T020 [P] Write Streamlit cache tests proving immutable snapshot loads are keyed by snapshot ID and manifest checksum, a new published checksum invalidates the load, session filters do not affect the shared cache key, normal page reruns invoke MCP zero times, and explicit runtime refresh delegates exactly once to the request use case in `tests/app/test_snapshot_cache.py`
- [ ] T021 Extend typed configuration with ordered direct provider IDs, optional MCP discovery endpoints and allowed tool/resource names, provider priorities, source-cache path, retry limits, and external `MASSIVE_API_KEY` credential reference in `src/market_leadership/config.py`; do not store credentials in snapshots, cache metadata, logs, or Streamlit state
- [ ] T022 Implement configured capability discovery and canonical access for Massive REST, `yfinance`, and optional MCP sources in `src/market_leadership/infrastructure/massive_provider.py`, `src/market_leadership/infrastructure/yfinance_provider.py`, `src/market_leadership/infrastructure/mcp_provider_catalog.py`, and `src/market_leadership/infrastructure/mcp_provider.py`; retain all providers matching the requested data point and normalize selected index, stock, price, volume, FX, classification, holdings, fundamentals, and evidence responses without ranking or eligibility logic
- [ ] T023 Implement an atomic canonical provider source cache in `src/market_leadership/infrastructure/market_data_cache.py`; key entries by provider identity, logical data point, normalized request, schema version, identifiers, date range, frequency, return basis, and currency basis, write canonical records as Parquet plus a JSON manifest, and record retrieval time, coverage start/end, source availability, selected provider, alternatives, selection reason, and SHA-256 checksums
- [ ] T024 Implement runtime discovery, deterministic provider selection, request, and refresh orchestration in `src/market_leadership/application/request_market_data.py`; return all matching provider candidates, select by canonical-schema compatibility then requested coverage then configured priority then provider ID, reuse only checksum-valid schema-compatible cache covering the latest required session, bypass every hit when `force=True`, preserve but never publish stale data after upstream failure, and never switch providers implicitly after selection
- [ ] T025 Integrate the runtime request service into snapshot construction, configured provider selection, required-session calculation, and `--force-refresh` in `src/market_leadership/application/build_snapshot.py`, and document direct adapters, MCP discovery, provider selection, runtime refresh, Parquet/manifest storage, and cache behavior in `specs/001-market-leadership-screener/quickstart.md`
- [ ] T026 Implement immutable `st.cache_data` snapshot loading keyed only by snapshot ID and manifest checksum in `src/market_leadership/ui/cache.py` and wire runtime request dependencies through `src/market_leadership/bootstrap.py`; keep upstream clients and refresh state outside the shared data cache and keep filters, search, sort, and drill-down in session state

**Checkpoint**: Contracts, provider discovery, adapters, Parquet/manifest cache, runtime refresh
policy, and composition root are ready. Discovery returns all matching providers and explains the
deterministic selection. A fresh cache causes no upstream call; missing, invalid, incompatible, or
under-covered data refreshes; force always refreshes; normal reruns read immutable snapshots.

---

## Phase 3: User Story 1 - Find Market Leadership (Priority: P1) MVP

**Goal**: Produce the dated weekly market-regime and GICS Industry scoreboard with auditable
strength, ranking, proxy, and insufficiency outcomes, plus a US-sector discovery workflow that
compares absolute and S&P 500-relative performance and charts sector price, 50-session SMA, and
volume.

**Independent Test**: Load a dated dataset containing known market and industry outcomes and verify
that the view shows each market regime, ranks industries, and distinguishes gaining, neutral,
declining, and insufficient-data entries according to the domain rules. Open discovery mode and
verify that all 11 effective US GICS sectors appear, the displayed sentiment matches the S&P 500
regime, switching performance mode changes the table from absolute returns to S&P 500-relative
returns for the same three/six/twelve-month periods, and every sector chart includes close, 50-session
SMA, and volume without changing the default Industry scoreboard.

### Tests for User Story 1

Write and confirm these tests fail before implementing the story.

- [ ] T027 [P] [US1] Test OLS slope indices 0 through 19, normalized boundaries exactly `+0.025%` and `-0.025%`, values outside each boundary, fewer than 20 values, and missing close or average behavior in `tests/unit/domain/test_regimes.py`
- [ ] T028 [P] [US1] Test three-, six-, and twelve-calendar-month relative returns with matching benchmark, currency, and return bases, including missing required history, in `tests/unit/domain/test_relative_strength.py`
- [ ] T029 [P] [US1] Test the 40%/30%/30% composite, gaining and declining equality boundaries, rounded-up top 20%, and tie-break order in `tests/unit/domain/test_rankings.py`
- [ ] T030 [P] [US1] Test proxy qualification, rejected-threshold reasons, and fallback order in `tests/unit/domain/test_proxies.py`
- [ ] T031 [P] [US1] Test dated snapshot building, latest completed market week, and insufficient-data outcomes over controlled inputs in `tests/integration/test_build_snapshot.py`
- [ ] T032 [P] [US1] Test the default scoreboard regimes, dated ranking, required row fields, and loading, empty, insufficient, and operational-error states with Streamlit `AppTest` in `tests/app/test_scoreboard.py`

### Implementation for User Story 1

- [ ] T033 [P] [US1] Implement normalized 20-session OLS slope and market regimes in `src/market_leadership/domain/regimes.py`: divide per-session slope by the latest average and express it as a percentage; greater than `+0.025%` is `RISING`, less than `-0.025%` is `FALLING`, and both boundaries and values between them are `FLAT`; fewer than 20 averages is `UNDEFINED` and not rising; with close and average present undefined slope yields `SIDEWAYS`, while missing either yields `INSUFFICIENT`
- [ ] T034 [P] [US1] Implement matching-basis three-, six-, and twelve-calendar-month relative returns and the 40%/30%/30% composite in `src/market_leadership/domain/relative_strength.py`; missing required twelve-month history or comparison-average history produces insufficiency, never a guessed value
- [ ] T035 [US1] Implement sufficient-entry ranking, status, top-group membership, and tie-breaking in `src/market_leadership/domain/rankings.py`: gaining requires composite `> 0` and `> 50-session composite average`; declining requires composite `< 0` and `<` that average; equality and all other values are neutral; top-group size is `ceil(0.20 * ranked_count)`; ties use six-month, three-month, twelve-month strength, then name without changing tied composite values
- [ ] T036 [P] [US1] Implement proxy selection and qualification reasons in `src/market_leadership/domain/proxies.py`: prefer the most liquid qualifying fund with purity at least 60%, AUM at least `$100 million`, and 20-session USD-equivalent ADV at least `$2 million`; otherwise choose an official index as reference-only; otherwise choose an equal-weight basket of at least five eligible stocks, each with ADV at least `$5 million`; otherwise use `NONE` and mark the node insufficient
- [ ] T037 [US1] Implement deterministic offline calculation, validation, and snapshot-build orchestration in `src/market_leadership/application/build_snapshot.py`; publish no partial snapshot and preserve valid local results when same-date FX is missing for global comparison
- [ ] T038 [US1] Implement the initial scoreboard query over calculated snapshots in `src/market_leadership/application/browse_scoreboard.py`, ranking only sufficient entries and preserving benchmark and market context
- [ ] T039 [US1] Implement supplied-value-only regime rendering in `src/market_leadership/ui/components/regime_summary.py`
- [ ] T040 [US1] Implement ranking-row rendering with name, rank, status, composite strength, week-over-week change, proxy type, eligibility state, and as-of date in `src/market_leadership/ui/components/ranking_table.py`
- [ ] T041 [US1] Implement the default weekly Industry scoreboard workflow through application use cases in `src/market_leadership/ui/workflows/scoreboard.py`
- [ ] T042 [P] [US1] Test absolute sector returns, S&P 500-relative returns, matching three/six/twelve-month periods and return bases, 50-session SMA values, and insufficient history in `tests/unit/domain/test_sector_performance.py`
- [ ] T043 [P] [US1] Test discovery queries return all 11 effective US GICS sectors in deterministic name order with S&P 500 sentiment, both performance modes, dated close/SMA50/volume series, and explicit insufficient records in `tests/integration/test_discover_sectors.py`
- [ ] T044 [P] [US1] Test discovery initial render, absolute-versus-S&P-500 segmented control, all-sector table and charts, selected and alternative runtime data providers, fresh-cache behavior, explicit forced refresh, empty state, insufficient state, and safe MCP failure with Streamlit `AppTest` in `tests/app/test_discovery.py`
- [ ] T045 [US1] Implement absolute sector returns, S&P 500-relative returns, and 50-session simple moving averages over matching return bases in `src/market_leadership/domain/relative_strength.py`; preserve missing history as insufficient and never forward-fill a missing sector or benchmark close
- [ ] T046 [US1] Implement a typed US-sector discovery query that selects the 11 effective US `SECTOR` nodes, uses their selected proxies, returns S&P 500 `MarketRegime` as sentiment, and supplies three/six/twelve-month absolute and relative performance plus dated close/SMA50/volume chart series in `src/market_leadership/application/discover_sectors.py`
- [ ] T047 [P] [US1] Implement a supplied-value-only sector performance table with an absolute-versus-S&P-500 segmented mode control and explicit period, basis, as-of, and insufficiency labels in `src/market_leadership/ui/components/sector_performance_table.py`
- [ ] T048 [P] [US1] Implement a stable all-sector chart component with official-session close and 50-session SMA in the price panel and aligned volume below it in `src/market_leadership/ui/components/sector_chart.py`
- [ ] T049 [US1] Implement the discovery workflow with current sentiment, performance table, one chart per sector, selected-provider provenance, alternative-provider details, cache freshness, and an explicit force-refresh action in `src/market_leadership/ui/workflows/discovery.py` and `src/market_leadership/ui/components/data_source_status.py`, then register its stable non-default `WorkflowSpec` in `src/market_leadership/bootstrap.py` without changing the default scoreboard

**Checkpoint**: Verify the P1 independent test. The MVP is this story with the shared foundation and
controlled fixture.

---

## Phase 4: User Story 2 - Focus the Market View (Priority: P2)

**Goal**: Support market, hierarchy, status, top-group, eligibility, and proxy filters; search,
sorting, drill-down, and reset.

**Independent Test**: Apply each supported filter to a mixed dataset and verify that only matching
entries remain, active criteria are visible, and clearing the criteria restores the complete view.

### Tests for User Story 2

- [ ] T050 [P] [US2] Test combined market, hierarchy, leadership, top-group, eligibility, and proxy filters plus name, company, and symbol search and every supported sort field in `tests/integration/test_browse_filters.py`
- [ ] T051 [P] [US2] Test visible active criteria, clear-all behavior, empty-result explanation and reset path, and hierarchy navigation retaining market and benchmark context in `tests/app/test_filters.py`

### Implementation for User Story 2

- [ ] T052 [US2] Define typed filter, search, and sort request records for market, hierarchy, status, top-group membership, research eligibility, proxy type, name/company/symbol search, sort field, and sort direction in `src/market_leadership/application/queries.py`
- [ ] T053 [US2] Implement session-local filter and drill-down state in `src/market_leadership/ui/state.py`; clearing state restores the weekly Industry scoreboard without hidden criteria
- [ ] T054 [US2] Implement filter controls that return user intent without mutating dataframes or session state in `src/market_leadership/ui/components/filters.py`
- [ ] T055 [US2] Implement combined filtering, search, and sorting in `src/market_leadership/application/browse_scoreboard.py`; sort only visible results by name, rank, composite, status, or week-over-week change
- [ ] T056 [US2] Integrate controls and typed browse requests in `src/market_leadership/ui/workflows/scoreboard.py`; display active criteria and the explanatory empty state
- [ ] T057 [US2] Implement hierarchy drill-down and return navigation while retaining market and benchmark context in `src/market_leadership/ui/workflows/scoreboard.py`

**Checkpoint**: Verify all criteria combine correctly, reset restores the default view, and empty
results remain recoverable.

---

## Phase 5: User Story 3 - Inspect Leading and Declining Stocks (Priority: P3)

**Goal**: Show industry context, candidate gates, survival evidence, and holding review flags without
generating automatic sale instructions.

**Independent Test**: Open a known industry, inspect its constituent stocks, and verify that stock
relative strength, industry status, eligibility warnings, and data sufficiency are shown separately.

### Tests for User Story 3

- [ ] T058 [P] [US3] Test deterioration transitions `CLEAR --monthly outside top--> COUNTING_1`, `COUNTING_1 --monthly outside top--> ACTIVE`, `COUNTING_1` and `ACTIVE --monthly back in top and not declining--> CLEAR`, and `ANY --weekly declining--> ACTIVE` in `tests/unit/domain/test_deterioration.py`
- [ ] T059 [P] [US3] Test every stock candidate gate and distinct pass, fail, and insufficient outcomes, including stale fundamentals, in `tests/unit/domain/test_candidates.py`
- [ ] T060 [P] [US3] Test constituent inspection, separate industry eligibility, and holding-review flags for stable instrument IDs in `tests/integration/test_inspect_industry.py`
- [ ] T061 [P] [US3] Test industry and stock detail initial, interaction, empty, insufficient-data, and safe operational-failure states in `tests/app/test_stock_research.py`

### Implementation for User Story 3

- [ ] T062 [P] [US3] Implement monthly and weekly deterioration transitions and holding flags in `src/market_leadership/domain/deterioration.py`; monthly outside-top reviews count consecutively, the second activates the flag, monthly return to top clears it only when not declining, and any weekly declining status activates it; emit `REVIEW_REDUCE` for affected supplied holdings with `automatic_sale = false`
- [ ] T063 [P] [US3] Implement survival and candidate gates in `src/market_leadership/domain/candidates.py`: require positive three- and six-month strength versus industry, `PASS` survival, fundamentals no older than two quarters, non-extreme volatility, matching primary classification, proxy weight at least 5% or proxy rank in the top 10, and a nonblank written reason; compute quarterly cash burn as `max(0, capital_expenditure - operating_cash_flow)` after excluding non-cash items; zero burn means unlimited runway, otherwise runway is `cash_and_equivalents / quarterly_cash_burn / 4` and must be at least two years; independently require EBIT TTM divided by interest expense TTM to meet size/volatility minimums above `$10B` = `1.5/2/3/4`, `$2B` through `$10B` = `2/3/4/5`, and below `$2B` = `3/4/5/6` for Low/Medium/High/Extreme; exempt financial companies only from interest cover; return `PASS`, `FAIL`, or `INSUFFICIENT` distinctly
- [ ] T064 [US3] Implement industry, constituent-stock, survival, and evidence inspection use cases in `src/market_leadership/application/inspect_industry.py`
- [ ] T065 [US3] Implement industry detail with status, local eligibility, constituents, and deterioration warnings in `src/market_leadership/ui/workflows/industry_detail.py`
- [ ] T066 [US3] Implement stock research details with each candidate gate, failure reason, stale or missing evidence, and written reason in `src/market_leadership/ui/workflows/stock_research.py`

**Checkpoint**: Confirm a declining industry blocks new-buy candidacy and raises review/reduce
information, never an automatic sale.

---

## Phase 6: User Story 4 - Understand and Trust the Evidence (Priority: P4)

**Goal**: Expose benchmark context, provenance, lagged evidence, definitions, and interpretation
warnings.

**Independent Test**: Inspect representative market, industry, and stock entries and verify that each
metric exposes its meaning, comparison basis, as-of date, data sufficiency, and relevant warning.

### Tests for User Story 4

- [ ] T067 [P] [US4] Test local/global disagreement, same-date FX insufficiency, source provenance, and isolation of lagged evidence from ranking and eligibility in `tests/integration/test_evidence_and_provenance.py`
- [ ] T068 [P] [US4] Test all required term definitions, historical-performance disclaimer, methodology initial render, and evidence interaction in `tests/app/test_methodology.py`
- [ ] T069 [P] [US4] Test required provenance fields and explicit unavailable-source representation in `tests/contract/test_provenance.py`

### Implementation for User Story 4

- [ ] T070 [US4] Extend inspection view records with local and global benchmarks, currency and return bases, as-of and comparison dates, source availability, and explicit missing-FX warnings in `src/market_leadership/application/inspect_industry.py`
- [ ] T071 [P] [US4] Implement provenance rendering for date, basis, instrument, benchmark, source name, and source availability, marking unavailable fields explicitly, in `src/market_leadership/ui/components/provenance.py`
- [ ] T072 [P] [US4] Implement `EvidenceItem` rendering with event date, availability date, age, coverage, and source in `src/market_leadership/ui/components/evidence_panel.py`
- [ ] T073 [US4] Implement definitions for market regime, relative strength, gaining, declining, neutral, top group, proxy, deterioration, and insufficient data, plus the historical-performance and non-advice warning, in `src/market_leadership/ui/workflows/methodology.py`
- [ ] T074 [US4] Display local and global benchmark views side by side with benchmark, currency basis, return basis, and global warning in `src/market_leadership/ui/workflows/industry_detail.py`
- [ ] T075 [US4] Add source and availability provenance, stale-data warnings, and relevant evidence in `src/market_leadership/ui/workflows/stock_research.py`
- [ ] T076 [US4] Keep lagged `EvidenceItem` records out of scoreboard rank, status, top-group, and eligibility inputs and allow them only as separate context or review/watchlist priority in `src/market_leadership/application/browse_scoreboard.py`

**Checkpoint**: Verify evidence remains contextual, local eligibility remains authoritative, and
unavailable provenance is explicit.

---

## Phase 7: User Story 5 - Preserve Equity Results During Extension (Priority: P5)

**Goal**: Protect established equity outputs and prevent default application of equity ranking
semantics to unspecified asset categories.

**Independent Test**: Add an acceptance fixture for one separately specified asset category
containing at least 100 instruments and verify that all baseline equity outputs and controls remain
unchanged.

### Tests for User Story 5

- [ ] T077 [P] [US5] Freeze baseline equity calculations, labels, history, and filter outcomes, then test that adding a separately specified category with at least 100 instruments leaves every baseline result unchanged in `tests/integration/test_asset_category_compatibility.py` and `tests/fixtures/equity_baseline.json`
- [ ] T078 [P] [US5] Test that a category without approved ranking semantics receives neither GICS nor equity gain/decline rules by default in `tests/integration/test_asset_category_dispatch.py`

### Implementation for User Story 5

- [ ] T079 [US5] Implement the release `EQUITY` category discriminator without changing company, instrument, or equity calculation semantics in `src/market_leadership/domain/models.py`
- [ ] T080 [US5] Dispatch only explicitly specified asset categories at the composition boundary and keep unspecified categories out of equity domain calculations in `src/market_leadership/bootstrap.py`

**Checkpoint**: Confirm the baseline equity fixture and controls remain identical after category
dispatch is introduced.

---

## Phase 8: Polish and Cross-Cutting Concerns

**Purpose**: Validate scale, operational instructions, and required quality gates.

- [ ] T081 Add a 20-market and 10,000-stock browse fixture and verify filter, search, sort, and hierarchy interactions meet the two-second target in `tests/integration/test_browse_performance.py` and `tests/fixtures/scale/market_20_stocks_10000.json`
- [ ] T082 Validate install, fixture snapshot build, app startup, and focused test commands against `specs/001-market-leadership-screener/quickstart.md`
- [ ] T083 Update usage and architectural boundaries for the implemented snapshot workflow and explicit registry in `README.md`
- [ ] T084 Run Ruff format/check, Pyright, and the full pytest suite using the project gates in `pyproject.toml`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: No dependencies; starts immediately.
- **Foundational**: Depends on Setup and blocks every user story.
- **US1**: Starts after Foundational and supplies the MVP scoreboard.
- **US2**: Depends on US1 scoreboard queries and workflow.
- **US3**: Depends on US1 industry results and US2 hierarchy context.
- **US4**: Depends on US1 and US3 result views; evidence remains independently testable.
- **US5**: Depends on frozen outputs from US1 and US2; it must not change their semantics.
- **Polish**: Follows all stories selected for delivery.

### Within Each User Story

- Write the story's tests first and confirm they fail for the expected missing behavior.
- Implement domain behavior before application use cases and application use cases before UI.
- Run the focused story tests at its checkpoint before starting the next story.
- Run the full suite before marking the story complete.

### Parallel Opportunities

- Foundational contract tests T005-T008 can run in parallel.
- MCP catalog, cache, runtime refresh, and Streamlit cache tests T017-T020 can run in parallel; T022 and T023 can proceed together after T010 and T021, while T024 waits for both.
- US1 tests T027-T032 and T042-T044 can run in parallel; after T009, T033, T034, and T036 touch independent modules, while T047 and T048 can run together after T046 defines their view records.
- US2 tests T050-T051 can run in parallel.
- US3 tests T058-T061 can run in parallel; T062 and T063 touch independent domain modules.
- US4 tests T067-T069 can run in parallel; T071 and T072 touch independent UI components.
- US5 tests T077-T078 can run in parallel.

## Parallel Examples

### User Story 1

```text
T027: Test market regimes in tests/unit/domain/test_regimes.py
T028: Test relative strength in tests/unit/domain/test_relative_strength.py
T030: Test proxy selection in tests/unit/domain/test_proxies.py
T042: Test sector performance in tests/unit/domain/test_sector_performance.py
T043: Test US-sector discovery in tests/integration/test_discover_sectors.py
T044: Test discovery workflow in tests/app/test_discovery.py
```

### User Story 2

```text
T050: Test browse filters in tests/integration/test_browse_filters.py
T051: Test filter workflow behavior in tests/app/test_filters.py
```

### User Story 3

```text
T058: Test deterioration in tests/unit/domain/test_deterioration.py
T059: Test candidates in tests/unit/domain/test_candidates.py
T061: Test stock research workflows in tests/app/test_stock_research.py
```

### User Story 4

```text
T067: Test evidence and provenance integration in tests/integration/test_evidence_and_provenance.py
T068: Test methodology workflow in tests/app/test_methodology.py
T069: Test provenance contract in tests/contract/test_provenance.py
```

### User Story 5

```text
T077: Test frozen equity compatibility in tests/integration/test_asset_category_compatibility.py
T078: Test category dispatch in tests/integration/test_asset_category_dispatch.py
```

## Requirement Coverage

- **FR-001**: T009, T031, T041, T043, T046, T049
- **FR-002**: T031-T032, T037, T041, T049
- **FR-003**: T027, T033, T039
- **FR-004**: T028, T034, T042-T046
- **FR-005**: T029, T034
- **FR-006**: T029, T035
- **FR-007**: T029, T035
- **FR-008**: T067, T070, T074
- **FR-009**: T051, T057, T065
- **FR-010**: T050, T052-T056
- **FR-011**: T050, T052, T055-T056
- **FR-012**: T051, T053-T056
- **FR-013**: T032, T040
- **FR-014**: T030, T036
- **FR-015**: T058-T059, T062-T066
- **FR-016**: T058, T060, T062, T065
- **FR-017**: T059-T061, T063-T066
- **FR-018**: T043-T049, T059-T061, T063-T066
- **FR-019**: T043-T049, T067, T069-T072, T075
- **FR-020**: T067, T072, T075-T076
- **FR-021**: T068, T073
- **FR-022**: T068, T073
- **FR-023**: T077-T080

## Input-Derived Coverage

- **MCP-001 - Find every runtime-capable provider for a requested data point**: T010, T017, T019, T021-T022, T024, T044, T049
- **MCP-002 - Request through deterministic provider selection and refresh only when stale/missing or forced**: T018-T020, T023-T026, T044, T049
- **MCP-003 - Store canonical acquired data in an appropriate typed format**: T006, T018, T023, T025, T082

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational.
2. Complete User Story 1.
3. Stop and validate the P1 independent test and full suite.
4. Demo the fixture-backed weekly Industry scoreboard before expanding scope.

### Incremental Delivery

1. Add US2 filtering and navigation, then validate independently.
2. Add US3 stock research and deterioration, then validate independently.
3. Add US4 evidence and interpretation, then validate independently.
4. Add US5 category isolation only after the equity baseline is frozen.
5. Complete scale and cross-cutting validation.

## Notes

- `[P]` means the task touches different files and has no dependency on another incomplete task in
  its phase.
- `[US1]` through `[US5]` map tasks to the prioritized user stories in `spec.md`.
- Commit after each task or coherent task group; do not mix unrelated refactors into a task.
- Stop at every checkpoint and preserve the smallest executable increment.