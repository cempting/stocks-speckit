---
description: "Implementation tasks for Stock Detail Analysis"
---

# Tasks: Stock Detail Analysis

**Input**: Design documents from `specs/017-stock-detail-analysis/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/stock-detail-ui.md`, `quickstart.md`

**Tests**: Test-first tasks are included because the project constitution requires regressions
to fail before the corresponding implementation changes.

**Organization**: Tasks are grouped by the specification's independently testable user stories.

## Phase 1: Setup

**Purpose**: Project initialization and basic structure.

The Python 3.12/uv workspace, pytest, Ruff, Pyright, Streamlit, Altair, pandas, and the existing
`market-data` package are already configured. No project scaffolding, dependency, or provider
setup task is needed.

---

## Phase 2: Foundational

**Purpose**: Shared prerequisites that block all user stories.

The existing verified listing, selected-provider, explicit-load, cache, and company-evidence
boundaries are shared prerequisites and will be preserved. No new shared infrastructure is
required. The feature-001 consolidation detector is a separate dependency of US2 only, not a
blocker for the independent chart and fundamentals stories.

---

## Phase 3: User Story 1 - Read Price, Trend, and Volume Together (Priority: P1) 🎯 MVP

**Goal**: Choose each requested stock-chart horizon and inspect the same listing's daily price,
50/150-session moving averages, and aligned volume.

**Independent Test**: With controlled verified-listing history, select all six chart ranges and
confirm each visible date interval, price/volume alignment, moving-average values/statuses, and
preserved stock identity.

### Tests for User Story 1

> Write these regressions first and confirm they fail before implementation.

- [X] T001 [P] [US1] Add stock-chart domain tests in `tests/unit/domain/test_stock_chart.py` for the six visible ranges, completed-session cutoff, 50/150-session warm-up, gaps, and insufficient/unavailable moving-average states.
- [X] T002 [P] [US1] Add history-request tests in `tests/unit/infrastructure/test_market_data_providers.py` for requested range boundaries, pre-range moving-average warm-up, selected provider identity, and cache-key separation by range/cutoff.
- [X] T003 [P] [US1] Extend stock-detail AppTests in `tests/app/test_stock_detail.py` to assert labels/order `1m, 3m, 6m, 12m, 18m, 24m`, default `6m`, range switching, and clearing chart state when listing identity changes.

### Implementation for User Story 1

- [X] T004 [US1] Extend the explicit stock-history request in `src/market_leadership/application/load_stock_history.py` and `src/market_leadership/infrastructure/yfinance_provider.py` to cover the selected visible interval plus at least 150 preceding valid completed sessions; include provider, symbol, requested dates, cutoff, and relevant parameters in the existing cache identity without bypassing listing verification.
- [X] T005 [US1] Extend `StockChartEvidence` in `packages/market-data/src/market_data/domain/stock_chart.py` to retain pre-range warm-up for the exact 50- and 150-session simple averages while exposing only the selected visible interval; exclude observations after `as_of` and preserve explicit available/insufficient/unavailable states.
- [X] T006 [US1] Update `build_sector_chart(...)` in `src/market_leadership/ui/sector_chart.py` to render all rows for the selected stock-detail interval rather than truncating that view at 260 sessions, while preserving existing sector/industry thumbnail limits and aligned volume.
- [X] T007 [US1] Add the six ordered, session-local chart-period controls to `render_stock_detail(...)` in `src/market_leadership/ui/components/stock_detail.py`, default to `6m`, reuse already-loaded sufficient history, and request only missing coverage through the existing explicit-load boundary.
- [X] T008 [US1] Run the US1 domain/provider/AppTest selectors and record outcomes and any existing baseline failures in `specs/017-stock-detail-analysis/quickstart.md`.

**Checkpoint**: US1 works independently with price, aligned volume, both moving averages, all six
periods, correct warm-up/cutoff, and explicit short-history states.

---

## Phase 4: User Story 3 - Understand Company Size and Financial History (Priority: P1)

**Goal**: Show verified company size and up to eight comparable quarterly periods of earnings,
revenue, cash flow, balance-sheet evidence, and supported derived fundamentals.

**Independent Test**: With controlled company evidence, verify identity, market-cap date/currency,
quarter ordering, metric values/units/origins, zero/negative/missing distinctions, and partial or
failed evidence without changing the existing scorecard or cash-flow warnings.

### Tests for User Story 3

> Write these regressions first and confirm they fail before implementation.

- [X] T009 [P] [US3] Extend derived-metric tests in `tests/unit/test_fundamentals.py` for net margin, current ratio, debt-to-equity, existing 002 metric definitions, compatible fiscal periods/currencies, invalid denominators, and missing/zero/negative observations.
- [X] T010 [P] [US3] Extend adapter tests in `tests/integration/test_yfinance_fundamentals.py` with fixture rows for cash and equivalents, total debt, shareholders' equity, and shares outstanding, including absent/alias rows and partial statement coverage.
- [X] T011 [P] [US3] Extend stock-detail AppTests in `tests/app/test_stock_detail.py` for verified profile display, latest-eight-quarter ordering, reported versus derived status, and distinct missing/zero/negative/failed states.

### Implementation for User Story 3

- [X] T012 [US3] Extend explicit quarterly row mappings in `src/market_leadership/infrastructure/yfinance_fundamentals.py` and the normalized bundle in `packages/market-data/src/market_data/domain/fundamentals.py` for cash and equivalents, total debt, shareholders' equity, and shares outstanding; preserve these data-model constraints verbatim: `basis` is `quarterly`, `annual`, `ytd`, or `unknown`; `origin` is `source_supplied` or `derived`; values are finite; periods are actual reported periods; units/currency/scale and source provenance remain identifiable; missing rows remain absent and are never zero-filled or fuzzy-matched.
- [X] T013 [US3] Add history-only derived metrics in `packages/market-data/src/market_data/domain/fundamentals.py` using the data-model formulas: revenue YoY = current quarter revenue/prior same fiscal-quarter revenue - 1; diluted EPS YoY = current diluted EPS/prior same fiscal-quarter EPS - 1; gross margin = gross profit/revenue; operating margin = operating income/revenue; net margin = net income/revenue; FCF margin = free cash flow/revenue; ROCE = TTM EBIT/quarter-end capital employed; current ratio = quarter-end current assets/current liabilities; debt-to-equity = quarter-end total debt/shareholders' equity. Require positive prior revenue/EPS and positive ratio denominators as specified in `data-model.md`; unavailable inputs remain unavailable, and no new metric changes peer-score inputs.
- [X] T014 [US3] Extend `render_stock_detail(...)` in `src/market_leadership/ui/components/stock_detail.py` to show verified profile fields and latest-eight-quarter facts with fiscal period, units/currency, origin, source/date context, and independent missing/partial/failure states; show market capitalization only with its current observation date/currency, never backdate it, and keep dated valuation snapshots optional; retain existing scorecard and risk-warning presentation.
- [X] T015 [US3] Run the US3 domain, adapter, and AppTest selectors and record actual coverage limitations and results in `specs/017-stock-detail-analysis/quickstart.md`.

**Checkpoint**: US3 is independently testable with verified evidence and partial/missing data;
existing peer scores, cash-flow warnings, identity, and data-source selection remain unchanged.

---

## Phase 5: User Story 2 - Identify a Consolidation Interval (Priority: P2)

**Goal**: Highlight the selected stock's latest qualifying historical consolidation and allow
inspection of older intervals without implying a prediction.

**Independent Test**: With controlled adjusted OHLC and volume plus typed detector intervals,
verify latest/older interval presentation, observed dates and corridor, and distinct no-detection
versus insufficient-evidence states.

**Dependency**: Feature 001 owns the `quiet-sideways-v1` detector. Do not duplicate its algorithm
in feature 017. If its implementation/reference tests are not ready, complete the feature-001
detector work before continuing with this phase.

### Tests for User Story 2

> Write these regressions first and confirm they fail before implementation.

- [X] T016 [US2] Verify the feature-001 detector and reference tests are implemented in `packages/market-data/src/market_data/domain/consolidation.py` and `tests/unit/domain/test_consolidation.py`; if either is missing or fails, stop this phase and complete the detector through feature 001 before changing feature-017 behavior.
- [X] T017 [P] [US2] Add adjusted-OHLC provider/history tests in `tests/unit/infrastructure/test_market_data_providers.py` and `tests/unit/domain/test_stock_chart.py` for finite positive adjusted prices, non-negative comparable volume, explicit gaps, cutoff isolation, and no inferred OHLC.
- [X] T018 [P] [US2] Extend stock-detail AppTests in `tests/app/test_stock_detail.py` with typed qualifying, older, no-interval, and insufficient-history detector outcomes and assertions for the default latest-only annotation.

### Implementation for User Story 2

- [X] T019 [US2] Extend the daily-history model in `packages/market-data/src/market_data/domain/stock_chart.py`, `MarketDataProvider` in `src/market_leadership/application/ports.py`, and `src/market_leadership/infrastructure/yfinance_provider.py` to carry verified adjusted open/high/low alongside adjusted close and comparable volume; preserve finite-value/date validation and never infer OHLC from close.
- [X] T020 [US2] Extend the selected-history request in `src/market_leadership/application/load_stock_history.py` to obtain up to 271 prior valid sessions before the first visible candidate for the preceding 252 valid 20-session BandWidth observations; retain the 150-session detector warm-up, explicit cutoff, and insufficient state when gaps or provider coverage prevent the requirement.
- [X] T021 [US2] Pass typed feature-001 intervals into the chart rendered by `src/market_leadership/ui/components/stock_detail.py` and `src/market_leadership/ui/sector_chart.py`; show at most the latest interval by default, allow older-interval inspection, expose dates/duration/corridor/cutoff/limitations, and distinguish no interval from insufficient evidence without forecast language.
- [X] T022 [US2] Run the US2 detector/provider/detail tests and record the feature-001 dependency, supported OHLC coverage, and actual annotation results in `specs/017-stock-detail-analysis/quickstart.md`.

**Checkpoint**: US2 uses only the established feature-001 detector and selected stock's own
history; no chart annotation appears as a forecast or substitutes for missing evidence.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete detail experience and preserve project-wide constraints.

- [X] T023 [P] Run `uv run ruff check` on `packages/market-data/src/market_data/domain/stock_chart.py`, `packages/market-data/src/market_data/domain/fundamentals.py`, `src/market_leadership/application/load_stock_history.py`, `src/market_leadership/application/ports.py`, `src/market_leadership/infrastructure/yfinance_provider.py`, `src/market_leadership/infrastructure/yfinance_fundamentals.py`, `src/market_leadership/ui/components/stock_detail.py`, `src/market_leadership/ui/sector_chart.py`, and the focused test files; run strict `uv run pyright` and record results in `specs/017-stock-detail-analysis/quickstart.md`.
- [X] T024 [P] Run the focused feature selectors followed by `uv run pytest -m "not live" -q` when focused results warrant or before release; record failures and outcomes in `specs/017-stock-detail-analysis/quickstart.md`.
- [ ] T025 Validate the stock-detail workflow in a controlled browser at actual 1440px and 390px CSS widths, including all six periods, touch/keyboard controls, chart readability, evidence access, and absence of page-wide horizontal scroll; record viewport, flows, results, and gaps in `specs/017-stock-detail-analysis/quickstart.md`.
- [ ] T026 Review the selected provider's display and derived-data terms for the intended deployment and record the approval/status in `specs/017-stock-detail-analysis/quickstart.md`; do not publish or host results while this release gate is unresolved.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No setup tasks; the existing workspace and validation tools are configured.
- **Foundational (Phase 2)**: No new shared code is required. Existing verified identity, explicit-load, provider, and cache boundaries remain prerequisites.
- **User stories (Phases 3-5)**: All use the existing stock-detail context. US1 and US3 are independently testable, but both update `stock_detail.py` and `tests/app/test_stock_detail.py`; serialize those shared-file edits.
- **Polish (Phase 6)**: Depends on the stories selected for delivery; provider-rights review is a release gate for public display/derived use.

### User Story Dependencies

- **US1 (P1)**: Can start immediately. It needs no new detector or financial mapping.
- **US3 (P1)**: Can proceed independently of chart calculations; its detail-view integration shares `stock_detail.py` with US1 and should be serialized. It must preserve features 002/011/014 semantics.
- **US2 (P2)**: Depends on feature 001's detector and passing reference tests. It also extends daily OHLC history and shares stock-chart/UI files; do not start its integration before the detector dependency is ready.
- **Recommended delivery order**: US1 MVP → US3 quarterly fundamentals → US2 consolidation overlay after feature 001 is ready.

### Within Each User Story

- Complete the story's controlled test tasks before its implementation tasks.
- For US1, history request/evidence precedes chart rendering and period-control integration.
- For US3, row mapping precedes derived calculations; metric calculations precede detail rendering.
- For US2, detector readiness precedes OHLC tests and integration; adjusted OHLC and warm-up precede chart annotations.
- Run the story's focused test selectors at its checkpoint before moving on.

### Parallel Opportunities

- **US1**: T001, T002, and T003 can be written in parallel because they target separate domain, provider, and AppTest files.
- **US3**: T009, T010, and T011 can be written in parallel because they target separate domain, adapter-integration, and AppTest files.
- **US2**: After T016 passes, T017 and T018 can be written in parallel because provider/domain and AppTest files are distinct.
- **Polish**: T023 and T024 are independent read-only validation runs after implementation; serialize any updates to the shared quickstart results section.
- **Cross-story caution**: Domain-level work for US1 and US3 can be parallelized by separate owners, but `stock_detail.py` and `tests/app/test_stock_detail.py` edits must be assigned sequentially. US2 also shares chart/history files with US1.

## Parallel Examples

### User Story 1

```text
Task: T001 - stock-chart evidence/range tests in tests/unit/domain/test_stock_chart.py
Task: T002 - provider request/cache tests in tests/unit/infrastructure/test_market_data_providers.py
Task: T003 - period controls AppTests in tests/app/test_stock_detail.py
```

### User Story 3

```text
Task: T009 - derived fundamental tests in tests/unit/test_fundamentals.py
Task: T010 - quarterly provider mapping tests in tests/integration/test_yfinance_fundamentals.py
Task: T011 - financial detail AppTests in tests/app/test_stock_detail.py
```

### User Story 2

```text
After T016 confirms feature 001 detector readiness:
Task: T017 - adjusted OHLC/domain/provider tests in tests/unit/infrastructure/test_market_data_providers.py and tests/unit/domain/test_stock_chart.py
Task: T018 - consolidation annotation AppTests in tests/app/test_stock_detail.py
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Retain the existing app setup and provider boundaries; record a non-live baseline.
2. Add and fail the chart-history, provider-request, and root-detail tests.
3. Implement requested-range history and the six controls with visible-window cropping and SMA warm-up.
4. **Stop and validate US1 independently** using the focused selectors and responsive browser checks.

### Incremental Delivery

1. Deliver US1 as the first independently testable increment.
2. Add US3's profile and quarterly raw/derived financial history without changing existing scores or risk warnings.
3. Add US2 only after feature 001's detector is implemented and its reference tests pass.
4. Complete cross-story static, offline-suite, responsive-browser, and provider-rights gates.
