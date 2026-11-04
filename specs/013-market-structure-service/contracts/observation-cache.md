# App Observation Store Contract v1

Scope: app-owned durable coverage for stock/ETF/index data, separate from service-owned
structure. Existing financial/research evidence formats remain unchanged.

## Acquisition boundary

An observation query contains one pinned `StructureReadContext`, resolved identity
targets, requested eligible intervals, freshness policy and explicit refresh intent.
No production provider request may rely on ticker, selected industry, or batch
membership as ownership proof.

Operation order:

1. Validate context mode, current source permissions and target identities/continuity.
2. Resolve completed official sessions inside eligible intervals; do not use industry
   membership dates to truncate valid listing history.
3. Acquire shared series locks and read CURRENT/generation manifests directly by stable key.
4. Under those locks read only intersecting monthly partitions and attempt/gap metadata;
   materialize selected rows, classify coverage, and release shared locks.
5. Return complete valid local coverage without a provider call.
6. For eligible misses, acquire exclusive series locks in lexical key order; shared
   locks must already be released, never upgraded in place. After at most two seconds
   total series-lock wait, including shared reads, return a typed loading outcome.
   Never start a second fetch merely because of contention.
7. Recheck coverage and overlapping attempt outcomes under lock. Coalesce identical
   concurrent misses; propagate a completed failed attempt to its waiters.
8. Recheck online mode/permissions; request only missing/stale intervals plus at most
   one preceding eligible reconciliation session. Group only compatible targets sharing
   provider, currency, frequency, return basis and interval. No off-view universe prefill.
9. Canonicalize results, preserve partial/missing outcomes explicitly, reconcile basis,
   and recheck permissions before retaining permitted data.
10. Publish touched partitions and a complete new generation atomically per series.
    Return structured coverage/outcome metadata; do not turn an exception into empty success.

Provider adapters keep their raw symbol-based fetch interface internally. The application
use case owns symbol-to-identity resolution and gates; raw adapters are not an alternate
production cache route. Financials and stored research still require their existing
explicit actions and separately reviewed evidence scopes.

## File layout

```text
<observation-root>/v1/
  series/<first-two-key-hex>/<series-key>/
    .lock
    CURRENT
    generations/<generation-id>.json
    parts/<YYYY-MM>/<content-sha256>.parquet
    attempts/<attempt-id>.json
```

Identifiers are safe hashes, never unsanitized provider symbols. CURRENT is a bounded
document naming a validated generation and its hash. Generation manifests include the
full identity, adjustment epoch, partition map/checksums, covered sessions, known gaps,
original retrieval attribution and commit time. Partition objects are immutable;
overwriting an existing object's bytes is invalid.

Only a target's selected month manifests/rows are read for a query. Startup and ordinary
navigation do not glob all instruments or concatenate the full held universe.
Derived hierarchy/rollup results may depend on structure revision, but observation
paths and historical ownership do not.

## Write and read guarantees

- Merge by session date within a series/epoch. Same values are idempotent; changed
  validated values replace affected dates with new retrieval provenance. Unchanged
  dates keep their original timestamps and retention deadlines, including during migration.
  Successful matching revalidation updates `last_validated_at` so already rechecked
  daily tails are not immediately treated as stale again. This is not a retention renewal.
- Build/fsync new touched-month objects, then a new generation manifest, then replace
  CURRENT atomically and sync its directory. Untouched partitions are referenced,
  not copied or rewritten. Each series commit is atomic; a multi-series result records
  the pinned vector of series generations and per-series outcomes, not a fictitious
  globally simultaneous market timestamp.
- Interrupted writes leave the previous CURRENT readable. Orphan staging bytes are
  reported and cleaned under an explicit maintenance operation, never made current.
  Missing/corrupt referenced bytes are diagnosed, not silently returned as current data.
- OS-managed local-filesystem locks release on process death. No stale-lease stealing,
  process-name killing, or in-memory-only lock guarantee. NFS/distributed caches are
  unsupported and must fail configuration validation rather than claim coordination.
- Shared locks remain held through selected partition loading, not just manifest
  selection. Every writer/pruner holds the same series' exclusive lock through pointer
  replacement and cleanup; an active reader's files cannot be removed underneath it.
  Use lexical ordering and one aggregate two-second contention budget. On a read miss,
  release shared locks, obtain exclusive locks and recheck; no lock upgrade or waiting
  for a series lock while retaining a replica/publication writer lock.
- Never unlink or replace a series `.lock`, including after pruning its last price row:
  waiting/open descriptors must continue to refer to the same lock inode. Readers open
  existing locks without creation; absent offline series return explicit missing coverage
  without filesystem writes. A committed series missing its lock is diagnosed as corrupt.
- Failed attempt metadata may coordinate waiters; it is not cached successful data.
  After failure, normal widget reruns show the same actionable failure. Explicit retry
  starts a new attempt; bounded provider retries remain visible in attempt accounting.

## Freshness and adjusted-price reconciliation

- Use the injected clock and each target's official calendar. Never fetch incomplete
  sessions merely because the wall-clock date advanced.
- The latest five completed official sessions are the mutable tail. Their reuse limit
  is the smaller of one hour and the approved policy's freshness limit, measured from
  `last_validated_at`, not the original retrieval time.
- Older closed coverage remains reusable within retention/permission bounds. Its
  retrieval time is shown; this is not a guarantee of detecting unobserved historical
  provider corrections. Explicit refresh revalidates the selected eligible window.
- An extension or stale-tail refresh includes at most one preceding eligible held
  session for comparison. No overlap crosses listing/issuer continuity boundaries.
- If an adjusted overlap disagrees, mark the held basis epoch invalid before merging.
  Reacquire the actively requested eligible window as stale coverage; hold older
  out-of-window data as basis-invalidated until separately requested. Never combine
  new adjusted values with old-scale history or silently use the old epoch after failure.
- A known provider correction/basis change can explicitly invalidate a series even
  without overlap disagreement. Record the reason and do not rewrite unrelated series.

## Partial data and volume

Valid price observations may be retained when another target fails, but gaps remain
visible and do not become complete coverage. Preserve provider-reported no-data periods
and actual returned coverage; a missing response does not prove a listing did not trade.
Invalid/empty/error responses do not create fresh successful partitions.

### Confirmed unavailable intervals

Only explicit provider confirmation creates `unavailable` gap metadata; absence of a
row, empty frame, HTTP failure or unrequested date is not such confirmation. Preserve
series/interval identity, confirmation code/reference, attempt ID, UTC `checked_at`
and policy fingerprint in the existing attempt/gap metadata. It grants no permissions,
contains no synthetic price/zero volume, and does not mark the interval complete.

Ordinary reruns and process restarts reuse the terminal diagnostic. When an unavailable
session is still in the latest five completed official sessions, it becomes eligible
for one recheck after `min(3600, current freshness_seconds)` from `checked_at`; classify
against the current calendar, not the age category at original request. A session
that has moved outside that tail requires explicit selected-window refresh.
Reconfirming no-data updates only `checked_at`; repeated reruns do not immediately poll.
Historical unavailable intervals require explicit refresh regardless of elapsed time.
Concurrent due rechecks share one acquisition through the same exclusive-lock recheck.
If that recheck fails, its terminal error takes precedence over elapsed `checked_at`;
subsequent reruns/restarts require explicit retry rather than polling the expired gap.

Unconfirmed partial gaps and errors remain distinguishable diagnostic outcomes of
their attempt; reruns/restarts preserve them until explicit retry/refresh, rather than
turning every still-missing row into a new request. An explicit refresh may recheck
either confirmed or unconfirmed gaps. Offline mode and current rights always take
precedence over elapsed freshness; no metadata TTL is authorization.

Stock/ETF incomplete volume remains unavailable evidence and cannot produce valid
official-volume conclusions. True indexes may have close-only coverage; retain null
volume and show unavailable volume rather than synthetic zeros. No genuine index is
passed off as an ETF or stock listing to satisfy an old schema.

## Outage and permission gates

Offline/rejected-update read-only contexts can read eligible committed data but cannot
fetch, refresh, publish, or prune observation/structure content. Session navigation and
sanitized synchronization-attempt diagnostics are not authoritative content writes.
Display requires applicable still-valid permission;
the requested historical analysis date cannot backdate today's source permission.
Source revocations received in a newer structure context invalidate affected cached
display/acquisition rights even when an in-memory cache contains a prior result.
If a newer known revision invalidates a pinned action's permissions, abort/withhold
that action and request a coherent reload rather than combining old members with new rights.
Apply the durable known permission guard from [data-model.md](../data-model.md) before
cached returns, acquisition/commit and final output, including after rollback/restart.
Renaming a policy/assessment ID or restoring old CURRENT cannot erase a source/scope
restriction. Fresh qualifying review can authorize new work, never revive expired rows.
Guard learning belongs only to fully validated synchronization/publication; ordinary
offline navigation cannot mutate it. Restrictive synchronization metadata surviving
an activation failure is not a content update or successful current check.

Check gates outside `st.cache_data` before a hit can return and immediately before
provider/commit side effects. Include series/generation and relevant identity/policy
fingerprints in cached request keys; include structure revision for derived cohorts.
Do not place tokens, credentials or user selections in shared response values.

## Migration and maintenance

New schema root is separate from request-hash caches. Unknown generation versions
produce explicit incompatible-cache status; no silent deletion or implicit reinterpretation.
An explicit migration report identifies accepted, ambiguous, expired, failed and
unverifiable old entries, and counts imported rows. Imports need reviewed exact identity
and period/issuer continuity proof, original timestamps, applicable permission and
validation. No automatic ticker-based linking or freshness renewal.

Planned maintenance CLI:

```text
market-observation-cache status --root PATH
market-observation-cache import-legacy --root PATH --legacy-root PATH \
  --structure-replica PATH --dry-run
market-observation-cache import-legacy --root PATH --legacy-root PATH \
  --structure-replica PATH --review-reference TEXT
market-observation-cache prune --root PATH --structure-replica PATH [--dry-run]
```

Operations return versioned JSON, selected roots, row/series counts, per-entry reasons
and sanitized errors. Status/dry-run never fetch or mutate. Mutating operations require
explicit roots, permissions, locks, and validated replica metadata. Physical retention
cleanup is explicit maintenance, scheduled to meet reviewed deletion limits; readers
always withhold expired data even before cleanup. Never delete the legacy source tree
or expand rights as a side effect of import.
Prune acquires exclusive series locks using the same two-second aggregate contention
budget and reports loading/contention explicitly without deleting locked content.
Readers use shared locks through row materialization; maintenance must not rely on
the manifest pin alone or keep expired generations indefinitely for reader safety.
Pruning removes expired rows from retained partitions without deleting still-permitted
rows, then cleans obsolete generations/unreferenced objects carrying expired data.
It must not keep an expired historical generation as a rollback escape from retention.
Every removed or rewritten path must be resolved inside the explicitly selected cache.

The original row retention deadline is an upper bound even after source-policy renewal.
Current revocation/expiry or a tighter reviewed duration may shorten it; ordinary reads,
refresh of unrelated dates and migration cannot extend it.
Expired rows are not reusable. A permitted new source acquisition can replace them
with newly attributed data; a cache hit, unchanged policy file or metadata-only import cannot.
