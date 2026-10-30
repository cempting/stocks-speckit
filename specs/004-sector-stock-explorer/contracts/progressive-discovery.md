# Progressive Discovery UI Contract

## Root and stages

- Keep the current two root tabs: `Discovery` and `Industry Deep-Dive`.
- Discovery shows exactly one progressive tape at a time:
  - no sector selection: sector performance;
  - valid sector selection: that sector's industry momentum;
  - valid industry selection: every active catalog member's stock tape;
  - selected stock: its detailed view, with a return action to the same valid discovery context.
- Do not add a separate Fundamental Grading root tab or a route solely for stock details.
- A selected parent controls the visible child set. Clear invalid descendants before rendering
  their widgets, and explain when a selection was cleared.

## Row identity and contents

- The first column in sector and industry tapes contains a compact chart for that row's own
  entity/history.
- Every stock row contains a compact chart for that stock, ticker, name, latest valid price, and
  the Quality, Growth, and Cash Flow peer scores when available.
- Score blocks use the 001 peer-scoring contract, not the eight raw metrics as a proxy and not a
  new aggregate score. Each score is 0–100 or explicitly unavailable/insufficient/not loaded.
- Activating a stock row opens that same stable instrument identity. A changed ticker or display
  name must not redirect selection to a different security.
- Keep all active members in the row set. Do not silently drop stocks without history, scores, or
  complete facts; explain their data state.

## Data loading and provenance

- Selecting or rendering a table does not trigger a financial statement load.
- An explicit score-load action is required. Because scores are peer-relative, it loads the
  complete eligible industry cohort before display filtering and uses existing successful cache
  entries where valid.
- Stock price history is loaded only for the active selected industry's members. Reuse that data
  for row thumbnails and the selected-stock detail chart.
- The sector, industry, and stock chart evidence must never be substituted across identities.
- Show source, requested/observed session, membership date, and freshness where relevant. Errors,
  unsupported historical requests, and incomplete coverage are explicit and cannot appear as a
  successful empty result.

## Stock detail

- Identify the selected stock by ticker and name, backed by its stable instrument ID.
- The chart includes that stock's price and volume and overlays 50- and 150-session simple moving
  averages when supported by its history.
- Mark each unavailable series as insufficient/unavailable; continue to show independent
  available series.
- Present the same three peer scores and evidence state used in the stock tape. No additional
  score or unspecified future detail is included.
- Returning to Discovery retains valid sector and industry selections and loaded data.

## Acceptance evidence

- AppTest: initial state, each stage transition, parent invalidation, no stale rows, row-to-detail
  identity, and return-context preservation.
- Domain tests: exact peer formulas/ranks/ties, five-peer boundary, insufficient metrics, and
  cutoff behavior against the referenced scoring contract.
- Integration tests: requested symbol set, cache reuse, explicit load behavior, partial provider
  failures, and provenance.
- Chart tests: row-specific series and exact 50/150-session calculations; browser inspection
  verifies actual thumbnail placement and detail chart rendering.
