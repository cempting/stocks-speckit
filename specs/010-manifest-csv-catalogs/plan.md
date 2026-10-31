# Implementation Plan: Manifest-Managed CSV Catalogs

**Branch**: `main` (unchanged; feature key `010-manifest-csv-catalogs`)
**Date**: 2026-10-31
**Spec**: [spec.md](spec.md)

**Input**: Active feature 010 and the [cross-feature authority map](../README.md).
The tagged feature 001 is retained calculation/domain context, not a different active feature.
Planning stops after design; no tasks, runtime refactor, database upgrade/export, or real catalog
activation is performed here.

## Summary

Replace catalog SQLite and embedded instrument lists with one manifest-managed immutable file
release. Use JSON for the consolidated manifest/entry, CSV for hierarchy, one stock file per
region, ETF listings and level-specific mappings, and benchmarks. Keep typed governance/research/
basket/listing-inventory history in a registered JSONL ledger and lossless migration rows in
a registered archive. The separate listing-only inventory preserves unclassified verified
securities without inventing industry membership or invalidating previously valid basket rules.

Reuse existing domain calculations and safe local extraction. Extract validation/record types
from SQL, wire every active/legacy production consumer to an explicit catalog snapshot or
retirement error, and confine SQL to an explicit read-only exporter. No ORM, derived database,
provider switch, new root tab, or runtime synthetic catalog.

Publish under a local OS writer lock with an expected-release check, validated captured inputs,
durable immutable generations, and one atomic entry switch. Cache immutable typed indexes by
content and check registered active-file identity before reuse. Research-only publication preserves
the catalog revision; both tabs in a rerun use one snapshot.

## Technical Context

**Language/Version**: Existing Python `>=3.12,<3.13`; package target `0.2.0` for the documented
pre-1.0 breaking catalog/admin changes. Catalog and CLI format versions are separately explicit.

**Primary Dependencies**: Existing Streamlit, pandas, yfinance, jsonschema and their constrained
versions. Standard-library `csv`, `json`, `hashlib`, `pathlib`, `dataclasses`, `decimal`,
`tempfile`, `os`, `uuid`, and macOS/Linux `fcntl`. No dependency additions.

**Storage**: Ignored `.data/catalog/` immutable release directories and `CURRENT.json`;
`MARKET_CATALOG_MANIFEST_PATH`/CLI `--manifest` select the entry. No catalog/review SQL,
DuckDB or Parquet. Existing market-response caches and historical snapshot formats remain outside
the redesign. Research/audit records are immutable logical history carried into new releases.

**Testing**: Existing pytest, Streamlit AppTest, Ruff, strict Pyright, and jsonschema validation.
Inject paths, clocks, publisher failure points and providers; use controlled file releases and
legacy databases only. Permanent tests never read user projects or request live data.

**Target Platform**: Current local macOS and Linux Streamlit/CLI deployments, including provisioned
local filesystem storage. Hosting must provision reviewed files separately; ephemeral hosting does
not guarantee retention of reviewer writes. No network-filesystem/distributed-writer guarantee.

**Project Type**: Existing Python/Streamlit application with an administration CLI.

**Performance Goals**: SC-004's 10,000 stock rows and 500 industry/sub-industry nodes: initial
catalog load plus local navigation projection within five seconds, warm catalog-only filter/
navigation within one second, excluding remote retrieval. Record environment and actual measurements.

**Constraints**: One regional stock CSV; exact industry/sector/sub-industry references and periods;
source/listing/suitability approval; no code ticker catalogs or parent/synthetic fallback; coherent
catalog+provenance publication; all twenty legacy tables accounted for; no source mutation or automatic
activation during export.

**Scale/Scope**: Reviewed US GICS initially. Preserve explicit regional identities, existing
reviewed records and historical scopes without inventing international taxonomies or licensed GICS
versions. Local research's four initial roots are registered optional data, not code defaults.

## Constitution Check

Gates evaluated before research and re-evaluated against the completed design:

| Gate | Pre-research | Post-design evidence |
|---|---|---|
| I. Keep It Simple | PASS | Existing JSON/CSV dependencies, one file store/snapshot, no query database/ORM/service |
| II. Lean Delivery | PASS | Only catalog consumers, admin/research, export, and directly related tests/docs |
| III. YAGNI | PASS | No distributed locking, new provider, taxonomy plugin, trading, or extra UI |
| IV. Avoid Waste | PASS | Region-wide CSV, immutable indexes, targeted fingerprints, deduplicated visible symbol requests |
| V. Separation of Concerns | PASS | File/clock/publication I/O in infrastructure; validation/calculations in domain; workflows/UI separate |
| VI. High Cohesion / Low Coupling | PASS | Narrow typed snapshot/publisher contracts; SQL isolated in exporter; no SQL-shaped facade |
| Single source and cache policy | PASS | yfinance unchanged, active request scope retained, no cached failure or invalid catalog fallback |
| Private stable selections | PASS | Existing namespaces; one rerun snapshot; clear only invalid descendants/affected cohorts |
| Error/privacy obligations | PASS | Source/row/reference diagnostics and explicit publication uncertainty; no source snippets/secrets |
| Breaking migration/versioning | PASS | `0.2.0`, versioned formats/reports, explicit retirement, complete row/link reconciliation and recovery |
| Test-first workflow | PASS | Failing contracts/integration/AppTests precede consumer cutover; benchmark and full offline gates |

No constitution exceptions or unresolved clarifications remain. Publication atomicity has a
documented commit point: known pre-commit failure preserves the prior entry; interrupted commit/
durability acknowledgement is reconciled explicitly, never mislabeled as successful rollback.

## Project Structure

### Documentation (this feature)

```text
specs/010-manifest-csv-catalogs/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── catalog-manifest.schema.json
│   ├── catalog-files.md
│   └── catalog-cli.md
└── checklists/requirements.md
```

`tasks.md` is generated later by `/speckit-tasks`; it is not created by this command.

### Source Code (repository root; planned)

```text
src/market_leadership/
├── domain/
│   ├── catalog.py                         # Extracted typed records/scope/date/source validation
│   ├── industry_representations.py        # Retain exact basket/ETF calculations
│   ├── industry_momentum.py               # Explicit representations, no catalog constant
│   ├── regimes.py                         # Required configured benchmark identity
│   └── local_etf_evidence.py              # Retain identities/review/currentness semantics
├── infrastructure/
│   ├── catalog_files.py                   # Manifest/CSV/ledger reader, indexes, coherent publisher
│   ├── catalog_migration.py               # Only production SQLite importer: read-only export
│   ├── local_etf_sources.py               # Manifest-supplied roots/descriptors; safe static reader
│   ├── stock_membership.py                # File snapshot handoff; retire runtime fixture/JSON paths
│   └── market_data_cache.py               # Existing market-response behavior unchanged
├── application/
│   ├── discover_sectors.py                # File-derived sector/benchmark request scope
│   ├── industry_representations.py        # Snapshot-backed worklist/resolution
│   ├── discover_etf_candidates.py         # Ledger-backed research/review/approval
│   └── build_snapshot.py                  # Retire production synthetic catalog route
├── ui/workflows/
│   ├── discovery_page.py                  # Same approved snapshot, layout and calculations
│   ├── industry_deep_dive.py              # Same catalog authority and valid selection state
│   └── industry_discovery.py              # Refactor catalog injection or explicit retirement
├── config.py                             # One catalog entry; actionable legacy-setting errors
└── universe_admin.py                      # Versioned file admin + explicit migration command
tests/
├── unit/test_catalog.py
├── unit/test_catalog_files.py
├── integration/test_catalog_publication.py
├── integration/test_catalog_migration.py
├── integration/test_catalog_workflows.py
├── integration/test_catalog_performance.py
├── contract/test_catalog_files.py
├── contract/test_catalog_cli.py
├── app/                                  # Existing Discovery/Deep-Dive regression tests
└── fixtures/catalogs/                    # Synthetic reviewed, invalid, and benchmark releases
```

**Structure Decision**: Extract the reused SQL-independent rules into one cohesive domain module
and use one file reader/index/publisher boundary, plus a separate legacy exporter. Do not introduce
`FileRegionDatabase`, fake connections, generic CRUD, or independent stores for each workflow.
Existing `region_database.py`/`universe_import.py` cease production authority; remove them after
validation is extracted and legacy test fixtures are isolated. Historical artifact readers keep
their file formats where unrelated to catalog authority. Synthetic provider/listing definitions
move from production to test helpers, and runtime routes that cannot meet the manifest contract
are retired explicitly, not left as hidden fallback.

## Phase 0 - Research Outcome

[research.md](research.md) resolves serialization, row granularity, governance/listing-only
inventory, indexed reuse/integrity, local locking/publication, twenty-table migration, and complete
consumer retirement. The bounded local schema inventory was delegated read-only; no real database
was opened. Current caller and cache patterns were inspected directly.

## Phase 1 - Data and Interface Design

1. Use [data-model.md](data-model.md) for typed entities, IDs, inclusive periods, governance
   ownership, ledger/history projection, and legacy disposition accounting.
2. Use [manifest schema](contracts/catalog-manifest.schema.json) for strict entry/release shapes.
   Cross-file/domain checks supplement schema validation; schema success alone is not approval.
3. Use [file contract](contracts/catalog-files.md) for roles, exact CSV headers, paths/checksums,
   inventory/ledger behavior, snapshot integrity and publication transitions.
4. Use [CLI contract](contracts/catalog-cli.md) for staging/activation, governed review, old-command
   retirement, report/error semantics, read-only export and explicit recovery.
5. Use [quickstart.md](quickstart.md) for post-implementation runnable fixtures, measured local
   thresholds, conflict/interruption tests, migration reconciliation and full offline checks.

## Implementation Sequence for Task Generation

1. Add failing format/domain/publication/migration and no-SQL/no-static-list tests first.
2. Extract existing typed records/validators without changing their intended business behavior.
3. Build strict captured-byte loader, immutable indexes and registered ledger projections.
4. Add writer lock, expected-release publication, coherent audit/candidate updates and recovery.
5. Implement twenty-table read-only export/reconciliation; quarantine missing scope/approval
   rather than guess. Verify source bytes/logical data remain unchanged.
6. Refactor both tabs, membership/peer flows, worklists, ETF/basket/candidate approval, configured
   benchmarks and sector/industry data requests against the same catalog boundary.
7. Remove/isolate all production static/fixture/legacy catalog paths and SQL imports except exporter.
   Update CLI/settings/package/docs and migration fixtures, preserving earlier completed tasks.
8. Run focused contracts/integration/AppTests, exact SC-004 benchmark, full offline tests, Ruff,
   strict Pyright and whitespace. Validate every row/state/request scope, not only file existence.

No production dataset is shipped as approved seed. Existing sector listings remain user-owned
input; activation/export of real data is an explicit later administrator action.

## Requirement and Outcome Coverage

| Requirements | Design / validation |
|---|---|
| FR-001, FR-009, FR-018 | File boundary and exporter isolation; CLI retirement; no-SQL/static catalog tests; SC-006/SC-007 |
| FR-002, FR-003 | Manifest roles/schema, ETF listing versus level mapping CSVs, benchmark purposes; SC-001/SC-002 |
| FR-004, FR-005, FR-006 | Regional assertion/listing rows, exact hierarchy, unresolved/inventory rules, temporal checks; SC-001/SC-003 |
| FR-007, FR-008 | Captured-byte identity checks, writer/CAS, complete generations and recovery; SC-001/SC-005 |
| FR-010, FR-011, FR-019 | Shared snapshot/indexes, scoped fingerprints, UI/provider/calculation regression; SC-002/SC-003/SC-004 |
| FR-012, FR-013, FR-015 | Registered optional research, immutable ordered ledger, unchanged/review mutation scenarios; SC-008 |
| FR-014, FR-016 | Existing exact listing/source/period/weight validation and coherent mapping/provenance; SC-005 |
| FR-017 | Twenty-table snapshot/archive/disposition reconciliation, no guessed versions/approvals; SC-006 |

All eight success criteria have explicit controlled scenarios in the quickstart.

## Complexity Tracking

No constitution violations. Immutable generations, a writer lock, retained ledger and read-only
exporter are required by coherent publication, concurrency, governed history and migration;
they are not speculative infrastructure.
