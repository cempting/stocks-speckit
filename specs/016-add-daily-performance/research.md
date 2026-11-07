# Research: Daily Performance

**Date**: 2026-11-06 | **Status**: Design decisions resolved.

## Decisions and Alternatives

| Decision | Rationale | Rejected alternative |
|---|---|---|
| Pure exact-endpoint daily helper in the existing domain module | Deterministic fractional arithmetic, isolated from clocks/calendars. | New service or generic configurable period engine. |
| Application resolves requested-date official sessions | Weekends/holidays and missing prices are distinct; entity/benchmark use the same pair. | Last two non-null rows, calendar-day subtraction or stale observed-date fallback. |
| Unified six-period representation results with value/reason entries | Daily and supported longer horizons remain available independently; no bare nullable result loses failure context. | Separate representation daily API, all-or-nothing display, fabricated zeros or silent omissions. |
| Exact approved ETF/basket evidence | Both entity tapes use reviewed representations; every basket member keeps approved weights and matching endpoints. | ETF-only handling, parent proxies, inferred members or renormalization. |
| Benchmark required only for relative daily | Absolute daily remains usable without benchmark; relative is entity minus matching benchmark. | Shared failure block blanking all periods or silent Absolute fallback. |
| Shared display mapping and renderer | Existing formatting/palettes/metadata are reused; `1 day`/`1 year` are captions for `1d`/`12m`. | Bespoke daily cells, new thumbnail or ranking controls, calculation-key renaming. |
| Scoped native header, row scrolling and details | Preserve existing state/callbacks; provide readable phone controls and non-hover evidence. | Page-global CSS, wrapped 390px strip, shrinking/clipping values or page-wide scrolling. |

## Boundaries

- Domain: [sector_performance](../../packages/market-data/src/market_data/domain/sector_performance.py)
  and [industry_representations](../../packages/market-data/src/market_data/domain/industry_representations.py).
  `PerformancePeriod` supports `1d`; `calculate_absolute_performance` accepts one selected period
  while retaining its default five-period contract and legacy `PerformanceResult`.
- Calendar: [market_sessions](../../src/market_leadership/application/market_sessions.py) and
  [exchange_calendar](../../src/market_leadership/application/exchange_calendar.py) supply explicit adjacent dates.
- UI: [discovery_page](../../src/market_leadership/ui/workflows/discovery_page.py),
  [performance_table](../../src/market_leadership/ui/performance_table.py) and
  [progressive_tape](../../src/market_leadership/ui/components/progressive_tape.py) reuse loaded histories,
  nullable percentage projections, shared palettes and native widgets.

Daily lookup precedes existing observed-date chart/long-period cropping. Missing requested-date
endpoints remain unavailable rather than triggering acquisition or interval shifts.
Preserve valid longer arithmetic, stock behavior and five-period ranking/snapshot outputs;
independent display availability and the typed Python return-shape migration are intentional.

## Validation

Extend existing domain, completed-session, workflow and renderer tests before source fixes.
Check exact units/endpoints, literal captions/order, independent availability, approved baskets,
both bases/themes, state/requests and stock preservation. Browser checks measure actual widths
and use real touch/keyboard input for scrolling/details; header presence, hover or DOM clicks
alone are insufficient. [Quickstart](quickstart.md) retains observed history and pending gates.
