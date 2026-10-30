# Data Model: Sector-to-Stock Explorer

These are in-memory application records and view projections, not a new persistence schema.
Reuse existing sector, industry, membership, market-history, and fundamental records wherever
their contracts match. All cached source results remain independent of user selections.

## Identity and Selection

### ProgressiveSelection

Fields: `sector_id?`, `industry_id?`, `instrument_id?`, `catalog_fingerprint?`,
`membership_date?`, `observation_date?`.

Invariants:

- Every non-null child ID belongs to the selected parent in the active dated catalog.
- Sector, industry, and instrument IDs are stable identities; names and tickers are display
  values, not keys.
- State lives in namespaced `st.session_state`; no selection is stored in shared cached results.
- Changing sector clears industry and instrument selections unless they are still valid under the
  new scope. Changing industry clears the stock/detail selection unless the instrument remains a
  member. Opening/closing a detail view preserves valid parent context.
- Catalog fingerprint/date changes invalidate dependent membership and score evidence. The UI
  reports the change instead of displaying stale rows.

### VisibleStage

Values: `sectors`, `industries`, `stocks`, `stock_detail`.

Transitions: initial state -> `sectors`; valid sector selection -> `industries`; valid industry
selection -> `stocks`; valid instrument selection -> `stock_detail`; return action -> the prior
valid stage. A child stage without a valid parent is not rendered.

## Tape Projections

### SectorTapeRow

Fields: `sector_id`, `name`, `symbol`, `performance`, `observation_date`, `source_evidence`,
`chart_series`, `chart_state`.

Validation: performance and chart evidence come from the sector's own eligible history.
Unavailable or stale observations remain explicitly identified; another sector's observations
are never used.

### IndustryTapeRow

Fields: `industry_id`, `parent_sector_id`, `name`, `representation_id`, `performance`,
`observation_date`, `source_evidence`, `chart_series`, `chart_state`.

Validation: the row's parent matches the selected sector at the relevant classification date.
Industry performance and chart evidence use the documented industry representation, not the
parent sector's observations. A missing qualified representation/history is insufficient.

### StockTapeRow

Fields: `instrument_id`, `industry_id`, `ticker`, `name`, `price?`, `price_date?`,
`price_source`, `chart_series`, `chart_state`, `quality_score`, `growth_score`,
`cash_flow_score`, `score_state`, `score_reason?`.

Score fields: each available block score is a finite value from 0 to 100. Unavailable scores
carry an explicit state such as `not_loaded`, `insufficient`, or `error`; they are not zero.
The cohort and metric formulas are defined by the existing
[fundamental scoring contract](../001-market-leadership-screener/contracts/fundamental-scoring.md).
All active catalog members are represented, even if price or score evidence is unavailable.

Validation:

- Stock identity and parent membership match the current catalog fingerprint and date.
- Price and chart series use only the stock's own validated history and selected observation
  cutoff.
- No score is calculated from a partial/display-only cohort, an invalid denominator, an
  unverified vintage, or fewer than five valid peer observations for a metric.

## Evidence

### PriceHistory

Reuse the current canonical daily history keyed by `instrument_id`/provider symbol and session.
The displayed entity's series is ordered, has unique completed sessions, finite positive prices,
and nonnegative volume. Preserve requested and observed dates, provider, freshness, and any
validation or coverage state.

Stock histories are requested only after selecting an industry and only for its active member
symbols. The same validated per-stock history supplies the stock thumbnail, latest displayed
price, and selected-stock detail chart.

### StockChartEvidence

Fields: `instrument_id`, `sessions`, `price`, `volume`, `sma50?`, `sma150?`,
`price_state`, `volume_state`, `sma50_state`, `sma150_state`, `observation_date`,
`source_evidence`.

Rules: moving averages use completed-session simple means over exactly 50 and 150 observations.
Insufficient history is represented per series, not as zero and not as a fabricated chart.
Price, volume, and moving averages all come from the same stock history.

### PeerBlockScore

Fields: `instrument_id`, `block` (`Quality | Growth | Cash Flow`), `value?`,
`state`, `valid_peer_count`, `analysis_cutoff`, `metric_evidence`, `source_evidence`,
`reason_codes`.

Rules: formulas, exact ranking, tie handling, cohort selection, and minimum count are owned by
the 001 contract. Both metrics in a block are required. Keep full precision for ranking and
round only for presentation. Peer cohort is the complete eligible industry membership before
technical filters, display selection, paging, or sorting. Evidence unavailable at the requested
cutoff is insufficient. No overall score is defined.

## State and Failure Semantics

Data load states distinguish `not_loaded`, `loading`, `available`, `partial`, `insufficient`,
`stale`, and `error`. Empty membership is different from an unavailable/invalid catalog. Remote
failures remain observable and are never cached as successful empty data. Independent valid rows
remain visible when a sibling stock fails.
