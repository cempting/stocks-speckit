# Phase 0 Research: Market Leadership Screener

## Runtime and Dependency Management

**Decision**: Use Python 3.12, a `pyproject.toml`, `uv`, and a committed `uv.lock`. Constrain direct
dependencies to compatible release series and let the lockfile pin the complete environment.

**Rationale**: Streamlit supports Python 3.11 through 3.15. Python 3.12 is modern while remaining a
conservative baseline for the numeric and Arrow ecosystem. `uv run` verifies that project metadata,
the lockfile, and the environment agree before commands run; its cross-platform lockfile makes local
and CI installs reproducible.

**Alternatives considered**: Plain `venv` plus `requirements.txt` lacks a first-class project model
and transitive lock. Poetry duplicates capabilities without a demonstrated project need. Python 3.15
would use the newest supported runtime but provides no feature-specific benefit.

## Application Boundaries

**Decision**: Use four layers in one package: pure domain policy, application use cases, provider
adapters, and Streamlit UI. Dependencies point inward; only `ui` imports Streamlit.

**Rationale**: Calculations and eligibility rules need deterministic unit tests and future reuse by
snapshot builds. Streamlit reruns the page script on interaction, so placing business policy in page
functions would couple correctness to UI state. A single package keeps deployment simple.

**Alternatives considered**: A monolithic Streamlit script is quick initially but makes calculations,
I/O, and session behavior inseparable. A backend API and separate frontend add deployment and
contract overhead without concurrent clients or an external API requirement.

## Swappable Workflows

**Decision**: Define a small immutable `WorkflowSpec` containing title, icon, URL path, default flag,
and a zero-argument render callable. `bootstrap.py` constructs dependencies, closes them over page
functions, and passes one explicit ordered registry to `st.Page` and one `st.navigation` call.

**Rationale**: Streamlit supports function-based pages. A workflow can therefore be replaced or
removed at one composition point while retaining focused modules and direct testability with
`AppTest`. Explicit registration makes enabled behavior reviewable.

**Alternatives considered**: Filesystem discovery, Python entry points, and a general plugin manager
are rejected until third-party runtime plugins are required. Streamlit's implicit `pages/` directory
offers less control over dependency construction and navigation policy.

## Market Data and Storage

**Decision**: The completed release consumes canonical, versioned snapshot directories made of Parquet
tables plus a JSON manifest. A `MarketDataProvider` protocol reads source data for the offline build;
a `SnapshotRepository` protocol atomically publishes and loads calculated snapshots. Configured
Phase 2 daily price/volume runtime adapters share the same contract: Massive REST is preferred when `MASSIVE_API_KEY` is
available, while `yfinance` provides an explicitly selected no-key adapter for development and
personal-use deployments. The deployed Streamlit application uses these direct HTTP/Python adapters
and does not depend on MCP services. Local Parquet remains the application's immutable input
boundary, with a fixture adapter for acceptance tests.

**Rationale**: A canonical file contract prevents vendor assumptions while preserving source
attribution. Massive provides an authenticated, documented API for US daily history; production
display rights and additional datasets require separate verification. `yfinance` covers the benchmark and sector ETF price history needed for
development without credentials, but its unofficial upstream interface, personal-use terms, and
lack of an availability contract make it an explicit alternative rather than a silent production
fallback. Parquet is compact, columnar, typed, and supported by pandas/PyArrow. Immutable dated
snapshots make weekly results reproducible and let the UI remain read-only.

**Alternatives considered**: Direct vendor calls in Streamlit would make reruns slow and tests
nondeterministic. SQLite is viable but adds schema migration and concurrency concerns before the app
needs writes or relational queries. CSV weakens types and increases load cost. Pickle is unsafe for
untrusted data and less portable. Automatically switching from Massive to `yfinance` after an
upstream error is rejected because it can change data semantics without an explicit operator choice.

## Staging and Deferred Inputs

**Staging decision**: Phase 2's immutable daily input snapshots and live US discovery are not
weekly calculated scoreboards. The US/JP/GB acceptance fixture establishes test-only multi-market
selection with distinct local currencies, benchmarks and regimes; it is not a live-data entitlement.
Before US1 calculations, define effective-dated market/classification/representation inputs and
weekly snapshot schema, then test them with controlled fixtures. Publish only completed local-market
weeks; never imply a shared date across markets. Release default switches to the SECTOR scoreboard
only after its acceptance tests pass. Alternative rejected: calling the Phase 2 input snapshot a
weekly ranking or treating cross-market fixtures as live providers.

**Evidence decision**: Implement dated classifications and representations in US2; constituent
membership and weights in US3; provenance across all stories; observed net flows and assets
get a separate US4 contract. All are deferred from Phase 2 and require verified source rights,
availability dates and coverage before a live adapter is enabled. Breadth, concentration and
price/volume pressure are supporting signals; observed flows never affect leadership scores. No
live source/license is assumed. Alternative rejected: inferring flows from price, volume or assets,
or using present-day memberships for historical calculations.

**Release gates, not assumed facts**: A product owner must approve eligible live market and
non-price sources with display/derived-data rights before enabling those adapters. US3 must
document and approve the numerical "material" cap-versus-equal-weight disagreement policy before
its acceptance test and implementation; the spec establishes the label but not its threshold.

## Domain Representation and Validation

**Decision**: Use frozen, slotted dataclasses and enums for domain results and request records;
pandas/NumPy for vectorized time-series work; and explicit PyArrow schemas at the adapter boundary.
All dates and clocks enter as values. Stable reason codes accompany insufficient and rejected states.

**Rationale**: Immutable records prevent cached shared data from being mutated accidentally. Arrow
schemas validate tabular types without another dataframe-validation dependency. Reason codes make
fail-closed outcomes testable and renderable without parsing messages.

**Alternatives considered**: Pydantic for every market row would add conversion overhead and a
second tabular type system. Untyped dictionaries hide missing fields. An ORM has no database to map.

## Caching and State

**Decision**: Cache manifest and snapshot loads with `st.cache_data`, keyed by snapshot ID and
manifest checksum. Cache only immutable/read-only values. Keep active filters, search, sort, and
drill-down context in `st.session_state`; pass a typed query to the browse use case on every rerun.

**Rationale**: Streamlit data caches are shared across sessions while session state is per user.
Separating them prevents one user's filters from leaking into another user's view and avoids repeated
disk reads. A new immutable snapshot ID naturally invalidates cached results.

**Alternatives considered**: Caching use-case objects with `st.cache_resource` risks hidden mutable
state and is unnecessary for local files. Encoding filters in cached functions increases cache
cardinality. Global module state is unsafe across sessions.

## Testing and Quality Gates

**Decision**: Use pytest at four levels: pure rule tests, adapter contract tests, use-case integration
tests, and Streamlit `AppTest` workflow tests. Controlled fixtures assert exact values and boundary
cases. CI runs Ruff format/check, Pyright, the full pytest suite, and coverage with branch reporting.

**Rationale**: The constitution requires tests to demonstrate behavior before implementation.
Formula and gate errors are cheapest to isolate below the UI; `AppTest` then protects widget and
navigation behavior without browser flakiness. A frozen baseline snapshot protects equity behavior
when later asset modules are added.

**Alternatives considered**: Screenshot-only tests cannot prove calculations. End-to-end browser
tests are reserved for gaps `AppTest` cannot cover. A broad coverage number alone is not acceptance
evidence, so requirement fixtures remain explicit.

## Failures and Observability

**Decision**: Reject invalid manifests and table schemas before calculation. Return typed
insufficiency/rejection reasons for expected data gaps; raise contextual exceptions for corrupt or
inconsistent snapshots. The UI shows the active snapshot ID, as-of date, source availability, and a
concise recovery message without exposing paths or credentials.

**Rationale**: Missing evidence is valid domain state, while malformed data is an operational fault.
Keeping those paths separate prevents silent partial rankings and gives users actionable context.

**Alternatives considered**: Logging and continuing can publish misleading ranks. Treating every
missing observation as a fatal error would violate the requirement to preserve valid local results
when global data is absent.

## Sources Consulted

- Streamlit documentation: installation support, multipage navigation, application testing, and
  caching behavior (accessed 2026-10-26).
- uv project documentation: `pyproject.toml`, project environments, lockfiles, and `uv run`
  synchronization (accessed 2026-10-26).
- pandas I/O documentation: Parquet round trips, column selection, and PyArrow support (accessed
  2026-10-26).
- Repository authority: `specs/decisions.md`, A01, A02, A04, A05, and the feature specification.