# Research: Market Structure Service and Persistent Observation Cache

Date: 2026-11-03; refined 2026-11-04. Decisions below are design decisions, not implemented behavior
or measured performance results.

## 1. Independent deployment and dependency direction

**Decision**: Use a uv workspace with three distributions:

- Root `market-leadership`: existing Streamlit app, depending on `market-data`.
- `packages/market-data`: move the existing `market_data` namespace unchanged;
  own shared domain, schemas, catalog/evidence readers, and new delivery records.
- `services/market-structure`: own `market_structure` server and the existing
  `market_data_tools` maintenance namespace, depending on `market-data`.

The app's optional `maintenance` extra installs the service/tool distribution for
old explicit CLI delegates. Ordinary app installation does not require the service
or administration tools. Service installation does not require Streamlit,
yfinance, Massive, or app caches. Keep namespace identities and schema resources;
move distribution ownership rather than duplicating domain modules.

**Rationale**: The current [wheel configuration](../../pyproject.toml) ships all three
namespaces with UI/provider dependencies. Another command in that wheel would not
demonstrate installation isolation. Separate deployment is a confirmed requirement.

**Alternatives considered**: Same wheel with another entry point; rejected for
dependency isolation. Separate repository; not selected by the user. Fourth tools
distribution; unnecessary because tools and service share operational ownership.

**Implementation correction approved 2026-11-04**: Installed metadata proves existing
Streamlit 1.66.1 requires `starlette>=0.46.0,<2` and `uvicorn>=0.30.0,<1`.
Ordinary app installs may contain these transitive UI dependencies but must still omit
`market_structure` and `market_data_tools`; the app never imports service internals.
The user chose this boundary instead of constraining an older Streamlit. Shared-only
installs still omit the server frameworks. Clean-wheel bootstrap also exposed repository-
relative daily/weekly schema loading; package the unchanged schemas with shared resources
and use `importlib.resources`, preserving contract bytes rather than shipping the spec tree.

## 2. Read-only HTTP delivery

**Decision**: Starlette `>=0.47,<1` and Uvicorn `>=0.35,<1`, resolved and locked during
implementation, serve a current pointer, immutable snapshot manifests, and explicitly
published digest-addressed objects. Use HTTPX `>=0.28,<1` in the app for bounded
streaming downloads. Expose no HTTP authoring or observation proxy endpoints.

**Rationale**: A small read-only application does not need another domain-model
framework. Shared validators remain authoritative. Raw artifacts avoid archive
extraction, repeated compression, and whole-release retransfers.

**Alternatives considered**: FastAPI adds Pydantic/OpenAPI generation not needed for
these few routes; handwritten stdlib HTTP serving lacks a production server;
ZIP transport adds extraction and duplicate transfer; per-node live queries permit
mixed revisions and require a remote query/index service unnecessarily.

**Verified external guidance**: A bounded research agent checked official upstream
documentation and HTTP standards, without inspecting repository code:

- [Python HTTP server guidance](https://docs.python.org/3/library/http.server.html):
  `http.server` is not recommended for production.
- [Starlette upstream documentation](https://github.com/encode/starlette/tree/master/docs):
  lightweight ASGI responses/static serving. Its default file ETag is based on
  filesystem metadata, not our content identity; supply digest-derived ETags explicitly.
- [Uvicorn settings](https://github.com/encode/uvicorn/blob/master/docs/settings.md):
  concurrency limits, keep-alive and shutdown controls. These are not download-size
  limits; the client and publisher enforce the contract limits separately.
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), sections 8.8.3, 13.1.2,
  and 15.4.5: entity tags, conditional GET comparison, and bodyless 304 responses.
- [RFC 8246](https://www.rfc-editor.org/rfc/rfc8246.html): immutable caching applies
  to version-addressed objects, not a mutable current pointer.

## 3. Preserve reviewed catalog semantics; add a delivery envelope

**Decision**: A `market-structure-snapshot-1` manifest pins exact existing v1/v2
catalog bytes plus versioned source, permission, binding, and index registries.
The SHA-256 of exact manifest bytes is the snapshot ID. A local publisher captures,
validates, stages, and atomically activates the entire bundle using expected-current
comparison. Do not separately read a mutable catalog pointer and mutable permissions.

**Rationale**: [Catalog loading](../../packages/market-data/src/market_data/catalog.py) already validates
contained paths, bounded artifacts, checksums, references, governance, and v1/v2
semantics. Materialize those same bytes in the replica and use `load_release`;
do not write a weaker HTTP-only catalog parser.

Registry records reuse `CompanyAssociation` and financial/disclosure/reference
`SourceAssessment` semantics. A news directory entry does not grant acquisition.
Add a distinct reviewed observation-source policy: current reference-only assessments
explicitly prohibit authorizing uses and must not be repurposed as price-data licenses.

**Alternatives considered**: New flattened taxonomy payload replacing v1/v2; loses
the existing validation contract. Live cross-store assembly; risks mixed permissions
and hierarchy. Exporting arbitrary evidence folders; risks including fetched content,
credentials, or unreviewed files. Silently redacting reviewed bytes; changes provenance.
Publishers must review exportability; private authoring paths are never dereferenced
by consumers and require a separately reviewed portable release if unsuitable to export.

## 4. Genuine indexes are not stock or ETF listings

**Decision**: Add a versioned `indexes.json` registry of reviewed index identities,
provider mappings, calendars, currency, return basis, effective dates, and intended
context. Index observation targets have `subject_kind=index`; they never become stock
members or ETF industry representations. Existing ETF benchmarks remain unchanged
unless a separately reviewed feature changes their selection semantics.

**Rationale**: [Listing validation](../../packages/market-data/src/market_data/domain/catalog.py) currently
accepts stock/ETF only. Widening that enum silently would change the v1/v2 contract.
Index close coverage may be valid with no volume; charts must show unavailable volume,
not manufactured zero volume. Index requests still obey the configured provider's
existing market/currency capabilities; no new geography is inferred.

**Alternatives considered**: Treat indexes as ETFs or use ticker-shaped identifiers;
both misstate identity. New catalog release version just for transport/index context;
unnecessary when the additive service registry is explicitly versioned.

## 5. Per-identity interval coverage, not another request cache

**Decision**: Add an app-owned store of immutable monthly Parquet partitions addressed
by stable series keys, with one atomic generation manifest per series. Keys include
identity, provider, currency, frequency, basis, normalization, and reviewed continuity;
exclude hierarchy path, member batches, and catalog revision. Requested date intervals
are coverage selectors, not components that prevent partial reuse.

Reuse pandas/PyArrow and existing canonical validation. Resolve target IDs through the
pinned structure before reaching a provider. Preserve the low-level provider interface;
refactor production orchestration and all callers to supply typed identity context.

**Rationale**: [Current disk caching](../../src/market_leadership/infrastructure/market_data_cache.py)
hashes the complete symbol batch and range. [Member caching](../../src/market_leadership/ui/cache.py)
reuses individual symbols in-process but still keys by date and does not prove listing
ownership. Neither is the persistent interval/identity contract required by FR-010--017.
[History eligibility](../../src/market_leadership/application/load_stock_history.py)
already bounds stock observations by reviewed listing/issuer continuity; preserve it.

**Alternatives considered**: SQLite index plus Parquet payloads; adds transactional
storage and conflicts with existing app SQL boundaries without a demonstrated need.
Single ever-growing global Parquet file; rewrites/scans unrelated instruments.
Sector/industry folders; duplicate overlapping members and break on reclassification.
Redis, queues, and lakehouse frameworks; not required for one deployment-local cache.

## 6. Freshness, retention, and adjusted-history corrections

**Decision**: Service metadata revalidation interval is 300 seconds, plus explicit
retry/refresh. Current daily tails have a maximum one-hour freshness, matching the
existing UI history TTL. The mutable daily tail is the latest five completed market
sessions at the injected clock. Older closed observations remain reusable within
reviewed retention limits until invalidated or explicitly refreshed.

An interval extension/revalidation overlaps at most one preceding eligible session.
If adjusted values disagree in that overlap, invalidate the held adjustment epoch
and reacquire the actively requested eligible window before using it. Other held
windows become explicitly stale, not mixed with the new basis. Historical corrections
outside observed overlap require explicit selected-window refresh; do not claim a
provider revision feed that the adapter does not supply.

Observation policy requires a reviewed maximum retention duration; no universal
license duration or implicit approval is invented. Expired/revoked data is withheld;
explicit cache maintenance purges expired retained files, independently of navigation.
Offline views permit no new acquisitions or content writes and never renew permissions.
Only fully validated synchronization may persist restrictive guard metadata; it does
not activate content or advance the successful-check clock when activation fails.

**Rationale**: [yfinance acquisition](../../src/market_leadership/infrastructure/yfinance_provider.py)
uses adjusted prices and does not expose a corporate-action revision token. Appending
new adjusted values to an incompatible old basis would silently corrupt returns.
TTL alone does not establish licensing or historical correctness.

**Alternatives considered**: Refetch every history hourly; wasteful. Append forever
without correction checks; unsafe. New raw-price/action ingestion model; broader than
this feature. Unlimited retention; not supported by source reviews.

## 7. Concurrency, coherent publication, and outage state

**Decision**: Use deployment-local filesystem locks (`fcntl.flock`) in stable key order,
recheck coverage after acquisition, and publish fsynced immutable files before atomic
pointer replacement. Share successful results and sanitized attempt outcomes across
waiters. Lock contention returns an explicit loading state after a bounded wait, never
a duplicate upstream request. One cache directory on a local filesystem is the supported
deployment unit; distributed/NFS cache coordination is out of scope.

Persist a validated structure replica and separate last-attempt/last-success timestamps.
Pin a read context per rerun/action. Transient service errors or invalid new revisions
yield a marked read-only replica; a failed check is never recorded as a successful
current check. Unauthorized service access blocks dependent views while retaining
bytes for explicit recovery. Permission and mode gates run before in-memory cache hits
and immediately before acquisition/publication.

**Alternatives considered**: Session-state shared cache; incorrect cross-user ownership.
In-process locks only; do not coordinate multiple processes. Expiring lock files and
lease stealing; unnecessary with OS-managed locks. Silent stale success; prohibited.

## Resolution status

The four refinements below were confirmed by the user on 2026-11-04. They use existing
technology/source evidence; no new dependency or external technology research is needed.

### A1. Exact observation-policy grammar

**Decision**: Adopt the [registry schema](contracts/observation-policies.schema.json)
and canonicalization rules in [data-model.md](data-model.md). Explicit tokens are
`collection`, `display`, `normalized_retention`; review is a UTC timestamp while expiry
is an inclusive UTC date. All keys are present; nullability depends on review status.
Use sorted compact ASCII-escaped JSON for fingerprints, normalizing review precision.

**Rationale**: Both applications and hand-authored publication inputs need one exact
grammar. Existing [identity fingerprints](../../packages/market-data/src/market_data/domain/company_evidence.py#L69)
already use sorted compact JSON with default ASCII escaping; existing
[SourceAssessment](../../packages/market-data/src/market_data/domain/company_evidence.py#L247) uses the same
permission tokens and date-only legacy reviews. Preserve those existing formats.

**Alternatives considered**: Implicit defaults/implementation-selected tokens; rejected
as ambiguous. A second unescaped-Unicode fingerprint convention; unnecessary. Renaming
legacy fields or upgrading existing assessments implicitly; outside this feature.

### A2. Terminal unavailable-gap behavior

**Decision**: Persist provider-confirmed unavailable intervals as diagnostics. Reuse
their terminal outcome across reruns/restarts; recheck current mutable-tail gaps once
the reviewed freshness interval elapses, historical gaps only on explicit refresh.
Unconfirmed missing/partial/error outcomes require explicit retry.

**Rationale**: Avoid repeated upstream calls without pretending that unavailable data
is a successful observation or permanently proving no trading occurred. Existing
attempt metadata can carry confirmation times; no separate negative-cache service.

**Alternatives considered**: Retry every rerun; wastes calls. Mark gaps complete; false
evidence. Automatically poll every historical gap forever; violates active-view limits.

### U1. Reader/pruner coordination

**Decision**: Hold `fcntl.flock` shared locks while selecting a generation and loading
its selected rows/diagnostics. Use exclusive locks for acquisition, commit and prune;
release shared locks before requesting exclusive locks and recheck under the new lock.
Apply the existing two-second aggregate wait budget to all series lock acquisitions.

**Rationale**: Pinning an immutable filename alone does not stop cleanup unlinking it
before a reader opens it. The already selected POSIX lock supports read/write exclusion
without another service, reference-count registry or delayed deletion license loophole.

**Alternatives considered**: Reader leases/refcounts; additional lifecycle machinery.
Unlocked reads plus retry/re-pin; not selected by the user. Keeping expired generations
indefinitely; violates physical retention cleanup.

### A3. Restrictions survive rollback and restart

**Decision**: Keep durable private constraint guards in both publication and replica
stores; reject publication that would restore obsolete rights and gate consumers
against all known bounds. Guard tightening precedes pointer activation. A historical
catalog can be republished with currently valid registries; selecting historical
approved metadata is not new source authorization.

**Rationale**: Expected-current comparison protects concurrent publication, not
permission rollback. New policy timestamps give exact review ordering; unchanged
date-only legacy assessments require strictly later review dates when relaxing a
known bound, failing closed on same-day ambiguity. Preserve original retention caps.

**Alternatives considered**: Trust the selected old policy alone; resurrects obsolete
approvals. Store only in session memory; loses restrictions on restart. Add an HTTP
write/authorization service or alter legacy evidence formats; unnecessary.

Transport, packaging, versioning, storage, identity, indexes, news-source scope,
freshness, correction handling, concurrency, and outage behavior are resolved above.
All four analysis findings now have explicit design decisions, validation scenarios,
and coverage in the [refreshed test-first backlog](tasks.md). Run `/speckit-analyze`
before implementation.
Performance numbers remain acceptance targets to measure during implementation.
No new runtime dependency was installed and no runtime behavior was changed in planning.
