# Implementation Plan: Sector-to-Stock Explorer

**Branch**: `004-sector-stock-explorer` | **Date**: 2026-10-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-sector-stock-explorer/spec.md`

## Summary

Extend the existing live Discovery workflow into a region-aware explorer backed by a persistent
market database. Start with one US region that combines securities across exchange listings,
while keeping exchange listings and classification systems distinct in the data model. Provide
CLI tooling to initialize the database, import reviewed local files, validate membership, and
refresh through the application's single live provider only after its coverage and display rights
are approved.

Discovery queries sector, industry, stock, and listing membership from the database instead of
requiring `STOCK_MEMBERSHIP_CATALOG` or relying on hard-coded membership configuration. The
existing two-tab Streamlit shell, yfinance price-history flow, market-data caches, financial
bundle reader, and stable session-state patterns remain. Each progressive tape has a price-chart
thumbnail with its 50-session average and an adjacent volume-chart thumbnail whose bars show
price direction. The selected-stock detail retains its price/volume chart, 50/150-session
averages, and peer scores. Unavailable or unresolved records remain explicit rather than
fabricated.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`.

**Primary Dependencies**: Existing Streamlit, pandas, NumPy, Altair, and yfinance dependencies;
Python's standard-library `sqlite3` provides persistence, with no new runtime dependency planned.

**Storage**: A local SQLite database under ignored `.data/` stores regions, classification
systems, sectors, industries, stable stock identities, exchange listings, memberships, and source
provenance. Existing response cache and `st.cache_data` remain for successful, parameter-keyed
market and financial evidence; namespaced `st.session_state` holds current stable-ID selections.
No user selection is stored in shared cached results.

**Testing**: pytest, Streamlit AppTest, Ruff, and strict Pyright; deterministic injected providers,
clocks, and membership/fundamental fixtures. No network is needed for required tests.

**Target Platform**: Browser-hosted Streamlit application, using the existing wide-layout
two-tab entrypoint.

**Project Type**: Single Python Streamlit application with existing domain, application,
infrastructure, and UI boundaries.

**Performance Goals**: With previously cached evidence, sorting, filtering, selecting, and
opening a row for up to 100 displayed entities should complete within two seconds in 95% of
controlled runs. Remote loads show progress and explicit partial/failure states; no latency
guarantee is made for yfinance.

**Constraints**: Use only the application's single selected live provider for all runtime
market-data requests; retain yfinance unless a reviewed provider decision replaces it. Request
stock history only for verified listings of stocks in the selected region/industry. Financial
peer scores require the complete eligible industry cohort, use the existing 001 formulas and
sufficiency rules, and are loaded only after explicit user intent. Reviewed local files are
authoritative for region, sector, industry, stock identity, and membership; live-source
discrepancies are reported without overwriting them. Do not enable a live database refresh unless
the selected provider supplies the needed coverage and passes terms/display-rights review.
Missing, stale, unauthorized, conflicting, or incomplete evidence is not substituted or presented
as success.

**Scale/Scope**: One initially populated US region combining eligible exchange listings, its
available sectors and industries, and member stocks of one selected industry at a time; a
detailed view for one selected stock. The schema supports additional regions and non-GICS
classifications, but no non-US data, alerts, recommendations, trading, portfolio workflow, or
aggregate score is introduced.

## Constitution Check

*GATE: Evaluated before Phase 0 research and again after Phase 1 design.*

| Principle or constraint | Pre-design | Post-design |
|-------------------------|------------|-------------|
| I. Keep It Simple | PASS: extend existing live Discovery and use stdlib SQLite | PASS: one local database and one CLI, with no service or new dependency |
| II. Lean Delivery | PASS: scope is limited to database-backed US region discovery | PASS: reuse existing market, cache, and financial boundaries |
| III. YAGNI | PASS: later “further things to come” are explicitly excluded | PASS: no extension points or speculative score aggregation |
| IV. Avoid Waste | PASS: active-view-only data and current caches are available | PASS: no hidden financial loads; stock history is limited to selected region/industry |
| V. Separation of Concerns | PASS: existing domain, provider, state, and render layers are suitable | PASS: DB access, ingestion, market retrieval, state, and rendering remain distinct |
| VI. High Cohesion, Low Coupling | PASS: stable identities and typed membership records are reusable | PASS: focused database repository, importer, CLI, and UI query boundaries |
| Streamlit and live-data constraints | PASS: current entrypoint already uses Streamlit and yfinance | PASS: preserve the two-tab shell, one price provider, scoped cache keys, reviewed local membership, and explicit errors |
| Test and evidence gates | PASS: project provides pytest, AppTest, Ruff, and Pyright | PASS: each workflow stage has controlled test evidence; live network is not required |

**Gate result: PASS.** No exception is requested. SQLite is the smallest persistent store already
available in Python. A named live membership source remains a release prerequisite, not a license
to guess at a provider or bypass the coverage and rights review. The peer-percentile contract is
authoritative for score calculation.

## Project Structure

### Documentation (this feature)

```text
specs/004-sector-stock-explorer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── progressive-discovery.md
│   └── universe-management-cli.md
├── checklists/
│   └── requirements.md
└── tasks.md              # generated by /speckit-tasks, not by this command
```

### Source Code (repository root)

```text
streamlit_app.py
src/market_leadership/
├── app.py
├── application/
│   └── discover_sectors.py
├── domain/
│   ├── industry_momentum.py
│   ├── sector_performance.py
│   ├── fundamentals.py
│   └── peer_scores.py                 # add only the missing 001 peer-score calculation
├── infrastructure/
│   ├── yfinance_provider.py
│   ├── region_database.py             # SQLite schema and focused query repository
│   ├── universe_import.py             # reviewed CSV/JSON ingestion and conflict report
│   ├── stock_membership.py            # adapt membership reads to database records
│   └── yfinance_fundamentals.py
├── universe_admin.py                  # init, validate, import, and approved refresh CLI
└── ui/
    ├── cache.py
    ├── dataframe.py
    ├── components/
    │   ├── progressive_tape.py       # focused row and chart-preview rendering
    │   └── stock_detail.py            # selected-stock chart and scorecard view
    └── workflows/
        ├── discovery_page.py
        └── industry_deep_dive.py

tests/
├── unit/
│   ├── domain/
│   │   └── test_peer_scores.py
│   ├── infrastructure/
│   │   ├── test_region_database.py
│   │   └── test_universe_import.py
│   └── ui/
│       └── test_progressive_tape.py
├── integration/
│   ├── test_stock_evidence.py
│   └── test_region_discovery.py
└── app/
    └── test_sector_stock_explorer.py
```

**Structure Decision**: Keep the current application entrypoint and two root tabs. Discovery and
Industry Deep-Dive read the same normalized region/industry membership repository. Add one
standard-library SQLite boundary and one CLI for database lifecycle and data imports; keep live
market evidence in the existing provider/cache boundary. The progressive tapes and stock detail
remain inside Discovery; no third top-level tab or separate routing system is introduced.

## Phase 0 - Research Resolution

See [research.md](./research.md). Resolved decisions:

1. Keep the existing two-tab live-only shell; all progressive selection occurs within Discovery,
   with stock detail replacing that view until the user returns.
2. Use stable sector, industry, and instrument IDs for selection and detail handoff. Symbols and
   names remain display attributes.
3. Use each entity's own cached price history for its chart; request member-stock histories only
   after a region and industry are selected.
4. Persist region, classification, sector, industry, stock, listing, and dated membership records
   in SQLite. The app reads memberships from this database instead of requiring a JSON path in
   runtime settings.
5. Import reviewed local CSV/JSON data with provenance. The user's existing sector-rotation
   resources are candidate inputs; source files are validated before publication, and source
   coverage is not claimed complete until reviewed.
6. Reviewed local data is authoritative for region, sector, industry, stock identity, and
   membership. A live refresh must use the application's single selected provider, pass coverage,
   terms, and display-rights review, and report rather than overwrite disagreements.
7. Represent US as one region with securities deduplicated by stable identity and exchange
   listings retained separately. Do not merge securities by display name or assume one ticker
   uniquely identifies a stock.
8. Use the existing 001 peer-percentile definitions for Quality, Growth, and Cash Flow. Add the
   missing pure calculation; do not treat the eight raw metrics in the current fundamental matrix
   as the three requested block scores.
9. Score calculations require the whole eligible industry peer set, at least five valid peers per
   metric, and dated/cutoff-valid evidence. Unknown or incomplete evidence is insufficient.
10. Fetch financial evidence only after explicit user intent, reuse the existing cache, and disclose
   partial failures; ordinary reruns and table navigation never cause a score-fetch storm.
11. Use the local US exchange CSVs as candidate listing inputs; treat S&P/Russell files as
   overlapping index sources rather than independent exchange listings. Unclassified symbols,
   duplicate/conflicting rows, or sources without approved coverage are reported for review.
12. SQLite, import format validation, and query semantics are resolved. Live refresh is
   intentionally a pre-release approval gate for the application's single selected provider;
   the current yfinance price integration is not presumed to have authorized or complete
   classification coverage.

## Phase 1 - Design and Contracts

### Data and interaction flow

1. The Discovery view reads available regions from SQLite, selects the US region initially, and
   offers a region selector when more than one region is populated. It queries sectors and
   industries using stable classification IDs. Existing sector/industry representation symbols
   move from Python constants into database-managed records; incomplete or absent representations
   are shown as unavailable.
2. With no sector selected, Discovery renders only the selected region's sector tape. Selecting a
   sector replaces it with that region/classification's industries. Selecting an industry queries
   every active member exactly once and clears only invalid descendant state.
3. The stock tape presents identified stocks and unresolved placeholders. Only verified listings
   are sent to the application's selected provider (currently yfinance); each stock row retains
   explicit unavailable, insufficient, or placeholder states. Histories are scoped to the
   selected region and industry. Unclassified listings remain visible in coverage reporting and
   are not assigned to a fabricated industry.
4. Each tape row carries its own completed price/volume history and stable identity. Compute the
   50-session simple moving average from 50 completed closes; render it in the price thumbnail
   when sufficient history exists. Put a separate volume-chart thumbnail immediately next to the
   price thumbnail. Color each volume bar green when the close rose from the prior observation,
   red when it fell, and neutral when unchanged or direction is unknown. Identify the colors as
   price-direction indications, not verified buyer/seller activity. Rendering never borrows a
   parent, sibling, or previous selection's chart. Unsupported histories retain the row and
   display an insufficiency state.
5. An explicit score-load action retrieves eligible peer evidence for the selected region and industry,
   reuses the existing per-symbol financial cache, and computes block percentiles over the full
   cohort before display filtering. The UI distinguishes not loaded, sufficient, insufficient,
   and failed evidence. Errors are visible; failed loads are not cached as successful scores.
6. Selecting a stock ID opens the detail view for that exact identity. Its chart uses its own
   completed daily observations and independently indicates whether price, volume, 50-session,
   and 150-session evidence is available. The scorecard uses the same industry peer result and
   provenance as the tape.
7. Returning from detail clears only the stock-detail selection. Valid region, sector, industry, filters,
   and available evidence remain. Changing a parent clears only invalid descendants and their
   selection-dependent display state.
8. The Industry Deep-Dive tab reads the same database membership while retaining its current
   evidence and review gates. User-specific selections stay in session state and never enter
   cached source results.
9. The CLI initializes the schema, validates imports before writing, and commits accepted rows
   atomically. A partial import marks region coverage partial and reports row issues. Live-source
   mismatches are reported; they do not overwrite reviewed local classification or membership.

### Implementation workflow and dependencies

Formal, independently testable task IDs and prerequisite edges are generated in Phase 2 by
`/speckit-tasks`. The design requires the following order; independent work may be split into
small tests and implementation tasks within each stage:

| Stage | Deliverable and smallest useful validation | Depends on |
|------:|---------------------------------------------|------------|
| 1. Region database | Schema constraints, migrations, idempotent queries, and uniqueness tests cover region coverage, classifications, chart representations, stock/listing/membership relationships | None |
| 2. Import and administration CLI | CSV/legacy-JSON parsing, dry-run reports, placeholders, unclassified rows, partial-coverage state, conflict reports, atomic writes, and CLI contract tests | 1 |
| 3. Region-aware selection state | Pure transition tests prove region/parent changes clear invalid descendants and preserve valid detail context | 1 |
| 4. Database-backed hierarchy and proxies | AppTest proves region selection and US region -> sector -> industry views; tests prove no runtime hierarchy depends on hard-coded membership/proxy lists | 1, 3 |
| 5. Progressive tapes and chart thumbnails | AppTest and chart tests prove row-specific price/volume thumbnails, 50-session SMA, adjacent columns, directional bar colors, and unavailable states for all three tape types | 3, 4 |
| 6. Member-stock tape | Repository tests and AppTest prove unique stocks, multiple listings, placeholders, and explicit unavailable evidence | 2, 3, 4, 5 |
| 7. Scoped market history | Provider/cache integration tests prove only verified active listings for the selected region/industry are requested and each row gets its own history | 6 |
| 8. Peer-score domain and loading | Formula tests match contract 001; integration/AppTest prove complete cohort, cache reuse, explicit load, and visible failures | 6 |
| 9. Stock detail | AppTest proves row-to-detail identity and return context; chart tests prove price, volume, and both moving-average states | 7, 8 |
| 10. End-to-end and regression | Import/coverage/conflict cases, full hierarchy, thumbnail placement/direction, two-tab shell, focused quality gates, then full non-live suite | 2, 4-9 |

Every implementation task should pair one observable behavior with focused automated evidence.
Do not combine domain score formulas, remote retrieval, state transitions, and UI rendering into
one task.

### Migration and scope reconciliation

- The current 003 specification keeps exactly two root tabs and excludes a separate Fundamental
  Grading tab. This plan preserves that boundary: the selected-stock scoreboard is part of the
  Discovery detail view, not a restored grading workflow.
- The current 002 implementation provides eight raw quarterly metrics in three groups, but no
  three 0–100 peer block scores. The user chose the three peer-percentile scores; the 001 scoring
  contract is authoritative. The feature adds the missing calculation only, while retaining the
  current raw-metric matrix as a separate existing capability.
- The stock tape must not trigger financial statement retrieval merely because an industry is
  selected. Scores become available only after explicit score-load intent; unavailable and
  insufficient states remain visible. Peer scores are never computed from only the displayed
  page, selected stocks, or technically filtered rows.
- Replace runtime dependence on `STOCK_MEMBERSHIP_CATALOG` with the database repository. Import
  reviewed local files and preserve source, classification, approval, and effective-date
  provenance. A database with no valid import is an explicit setup state, not an empty market.
- Existing live provider, date/freshness, and source-error behavior remains authoritative. Do not
  add a second/fallback provider or runtime fixture mode. Enabling live database refresh requires
  the application's selected provider's US coverage, terms, and rights to pass review first.

Use the [progressive discovery contract](./contracts/progressive-discovery.md) and
[universe-management CLI contract](./contracts/universe-management-cli.md) for selection,
ingestion, and error-state expectations; use the [quickstart](./quickstart.md) for runnable
validation.

## Complexity Tracking

No constitution violations or exceptions are required. SQLite adds only the persistent capability
explicitly requested and avoids a new runtime dependency. The peer-score calculation implements
the chosen existing contract; the unselected live membership source remains gated rather than
being guessed or generalized into a multi-provider system.
