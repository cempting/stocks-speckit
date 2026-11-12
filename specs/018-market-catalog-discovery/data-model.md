# Data Model: US Industry and Theme ETF Discovery

This feature reuses the manifest-managed file catalog and typed market-data domain. It introduces
no database, parallel catalog, or new persisted approval format. The existing catalog release and
representation types remain authoritative.

## Entities and projections

### Catalog release

An immutable, validated release identified by `release_id`, content revision, manifest hash,
format version, region metadata, evidence sources, artifact roles, and audit history. It is
selected through the catalog's current-entry file.

**Rules**

- Preserve explicit release-v1/release-v2 dispatch and artifact hashes.
- A v2 release uses custom classifications and keeps its required operational roles, including
  the regional stock artifact, benchmarks, and audit.
- No release becomes active until all required artifacts and review evidence validate.
- The authoring files remain candidate inputs; the publisher captures validated copies.

### Classification scope

The exact identity `(region_id, classification_id, classification_version)` associated with
reviewed scheme metadata and an effective period.

**Relationships**

- A region may have multiple classifications active on the same date.
- A classification has one or more active hierarchy nodes.
- `MY_TAXONOMY` and `MY_THEMES` are separate custom scopes; their names and labels come from
  reviewed manifest metadata rather than assumptions based on file order.

**Rules**

- Scope enumeration returns all active classifications for a region/date.
- Scope resolution by region/date alone remains valid only when exactly one classification is
  active; otherwise the caller must supply a selected exact scope.
- Classification changes invalidate descendant node selections but do not modify other
  session-local controls.

### Hierarchy node

An effective reviewed node identified by `(scope, node_id)` with `node_type`, display `name`,
`sector_id`, optional `parent_industry_id`, effective period, and source/approval provenance.

**Relationships**

- A sector is its own `sector_id` and has no parent.
- An industry is a child in a sector.
- A sub-industry resolves to its exact parent industry and sector.
- The supplied flat theme nodes are represented as sectors within a distinct custom
  classification; they are not official GICS sectors by implication.

**Rules**

- Category navigation follows reviewed parent relationships and never matches by display name.
- Empty nodes remain visible with explicit missing representation status.
- Nodes are filtered by exact scope and effective date.

### ETF listing

A verified regional ETF listing identified by `listing_id`, instrument identity, display ticker,
provider symbol, name, exchange, currency, primary status, effective period, and source/approval
references.

**Rules**

- Only a verified, active listing is eligible for a reviewed representation.
- The provider symbol is the exact market-history request identifier; it is not guessed from the
  ticker.
- A listing may be used for multiple category mappings only when each mapping has its own reviewed
  suitability and approval evidence.

### ETF representation option

An exact effective mapping from `(scope, node_id)` to `listing_id`, identified by
`representation_id` and carrying source, approval, suitability, and optional candidate-review
provenance.

**Relationships**

- A node may have zero or multiple effective approved ETF representation options.
- An option references exactly one listing and one node in one classification scope.
- Multiple options remain separate in the Discovery projection even when they share one provider
  symbol; their approval/mapping identities are not deduplicated.

**Rules**

- Mapping approval is not inferred from a category label, ETF name, ticker, or ETF holdings.
- The app displays all valid options; it does not select one based on CSV order or sort order.
- Invalid or unapproved options never supply a successful performance result.

### ETF history availability

A request-date projection keyed by `(provider_id, provider_symbol, start_date, end_date)` with an
explicit status, optional canonical daily history, and optional reason.

**Statuses**

- `available`: usable adjusted daily closes and volume exist for the requested period.
- `no_history`: the request completed but returned no usable observations.
- `insufficient_history`: observations exist but cannot support one or more requested periods.
- `request_failed`: the provider request failed; actionable context is surfaced.

**Rules**

- The only runtime provider in this feature is yFinance.
- A missing symbol must not suppress valid symbols in a partial provider response.
- Failures are not cached or presented as successful stale results.
- Shared symbols may reuse one fetched history but retain separate representation result records.

### Discovery selection

Session-local user selection consisting of `region_id`, exact classification scope, selected
parent/child node path, as-of date, and optional stock selection.

**Rules**

- State keys are namespaced per workflow and stable IDs, not display labels.
- Changing classification or a parent clears only invalid descendants.
- Discovery and Industry Deep-Dive each resolve a selected classification explicitly when the
  region has multiple active classifications.

### Stock membership

An existing, separately reviewed association between an instrument and a hierarchy node. It is
not part of the five supplied files and is not created by ETF representation mappings.

**Rules**

- If no reviewed membership artifact is present, contained-stock data is explicitly unavailable.
- ETF holdings, names, and classification labels cannot be used to manufacture membership.

## Source-file correspondence

| Supplied file | Catalog role | Domain entities |
|---|---|---|
| `hierarchy.csv` | `hierarchy` | Classification scopes and hierarchy nodes |
| `etf_listings.csv` | `etf_listings` | ETF listings |
| `sector_etfs.csv` | `sector_etfs` | Sector/theme representation options |
| `industry_etfs.csv` | `industry_etfs` | Industry representation options |
| `sub_industry_etfs.csv` | `sub_industry_etfs` | Sub-industry representation options |

The supplied directory does not include release metadata, audit, benchmark, or stock artifacts.
The full release must obtain or retain those according to [the catalog input contract](contracts/us-market-catalog-input.md).
