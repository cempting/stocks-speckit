# Implementation Plan: Add Daily Performance

**Branch**: `main` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/016-add-daily-performance/spec.md`

**Feature identifier**: `016-add-daily-performance`. Setup reports this identifier in its
`BRANCH` field; `git branch --show-current` confirms the actual working branch is `main`.
No branch hook is configured and this plan does not create a branch.

## Summary

Add a literal `1d` performance column immediately before `1 week` in both sector and industry
tapes. Reuse existing adjusted history, approved ETF/basket representations, performance-basis
selection, and the shared percentage/color renderer. Do not add requests or controls.

Calculate daily returns independently of the existing five-period calculators. Those calculators
require long history and return all periods together; extending them would risk changing existing
callers and turning an isolated daily-data gap into missing longer-period values. Add narrowly
scoped daily helpers to the existing domain modules, supplied with exact completed-session dates
by the application calendar boundary. Daily failure remains visible without mutating legacy values.

## Technical Context

**Language/Version**: Python 3.12 (`>=3.12,<3.13`).

**Primary Dependencies**: Existing Streamlit, pandas, exchange-calendars, yfinance, and the
workspace `market-data` package. No dependency or lockfile change.

**Storage**: No schema, catalog, or persisted-data change. Reuse in-memory/cached adjusted daily
history and existing namespaced session-local controls.

**Testing**: pytest domain tests, Streamlit AppTest workflow/renderer tests, Ruff, and strict
Pyright. Browser walkthroughs verify readable light/dark cells and narrow-width accessibility.

**Target Platform**: Existing local/hosted Streamlit application.

**Project Type**: Python web application with a workspace market-data domain package.

**Performance Goals**: Zero additional provider/catalog requests for the daily column.
Ordinary control reruns reuse existing histories. Daily arithmetic is limited to two endpoint
lookups per representation constituent and the matching benchmark interval.

**Constraints**: Exact adjusted completed-session endpoints; no dropped missing-session
substitution; no absolute fallback in relative mode; no change to existing five-period
calculations, ranking, chart dimensions, selection keys, or thumbnail options.

**Scale/Scope**: Sector performance and Industry momentum wherever the shared entity tape is
rendered. Nine visible columns per entity tape: two charts, one entity button, six performance
periods. Stock tapes remain at five columns. No new tabs, markets, providers, or scoring work.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or constraint | Before research | After design | Evidence |
|---|---|---|---|
| I. Keep It Simple | PASS | PASS | Add scalar daily helpers to existing domain modules and reuse the shared tape renderer. |
| II. Lean Delivery | PASS | PASS | One column in the two requested tables; no stock or navigation redesign. |
| III. YAGNI | PASS | PASS | No configurable period engine, new persistence, ranking selector, or daily chart option. |
| IV. Avoid Waste | PASS | PASS | Reuse already-loaded histories; no provider or catalog requests added. |
| V. Separation of Concerns | PASS | PASS | Application resolves sessions; domain validates/calculates; UI formats and exposes reasons. |
| VI. High Cohesion, Low Coupling | PASS | PASS | Reuse explicit representation contracts; leave legacy five-period dictionaries and callers intact. |
| Native Streamlit architecture | PASS | PASS | Keep the approved four root tabs and current native buttons/state. |
| Source, freshness, cache and state | PASS | PASS | Existing yfinance path, dates, cache keys, and session-local selections remain authoritative. |
| Observable failure | PASS | PASS | Expected insufficiency has a daily-specific reason in existing context/tooltips, not a fabricated value. |
| Test-first and type safety | PASS | PASS | Add failing endpoint/basket/renderer/workflow regressions before code; run focused tests and quality gates. |
| Migration/versioning | PASS | PASS | Additive UI amendment; no public persisted schema migration or change to legacy return types. |

Both gates pass against constitution 4.0.0; no exception is required. Reconcile the existing
five-period presentation statements with this feature, while preserving their historical
implementation evidence. Planning does not claim that six-period rendering is implemented.

## Project Structure

### Documentation (this feature)

```text
specs/016-add-daily-performance/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
├── contracts/daily-performance-ui.md
└── tasks.md             # Future /speckit-tasks output; not created by planning
```

### Source Code (repository root)

```text
packages/market-data/src/market_data/domain/
├── sector_performance.py       # New exact-endpoint scalar daily helper
└── industry_representations.py # Approved ETF/basket daily return
src/market_leadership/
├── application/market_sessions.py    # Resolve explicit daily session interval
├── application/exchange_calendar.py  # Existing typed calendar boundary
└── ui/
    ├── workflows/discovery_page.py   # Build daily cells and expose daily reasons
    ├── performance_table.py          # Recognize 1d as a styled performance column
    └── components/progressive_tape.py # Reuse percentage rendering and tooltips
tests/
├── unit/domain/test_sector_performance.py
├── unit/test_industry_representations.py
├── unit/ui/test_performance_table.py
├── unit/ui/test_progressive_tape.py
├── app/test_sector_stock_explorer.py
├── app/test_discovery.py
└── integration/test_industry_representations.py
```

**Structure Decision**: Extend existing modules and test files. Domain modules reside in
`packages/market-data`, not the stale paths formerly under the app's domain directory.
No new service or generic period framework is needed.

## Phase 0: Research Decisions

See [research.md](research.md). Repository inspection resolved session, return-unit,
representation, formatting, and regression questions. There are no unresolved clarifications
or external technology choices requiring separate research agents.

## Phase 1: Design and Contracts

1. Resolve an explicit consecutive-session pair using the existing calendar boundary and
   completed-session cutoff. Use the existing observed table date when stale evidence limits
   the table, bounded by the requested date and latest actually completed session. Supply dates
   to pure domain arithmetic; never infer a daily interval by dropping missing observations.
2. Add `calculate_daily_return(closes, *, start_session, end_session) -> float` alongside the
   unchanged five-period functions. Return a fractional return. Require unique dates, the two
   exact endpoints, finite strictly positive prices, and ordered distinct session dates.
   Raise `InsufficientHistoryError` for missing/invalid evidence; malformed date/index inputs
   raise contextual `ValueError`. Do not inspect unrelated older price values for daily validity.
3. Add `representation_daily_return(...) -> float` in the existing representation module,
   receiving the same explicit dates. Validate existing approval/effectivity rules, calculate
   ETF daily return directly, or sum approved weighted constituent daily returns. Every basket
   constituent must have both exact endpoints; never drop a constituent or renormalize weights.
4. In `_build_entity_tape`, independently calculate daily evidence for the approved
   representation (or existing symbol-only helper path), then subtract an exact matching
   benchmark daily return only in relative mode. Absolute daily calculation must work without
   benchmark prices. Preserve the existing five-period code paths and multiply the daily
   fractional result by 100 once when inserting `1d` before `1 week`.
5. Catch only expected domain evidence errors at the workflow boundary. Preserve any daily
   reason in the existing entity tooltip/context with a `1d:` prefix, without replacing
   longer-period values, existing status meaning, representation identity, or freshness warnings.
6. Prepend `1d` to `PERFORMANCE_COLUMNS` so the existing renderer supplies right-aligned
   percentages, per-period/sign palettes, and uncolored `Unavailable`. Preserve internal
   Ticker/ETF/Node ID fields and the five-column stock projection.
7. Add test-first regressions for exact daily math, stale/as-of and incomplete-session
   exclusion, missing endpoints, matching benchmark intervals, approved baskets, independent
   daily/legacy availability, exact headings, both themes, and unchanged interactions.
   Existing renderer tests hard-code 20 cells/five cells per row: update those assertions to
   24/six and add an explicit literal-heading assertion rather than relying only on the constant.
8. Validate via [quickstart.md](quickstart.md), including a browser walkthrough. This feature
   does not change `_calculate_discovery`'s cached result schema or remote request parameters;
   do not invalidate market-data caches merely to add an uncached tape projection.

Outputs: [data-model.md](data-model.md), [UI contract](contracts/daily-performance-ui.md),
and [quickstart.md](quickstart.md). Task generation and implementation remain subsequent phases.
