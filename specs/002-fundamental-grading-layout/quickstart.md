# Quickstart and Validation: Fundamental Grading Layout

This is a Phase 1 design guide. New test files, fixtures, and UI behavior described
below are to be created during implementation; they do not exist or pass yet.

## Prerequisites

- Python 3.12 and the repository's existing `uv` workflow.
- Dependencies already available through the existing environment/lockfile. Restore
  with `uv sync --frozen` only if missing; no new dependency is required by this plan.
- Deterministic fake-Ticker bundles and a dated synthetic membership catalog.
  Fixtures include two industries and at least six stock IDs to prove pagination.
- No API key, `.env` disclosure, or live provider permission is needed for required
  tests. Tests inject settings/data sources rather than depending on developer secrets.

Definitions and expectations live in [data-model.md](./data-model.md),
[the data contract](./contracts/fundamental-data.md), and
[the UI contract](./contracts/fundamental-ui.md).

## Red-first focused checks

From the repository root, implement the planned tests first and confirm failures
identify absent behavior, not missing packages:

```bash
uv run pytest -q \
  tests/unit/test_fundamentals.py \
  tests/unit/test_stock_selection.py \
  tests/integration/test_yfinance_fundamentals.py \
  tests/integration/test_fundamental_cache.py \
  tests/integration/test_stock_membership.py \
  tests/app/test_fundamental_grading.py \
  tests/app/test_progressive_tabs.py
```

Expected outcomes after implementation:

1. Known statements produce all eight exact values under contract formulas.
   Example latest-quarter revenue 100, gross profit 40, operating income -5,
   net income 10, OCF 12, capex -2 yields 40.0% Gross Margin, -5.0% Operating
   Margin, 120.0% Cash Conversion, and 10.0% FCF Margin. Prior-year revenue
   80 yields 25.0% Sales YoY. Four EBIT quarters totaling 20 with quarter-end
   assets 200/current liabilities 100 yield 20.0% ROCE.
2. Positive/zero/negative EPS fixtures produce every valid count 0 through 8;
   three/five/seven quarters, gaps, non-finite EPS, and invalid supplied counts
   never claim an eight-quarter observation.
3. Eight single-missing cases and all-missing case retain all labels and exact
   fallback strings. Zero/negative valid values survive.
4. Four/five/eight comparable observations produce exactly four/five/eight
   chronological points; three produce the separate history caption. Five raw
   revenue quarters produce one YoY point and no fabricated four-bar YoY chart.
5. Fake factory creates one Ticker per cache miss and reads each component once
   per attempt. Fresh identical request reuses the bundle; symbol/window/cutoff/
   schema changes isolate keys; targeted refresh leaves unrelated cached stocks.
6. Exceptions, ambiguous empty statements, and rate limits are observable and
   uncached. A second explicit attempt invokes acquisition again. Valid partial
   component data remains available with a visible failed/partial request warning.
7. Fixture mode never calls yfinance. Unsupported provider configuration, invalid
   membership, unapproved live rights, and unsupported historical live contexts
   block requests with actionable messages.
8. Real entrypoint exposes three tabs, no routed page transition. Ordinary reruns
   preserve selections; parent changes invalidate only dependents; eager tab
   execution, paging, and unrelated widgets cause zero financial requests.

Use a controllable clock for cache/freshness tests; do not sleep for the TTL.
Inspect chart serialization or capture renderer chart inputs rather than assuming
AppTest text alone proves height, order, or point count.

## Regression and static validation

After focused tests pass:

```bash
uv run pytest -q tests/app tests/integration tests/contract tests/unit -m "not live"
uv run ruff check src tests
uv run pyright
```

The expanded app-shell change warrants non-live regression across discovery,
weekly fixture, state/cache, and cloud entrypoint tests. Update only navigation
expectations intentionally changed by the approved migration; unrelated existing
failures must be identified rather than silently skipped.

## Browser walkthrough

```bash
uv run streamlit run streamlit_app.py
```

Using the implementation's explicitly labelled fixture evidence mode:

1. At desktop width, choose a sector/industry in Sector/Industry Screen.
2. In Industry Deep-Dive, verify dated membership/provenance, select two stocks.
3. In Fundamental Grading, explicitly load the first page. Verify three equal
   columns, exact metric order, compact blocks, comments beneath values, and
   actual 60-pixel chart height. No ninth Cash Flow metric.
4. Review a stock with a missing metric and one with negative operating margin.
   Verify exact missing strings and "Losing money on operations" only where valid.
5. Change stock/context and verify no stale comments/charts; change industry/mode
   and verify explained dependent-state invalidation.
6. Use six selected stock fixtures to exercise page two; confirm paging alone
   does not fetch until Load is clicked. Refresh only the displayed request keys.
7. Narrow the browser; ensure ordered reflow and long commentary do not overlap
   or clip. Confirm missing chart history is distinct from missing metric data.
8. In a separate browser session, verify selections are independent.

Do not claim screenshot-identical colors/spacing without an actual reference
image; the provided textual matrix is the available layout authority.

## Optional live validation and release gates

Before any live activation or hosted publication, review source display/derived
rights and configure a validated dated catalog with provenance/coverage/approval
reference. Use only the selected yfinance provider for the live workflow.
Historical weekly fixture dates must not authorize present-day financial fetches.

After approval, explicitly load one stock and verify source/fetch time and current
quarter context. Expect Yahoo to return fewer than eight quarters: EPS Consistency
may correctly be N/A and some charts may show history limitations. This is not a
reason to pad data or switch providers. Live smoke tests are optional, not part of
the deterministic required suite and not evidence of universal provider coverage.

## Documentation and migration check

Implementation updates README with the root three-tab journey, retired routed
URLs, membership configuration, one-hour freshness/targeted refresh, and live
coverage/permission limitations. Keep old evidence labels accurate and preserve
the Cloud entrypoint. No secrets or runtime responses are committed.
