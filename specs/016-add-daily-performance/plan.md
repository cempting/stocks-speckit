# Implementation Plan: Daily Sector and Industry Performance

**Feature**: `016-add-daily-performance` | **Working branch**: `main` | **Date**: 2026-11-06
**Authority**: [spec.md](spec.md), [UI contract](contracts/daily-performance-ui.md), constitution 4.1.0.

## Scope and Stack

Extend existing Python 3.12/Streamlit code using pandas, exchange-calendars, yfinance and the
workspace `market-data` package. No dependency, catalog, persistence, cache-schema, or provider change.
Reuse loaded histories and existing native widgets/state. The six display horizons, responsive
header/rows and full-text details are defined by the UI contract; stock tapes remain five columns.

Daily calculations and 640/1440px layouts have recorded evidence.
The `1 year` caption migration and 390px/touch acceptance remain pending T027-T030.
Historical passes do not establish current phone compliance or the new caption.

## Design

1. **Session boundary**: Resolve one pair per table context from `requested_as_of` and a timezone-aware
   clock: `latest_completed_us_session(..., now=...)`, then the calendar's `previous_session`.
   Retain future-date/clock validation. Never derive endpoints from prices or `observed_as_of`.
2. **Pure arithmetic**: `calculate_daily_return` receives explicit dates and returns a fraction.
   Require distinct ordered sessions, unique observation dates, and exact finite positive endpoint closes.
   Missing/invalid evidence raises `InsufficientHistoryError`; malformed dates/indexes raise contextual
   `ValueError`. Unrelated old prices must not invalidate usable daily endpoints.
3. **Independent periods**: `calculate_performance_periods` prepares calendar history once per series
   and returns six typed value/reason entries. `representation_performance` handles approved ETFs and
   exact baskets with independent availability. Every constituent retains approved membership, weights
   and alignment; no dropping or renormalization. Daily activity uses the requested date; longer activity
   and calendar cutoffs use the existing observed-date context.
4. **Workflow projection**: `_build_entity_tape` calls the shared representation API once per row;
   retain the symbol-only path. Reuse benchmark results across rows. Absolute daily needs no benchmark;
   relative daily requires identical entity/benchmark session dates. Read daily endpoints from loaded
   histories before legacy/chart observed-date cropping. Convert fractions to percentages once;
   use nullable numeric cells plus contextual reasons, never fabricated values or silent fallbacks.
5. **Display mapping**: Use `1 day` for `1d` and `1 year` for `12m` in entity tapes. The latter is
   caption-only: preserve calendar offsets, numerical values, ranking/snapshot keys and legacy-frame
   formatting. Reuse `PERFORMANCE_COLUMNS`, shared palettes, hidden identity metadata and stock projection.
6. **Scoped layout**: Keep native keyed `discovery_header` and entity-tape containers, not page-global CSS.
   Preserve desktop header weights 4:3:3:2 and chart height 84px. At 390/640px, title stays left beside
   date above refresh/theme; retain the narrow theme button's minimum 40px click width and existing keys/callbacks.
   Charts stack above the ticker/six-value strip: fitting at 640px, unwrapped local scrolling at 390px.
7. **Evidence access**: Reuse native controls for an explicit full-name/evidence detail action.
   Detail text wraps freely and is usable by touch/keyboard, without entity callbacks or data requests.
   Compact 84px labels and supplementary tooltips are allowed only with complete non-hover access.
8. **Preservation**: Keep chart cropping, thumbnail options, sorting, selections, breadcrumbs, stock
   detail/loading safeguards and remote request parameters. Daily tape projection does not invalidate
   `_calculate_discovery` caches or add requests.

Rejected alternatives and rationale are in [research.md](research.md):
observed-date daily fallback, constituent renormalization, all-or-nothing display results,
new period infrastructure, wrapping the phone strip, and page-wide horizontal scrolling.

## Python API Migration

`representation_performance(...)[period]` is now `RepresentationPeriodResult`, not a float.
Read `.value`; when it is `None`, expose `.reason`. Valid representation contexts return the
ordered keys `1d`, `1w`, `1m`, `3m`, `6m`, `12m`.

Invalid shared approval evidence always raises a domain error. Activity is evaluated independently
for the requested daily date and longer-period date. Inactivity in one context makes its periods
unavailable; inactivity in both raises an error. Supply explicit `start_session`/`end_session`;
omitted dates produce an unavailable daily entry, not inferred sessions.

`calculate_absolute_performance` accepts one period, including explicit-session `1d`; its default
remains five all-required periods with unchanged arithmetic/error behavior.
Ranking/snapshot callers require and project only those five float results.
Repository callers were migrated; external Python consumers must adapt to the backward-incompatible
return shape. No release version or persisted/snapshot schema change was made.

## Constitution Check

| Gate | Design compliance |
|---|---|
| I-III: simplicity, lean delivery, YAGNI | Existing modules/native controls; only approved daily, caption and responsive work. |
| IV: avoid waste | Reuse loaded histories, one preparation per series, reused benchmark results, zero added requests. |
| V-VI: separation/cohesion | Application resolves dates; domain validates/calculates; UI projects/formats/exposes reasons. |
| Native architecture/state | Existing four tabs, callbacks, namespaced state and explicit loading remain. |
| Evidence/observable failure | Exact approved evidence, explicit unavailable reasons, no stale success or substitute data. |
| Migration/type safety | Typed six-period results; explicit legacy caller adaptation; no stored schema migration. |
| Test-first/quality | Failing focused regressions before fixes, pytest, Ruff and strict Pyright. |
| Phone/desktop usability, 4.1.0 | Six measured width/theme combinations, local scrolling and touch/keyboard evidence access. Execution pending. |

No constitutional exception is proposed. This feature validates affected Discovery surfaces,
not app-wide responsive compliance.

## Source Inventory

| Responsibility | Existing repository-root-relative files |
|---|---|
| Domain arithmetic/callers | `packages/market-data/src/market_data/domain/{sector_performance,industry_representations,industry_momentum}.py` |
| Calendar/ranking boundary | `src/market_leadership/application/{market_sessions,exchange_calendar,discover_sectors}.py` |
| Workflow/renderer | `src/market_leadership/ui/workflows/discovery_page.py`, `src/market_leadership/ui/performance_table.py`, `src/market_leadership/ui/components/progressive_tape.py` |
| Domain tests | `tests/unit/domain/test_sector_performance.py`, `tests/unit/test_industry_representations.py`, `tests/unit/test_industry_momentum.py` |
| UI tests | `tests/unit/ui/test_performance_table.py`, `tests/unit/ui/test_progressive_tape.py` |
| App tests | `tests/app/test_sector_stock_explorer.py`, `tests/app/test_discovery.py`, `tests/app/test_market_selection.py`, `tests/app/test_scoreboard.py` |
| Integration tests | `tests/integration/test_build_snapshot.py`, `tests/integration/test_industry_representations.py` |

## Execution and Validation

[Tasks](tasks.md) preserve the completed foundation and unified-API migration.
Next: T030 caption regressions/migration -> T027 failing phone/detail regressions ->
T028 scoped fixes -> T029 automated and browser acceptance.
Shared files make this sequence non-parallel.

Use [quickstart.md](quickstart.md) for commands and measured history. Test exact session math,
independent availability, literal captions/nine fields/24 cells for four rows, themes, state,
requests and stock preservation. Browser acceptance measures actual 390/640/1440 CSS pixels
in both themes and exercises real touch and keyboard; DOM clicks or hover alone are not phone proof.

Supporting artifacts: [data model](data-model.md), [research](research.md),
[UI contract](contracts/daily-performance-ui.md), [requirements checklist](checklists/requirements.md).
