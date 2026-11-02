# Contract: Catalog Release v2

**Status**: Target interface, not implemented by planning.
**Supersedes**: Membership/hierarchy/derived-query portions of
[010's file contract](../../010-manifest-csv-catalogs/contracts/catalog-files.md).
Storage, source permissions, paths, publication and missing-data safeguards remain.

## Version and publication boundary

- CURRENT keeps market-catalog-entry-1 and its exact release/path/checksum envelope.
- Inspect manifest format and explicitly dispatch v1/v2. Never retry malformed v2
  as v1 or infer a format from headers.
- V2 uses market-catalog-release-2. Preserve release/parent/source/artifact/audit/
  benchmark/research metadata; add scheme_kind=custom to classifications and the
  membership_migration artifact role.
- Exactly one stock artifact per region. V2 stock artifact classification ID/version
  are null: membership rows supply exact scope; instrument rows assert none.
- Keep required hashes/counts, containment, duplicate-key/header rejection,
  64 MiB artifacts, 1 MiB manifests/records, captured-byte validation, approved
  source checks and on-access integrity verification.
- Retained v1 files use original stock headers, rank/cardinality and classification
  meaning. The new reader may accept only the explicitly typed nonoperational
  membership_migration history role when restoring v1 data; all other v1 metadata
  shape checks remain strict. Old binaries reject this extension/v2 explicitly.

Package the version-specific runtime manifest schema alongside the existing schema.
Data compatibility does not preserve StockRow's old single-industry application
interface: all member-query callers must use the shared projections below.

## Hierarchy CSV

Header remains:

```csv
RegionId,ClassificationId,ClassificationVersion,NodeId,NodeType,Name,SectorId,ParentIndustryId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,ApprovalOrigin
```

Sector fields retain v1 semantics. In v2 an industry may have one optional parent;
a sub_industry has a parent. Either non-sector type may parent another non-sector
node. Legacy types do not automatically establish formal GICS ranks.

Parents/ancestors resolve in identical scope; stored SectorId corroborates inherited
root sector. Allow disjoint reviewed parent periods for a stable node, reject
overlapping node periods and contemporaneous cycles, and verify full period coverage.
Names/row order are not identities. Use iterative traversal, not a recursion limit.

## Regional stock CSV

Replace the IndustryId/SubIndustryId path pair with one exact direct target; add RowKind:

```csv
RowId,RowKind,MembershipId,RegionId,ClassificationId,ClassificationVersion,InstrumentId,CompanyId,Name,IndustryId,ResolutionState,MembershipEffectiveFrom,MembershipEffectiveTo,MembershipSourceId,MembershipApprovalReference,MembershipReviewState,ListingId,Ticker,ProviderSymbol,Exchange,Currency,IsPrimary,ListingResolutionState,ListingEffectiveFrom,ListingEffectiveTo,ListingSourceId,ListingApprovalReference
```

All columns are present; optional nulls are empty cells. Preserve UTF-8/quoted comma
grammar, ISO inclusive dates, explicit Boolean and currency rules.

### RowKind=instrument

- Required: RowId, RegionId, InstrumentId, Name, ResolutionState.
  CompanyId remains nullable.
- MembershipId, ClassificationId/Version, IndustryId and every membership
  period/source/approval/review cell must be empty.
- Listing fields independently retain known metadata or are wholly empty.
  This is not a fake membership or an "unassigned industry."

### RowKind=membership

- Require association identity/scope/target/source/approval and reviewed state;
  only membership end date is optional.
- IndustryId targets an exact non-sector node at any depth.
- Instrument metadata agrees with all records for that instrument.
- Listing remains optional and independent. Concurrent different target industries
  are not conflicting_assignment in v2.

### Shared validation

- Unique RowId; unique membership/listing pairings; unique instrument-only
  `(InstrumentId, ListingId-or-null)` pairings.
- Shared MembershipId agrees on association fields; shared ListingId agrees on
  listing identity, dates and approval. Existing primary/symbol conflicts still fail.
- Build the instrument registry even when no association is effective.
  Multiple listing rows or sources never multiply instruments/peer facts.
- Identified retained instruments are lookup-visible. Placeholders remain unresolved.
  CompanyId is not profile corroboration, issuer ownership proof or permission.

## Snapshot/application boundary

Use typed projections from [data-model.md](../data-model.md):

| Operation | Required result |
|---|---|
| scope_on(region, date) | One exact operational scope or explicit unavailable/conflict |
| active_nodes(scope, date) | All active reviewed nodes, including empty nodes |
| members(scope, node, date) | Sorted unique CatalogMember direct/descendant instrument union |
| memberships_for_instrument(scope, instrument, date) | All effective direct assertions and ancestor paths |
| lookup_instruments(region, query) | Local retained identified candidates, independent of membership |
| listing_for_instrument(region, instrument, date) | Explicit eligible selection or explained unavailable state |
| cohort_fingerprint(scope, node, date) | Canonical eligible identity/approval context, not physical row count |

Adapters use selected node as comparison context, not the first direct target.
Update direct snapshot.stocks/StockRow consumers, provider-symbol collectors,
CLI counts, fingerprints, source approval/representation adapters and both root
workflows. Do not duplicate filtering in the UI.

Retain historical governance under its exact original scope. Resolve historical
references against captured source/explicit retained parent-chain snapshots;
never apply an old NodeReview/representation approval to a new scope implicitly.
No directory scans, guessed IDs, or requirement to activate historical classifications.

## Representations and unavailable evidence

Keep exact sector_etfs/industry_etfs/sub_industry_etfs headers and node-type/scope
approval checks. New scope/meaning requires reviewed applicability. Deeper ancestry
does not confer ETF approval. Baskets retain explicitly reviewed constituents and
weights, not automatic descendant-based population.

Unassigned membership affects membership/peers, not independently eligible listing
history/company evidence. Preserve distinct inactive, insufficient, unresolved,
unauthorized, missing, historical-unavailable and active-corruption states.
