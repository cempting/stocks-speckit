# US Market Catalog Input Contract

## Authority and release format

`docs/markets/US/` is an authoring location, not a runtime catalog path. Discovery reads the
active entry selected by `MARKET_CATALOG_MANIFEST_PATH` (default `.data/catalog/CURRENT.json`)
through the existing `CatalogReader`. Do not scan directories, read candidate CSVs directly from
the UI, or activate a release as a side effect of reading it.

The supplied `MY_TAXONOMY` and `MY_THEMES` scopes are custom classifications. Use the existing
`market-catalog-release-2` manifest contract; do not invent a release-v3 solely for these rows.
Keep the exact scope fields in every hierarchy and ETF mapping row:

```text
RegionId, ClassificationId, ClassificationVersion
```

Theme nodes are represented at sector level in their own classification. They must not be
described as official GICS taxonomy unless independent reviewed evidence establishes that status.

## Artifact roles

| Source CSV | Release artifact role | Expected domain level |
|---|---|---|
| `hierarchy.csv` | `hierarchy` | sector, industry, sub_industry |
| `etf_listings.csv` | `etf_listings` | ETF listings |
| `sector_etfs.csv` | `sector_etfs` | sector nodes, including theme nodes |
| `industry_etfs.csv` | `industry_etfs` | industry nodes |
| `sub_industry_etfs.csv` | `sub_industry_etfs` | sub-industry nodes |

The three representation roles share this exact header:

```csv
RepresentationId,RegionId,ClassificationId,ClassificationVersion,NodeId,ListingId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,SuitabilityReference,CandidateReviewId
```

The listing header is:

```csv
ListingId,RegionId,InstrumentId,InstrumentType,Ticker,ProviderSymbol,Name,Exchange,Currency,IsPrimary,ResolutionState,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference
```

The hierarchy header is:

```csv
RegionId,ClassificationId,ClassificationVersion,NodeId,NodeType,Name,SectorId,ParentIndustryId,EffectiveFrom,EffectiveTo,SourceId,ApprovalReference,ApprovalOrigin
```

Use the existing catalog schema and strict CSV grammar for all additional roles and fields.
Dates are ISO `YYYY-MM-DD`; empty end dates mean open-ended. IDs are exact, scoped identities.
`ProviderSymbol` is preserved exactly and is not reconstructed from `Ticker`.

## Completeness and validation

A release requires all operational artifact roles for each active region under the existing
manifest schema, including `stocks`, `benchmarks`, and `audit`. The supplied folder contains only
the five CSVs listed above. A reviewer must supply or explicitly retain valid stock, benchmark,
source, and audit records before publication. A zero-row stock artifact is permitted only when
the reviewer confirms that the release has no reviewed stock membership; it does not imply
stock coverage. Never invent benchmark instruments or approvals to make a release validate.

Before publication:

1. Validate CSV headers, row shapes, exact scope and hierarchy level.
2. Resolve every `ListingId` and node reference in the same region/classification/version.
3. Verify effective periods, listing identity, provider symbol, source ownership, approval, and
   ETF-to-node suitability.
4. Require the exact evidence and review records for every active mapping. Generic identifiers
   such as the supplied `source-1` and empty candidate-review fields are not proof.
5. Register all artifacts with exact row counts and content hashes, validate the complete release,
   and publish atomically through the existing catalog lifecycle.

Invalid candidate data must not replace the previous active release. Current cross-file reference
resolution is a structural check only; it does not establish approval.
