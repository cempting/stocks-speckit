# Implementation Plan: Fundamental Grading Layout

**Reconciled**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Scope and Ownership

002 owns the three-column/eight-metric fundamental matrix, adjacent commentary,
EPS consistency and actual quarterly history on existing stock surfaces.
Navigation follows 004/015; retain Discovery, Industry Deep-Dive, Yahoo
Classification Preview and Find a stock. No separate grading tab, old routed
workflow, fixture runtime mode or obsolete multi-sector control is authorized.
Catalog/membership follows 010/012; shared service context follows 013 on adoption.

The obsolete three-tab/database/fixture foundation plan has been removed.
[Tasks](tasks.md) retain completed T001-T004 and explicitly superseded, not
completed, T005-T008. Historical completion does not authorize replaying the old
foundation or prove current migration/source permissions.

## Technical Context and Data Flow

- Reuse the existing Python/Streamlit/yfinance workspace and constrained lockfile;
  this plan adds no dependency, source, storage system or parallel runtime.
- Pure financial records/calculations belong in
  `packages/market-data/src/market_data/domain/`. Acquisition, cache and rendering
  remain in `src/market_leadership/`; do not recreate moved domain modules.
- One injected Ticker reader obtains `.info`, `.quarterly_financials`,
  `.quarterly_cashflow` and `.quarterly_balance_sheet`. A Ticker object does not
  imply one HTTP request. Bounded retries and component failures stay explicit.
- Follow [fundamental-data](contracts/fundamental-data.md) for all eight formulas,
  units, periods and publication/source limitations. Cash Conversion uses
  quarterly OCF / positive net income; YoY requires a positive prior-year baseline;
  ROCE uses four-quarter EBIT / quarter-end capital employed.
- Key successful financial bundles by provider, symbol, cutoff/window, quarterly
  frequency and bundle schema version. Retain the one-hour/256-entry bound and
  targeted explicit refresh. User selections and errors are not shared cache data.
- Entirely empty or failed components are ambiguous acquisition outcomes, not
  successful missing-data bundles. Surface structured errors and any safe partial
  evidence without caching the failure as success.
- Preserve current identity/listing verification, source/display permissions and
  explicit load actions. Eager tab rendering does not authorize acquisition.
  Test fixtures are controlled inputs, not evidence of live coverage or rights.

## Protected Matrix Presentation

Follow [fundamental-ui](contracts/fundamental-ui.md):

- One `st.columns(3)` per stock, Quality/Growth/Cash Flow in 3/3/2 grouping.
- Each slot retains label, value and immediately adjacent metric-specific or
  neutral commentary. Missing metrics do not erase valid neighbors or headings.
- Preserve valid zero/negative values and exact fallback pairs. EPS Consistency
  requires eight real comparable quarters and valid counts from zero through eight.
- Native bar charts follow commentary, remain 60 pixels high and show four to
  eight actual chronological comparable observations. Below four, show
  `Insufficient quarterly history`; do not pad, interpolate or invent quarters.
- Do not redefine 001 component formulas, 006 Total Score or 011 warnings.
  Score-methodology changes remain subject to 014's evidence and approval.

## Execution and Validation

The original T001-T004 evidence remains in [tasks](tasks.md); there is no executable
T005-T008 dependency chain. Future accepted changes need current tests before
implementation, not restoration of the historical foundation.
Use existing formula, fake-Ticker, cache and AppTest coverage to distinguish complete,
partial, missing, failing and unsupported historical cases. Verify exact chart
shape/order/count, context invalidation, cache isolation and zero hidden acquisition.
Run the affected selectors and existing Ruff/strict Pyright gates; live checks are
optional and permission-gated. See [quickstart](quickstart.md).

## Constitution and Complexity

Reuse existing pure/application/UI boundaries, one live source, explicit failures,
private state and reviewed catalog/permission gates. No new architecture or exception
is requested. The existing fourth-tab exception remains owned by 015 under
[issue #2](https://github.com/cempting/stocks-speckit/issues/2).
Documentation cleanup neither changes app styling nor certifies implementation.
