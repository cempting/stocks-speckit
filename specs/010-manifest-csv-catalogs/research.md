# Research: Manifest-Managed CSV Catalogs

**Date**: 2026-10-31
**Status**: Local research complete; implementation not started.

## Decision: One JSON manifest per immutable release

**Rationale**: Use the existing JSON/JSON Schema dependencies and standard-library CSV reader.
A release manifest registers physical artifacts, reviewed evidence-source metadata, regional
classification/coverage, and optional research descriptors. A small `CURRENT.json` entry contains
only the chosen release manifest path and checksum; it is not a second source register.
`MARKET_CATALOG_MANIFEST_PATH` selects this entry, defaulting to `.data/catalog/CURRENT.json`.
There is no catalog SQLite, DuckDB, Parquet, index service, or alternate JSON membership authority.

**Alternatives considered**: YAML adds a runtime dependency and additional coercion semantics.
Directly editing the active manifest cannot publish several files coherently. A derived database
contradicts the user's files-only decision. Existing market-response Parquet/JSON caches are
unrelated and remain unchanged.

**Evidence**: [dependencies](../../pyproject.toml#L1),
[configuration](../../src/market_leadership/config.py#L8), and [D-F010](../decisions.md).

## Decision: One regional stock CSV, explicit identities and periods

**Rationale**: A row represents a reviewed membership assertion combined with a particular listing
period, or an explicit unresolved stock without a listing. It carries an exact industry and optional
sub-industry reference. Sector identity comes from hierarchy, never repeated stock-sector authority.
Repeated listing metadata across historical memberships must agree; filtering deduplicates instrument
IDs, not symbols. Industry-only rows do not create sub-industry membership.

Keep listing and membership dates/sources separate. A listing may predate membership, have a different
reviewed source, or change primary status. Compatible same-industry historical assertions can overlap
without duplicating displayed stocks; conflicting industries or simultaneous distinct sub-industries
cannot. Every physical row and logical assertion/listing identity is validated.

**Alternatives considered**: One CSV per node duplicates sources and complicates updates. Separate
stock membership/listing CSVs undo the selected regional stock organization. Ticker-only rows lose
multiple listings, effective dates, stable identity, and approval ownership. Replaying the old importer
loses temporal/primary-listing information and invents normalization/defaults.

**Evidence**: [legacy listing/membership keys](../../src/market_leadership/infrastructure/region_database.py#L97),
[old importer limitations](../../src/market_leadership/infrastructure/universe_import.py#L118).

## Decision: Separate ETF listing and level-specific mapping CSVs

**Rationale**: Register hierarchy, regional stocks, ETF listings, sector ETF mappings, industry ETF
mappings, sub-industry ETF mappings, and benchmark mappings as explicit artifact roles.
Mapping rows reference verified listing IDs, exact classification/version/node IDs, sources,
approval references, and periods. A file can be empty with an honest partial coverage declaration;
empty files do not establish complete coverage. The supplied sector CSV has no reviewed node links
and is retained as a legacy listing input only, not auto-converted into mappings.

Benchmark purposes are product semantics, not instruments: `sp500_comparison` and `market_sentiment`.
Their reviewed listing IDs come from files. Preserve existing labels, matching-period subtraction,
session alignment and calculation rules; do not replace missing benchmark data with another symbol.

**Alternatives considered**: Putting ETFs in stock membership creates false constituents. A merged
listing/mapping row obscures listing verification versus node suitability. Keeping the historical
eleven-sector or thematic symbol roster in code violates FR-009.

**Evidence**: [remaining sector/benchmark constants](../../src/market_leadership/application/discover_sectors.py#L22),
[thematic industry roster](../../src/market_leadership/domain/industry_momentum.py#L22),
[benchmark default](../../src/market_leadership/domain/regimes.py#L18).

## Decision: One immutable JSONL governance/research ledger per release

**Rationale**: Retain typed observations, evidence, decisions, links, basket records, and reviewed
listing-only inventory in an append-only logical history. Publication copies the previous ledger
prefix and appends new records; already published releases are never edited. Original candidate/
evidence/review/run/representation IDs and the separate collection/review event-order streams are
preserved. An unchanged collection may record a new observation/run, but reuses evidence IDs and
creates no duplicate evidence or manual reviews.

Listing-only inventory is needed: existing verified but unclassified securities and ETF listings
are not automatically industry members, while approved baskets need not require constituent
membership in their target industry. Explicit stock inventory records in the registered ledger
can support listing worklists and approved basket references, never stock-tape membership fallback.
Classified stock listings remain in the one regional stock CSV. Identical listing IDs appearing
in both places must have identical attributes and provenance.

Retain raw migration rows separately in a registered, immutable JSONL archive, not a runtime
lookup fallback. This keeps unknown legacy metadata and original payload text recoverable without
requiring SQL after cutover.

**Alternatives considered**: One mutable log plus independently edited CSVs permits partial
approval. One file per event creates unnecessary files. Reconstructing research solely from scalar
SQL columns loses JSON evidence and relationships. Automatically classifying unassigned basket
constituents fabricates memberships; discarding them silently breaks valid basket behavior.

**Evidence**: [research relations](../../src/market_leadership/infrastructure/region_database.py#L285),
[listing validation](../../src/market_leadership/infrastructure/region_database.py#L1545),
[basket validation](../../src/market_leadership/domain/industry_representations.py#L26).

## Decision: Reuse immutable indexes and check active artifact identity on access

**Rationale**: Parse/hash captured file bytes once, build typed immutable hierarchy/membership/
listing/representation/review indexes, and reuse them through `st.cache_data`.
Every catalog access checks the entry and registered artifact filesystem signatures
`(device, inode, size, mtime_ns, ctime_ns)`; a changed signature triggers checksum validation
before any cached snapshot can be reused. Reads check signatures before/after capture and reject
concurrent modifications. Do not follow catalog-artifact symlinks outside the release or use
unchanged size/mtime alone as proof of content identity.

Use one snapshot for both root tabs within a rerun and pass it down, rather than independently
resolving the entry in each helper. The catalog revision hashes catalog artifacts, scope/coverage,
and referenced catalog-approval metadata, not unrelated research/archival history. Research-only
publication changes the release ID but not the catalog revision. Peer/membership-derived keys use
exact scope, effective date, cohort/listing identities, and relevant fingerprints; unchanged remote
price/fact caches and valid selections remain reusable.

**Alternatives considered**: Reloading/parsing all files on every widget rerun wastes work.
Timestamp-only keys miss same-size edits with restored mtime. TTL-only catalog caching masks
altered sources. A global revision tied to every research record invalidates unrelated prices/
peers. A new indexing framework is not justified for the controlled 10,000-row target.

**Evidence**: [current revision-based membership](../../src/market_leadership/infrastructure/stock_membership.py#L32),
[Discovery consumers](../../src/market_leadership/ui/workflows/discovery_page.py#L134),
[Deep-Dive consumer](../../src/market_leadership/ui/workflows/industry_deep_dive.py#L58).

## Decision: Serialized writer, optimistic release check, final atomic pointer switch

**Rationale**: Support the existing macOS/Linux local-filesystem deployment with standard-library
`fcntl.flock`, an exclusive nonblocking lock on one persistent store lock file. Never unlink that
file to release/recover a lock; process exit releases the OS lock. All publishers use the same
lock and require the expected active release (`none` for first activation). Conflicting writers
return an explicit conflict, not silent last-writer-wins or implicit rebasing.

Copy captured validated inputs into a uniquely named staging directory inside the store.
Do not use hardlinks to editable authoring files. Flush/sync payloads and manifest, finish the
release directory, then atomically replace the small entry. Retain prior releases. Before the
commit point, errors leave the old entry unchanged; do not add failure-prone cleanup that turns
a completed commit into a claimed rollback.

The pointer switch is the linearization point. A crash or durability/reporting failure at/after
that point requires an explicitly reported indeterminate/committed outcome and operator
reconciliation, not an assertion that the old pointer survived. Readers accept only a complete,
checksum-valid selected release. Power-loss recovery may observe old or new complete release;
it must never auto-select an unreferenced staging directory. Network filesystems, remote writers,
and Windows locking are outside this release's deployment scope.

**Alternatives considered**: Individually replacing CSVs loses multi-file atomicity.
A lockfile based on existence leaves stale-owner recovery problems. Distributed locks or a
database violate scope/simplicity. Atomic rename alone without expected-release checks loses updates.

**Evidence**: [existing immutable generation publication](../../src/market_leadership/infrastructure/market_data_cache.py#L210)
and [atomic/fsync file replacement](../../src/market_leadership/infrastructure/market_data_cache.py#L408).
Reuse the proven publication pattern, but add catalog-specific writer/CAS and directory durability checks.

## Decision: Isolate SQLite in an explicit read-only migration tool

**Rationale**: The inventory contains twenty schema-3 tables, not just memberships and mappings.
Export an internally consistent read-only snapshot of versions 1/2/3, retain schema/column presence,
and reconcile every original primary-key row plus its links. Do not run initialization or upgrade
the source. A logical snapshot digest covers schema and canonical typed row values, including WAL-
visible committed data; hashing the main database file alone is insufficient.

Preserve raw JSON payload strings, decimal weight strings, arbitrary metadata, coverage history,
primary flags, inclusive periods, import context fingerprints, review ordering, and approval-run
versus review-run identity. The archive stores original values even when operational rows require
explicit quarantine. Unknown classification versions and non-GICS labels cannot be guessed or
renamed into reviewed GICS; missing required review must be resolved explicitly before activation.
Inherited approval is identified as inherited, not falsely presented as a new independent review.

Source issues contain references/details, not the full rejected source rows. Export must not
promise recovery of data that was never retained. Missing version-1/2 tables/columns are absence,
not invented zero-history approvals. Unsupported schema versions fail explicitly.

**Alternatives considered**: Upgrade first mutates user data. `validate/import` replay loses
primary flags, history, empty nodes, sub-industry parentage, and all six research relations.
Retaining SQL reads behind a compatibility repository leaves dual authority. Dropping expired
or unclassified evidence prevents complete reconciliation.

**Evidence**: [schema inventory](../../src/market_leadership/infrastructure/region_database.py#L38),
[schema evolution](../../src/market_leadership/infrastructure/region_database.py#L426),
[coverage history](../../src/market_leadership/infrastructure/universe_import.py#L617),
[import identity](../../src/market_leadership/infrastructure/universe_import.py#L761).

## Decision: Extract narrow shared domain validation, replace every production consumer

**Rationale**: Move reusable record types and source/scope/listing/date/overlap checks out of
the SQL module. A file catalog supplies read snapshots and coherent publication through existing
application workflows; do not emulate SQL connections or add a generic CRUD/ORM layer.
Refactor both tabs, representation worklists, administration/research, sector/industry momentum,
benchmark defaults, legacy industry workflow and snapshot-builder fixture route. Move synthetic
instrument catalogs/provider implementations into test-only helpers; production fixture entry
points become explicit retirement errors. Existing artifact readers may retain their file-based
historical schemas, but cannot seed approved live catalogs.

Keep bounded AST extraction/domain currentness; source roots/descriptors move from code defaults
to manifest data. Parser syntax/role names are grammar, not hardcoded instruments.
Retire old database flags/commands and independent catalog settings with actionable messages.
Only the explicit exporter may import/open SQLite. Plan package version `0.2.0` and independent
catalog/CLI format versions; do not change dependencies, provider, or market-data cache schema.

**Alternatives considered**: A `FileRegionDatabase` preserving SQL-shaped APIs hides the breaking
change. Fixing only Discovery leaves Deep-Dive/CLI/legacy paths inconsistent.
Deleting unrelated provider/cache code exceeds the catalog task.

**Evidence**: [review workflow](../../src/market_leadership/application/industry_representations.py#L24),
[research persistence boundary](../../src/market_leadership/application/discover_etf_candidates.py#L33),
[CLI database coupling](../../src/market_leadership/universe_admin.py#L12),
[runtime fixture route](../../src/market_leadership/application/build_snapshot.py#L384).

## Research resolution

No unresolved design questions or new runtime dependencies remain. The file contracts and
controlled validation targets are defined in Phase 1; timing targets are acceptance budgets,
not performance claims from this documentation-only planning run.
