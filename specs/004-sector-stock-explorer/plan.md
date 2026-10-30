# Implementation Plan: Sector-to-Stock Explorer

**Branch**: `004-sector-stock-explorer` | **Date**: 2026-10-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-sector-stock-explorer/spec.md`

## Summary

Extend the existing live Discovery workflow into a progressive US market explorer: show sector
performance until a sector is selected, then its industries, then all available member stocks.
Each tape starts with an entity-specific chart thumbnail. Selecting a stock opens its detail view
with its own price/volume history, 50- and 150-session moving averages, and the Quality, Growth,
and Cash Flow peer scores defined by the existing [fundamental scoring contract](../001-market-leadership-screener/contracts/fundamental-scoring.md).

Keep the current two-tab Streamlit shell and single yfinance runtime source. Reuse the reviewed
membership catalog, market-data caches, financial bundle reader, and stable session-state
patterns. Add the peer-score calculation required by the accepted score choice, because the
current application has the raw quarterly scorecard but not the contract's three peer scores.
No scores are inferred when their inputs or evidence are insufficient.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`.

**Primary Dependencies**: Existing Streamlit, pandas, NumPy, Altair, and yfinance dependencies;
no new runtime dependency is planned.

**Storage**: Existing response cache and `st.cache_data` for successful, parameter-keyed market
and financial evidence; namespaced `st.session_state` for current stable-ID selections. No new
persistent database or user-specific shared cache.

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

**Constraints**: Use only live yfinance market data. Request stock history only for the selected
industry's active catalog members. Financial peer scores require the complete eligible industry
cohort, use the existing 001 formulas and sufficiency rules, and are loaded only after explicit
user intent. Missing, stale, unauthorized, or incomplete evidence is not substituted or presented
as success. Live membership/financial display remains subject to reviewed catalog coverage and
rights.

**Scale/Scope**: US sectors, their available industries, and the active member stocks of one
selected industry at a time; a detailed view for one selected stock. No new markets, alerts,
recommendations, trading, portfolio workflow, or aggregate score.

## Constitution Check

*GATE: Evaluated before Phase 0 research and again after Phase 1 design.*

| Principle or constraint | Pre-design | Post-design |
|-------------------------|------------|-------------|
| I. Keep It Simple | PASS: extend the existing live Discovery and selection patterns | PASS: no service, route framework, or dependency added |
| II. Lean Delivery | PASS: scope is limited to the accepted sector-to-stock journey | PASS: reuse existing market, membership, cache, and financial boundaries |
| III. YAGNI | PASS: later “further things to come” are explicitly excluded | PASS: no extension points or speculative score aggregation |
| IV. Avoid Waste | PASS: active-view-only data and current caches are available | PASS: no hidden financial loads; stock history is limited to selected industry |
| V. Separation of Concerns | PASS: existing domain, provider, state, and render layers are suitable | PASS: calculations, data retrieval, state reconciliation, and rendering remain distinct |
| VI. High Cohesion, Low Coupling | PASS: current stable identifiers and existing typed records are reusable | PASS: add only the missing peer-score calculation boundary and focused UI components |
| Streamlit and live-data constraints | PASS: current entrypoint already uses Streamlit and yfinance | PASS: preserve the two-tab shell, one provider, scoped cache keys, reviewed membership, and explicit errors |
| Test and evidence gates | PASS: project provides pytest, AppTest, Ruff, and Pyright | PASS: each workflow stage has controlled test evidence; live network is not required |

**Gate result: PASS.** No exception is requested. The current score implementation is not assumed
to satisfy the feature: the peer-percentile contract is the authoritative scoring rule, and the
calculation work is an explicit prerequisite in the implementation workflow.

## Project Structure

### Documentation (this feature)

```text
specs/004-sector-stock-explorer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── progressive-discovery.md
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
│   ├── stock_membership.py
│   └── yfinance_fundamentals.py
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
│   └── ui/
│       └── test_progressive_tape.py
├── integration/
│   └── test_stock_evidence.py
└── app/
    └── test_sector_stock_explorer.py
```

**Structure Decision**: Keep the current application entrypoint and two root tabs. The progressive
sector/industry/stock tapes and selected-stock detail view belong to the Discovery journey; the
existing Industry Deep-Dive tab remains available and reuses the same reviewed membership
contracts. Use existing data and validation modules where possible; add only the missing peer
score calculation and cohesive renderers. No third top-level grading tab or separate routing
system is introduced.

## Phase 0 - Research Resolution

See [research.md](./research.md). Resolved decisions:

1. Keep the existing two-tab live-only shell; all progressive selection occurs within Discovery,
   with stock detail replacing that view until the user returns.
2. Use stable sector, industry, and instrument IDs for selection and detail handoff. Symbols and
   names remain display attributes.
3. Use each entity's own cached price history for its chart; request member-stock histories only
   after an industry is selected.
4. Reuse the reviewed dated membership catalog and its live-access validation. An invalid or
   unavailable catalog blocks member rows rather than producing a misleading empty industry.
5. Use the existing 001 peer-percentile definitions for Quality, Growth, and Cash Flow. Add the
   missing pure calculation; do not treat the eight raw metrics in the current fundamental matrix
   as the three requested block scores.
6. Score calculations require the whole eligible industry peer set, at least five valid peers per
   metric, and dated/cutoff-valid evidence. Unknown or incomplete evidence is insufficient.
7. Fetch financial evidence only after explicit user intent, reuse the existing cache, and disclose
   partial failures; ordinary reruns and table navigation never cause a score-fetch storm.
8. No unresolved technical decisions remain. yfinance's missing point-in-time evidence remains an
   explicit insufficiency, not a basis for relaxing the existing scoring contract.

## Phase 1 - Design and Contracts

### Data and interaction flow

1. The Discovery view loads the existing live sector and industry representation observations.
   With no selected sector, it renders only the sector tape; selecting one valid sector ID changes
   the visible tape to that sector's industries.
2. Selecting one valid industry ID clears any invalid stock/detail state, validates the matching
   current membership context, and loads daily price history for its active members in a scoped
   batch. The stock tape presents all catalog members, including rows with explicit unavailable
   history or financial evidence.
3. A tape row carries its own chart series and stable identity. Rendering never borrows a parent,
   sibling, or previous selection's chart. Unsupported histories retain the row and display an
   insufficiency state.
4. An explicit score-load action retrieves eligible peer evidence for the selected industry,
   reuses the existing per-symbol financial cache, and computes block percentiles over the full
   cohort before display filtering. The UI distinguishes not loaded, sufficient, insufficient,
   and failed evidence. Errors are visible; failed loads are not cached as successful scores.
5. Selecting a stock ID opens the detail view for that exact identity. Its chart uses its own
   completed daily observations and independently indicates whether price, volume, 50-session,
   and 150-session evidence is available. The scorecard uses the same industry peer result and
   provenance as the tape.
6. Returning from detail clears only the stock-detail selection. Valid sector, industry, filters,
   and available evidence remain. Changing a parent clears only invalid descendants and their
   selection-dependent display state.
7. The Industry Deep-Dive tab keeps its current reviewed-catalog behavior. Any shared membership
   helper remains responsible for catalog validation; user-specific selections stay in session
   state and are never part of cached source results.

### Implementation workflow and dependencies

Formal, independently testable task IDs and prerequisite edges are generated in Phase 2 by
`/speckit-tasks`. The design requires the following order; independent work may be split into
small tests and implementation tasks within each stage:

| Stage | Deliverable and smallest useful validation | Depends on |
|------:|---------------------------------------------|------------|
| 1. Stable selection state | Pure parent/child transition tests prove valid IDs persist and stale industry/stock IDs clear | None |
| 2. Peer-score domain | Formula, tied percentile, minimum-peer, missing-data, and cutoff tests match contract 001 | None |
| 3. Sector and industry tapes | AppTest proves initial sector-only view and sector-to-industry transition; row tests verify own chart series | 1 |
| 4. Member-stock tape | Catalog tests and AppTest prove all active members appear, stock fields are bound to stable IDs, and missing evidence is explicit | 1, 3 |
| 5. Scoped market history | Provider/cache integration tests prove only active selected-industry symbols are requested and each row gets its own history | 4 |
| 6. Explicit peer-score loading | Integration and AppTest prove complete peer cohort, cache reuse, no eager calls, and visible partial failures | 2, 4 |
| 7. Stock detail | AppTest proves row-to-detail identity and return context; chart tests prove price, volume, and both moving-average states | 4, 5, 6 |
| 8. End-to-end and regression | Complete hierarchy, empty/error/freshness cases, two-tab shell, focused quality gates, then full non-live suite | 3-7 |

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
- Existing live provider, catalog, date/freshness, and source-error behavior remains authoritative.
  The feature does not add another provider, fallback data path, or runtime fixture mode.

Use the [progressive discovery contract](./contracts/progressive-discovery.md) for precise
selection, data, and error-state expectations and the [quickstart](./quickstart.md) for runnable
validation.

## Complexity Tracking

No constitution violations or exceptions are required. The peer-score calculation is a necessary
implementation of the chosen existing contract, not a new aggregate or future-facing abstraction.
