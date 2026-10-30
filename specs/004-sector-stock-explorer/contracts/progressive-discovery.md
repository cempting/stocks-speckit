# Progressive Discovery UI Contract

## Root and stages

- Keep the current two root tabs: `Discovery` and `Industry Deep-Dive`.
- Discovery shows exactly one progressive tape at a time:
  - selected region with no sector selection: that region's sector performance;
  - valid sector selection: that region/classification's industry momentum;
  - valid industry selection: every active database member's stock tape, each security once;
  - selected stock: its detailed view, with a return action to the same valid discovery context.
- The initial region is US. When more than one region is populated, the user can select the region;
  all sectors, industries, stock memberships, and chart representations are scoped to it.
- Show the region's reviewed coverage scope, as-of date, and completeness state. Partial or
  unverified input must not be presented as complete regional coverage.
- Do not add a separate Fundamental Grading root tab or a route solely for stock details.
- A selected parent controls the visible child set. Clear invalid descendants before rendering
  their widgets, and explain when a selection was cleared.
- Sector, industry, stock, listing, membership, and chart-representation records come from the
  database. Missing or uninitialized database state has an actionable setup message, not a
  success-shaped empty tape.

## Row identity and contents

### Preserved presentation (2026-10-30)

- On wide screens, keep one row: active tape heading left, `Thumbnail period` middle,
  `Performance basis` right.
- Period options/default: `1w`, `1m`, `3m`, `6m`, `1y` / `3m`. Basis options/default:
  `Absolute`, `vs S&P 500` / `Absolute`. Choices survive hierarchy navigation; empty choices
  use defaults. Relative performance subtracts SPY's matching-period return.
- Column order: `Price + 50-session SMA`, `Volume by price direction`, `Sector`, `Ticker`,
  `1 week`, `1 month`, `3 months`, `6 months`, `12 months`, `Status`.
  Industry rows replace `Sector` with `Industry`; never revert `Ticker` to `Representation`.
- Both plots stay 84 pixels high. Their nominal width is 135, stretched to the containing
  cell. Price/SMA and volume remain separate adjacent charts.
- Both previews use the inclusive calendar window anchored at the selected as-of date,
  cropped after SMA/direction calculation. Period changes do not change return columns,
  latest stock price, stock-detail history, or membership. Empty windows stay unavailable.
- Preserve per-period/per-sign gain/loss intensity, readable light/dark palettes, neutral
  zero, and uncolored `Unavailable` for missing returns. Valid values remain right-aligned
  two-decimal percentages; chart rendering must not remove these colors.
- Preserve spec FR-032's explicit reviewed sector ETF mappings. They are chart proxies,
  not member-stock aggregates, and create no industry memberships. Missing/inactive mappings
  remain unavailable rather than borrowing another entity's chart.
- This accepted presentation requires explicit user approval and coordinated spec, plan,
  task, contract, and regression-evidence updates before intentional changes.

- The first column in each discovery tape contains that row's price chart with its 50-session
  moving average when 50 completed observations exist. The adjacent column contains the same
  row's volume chart for the same sessions.
- Volume bars are green when the close rose from the previous completed close, red when it fell,
  and neutral when unchanged or direction is unavailable. Label the colors as price-direction
  indications; they do not identify verified buyer/seller activity.
- Price and volume charts remain separate columns for sector, industry, and stock tapes. Missing
  price, volume, or moving-average evidence is identified in the corresponding chart cell.
- Every stock row contains price and volume charts, ticker/listing, name, latest valid price, and
  the Quality, Growth, and Cash Flow peer scores when available.
- Score blocks use the 001 peer-scoring contract, not the eight raw metrics as a proxy and not a
  new aggregate score. Each score is 0–100 or explicitly unavailable/insufficient/not loaded.
- Activating a stock row opens that same stable instrument identity. A changed ticker or display
  name must not redirect selection to a different security.
- Keep all active members in the row set. Do not silently drop stocks without history, scores, or
  complete facts; explain their data state.
- An unresolved placeholder may be present without a verified listing. Identify it as a
  placeholder and do not request market data for it.

## Data loading and provenance

- Selecting or rendering a table does not trigger a financial statement load.
- An explicit score-load action is required. Because scores are peer-relative, it loads the
  complete eligible industry cohort before display filtering and uses existing successful cache
  entries where valid.
- Stock price history is loaded only for verified listings in the active region/industry. Reuse
  that data for row thumbnails and the selected-stock detail chart.
- The sector, industry, and stock chart evidence must never be substituted across identities.
- Reviewed local files are authoritative for region, sector, industry, stock identity, and
  membership. Report live-source differences without overwriting local classifications.
- Show source, requested/observed session, membership date, and freshness where relevant. Errors,
  unsupported historical requests, and incomplete coverage are explicit and cannot appear as a
  successful empty result.

## Stock detail

- Identify the selected stock by its stable instrument ID and associated listings, not ticker
  alone.
- The chart includes that stock's price and volume and overlays 50- and 150-session simple moving
  averages when supported by its history.
- Mark each unavailable series as insufficient/unavailable; continue to show independent
  available series.
- Present the same three peer scores and evidence state used in the stock tape. No additional
  score or unspecified future detail is included.
- Returning to Discovery retains valid sector and industry selections and loaded data.

## Acceptance evidence

- Baseline: five exact calendar windows, both thumbnail branches at 84-pixel height,
  retained SMA warmup/direction, empty-window states, ordered labels, per-sign heatmap
  colors/formatting, persistent controls, and returns unchanged by preview selection.
- Wide-screen browser checks verify heading/control alignment and actual chart geometry.
  Track missing permanent coverage explicitly; manual checks are not automated tests.

- AppTest: initial state, each stage transition, parent invalidation, no stale rows, row-to-detail
  identity, region scoping, and return-context preservation.
- Database/import tests: multiple listings for one stock, unique region/industry membership,
  unresolved placeholders, rejected invalid imports, and live-source conflict reports that
  preserve reviewed local classifications.
- Domain tests: exact peer formulas/ranks/ties, five-peer boundary, insufficient metrics, and
  cutoff behavior against the referenced scoring contract.
- Integration tests: requested symbol set, cache reuse, explicit load behavior, partial provider
  failures, and provenance.
- Chart tests: row-specific series, exact 50/150-session calculations, direction/color mapping,
  and neutral/missing-volume cases; browser inspection verifies adjacent thumbnail placement in
  all three tapes and detail chart rendering.
