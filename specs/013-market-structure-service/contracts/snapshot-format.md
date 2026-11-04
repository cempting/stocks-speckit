# Market Structure Snapshot Contract v1

Normative alongside [HTTP contract](market-structure.openapi.json) and
[data model](../data-model.md). Existing catalog and company-evidence validators
remain authoritative for their embedded records.

## Envelope and object graph

Current entry:

```json
{
  "format": "market-structure-entry-1",
  "snapshot_id": "64-lowercase-hex-digits"
}
```

The ID is the SHA-256 of exact snapshot manifest bytes. Manifest example, with
illustrative digest placeholders that must be replaced for a real candidate:

```json
{
  "format": "market-structure-snapshot-1",
  "created_at": "2026-11-03T10:00:00Z",
  "catalog": {
    "path": "catalog/manifest.json",
    "format": "market-catalog-release-2",
    "release_id": "reviewed-release-id",
    "catalog_revision": "64-lowercase-hex-digits"
  },
  "objects": [
    {
      "path": "catalog/manifest.json",
      "kind": "catalog_manifest",
      "sha256": "64-lowercase-hex-digits",
      "size_bytes": 1000
    }
  ]
}
```

The example omits required catalog artifacts and four required registry objects for
brevity; an actual manifest is complete:

| Logical path | Kind | Record format |
|---|---|---|
| `catalog/manifest.json` | `catalog_manifest` | Existing market-catalog-release-1 or -2 |
| `catalog/<original artifact path>` | `catalog_artifact` | Exact referenced CSV/JSONL bytes, no weaker HTTP grammar |
| `registries/sources.json` | `source_registry` | market-structure-sources-1 |
| `registries/bindings.json` | `issuer_bindings` | market-structure-bindings-1 |
| `registries/observation-policies.json` | `observation_policies` | market-structure-observation-policies-1 |
| `registries/indexes.json` | `index_registry` | market-structure-indexes-1 |

Registry fields, references and validation rules are defined in the data model.
The [observation-policy schema](observation-policies.schema.json) supplies exact
required fields/types/tokens; [canonical fingerprints and permission guards](../data-model.md)
remain shared semantic validation, not a JSON Schema licensing grant.
Documents use UTF-8 JSON, exact fields, finite numbers, ISO dates, UTC timestamps,
and unique stable IDs. Unknown formats/fields and invalid fingerprints fail closed.
New transport schemas and typed parsers live in `market_data`; server and consumer
must run the same validators. No inferred default approval or empty-document fallback.

Paths are logical materialization names, never URLs. They must be relative POSIX
paths with no empty, `.` or `..` components, backslashes, drive letters, query,
fragment, symlink, NUL or URI scheme. Duplicate paths, multiple catalog manifests,
unknown object kinds, missing registries, or unreferenced catalog files are invalid.
Objects with identical digest/bytes may serve several validated logical references.

Do not include fetched prices, financial observations, claims, credentials, private
request headers or arbitrary filesystem directories. Export of original catalog
audit/archive/provenance bytes must be explicitly reviewed; no silent redaction or
client dereferencing of authoring research roots is allowed.

## Validation and activation

1. Capture the selected reviewed catalog release and explicit registry files.
2. Validate catalog v1/v2, source and policy fingerprints, binding/catalog references,
   index mappings, and export review. No runtime source acquisition occurs.
3. Store captured bytes by digest and construct the descriptor. Serialize once; its
   exact digest is the snapshot ID, independent of JSON re-encoding by a consumer.
4. Materialize a candidate and run shared validation again, including `load_release`.
5. Under a writer lock, compare the expected current snapshot (`none` for empty).
   Apply the private known-permission guard: reject obsolete authorization expansion,
   persist/fsync newly learned restrictions and review high-water marks, and fsync
   objects/descriptor. Then atomically replace CURRENT and fsync its directory.
6. On expected-current conflict or validation failure, return an explicit failure
   without replacing current. Uncertain post-replace errors report an uncertain
   publication outcome and operation ID, not a rollback/success claim.

A consumer follows the same validate-before-activate order in its own replica directory.
It persists validated restrictions before activation and applies them to older pinned
contexts too. Guard metadata is private to each store, never added to the two-field
HTTP entry or exported as an extra object kind/endpoint. A conservatively tightened
guard may remain after a failed activation; preserve the old structure and report the
failure, never turn this into a successful synchronization. Invalid/incomplete
candidates and dry-runs cannot update guards. Missing/corrupt required guards block
dependent operations/readiness; do not silently initialize an empty replacement.
Its CURRENT is not service authority and may only select a fully validated downloaded
snapshot. A 304 is usable only with the matching validated local entry; otherwise retry
once without a conditional header. Artifact downloads use configured-origin fixed routes,
not object-provided URLs. Reject redirects, over-limit responses and content mismatch.

## Bounds

- Current entry and snapshot manifest: at most 1 MiB each.
- Object count: at most 256; each object at most 64 MiB; total distinct bytes <=1 GiB.
- Registry record size <=1 MiB; record and row types checked before activation.
- Keep existing catalog field/record/artifact bounds; the envelope never relaxes them.
- Client: HTTPX connect timeout 2 s, read timeout 5 s, pool timeout 2 s; each download
  also has a 30 s elapsed budget checked while streaming. At most two downloads at once.
  At most one bounded retry for transient failures; manual retry remains available.
- Service: default maximum eight concurrent responses, bounded validated object reads;
  no automatic compression, archive building, or whole-universe processing on GET.

## Operational commands (to implement)

```text
market-structure publish --store PATH --catalog-release PATH \
  --registry-dir PATH --expected-snapshot ID|none --review-reference TEXT [--dry-run]
market-structure serve --store PATH [--host 127.0.0.1] [--port 8765]
```

Publication output is versioned JSON with operation ID, candidate snapshot ID,
catalog revision, expected/current snapshot, validation state and publication state
(`not_published`, `published`, `unknown`). Exit 0 means the requested action succeeded;
exit 2 means validation/conflict/failure or unknown outcome. Diagnostics go to stderr.
`--dry-run` performs capture/validation but never alters published objects/CURRENT.

Use explicit paths and an explicit expected snapshot. `publish` is local administration,
not an HTTP upload. Startup never imports or activates authoring data automatically.

## Permission-safe rollback

Rollback does not discard the service/app guards described in the data model. Selecting
an older complete snapshot is permitted only if its grants remain within known bounds
or carry a qualifying fresh source review. `--review-reference` reviews the publication,
not the source's rights; it cannot reapprove an old policy/assessment.

If historical source metadata would restore revoked rights or loosen tighter limits,
publication fails explicitly with no CURRENT replacement. Republish the reviewed
historical catalog with currently valid restrictive registries and explicitly compatible
bindings instead; construct/validate a new complete manifest rather than editing old
immutable bytes. Backups and operator recovery preserve private guard generations.
Fresh source reapproval must satisfy the review cutoff/fingerprint/reference rules;
it never renews original or subsequently shortened observation retention deadlines.

## Deployment and mode

The server reads only its reviewed published store; ordinary serving has no write access.
The publisher has separate write permissions. The app has no service filesystem access.
It writes only its replica, observations, and already permitted company-evidence store.

Development is loopback-only by default. Remote clients require HTTPS and bearer
authentication, supplied from environment/secrets and excluded from logs/cache keys.
Non-loopback service binding requires explicit configuration and a read token;
deploy behind a TLS gateway, not an unauthenticated public listener. Invalid credentials
produce 401/403 and block dependent app views; they are not ordinary offline access.

ETag syntax is `"sha256:<lowercase SHA-256 of exact response representation bytes>"`.
For CURRENT this hashes the entry bytes, not just its embedded snapshot ID.
`/v1/current` uses `Cache-Control: no-cache` and that content-derived ETag. Immutable
manifests/objects use `Cache-Control: private, max-age=31536000, immutable` and exact
byte-derived ETags. Implement RFC 9110 conditional matching, including tag lists and
weak comparison for If-None-Match; default filesystem mtime tags are not sufficient.
