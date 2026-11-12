# Validation Guide: Stock Detail Analysis

**Status**: US1 chart ranges, US2 consolidation evidence, and US3 quarterly fundamentals are
implemented and focused automated checks pass. Browser acceptance and provider-rights review
remain release gates; this guide does not authorize live tests or public data publication.

See the [implementation plan](plan.md), [data model](data-model.md), and
[stock-detail UI contract](contracts/stock-detail-ui.md).

## Prerequisites

- Run from the repository root with Python 3.12 and the existing `uv` environment.
- If the environment is unavailable, restore the checked-in dependency set with
  `uv sync --all-packages`; do not add dependencies for this feature.
- Preserve the selected catalog, active source configuration, local caches, and unrelated work.
- Use injected, deterministic histories and quarterly bundles for automated tests. Do not mark
  external-provider tests as part of the default offline suite.
- Keep current explicit stock-history and financial-evidence load actions. Never use a synthetic
  catalog to request live company or market data.
- Provider display and derived-use permissions must be reviewed before any public deployment.

## Focused Automated Checks

The following selectors cover chart history, the feature-001 detector contract, stock-detail
annotation behavior, and quarterly fundamentals.

```bash
uv run pytest -m "not live" -q \
  tests/unit/domain/test_stock_chart.py \
  tests/unit/domain/test_consolidation.py \
  tests/unit/test_fundamentals.py \
  tests/integration/test_yfinance_fundamentals.py \
  tests/app/test_stock_detail.py
```

### US1 Implementation Checkpoint — 2026-11-12

- `uv run pytest -q tests/unit/domain/test_stock_chart.py tests/unit/infrastructure/test_market_data_providers.py tests/unit/infrastructure/test_market_data_cache.py tests/unit/ui/test_sector_chart.py tests/app/test_stock_detail.py tests/app/test_stock_lookup.py tests/integration/test_stock_evidence.py`
  — **86 passed**.
- Focused `uv run ruff check` over the changed chart/history modules and selectors — **passed**.
- Coverage includes all six month ranges, pre-range 50/150-session averages, cutoff and gap
  handling, selected-provider/date-window cache identity, explicit range-based history loading,
  period-state reset for a changed listing, and detail rendering beyond the 260-row thumbnail cap.
- No pre-existing failures occurred in these selectors. The run emitted 12 dependency
  deprecation warnings from `exchange_calendars` concerning NumPy's generic timedelta unit.
- The yfinance adapter already applies its explicit `start`/`end` request bounds and adjusted
  daily close mapping; the change now supplies a range-specific verified request window through
  that existing adapter and cache boundary.

### US3 Implementation Checkpoint — 2026-11-12

- Added history-only net margin, current ratio, and debt-to-equity alongside the established
  feature-002 history formulas. Derived observations retain their input observation IDs and
  explicit insufficient states; the eight-metric peer scorecard is unchanged.
- Added explicit quarterly yfinance mappings for cash and equivalents, total debt, shareholders'
  equity, and ordinary shares. Missing rows remain absent. Current market capitalization is
  attached only with its current observation date and currency.
- The detail view shows the latest eight quarters, source/observation context, reported versus
  derived origin, and missing/zero/negative/insufficient values without backdating current
  market capitalization.
- `uv run pytest -q tests/unit/test_fundamentals.py tests/integration/test_yfinance_fundamentals.py tests/integration/test_company_evidence.py tests/app/test_stock_detail.py`
  — **74 passed**.
- Focused `uv run ruff check` over the changed fundamentals, company-evidence, adapter, UI, and
  test files — **passed**. `uv run pyright` — **0 errors, 0 warnings, 0 informations**.
- Existing tests emitted four NumPy timedelta deprecation warnings from `exchange_calendars`;
  no feature-specific failures occurred.

### US2 Implementation Checkpoint — 2026-11-12

- Feature 001's `quiet-sideways-v1` detector and reference tests are implemented. The stock-detail
  view consumes its typed result and does not duplicate its detection algorithm.
- Selected history retains provider-verified adjusted OHLC and split evidence. Consolidation
  remains explicitly insufficient when adjusted prices, comparable volume, source provenance,
  or complete history evidence is unavailable; OHLC is never inferred from close.
- History requests include 271 pre-range sessions for the preceding 252 valid 20-session
  BandWidth observations. Cutoff and gap behavior remain covered by the detector and provider
  selectors.
- The detail view defaults to the latest interval, permits inspection of older intervals, and
  displays observed dates, duration, corridor, volume context, cutoff, and truncation status.
  An interval outside the visible range is described without changing the selected chart period.
  Sufficient history with no interval is distinct from insufficient evidence; no forecast language
  is used.
- `uv run pytest -m "not live" -q tests/unit/domain/test_stock_chart.py tests/unit/domain/test_consolidation.py tests/unit/infrastructure/test_market_data_providers.py tests/contract/test_market_data_provider.py tests/contract/test_runtime_market_data_providers.py tests/unit/ui/test_sector_chart.py tests/app/test_stock_detail.py`
  — **110 passed**.
- Focused Ruff and repository-wide `uv run pyright` checks passed; Pyright reported **0 errors,
  0 warnings, 0 informations**. Test output contained 12 dependency deprecation warnings from
  `exchange_calendars` for NumPy's generic timedelta unit.

### Remaining implementation and release gates

- The latest full offline suite recorded before the US2 UI integration reported **1,112 passed,
  1 failed, 1 deselected**. The known failure,
  `test_app_starts_with_default_catalog_without_live_provider`, expects three tabs while the
  current app also exposes `Find a stock`; it is unrelated to stock detail. The full suite has not
  been rerun after US2 integration.
- The 1440px/390px browser acceptance has not been run.
- Provider display and derived-use permissions remain unreviewed for public deployment. Do not
  publish or host results until this release gate is resolved.

Verify at least these controlled cases:

1. All six period choices are present in order, default to `6m`, and crop the same selected
   listing's aligned price, moving-average, and volume history.
2. The 50/150-session averages use completed adjusted closes, include pre-range warm-up, respect
   the as-of cutoff, and distinguish short history, gaps, non-finite data, and failed requests.
3. A 24-month visible range is not truncated by the old 260-session renderer cap or 550-calendar-
   day request limit; the required warm-up remains outside the visible range.
4. Consolidation uses the selected stock's adjusted OHLC and comparable volume, the 001 detector,
   prior-only bandwidth history, its 271-session pre-range warm-up, and explicit cutoff/gap/
   insufficiency states. There is no inferred OHLC or breakout claim.
5. Quarterly income, cash-flow, and balance-sheet rows retain fiscal period, currency, basis,
   origin, and source. Test zero, negative, missing, partial, restated, cumulative-YTD, stale,
   incompatible, and failed evidence.
6. Additional cash, debt, equity, and share-count mappings remain unavailable when the provider
   does not return the row. Ratio denominators and period/currency compatibility are validated.
7. Identity mismatch blocks evidence attachment; market capitalization has a dated current value
   and is not backdated to manufacture historical valuation multiples.
8. A rerun, resize, or chart-only selection does not repeat unrelated fundamental acquisition;
   refresh targets only the relevant cache request and failures do not become successful cached
   results.

Run focused formatting and strict type checking after implementation:

```bash
uv run ruff check \
  packages/market-data/src/market_data/domain/stock_chart.py \
  packages/market-data/src/market_data/domain/fundamentals.py \
  src/market_leadership/application/load_stock_history.py \
  src/market_leadership/ui/components/stock_detail.py \
  src/market_leadership/ui/sector_chart.py \
  tests/unit/domain/test_stock_chart.py \
  tests/unit/test_fundamentals.py \
  tests/app/test_stock_detail.py
uv run pyright
```

If feature 001's detector or provider mappings change additional files, include their focused
tests and source paths in the same checks. Escalate to `uv run pytest -m "not live" -q` when
focused failures indicate coupling or when preparing a release.

## Browser Acceptance

Start with `uv run streamlit run streamlit_app.py` only in an environment configured for the
existing reviewed catalog and selected permitted provider. For deterministic browser acceptance,
use a test harness with injected fixture evidence; it must not add a production fixture-provider
switch. Do not call live endpoints solely to create a visual test dataset.

At actual CSS viewport widths **1440px** and **390px**, verify the existing stock-detail journey:

1. Select the same verified listing, explicitly load history and financial evidence, and exercise
   `1m`, `3m`, `6m`, `12m`, `18m`, and `24m`. Record that each visible window is correct and that
   moving-average warm-up is not displayed as part of the selected range.
2. Confirm price and aligned volume remain readable in one chart view, with 50/150-session
   overlays, selected range, stock identity, and requested/observed data context.
3. Exercise sufficient, short, gapped, and failed history. Valid series remain visible and
   insufficiency/failure states are not obscured by a zero line or stale result.
4. Inspect a fixture with latest, older, and no consolidation intervals; verify only the latest
   appears by default, older intervals are inspectable, and insufficient history is distinct from
   no detection. No annotation predicts a breakout.
5. Read company size and quarterly metrics, including missing/zero/negative and partially
   available values. Verify fiscal period, units/currency, source, derived status, and explanations
   are accessible without hover.
6. On the phone-width view, verify touch/keyboard-operable controls, readable charts, stacked or
   reflowed evidence, and any table-local scrolling. Ordinary page content must not scroll
   horizontally; no controls or disclosures overlap or clip.

Automated DOM/AppTest assertions do not establish phone usability. Record viewport dimensions,
exercised flows, request/cache observations, outcomes, and remaining gaps. Live-provider output
is supplementary only and must not replace deterministic results.
