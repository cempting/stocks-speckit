# Data Model: Service Structure and App-Owned Observations

This design adds a delivery envelope and cache records. It does not silently change
the v1/v2 catalog grammar, company-evidence formats, or stock/ETF listing enum.

## 1. StructureSnapshotManifest (shared, immutable)

| Field | Type / invariant |
|---|---|
| `format` | Literal `market-structure-snapshot-1` |
| `created_at` | Timezone-aware UTC publication time |
| `catalog` | Catalog manifest logical path, original format, release ID and computed catalog revision |
| `objects` | Unique logical paths with SHA-256, exact byte size and object kind |

`snapshot_id = SHA256(exact manifest bytes)`; the ID is carried in the current entry
and URL, not embedded in its own hashed document. Object paths are portable relative
paths. The descriptor and every referenced object must validate before activation.
Every required catalog artifact and registry is present; no implicit empty registry.
See [snapshot-format.md](contracts/snapshot-format.md).

**Relationships**: Exactly one existing reviewed catalog release, source registry,
issuer-binding registry, observation-policy registry, and index registry per snapshot.
Empty registries are explicit valid documents, subject to reference validation.

**Transitions**: authoring -> captured -> validated staging -> published immutable
snapshot -> selected current. Invalid/stale-expected candidates never change current.
Publication history is retained; rollback selects reviewed bytes through expected-current
publication, not editing an existing snapshot.

## 2. Existing catalog entities (unchanged)

Reuse `CatalogSnapshot`, `Scope`, hierarchy nodes, stock instruments, listings,
memberships, reviewed representations, benchmarks and ledger records. One stock may
have several dated memberships; nested industries remain single-parent and acyclic.
Ancestor rollups deduplicate instruments without merging distinct listings.

Catalog semantic revision differs from transport snapshot ID: a source-permission
change can create a new service snapshot without a membership change. Catalog release
IDs, hashes, review references and original artifact bytes remain inspectable.

## 3. SourceRegistry (shared, new wrapper)

`format=market-structure-sources-1`; fields `sources` and `assessments`.

- **SourceRegistration**: `source_id`, `name`, `kind` (`market_data`, `financial`,
  `disclosure`, `news`, `reference`), `location` (credential-free HTTPS URL or null),
  `region_ids` (explicit applicability; empty means no regional assertion),
  `scope_refs` (explicit existing classification/node scopes), `provenance_reference`,
  `review_state` (`unreviewed`, `approved`, `denied`, `revoked`).
- **SourceAssessment**: Existing exact financial/disclosure/reference record, unchanged
  status, permission, fingerprint, allowed-host/route and expiry semantics.

Source IDs are unique. Assessment references must identify registrations, with compatible
role/kind. `news` and `reference` may have reference-only assessments; these authorize
no acquisition/retention. Publishing news metadata is not publishing article content.
An approved registration cannot override a denied, revoked, missing or expired assessment.

## 4. IssuerBindingRegistry (shared)

`format=market-structure-bindings-1`; field `bindings`, containing exact serialized
`CompanyAssociation` records. Bindings retain independently reviewed nullable issuer
identifiers, source references, separate financial/research evidence, dated listing
continuity and state. Duplicate association IDs or conflicting active bindings fail.

Each binding must match a candidate catalog stock/listing and its `catalog_revision`.
Membership-only revisions can reuse observation continuity when explicit candidate
bindings prove the same identity; the app must not rewrite a binding's revision to
make it appear reviewed. Fetched company profiles/financials/claims remain app-owned,
outside this registry.

## 5. ObservationSourcePolicy (shared; not a reference-only assessment)

`format=market-structure-observation-policies-1`; field `policies`.

| Field | Meaning |
|---|---|
| `policy_id`, `source_id`, `provider_id` | Unique policy identity and registered observation provider |
| `status` | `unreviewed`, `approved`, `denied`, `revoked` |
| `reviewed_at` | UTC review timestamp string or null, conditional on status |
| `review_reference` | Nonblank review reference or null, conditional on status |
| `expires_at` | ISO `YYYY-MM-DD` inclusive UTC expiry date or null, conditional on status |
| `allowed_uses` | Unique array drawn from `collection`, `display`, `normalized_retention`; no implicit grant |
| `region_ids`, `currencies`, `frequencies`, `return_bases` | Exact approved scope |
| `freshness_seconds` | Approved: integer 1 through 3600; otherwise null or a prior reviewed positive limit |
| `max_retention_days` | Approved: explicit positive integer; otherwise null or a prior reviewed positive limit; no default duration |
| `fingerprint` | Lowercase SHA-256 of canonical fields excluding this fingerprint |

Approved policies require review timestamp/reference, expiry, positive limits, and
nonempty applicable scope arrays. Denied/revoked policies require review timestamp/reference;
expiry and limits may be null or retain prior reviewed values. Unreviewed policies have
null review timestamp/reference, expiry and limits. Other statuses have no allowed uses.
Absent/expired policy blocks the corresponding operation.
Daily cache writes require collection and normalized-retention permission; reads require
display and still-valid retention. Existing financial/research assessment gates also
remain in force, independently of this price-data policy.

### Wire grammar and canonical fingerprint

The [registry JSON Schema](contracts/observation-policies.schema.json) is normative.
Every listed field is present, including explicit nulls; unknown fields fail.
IDs/references are nonblank strings without NUL. No trimming, case folding, or Unicode
normalization is implicit. Scope arrays and allowed uses contain unique values; order
is preserved. Currencies use uppercase three-letter codes; regions, frequencies and
return bases must also resolve through existing catalog/provider capabilities, with
no wildcard or new-market inference. Policy IDs are unique within the registry.

`reviewed_at` accepts `YYYY-MM-DDTHH:MM:SSZ` or one to six fractional digits before `Z`;
non-UTC offsets and leap seconds are rejected. The review cannot be in the future at
permission evaluation. For approved policies its UTC date is no later than `expires_at`.
Expiry is exclusive at midnight starting the following UTC date; `expires_at` deliberately
remains a date despite its retained field name. Existing `SourceAssessment` date fields,
fingerprints and formats are unchanged.

Fingerprint material is the complete policy object minus `fingerprint`, including nulls
and arrays in their original order. Normalize a non-null review timestamp to UTC with
exactly six fractional digits and `Z`; retain ISO dates and all other string values
exactly. Encode JSON with sorted object keys, compact `,`/`:` separators,
`ensure_ascii=True`, `allow_nan=False`, then UTF-8; hash those bytes with SHA-256.
This reuses the existing evidence identity fingerprint's sorted/compact ASCII-escaped
JSON convention without changing existing fingerprints. Equivalent JSON key order or
timestamp precision does not alter this fingerprint; array order does.
Snapshot/object hashes still cover exact captured bytes, not canonicalized policy JSON.

## 6. IndexRegistry (shared, additive)

`format=market-structure-indexes-1`; field `indexes`.

**IndexReference**: `index_id`, `name`, `region_id`, `provider_id`, `provider_symbol`,
`calendar_id`, `currency`, `return_basis`, `effective_from`, `effective_to`,
`source_id`, `approval_reference`, `context_purposes` (explicit informational uses).

Stable IDs and active provider aliases are unambiguous. Currency/calendar and provider
capabilities must match. A real index has no stock membership, company binding, or
invented exchange listing; absence of official volume is represented as unavailable.
These records do not override existing catalog ETF benchmark/representation selections.

## 7. StructureReadContext (app, immutable per action)

Fields: `snapshot_id`, catalog snapshot, parsed registries, `mode`
(`online`, `offline_read_only`, `rejected_update_read_only`, `blocked`),
`last_successful_check_at`, `last_attempted_check_at`, diagnostic code/message,
`permission_evaluated_at`, and applicable market date.

Use the injected real clock for permission evaluation even when the requested analysis
date is historical. Historical cutoffs and current permission expiry are distinct.
Pin the context for an entire view/action. Re-evaluate known revocation and operation
capability at side-effect boundaries; do not assemble new structure mid-calculation.

**Transitions**:

- No replica + validated service response -> online; no replica + error -> blocked.
- Replica + matching valid 304 -> online with updated successful-check time.
- Replica + valid new snapshot -> atomically replace replica, then online.
- Replica + transport failure -> offline read-only, with old successful-check time.
- Replica + invalid/incompatible candidate -> rejected-update read-only, never current success.
- Authentication/authorization failure -> blocked; preserve bytes, do not bypass denial.
- Explicit retry + validated response -> online. Service checks occur at start, every
  300 seconds when needed, or explicit retry; ordinary reruns within the interval reuse
  the last known state rather than retrying failures continuously.

Source permissions are checked before cached-content return, including offline display.
The context is not itself proof that any provider or financial scope is approved.
Its effective capability also applies the durable known permission guard in section 11;
an old snapshot or a 304 cannot reset that guard.

## 8. ObservationTarget and SeriesIdentity (app)

A resolved target carries:

- `subject_kind` (`listing` or `index`), stable region/instrument/listing/index IDs.
- Provider/source ID and the effective symbol binding for the requested interval.
- Trading currency, calendar, frequency, observation kind and return basis.
- Normalization version and reviewed continuity fingerprint.
- Current permission/binding provenance, kept alongside identity rather than granting
  rights merely by presence in a cache key.

For stocks, continuity includes independently reviewed issuer identifiers and the
eligible listing/association period, not industry membership. ETFs use their reviewed
instrument/listing continuity. Indexes use reviewed index/provider continuity.

The canonical hashed series identity includes subject IDs, provider/source, currency,
frequency, kind, basis, normalization and continuity fingerprint. It excludes symbol
batches, selected sector/industry, catalog revision, requested dates, UI state and secrets.
Provider alias changes are validated against dated mappings; identical text cannot
merge distinct listings or predecessor issuers.

## 9. ObservationPartition and SeriesGeneration (app, immutable)

Daily Parquet rows: `session_date`, `close`, nullable `volume`, `source_available_on`,
`retrieved_at`, `last_validated_at` and `retention_deadline` in UTC.
Dates are unique and ordered; prices are finite/positive,
reported volumes finite/nonnegative. Stock/ETF volume gaps remain explicit incomplete
volume evidence. Index volume absence is not an acquisition failure of valid closes.
Unchanged still-retainable rows keep original retrieval timestamps/deadlines through
merges; a matching source revalidation advances `last_validated_at`, not their value
provenance. Freshness uses the last validation time, independently of retention age.

A monthly partition belongs to exactly one series identity and adjustment epoch.
A generation manifest holds its identity, generation ID, touched-month object hashes,
full month-to-partition map, covered sessions, known gaps, row counts, source attribution,
adjustment epoch and commit time. A small atomic `CURRENT` points to a complete generation.
Reads select only relevant series/months and pin the generation before reading rows.
Readers hold the series shared OS lock from before CURRENT selection until all selected
partition rows and attempt/gap metadata are materialized. Writers/pruners hold its
exclusive lock; no reader can pin a partition that cleanup removes underneath it.
Committed series retain a stable `.lock` inode even when all price rows are pruned;
never unlink/replace that lock during maintenance. Readers open existing locks without
creation. An absent series/lock in offline mode yields explicit missing coverage without
creating directories/files; a missing lock for an otherwise committed series is corruption.

**Coverage states**: never requested, available, missing, stale, unavailable, error,
or basis-invalidated. Validation age, retention deadline and current policy determine reuse. Failed attempts
are diagnostic outcomes, not successful coverage or zero-valued observations.

**Update transitions**: missing/stale -> in flight -> validated partitions -> committed
generation; failure -> visible attempt outcome with old committed generation unchanged.
An overlap adjustment mismatch invalidates the old epoch before any mixed-basis read.

**Confirmed unavailable gaps**: Persist identity/eligible interval, provider confirmation
code/reference, attempt ID, `checked_at`, and applicable policy fingerprint as diagnostic
metadata, never price rows or complete coverage. Set `checked_at` only after a successful
explicit provider no-data confirmation. Missing rows, empty frames and transport errors
are not confirmation. Failed/unconfirmed partial gaps keep their diagnostic state and
require explicit retry; ordinary reruns and restarts do not refetch them automatically.
For confirmed gaps currently inside the latest five completed official sessions,
one recheck becomes eligible after `min(3600, current freshness_seconds)` from `checked_at`;
older gaps require explicit refresh. Reclassify against today's calendar at query time:
a gap that has left the mutable tail does not gain an automatic historical retry.
Explicit refresh can recheck either kind; all mode/rights/rate-limit/coalescing gates apply.
A repeated confirmation advances `checked_at`, never observation freshness or retention.
If an eligible automatic recheck fails, its terminal error suppresses further automatic
rechecks until explicit retry; the old expired confirmation time cannot trigger a loop.
Offline views may display gap diagnostics but never recheck them.

## 10. AcquisitionAttempt and retention

Attempt records hold attempt ID, affected series/intervals, start/end timestamps, terminal
status and sanitized error, never raw credentials or user selections. They coordinate
waiters but do not authorize a retry or masquerade as observations.

An OS lock protects each series across processes, acquired in stable key order. Reads
use shared locks; acquisition/commit/prune uses exclusive locks. Release shared locks
before requesting exclusive locks; never upgrade in place. After
waiting, recheck coverage/attempt outcome before fetching. On contention return a loading
state after two seconds total across that action's series-lock waits, including shared
read locks; on failure share the failed outcome. UI explicit retry starts
a new attempt; ordinary reruns do not repeatedly retry the failed work.

At acquisition, `retention_deadline` is the earlier of retrieval time plus the reviewed
maximum and the policy's expiry boundary (end of its inclusive UTC expiry date).
Retention also obeys subsequent tighter limits/revocation. A later policy renewal or
migration cannot extend this original deadline or reset retrieval timestamps.
Retention does not derive from analysis date. Expired bytes are never served.
After expiry, an explicitly authorized new acquisition may create new provenance and
a new retention deadline; it cannot reauthorize old bytes by relabeling them.
Explicit `market-observation-cache prune` handles physical cleanup under series locks;
deployment scheduling must satisfy reviewed deletion obligations. Offline UI actions
do not write/prune. Raw provider responses are not retained by this feature.

## 11. Known permission guard (private service/app safety metadata)

Each service publication store and app replica retains a versioned
`market-structure-permission-guard-1` document alongside its existing pointer metadata.
It is a constraint on current reviewed grants, never a grant or another editable
structure authority. It is not exported as a new HTTP object/route.

Entries retain source ID, provider ID for observation policies or existing assessment
role, affected scope/use bounds, restricting record fingerprint and snapshot ID,
review timestamp/date/reference, UTC `observed_at`, review high-water marks/cutoffs,
and tighter retention limits.
Affected scope comes from the previous reviewed grant and its restrictive replacement;
source-wide denial with no narrower known scope applies to the whole source/provider
or source/role. Matching uses those stable identities/scopes, not policy/assessment IDs
alone: renaming an ID cannot bypass a restriction. Preserve original record evidence.

Fully validate a candidate before learning constraints. Denied/revoked records, removed
grants/scopes, shorter expiry or retention, and missing previously approved records
tighten the guard. Serialize guard writers under the existing store/replica writer lock.
Persist/fsync tightened guard state before any corresponding CURRENT activation.
Tightening may survive an activation failure conservatively; it never grants permissions
or turns the failed activation into success. Positive grants come only from the selected
fully validated snapshot. Dry-run and invalid/incomplete candidates never mutate guards.
Only synchronization/publication of a fully validated candidate can learn guard state;
ordinary offline views cannot mutate it. This is restrictive safety metadata, not
observation content or successful structure activation.

CURRENT's private metadata references a minimum required guard generation; the latest
validated guard generation must be at least that new. A newer guard remains effective
even when CURRENT is older after an activation failure; never follow an older pointer
to discard subsequently learned restrictions. HTTP entry bytes
remain exactly the existing two-field contract. Missing/corrupt required guards block
dependent operations with recovery guidance, rather than resetting to empty. Backups,
migration and rollback preserve guards. A new root cannot establish unseen history;
do not claim knowledge of restrictions never received. Service readiness fails closed
if its required guard cannot be validated.

A current grant within all applicable known bounds may operate. Track the greatest
review time already learned for each affected source/provider or source/role scope.
On tightening, its cutoff is the maximum of that high-water mark, the restricting
record's review time and the existing cutoff; never decrease it. This prevents a
backdated denial from making some previously accepted approval look like a fresh review.
Positive-review high-water marks alone do not relax any bound.

Relaxing a known bound
requires an approved, correctly scoped record with a different fingerprint and review
reference and a review time strictly later than its cutoff. A service
publication review reference or old approved bytes are not a fresh source-policy review.
For removed grants with no replacement review, use `observed_at` as the review cutoff.
Existing assessment records retain date-only review semantics: compare UTC dates;
when a restricting review date is absent use its observed UTC date, and an ambiguous
same-day legacy reapproval cannot relax a guard. It remains blocked with explicit
later-review guidance; no existing assessment format is silently upgraded.

Known restrictions persist even after a qualifying new approval: later rollback must
not revive an older grant. Gates consult the guard before cached returns, acquisition,
retention/commit, and final dependent output; invalidate a pinned action and coherently
reload rather than mixing revisions. Guard updates do not require series-wide scans.

For rows acquired on/before a tightening's `observed_at`, retain its shorter deadline as
an irreversible upper bound: minimum of original deadline, applicable reviewed duration/
expiry caps, and `observed_at` if retention permission was removed. A new approval can
authorize genuinely new acquisition, not relabel or revive these expired rows.
Display-only restrictions do not shorten still-authorized retention, but still gate
display until a qualifying fresh review. Pruning enforces these bounds under series locks.
