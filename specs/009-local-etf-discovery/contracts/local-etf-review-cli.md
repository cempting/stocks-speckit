# Local ETF Review CLI Contract

> **2026-10-31 — pre-cutover interface:** Resource defaults, database flags/schema prerequisites,
> SQL publication, and report behavior below document implemented feature 009.
> [Feature 010](../../010-manifest-csv-catalogs/spec.md) replaces source registration and
> persistence with manifest-registered optional research inputs and durable file histories.
> Preserve accepted grammar, safe paths, evidence identities/currentness, exact decisions,
> reports/errors, and coherent approval/provenance semantics; migrate or explicitly retire old
> command paths with guidance. New file formats/CLI flags await 010 planning, not this historical table.

These are implemented interfaces for feature 009, with report version `local-etf-discovery-1`.
Entry point remains `python -m market_leadership.universe_admin`.
See [data model](../data-model.md) for persisted evidence and review transitions.

## 1. Catalog Selection and Accepted Grammar

Default resource aliases and descriptors:

| Alias | Default root | Industry catalogs |
|---|---|---|
| `sector_rotation` | `~/Documents/learn/invest_screener/sector_rotation` | `src/constants.py:US_INDUSTRY_ETFS`, `src/constants.py:EUROPE_INDUSTRY_ETFS` |
| `analyzer` | `~/Claude/Projects/SectorStockScreener/Analyzer` | `config.py:INDUSTRY_ETFS` |
| `stockviewer` | `~/Claude/Projects/SectorStockScreener/stockviewer` | None known; missing root is reported, not substituted |
| `stockfinder` | `~/Claude/Projects/SectorStockScreener/stockfinder` | `src/stockfinder/data.py:INDUSTRY_ETFS` |

Read each selected file once. Select named top-level catalogs only, not function-local
variables, stock universes, narrative documents, arbitrary directories, or runtime outputs.
Named sector/index/commodity context catalogs listed in [research](../research.md) are read only
to attach unreviewed qualification facts to candidate evidence.

```text
industry_catalog := Name "=" dict_literal
                  | Name ":" annotation "=" dict_literal
dict_literal     := ordered occurrences of string_literal ":" string_literal
```

- Accept `Assign` with a single name target and `AnnAssign` with a name target. Ignore annotations.
- Accept non-empty decoded string keys/tickers; preserve originals and declaration order/locations.
- Extract each `ast.Dict` entry directly, including repeated keys with equal or different tickers.
  Do not import the file, call `eval`/`exec`, or construct/evaluate the full dictionary.
- Named sector/index context accepts the same string/string grammar.
- Only named `METAL_PROXIES` context accepts `string symbol -> (string name, string category)`.
  It produces context, never an industry candidate.
- Reject unsupported selected expressions: calls, names, subscripts, attributes, f-strings,
  comprehensions, unpacking/merges, numeric values, nested dictionaries, and other dynamic forms.
  Do not resolve references even if a referenced catalog also appears in the file.
- Keep supported literal sibling occurrences with per-entry diagnostics when a selected catalog
  is partial; those partial-catalog occurrences cannot independently support new approval.
- Unselected dictionaries are excluded, not inspected as mapping failures. Missing selected
  catalogs and non-dictionary selected assignments receive explicit diagnostics.
- Default context names are optional: a completely parsed file may establish no declarations
  for an absent context catalog. Explicitly requested descriptors and default industry catalogs
  are required; their absence receives a diagnostic rather than an invented empty catalog.
- Preserve an explicit catalog-prefix region label, but never infer scope for unqualified
  INDUSTRY_ETFS from the application's selected region or nearby runtime code.
- Source sector aliases are unreviewed labels, not classification crosswalks.

Expand explicit home paths, resolve catalog files inside their configured root, and reject path
traversal/symlink escapes. A descriptor cannot select credentials, private portfolios/watchlists,
generated logs, caches, or unrelated input. Decode using the source encoding without executing it.
Diagnostics contain file/catalog/line/category, not unrelated source snippets or exception text
that reveals private source content.

## 2. Collect Candidates

```text
collect-etf-candidates
  [--database PATH]
  [--root RESOURCE=PATH]...
  [--catalog RESOURCE=RELATIVE_PATH:CATALOG]...
```

`--root` replaces the default root for one of the four known aliases; unspecified aliases remain
in the inspection manifest. `--catalog` adds a selected named literal catalog within that root.
The known catalog names determine industry versus context role; unsupported names are reported
explicitly, not assigned an inferred role. These arguments permit correcting stockviewer and
selecting its actual supported catalog without an unrestricted scan.

An initialized schema 3 database is required. Collection is independent of populated hierarchy.
It persists only immutable research evidence and inspection history. It never populates a
classification, source approval, listing, representation, or basket.

Stdout is one JSON object:

| Field | Meaning |
|---|---|
| `report_version` | `local-etf-discovery-1` |
| `collection_run_id`, `observed_at` | Persisted attempt and explicit observation time |
| `status` | `complete`, `partial`, `failed` |
| `resources` | All four aliases with roots, descriptors, outcomes, completeness, counts, issues |
| `candidates` | Stable candidate IDs, original labels/tickers, declared scope, all occurrence IDs/locations, qualification issues |
| `context` | Selected sector/index/commodity declarations; never industry coverage |
| `changes` | Compared with prior complete observations: changed, removed, or unknown support |

Sort resources/candidates/occurrences deterministically. Timestamps and run IDs are attempt
metadata; unchanged candidates/evidence reuse their identities and never append manual reviews.

Exit 0: complete inspection, including a legitimately empty readable catalog.
Exit 2: partial or failed collection, retaining valid partial research and explicit statuses.
All roots unavailable/unsupported is failed, not a successful empty inventory. A storage failure
emits an actionable error and cannot claim a persisted successful collection.

## 3. Review Consolidated Candidates and Hierarchy Coverage

```text
review-etf-candidates
  --region REGION --classification CLASSIFICATION --as-of YYYY-MM-DD
  [--collection-run RUN_ID] [--database PATH]
```

Default run is the latest persisted collection; a specific run can be viewed as historical
research. Validate requested region/classification/date explicitly. Invalid scope is an error,
not a success-shaped empty hierarchy.

Return versioned JSON containing:

- Collection ID/time/status and resource issues, including incomplete-source warnings.
- Every active reviewed industry/sub-industry with exact IDs and existing representation status.
- Candidate evidence, provisional label matches, explicit reviewed classification bindings,
  conflicts, decisions, qualification issues, and selected-review currentness.
- A separate `unbound_candidates` list for labels without reviewed node bindings, unknown scope,
  and evidence belonging to another scope. Nothing silently inherits the requested region.
- `no_candidate` for nodes with no relevant candidate; candidate absence never drops hierarchy rows.

Spelling/whitespace/punctuation similarity is not an approved alias. Only explicit accepted
decisions with exact-scope confirmation establish reviewed label equivalence for the same
logical source label/scope; rejection or source-level sector aliases do not.

Different ticker choices remain visible. A selected acceptance is a reviewer decision, not
source-order prioritization or approval coverage. Currentness uses the latest persisted
observation of supporting catalogs and displays that observation time; there is no hidden
rescan, freshness claim beyond the observation, background polling, or provider request.

## 4. Record an Explicit Candidate Decision

```text
review-etf-candidate
  --candidate-id CANDIDATE_ID --collection-run RUN_ID
  --region REGION --classification CLASSIFICATION --entity-id NODE_ID --as-of YYYY-MM-DD
  --decision {accept,reject} --reason TEXT --review-reference REFERENCE
  --evidence-id OCCURRENCE_ID...
  [--confirm-etf-identity] [--confirm-exact-scope] [--confirm-suitability]
  [--issue-resolution ISSUE=RATIONALE]...
  [--database PATH]
```

Require at least one selected persisted candidate occurrence from the run, an exact active
reviewed node at the explicit as-of date, and non-empty reason/reference. Do not infer the
hierarchy date from the file observation clock.
The three confirmations and non-empty resolutions for applicable warnings are required for
acceptance, not rejection. A confirmation records an actual human assessment, not a substitute
for imported listing/source approval. Known index/non-ETF evidence is not ETF-acceptable.

Acceptance explicitly binds/chooses this candidate for the node and supersedes the prior research
selection, preserving history. Rejecting the selected candidate clears it; no older alternative
is restored. Other rejections do not clear a selected candidate. These operations do not modify
runtime representations or the universe revision.

Acceptance resolves the alternatives already present in the referenced run without hiding them.
New/changed conflicting evidence for that reviewed node/label scope in a later observation marks
the selection for re-review rather than choosing another ticker automatically.

Return JSON with `review_id`, decision, exact target, selected evidence, confirmations/resolutions,
and `selected_review_id`/selected-review state. Repeating collection creates no extra decision; a new explicit manual
review invocation is an intentional new event.

## 5. Existing ETF Approval with Optional Provenance

```text
approve-etf
  --region REGION --classification CLASSIFICATION --entity-id NODE_ID
  --exchange EXCHANGE --symbol VERIFIED_LISTING_SYMBOL
  --source-id REVIEWED_SOURCE --approval-reference APPROVAL
  --effective-from YYYY-MM-DD [--effective-to YYYY-MM-DD]
  [--candidate-review-id REVIEW_ID] [--database PATH]
```

Without the new optional flag, keep feature 008's existing interface and behavior.
With it, require the current accepted selection, complete current supporting observations,
exact candidate/node identity, resolved qualifications, and candidate ticker equal to the
verified listing/provider identity. Historical/changed/removed/unobservable research is
ineligible for new provenance-linked approval until explicitly recollected/re-reviewed.

Every existing source approval, verified-primary-listing, region, hierarchy, date interval,
and overlap check still applies. Research review does not create missing listings/sources or
bypass matching approval references.

Persist representation and provenance atomically, including the idempotent-existing-mapping
path. Link failure rolls back both evidence attachment and mapping/revision changes. Existing
approval evidence remains retained; additional evidence links do not overwrite it.

Existing `review-representations`, `review-listings`, `approve-basket`, `represent`, and Discovery
remain unchanged. No source collection is initiated by these existing flows.

## 6. Error and State Guarantees

- JSON stdout and diagnostics stderr remain separate; no broad silent exception handling.
- CLI/domain/storage/partial-collection errors exit 2; successful read/decision commands exit 0.
- A failed catalog is unknown, not removed; only a later complete observation proves removal.
- Unrelated missing roots do not invalidate currently complete selected support.
- Data collection, rejection, source changes, and failed promotion never overwrite an approved ETF
  or basket or fabricate momentum.
- Valid basket administration remains the existing explicit fallback, not a generated result of
  having no suitable candidate.
