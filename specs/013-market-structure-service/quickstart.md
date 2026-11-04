# Validation Guide: Market Structure Service and Persistent Observation Cache

Status: **implementation in progress; acceptance guide**. Workspace setup and the
test-owned fixture builder are implemented and verified. Service publication/HTTP and
app cache commands below remain planned interfaces, not runnable acceptance claims.
Refined 2026-11-04 after analysis. The [96-task implementation backlog](tasks.md) now
incorporates those decisions. Cross-artifact analysis completed without actionable
findings before implementation. Task checkboxes track verified progress; commands
below remain planned until their corresponding implementation gates pass.

## Recorded implementation evidence

### T001: pre-move baseline (2026-11-04)

- `uv run --no-sync ruff check src tests`: passed.
- `uv run --no-sync pyright`: zero errors/warnings.
- `uv run --no-sync pytest -m "not live" -q`: 864 passed, one live test deselected,
  12 existing exchange-calendar/NumPy deprecation warnings, 53.03 seconds.
- `uv build`: source distribution and combined wheel built successfully.
- Existing `market-catalog`, `market-company-evidence`, and `market-universe-legacy`
  `--help` commands: exit 0.
- Before the move, all three namespaces and maintenance entry points belong to the
  root distribution. Existing uncommitted runtime/tool changes are preserved.
- Python/universal ignore patterns are already present; no Docker, Node, Terraform,
  or Helm configuration was detected. No ignore-file changes were necessary.

### T002-T008: independent workspace setup (2026-11-04)

- Added failing isolated-install tests first: three expected delegate failures and
  four expected missing-distribution setup errors established the pre-change baseline.
- Shared/app/service and optional-maintenance clean-wheel installs now pass; all
  existing maintenance help commands work, app-only delegates explain the missing extra,
  internal import failures remain visible, and legacy aliases preserve module identity.
- Existing daily/weekly schemas are packaged byte-for-byte; installed bootstrap no
  longer reads an unavailable repository specification directory.
- User-approved correction: Streamlit 1.66.1 already requires Starlette/Uvicorn.
  Their transitive UI presence is allowed; the app still excludes service/tools.
- Focused boundary/distribution/schema suite: 80 passed.
- All-source Ruff and strict Pyright: passed, zero type errors/warnings.
- Full non-live suite after source-root/editable-install corrections:
  874 passed, one live test deselected, 12 existing warnings, 188.49 seconds.
- `uv build --all-packages`: all three source distributions and wheels built.
- New service publication/HTTP commands and observation-cache behavior remain
  unimplemented. This setup checkpoint does not complete US1 or authorize cutover.

### T009-T012: controlled foundation (2026-11-04)

- Demonstrated missing fixture/support modules and missing public evidence codecs
  before implementation.
- The documented fixture builder now creates deterministic, independently validated
  v1/v2 catalogs and four explicit registries per revision under a fresh output root.
  Bindings carry the actual computed catalog revision; policies follow the normative
  schema and fingerprint recipe. No prices, network acquisition or production fixture
  provider is involved. Full service-level cross-registry validation remains US1 work.
- Controlled HTTP transport, partial/empty/failed provider responses, UTC frozen
  clocks and a locked/fsynced cross-process call ledger are available to later tests.
- Public typed association/assessment codecs reuse existing representations and
  preserve nullable identities, fingerprints, legacy dates and reference-only denial.
- Full non-live suite: 890 passed, one live test deselected, 12 existing warnings,
  126.56 seconds. All-source Ruff and strict Pyright passed.
- Foundation is complete; independent service implementation and app/cache cutover
  remain pending. No production data was changed.

## Prerequisites and isolation

- Python 3.12 and uv; run from the repository root.
- Complete the relevant feature implementation tasks before executing the planned
  service/cache scenarios; generating the backlog alone does not make commands runnable.
- Use only temporary directories and test-owned synthetic reviewed metadata.
- Recording providers are injected by tests/AppTest, never exposed as a production
  provider option. Do not start the production app with synthetic metadata and let
  it contact yfinance.
- No production catalog/source permission/binding/cache is copied, activated, changed
  or cleaned by this guide.

The [contracts](contracts/snapshot-format.md) and [data model](data-model.md) define
payload, source-rights, identity, registry and policy rules. Do not duplicate those
rules in ad hoc fixtures.
Validate policy wire fixtures against the [registry schema](contracts/observation-policies.schema.json)
with format checking plus the shared semantic validator; schema acceptance alone does
not prove current permission, references, review ordering or a correct fingerprint.

## 1. Workspace and dependency isolation

After manifests are implemented:

```bash
uv sync --all-packages
uv run ruff check src packages services tests
uv run pyright
uv run pytest tests/contract/test_package_boundaries.py \
  tests/contract/test_market_structure_http.py \
  tests/contract/test_market_structure_snapshot.py -q
```

Expected:

- Shared package loads with app/service/provider imports blocked.
- Service and offline tools load with app/UI/yfinance/Massive imports blocked.
- Stock-app runtime loads with service/tools imports blocked; old maintenance CLI
  delegates only work when the optional maintenance distribution is installed.
  Streamlit's existing transitive Starlette/Uvicorn dependencies are allowed; importing
  the independently deployed `market_structure` application is not.
- Catalog v1/v2 resources remain packaged; class/module compatibility aliases retain
  identity after moving package roots.
- Tests also build isolated wheels/virtual environments to prove that import isolation
  is not merely the result of all workspace dependencies being installed together.

## 2. Serve one synthetic reviewed snapshot

The test-owned fixture builder creates catalog authoring files and all four registry
documents under the selected temporary root. This is not a seeding command in a
production distribution.

```bash
RUN_DIR="$(mktemp -d)"
export RUN_DIR
uv run python -m tests.fixtures.market_structure.build_demo --output "$RUN_DIR/input"
uv run --package market-structure market-structure publish \
  --store "$RUN_DIR/service" \
  --catalog-release "$RUN_DIR/input/catalog/manifest.json" \
  --registry-dir "$RUN_DIR/input/registries" \
  --expected-snapshot none --review-reference synthetic-local-validation
uv run --package market-structure market-structure serve \
  --store "$RUN_DIR/service" --host 127.0.0.1 --port 8765
```

Run the server in a separate terminal. In another terminal, with the same `RUN_DIR`
value, check:

```bash
curl --fail http://127.0.0.1:8765/healthz
curl --fail http://127.0.0.1:8765/readyz
curl --fail -D "$RUN_DIR/headers.txt" \
  http://127.0.0.1:8765/v1/current -o "$RUN_DIR/current.json"
```

Expected: liveness `live`, readiness `ready`, one current snapshot hash, ETag and
`Cache-Control: no-cache`. A second GET using the returned ETag as `If-None-Match`
returns 304 with no body. Fetching the fixed manifest route and its digest objects
matches every declared hash/length; traversal or unpublished objects cannot be read.
POST/PUT/DELETE do not publish anything.

Stop only this server with Ctrl-C when finished. Keep the temporary path for inspection,
or remove only its named files after confirming the resolved path and stopping users
of those files; never use a broad cleanup of workspace/session roots.

## 3. Consumer bootstrap, coherent replica and news metadata (US1/US2)

```bash
uv run pytest tests/integration/test_market_structure_delivery.py \
  tests/integration/test_observation_bootstrap.py \
  tests/app/test_market_structure_context.py -q
```

The controlled harness supplies the service URL/transport and recording provider
through normal composition seams. It starts with empty explicit replica/observation
roots, not the production defaults.

Expected:

- First structure load downloads/validates exactly one complete snapshot before use.
- Required active-view price/representation/benchmark data alone is requested.
  Financials/research and unrelated stocks remain unloaded.
- Cache directories are created without an import command or fixture production mode.
- News sources show correct metadata/review state; zero article fetches occur.
- Genuine indexes remain separate identities; missing official volume is unavailable.
- A partial provider failure retains valid price coverage while exposing individual gaps.
- A 304 with no matching validated local snapshot triggers one unconditional retry,
  not acceptance of missing local bytes.

## 4. Durable reuse, gaps, reclassification and continuity (US3/US4)

```bash
uv run pytest tests/integration/test_observation_reuse.py \
  tests/integration/test_observation_revisions.py \
  tests/integration/test_observation_concurrency.py \
  tests/integration/test_observation_retention.py -q
```

Assert actual values, identities, partition/generation references and source calls:

| Scenario | Required outcome |
|---|---|
| A -> overlapping B -> A, then process restart | Existing valid series/ranges cause zero additional observation calls, even with different symbol batches |
| 252 held sessions -> five newly completed sessions | Fetch five sessions plus at most one eligible reconciliation overlap, not the whole range |
| Expired mutable tail revalidated with identical values, then immediate rerun | One revalidation, then zero further calls; last-validation time advances but original retention deadlines do not |
| Membership move/addition/removal | Correct current hierarchy; unchanged eligible history reused, no observation duplication |
| Reused ticker or changed issuer continuity | No predecessor history; unverifiable periods explained |
| Source correction/adjusted overlap mismatch | Old epoch invalidated; requested stale window reconciled before use, no mixed scales |
| Two simultaneous identical misses | One upstream acquisition; coherent result for both, or one shared explicit failure |
| Process interruption during commit | Old generation readable, new incomplete generation never current |
| Partial stock/ETF volume or close-only index | Correct independent evidence states; no invented volume |
| Confirmed unavailable mutable-tail gap -> rerun -> restart -> freshness boundary | No extra calls before the boundary; one shared eligible recheck afterwards, still explicit unavailable coverage if confirmed again |
| Confirmed unavailable historical gap or gap leaving the mutable tail | Zero automatic calls regardless of age; explicit selected refresh can recheck |
| Due unavailable-gap recheck fails -> rerun -> restart | Preserve terminal error; zero further automatic calls until explicit retry |
| Unconfirmed partial/empty/error result -> rerun/restart | Preserve distinct missing/error diagnostic; no automatic retry or false successful coverage |
| Reader paused after CURRENT selection while another process prunes | Reader holds shared lock through rows; prune waits/returns contention without unlinking needed files; permitted values remain readable |
| Shared read released before exclusive miss/refresh acquisition | No in-place upgrade/deadlock; total series-lock wait <=2 seconds, then explicit loading |
| Prune removes the last price row while another process has the series lock open | Stable `.lock` inode remains; later readers/writers coordinate on the same lock, with no expired price bytes retained |

Use real process concurrency and durable restarts for those assertions, not only
two calls against one in-memory mock.

## 5. Outage, rejected revisions and permission expiry (US5)

```bash
uv run pytest tests/integration/test_market_structure_outage.py \
  tests/app/test_market_structure_offline.py -q
```

Cover empty replica, valid replica, failed GET, timeout, malformed response, truncated/
oversized object, invalid catalog reference, unsupported format, corrupt disk object,
401/403, service recovery, and a source permission expiring at an injected clock boundary.

Expected:

- No replica + no service -> actionable blocked setup state, no guessed roster.
- Replica + transient failure/rejected update -> explicitly marked read-only browsing;
  last successful check is not advanced by a failed request.
- Authentication denial blocks dependent views instead of bypassing service access.
- Offline mode makes zero provider calls, including from cached financial/research,
  direct snapshot CLI and history-loading paths; refresh cannot bypass the gate.
- Known expiry/revocation applies before in-memory hits can display restricted data.
- Recovery validates complete current bytes before leaving read-only mode.
- Old structure after rollback cannot restore known revoked/shortened rights. Guard
  state survives process restart, and corrupt/missing required state blocks rather
  than resetting approval. Cached financial/research routes obey the same constraint.

### Exact policy grammar and rollback cases

Use the snapshot contract selector above and extend the controlled tests to assert:

- All four policy statuses, exact allowed-use tokens, UTC review timestamp/date-only
  expiry boundaries, conditional nullability, unique scope values, and no inferred grant.
- Missing/unknown fields, non-UTC/future reviews, leap seconds, invalid dates, booleans
  for integer limits, zero/negative limits, freshness >3600, and fingerprint mismatch fail.
- Reordering JSON object keys or equivalent review precision preserves the fingerprint;
  changing array order changes it; non-ASCII references follow the declared escaping.
- `approved -> revoked -> old-snapshot rollback -> restart` remains unauthorized;
  publisher rejects obsolete grant expansion without replacing CURRENT.
- A renamed policy ID, backdated restriction, or fresh publication-only review reference
  cannot bypass stored review cutoffs. A genuinely later source review can authorize
  new acquisition, without reviving rows expired under previous retention restrictions.
- Same-day ambiguous legacy assessment reapproval remains blocked with explicit guidance;
  existing assessment date fields/fingerprints do not silently change.
- A fully validated restriction persisted before a pointer fault still constrains the
  old structure; an invalid candidate/dry-run never mutates guards.

## 6. Exact performance gate

```bash
uv run pytest tests/integration/test_market_structure_performance.py -q -s
```

Controlled workload and assertions:

- 10,000 distinct instruments with >=252 daily observations each: >=2,520,000 actual
  retained observations, including overlapping industries and multiple listings.
- Record OS, architecture, Python/package versions, storage, clock, CPU/memory conditions,
  dataset shape, and whether in-memory/OS caches are warm.
- Record cold first-view elapsed time, excluding only explicitly measured external wait;
  target <=5 s and zero off-view acquisitions.
- Run 20 warm navigation actions selecting up to 100 stocks each; at least 19 must
  complete within 1 s with correct nonempty rendered/returned data and zero external calls.
- Validate a 500-observation update: five new sessions for 100 already known listings;
  commit-to-readable time <=2 s.
  Untouched series/partitions must not be rewritten.
- Instrument partition reads, directory enumeration, CSV reparses, upstream calls and
  row counts. No whole-universe scan, empty-result shortcut, or precomputed-view proxy
  can satisfy these gates.

Existing catalog-only performance tests remain regression checks, not a substitute.
If these exact targets fail, record evidence and fix the measured bottleneck; do not
silently loosen the accepted workload or introduce a different database without review.

## 7. Explicit migration, rollback and final release checks

Before any real cutover, inventory and back up reviewed catalog/source/binding files
and old observation roots. Run service publication and legacy-cache import in dry-run
mode against explicit candidate paths. Review accepted/rejected entry reports; unresolved
identity or permission cannot be inferred from tickers. Keep original retrieval times.

Planned app configuration:

```text
MARKET_STRUCTURE_URL
MARKET_STRUCTURE_TOKEN                  # secret; optional only for loopback development
MARKET_STRUCTURE_REPLICA_ROOT
MARKET_OBSERVATION_CACHE_PATH
```

`MARKET_STRUCTURE_URL` is mandatory in production service mode; missing configuration
does not reactivate local-authority reads. `MARKET_CATALOG_MANIFEST_PATH` becomes an
explicit legacy maintenance/migration input, not a silent fallback. Keep old paths
unchanged until cutover is approved. Retention pruning is an explicit separately
scheduled maintenance operation; its dry-run reports precise candidate files.

Rollback selects a previously reviewed service snapshot through expected-current
publication only when its permissions remain guard-compatible. Otherwise republish the
historical catalog with currently valid restrictive registries and explicitly compatible
bindings as a new complete snapshot; do not edit an immutable historical bundle.
Inventory/back up private service/replica guard generations as well as catalog/cache
files, and preserve the latest guard even if an older CURRENT is restored. Fresh source
review, not publication review, is required to relax known bounds.
Rollback preserves compatible observation generations. Rolling back app code
uses the preserved old cache root; never relabel a new cache version or renew revoked
permissions to make old code run.

Final validation:

```bash
uv run ruff check src packages services tests
uv run pyright
uv run pytest -m "not live" -q
uv build --all-packages --out-dir "$RUN_DIR/wheels"
```

Inspect separate wheels, packaged schemas, dependency metadata, installed CLIs and
app/service isolated environments. Production data migration remains an explicit
operator action after these gates, not a consequence of running this guide.
