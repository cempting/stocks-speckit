# Quickstart Validation: Manifest-Managed CSV Catalogs

**Status**: Partially implemented. The domain/file-release foundation and
`catalog-init`, `validate-catalog`, `activate-catalog`, and `recover-catalog` are available.
Both root screening tabs now consume the same validated file snapshot, with exact effective
membership, explicit ETF/basket gaps and purpose-specific benchmarks. Governance, migration
and final deployment/retirement sections remain target acceptance scenarios.
Use only explicit disposable stores for the synthetic fixtures; no real user-data cutover is implied.

**Observed validation (2026-10-31, macOS arm64, Python 3.12)**:
All 131 focused foundation/lifecycle and existing configuration/admin regressions passed,
including domain import with SQLite unavailable, concurrent publication, raw-entry conflicts,
copy isolation, restored-mtime corruption, and recovery history retention.
Ruff and strict Pyright passed; the foundation wheel contains the exact contract schema and its
init/validate commands ran outside the repository working directory.
The US2 acceptance selectors passed **42 tests**, including two controlled activations, exact
request sets, unchanged cohort/selection/cache reuse, zero-member and sub-industry projections,
corruption clearing, and all Quality/Growth/Cash Flow components with explicit missing states.
The latest full offline run reported **713 passed, 3 failed, 1 deselected**: the three deliberately
retained `test_catalog_boundaries.py` failures cover research-source defaults, runtime fixture
provider retirement and SQL outside migration, which belong to later phases.
Ruff, strict Pyright and whitespace validation passed after the screening cutover.
T001-T029 are completed; T030-T053 remain unchecked. This is not a completed feature or production
cutover. Input-limit and snapshot tests also live in
`tests/unit/test_catalog_files.py` to keep reader-unit scenarios separate from the schema/CLI contracts.
T010's wording was corrected from thirteen kinds to the twelve actually declared in data-model section 7;
no undeclared operational record kind was invented.

**Measured SC-004 handling (Darwin arm64, Python 3.12.15)**:
The generated test-only release contains exactly 10,000 stock rows, 11 sectors and 500 combined
industry/sub-industry nodes (400 industries plus 100 sub-industries).
Each cold run creates a fresh reader and reads/hashes/parses/validates/indexes the files, then
materializes all 511 navigation nodes and 10,000 distinct sector members. Three cold runs caused
exactly 21 CSV parses; ten warm filter/navigation accesses caused zero additional parses.
Every warm selection returned the exact 25 expected industry members and provider symbols.
The fixture guards network access, and no production files or database were activated.

| Run | Cold seconds (limit 5) | Warm seconds (limit 1) |
|-----|------------------------|------------------------|
| 1 | 0.306920 | 0.001151417 |
| 2 | 0.294683 | 0.000818542 |
| 3 | 0.362500 | 0.000811666 |
| 4 | - | 0.000774291 |
| 5 | - | 0.000785958 |
| 6 | - | 0.000803208 |
| 7 | - | 0.000803125 |
| 8 | - | 0.000806791 |
| 9 | - | 0.000787000 |
| 10 | - | 0.000936625 |

## Prerequisites

- Complete `/speckit-tasks` and `/speckit-implement` for active feature 010 first.
- Use the existing Python 3.12 environment and repository validation tools.
- Use supported local macOS/Linux storage, not a network share.
- Controlled fixtures under `tests/fixtures/catalogs/` contain synthetic hierarchy, listing/
  membership/approval/basket/research records with no network dependency.
- Use fresh ignored validation stores and test providers only. Never publish synthetic fixtures
  into the default production store or run live Streamlit requests against them.
- For real cutover later, back up existing database/files, substantiate scope/version/listing/
  suitability/source rights, and resolve quarantine before any explicit activation.

Contracts: [manifest schema](contracts/catalog-manifest.schema.json),
[file rules](contracts/catalog-files.md), [CLI](contracts/catalog-cli.md).
Entity and complete legacy table accounting: [data-model](data-model.md).

## 1. Validate and Activate an Isolated Controlled Release

After implementation creates the fixtures, run:

```bash
uv run python -m market_leadership.universe_admin catalog-init \
  --directory .data/catalog-validation

uv run python -m market_leadership.universe_admin validate-catalog \
  --release-manifest tests/fixtures/catalogs/reviewed-us/manifest.json

uv run python -m market_leadership.universe_admin activate-catalog \
  --manifest .data/catalog-validation/CURRENT.json \
  --release-manifest tests/fixtures/catalogs/reviewed-us/manifest.json \
  --expected-release none
```

Expected: initialization invents no approvals or active data. Validation verifies exact required
artifacts, row counts, hashes, source/approval, parent/period/listing identities and ledger links.
Activation copies a coherent reviewed test release and reports the new release ID/catalog revision.
Original fixtures remain unchanged. No SQL connection or provider request occurs.
All subsequent commands explicitly select this isolated entry; do not set a global environment override.

## 2. Membership, Hierarchy and ETF/Basket Coverage

```bash
uv run python -m market_leadership.universe_admin review-representations \
  --manifest .data/catalog-validation/CURRENT.json \
  --region US --classification TEST_CLASSIFICATION --classification-version TEST_VERSION \
  --as-of 2026-10-30

uv run python -m market_leadership.universe_admin review-listings \
  --manifest .data/catalog-validation/CURRENT.json \
  --region US --as-of 2026-10-30
```

Use fixture-defined identities; they are test evidence, not licensed GICS claims or real symbols.
Verify:

- Every active sector/industry/sub-industry is represented, including zero-stock and zero-ETF nodes.
- Sector stock sets resolve through exact industry references; sub-industry sets use only explicit
  reviewed sub-industry rows. Each instrument appears once despite multiple listing/assertion rows.
- Parent and child may share a listing only with separate exact approvals.
- Mapping absence, invalid mapping, unavailable/insufficient history and not-covered/basket states
  remain distinguishable. No sector/parent/sample ticker is substituted.
- Approved basket weights remain exact; verified non-primary/listing-only inventory remains eligible
  only through explicit basket references, without invented stock membership.
- Missing constituent history is unavailable, never reweighted; no fabricated basket chart.

Acceptance: SC-001, SC-003, SC-005, SC-007.

## 3. File-Only Changes and UI Regression

Prepare a second controlled authoring manifest with one reviewed stock reassignment and one
approved ETF listing change, using file/ledger contracts rather than editing application code.
Activate with the release ID returned in section 1:

```text
activate-catalog --manifest .data/catalog-validation/CURRENT.json \
  --release-manifest SECOND_CONTROLLED_MANIFEST --expected-release FIRST_RELEASE_ID
```

Verify changed requests/stock sets, unchanged unrelated selections, exact peer cohorts before
display filters, reused valid raw financial/price evidence, and no hidden data loading.
Both root tabs must use one release snapshot per rerun while preserving their existing date contexts.
With injected test providers, check:

- Exactly Discovery and Industry Deep-Dive; no fixture/provider/new root-tab controls.
- One progressive tape; original heading/period/basis controls, five thumbnail windows, 84-pixel
  chart geometry, gain/loss palettes and two-decimal return display.
- Six stock columns, unchanged CAP Type thresholds, complete three-component Total Score, and
  explicit score load/missing/placeholder states.
- Configured benchmark listing identity, matching-period subtraction and accepted session handling;
  no hardcoded benchmark even when price history is missing.
- Detail return retains valid context; invalid active artifacts do not leave stale selected rows.

The comparison fixture must use instruments absent from all legacy embedded rosters. Assert the
exact provider symbol set, not only that a request occurred.
Acceptance: SC-002, SC-003, SC-007 and FR-019.

## 4. Optional Local Research and Coherent Provenance

Register the controlled local-project roots/descriptors in the fixture manifest. One root is missing.
Run collection against the returned current release:

```text
collect-etf-candidates --manifest .data/catalog-validation/CURRENT.json \
  --expected-release CURRENT_RELEASE_ID
```

Expected: partial/exit 2 with durable readable observations/evidence, truthful `published` research
state, and `catalog_changed=false`. No source execution, recursive scans, private data collection,
market requests, approvals, or approved membership/mapping changes.

Recollect unchanged sources: new observation/run may be retained, but evidence/candidate identities
are reused and no manual review is duplicated. Make controlled label/ticker/context/removal/conflict/
partial-read mutations and verify all affected relationships are flagged without overwriting history.

Record accept/reject with exact scope/version/as-of/evidence and existing confirmations/issues.
Then use `approve-etf` with real fixture source/approval/suitability and optional candidate-review
identity. Acceptance alone cannot approve an ETF/listing. Inject publication failure and verify no
partial mapping/provenance; stale expected release conflicts instead of silently rebasing.
Acceptance: SC-005, SC-008.

## 5. Invalid Inputs, Tampering, Concurrency and Recovery

Controlled negative fixtures/test fault points must cover:

- Missing required file, extra/duplicate headers/JSON keys, wrong counts/hash, unknown role/version,
  wrong node type, cross-region/version references, reversed dates, invalid parent coverage/cycles.
- Duplicate physical IDs, conflicting listing attributes, symbol reuse/primary overlap, conflicting
  industry/sub-industry membership, unverified listing/suitability/source/period prerequisites.
- Existing sector-listing input with blank classification references never becomes a mapping.
- Edit an active source while keeping size and restoring mtime: ctime/content checks invalidate
  access; cached success is not served. Broken entry/hash or symlink escape is explicit failure.
- Concurrent publishers using the same expected parent: at most one commits, the other conflicts.
- Pre-commit interruptions: old pointer/approved data unchanged; no mixed generation.
- At/after-commit durability/report uncertainty: inspect validated entry/operation before retry,
  accept only complete old/new generation, and never claim unknown commit rolled back.
- Explicit recovery verifies expected raw entry identity and a known approved target checksum;
  never chooses newest leftover staging/release directory.
- Retired settings/commands/fixture entry routes fail before SQL or instrument requests.

Acceptance: SC-001, SC-005, SC-007.

## 6. Lossless Legacy Migration

Use controlled databases generated by migration tests, not the default/user database:

```text
export-database --database CONTROLLED_SCHEMA_3_DATABASE \
  --output .data/catalog-migration-validation
```

Repeat for schemas 1/2. Verify source logical/physical evidence is unchanged and no initializer
or upgrade ran. Reconciliation must account for every original table PK row as transferred,
quarantined, or archived, including all twenty schema-3 tables and actual absent legacy columns.
Compare exact raw JSON payload text, decimal strings, IDs, primary flags, intervals, region coverage
history, import fingerprints/issues, collection/review sequences and every relation/provenance link.

Include expired/empty nodes, multiple listings, placeholders, unclassified verified inventory,
valid baskets and non-primary constituents, same-industry historical assertions, unmapped provider
labels, unknown versions, conflicts/unreviewed rows, and failed/partial research.
Never restore rejected source rows that were not retained, infer ETF/GICS suitability, or manufacture
an unknown classification version. Missing reviewed prerequisites block operational activation
with retained archive/reasons, not misleading complete migration.

After resolving controlled review bindings, validate/activate the candidate. With the old database
unavailable and SQL access guarded to fail, repeat catalog browse/review/collection/approval/UI
scenarios. Historical records remain auditable from registered files.
Acceptance: SC-006 and all governed workflow invariants.

## 7. Exact Local Handling Thresholds

Planned fixture: exactly 10,000 regional stock rows, 500 industry/sub-industry nodes and 11 sectors,
plus valid approvals/listings/ledger links. The benchmark measures real required-file reads, hashing,
shape/domain validation, index construction and initial local navigation projection; a preloaded
dictionary lookup alone is not the cold criterion.

Run three cold loads with empty catalog cache and ten warm catalog-only filter/navigation changes.
Record environment, dataset counts, complete output sets and elapsed wall-clock durations.
All three cold runs must be <= 5 seconds; each warm operation <= 1 second, excluding only remote
retrieval. Warm accesses still perform integrity checks. Verify rows/scopes/states and zero unexpected
file reparses/provider calls; an empty/partial result cannot satisfy the timing criterion.

```bash
uv run pytest -q tests/integration/test_catalog_performance.py
```

Acceptance: SC-004. These are targets, not measurements already obtained during planning.

## 8. Focused and Full Validation

After adding the planned tests, use one focused runner:

```bash
uv run pytest -q tests/unit/test_catalog.py tests/unit/test_catalog_files.py \
  tests/contract/test_catalog_files.py tests/contract/test_catalog_cli.py \
  tests/integration/test_catalog_publication.py tests/integration/test_catalog_migration.py \
  tests/integration/test_catalog_workflows.py tests/integration/test_catalog_performance.py \
  tests/app -m "not live"
```

Then run the required final gates:

```bash
uv run pytest -q -m "not live"
uv run ruff check src tests
uv run pyright
git diff --check
```

AST/import guards must prove no production embedded instrument catalog/fixture route and no
SQLite access outside explicit migration. Preserve earlier domain outcomes while replacing
SQL-backed fixtures with file-backed ones where appropriate; earlier passed suites are not proof
of new acceptance. Inspect UI behavior with AppTest and targeted browser checks when real reviewed
deployment data is available, without exposing credentials or synthetic runtime evidence.

Provision the real reviewed store separately from code deployment, record migration/version
guidance, and preserve backups/known release checksums. No real export/activation is automatic.
