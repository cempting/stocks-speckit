# Feature Specification: Sector-to-Stock Explorer

**Feature Branch**: `004-sector-stock-explorer`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "1. when no sector is selected, the app show the sector tape
2. if a sector is selected the app shows the industries tape, the sector tape is no longer shown
3. if an indiustry is selected the app shows the stocks tape of all contained stocks in the industrs
4. the sector performce shall contain a thumbnails of the aector chart at the first column
5. the industry momentum shall contain a thumbnails of the industry chart at the first column
6. the contained stocks view shows a thumbnail chart, ticker, name, price, score
7. the user may click on a stock and the will jump into a detailed stock view page
8. the detailed stock view page contains chart (price, volume, 50SMA, 150 SMA) scoreboard , further things to come"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explore Market Leadership by Hierarchy (Priority: P1)

As an investor, I want the discovery view to show sectors first, then industries for my selected
sector, then the sector's stocks for my selected industry, so I can move from broad performance
to individual opportunities without unrelated levels competing for attention.

**Why this priority**: The ordered views are the core discovery journey and define what users see
at each point in their exploration.

**Independent Test**: Provide a market with sectors, industries, and member stocks; verify the
visible tape and its rows at each selection state, including that changing a parent removes stale
child selections.

**Acceptance Scenarios**:

1. **Given** no sector is selected, **When** the user opens discovery, **Then** the sector
   performance tape is visible and the industry and stock tapes are not.
2. **Given** a sector is selected, **When** discovery updates, **Then** its industry momentum tape
   replaces the sector tape, contains only industries belonging to that sector, and the stock tape
   is not visible until an industry is selected.
3. **Given** an industry is selected, **When** discovery updates, **Then** the contained-stocks
   tape replaces the industry tape and includes all available stocks belonging to that industry.
4. **Given** a selected sector or industry changes, **When** the dependent view updates, **Then**
   selections that do not belong to the new parent are cleared and no stale rows remain visible.

### User Story 2 - Compare Sector, Industry, and Stock Evidence (Priority: P1)

As an investor, I want compact charts beside the performance data at each discovery level, so I
can visually assess trend context while comparing sectors, industries, and their stocks.

**Why this priority**: A chart preview makes the performance tapes useful for visual screening
without requiring a separate chart visit for every row.

**Independent Test**: Display controlled sector, industry, and stock price histories and verify
each tape's first column contains a chart for the same entity as its row and the stock rows show
the requested identifying and performance information.

**Acceptance Scenarios**:

1. **Given** sector performance rows, **When** the sector tape is displayed, **Then** its first
   column contains a thumbnail chart for each corresponding sector.
2. **Given** industry momentum rows, **When** the industry tape is displayed, **Then** its first
   column contains a thumbnail chart for each corresponding industry.
3. **Given** an industry with available member stocks, **When** the contained-stocks tape is
   displayed, **Then** each row shows a chart thumbnail, ticker, name, price, and its Quality,
   Growth, and Cash Flow scores where available.
4. **Given** a row whose chart or price evidence is unavailable, **When** its tape is displayed,
   **Then** the unavailable evidence is identified and is not presented as valid data.

### User Story 3 - Inspect an Individual Stock (Priority: P2)

As an investor, I want to open a detailed view for a stock from its tape, so I can inspect its
price and volume history, moving averages, and score information together.

**Why this priority**: Individual inspection completes the discovery journey after a stock has
been identified in its industry.

**Independent Test**: Select a stock from a controlled stock tape and verify the resulting detail
view identifies that stock and presents its price/volume chart, 50-session and 150-session
simple moving averages, and scorecard information.

**Acceptance Scenarios**:

1. **Given** a stock appears in the contained-stocks tape, **When** the user activates that stock,
   **Then** the detailed stock view opens for the same ticker and name.
2. **Given** the detailed stock view has adequate observations, **When** it is displayed,
   **Then** its chart presents price, volume, 50-session simple moving average, and 150-session
   simple moving average.
3. **Given** a stock's existing financial scorecards are available, **When** its detail view is
   displayed, **Then** it presents the Quality, Growth, and Cash Flow scorecards without adding
   an overall score not defined by the existing scoring requirements.
4. **Given** required chart or score evidence is missing or insufficient, **When** the detail view
   is displayed, **Then** the affected evidence is marked unavailable or insufficient rather than
   estimated.
5. **Given** the user returns from a stock detail view, **When** the discovery view is restored,
   **Then** the prior sector, industry, and tape context is preserved when still valid.

### Edge Cases

- A selected sector with no eligible industries shows an empty-state explanation and retains the
  sector selection.
- A selected industry with no available member stocks shows an empty-state explanation and does
  not retain an invalid stock selection.
- A stock with insufficient history for either moving average still shows available price and
  volume evidence and identifies the unavailable average.
- Missing chart history, price, or score evidence is not replaced with a chart or value from a
  different entity.
- A stock's ticker or name is not unique or changes over time; the detail view remains associated
  with the selected stock identity rather than a different row.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When no sector is selected, the discovery view MUST show the sector performance
  tape and MUST NOT show the industry or stock tape.
- **FR-002**: When a sector is selected, the discovery view MUST replace the sector performance
  tape with an industry momentum tape containing only industries in that sector.
- **FR-003**: When an industry is selected, the discovery view MUST replace the industry momentum
  tape with a contained-stocks tape containing all available stocks in that industry.
- **FR-004**: A user MUST be able to select a sector and an industry from their respective tapes.
  Changing a parent selection MUST clear any dependent selection that is no longer valid.
- **FR-005**: The first column of every sector performance row MUST contain a thumbnail chart for
  that sector.
- **FR-006**: The first column of every industry momentum row MUST contain a thumbnail chart for
  that industry.
- **FR-007**: Each contained-stock row MUST show a thumbnail chart, ticker, name, price, and the
  existing Quality, Growth, and Cash Flow scores where available. It MUST NOT show a newly
  calculated aggregate score.
- **FR-008**: Activating a stock row MUST open a detailed view for that same stock.
- **FR-009**: The detailed stock view MUST provide a chart containing price, volume, 50-session
  simple moving average, and 150-session simple moving average, when each measure has sufficient
  observations.
- **FR-010**: The detailed stock view MUST present the stock's existing Quality, Growth, and Cash
  Flow scorecards where available. It MUST NOT invent an overall score.
- **FR-011**: The detail view MUST distinguish unavailable or insufficient data from valid
  observations and MUST NOT substitute evidence from another security.
- **FR-012**: Returning to discovery from a stock detail view MUST preserve the prior valid
  selection context.
- **FR-013**: Empty sector, industry, and stock results MUST be communicated without showing
  stale rows or fabricated chart and score values.

### Key Entities *(include if feature involves data)*

- **Sector**: A market grouping with an identity, performance observations, and chart history.
- **Industry**: A classified group belonging to a sector, with momentum observations and its own
  chart history.
- **Stock**: A uniquely identified security belonging to an industry, with ticker, name, price,
  chart history, and available score information.
- **Selection Context**: The currently selected sector, industry, and stock that determine which
  tape or detail view is displayed.
- **Scorecard**: An existing stock assessment consisting of Quality, Growth, and Cash Flow
  scores, with its underlying availability and sufficiency information.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all controlled hierarchy cases, 100% of states show only the tape appropriate to
  the current sector and industry selections, with no rows from an invalidated parent context.
- **SC-002**: In controlled data, 100% of sector and industry rows show their own chart thumbnail
  in the first column, and 100% of stock rows show the required thumbnail, ticker, name, price,
  and existing Quality, Growth, and Cash Flow scores where available.
- **SC-003**: At least 90% of first-time test users can move from the sector tape to a selected
  stock's detail view and identify its industry within 60 seconds.
- **SC-004**: For every stock with sufficient history, the detail view identifies price, volume,
  and both requested moving averages; 100% of unavailable measures in controlled cases are
  explicitly identified as unavailable or insufficient.
- **SC-005**: At least 90% of test users can return from stock detail to the same valid discovery
  context without repeating their sector and industry selections.

## Assumptions

- The hierarchy is a single-selection path: at most one sector and one industry define the next
  tape at a time.
- Selecting an industry replaces the industry tape with its stocks; the user can return to the
  industry tape through the existing navigation or by clearing the industry selection.
- "Thumbnail chart" means a compact visual preview of that row's own historical chart; detailed
  chart-analysis criteria remain those defined by the existing sector and industry requirements.
- "Scoreboard" refers to the project's existing Quality, Growth, and Cash Flow stock scorecards.
  The stock tape shows all three scores where available, not a new aggregate score or a single
  selected scorecard dimension.
- The stock detail chart uses completed price and volume observations and the project's existing
  data freshness and insufficiency disclosures.
- This feature adds progressive views and stock detail to the existing market discovery
  experience; alerts, recommendations, trading, and additional detail-page sections are out of
  scope until separately specified.
- The existing market/industry classification, stock membership, scorecard, and chart-analysis
  requirements remain the authority for their respective data and calculations.
