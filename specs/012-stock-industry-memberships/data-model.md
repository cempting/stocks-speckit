# Data Model: Stock Identity and Industry Membership Revision

Target model, not a migrated catalog. See [catalog v2](contracts/catalog-v2.md) and
[migration](contracts/membership-migration.md) for physical grammar and lineage.

## 1. Company facts and reviewed consumer attachment

Financial statements, reporting currency/basis, publication evidence, descriptions
and moat claims belong to the issuer. Do not add these to stock rows or use CompanyId
as financial-attachment permission.

Reuse [011 CompanyAssociation](../011-company-risk-evidence/data-model.md):
association_id; instrument_id/listing_id/region_id; nullable company_id;
provider_id/provider_symbol/exchange/trading_currency; catalog_revision;
effective_from/to; optional issuer_key/CIK/issuer_domain; binding_reference,
identity_evidence, state and reason.

Association identity remains per consumer instrument/listing/source/effective binding,
not company identity. A separately reviewed common issuer reference may own reusable
statement facts. Without such a reference, do not coalesce null IDs or equal domain,
name or ticker strings.

The shared projection contains only statement observations with original source,
reporting currency, scale, period/basis, definitions, derivations and provenance.
Every consumer independently passes 011's reviewed binding/profile/permission gate.
Retain original acquisition listing identity; never rewrite a bundle symbol to
simulate another share class. Capitalization, trading currency, listing history and
instrument eligibility remain separate. No implicit FX conversion or source pooling.

Stored qualitative reuse separately uses 011's CompanyResearchClaim and research-scope
request/outcome/snapshot envelopes, not the statement projection. Retain business_model
and competitive_advantage topics, claim kind/qualifications, named source where
required, original provenance/capture and state/reason. Each consumer needs an
independently reviewed issuer association and its own eligible research binding/
permissions; a financial grant is insufficient. Recheck current permissions on
reuse, block denied/revoked/expired uses and exclude captures after the requested
historical UTC day's end. Reuse 011's research age/limitation rules without new
collectors, inferred claims or document import tooling.

## 2. StockInstrument

| Field | Invariant |
|---|---|
| instrument_id | Stable nonempty security identity; separate share classes differ |
| region_id | Exact retained regional identity |
| company_id | Nullable reviewed identifier/hint, not issuer-attachment proof |
| name | Nonempty display label, not a join key |
| resolution_state | identified or placeholder; lookup requires identified |

Project by exact instrument identity from all regional stock records. Repeated
metadata agrees; membership is not required for existence. Blank CompanyId values
do not establish a shared company.

## 3. Listing

Reuse Listing fields/validation: listing_id, instrument_id, region_id, instrument_type,
ticker, provider_symbol, name, exchange, currency, is_primary, resolution_state,
independent period, source_id and approval_reference.

One instrument may have several listings. Copies of ListingId agree on one dated
record. Overlapping primary listings and ambiguous effective provider symbols
remain errors. Missing/unverified metadata is retained without authorizing requests.

Lookup history uses an explicitly resolved eligible listing at the requested date.
Member/cohort requests also require valid membership context and verified primary
listing. Never merge or silently substitute histories.

The permitted observation window is the requested range intersected with reviewed
dated listing/issuer continuity, never membership dates. Verify returned observation
dates as well as requested bounds, including after cache reuse: a symbol response
may contain a predecessor issuer. Exclude predecessor/out-of-window observations
before charting/calculation, disclose unverifiable intervals and do not fabricate
zeroes or silently bridge them. Missing continuity produces affected-history
unavailability, not a guessed range. Use existing dated listing/source identity
references; no new financial-profile requirement or automatic issuer grant is
introduced for charts. History prior to membership remains eligible when continuity
is independently reviewed.

## 4. ClassificationScope and HierarchyNode

Scope stays `(region_id, classification_id, classification_version)`.
V2 classifications add scheme_kind=custom; release v2 defines overlap semantics.
One operational scope is explicitly resolved per region/date, not two overlay views.
Retained v1 scopes keep their original declared meaning.

Hierarchy fields remain scope, NodeId, NodeType, Name, SectorId, ParentIndustryId,
EffectiveFrom/To, SourceId, ApprovalReference and ApprovalOrigin.

- Sector: self SectorId, no parent.
- Root industry: one sector, no industry parent.
- Nested industry: one non-sector parent in identical scope; inherited root sector
  must match the stored corroborating SectorId.
- industry/sub_industry types preserve labels and representation-role checks,
  not a depth limit. A sub_industry has a parent; either type may parent a non-sector
  node in v2.
- A stable node may have disjoint reviewed parent periods. Node identity/type remains
  consistent within a scope; overlapping periods fail. Type/meaning changes require
  a separately reviewed classification version.
- Validate child/ancestor/sector/classification period coverage and the active forest
  at every interval-change boundary. Reject contemporaneous cycles, not merely a
  cycle in the union of noncontemporaneous historical edges.
- Traverse iteratively, with finite input limits but no semantic depth cap.

Version-specific validation receives trusted manifest format explicitly, with v1
as default for existing direct construction. Rows cannot select relaxed validation.

## 5. IndustryMembership

| Field | Invariant |
|---|---|
| membership_id | Stable logical association identity, shared by listing copies |
| scope | Exact region/classification/version |
| instrument_id | Existing retained instrument |
| industry_id | One exact non-sector target at any supported depth |
| effective_from/to | Inclusive reviewed period covered by hierarchy/classification |
| source_id / approval_reference | Valid reviewed source and approval |
| review_state | reviewed for operational membership |

Concurrent different targets are valid in v2, including across sectors. Copies of
MembershipId agree on all assertion fields. Compatible independent sources may
retain distinct assertions. Parent inclusion is query-derived, not a newly approved
direct membership. Enrichment does not modify any assertion.

## 6. CatalogMember and snapshot projections

CatalogMember contains instrument metadata, all relevant reviewed membership
identities/direct targets, and independently resolved listing eligibility. It does
not designate one representative assertion as a stock's sole industry.

Indexes: instruments by region/identity; listings by ListingId/dated instrument;
memberships by scoped target and instrument; nodes by scope/identity/period, with
active children by parent. Industry/sector queries traverse active descendants and
union effective direct members, deduplicating instruments before peer calculation.

Lookup searches retained identified instruments locally, including historical members
currently unassigned. It is independent of classification activation.
Historical audit approvals retain original scope and source provenance; validate
them against captured source or explicitly retained parent-chain snapshots. Do not
require old scopes to become current classifications or reinterpret old approvals.

## 7. PeerComparisonContext

Fields: selected scope/non-sector node; membership_as_of; unique eligible instrument/
listing identities; cohort_fingerprint; calculation-rules revision; financial
observation/vintage fingerprints used by the result.

Selected parent/child context is explicit. Two share classes remain two instruments.
Preserve existing sufficiency, ties, TTM/publication, currency and dated-capitalization
eligibility; shared issuer facts never imply eligible capitalization.

Canonically hash selected scope/node/date, eligible identity set and relevant
eligibility/approval inputs. Physical row/assertion IDs, unrelated catalog edits,
transport and research-only history do not multiply/change the cohort arbitrarily.
Recheck catalog integrity/permissions before reuse. Fact changes affect result keys
even when the membership cohort is unchanged.

Acquisition counters are per issuer/evidence request with date/basis/source/schema,
binding/policy compatibility and freshness held valid. Switching A -> B -> A reuses
each such request; it does not imply that different cohorts have identical evidence
requirements. Previously unrequested peers require explicit loading for the active
view, with their necessary first requests counted separately. No context-switch
acquisition or eager whole-universe prefetch is allowed to manufacture reuse.

## 8. State and lifecycle

Instrument/listing selection is separate from comparison scope/node/date.
Deep-Dive multiselections retain the intersection with the new filtered eligible set.
A valid singleton detail may stay open after membership expiry, without peer context.

Migration: prepared -> reviewed approved reconciliation -> validated candidate ->
staged -> published. Preparation grants no approval; incompatible/new assertions
stay non-operational until separately reviewed. Invalid candidates leave CURRENT intact.

Retain immutable releases, audit sequences, legacy archives and registered reports.
Restoration publishes target data semantics with full current governance history,
never rewriting the original target. New readers support only an explicit typed
report-history extension for v1 restoration, without loosening v1 stock/hierarchy
validation. Unsupported formats, stale sources, bad hashes and concurrent publishers
produce actionable failures.
