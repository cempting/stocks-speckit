# Feature Specification: Sector-to-Stock Explorer

**Feature Branch**: `004-sector-stock-explorer`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Show progressive sector, industry, and stock tapes with chart
thumbnails and a detailed stock view; add a 50-simple moveing average to price thumbnails and an
adjacent, separate volume-chart column with directional green and red bars."

Original feature description: "1. when no sector is selected, the app show the sector tape
2. if a sector is selected the app shows the industries tape, the sector tape is no longer shown
3. if an indiustry is selected the app shows the stocks tape of all contained stocks in the industrs
4. the sector performce shall contain a thumbnails of the aector chart at the first column
5. the industry momentum shall contain a thumbnails of the industry chart at the first column
6. the contained stocks view shows a thumbnail chart, ticker, name, price, score
7. the user may click on a stock and the will jump into a detailed stock view page
8. the detailed stock view page contains chart (price, volume, 50SMA, 150 SMA) scoreboard , further things to come"

## Clarifications

### Session 2026-10-30

- Q: What should the spec define as the fix when an industry is selected but no stock membership catalog is configured? → A: Maintain a database and tooling to create and populate region, sector, industry, and stock records; start with the US region while allowing future regions with classifications that do not use GICS, and make membership filterable by sector and industry.
- Q: How should the data-management tooling populate and refresh the initial US region? → A: Support both reviewed local-file imports and refreshes from one approved live source, and assess the existing local sector-rotation resources as a candidate for initial data.
- Q: How should the existing US ticker lists be represented when seeding the database? → A: Treat US as one region, combine its stock records across exchanges, and retain each exchange as a listing of the stock rather than a separate universe.
- Q: How should the app choose among separate named US universes before sector and industry filtering? → A: Scope discovery by region instead of named index universes; the initial US region includes stocks listed across its exchanges.
- Q: What should the data-management tooling do when local files and the approved live source disagree about a stock's region, sector, or industry? → A: Treat reviewed local files as authoritative for those classifications and report live-source differences without overwriting them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explore Market Leadership by Hierarchy (Priority: P1)

As an investor, I want the discovery view to show sectors first, then industries for my selected
sector, then the sector's stocks for my selected industry within a region, so I can move from
broad performance to individual opportunities without unrelated levels competing for attention.

**Why this priority**: The ordered views are the core discovery journey and define what users see
at each point in their exploration.

**Independent Test**: Provide a region with sectors, industries, and member stocks; verify the
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
5. **Given** the US region contains stock records associated with industries, **When** the user
   selects an industry, **Then** the stock tape includes every stock associated with that
   industry in the region and excludes stocks from other industries or regions.
6. **Given** more than one region is available, **When** the user selects a region, **Then** all
   sector, industry, and stock results are limited to that region.
7. **Given** reviewed local files contain multiple exchange listings for one security, **When**
   those files are imported, **Then** the database stores one stock identity with its distinct
   listings and industry filtering returns that stock only once.
8. **Given** an imported member has no verified tradable listing, **When** the user selects its
   industry, **Then** the stock remains identifiable as an unresolved placeholder and no live
   market-data request is made for it.
9. **Given** a live refresh disagrees with locally reviewed classification or membership,
   **When** the refresh completes, **Then** it reports the difference without overwriting the
   local values.
10. **Given** the database is missing or has no reviewed US data, **When** the user opens
    Discovery, **Then** the app explains how to initialize and populate it rather than reporting
    a valid empty industry or asking for `STOCK_MEMBERSHIP_CATALOG`.
11. **Given** two local source files disagree about the same stock's classification or
    membership, **When** the import is validated, **Then** the discrepancy is reported and the
    importer does not silently select one source's value.
12. **Given** the selected region's reviewed source data is partial or unverified, **When**
    Discovery is displayed, **Then** its coverage status is visible and the app does not claim the
    results include all stocks in that region.

### User Story 2 - Compare Sector, Industry, and Stock Evidence (Priority: P1)

As an investor, I want compact charts beside the performance data at each discovery level, so I
can visually assess trend context while comparing sectors, industries, and their stocks.

**Why this priority**: A chart preview makes the performance tapes useful for visual screening
without requiring a separate chart visit for every row.

**Independent Test**: Display controlled sector, industry, and stock price and volume histories
and verify each tape's price thumbnail and adjacent volume thumbnail match the same entity, show
the 50-session average when enough history exists, and use the required directional bar colors.

**Acceptance Scenarios**:

1. **Given** sector performance rows, **When** the sector tape is displayed, **Then** its first
   column contains a price-chart thumbnail for each corresponding sector, including its
   50-session average when sufficient history exists, and the next column contains that sector's
   volume-chart thumbnail.
2. **Given** industry momentum rows, **When** the industry tape is displayed, **Then** its first
   column contains a price-chart thumbnail for each corresponding industry, including its
   50-session average when sufficient history exists, and the next column contains that
   industry's volume-chart thumbnail.
3. **Given** an industry with available member stocks, **When** the contained-stocks tape is
   displayed, **Then** each row shows a price-chart thumbnail, an adjacent volume-chart
   thumbnail, ticker, name, price, and its Quality, Growth, and Cash Flow scores where available.
   The price thumbnail includes its 50-session average when sufficient history exists.
4. **Given** a row with volume and price-direction observations, **When** its volume thumbnail is
   displayed, **Then** volume bars for up sessions are green and bars for down sessions are red.
   A bar is neutral when the price is unchanged or its direction cannot be determined, and the
   chart identifies these colors as directional indications.
5. **Given** a row whose chart, price, volume, or moving-average evidence is unavailable or
   insufficient, **When** its tape is displayed, **Then** the affected evidence is identified
   and is not presented as valid data.

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
- A sector, industry, or stock with insufficient price history for the 50-session average still
  shows its available price thumbnail and identifies the average as unavailable.
- A row without usable volume observations shows an unavailable-volume indication in the volume
  column rather than an empty or misleading chart.
- A volume bar is neutral when the price is unchanged or a prior closing price is unavailable;
  green and red bars indicate price direction between consecutive observations, not verified
  buyer and seller identities.
- Missing chart history, price, or score evidence is not replaced with a chart or value from a
  different entity.
- A stock's ticker or name is not unique or changes over time; the detail view remains associated
  with the selected stock identity rather than a different row.
- A stock record without a verified tradable listing remains identifiable as an unresolved
  placeholder and does not trigger a market-data request.
- Local source files or live-source records with incomplete or invalid membership data are not
  treated as a complete, successful market-universe update.
- A live source that disagrees with a reviewed local classification is reported and does not
  silently overwrite the local region, sector, industry, or membership.
- Local source files that disagree about one stock's classification or membership are reported
  for review rather than silently resolved by source priority.
- A missing database or an unpopulated US region shows an actionable setup explanation and is not
  presented as a valid empty market.
- A region whose sources are partial or unverified shows its coverage scope and status instead of
  implying that its industry results contain every stock in that region.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Within the selected region, when no sector is selected, the discovery view MUST show
  the sector performance tape and MUST NOT show the industry or stock tape.
- **FR-002**: When a sector is selected, the discovery view MUST replace the sector performance
  tape with an industry momentum tape containing only industries in that sector.
- **FR-003**: When an industry is selected, the discovery view MUST replace the industry momentum
  tape with a contained-stocks tape containing all available stocks in that industry.
- **FR-004**: A user MUST be able to select a supported region, sector, and industry from their
  respective controls or tapes. Changing a parent selection MUST clear any dependent selection
  that is no longer valid.
- **FR-005**: The first column of every sector performance row MUST contain a price-chart
  thumbnail for that sector, including its 50-session simple moving average when sufficient price
  history exists.
- **FR-006**: The first column of every industry momentum row MUST contain a price-chart
  thumbnail for that industry, including its 50-session simple moving average when sufficient
  price history exists.
- **FR-007**: Each contained-stock row MUST show a price-chart thumbnail including its 50-session
  simple moving average when sufficient price history exists, ticker, name, price, and the
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
- **FR-014**: Region, classification, sector, industry, stock, stock-listing,
  stock-to-industry membership, and sector/industry chart-representation records MUST be
  maintained in a database and MUST be creatable and populatable through data-management tooling
  rather than hard-coded application configuration.
- **FR-015**: The initial populated region MUST be the US, combining stock records across its
  exchange listings rather than treating each exchange or index list as a separate region. The
  data model MUST support additional regions and classification systems without requiring those
  systems to use GICS.
- **FR-016**: Industry filtering MUST use the selected region and industry identity to return
  every associated stock in that region exactly once, without including stocks from another
  industry or region.
- **FR-017**: Every discovery table MUST include a separate volume-chart thumbnail column
  immediately next to the price-chart thumbnail column. Each volume thumbnail MUST represent the
  same entity as its row; unavailable volume evidence MUST be identified.
- **FR-018**: Volume-chart bars MUST be green when the corresponding observation's price closes
  above the prior observation's close, red when it closes below, and neutral when unchanged or
  when direction cannot be determined. Each volume chart MUST identify these colors as
  price-direction indications, not verified identification of individual buys or sells.
- **FR-019**: When a row lacks sufficient price history for its 50-session simple moving average,
  the price thumbnail MUST identify the average as unavailable or insufficient without hiding
  available price evidence.
- **FR-020**: Data-management tooling MUST support importing reviewed local data files as the
  authority for region, sector, industry, stock identity, and membership, and refreshing records
  from the application's single live-data provider after its US coverage, terms, and display
  rights have been reviewed. Live-source differences MUST be reported and MUST NOT silently
  overwrite locally reviewed classifications or membership. Existing local sector-rotation
  resources MUST be assessed as a candidate source for the initial import.
- **FR-021**: The database MUST support unresolved stock placeholders with region and industry
  membership but no verified listing. A placeholder MUST be identified as unresolved, remain
  distinguishable from a live-data failure, and MUST NOT trigger market-data requests until a
  verified listing is associated with it.
- **FR-022**: When the database is missing, invalid, or has no reviewed US data, the app MUST show
  an actionable initialization/import message and MUST NOT present the state as a valid empty
  market or require `STOCK_MEMBERSHIP_CATALOG`.
- **FR-023**: Data-management tooling MUST report conflicts between local source files and MUST
  NOT resolve conflicting region, sector, industry, or membership values by implicit source
  priority.
- **FR-024**: Discovery MUST show each region's reviewed coverage scope, as-of date, and
  completeness state (`complete`, `partial`, or `unverified`) and MUST NOT describe partial or
  unverified results as all stocks in that region.

### Key Entities *(include if feature involves data)*

- **Sector**: A market grouping with an identity, performance observations, and chart history.
- **Industry**: A classified group belonging to a sector, with momentum observations and its own
  chart history.
- **Stock**: A uniquely identified security with a name, zero or more verified exchange listings,
  industry membership, price, chart history, and available score information; an unresolved stock
  may have no listing.
- **Region**: A geographic stock universe such as the US, Europe, or Asia; the initial populated
  region is the US and carries reviewed coverage scope, as-of date, and completeness state.
- **Classification System**: The market-specific scheme used to identify and relate sectors and
  industries; it is not assumed to be GICS.
- **Stock Listing**: A stock's listing on an exchange, with its own ticker and exchange identity;
  one stock may have listings on more than one exchange.
- **Entity Representation**: A reviewed market instrument associated with a sector or industry
  for its price and volume chart evidence.
- **Stock Membership**: A database relationship associating a stock with an industry within a
  region and classification system, used to determine industry-filter results.
- **Selection Context**: The currently selected sector, industry, and stock that determine which
  region, tape, or detail view is displayed.
- **Scorecard**: An existing stock assessment consisting of Quality, Growth, and Cash Flow
  scores, with its underlying availability and sufficiency information.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all controlled hierarchy cases, 100% of states show only the tape appropriate to
  the current sector and industry selections, with no rows from an invalidated parent context.
- **SC-002**: In controlled data, 100% of sector, industry, and stock rows show their own price
  thumbnail followed immediately by a separate volume-chart thumbnail; stock rows also show the
  required ticker, name, price, and existing Quality, Growth, and Cash Flow scores where available.
- **SC-003**: At least 90% of first-time test users can move from the sector tape to a selected
  stock's detail view and identify its industry within 60 seconds.
- **SC-004**: For every stock with sufficient history, the detail view identifies price, volume,
  and both requested moving averages; 100% of unavailable measures in controlled cases are
  explicitly identified as unavailable or insufficient.
- **SC-005**: At least 90% of test users can return from stock detail to the same valid discovery
  context without repeating their sector and industry selections.
- **SC-006**: In controlled regional market data, 100% of stocks associated with the selected
  industry in the selected region are returned exactly once, and no stock from another industry
  or region is returned.
- **SC-007**: In controlled chart data, 100% of price thumbnails with sufficient history show
  the 50-session simple moving average, and all volume bars use green for up sessions, red for
  down sessions, and a neutral color when unchanged or direction cannot be determined.
- **SC-008**: In controlled source-conflict cases, 100% of differences from the live source are
  reported and no locally reviewed region, sector, industry, or membership value is overwritten;
  conflicting local values are reported and not silently selected by source priority.
- **SC-009**: In controlled placeholder cases, all unresolved stock records are identified as
  placeholders and none triggers a live market-data request.
- **SC-010**: In controlled missing-data-source and unpopulated-region cases, 100% of states show
  the database setup action and none is presented as a valid empty market.
- **SC-011**: In controlled partial or unverified coverage cases, 100% of region views identify
  the coverage state and none claims complete regional stock coverage.

## Assumptions

- The hierarchy is a single-selection path: at most one sector and one industry define the next
  tape at a time.
- Selecting an industry replaces the industry tape with its stocks; the user can return to the
  industry tape through the existing navigation or by clearing the industry selection.
- A price-chart thumbnail is a compact preview of that row's own historical price chart and
  includes the 50-session simple moving average when sufficient history exists. Its adjacent
  volume-chart thumbnail uses the same entity's available volume observations.
- Green and red volume bars use consecutive closing-price direction as a visual proxy for buying
  and selling pressure; they do not represent verified trade-side or order-flow data.
- "Scoreboard" refers to the project's existing Quality, Growth, and Cash Flow stock scorecards.
  The stock tape shows all three scores where available, not a new aggregate score or a single
  selected scorecard dimension.
- The stock detail chart uses completed price and volume observations and the project's existing
  data freshness and insufficiency disclosures.
- This feature adds progressive views and stock detail to the existing market discovery
  experience; alerts, recommendations, trading, and additional detail-page sections are out of
  scope until separately specified.
- The existing market/industry classification, stock membership, scorecard, and chart-analysis
  requirements remain the authority for their respective data and calculations. Sector,
  industry, and stock membership data is maintained in the database through data-management
  tooling; the application does not rely on hard-coded membership configuration. Existing local
  sector-rotation resources are a candidate initial import source and must be assessed for
  coverage and suitability. US exchange listings are combined into one region, with distinct
  exchange listings retained for each stock. Live membership refresh is enabled only through the
  application's single selected provider after its coverage, terms, and display rights are
  reviewed.
