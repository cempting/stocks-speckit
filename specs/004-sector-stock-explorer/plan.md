# Implementation Plan: Sector-to-Stock Explorer

**Reconciled**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Scope and Current Authority

The approved [016 amendment](../016-add-daily-performance/spec.md) adds `1d` before `1 week`
to both entity tapes, superseding only the five-return/eight-visible-column baseline with
six returns/nine columns. Preserve all chart, thumbnail, ranking, stock, and loading behavior;
historical completed tasks do not claim delivery of the new column.

004 owns Discovery and Industry Deep-Dive, progressive navigation, live industry
momentum and the accepted chart/control baseline, incorporating former 003.
015 owns Find a stock placement; retain Yahoo Classification Preview as well.
Keep the four existing root tabs in their current order, with independent widget
state. Discovery must not render the dedicated lookup workflow.
012 retains exact identity/listing and membership safeguards. On 013 adoption,
all four workflows consume one pinned validated service context and permission gate.

Catalog authority is the validated manifest-backed regional release under 010,
with 012's explicit reviewed version boundary for overlapping memberships/deeper
hierarchy. Do not restore SQLite catalogs, database initialization/import commands,
fixed tickers, JSON environment catalogs or provider/fixture runtime modes.
006 owns the current five-column stock table; 008 owns reviewed representations.

The obsolete database/two-tab planning body has been removed.
[Tasks](tasks.md) preserve existing completion evidence, not permission to replay
historical storage/navigation work. Former 003 IDs and original evidence are in
the [ledger](../task-history.md).

## Implemented Sector Performance Preservation Baseline

This is a preservation plan, not a UI rebuild or redesign.
[Spec](spec.md) FR-025-FR-032 / SC-012-SC-015,
[progressive UI contract](contracts/progressive-discovery.md) and the supporting
[live UI contract](../003-industry-momentum-table/contracts/live-discovery-ui.md)
govern subsequent work. Intentional presentation changes require explicit approval
and coordinated artifact/test updates.

The user-approved 2026-11-06 amendment under [015](../015-dedicated-stock-lookup/plan.md)
changes only entity-button labels to ticker above full wrapping name, with ticker
font size at least twice the name's. Missing sector/industry ETF tickers say `No ticker`.
The subsequent approved column amendment removes sector Ticker and industry ETF
as separate visible columns because the buttons already contain those values.
Keep the internal evidence fields, all other preservation invariants and selection behavior.

### Implementation invariants

- `discovery_page.render_discovery` uses `st.columns((2, 2, 2))` for heading,
  Thumbnail period and Performance basis, left to right. Preserve active-stage
  titles, selectors, coverage, provenance, refresh and insufficiency messages.
- Segmented-control keys remain
  `market_leadership.progressive_discovery.thumbnail_period` and
  `market_leadership.progressive_discovery.performance_basis`.
  Ordered period options/default: `1w, 1m, 3m, 6m, 1y` / `3m`; basis:
  `Absolute, vs S&P 500` / `Absolute`. Cleared selections use these defaults;
  parent callbacks do not reset valid controls.
- Calendar windows subtract pandas `DateOffset` from the as-of date.
  `_preview_payloads` calculates SMA/direction before inclusive cropping, without
  modifying source history. Keep `preview_start` handoff through entity/member
  tapes; selected-stock detail retains its full history.
- Keep one progressive tape at a time, stable catalog-node name-button callbacks,
  breadcrumbs and existing descendant invalidation before widget rendering.
  Preserve date, control choices and valid loaded peer context on return.
- Keep Streamlit chart rows and styled return cells, not a plain dataframe.
  Row weights remain `[1.3, 1.3, 1.0, ...]`. Price/SMA and volume plots remain
  separate adjacent charts, nominal width 135 and height 84, stretched to cells.
  Preserve the current `Price + 50 MA` and `Volume by price direction` headings.
- Stock tapes retain exactly five visible columns: price/50-MA chart, volume
  chart, Ticker including company name, CAP Type, Total Score. A private Name
  projection must not become a sixth visible column.
  Industry Status, Representation and Representation type stay hidden, with
  their evidence retained in name-button tooltips; sector status follows its
  existing tooltip treatment. Sector Ticker and industry ETF stay internal;
  each entity tape shows two charts, its entity button and five return periods.
  Keep current name/ID ordering and the stock Ticker label.
- `performance_column_styles` remains the shared palette producer for Styler
  and HTML cells, with independent per-column positive/negative normalization.
  Light neutral/gain/loss: `#f4f6f5` / `#5f9f75` / `#d66d65`;
  dark: `#18232d` / `#166534` / `#991b1b`;
  foregrounds: `#17212b` / `#edf3f7`.
  Return cells retain two-decimal percentages, right alignment, 0.5rem padding,
  0.25rem corners and tabular numerals. Missing cells say `Unavailable` without
  a gain/loss background. Volume direction colors remain unchanged.
- `calculate_performance` remains authoritative: completed closes on/before
  calendar boundaries and matching-period reviewed S&P 500 benchmark subtraction.
  Preview selection does not change returns or provider history-range keys.
  Preserve requested/observed session, stale and insufficient states.
- Sector/industry representations use exact approved effective-dated listings
  in the active release, not automatic largest-stock, fixed ETF or parent proxies.
  Preserve the reviewed sector mapping basis without fabricating absent coverage.
  ETF representations do not create stock industry memberships.
- History, scores and issuer evidence remain explicitly loaded/refreshed.
  Selection, tab rendering and ordinary reruns must not cause hidden acquisition.
  Errors, incomplete data and unauthorized source context remain visible.

### Preservation evidence

Existing coverage includes `tests/unit/ui/test_progressive_tape.py`,
`tests/unit/ui/test_performance_table.py`,
`tests/app/test_sector_stock_explorer.py` and
`tests/integration/test_region_discovery.py`.
T034-T035 and T047 in [tasks](tasks.md) protect this baseline.
Keep the [recorded browser evidence](quickstart.md#convergence-preservation-evidence-2026-10-30)
as historical observations, not a substitute for permanent regression tests.
Use controlled catalogs and injected providers; never alter user data to satisfy tests.

## Technical Context and Delivery

Reuse constrained Python, Streamlit, pandas, NumPy, Altair and yfinance dependencies,
existing parameter-keyed successful caches and session-private stable-ID selections.
Pure calculations/catalog/schema code belongs in `packages/market-data/src/market_data/`;
app acquisition, rendering and state stay in `src/market_leadership/`.
Reviewed publication/maintenance belongs to `services/market-structure/`.
Do not recreate moved helpers or introduce another authority/store.

For accepted future changes: add failing identity/catalog/chart/state tests, change
the smallest owned boundary, integrate the current workflows, then run focused
regressions and existing Ruff/strict Pyright gates. Preserve cached interaction
p95 <=2 seconds for up to 100 displayed entities in controlled runs; remote source
latency is not guaranteed. Source/display rights, complete eligible peer cohorts,
001 formulas and 012 context gates remain prerequisites, not inferred permissions.

## Constitution and Complexity

No new exception or architectural expansion is authorized. 015's existing fourth-tab
exception remains owned, time-bounded and tracked by
[issue #2](https://github.com/cempting/stocks-speckit/issues/2).
This documentation-only cleanup changes neither application behavior/style nor
the completion status of accepted pending work.
