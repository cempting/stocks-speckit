# Quickstart Validation: Add Daily Performance

This guide applies after implementation. Planning alone does not add `1d` or establish passing
application tests. See the [UI contract](contracts/daily-performance-ui.md) and
[data model](data-model.md) for exact expected behavior.

## Prerequisites

- Python 3.12 and the repository's existing uv-managed environment/dependencies.
- A valid existing catalog manifest and approved sector/industry representations for a live
  walkthrough. Use the current default catalog; do not alter published releases for this feature.
- Deterministic tests use existing fixtures, injected histories, and a fixed clock/calendar
  boundary rather than real network data.

## Focused automated validation

Add failing tests for the new requirements before implementation. Extend the existing files,
then run from the repository root:

```bash
uv run pytest -m "not live" -q \
  tests/unit/domain/test_sector_performance.py \
  tests/unit/test_industry_representations.py \
  tests/unit/ui/test_performance_table.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_discovery.py \
  tests/integration/test_industry_representations.py
```

Include tests for the session-resolution boundary alongside the related domain/workflow tests,
freezing the clock for today's incomplete-session behavior.

Expected evidence:

- Known positive, negative, zero, and relative returns match the contract to two decimals.
- Weekend/holiday adjacency and historical as-of bounds are exact; missing sessions are not skipped.
- Non-finite/non-positive prices, duplicate dates, and missing exact endpoints are explicit failures.
- Both approved ETF and basket paths work; baskets retain all approved weights and exact endpoints.
- Daily and legacy period availability are independent. Existing five-period values/types and
  row ordering are unchanged for the same input.
- Both tables show literal `1d` before `1 week`, including unavailable-only rows.
- Four rows across six periods generate 24 formatted performance cells; missing cells are uncolored.
- Daily color scaling does not depend on longer-period extrema; both themes remain readable.
- Basis/thumbnail changes and navigation preserve selections and do not add data requests.
- Stock tapes retain their five-column projection, chart behavior, and native selection.

Run the existing quality gates without adding dependencies:

```bash
uv run ruff check \
  packages/market-data/src/market_data/domain/sector_performance.py \
  packages/market-data/src/market_data/domain/industry_representations.py \
  src/market_leadership/application/market_sessions.py \
  src/market_leadership/ui/workflows/discovery_page.py \
  src/market_leadership/ui/performance_table.py \
  src/market_leadership/ui/components/progressive_tape.py \
  tests/unit/domain/test_sector_performance.py \
  tests/unit/test_industry_representations.py \
  tests/unit/ui/test_performance_table.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_discovery.py \
  tests/integration/test_industry_representations.py
uv run pyright
```

Expand the selectors only if implementation touches additional files. Escalate to
`uv run pytest -m "not live" -q` when practical or when focused results reveal coupled failures.

## Browser walkthrough

```bash
uv run streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. If another manifest is already used, retain the existing
`MARKET_CATALOG_MANIFEST_PATH` setting. Keep synthetic validation histories isolated in automated
tests; do not introduce a runtime fixture/provider selector.

1. Open Discovery. Confirm Sector performance shows nine visible columns with `1d` immediately
   before the existing weekly header and all longer-term headers unchanged.
2. Inspect gain/loss/zero or unavailable examples supported by current evidence. Confirm two-decimal
   percentages, neutral zero, uncolored `Unavailable`, and visible daily failure context where needed.
3. Select an approved sector. Confirm Industry momentum presents the identical six horizons using
   each industry's own approved representation, not the parent sector's return.
4. Change Performance basis to vs S&P 500. Compare daily values against the same-session entity
   minus benchmark result. Return to Absolute; no new history load should be needed.
5. Change each existing thumbnail period. Confirm daily/legacy values are unchanged while chart
   cropping changes. Navigate between sectors, industries, and stocks; controls/selections retain
   their existing behavior and stocks show the unchanged five columns.
6. Check both light and dark themes at wide and narrow widths. Confirm daily/weekly adjacency,
   all-column access, readable cells, full entity labels, native selection, and preserved charts.
7. Use deterministic automated cases for missing endpoints, baskets, weekend/holiday dates, and
   incomplete sessions when live market evidence cannot exercise them.

Record observed outcomes and commands during implementation. Do not infer numeric correctness,
CSS accessibility, or zero extra requests solely from a visible header or a successful app launch.
