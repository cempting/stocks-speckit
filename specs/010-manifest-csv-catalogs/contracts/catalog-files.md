# File Catalog Contract

**Formats**: `market-catalog-entry-1`, `market-catalog-release-1`, ledger/archive v1.
**Status**: Target contract; implemented by feature 010, not current runtime.

## Store and Manifest

```text
catalog/
├── CURRENT.json
├── .writer.lock
├── releases/<release-id>/
│   ├── manifest.json
│   ├── hierarchy.csv
│   ├── stocks-US.csv
│   ├── etf-listings.csv
│   ├── sector-etfs.csv
│   ├── industry-etfs.csv
│   ├── sub-industry-etfs.csv
│   ├── benchmarks.csv
│   ├── governance.jsonl
│   └── migration-archive.jsonl  # Registered only when present
└── .staging/<operation-id>/    # Never selected by readers
```

Filenames are examples; artifact roles and the strict [schema](catalog-manifest.schema.json)
control loading. Exactly one manifest consolidates a release; the entry only chooses its path/hash.
There must be one stock artifact per region, not multiple stock files for scopes/industries.
Hierarchy/ETF artifacts may cover explicit scopes or several versions through row fields.
All operational roles and `audit` are required once registered. A migration archive is required
once registered; it must not be silently discarded on later publication.

Artifact paths are relative to the release manifest directory and contained within it after
canonical resolution. Entry paths are contained within the store. Reject absolute paths, traversal,
unregistered files, and symlink escapes; no automatic directory scans or alternate-path search.
External research roots are the only separately registered home/absolute paths; their selected
relative catalog files must resolve inside the registered root.

SHA-256 checks raw bytes. Duplicate JSON keys, malformed/unsupported formats, scope mismatches,
duplicate role/region stock declarations, wrong row counts, missing required artifacts and unknown
operational fields fail with bounded file/row/reference diagnostics. JSON Schema validates shapes;
typed domain checks validate dates, references, source ownership, overlaps and review suitability.
Strict schemas do not manufacture approvals.

Published CSV/ledger files are copies of captured validated inputs, never hardlinks to editable
authoring files. Editing authoring inputs prepares a new candidate; changing a selected release's
files is corruption and invalidates access. Check active entry/artifact signatures including ctime
on each access; rehash changed signatures before cache reuse. Validate captured bytes and detect
modification during reads. Never serve a cached successful catalog when its active source is invalid.

## CSV Grammar

UTF-8, comma-separated, RFC-style quoted fields, one header row, explicit named headers below.
Emit LF; readers may accept CRLF/UTF-8 BOM. IDs are nonempty exact strings, not case-folded labels.
Dates are ISO `YYYY-MM-DD`; empty optional end means open-ended, inclusive endpoints.
Use `true/false` for booleans; empty optional boolean means unknown/not applicable.
Decimal weight strings are never converted through float.

Reject duplicate/unknown headers, extra/missing fields, malformed dates/booleans, invalid currencies,
unbounded input and conflicting references. Use shared documented finite input limits, initially
64 MiB per CSV/JSONL artifact and 1 MiB per manifest/record; excess is an explicit validation error,
not truncated data. The controlled reference release must fit these bounds; raising them requires
measured evidence. Names are display fields; no name-to-ID joins, guessed USD, default 1970 date,
primary-listing inference from row order, or licensed version inferred from filenames.

### `hierarchy`

```csv
RegionId,ClassificationId,ClassificationVersion,NodeId,NodeType,Name,SectorId,ParentIndustryId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,ApprovalOrigin
```

`NodeType`: sector, industry, sub_industry. Sector references itself and has no parent industry.
Industry references its sector. Sub-industry references its exact industry and that industry's
sector. Parents/classification cover child periods and match exact scope. `ApprovalOrigin=own`
requires node source/reference; `classification_inherited` requires empty own review fields and
a valid explicitly reviewed classification source/reference.

### `stocks` (one per region)

```csv
RowId,MembershipId,RegionId,ClassificationId,ClassificationVersion,InstrumentId,CompanyId,Name,IndustryId,SubIndustryId,ResolutionState,MembershipEffectiveFrom,MembershipEffectiveTo,MembershipSourceId,MembershipApprovalReference,MembershipReviewState,ListingId,Ticker,ProviderSymbol,Exchange,Currency,IsPrimary,ListingResolutionState,ListingEffectiveFrom,ListingEffectiveTo,ListingSourceId,ListingApprovalReference
```

Logical stock/membership/listing rules are in [data-model](../data-model.md#4-regional-stock-assertionlisting-row).
Membership is reviewed and scoped. No-listing rows explicitly carry empty listing fields and never
trigger remote requests; unverified listing evidence remains noneligible. Duplicate listings/
assertions are validated, not chosen by source priority.
No sector label/ID is duplicated as stock-row authority.

At a date, industry filtering matches `IndustryId`, sub-industry filtering matches only explicit
`SubIndustryId`, and sector filtering uses hierarchy. Compatible same-industry source assertions
are retained but instrument IDs appear once. Multiple primary/listing-symbol conflicts or active
distinct industry/sub-industry assignments fail. Historical non-overlapping assignments are allowed.

### `etf_listings`

```csv
ListingId,RegionId,InstrumentId,InstrumentType,Ticker,ProviderSymbol,Name,Exchange,Currency,IsPrimary,ResolutionState,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference
```

`InstrumentType=etf` requires reviewed ETF identity. A listing is not an approved node mapping.
An unreviewed issuer/theme/name claim remains research/inventory. Listing and source dates/
verification must satisfy the existing approval validator before use. Exact symbol suffix/exchange
identity is preserved; provider requests use the verified provider symbol.

### `sector_etfs`, `industry_etfs`, `sub_industry_etfs`

Each role uses the same header and validates node level:

```csv
RepresentationId,RegionId,ClassificationId,ClassificationVersion,NodeId,ListingId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,SuitabilityReference,CandidateReviewId
```

Source/reference/suitability and exact listing/classification/node periods are mandatory for approval.
`CandidateReviewId` is optional but, when present, resolves through retained exact decision/evidence/
approval-run provenance. No overlapping conflicting mappings; shared ETF requires separate node approval.
CSV listing with blank hierarchy fields from the old sector file cannot establish these records.

### `benchmarks`

```csv
BenchmarkId,RegionId,Purpose,Label,ListingId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference
```

`Purpose=sp500_comparison|market_sentiment`. Resolve approved effective listing, never a literal
ticker default. Existing benchmark/date/subtraction semantics remain; missing evidence is explicit.
Do not claim another index is S&P 500 by changing its label.

## Ledger and Listing Inventory

`audit` is UTF-8 JSONL: exactly one object per nonblank line, no multiline record. Envelope:

```json
{
  "record_type": "publication",
  "record_id": "example-operation",
  "sequence": 1,
  "recorded_at": "2026-10-31T20:00:00+00:00",
  "payload": {"action": "bootstrap", "expected_release": null, "catalog_changed": false},
  "origin": null
}
```

This envelope is a format example, not an approval/seed. Typed payload kinds and relationships
are defined in [data-model](../data-model.md#7-governance--research-ledger). Existing local research
dataclass payloads retain their fields, unknown claims and identities. Validate every operational
record; malformed/unsupported payload cannot be silently skipped. Archive preserves legacy extension
fields/text without treating them as supported live records.

Record IDs are immutable; repeating an ID with different content is an error. Transport sequence
is unique/increasing, separate from original collection and review event-order streams. Publications
preserve previous ledger bytes as a prefix and append records. Existing mapping idempotence may add
new provenance without changing catalog revision. Candidate accept/reject, source reconciliation and
collection never insert an ETF, listing verification, hierarchy or basket automatically.

Listing-only inventory records retain explicit source/verification/period and optional unknown
instrument type. They never supply stock membership. An existing approved basket can reference
a verified inventory listing even without industry membership, preserving the existing validator.
Do not assign it to the basket's industry or require it to be primary. All listing IDs shared with
CSV records must match exactly. Missing/incomplete basket history remains unavailable, never reweighted.

## Research Registration

Research entries contain `resource_id`, explicitly configured `root`, `required=false`, and selected
`catalogs` with `path`, `name`, `catalog_type` (industry/sector_context/index_context/commodity_context).
Descriptors select bounded static literal extraction only; neither configuration nor source order
is proof of regional identity, ETF type, suitability, or reviewed GICS equivalence.

Initial resource aliases/roots are those supplied in feature 009; retain them as documented data
to register, not production code defaults. A missing root, absent catalog, failed parse or partial
inspection yields explicit partial/failed research outcomes. It does not invalidate complete approved
catalog data. Complete inspection is required to prove removal. Source files are read once per
explicit collection and never executed, modified, recursively scanned or sent to an online service.

## Atomic Publication and Recovery

1. Validate expected entry and input manifest; capture required bytes and domain-validated snapshot.
2. Acquire one nonblocking exclusive `fcntl` lock on the persistent store lock file.
3. Recheck expected release and active integrity; reject conflict rather than implicitly rebasing.
4. Stage complete copies and append-only ledger under a unique store-owned operation directory.
   Revalidate written bytes/hash/row counts and references; compute catalog revision and parent link.
5. Flush/fsync staged files/directories; rename the complete directory into `releases/`.
6. Write/fsync a temporary entry, then atomically replace `CURRENT.json`. This is the commit point.
   Sync directory durability before acknowledging a durable publication. Never rewrite CSVs in place.
7. Keep prior generations; cleanup is bounded to the publisher's own unreferenced staging paths,
   not user sources, referenced releases or store root. Never unlink a live lock file.

Pre-commit error/conflict: no entry change, explicit failed report. A failure at/after pointer commit
can make acknowledgement/durability uncertain: report `publication_state=unknown` (or `published`
when verified) with nonzero diagnostic outcome, do not claim rollback or retry blindly.
The next access/recovery verifies the selected complete release and operation/parent identity.
Interrupted publication exposes an old or new complete generation, not mixed files or dangling approval.
No automatic activation of leftover directories, deletion of old histories, or best-effort stale fallback.

Recovery is explicit, requires expected current entry identity, and revalidates a known reviewed
target manifest/checksum. An invalid current entry may be identified by its raw checksum for recovery;
never guess a latest directory. Local POSIX filesystem/locking is required; reject unsupported storage.

## Migration Archive

`migration_archive` is registered JSONL with original schema/column presence and one lossless record
per source primary-key row, disposition, target references and reason codes. All twenty schema-3
tables and actual version-1/2 differences are accounted for in [data-model](../data-model.md#8-migration-archive-and-reconciliation).
An input exceeding declared file/record limits blocks export with explicit table/row diagnostics;
never truncate raw payloads or report an incomplete archive as a complete lossless export.
The archive is audit/reconciliation only, never runtime membership/approval fallback.
Quarantined original rows remain inspectable; missing historical rejected input is reported as
never retained, not reconstructed from an issue string.
