# Tasks: Fundamental Grading Layout

**Input**: [spec.md](./spec.md), [plan.md](./plan.md),
[research.md](./research.md), [data-model.md](./data-model.md), and
[contracts/](./contracts/).

**Reconciliation**: During planning, a concurrent four-task preview-only artifact
appeared. The user explicitly chose this session's expanded three-tab plan as the
authority and authorized reconciling that artifact. Its four uncompleted task IDs
are retained below; its preview-only scope, 90-pixel charts, FCF-based Cash Conversion,
negative-baseline YoY convention, and template-plan claims are superseded.
No implementation or passing tests are claimed.

## Authoritative Scope and Contracts

- Build the missing three-tab and dated stock-selection foundation, not a
  standalone preview as the final deliverable. Keep the Cloud root entrypoint.
- Use one yfinance live source and an explicitly offline fixture mode. Live
  membership/display rights remain fail-closed until reviewed and documented.
- Bundle `.info`, `.quarterly_financials`, `.quarterly_cashflow`, and the approved
  `.quarterly_balance_sheet` through one injected Ticker reader and keyed cache.
- Use the exact formulas and source/period rules in
  [fundamental-data.md](./contracts/fundamental-data.md). Cash Conversion is
  quarterly OCF / positive net income; YoY requires a positive prior-year baseline.
  ROCE uses four-quarter EBIT / quarter-end capital employed.
- One `st.columns(3)` per scorecard; 3/3/2 metric grouping. Blocks show label,
  value, immediately adjacent commentary, then chart/history limitation.
- Charts use `st.bar_chart(height=60)` and four to eight actual consecutive
  comparable observations. Below four show `Insufficient quarterly history`.
  EPS counts require eight real quarters per current or historical window.
- A one-hour cache with 256-entry bound stores only validated successful bundles.
  Ambiguous entirely empty source components and acquisition failures are explicit,
  uncached outcomes; surviving partial metrics may render alongside the error.
- Do not add a second provider, guessed members, invented financial thresholds,
  adaptive consolidation, new technical filters, or new aggregate peer scoring.

## T001 - Financial Evidence and Calculations

**Goal**: Obtain typed, deterministic scorecards independently of rendering.

- [ ] T001 Add failing tests in `tests/unit/test_fundamentals.py`, `tests/integration/test_yfinance_fundamentals.py`, and `tests/integration/test_fundamental_cache.py`; then implement typed records/pure formulas in `src/market_leadership/domain/fundamentals.py`, injected acquisition in `src/market_leadership/infrastructure/yfinance_fundamentals.py`, and keyed cache/refresh helpers in `src/market_leadership/ui/cache.py`. Cover all eight formulas, period/unit alignment, signed capex, zero/negative numerators, nonpositive denominators, missing/non-finite rows, EPS counts 0 through 8, incomplete/gapped windows, raw lookback retention, component errors/ambiguous empty responses, safe partial evidence, fresh reuse, TTL, key isolation, and targeted refresh under the data contract. Leave daily-history provider behavior unchanged.

**Checkpoint**: Complete fixture statements yield known exact values; missing
rows localize insufficiency; ambiguous/failing acquisition is observable and never
cached as successful missing data. No network is used in required tests.

## T002 - Three-Tab and Stock-Selection Foundation

**Goal**: Establish the approved production journey using dated evidence.

- [ ] T002 Add failing tests in `tests/unit/test_stock_selection.py`, `tests/integration/test_stock_membership.py`, and `tests/app/test_progressive_tabs.py`; then replace runtime routing in `src/market_leadership/app.py` with the three required tabs, extract callable discovery renderers from `src/market_leadership/ui/workflows/discovery_page.py` and `industry_discovery.py`, compose helpers through `bootstrap.py`, and add `domain/stock_selection.py`, `infrastructure/stock_membership.py`, and `ui/workflows/industry_deep_dive.py`. Extend `config.py` only for the documented catalog/source gate. Add synthetic dated catalog fixtures, validate provenance/coverage/identity/date/parent relationships, display eligible members, and maintain namespaced session-local stock IDs. Configure the page once; replace routed handoffs and whole-app stops with tab-safe flow. Test exact tab labels, parent-change invalidation, valid rerun retention, multi-session isolation, missing/invalid catalog behavior, unsupported provider/rights/historical contexts, no guessed membership, and zero financial calls from eager tab execution.

**Checkpoint**: Offline fixtures support sector -> industry -> stock selection
through the root app. Live limitations remain explicit. Existing discovery
calculations and evidence meanings are preserved; parent technical filters are
not implicitly implemented.

## T003 - Compact Matrix and Historical Bars

**Goal**: Prove the exact layout with controlled data before live integration.

- [ ] T003 Add failing renderer/AppTest cases in `tests/app/test_fundamental_grading.py`; then implement `src/market_leadership/ui/components/fundamental_matrix.py` using the typed scorecard from T001. Assert exactly one structural three-column group per stock, exact 3/3/2 order, all eight labels, percentage/count formatting, dynamic evidence-specific or neutral commentary immediately below values, and exact missing-data pairs. Add native bar charts after commentary with height 60 and four-to-eight chronological comparable points; below four show the separate history limitation. Cover eight single-missing cases and all-missing, long comments, valid zero/negative values, invalid EPS counts, stock/evidence switches, four/five/eight/three-point histories, and formula-specific lookback limits. Capture chart data/specifications to verify height/order/count rather than relying only on text.

**Checkpoint**: Fixture scorecards demonstrate the exact required matrix and
truthful histories; missing current values and missing chart history are distinct.
No ninth metric, clipped commentary, zero padding, or fabricated eight-quarter count.

## T004 - Grading Actions, Integration, and Validation

**Goal**: Complete the production flow, not just a preview.

- [ ] T004 Add failing integration/AppTest cases, then implement `src/market_leadership/ui/workflows/fundamental_grading.py` and root-tab wiring for explicit Load/Refresh actions, five selected stocks per page, current request-context tokens, freshness/provenance, visible component errors, and safe partial results. Reuse T001 cache/reader and T003 renderer; do not duplicate them. Page/context changes clear invalid displayed evidence, require explicit loading, and never leak a previous stock's comments/charts. Ensure fixture mode is entirely offline and failed Refresh never silently uses old success. Update directly related `README.md` migration/source/catalog/freshness documentation; replace intentionally obsolete navigation expectations and retain Cloud entrypoint regression. Run the focused and full non-live/static checks in the quickstart, then inspect desktop/narrow layouts, long comments, two sessions, and six-stock pagination with browser tooling.

**Checkpoint**: The fixture three-stage flow grades two or more selected stocks
end-to-end. Fresh requests reuse evidence; refresh is key-scoped; eager rendering
and unrelated widgets do not request data. Live activation remains gated by actual
reviewed rights and catalog coverage, not by success of fixture tests.

## Dependencies and Execution Order

```text
T001 financial contract -> T002 selection foundation -> T003 renderer -> T004 integration
```

Keep the four existing task IDs sequential; there are no parallel markers because
the app/cache/state integration shares boundaries. Each task contains its own
fail-first validation, not an additional hidden test phase.

| Story | Tasks | Independently verifiable result |
|-------|-------|--------------------------------|
| US1: exact matrix | T003, T004 | Controlled eight-slot scorecard; repeated stock layout |
| US2: commentary | T001, T003, T004 | Current evidence-specific text and immediate adjacency |
| US3: missing evidence | T001, T003, T004 | Exact fallbacks and unaffected valid slots |
| US4: three-step journey | T002, T004 | Dated stock selection and production grading handoff |
| US5: quarterly history | T001, T003, T004 | Four-to-eight real bars or separate short-history status |

## Required Completion Evidence

Follow [quickstart.md](./quickstart.md) for executable commands and expected
outcomes. Focused tests must fail before implementation and pass afterward; run
full non-live regression because the approved migration crosses the app shell.
Run Ruff and strict Pyright. Document actual failures instead of skipping or
claiming success. No task is complete merely because design artifacts exist.

The old routed URLs are intentionally retired, while existing discovery evidence,
valid state, source disclosures, and any already implemented aggregate grades
remain semantically unchanged. Do not claim the larger parent feature is complete.
