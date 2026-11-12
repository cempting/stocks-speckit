# Implementation Plan: Stock Detail Analysis

**Branch**: `main` (planning feature identifier: `017-stock-detail-analysis`) | **Date**:
2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/017-stock-detail-analysis/spec.md`

## Summary

Extend the existing stock-detail price/volume chart and financial-evidence surface rather than
adding another stock page or data provider. Reuse typed stock-chart history, the current verified
listing loader, the `quiet-sideways-v1` consolidation contract, and the quarterly fundamental
bundle. Add the six chart ranges, request only enough history for the selected range plus
indicator warm-up, extend adjusted OHLC and quarterly row coverage where required, and present
availability/provenance without changing existing peer scores or cash-flow warnings.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: Existing Streamlit application, Altair, pandas, internal `market-data`
workspace package, and the selected yfinance market-data source. No new dependency is proposed.

**Storage**: No new durable store. Reuse the current `st.cache_data` market/fundamental results and
namespaced session-local selection state; retain historic evidence only through its existing
approved archive path.

**Testing**: Existing pytest unit, integration, and AppTest suites; Ruff; strict Pyright; and
manual/browser responsive validation. Deterministic market and financial cases use injected
fixtures. Live-provider tests remain separately marked and are not required for normal validation.

**Target Platform**: Existing Streamlit web application, usable in desktop and phone browsers.

**Project Type**: Python/Streamlit application with a shared domain-data workspace package.

**Performance Goals**: No new provider-latency SLA. Chart rendering, detail reruns, and resizing
must not cause duplicate acquisition. A changed chart range may request missing history only as
an explicit user interaction, and must reuse a sufficient cached history where possible.

**Constraints**:

- Keep the current verified listing/issuer continuity checks, selected provider, source status,
  permissions, cache freshness, explicit load and actionable error behavior.
- The selected listing-history path currently defaults to a 550-calendar-day lookback and the
  chart renderer currently limits its visible rows to 260 sessions. Neither is sufficient for
  every requested 24-month view.
- The current normalized daily-history contract contains close and volume, while the existing
  consolidation contract requires adjusted OHLC and comparable volume. Do not infer open, high,
  or low from close; extend source mapping only with valid adjusted observations.
- For a detector result at the first displayed date, the consolidation contract needs 271 prior
  valid sessions for its preceding 252 valid 20-session bandwidth observations, which exceeds the
  150-session moving-average warm-up. Request that warm-up in addition to the selected visible
  range; insufficient or gapped history remains explicitly insufficient.
- Existing quarterly fundamentals support four-to-eight-quarter requests and have verified
  profile, identity, provenance, period, and partial/failure states. Current row mappings do not
  include every requested balance-sheet and share-count value; absent provider coverage remains
  unavailable rather than fabricated.
- No historical valuation snapshot may be inferred from today's market capitalization. Existing
  source-vintage limitations remain binding.
- Provider display and derived-data rights must be reviewed before results are published or hosted.

**Scale/Scope**: One explicitly selected, verified U.S. stock listing at a time; six visible chart
ranges from 1 to 24 months; 50- and 150-session simple moving averages; the existing consolidation
heuristic; latest eight comparable fiscal quarters; no new root tab, multi-stock batch, peer-score
formula, or persistent financial store.

## Constitution Check

### Initial Gate (before Phase 0)

| Principle or constraint | Status | Plan application |
|---|---|---|
| I. Keep It Simple | PASS | Extend the existing stock-detail workflow, chart evidence, and financial bundle; add no framework or provider. |
| II. Lean Delivery | PASS | Limit the change to the requested stock detail, its range/history support, and quarterly evidence. |
| III. YAGNI | PASS | Do not add a new score, forecast, company-research crawler, provider fallback, or persistent store. |
| IV. Avoid Waste | PASS | Request the selected range plus required warm-up only; use existing bounded caches and explicit loads. |
| V. Separation of Concerns | PASS | Keep provider normalization, domain indicators, and UI composition in their existing layers. |
| VI. High Cohesion, Low Coupling | PASS | Reuse narrow typed chart and evidence outcomes; do not make chart rendering own financial retrieval. |
| Python/Streamlit and navigation | PASS | Modify the existing native stock-detail surface; no new tab or navigation architecture. |
| Single provider, caching, permissions | PASS WITH RELEASE GATE | Reuse the selected yfinance path and existing cache/source checks. Confirm applicable display/derived-data rights before any public deployment. |
| Session state, data minimization, errors | PASS | Keep choices session-local; make coverage/failure explicit; do not substitute stale or alternate-provider data. |
| Responsive UI and validation | PASS | Define 1440px and 390px acceptance and validate the actual browser view, including chart and evidence access. |
| Test-first and documentation gates | PASS | Add controlled failing tests before implementation, then focused tests, static checks, and browser validation. |

No unresolved requirement is needed to begin design. The known source-data limitations are
handled as explicit insufficiency states and prerequisites, not as assumed coverage.

## Phase 0: Research Decisions

Research findings, rejected alternatives, and implementation constraints are recorded in
[research.md](research.md). The design reuses the ownership and calculation boundaries in
features 001, 002, 011, 014, and 015.

## Phase 1: Design & Contracts

- [Data model](data-model.md) defines selected detail context, daily history and overlays,
  consolidation evidence, company profile, financial observations, and metric states.
- [Stock detail UI contract](contracts/stock-detail-ui.md) defines the visible controls, history
  behavior, disclosure, responsive layout, and testable interactions.
- [Quickstart](quickstart.md) defines controlled automated and browser validation.
- No public HTTP API or new persistence format is introduced.

### Dependency and Implementation Boundaries

1. Reuse `load_selected_listing_history(...)`, `MarketDataProvider`, and
   `StockChartEvidence`; increase history coverage based on the selected visible range and
   required pre-range warm-up, without bypassing listing continuity or explicit-load safeguards.
2. Keep the 50/150 moving-average calculations in the domain chart-evidence boundary. Extend the
   daily-history contract with adjusted OHLC only where the provider supplies comparable values.
3. The detail chart consumes typed consolidation intervals from feature 001's
   `quiet-sideways-v1` detector. Feature 017 owns chart placement and detail display, not a second
   detector. If the detector is not available at implementation time, coordinate its completion
   with feature 001 before claiming consolidation support.
4. Reuse the current company-evidence loader and `FundamentalBundle`; extend explicitly mapped
   statement rows for cash, debt, equity, and shares where the selected source provides them.
   Preserve issuer verification, source rights, period/currency validation, and partial failures.
5. Reuse the metric semantics from feature 002 for existing scorecard metrics. Any additional
   history-only ratios are documented separately and never enter peer percentiles or alter the
   scorecard.
6. Preserve current stock identity, navigation, explicit load/refresh, peer scorecard, risk
   warnings, and evidence-provenance behavior.

### Project Structure

```text
packages/market-data/src/market_data/
├── domain/
│   ├── stock_chart.py                 # typed daily chart evidence and moving-average status
│   └── fundamentals.py                # quarterly bundle and established metric semantics
└── [existing provider/domain modules] # adjusted OHLC mapping and consolidation ownership

src/market_leadership/
├── application/
│   ├── load_stock_history.py          # verified listing-history request boundary
│   └── load_company_evidence.py       # verified financial-evidence request boundary
├── infrastructure/
│   └── yfinance_provider.py           # current selected daily-history provider
└── ui/
    ├── components/stock_detail.py     # existing stock-detail composition
    └── sector_chart.py                # existing aligned price/volume chart renderer

tests/
├── unit/                              # controlled chart, detector, and fundamental tests
├── integration/                       # provider normalization/cache tests
└── app/test_stock_detail.py           # root detail-flow regression and acceptance
```

**Structure Decision**: Use the existing multi-package layout: pure calculation and normalized
evidence belong in `packages/market-data`; application requests and provider mapping remain in
`src/market_leadership`; rendering stays in the existing stock-detail/chart UI; tests remain in
the current unit/integration/AppTest suites. Add only the narrow files required by feature 001's
detector dependency and this feature's tests/contracts.

## Post-Design Constitution Check

| Gate | Status | Evidence |
|---|---|---|
| Minimal change and reuse | PASS | No new app surface, provider, score, or durable store; existing detail/chart/evidence owners are retained. |
| Data minimization and caching | PASS | Query coverage is limited to the requested chart window plus stated indicator warm-up; explicit loads and existing cache identities are preserved. |
| Separation and typed boundaries | PASS | History, calculations, source normalization, consolidation intervals, and UI display remain separate. |
| Financial correctness and provenance | PASS | Existing 002/011 period, units, issuer, source, partial-coverage, and missingness contracts remain authoritative. |
| UI responsiveness and access | PASS | The contract includes narrow layouts, touch/keyboard access, and explicit non-hover evidence. |
| Verification quality | PASS | Tests cover exact period boundaries, warm-up/gap cases, data states, and 1440px/390px browser acceptance. |
| Rights and deployment | RELEASE GATE | Review provider terms and permitted display/derived uses before publishing or hosting; no permission is inferred by this plan. |
