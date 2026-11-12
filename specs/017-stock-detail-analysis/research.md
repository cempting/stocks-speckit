# Stock Detail Analysis Research

## Decisions

### Extend the current stock-detail surface

**Decision**: Add range selection and additional chart/fundamental coverage to the existing detail
workflow. Keep existing identity, chart, moving-average status, peer scorecard, company-evidence
actions, navigation, and explicit-load safeguards.

**Rationale**: `render_stock_detail(...)` already composes verified listing identity, chart,
scorecard, and financial/research evidence. `build_stock_chart_evidence(...)` already truncates
history at the requested cutoff and reports available, insufficient, or unavailable moving
averages. `build_sector_chart(...)` already renders price, available averages, and aligned volume
in a vertically combined chart. The gap is coverage and user control: the renderer currently
shows at most 260 sessions, and no stock-detail range selector exposes the requested six horizons.

**Alternatives considered**: Create a second detail page, add a separate price/volume chart, or
recompute existing moving averages in the UI. These duplicate current behavior and weaken the
typed-data boundary.

### Request history for the selected range plus validated warm-up

**Decision**: Keep history retrieval behind the current explicit stock-history action. Request
only the selected chart range plus the earlier completed sessions needed for the moving averages
and detector; reuse a sufficient cached history when users change periods. Expand the current
550-calendar-day request limit as necessary for longer ranges.

**Rationale**: A 24-month visible window needs more than the current 550-calendar-day ceiling in
many cases. A 150-session moving average requires earlier observations than the visible range.
More importantly, the existing consolidation contract requires a preceding 252 valid BandWidth
observations, each with a 20-session window: detecting an interval at the first visible date can
require 271 valid prior sessions. Gaps, recent listings, and provider limits remain explicit
insufficiency rather than reasons to shorten the declared warm-up.

**Alternatives considered**: Fetch the full available history on every detail open, assume 550
calendar days covers 24 months and all warm-ups, or calculate indicators only from the visible
window. These choices either waste requests or produce incomplete/incorrect overlays.

### Reuse the stock-chart evidence and extend its source contract for consolidation

**Decision**: Keep simple moving-average calculations and availability states in
`StockChartEvidence`. Keep the consolidation algorithm owned by feature 001 and pass its typed
interval result to the detail chart. Extend the normalized daily-history contract to carry
adjusted OHLC plus comparable volume only when verified provider observations are available.
Never infer open, high, or low from close; if required fields are missing, consolidation is
insufficient.

**Rationale**: Feature 001's `quiet-sideways-v1` contract derives trend strength, volatility, and
the corridor from an instrument's own adjusted OHLC and volume. The current stock history contract
contains close and volume, which is not enough to compute true range, ATR, ADX, or observed
high/low corridor bounds. The feature 001 contract additionally requires cutoff isolation,
contiguous-session warm-up, explicit gaps, and non-predictive annotations.

**Alternatives considered**: A close-only range, a universal percentage corridor, fixed-duration
consolidation labels, or a duplicate stock-detail detector. Each conflicts with the existing
heuristic or misstates the available evidence.

**Dependency**: If the feature 001 detector has not been implemented when feature 017 is
implemented, coordinate its completion first. Feature 017 owns neither a new ruleset nor a
fallback detector.

### Reuse the verified quarterly evidence path and extend explicit row mappings

**Decision**: Continue using the current selected yfinance source, verified issuer-association
gate, `FundamentalBundle`, quarterly financial/cash-flow/balance-sheet tables, evidence
provenance, and explicit partial/failure states. Add only explicit row mappings required for cash
and equivalents, total debt, shareholders' equity, and shares outstanding when the selected
source provides them. Keep historical archive evidence on its existing path.

**Rationale**: `FundamentalRequest` already supports quarterly four-to-eight-quarter requests.
The existing bundle carries profile, market capitalization/date, issuer identity, currency, and
quarterly statement tables. The current row mapping already covers revenue, gross/operating
income, EBIT, net income, diluted EPS, operating cash flow, capex, FCF, total assets, and current
liabilities. The missing balance-sheet and share-count rows must be mapped deliberately. The
company-evidence loader already enforces issuer continuity, source assessment, provenance, and
partial/error reporting.

**Alternatives considered**: Fetch profile data from a second website, attach facts by matching
ticker/name alone, use scraped company pages, or replace missing data with estimates. These
conflict with the provider and identity safeguards and could silently attach another issuer's
facts.

### Preserve established metric definitions and isolate new ratio context

**Decision**: Reuse feature 002's defined gross margin, operating margin, sales YoY, diluted-EPS
YoY, FCF margin, and ROCE semantics. For new history-only context, define net margin as quarterly
net income divided by quarterly revenue, current ratio as quarter-end current assets divided by
current liabilities, and debt-to-equity as quarter-end total debt divided by shareholders'
equity; require compatible dates, currency, and valid denominators. Do not feed any added ratio
into peer percentiles or the existing scorecard.

**Rationale**: Existing raw metrics and score components have separate, approved ownership and
definitions. The additional ratios provide profit, liquidity, and leverage context without
changing score meaning. The quarterly observation data model distinguishes reported values,
derived values, fiscal basis, publication/observation dates, and unavailable reasons.

**Alternatives considered**: Reusing current market multiples as quarterly metrics, deriving
ratios from incompatible statement periods, or treating a peer percentile as an absolute
financial-health threshold. These imply unsupported comparability or alter existing score
semantics.

### Keep valuation multiples as dated, optional snapshots

**Decision**: Display P/E, P/S, EV/EBITDA, or FCF yield only when source values and inputs have
compatible dates and currencies, and label them as latest valuation context rather than quarterly
operating history. Otherwise show them as unavailable or omit the unsupported value.

**Rationale**: Current company market capitalization and profile data are not a verified historical
market-value series. Existing score research also identifies unavailable publication vintages or
matching dated market capitalization as a reason not to fabricate point-in-time peer values.

**Alternatives considered**: Apply today's market capitalization to past quarters or imply
historical comparability from an undated current profile. Both introduce look-ahead or misleading
valuation context.

### Use the existing Streamlit and test architecture

**Decision**: Keep the six range choices in the existing stock detail with a namespaced,
session-local selection; use the existing chart renderer and native UI patterns. Test calculation
and provider normalization with deterministic fixtures, then verify the complete stock-detail
flow at 1440px and 390px.

**Rationale**: The application already uses Python 3.12, Streamlit, Altair, pandas, a typed market
data package, pytest/AppTest, Ruff, and strict Pyright. The constitution requires phone/desktop
browser checks for UI work and bars extra navigation frameworks, data providers, and unmeasured
optimizations.

**Alternatives considered**: Add a charting dependency, create parallel mobile/desktop widgets,
or rely on AppTest alone for responsive acceptance. None is needed and the last does not prove
browser layout or touch/keyboard access.

## Repository Evidence

- [Stock detail](../../src/market_leadership/ui/components/stock_detail.py) already renders the
  selected listing, stock chart, peer scorecard, and financial/company evidence.
- [Stock chart evidence](../../packages/market-data/src/market_data/domain/stock_chart.py)
  centralizes cutoff handling and SMA availability.
- [History loader](../../src/market_leadership/application/load_stock_history.py) preserves
  verified listing/issuer continuity and explicit date eligibility.
- [Chart renderer](../../src/market_leadership/ui/sector_chart.py) combines price, available
  averages, and aligned volume but currently truncates its plotted history.
- [Fundamentals model](../../packages/market-data/src/market_data/domain/fundamentals.py) and
  [financial metric contract](../../specs/002-fundamental-grading-layout/contracts/fundamental-data.md)
  define quarterly requests, established formulas, and coverage constraints.
- [Company evidence loader](../../src/market_leadership/application/load_company_evidence.py)
  and [company evidence contract](../../specs/011-company-risk-evidence/contracts/company-evidence-acquisition.md)
  govern issuer checks, source assessment, provenance, cache behavior, and partial failures.
- [Consolidation contract](../../specs/001-market-leadership-screener/contracts/consolidation.md)
  is authoritative for the versioned detection rules and chart annotation.
