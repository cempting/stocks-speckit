# Data Model: Local ETF Mapping Discovery

> **2026-10-31 alignment — migration reference:** The implemented schema 3 tables below are
> legacy export/reconciliation inputs, not the post-cutover storage design.
> [Feature 010](../010-manifest-csv-catalogs/spec.md) requires manifest-registered research and
> file-only immutable runs/evidence/decisions/provenance. Account for every table relation,
> identity, selected-evidence association, and review ordering; preserve semantic/currentness
> rules without retaining SQL catalog dependencies. Exact audit-file formats await 010 planning.

Implemented additive schema version: **3**. Existing regions, classifications, industry/sub-industry
nodes, sources, listings, ETFs, baskets, and approval semantics are preserved.

Scalar lookup/foreign-key/status fields are stored in SQL columns; selected record metadata is
stored in validated JSON payloads, not copied source files. RegionDatabase owns all persistence.
Candidate/reconciliation/currentness projections remain unpersisted, and write APIs append
immutable runs/evidence/decisions/links rather than replacing historical records.

## 1. Local Resource Inspection / Collection Run

Storage: `etf_collection_runs`.

| Field | Meaning / invariant |
|---|---|
| run ID | Unique inspection attempt; timestamps are not candidate identity |
| observed at | Injected UTC observation clock |
| status | `complete`, `partial`, or `failed` |
| resource manifest | All four aliases, canonical roots, requested descriptors and outcomes |
| catalog outcomes | File/catalog identity, completeness, content identity, counts, bounded diagnostics |

Resource statuses: `inspected`, `inspected_with_issues`, `missing`, `inaccessible`, `unsupported`.
A readable inspected catalog can contain zero relevant declarations. Incomplete reading does not
establish absence. Every resource appears, including missing stockviewer. Metadata stores safe
paths and issue categories, not unrelated source text.

Collection/evidence membership: `etf_collection_evidence(run_id, evidence_id)`, composite primary
key with foreign keys. A new attempt may reuse immutable evidence from an earlier run.

## 2. Mapping Evidence Occurrence

Storage: `etf_mapping_evidence`.

| Field | Meaning / invariant |
|---|---|
| evidence ID | Deterministic source/catalog-snapshot/declaration/location identity |
| candidate ID | Grouping identity for industry declarations; context occurrences are distinguishable |
| logical source | Resource alias, canonical root, relative file, catalog name |
| catalog content ID | Hash of extracted declarations/allowed metadata, excluding unrelated source values |
| original label/ticker | Exact decoded literals; no taxonomy rewrite |
| normalized ticker | Trimmed/uppercase lookup form; retain suffixes and original string |
| declared catalog type | `industry`, `sector_context`, `index_context`, `commodity_context` |
| declared region/classification/node level | Source-declared labels where available; otherwise null |
| declaration ordinal | Distinguishes repeated occurrences, including identical duplicate keys |
| location | One-based start/end lines and AST byte-column offsets |
| allowed context | Literal display/category/sector/index claims and qualification annotations only |
| semantic fingerprint | Declaration values/scope and relevant qualification evidence used for currentness |
| first observed at | Original observation clock; immutable evidence is not overwritten |

Do not save complete files, raw unrelated declarations, executable code, private watchlists/
portfolios, comments, or exception source snippets. Retain approved evidence even if sources vanish.

Evidence IDs distinguish snapshots/locations. Currentness compares logical source and semantic
fingerprint rather than requiring unchanged line numbers. Changing a root to a different canonical
source requires explicit reconciliation/re-review.

## 3. ETF Mapping Candidate

Projection only; no additional candidate table.

Identity is a canonical hash of original label, normalized ticker, declared catalog type, and
declared region/classification/node-level labels, with null distinct from any declared value.
Projects contribute to one candidate only when that tuple agrees.

Expose all supporting occurrences, current/unknown/historical presence, source conflicts, and
qualification issues. Same-label/different-ticker choices remain separate. Sector/index/commodity
context is neither an eligible industry candidate nor an approved representation.

Collection never changes sources, verified listings, hierarchy membership, ETF/basket
representations, or the market-universe revision.

## 4. Classification Reconciliation / Candidate Review Decision

Storage: `etf_candidate_reviews`; reconciliation is embedded in each immutable decision.

| Field | Meaning / invariant |
|---|---|
| review ID / event order | Unique explicit manual decision; insertion order identifies later reviewer decisions |
| candidate ID | Must identify a persisted industry candidate |
| region/classification/node | Exact active reviewed target; sub-industries use existing industry node IDs |
| as-of date | Explicit hierarchy date selected by the reviewer; independent of the source observation clock |
| collection run ID | Inspection used for this decision |
| decision | `accept` or `reject`; never created automatically by collection |
| reason / review reference | Non-empty classification/suitability rationale and actual review reference |
| confirmations | Acceptance requires ETF identity, exact classification/region scope, industry suitability |
| resolved issues | Explicit reviewed rationale for applicable proxy/scope warnings |
| observed at | Injected decision clock |

`etf_review_evidence(review_id, evidence_id)` retains the explicitly selected non-empty set of
supporting occurrences with foreign keys. They must belong to the candidate and referenced run.

Acceptance confirms the source-label-to-exact-node relationship; unknown source region/taxonomy
is not rewritten into evidence. Prior explicit bindings for the same logical label/scope can
provide reviewed equivalences, but are not propagated across schemes/nodes. Identical spelling
alone is a provisional match.

Acceptance is suitability research, not source/listing approval or an active ETF. A known index/
non-ETF declaration cannot be promoted. Other proxy warnings require explicit assessment;
parent/sector substitution remains prohibited.

Selection/history:

1. Explicit acceptance selects that candidate for the node, superseding prior candidate selection
   without deleting history or altering an approved representation.
2. Rejecting the selected candidate clears that selection without resurrecting an older alternative.
   Rejecting a different candidate does not clear the selected candidate.
3. Re-acceptance is a new explicit event; collection never appends review decisions.
4. Currentness is derived: accepted evidence requires re-review when changed, removed, newly
   conflicting in its reviewed scope, or currently unobservable. Alternatives present in the
   decision's recorded run are resolved by the explicit selection and remain visible; new/changed
   conflicting evidence after that decision requires re-review. No older choice is substituted.

## 5. Currentness and Coverage Projections

Reuse `representation_worklist` as the approved hierarchy/status row set. Return every active
industry/sub-industry and separate unbound candidate evidence.

Per-candidate states: `needs_classification_reconciliation`, `needs_suitability_review`,
`conflicting_evidence`, `reviewer_accepted`, `reviewer_rejected`; nodes without candidates have
`no_candidate`. Several issue states may coexist. Approved status remains independently
`etf`, `basket`, `not_covered`, or `invalid`.

Selected review status: `none`, `accepted_current`, `accepted_needs_re_review`. Explain changed,
removed, or unobservable support rather than hiding the earlier acceptance.

Only complete inspection of the same catalog establishes removal. Partial/missing/failed input
establishes unknown presence; retain the last complete baseline and linked approvals. Unrelated
missing resources do not invalidate complete supporting catalogs. Metadata-only location moves
do not invalidate unchanged declaration semantics.

## 6. Approved ETF Representation Provenance

Storage: `etf_representation_provenance(representation_id, review_id, approval_run_id)`.
Composite representation/review primary key, with foreign keys to representation, review, and
current approval inspection.

The optional reviewed-candidate approval path requires:

- The explicit accepted selection is current for the exact region/classification/node.
- Selected evidence is observable in complete supporting catalogs and remains semantically valid.
- Candidate ticker matches the requested verified listing/provider identity, without inference.
- ETF identity/scope/suitability confirmations and applicable warning resolutions are complete.
- Existing source approval, listing, hierarchy, interval, and overlap checks all pass.

Insert/link representation and provenance inside the existing `BEGIN IMMEDIATE` transaction.
Failure leaves mapping, provenance, and universe revision unchanged. Existing idempotent mappings
must still acquire the explicit provenance link idempotently. Additional links are append-only;
they do not overwrite original approval evidence.

## Migration / Integrity

- Upgrade supported schema 1/2 atomically, retaining existing rows/revisions; reject unknown versions.
- Enforce foreign keys, unique membership/provenance keys, valid statuses, and non-empty decisions.
  Validate candidate/scope/evidence consistency before persisting a decision.
- Keep SQLite operations at `RegionDatabase`; collection/research methods cannot write approved
  representation tables or create listings/sources.
- Research-only rows and metadata-only provenance links do not increment the market-universe
  revision; actual representation changes retain existing revision behavior.
