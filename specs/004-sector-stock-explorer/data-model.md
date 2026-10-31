# Data Model: Sector-to-Stock Explorer

> **2026-10-31 alignment — migration reference:** The SQL records and `database_revision`
> below document pre-cutover storage, not current target authority.
> [Feature 010](../010-manifest-csv-catalogs/spec.md) requires one regional stock CSV with exact
> industry references, reviewed sector/sub-industry hierarchy, manifest-registered ETF/listing
> sources, and file-only audit records. Preserve identities, periods, verified listing/placeholder
> states, source conflicts, and selection reconciliation when exporting/refactoring these records.

The SQLite database is the persistent authority for regional classification and membership.
Market observations and user selections remain outside the database: market evidence uses the
existing provider caches, and selections remain namespaced in Streamlit session state.

## Persistent Records

### Region

Fields: `region_id`, `name`, `status`, `coverage_state` (`complete | partial | unverified`),
`coverage_description`, `coverage_as_of`, `last_reviewed_at?`.

The initial region is `US`. Region identifiers are stable and independent of exchange listings.
Future regions may use classification systems different from GICS.

### ClassificationSystem

Fields: `classification_id`, `region_id`, `name`, `version?`, `source_id`,
`approval_reference?`, `effective_from`, `effective_to?`.

Each system belongs to one region. Sector and industry identities are scoped to a system; names
are display values and never used as keys. The system does not assume GICS.

### Sector and Industry

`Sector` fields: `sector_id`, `classification_id`, `name`, `effective_from`, `effective_to?`.

`Industry` fields: `industry_id`, `sector_id`, `classification_id`, `name`, `effective_from`,
`effective_to?`.

An industry belongs to exactly one sector in its classification system and effective period.
Stable source identifiers are preserved when supplied; ambiguous source identity is reported for
review instead of being inferred from a display name.

### Stock

Fields: `instrument_id`, `company_id?`, `name`, `resolution_state`
(`identified | placeholder`), `classification_state` (`classified | unclassified | conflict`).

`instrument_id` identifies a security, not an issuer name or exchange ticker. A stock can have
multiple exchange listings. A placeholder can have classification membership without a verified
listing; it remains visible as unresolved and is never sent to a market-data provider.

### StockListing

Fields: `listing_id`, `instrument_id`, `region_id`, `exchange_id`, `symbol`, `provider_symbol?`,
`currency`, `is_primary`, `effective_from`, `effective_to?`, `source_id`, `resolution_state`.

Ticker symbols are only unique within their exchange/region and effective period, not globally.
One security can have multiple verified listings but at most one active primary listing for the
selected provider and region. Index membership does not create a second security. A listing is
eligible for live market requests only when its identity and source are verified and its effective
period includes the requested observation date. Other listings remain available as identity
metadata and do not cause duplicate market-data requests.

### StockMembership

Fields: `instrument_id`, `region_id`, `classification_id`, `industry_id`, `effective_from`,
`effective_to?`, `source_id`, `approval_reference?`, `review_state`.

Membership joins a stable security to one industry under one region-specific classification. A
valid industry filter joins through this record and returns each eligible `instrument_id` once.
Local reviewed membership is authoritative; a live-source disagreement is recorded and reported,
not applied as an update.

### EntityRepresentation

Fields: `representation_id`, `region_id`, `classification_id`, `entity_type`
(`sector | industry`), `entity_id`, `listing_id`, `effective_from`, `effective_to?`, `source_id`.

This holds the existing sector and industry chart-proxy relationships currently embedded in
application constants. A missing or unapproved representation produces an unavailable chart
state; it never substitutes another entity's history.

### DataSource, ImportRun, and ImportIssue

`DataSource` fields: `source_id`, `source_type` (`local_file | live`), `description`,
`coverage`, `authority`, `approval_reference?`, `reviewed_at?`.

`ImportRun` records source, input fingerprint, start/completion time, status
(`validated | committed | committed_partial | rejected`), and row counts. `ImportIssue` records
the affected source row/entity, issue kind, and actionable detail for invalid or conflicting data.

Each import validates the complete input before publication and commits accepted changes in one
SQLite transaction. A rejected import leaves the last valid database state unchanged. Listings
with missing classification can be retained as unclassified and make region coverage partial;
they are not assigned to an industry. Conflicts are reported and conflicting values are not
silently selected by source priority. Local reviewed sources own classification and membership;
live differences are persisted as issues and do not overwrite those fields.

## Selection and Views

### ProgressiveSelection

Fields: `region_id?`, `sector_id?`, `industry_id?`, `instrument_id?`, `database_revision?`,
`observation_date?`.

Invariants:

- Every child belongs to its selected parent and region in the active classification and
  membership context.
- Stable IDs, not names or tickers, are stored in session state.
- Changing region/sector/industry clears only invalid descendants; returning from detail preserves
  valid region and hierarchy context.
- A database revision change triggers membership reconciliation before stale rows are rendered.

### VisibleStage

Values: `sectors`, `industries`, `stocks`, `stock_detail`.

The initial view is the sector tape for the US region. A valid sector selection shows that
region's industries; an industry selection shows its member stocks; a stock selection opens the
same stock's detail view. A placeholder remains in the stock tape with an unresolved state.

### Tape Projections

`SectorTapeRow`: `sector_id`, `name`, `performance`, `observation_date`, `source_evidence`,
`price_chart_series`, `volume_chart_series`, `chart_state`.

`IndustryTapeRow`: `industry_id`, `parent_sector_id`, `name`, `performance`,
`observation_date`, `source_evidence`, `price_chart_series`, `volume_chart_series`,
`chart_state`.

`StockTapeRow`: `instrument_id`, `industry_id?`, `listing_ids`, `ticker_display`, `name`, `price?`,
`price_date?`, `price_source`, `price_chart_series`, `volume_chart_series`, `chart_state`,
`quality_score?`, `growth_score?`, `cash_flow_score?`, `score_state`, `resolution_state`.

Rows are generated from the selected region/classification and include all active members,
including placeholders or securities with missing evidence. Every chart is bound to the row's
stable ID. Each price-chart point contains session, close, and 50-session average when available.
Each volume-chart point contains session, volume, and a direction value (`up`, `down`, or
`neutral`). Direction compares its close with the previous completed close; the first point, an
unchanged close, or an unavailable comparison is neutral. These directions do not claim verified
individual buy/sell activity. Both thumbnails cover the same sessions, appear in adjacent table
columns, and display unavailable states instead of fabricated values.

## Market Evidence and Scores

### PriceHistory

Reuse canonical completed daily histories keyed by verified listing/provider symbol and session.
The displayed entity's series is ordered, has unique completed sessions, finite positive prices,
and nonnegative volume. Preserve requested/observed dates, provider, freshness, and validation
state. Request histories only for verified listings in the active region/industry.

### DiscoveryChartPreview

Fields: `entity_id`, `sessions`, `close`, `sma50?`, `volume`, `direction` (`up | down | neutral`),
`price_state`, `volume_state`.

The price thumbnail overlays the 50-session simple moving average computed from exactly 50
completed closes. It may show only the most recent preview sessions, but must compute the average
from the complete preceding history needed for those points. The adjacent volume thumbnail uses
the same sessions and entity. Direction is green/up when close exceeds the prior close, red/down
when lower, and neutral when unchanged or indeterminate; the legend describes price direction,
not verified trade-side volume. Missing price, volume, or SMA observations are identified per
series without suppressing independent available evidence.

### StockChartEvidence

Fields: `instrument_id`, `sessions`, `price`, `volume`, `sma50?`, `sma150?`, `price_state`,
`volume_state`, `sma50_state`, `sma150_state`, `observation_date`, `source_evidence`.

Moving averages use completed-session simple means over exactly 50 and 150 observations.
Insufficient history is represented per series, not as zero. Price, volume, and moving averages
come from the same security history.

### PeerBlockScore

Fields: `instrument_id`, `block` (`Quality | Growth | Cash Flow`), `value?`, `state`,
`valid_peer_count`, `analysis_cutoff`, `metric_evidence`, `source_evidence`, `reason_codes`.

The existing 001 contract owns formulas, exact ranking, tie handling, cohort selection, and
minimum peer count. Both metrics in a block are required. The peer cohort is the complete
eligible industry membership before technical filters, display selection, paging, or sorting.
Evidence unavailable at the requested cutoff is insufficient. No overall score is defined.

## Indexes and Query Rules

- Index membership by `(region_id, classification_id, industry_id, effective_from, effective_to)`.
- Enforce foreign keys and stable IDs; enforce listing identity within the region/exchange and
  effective period, not globally by ticker.
- Fetch an industry's rows with one region- and classification-scoped membership query and
  deduplicate by `instrument_id`, never by company name.
- Cache only remote source evidence using existing provider/symbol/date/request cache keys;
  database results do not contain user-specific selection state.

## Failure Semantics

Load states distinguish `not_loaded`, `loading`, `available`, `partial`, `insufficient`,
`placeholder`, `stale`, and `error`. Empty valid membership is different from an absent or invalid
database, a rejected import, or an unapproved source. Errors and source conflicts remain
observable; they are never cached or rendered as successful empty data. Independent valid rows
remain visible when a sibling stock fails.
