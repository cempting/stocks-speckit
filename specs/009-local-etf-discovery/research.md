# Research: Local ETF Mapping Discovery

> **2026-10-31 alignment:** SQLite storage and existing approval-transaction decisions below
> describe the implemented legacy boundary. [Feature 010](../010-manifest-csv-catalogs/spec.md)
> supersedes storage/source registration with a manifest and durable file-only evidence/review
> history. Safe static extraction, deterministic identities, currentness, source privacy,
> exact decisions, and coherent approval/provenance publication remain required.

All planning unknowns are resolved. Research used local source inspection only; no source
project was imported/executed, and no online services were consulted.

## Decision: Extend the administration CLI, not the Discovery UI

**Rationale**: Feature 008 already exposes worklists, verified listings, and explicit ETF/basket
approval through [universe_admin.py](../../src/market_leadership/universe_admin.py).
Candidate collection and research decisions belong to that reviewer workflow. Discovery continues
to consume approved representations only.

**Alternatives considered**: A new Streamlit research screen, new root tab, and automatic collection
on widget reruns add unnecessary UI and runtime work and are outside the accepted scope.

## Decision: Use bounded catalog descriptors and static literal extraction

**Rationale**: The three available resources already contain directly declared mapping catalogs.
Use standard-library `ast`/`tokenize` to inspect module-level `Assign` and `AnnAssign` dictionaries
without evaluating annotations, imports, references, calls, or expressions. Iterate original
`ast.Dict` key/value nodes; building a Python dictionary first would lose duplicate declarations.

Verified source inventory:

| Resource/file | Relevant declarations | Observation |
|---|---|---|
| `sector_rotation/src/constants.py` | `US_INDUSTRY_ETFS`, lines 106-310; `EUROPE_INDUSTRY_ETFS`, lines 311-335 | 202 US literal occurrences, including eight repeated keys with identical values; 23 European occurrences |
| `Analyzer/config.py` | `INDUSTRY_ETFS`, line 336 onward | 73 literal industry declarations; annotations are absent |
| `stockfinder/src/stockfinder/data.py` | `INDUSTRY_ETFS`, lines 81-101 | 20 literal industry declarations |
| Requested `stockviewer` root | No readable directory during specification | Report `missing`; no substitute directory is assumed |

Examples: Semiconductors has SOXX and SMH alternatives; Biotechnology has IBB and XBI alternatives.
`sector_rotation` repeats Media/XLC at lines 195-196 and Medical Care Facilities/XLV at lines
192 and 259. These are occurrences to retain, not runtime dictionary winners.

The default descriptors select those three files and named literal industry catalogs. Named
sector ETF/index catalogs in the same files provide qualification context, never reviewed aliases:
`US_SECTOR_ETFS`, `EU_SECTOR_ETFS`, `EUROPE_SECTOR_ETFS`, `SECTOR_ETFS`,
`MORNINGSTAR_SECTOR_ETFS`, `ASIA_SECTOR_PROXIES`, and `ASX_SECTOR_INDICES`.
The named `METAL_PROXIES` catalog in stockfinder is a narrowly supported context-only
`symbol -> (display name, category)` literal, not an industry mapping catalog.

Allow an explicit additional descriptor inside a configured root. Do not recursively discover
arbitrary source files. An existing stockviewer root without a descriptor reports `unsupported`
with instructions to specify its catalog, rather than inventing a filename.

**Alternatives considered**: Importing projects, `eval`/`exec`, dictionary-wide `literal_eval`,
general AST interpretation, nested configuration resolution, and unrestricted repository crawling.
None is needed to recover the verified direct mapping declarations. Numeric/scoring dictionaries,
stock universes, watchlists, nested configuration shells, and fund-name inference are excluded.

## Decision: Preserve original scope and treat all local mappings as unreviewed

**Rationale**: `Analyzer` and `stockfinder` use unqualified `INDUSTRY_ETFS` names and provider labels.
Their target region/classification cannot be inferred from the selected application scope.
Explicit catalog prefixes retain a declared region label such as US or EUROPE, not an approved
regional identity. No inspected catalog supplies an approved GICS crosswalk.

Known local context can flag a symbol used as a sector, commodity, or index proxy. A caret-prefixed
index cannot be promoted as an ETF. Other local declarations, including broad/thematic claims,
are warnings requiring suitability review, not proof of instrument identity or verified holdings.
Never turn source sector aliases into reviewed classification equivalences.

**Alternatives considered**: Inferring GICS from spelling, assuming US for all sources, trusting a
catalog called INDUSTRY_ETFS, or choosing the source appearing first. These violate FR-007/FR-009.

## Decision: Derive candidates; persist immutable evidence and review events

**Rationale**: Extend the existing regional SQLite database to schema 3 with six small audit
tables: collection runs, evidence occurrences, collection/evidence links, review decisions,
review/evidence links, and representation/review provenance links. Candidates and classification
reconciliations are projections, not additional independently mutable tables.

Candidate IDs are hashes of original label, normalized ticker, declared catalog type, and declared
scope. Do not case-fold or rewrite classification labels. Evidence IDs additionally distinguish
the logical source, catalog snapshot, declaration ordinal, and location. Identical duplicate
occurrences remain separately attributable; unchanged collection reuses evidence rows.

Persist only selected mapping fields, allowed context, and declaration locations, not complete
source files, imports, comments, personal holdings, or watchlists. Fingerprints describe extracted
catalog content; unrelated configuration values are excluded.

Manual review events are append-only and bind an exact candidate/node relationship to selected
evidence occurrences. That binding is the reviewed classification reconciliation, including
unknown-source-scope confirmation; no generalized alias subsystem is required.

**Alternatives considered**: An overwrite-in-place JSON inventory loses historical approvals.
A second database, ORM, persistent candidate cache, independent alias service, and separate
source-version service add ownership boundaries without a current need.

## Decision: Distinguish changed, removed, and unobservable evidence

**Rationale**: A later complete inspection of the same catalog can prove changes or removal.
An unreadable/missing catalog cannot. Store per-catalog completeness in each collection manifest
and retain the last complete evidence baseline for comparisons.

A review needs re-review if its supporting declaration semantics, declared scope, or relevant
qualification evidence changed, disappeared, or cannot currently be observed. A line-number-only
move may create a new location snapshot without changing the reviewed declaration semantics.
Changes elsewhere in a catalog do not automatically invalidate unrelated declarations.

An overall partial run caused by unrelated missing resources does not invalidate a candidate
supported entirely by currently complete catalogs. Old data from failed catalogs is explicitly
historical/unknown, never silently current.

An explicit accepted selection resolves alternatives present in its recorded inspection without
deleting them. New or changed conflicting evidence for the same reviewed node/label scope after
that decision requires re-review; the original alternatives alone do not permanently block it.

**Alternatives considered**: Replacing the entire inventory per run, declaring missing input
removed, trusting stale successful runs for new approval, and marking every private/configuration
edit as a mapping change. These either lose evidence or create misleading approval state.

## Decision: Link provenance inside the existing ETF approval transaction

**Rationale**: [RegionDatabase.add_entity_representation](../../src/market_leadership/infrastructure/region_database.py)
already validates exact hierarchy scope, source/approval agreement, a verified primary listing
covering the entire effective interval, and overlapping mappings under `BEGIN IMMEDIATE`.

Add an optional candidate-review ID to that existing boundary and CLI command. When supplied,
validate the explicit accepted selection, current supporting evidence, exact node/symbol, and
reviewed qualifications, then insert representation and provenance in the same transaction.
Handle the existing idempotent-return path without omitting the provenance link. Keep the
representation's existing deterministic identity; provenance attachments are additive.

Candidate review is not `data_sources` approval. Listing import/source approval remains a
separate existing prerequisite. Collection and candidate review never create listings or sources
and never modify representations. They do not increment the market-universe revision used by
Discovery; only actual representation changes retain that behavior.

**Alternatives considered**: Approving during collection, accepting a source filename as an
approval reference, linking evidence after committing a mapping, or duplicating ETF validation
in a second approval implementation. These weaken governance or transaction consistency.

## Decision: Fail explicitly, retaining usable partial research

**Rationale**: Emit versioned JSON on stdout and actionable diagnostics on stderr, following the
existing CLI convention. Exit 0 for complete collection/read/review, 2 for partial/failed
collection or domain/storage errors; malformed CLI arguments retain argparse exit 2.

Report source/path/catalog/line and a bounded diagnostic category, never an unrelated source
snippet such as `SyntaxError.text`. A supported literal entry can be retained from an otherwise
partial catalog, but partial catalog evidence is not eligible for a new approval until a complete
supporting occurrence is explicitly reviewed.

**Alternatives considered**: Silent skips, success-shaped empty output, broad exception catches,
and discarding all successful sources when one root fails.

## Decision: Keep dependencies and runtime market-data boundaries unchanged

**Rationale**: Python 3.12, `ast`, `tokenize`, `hashlib`, `json`, `sqlite3`, and existing application
types cover the feature. Inject filesystem roots and observation clock into tests. No new packages,
providers, network requests, caches, or background watchers are required.

Use synthetic catalog fixtures for permanent tests, not user-owned directories. Validate the
controlled declaration counts, duplicate provenance, source failure/recovery, repeated collection,
exact hierarchy coverage, review state transitions, and atomic approval/provenance rollback.

**Alternatives considered**: A new parsing framework, schema registry, provider lookup, and live
tests. These would add cost or external dependence without serving offline discovery.
