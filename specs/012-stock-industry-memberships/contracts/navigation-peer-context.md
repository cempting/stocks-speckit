# Contract: Stock Lookup, Membership Paths and Peer Context

**Status**: Target behavior for existing root workflows; lookup placement follows
[015](../../015-dedicated-stock-lookup/spec.md), identity safeguards remain owned by 012.

## Lookup and navigation

Find a stock provides retained-identified-instrument lookup in the selected
release/region, independently of Discovery classification/empty-sector early returns. Labels/reviewed
symbols may filter candidates, but selection resolves an exact InstrumentId.
Ambiguous matches require explicit choice; do not create records or request an
arbitrary user-entered remote ticker.

Lookup makes zero market-data, financial or research calls. Detail opening uses only
the explicitly resolved eligible listing and existing price controls; bypass unrelated
industry-member prefetch for the lookup-detail path. Financial/research collection
still requires explicit loading and 011 eligibility. Unassigned/unlisted stocks open.

Industry controls/breadcrumbs show complete same-sector ancestor paths. Disambiguate
duplicate labels by path/stable ID. Keep empty nodes and distinguish direct coverage
from rollup inclusion. Details list every effective direct membership and its path.
Opening through a parent rollup establishes that parent as explicit peer context.

Preserve Discovery, Industry Deep-Dive, Yahoo Classification Preview and Find a stock,
mandatory stock columns, chart periods/bases, metric formulas, three-component aggregate
rules and source selection. Discovery must not render lookup controls.
On 013 adoption, every workflow consumes the same pinned validated service context;
retained local replica reads are not a separate lookup authority.

## Session state

Use market_leadership.stock_lookup.* for the dedicated lookup, keeping Discovery's
market_leadership.progressive_discovery.* and existing market_leadership.screening.*
namespaces distinct. Separate instrument/listing selection from comparison scope/node/date
and context-keyed explicitly loaded peer results.

Ordinary reruns and compatible cutovers retain valid identities. Deep-Dive selections
retain the intersection with the new eligible filtered set, including overlap.
Singleton lookup detail may remain open after membership expiry.
Clear only invalid dependent listing, comparison or instrument selections, with a
reason; never substitute the first row. No selections enter shared cached data.

Industry A/B results coexist under distinct complete keys while valid; B must not
overwrite A. Revalidate retained keys and discard only invalid results.
A sector-only/unassigned detail has no default industry score: select an applicable
non-sector comparison context explicitly.

## Comparative calculation

Resolve the industry's effective direct/descendant union, verified primary listings
and existing eligibility; deduplicate before score_industry/calculate_peer_scores.
Keep five-peer sufficiency, ties, TTM/publication, dated capitalization/currency
and missing-value rules. Two share classes remain two instruments.

Each result identifies scope/version, selected industry, membership date, eligible
IDs/cohort fingerprint, calculation revision and fact observation/vintage basis.
No cross-industry averaging, issuer-deduplicated cohorts or arbitrary child context.
Missing point-in-time live facts remain insufficient, not repaired by research.

## Evidence/cache keys and gates

| Layer | Required identity/context |
|---|---|
| Catalog query | Verified integrity, scope/node/date and relevant data revision |
| Listing history | Provider, exact dated listing/symbol, range/request parameters and reviewed observation-continuity context |
| Company statements | Selected source, reviewed common issuer reference, original acquisition identity, date/basis/schema and binding/policy compatibility |
| Consumer attachment | Each instrument/listing's reviewed dated binding, profile corroboration and current permission |
| Peer result | Industry/scope/date, eligible cohort, rules and attached fact/vintage fingerprints |

Industry changes alone do not invalidate raw eligible facts/history. Issuer/listing/
binding changes revalidate fresh, cached and historical attachment. Global catalog
revision or transport alone must not recollect unchanged issuer evidence.
Retain 011 financial/research TTLs of 3,600/86,400 seconds and targeted refresh.

Only normalized issuer-owned statement subsets can be shared with independently
verified consumers. Whole listing-bound bundles, trading currencies, prices,
capitalization and instrument eligibility are not substitutable across share classes.
CompanyId, membership approval, copied references or equal ticker/name/domain strings
cannot authorize sharing. Missing gates produce unavailable evidence.
Enrichment never edits classification/review records.

## Acceptance observations

Injected loaders assert exact cohort sets and counts: zero calls during lookup;
zero repeats per unchanged, still-valid issuer/evidence request on industry switches;
explicit-only first loads for newly required peers with no universe prefetch; separate listing
histories; no unverified request or successor attachment; no duplicate eligible ID;
explicit insufficiency for truly missing facts. AppTest preserves existing tabs/
columns and exercises deep paths, lookup and valid selection retention.

## Refined acceptance boundaries (2026-11-02)

### Per-request acquisition accounting

For A -> B -> A with overlapping but different cohorts, identify counters by reviewed
issuer/evidence request, applicable date/basis/source/schema and valid binding/policy/
freshness context. Already acquired valid requests incur zero repeats. A newly
required peer is not a repeat request: it may load only after explicit loading for
the active view. Context switching alone makes zero such acquisitions. Test first
requests separately from repeats and unrelated acquisitions; preloading the whole
universe or both cohorts on navigation is not an acceptable passing strategy.

### Stored qualitative evidence

The minimum 011 slice includes CompanyResearchClaim and research-scope envelopes,
not only financial observations. A permitted stored business-model/moat snapshot
can attach to two independently verified share classes while preserving claim
kind, source/locator, qualifications, capture and original provenance. Research
identity/permissions are separate from financial approval. Check permission denial,
revocation/expiry and historical capture cutoff before cached/stored attachment;
later captures cannot fill earlier historical views. Preserve existing stale/
limited/blocked states. No new collectors, inferred claims, document import path
or permission grants are required.

### Listing observation ownership

Intersect the requested range with reviewed dated listing/issuer continuity, not
industry membership. Bound requests where possible and validate every returned
date before charting/calculation, including on cache hits; current-date listing
eligibility and different cache keys cannot prove ownership of the full lookback.
Exclude predecessor observations from a response spanning ticker reuse and report
unverifiable intervals as unavailable. Never fill gaps with zeroes, another listing
or silently bridged history. Include tests immediately before/on/after reviewed
continuity boundaries and retain valid history before/after membership dates.
Use captured dated listing/source identity evidence without making charts depend
on financial-profile acquisition or granting research eligibility.
