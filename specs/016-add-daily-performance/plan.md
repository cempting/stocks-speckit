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

Following the user's implementation decision, extend `representation_performance` to return
`1d`, `1w`, `1m`, `3m`, `6m`, and `12m` by default. Each entry is a
`RepresentationPeriodResult(value, reason)`, so one unavailable horizon cannot suppress another.
Keep the exact-endpoint scalar daily calculator and supply official session dates from the
application calendar boundary. The shared absolute calculator accepts one existing period when
requested; its default five-period dictionary, arithmetic, and error behavior remain unchanged.
Migrate callers explicitly: entity tapes use independent availability, while ranking/snapshot
callers still require and project only the five legacy periods.

The 2026-11-06 clarification anchors the daily interval to the requested as-of date, not the
observed table date. Resolve the latest completed official session and its exact predecessor
independently of price availability. Missing required closes yield `Unavailable`; an older
observed date remains disclosure context and never selects an older daily interval.

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

**Constraints**: Exact adjusted completed-session endpoints anchored to the requested date;
no observed-date fallback or dropped missing-session substitution; no absolute fallback in
relative mode; no change to existing five-period calculations, ranking, chart dimensions,
selection keys, or thumbnail options.

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
| VI. High Cohesion, Low Coupling | PASS | PASS | One six-period representation API with explicit availability; legacy callers adapt to their five-period contract. |
| Native Streamlit architecture | PASS | PASS | Keep the approved four root tabs and current native buttons/state. |
| Source, freshness, cache and state | PASS | PASS | Reuse existing histories/cache/state; requested date determines daily sessions, while observed dates remain explicit disclosures. |
| Observable failure | PASS | PASS | Expected insufficiency has a daily-specific reason in existing context/tooltips, not a fabricated value. |
| Test-first and type safety | PASS | PASS | Add failing endpoint/basket/renderer/workflow regressions before code; run focused tests and quality gates. |
| Migration/versioning | PASS | PASS | Representation API return values change to typed value/reason entries; repository callers are migrated. No persisted or snapshot schema changes. |

Both gates pass against constitution 4.0.1; no exception is required. Reconcile the existing
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
└── tasks.md             # Regenerated backlog aligned with the selected-date clarification
```

### Source Code (repository root)

```text
packages/market-data/src/market_data/domain/
├── sector_performance.py       # New exact-endpoint scalar daily helper
└── industry_representations.py # Unified six-period ETF/basket results with reasons
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
├── integration/test_build_snapshot.py # Existing completed-session boundary regressions
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

1. Resolve one explicit consecutive-session pair per table context from `requested_as_of` and
   a single timezone-aware evaluation clock. Reuse
   `latest_completed_us_session(requested_as_of, now=...)` for `end_session`, then the typed
   calendar's `previous_session` for `start_session`. Keep existing future-date/clock validation.
   Price availability and `observed_as_of` must not select or move either daily endpoint.
   Supply exact dates to pure domain arithmetic; never infer a daily interval by dropping
   missing observations. Missing either required close produces `Unavailable`.
2. Add `calculate_daily_return(closes, *, start_session, end_session) -> float` alongside the
   default five-period functions. Return a fractional return. Require unique dates, the two
   exact endpoints, finite strictly positive prices, and ordered distinct session dates.
   Raise `InsufficientHistoryError` for missing/invalid evidence; malformed date/index inputs
   raise contextual `ValueError`. Do not inspect unrelated older price values for daily validity.
3. Extend `representation_performance` to six default periods with a typed value and unavailable
   reason per entry. Use `as_of=requested_as_of` for daily effectivity and
   `performance_as_of=observed_as_of` for the existing longer-period cutoff/effectivity.
   Receive explicit daily session dates, use the scalar daily calculator, and preserve exact
   approved weights. Missing dates make only `1d` unavailable; do not infer sessions from prices.
   Longer periods use the existing calendar offsets independently, retaining full basket
   alignment and approved constituent checks. Never drop or renormalize constituents.
4. In `_build_entity_tape`, call the representation API once per reviewed row for all six periods
   (retain the existing symbol-only helper path), then subtract an exact matching
   benchmark daily return only in relative mode. Absolute daily calculation must work without
   benchmark prices. Display each available longer period independently and multiply the daily
   fractional result by 100 once when inserting `1d` before `1 week`. Use loaded histories
   directly for daily endpoint lookup, not chart/legacy series cropped at `observed_as_of`.
   Preserve the existing observed-date cutoff for charts and all five longer-period calculations.
5. Convert expected domain evidence errors to explicit per-period reasons in the representation
   API; catch invalid representations and benchmark errors at the workflow boundary. Preserve any daily
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
   Include a fixed requested-date pair with an older valid observed pair: the daily cell must
   remain unavailable when a required requested-date close is missing, even though an older
   daily return could be computed. Assert the same pair for entity, benchmark, and every basket
   constituent while preserving valid longer-period values and freshness disclosures.
8. Validate via [quickstart.md](quickstart.md), including a browser walkthrough. This feature
   does not change `_calculate_discovery`'s cached result schema or remote request parameters;
   do not invalidate market-data caches merely to add an uncached tape projection.

Outputs: [data-model.md](data-model.md), [UI contract](contracts/daily-performance-ui.md),
and [quickstart.md](quickstart.md). [tasks.md](tasks.md) was regenerated on 2026-11-06 after this
design reconciliation: its endpoint instructions and quoted model constraints now follow the
selected-date clarification. The six-period API supersedes the original separate representation
daily helper design. Automated implementation evidence is recorded in [quickstart.md](quickstart.md);
browser acceptance and final feature completion remain pending.

## Python API migration

`representation_performance(...)[period]` is now a `RepresentationPeriodResult`, not a float.
Read `.value`, check for `None`, and expose `.reason` on failure. The ordered dictionary always
contains six keys for valid representation inputs. Inactive/invalid representations remain
explicit errors when neither requested nor longer-period context permits them.
Pass `start_session` and `end_session` for a usable daily result; domain code does not resolve
clocks/calendars. Omitted endpoints produce an explicit unavailable daily entry.

This is a backward-incompatible Python return-shape change, approved by the user. All repository
callers are migrated; external consumers must adapt before adopting it. No release version,
stored catalog, persisted schema, or cached snapshot format changes are made by this implementation.
