# Data Model: Manifest-Managed CSV Catalogs

All formats are version 1. Files are the sole operational catalog/review authority.
Serialization and headers: [file contract](contracts/catalog-files.md).
Shape validation: [manifest schema](contracts/catalog-manifest.schema.json).
Existing types/validators are extracted and reused, not reimplemented as SQL-shaped objects.

## 1. Entry and Catalog Release

| Entity / field | Type and invariant |
|---|---|
| Entry `format` | `market-catalog-entry-1` |
| `release_id` | Nonempty immutable release identity; agrees with selected manifest |
| `manifest_path` | Relative contained path under the store, normally `releases/<id>/manifest.json` |
| `manifest_sha256` | SHA-256 of actual selected manifest bytes |
| Release `format` | `market-catalog-release-1` |
| `release_id` | Publisher-assigned unique ID; no timestamp-based entity identity |
| `created_at` | UTC publication time; not an observation date or approval |
| `parent_release` | Null for bootstrap, otherwise prior release ID and manifest checksum |
| `catalog_revision` | Derived digest of catalog artifacts, region/classification/coverage, and relevant approval metadata |
| `regions` | Explicit reviewed regional/classification metadata |
| `evidence_sources` | Original source/review registry, separate from physical artifact IDs |
| `artifacts` | Required catalog/ledger/archive files with paths, roles, scopes, hashes and row counts |
| `research_sources` | Optional selected local roots/catalog descriptors; research only |

The manifest checksum identifies the whole release. `catalog_revision` excludes unrelated
research observations, transport/publication history, and raw archive records. A research-only
publication can change the entry/release ID while preserving catalog data revision and remote caches.
Do not accept a caller-supplied revision without recomputing its declared content dependencies.

Lifecycle: `authoring -> validated candidate -> staged -> published`.
Validation or pre-commit publication failure leaves the entry unchanged. Published files are never
edited by the writer. Active missing/modified files produce invalid/unavailable state, not automatic
rollback. Explicit recovery revalidates a known reviewed release.

## 2. Region, Classification, Evidence Source and Artifact

**Region**: `region_id`, `name`, `status` (`active/inactive`), `coverage_state`
(`complete/partial/unverified`), `coverage_description`, `coverage_as_of`, nullable
`last_reviewed_at`, and `classifications`.

**Classification**: `classification_id`, `scheme_name`, `version`, `source_id`,
`approval_reference`, inclusive `effective_from`, nullable `effective_to`.
Version is an explicit reviewed identity, never an inferred year or `latest` alias.
Operational scope keys are `(region_id, classification_id, version)`.
There must be an unambiguous enabled classification at the requested date for a regional view;
overlapping competing scopes need explicit resolution, not most-recent/file-order selection.
Initial delivery is US GICS; retaining other legacy scopes does not establish new taxonomy coverage.

**EvidenceSource**: `source_id`, `source_type` (`local_file/live`), `description`,
nullable `coverage`, `authority`, `approval_reference`, and `reviewed_at`.
Preserve existing local-file/source-reference approval checks. Registration or a copied string
is not a listing verification, suitability decision, or data/display-rights grant.
Unreviewed source metadata may be retained for research/history but cannot authorize publication.

**Artifact**: `artifact_id`, `role`, `path`, `sha256`, `required`, `row_count`,
nullable `region_id`, `classification_id`, `classification_version`.
Scope fields restrict contents; region stock files have one region and can carry multiple explicitly
dated classification versions. `row_count` counts physical CSV rows or nonblank JSONL records.
An artifact ID is not an issuer/source/review ID. Required artifacts must exist and match identity.
Exactly one `stocks` artifact per operational region; never one per industry.

## 3. Reviewed Hierarchy Node

Fields: exact scope, `NodeId`, `NodeType` (`sector/industry/sub_industry`), `Name`,
`SectorId`, nullable `ParentIndustryId`, inclusive `EffectiveFrom`, nullable `EffectiveTo`,
nullable node `SourceId`/`ApprovalReference`, and `ApprovalOrigin`
(`own/classification_inherited`).

- Sector: `SectorId = NodeId`, no parent industry.
- Industry: sector reference resolves within identical scope; no parent industry.
- Sub-industry: exact parent industry resolves in the same sector and scope.
- Child periods must be covered by classification/parent periods; cycles, wrong type and dangling
  references fail validation. Display labels never determine identity.
- Explicit classification-inherited approval resolves the existing reviewed classification/source
  ownership, without inventing an independent node approval. `own` requires both review fields.
- Historical node intervals can share a stable ID only with consistent identity and nonconflicting
  periods. Empty nodes remain visible independently of stock membership.

## 4. Regional Stock Assertion/Listing Row

| Field group | Meaning |
|---|---|
| `RowId` | Unique physical row; stable identity of membership/listing pairing |
| `MembershipId` | Stable logical assertion ID, shared by its distinct listing rows |
| Scope | `RegionId`, `ClassificationId`, `ClassificationVersion` |
| Stock identity | `InstrumentId`, nullable `CompanyId`, `Name`, `ResolutionState` (`identified/placeholder`) |
| Hierarchy | Required `IndustryId`; nullable exact `SubIndustryId` belonging to that industry |
| Membership period | `MembershipEffectiveFrom`, nullable `MembershipEffectiveTo` |
| Membership review | `MembershipSourceId`, `MembershipApprovalReference`, `MembershipReviewState=reviewed` |
| Listing identity | Nullable `ListingId`, `Ticker`, `ProviderSymbol`, `Exchange`, `Currency` |
| Listing state | Nullable `IsPrimary`, `ListingResolutionState` (`verified/unverified`) |
| Listing period | Nullable `ListingEffectiveFrom`/`ListingEffectiveTo` |
| Listing review | Nullable `ListingSourceId`, `ListingApprovalReference` |

All rows reference exact reviewed industries. The optional sub-industry is an independently
reviewed assignment, not inferred from parent membership or fund exposure. Conflicting/unclassified/
unreviewed membership stays in inventory/quarantine/history, not in the operational stock CSV.

A no-listing row has all listing fields empty and is explicitly unresolved for price requests.
Preserve identified versus placeholder instrument state; neither a missing nor unverified listing
creates a provider request. A verified usable listing needs identified instrument, canonical
provider symbol, reviewed regional source, valid dates, and primary selection for member requests.
Basket eligibility keeps the existing ability to use a verified non-primary listing explicitly.

Membership and listing periods are independent; requests require their intersection at the
requested date. All rows sharing a `MembershipId` must agree on assertion fields; rows sharing
a `ListingId` must agree on listing attributes, period and source. Repeated instrument metadata
must agree. Reject exact duplicate rows, overlapping primary listings, ambiguous symbol identities,
conflicting active industries or distinct sub-industries in one scope. Compatible same-industry
assertions may retain distinct provenance while returning an instrument once.

For legacy sub-industry membership, map the original node to `SubIndustryId` and its exact parent
to `IndustryId`; preserve the original membership primary key in migration provenance.
Do not replace stored IDs or regenerate identities from names. New logical IDs may be explicit
stable IDs; derived legacy membership/row IDs use canonical original keys, not file order/clock.

## 5. ETF Listing and Representation

**ETF Listing**: `ListingId`, `RegionId`, `InstrumentId`, `InstrumentType=etf`, `Ticker`, `ProviderSymbol`,
`Name`, `Exchange`, `Currency`, `IsPrimary`, `ResolutionState`, inclusive
`EffectiveFrom`, nullable `EffectiveTo`, `SourceId`, `ApprovalReference`.
Unknown product identity remains inventory evidence; issuer names do not establish ETF identity.
The supplied legacy sector file requires explicit verification/references before normalization.

**ETF Representation**: `RepresentationId`, exact scope, `NodeId`, `ListingId`,
inclusive `EffectiveFrom`, nullable `EffectiveTo`, `SourceId`, `ApprovalReference`,
`SuitabilityReference`, nullable `CandidateReviewId`.
The artifact role fixes sector/industry/sub-industry level. Node/listing/classification/source
period and approval must agree. ETF approval retains the verified primary-listing rule.
Duplicate/conflicting mapping periods fail; sharing an ETF across nodes requires independent approvals.
A migrated suitability reference can point to an existing explicit mapping approval; it cannot be
invented when the legacy record lacks reviewed scope/ETF evidence.

Missing mapping, invalid mapping, and valid mapping with insufficient/unavailable history remain
different row states. No broad/parent/index/stock substitute and no inference from the stock CSV.

## 6. Benchmark Mapping

Fields: `BenchmarkId`, `RegionId`, `Purpose`, `Label`, `ListingId`,
inclusive `EffectiveFrom`, nullable `EffectiveTo`, `SourceId`, `ApprovalReference`.
Purposes: `sp500_comparison`, `market_sentiment`. A purpose resolves to at most one approved
effective listing. Keep S&P 500 comparison label/subtraction and existing valid session anchoring.
No benchmark symbol default is permitted. A missing benchmark is explicit evidence insufficiency.

## 7. Governance / Research Ledger

Envelope: `record_type`, immutable `record_id`, transport `sequence`, nullable UTC `recorded_at`,
typed `payload`, nullable `origin` referencing legacy table/key or the authoring/review action.
Transport order is not a fabricated legacy observation chronology.
Known types:

| Type | Payload / relationship |
|---|---|
| `listing_inventory` | Stock/unknown listing-only identity, region, attributes, verification, periods and original source/approval |
| `node_review` / `representation_approval` | Exact target/source/reference/period and action; links to published CSV IDs |
| `basket` | Existing representation ID, exact target, name, source/approval, dates, review state |
| `basket_constituent` | Basket ID, exact verified listing ID, decimal weight string |
| `collection_run` | Original run ID, collection event order, observation clock, outcomes and selected descriptors |
| `mapping_evidence` | Original evidence/candidate identity, declarations/scope, snapshots/locations and semantic fingerprint |
| `collection_evidence` | Run/evidence relationship |
| `candidate_review` | Original review ID, review event order, exact scope/node/as-of, decision/reason/reference, selected run and assessments |
| `review_evidence` | Exact review/evidence relationship |
| `representation_provenance` | Representation/review relationship and approval-run ID, distinct from review-run ID |
| `publication` | Operation identity, expected parent, action and whether approved catalog content changed |

Payloads for local research preserve existing typed domain fields and identity algorithms;
nullable/unknown declarations remain unknown. Keep collection and review event orders separate.
Recognized legacy JSON payload extension fields survive export/archive; unsupported operational
record types fail validation rather than silently dropping data.

Listings in inventory do not confer industry membership. Only explicit approved basket references
may use eligible inventory listings for live calculations. Conflicts with stock/ETF CSV listing
identity fail validation; inventory is not a lookup fallback for missing stock memberships.

Existing approved ETF takes precedence over an explicit basket. Basket approval requires no
overlapping approved ETF, full source/target/constituent periods, unique listing/provider identities,
finite positive decimal weights totaling exactly 100%. Preserve stored weight strings and calculate
without renormalization. No artificial basket OHLC/volume chart.

Review state: unbound candidate -> explicit exact reconciliation -> accepted/rejected assessment ->
separate valid approval. Later rejection clears selection without reviving an older acceptance.
Changed/removed/newly conflicting/unknown support flags affected decisions; incomplete inspection
does not prove absence. Existing approvals remain historical/runtime evidence until explicitly
changed; invalid current support blocks new candidate-provenance approval.

## 8. Migration Archive and Reconciliation

An archive record retains original table, original primary-key object, column presence, typed column
values, disposition (`transferred/quarantined/archived`), target IDs/paths, and safe reason codes.
Every source row is stored losslessly, even if also projected into operational CSV/ledger data.
Disposition accounting counts each original row once, not each duplicated listing/membership CSV row.
Original raw JSON TEXT and decimal TEXT remain strings; do not normalize away their content.

### Complete schema-3 inventory

| Legacy table | Keys / transfer or retention |
|---|---|
| `database_metadata` | `key`; schema/revision/arbitrary metadata and regional scope history archived |
| `regions` | `region_id`; region coverage/status/date metadata transferred or retained |
| `data_sources` | `source_id`; original registry/review ownership, including unreviewed metadata |
| `classifications` | `classification_id`; region/name/nullable version/source/approval/period |
| `sectors` | `sector_id`; exact classification/name/period; inherited classification approval |
| `industries` | `industry_id`; sector/classification/node type/parent/source/approval/period |
| `stocks` | `instrument_id`; company/name/identified-placeholder/classification state |
| `stock_listings` | `listing_id`; instrument/region/exchange/symbol/provider/currency/primary/period/source/verification |
| `stock_memberships` | instrument/region/classification/industry/start composite key; source/approval/review/end |
| `entity_representations` | `representation_id`; exact logical entity/listing/scope/source/approval/period |
| `import_runs` | `import_run_id`; source/context fingerprint/times/status/counts, unique source+fingerprint |
| `import_issues` | `import_issue_id`; run/row/entity/kind/detail; original rejected rows may not exist |
| `stock_baskets` | `representation_id`; target/name/source/approval/period/review state |
| `basket_constituents` | basket+listing composite key; positive decimal weight TEXT |
| `etf_collection_runs` | `run_id`; collection event order/observation/status/raw JSON payload |
| `etf_mapping_evidence` | `evidence_id`; nullable candidate/raw JSON payload |
| `etf_collection_evidence` | run+evidence composite key |
| `etf_candidate_reviews` | `review_id` and review event order; exact target/as-of/run/decision/reason/reference/raw payload |
| `etf_review_evidence` | review+evidence composite key |
| `etf_representation_provenance` | representation+review composite key; distinct approval-run reference |

Versions 1/2 are exported by their actual schema; absent later tables/columns are recorded as absent.
No initialization/backfill is run against the source. Unknown version/scope and unresolved approval
cannot be guessed. Quarantine operationally unusable records and retain their dependencies/history;
resolve a missing classification version only through a new explicit reviewed source binding.

Reconciliation includes source logical snapshot checksum, schema inventory, original row counts,
disposition counts, key/value digests, FK/logical-link checks, and every source-to-target mapping.
Record `complete/blocked` operational-readiness separately from successful archive retention.
No real database/source input is opened by this planning workflow.

## 9. Snapshot and Derived Selection

`CatalogSnapshot` contains immutable typed records/indexes, release identity, catalog revision,
artifact fingerprints, exact scope/date membership projections, listing eligibility, and
review/representation views. It contains no credentials or user selections.
Cached snapshots are reused only after entry/artifact identity checks.

Existing session namespaces keep region/classification/version/sector/industry/stock IDs and
context fingerprints. Parent/release changes intersect selections with current valid members;
clear only invalid choices. Peer cohorts use effective reviewed membership before display filters.
File updates never relabel stale selected rows as current or change raw financial/price evidence.
