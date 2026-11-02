# Research: Stock Identity and Industry Membership Revision

**Date**: 2026-11-01. Repository inspection and bounded test/011-contract research.
No external data research, source approval, or application changes.

## R1 - Explicit version boundary

**Decision**: Retain entry format `market-catalog-entry-1`; explicitly dispatch
release v1/v2 schemas and parsers. V2 requires custom scheme metadata and stock
grammar. V1 operational rank/cardinality/headers remain unchanged; only a typed
nonoperational migration-report history extension is added for restoration.

**Rationale**: [HierarchyNode](../../src/market_leadership/domain/catalog.py):408-419
rejects industry parents; validation at 1311-1324 rejects active distinct assignments.
[load_release](../../src/market_leadership/infrastructure/catalog_files.py):745-750
accepts only release v1. These constraints exist in runtime code despite older 010
documents describing implementation as pending.

**Alternatives considered**: Globally loosening v1 data validation or relabelling a
legacy classification without review would alter historical authority.

## R2 - Logical separation without replacing joined files

**Decision**: Keep one stock CSV per region, add RowKind, and target one exact
IndustryId per membership. Instrument rows assert no classification. Project
immutable instruments, memberships, listings and member views from captured records.

**Rationale**: [StockRow](../../src/market_leadership/domain/catalog.py):491-535
mixes listing copies with assertions but already supplies logical MembershipId.
Typed projections solve ownership and unassigned lookup without a database redesign.

**Alternatives considered**: Three normalized CSVs add join/migration surfaces;
fake "unassigned" memberships fabricate classification; representative assertions
discard overlap/provenance.

## R3 - Dated forest, iterative selected-subtree traversal

**Decision**: One optional industry parent, inherited sector, all-depth support.
Validate active parent mappings at interval boundaries. Traverse the requested
active subtree using direct membership/children indexes, not full transitive closure.

**Rationale**: [catalog.py](../../src/market_leadership/domain/catalog.py):1184-1212
rejects disjoint parent changes; indexing in
[catalog_files.py](../../src/market_leadership/infrastructure/catalog_files.py):901-920
only adds sector/industry/one child. A date-specific forest supports reviewed history.

**Alternatives considered**: Recursion imposes an accidental depth ceiling;
union-of-all-dates cycle detection rejects valid noncontemporaneous reparenting;
precomputed ancestor/member combinations multiply storage and invalidation work.

## R4 - Selected industry is independent of direct assertion

**Decision**: Return one instrument with all applicable direct assertions and
independently resolved listing eligibility. Pass selected node/scope/date explicitly
to peer adapters.

**Rationale**: [membership_entry](../../src/market_leadership/infrastructure/stock_membership.py):44-83
derives industry from one row, which would assign an arbitrary child context to
parent rollups. [score_industry](../../src/market_leadership/application/score_industry.py):50-66
requires unique active instruments; deduplication precedes calculation.

**Alternatives considered**: First-row/source-priority selection, issuer-deduplicated
cohorts or averaging scores across industries change requested behavior.

## R5 - Independent lookup, selections and caches

**Decision**: Host local stock lookup before Discovery's classification early returns.
Separate instrument/listing selection from comparison context and retain applicable
IDs by intersection. Keep valid industry results under their complete context keys.

**Rationale**: [Discovery](../../src/market_leadership/ui/workflows/discovery_page.py):655-670
returns when classification is missing; detail is current-membership-only at 403-443.
[reconcile_selection](../../src/market_leadership/domain/stock_selection.py):57-68
clears all stocks on parent/date changes even when overlapping IDs remain valid.

**Alternatives considered**: New root browser, arbitrary remote ticker search,
invalid retained scores, or blanket cache/selection clearing.

## R6 - Share issuer facts, not listing-bound bundles

**Decision**: Reuse 011's reviewed association/acquisition/store boundary. Add a
normalized issuer-owned statement-fact projection and separately verified consumer
attachments. Research may be issuer-shared; prices, capitalization, trading currency
and eligibility remain separately contextualized.

**Rationale**: [011 data model](../011-company-risk-evidence/data-model.md):9-42
has nullable issuer identity, per-listing bindings and no whole cross-listing
financial-bundle substitution.
[011 acquisition](../011-company-risk-evidence/contracts/company-evidence-acquisition.md):19-39,66-79
requires profile corroboration and binding/permission checks outside cache hits;
financial/research TTLs are 3,600/86,400 seconds.
Current [FundamentalRequest](../../src/market_leadership/domain/fundamentals.py):29-49
and [cache](../../src/market_leadership/ui/cache.py):108-138 are symbol keyed, not a
completed issuer-verification/reuse boundary.

**Alternatives considered**: Rewriting bundle symbols, guessing an issuer from
CompanyId/name/ticker/domain, duplicating collectors, or claiming acceptance with
stubs. [plan.md](plan.md) records exact planned 011 prerequisites and graph reconciliation.

## R7 - Immutable reports, historical governance and restoration

**Decision**: Register immutable membership_migration JSONL reports. Preserve audit
vocabulary and byte-immutable legacy archives. Newly migrated scopes do not retarget
historical NodeReview/representation records; validate their original scope against
captured source/retained history and project only applicable current approvals.

**Rationale**: [publisher](../../src/market_leadership/infrastructure/catalog_files.py):1079-1094
requires audit-prefix and exact archive-hash retention. Existing
[governance projection](../../src/market_leadership/infrastructure/catalog_files.py):521
must distinguish historical assertions from active applicability after scope changes.
Restoration must compose prior data with full current governance, not publish an
old short ledger against a newer parent.

**Alternatives considered**: Unregistered report files, appending into a frozen
archive, direct CURRENT editing, deleting historical approvals, automatic rollback,
or silently interpreting old approvals as new-scope permission.

## R8 - Existing measured baseline, not an invented SLA

**Decision**: Retain existing performance bounds and source-free fixture counters.
Extend overlap/depth at the same 10,000-instrument scale, keeping 64 MiB/1 MiB limits.

**Evidence**: [Performance test](../../tests/integration/test_catalog_performance.py):16-104
uses 10,000 instruments, 11 sectors, 500 nodes, cold <=5 s, warm <=1 s and no warm
reparse. It passed locally on 2026-11-01: 1.49 s test-call duration, 2.13 s total
pytest duration. These do not separately measure phases or prove future v2 behavior.

**Alternatives considered**: Arbitrary volume/latency promises, live-network timing
tests, and treating runner duration as exact query latency.

## R9 - Approved acceptance-boundary refinements (2026-11-02)

**Decision**: SC-009 counts repeats per unchanged, still-valid issuer/evidence
request. Different cohorts may need different peers, but new requests require
explicit loading for the active view. Test A -> B -> A with separate first/repeat/
unrelated counters and no eager universe prefetch.

**Decision**: The narrow 011 dependency includes CompanyResearchClaim and
research-scope envelope validation plus eligible stored-snapshot attachment.
Positive business-model/moat reuse across independently verified share classes
must preserve provenance, separate research permissions and historical cutoff;
financial approval cannot authorize denied/revoked research. New collectors remain
outside 012.

**Decision**: History ownership is bounded by the requested range and reviewed
listing/issuer continuity, not membership dates. Mixed predecessor/successor
responses require observation-level exclusion before display/calculation,
including on cache reuse. Unverifiable intervals stay explicitly unavailable.
Existing dated listing/source references supply the boundary; charts do not
require new financial-profile collection.

**Rationale**: The user explicitly approved these refinements after cross-artifact
analysis. They make existing FR-002/FR-004/FR-015 and SC-001/SC-009 testable without
changing classification scope, calculations, source permissions or runtime providers.

**Alternatives rejected**: A global zero-call promise for uncached peer cohorts;
financial-only tests as proof of qualitative reuse; ticker/cache identity as proof
that every returned price observation belongs to the selected issuer.

## Outcome

No unresolved technical clarification remains. Missing v2/011 production behavior
is an explicit implementation dependency, not completed capability.
[Quickstart](quickstart.md) separates current baseline from prospective acceptance.
