# Data Model: Dedicated Stock Lookup

This feature adds no persisted data model. It reuses the active catalog and existing stock-detail
contracts; lookup selections are session-local UI state.

## Existing Entities

### Catalog Context

- **Fields**: active catalog revision, region identifier, selected as-of date.
- **Relationships**: scopes the retained stock identities and determines which listings are
  active and verified for lookup.
- **Validation**: region and date must be supported by the active catalog; changing the catalog
  revision, region, or date invalidates dependent selections unless they are revalidated.

### Stock Identity

- **Fields**: stable instrument identifier, display name, region, optional company identifier,
  retained listings and memberships.
- **Relationships**: may have zero or more listings and zero or more industry memberships.
- **Validation**: identity search returns only identities retained in the active catalog and
  selected region. An identity without an active membership remains searchable and must not be
  assigned one by lookup.

### Stock Listing

- **Fields**: stable listing identifier, instrument identifier, instrument type, provider symbol,
  exchange, currency, and active date range.
- **Relationships**: belongs to a stock identity.
- **Validation**: remote history is available only for an active, verified stock listing selected
  for the current catalog context and date.

## Session-Local Lookup State

- **Query**: current user-entered search text.
- **Matches**: retained identities matching the query; empty query and no-match states are
  distinct.
- **Selected identity**: exact stable instrument identifier chosen from the matches.
- **Selected listing**: optional exact active verified listing identifier for the selected
  identity.
- **Detail context**: selected identity/listing plus region, date, and catalog revision.
- **History state**: not requested, requested, loaded, failed, or incomplete for that detail
  context.

## State Transitions

1. Empty query → query matches → user selects an exact identity.
2. Selected identity → select an active verified listing when one exists → user opens detail.
3. If no verified listing exists, detail may show the identity under existing rules but no remote
   listing-history request is made.
4. Open detail → explicit load or refresh action → visible loaded, failed, or incomplete history
   state.
5. Query, region, date, catalog revision, identity, or listing changes invalidate dependent
   state; old detail/history must not be presented as current.

## Existing Entity-Tape Presentation Projection

This is a view over existing frame values, not a new domain class or persisted entity.

| Surface | Stable selection identity | Full name | Ticker evidence |
|---|---|---|---|
| Sector performance | `Node ID` | `Sector` | `Ticker`, from existing associated ETF evidence |
| Industry momentum | `Node ID` | `Industry` | `ETF`, from existing associated ETF evidence |
| Stock list | `Instrument ID` | `Name` | Existing listing `Ticker` or explicit unresolved-placeholder state |

- Sector `Ticker` and industry `ETF` are internal backing fields, not separate visible
  columns. The entity button contains the ticker and full name. Both entity tapes have
  eight visible columns; the stock tape keeps its five-column projection and Ticker button.
- Sector/industry missing, blank, `Unavailable`, `Not covered`, and `Not an ETF` values render
  as `No ticker` in the first block; no internal identifier or basket label becomes a ticker.
- Status, representation, and representation type remain separate evidence in existing tooltips.
  Display fallback does not erase the underlying evidence state or change row eligibility.
- Names and ticker text are escaped for literal Markdown display, never abbreviated or used as
  widget identity. Duplicate names/tickers still select by the original stable ID.
- The label contains two text blocks separated by a hard line break. The ticker block is at
  least twice the name's font size; the name may occupy several physical lines.
- Stock selection still returns the existing row-index tuple, and sector/industry callbacks
  still receive the node ID. Rendering does not create selection state or remote requests.
- No schema migration, catalog change, new cache key, or additional state transition is needed.
