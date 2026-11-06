# Implementation Plan: Market Structure Service and Persistent Observation Cache

**Branch**: `main` (unchanged) | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: `specs/013-market-structure-service/spec.md`

The setup script reports feature key `013-market-structure-service` as `BRANCH`;
the actual Git branch is `main`. Planning does not create or switch branches.

## Summary

Deliver a separately installable/runnable `market-structure` service in this repository.
It serves an immutable, reviewed catalog/source/identity bundle through a small read-only
HTTP contract. The stock app validates and retains a local replica, pins each action to
one structure revision, and owns a persistent per-identity observation store with
incremental coverage. Empty caches initialize on demand; outages permit visibly marked,
permission-gated read-only browsing, not new acquisition.

Reuse catalog validators, canonical provider adapters, listing-history eligibility,
reviewed evidence models, and the existing Streamlit caching patterns. Do not add a
structure database, distributed cache, background universe prefill, article collector,
or new stock-screening surface. See [research decisions](research.md).

### Approved analysis refinements (2026-11-04)

The user confirmed all four decisions from the preceding analysis:

1. **A1**: Exact policy tokens, UTC review timestamps, inclusive UTC expiry dates,
   status-dependent required/null fields and canonical fingerprints; the normative
   [policy registry schema](contracts/observation-policies.schema.json) now defines
   syntax, with cross-record/time/capability rules in the [data model](data-model.md).
2. **A2**: Confirmed unavailable mutable-tail gaps recheck after reviewed freshness;
   historical gaps require explicit refresh. Failed/unconfirmed gaps do not retry on
   rerun/restart. Gap diagnostics never become successful observation coverage.
3. **U1**: Shared series locks cover CURRENT selection through row materialization;
   acquisition/writers/pruners use exclusive locks. No in-place lock upgrade; recheck
   after reacquiring. The two-second total lock-wait budget includes readers.
4. **A3**: Private durable known-permission guards survive rollback/restart. Historical
   structure cannot restore older rights; relaxing a known bound requires a fresh
   source-policy review. Original/tightened row retention deadlines never renew.

These refine FR-005, FR-012--016, FR-018 and FR-020--022 without changing the five HTTP
operations, catalog v1/v2, existing evidence formats, provider choice or performance
targets. No new dependency, database or distributed coordination is required.
The [implementation backlog](tasks.md) was subsequently refreshed with 96 unchecked
test-first tasks incorporating these decisions. Analysis completed without actionable
findings; implementation is now in progress. Task checkboxes record validated progress.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`, unchanged.

**Primary Dependencies**: Existing Streamlit, pandas, PyArrow, JSON Schema and yfinance
on their current constrained ranges. New service-only Starlette `>=0.47,<1` and Uvicorn
`>=0.35,<1`; app HTTPX `>=0.28,<1`. Resolve exact versions in `uv.lock` when manifests
change; build the service and shared-data wheels without UI/provider dependencies.
Implementation verified that existing Streamlit 1.66.1 itself requires Starlette/Uvicorn.
The user approved allowing those transitive UI dependencies while excluding the actual
service/tools distributions from ordinary app installs. Do not downgrade Streamlit to
enforce an invalid framework-absence assumption; app source does not import server internals.

**Storage**: Service-owned immutable file releases, digest-addressed objects, atomic
current pointer; app-owned validated structure replica and per-series monthly Parquet
partitions with immutable generation manifests, terminal gap diagnostics, and private
permission-guard metadata in the existing publication/replica stores. Existing app-owned
financial/research evidence storage remains separate. No SQLite in app/modern service.

**Testing**: pytest contract/unit/integration/AppTest; isolated service/client processes;
fake clocks and recording providers; existing Ruff and strict Pyright; wheel dependency
and import-isolation tests; exact SC-002--006/008 workload benchmarks; schema rejection
cases, unavailable-gap clock/restart tests, reader-versus-pruner processes, and
revocation/rollback/reapproval/restart faults.

**Target Platform**: macOS development and Linux deployment, local filesystem supporting
POSIX locks, fsync, and atomic rename. HTTPS and authentication required for remote
service access; default development server is loopback-only.

**Project Type**: uv monorepo workspace: shared contract library, read-only service plus
maintenance tools, existing Streamlit application.

**Performance Goals**: Cold active view <=5 s excluding external wait; 10,000 instruments
with >=252 observations each, 19/20 warm views of <=100 stocks <=1 s; 500-observation
incremental batch readable <=2 s after validation; zero duplicate calls for valid
A-to-B-to-A/restart coverage and one acquisition for concurrent identical misses.

**Constraints**: Single approved observation provider; no hidden financial/research
loads; source-specific reviewed retention; no ticker-only ownership; no mixed structure
revisions; no observation-source calls in offline mode; failed acquisitions are not
successful cache entries. Benchmarks must instrument reads/reparses and calls, not
merely measure an empty or precomputed result.

**Scale/Scope**: One service endpoint per app deployment and one local shared cache
root per deployment; multiple sessions/processes may share that root. Initial reviewed
universe and supported provider geography unchanged. No distributed locks or new markets.

## Constitution Check

Pre-research evaluation: **PASS**. The user explicitly requires an independent service,
durable reuse, fast subset reads, and incremental writes; these are present requirements,
not speculative optimization.

| Gate | Design evidence | Post-design |
|---|---|---|
| I. Keep it simple | Three ownership-aligned distributions; small read-only HTTP surface; existing catalog validation and Parquet stack | PASS |
| II. Lean delivery | Deliver in independently demonstrable slices; no service admin UI, new collectors, or universe prefill | PASS |
| III. YAGNI | No broker, Redis, distributed cache, taxonomy query framework, or generalized ingestion platform | PASS |
| IV. Avoid waste | Conditional revision checks, changed-object reuse, indexed series paths, gap-only fetch and touched-month updates | PASS |
| V. Separation | Service owns reviewed structure; app owns observations; UI owns session-local selection | PASS |
| VI. Low coupling | App imports shared contracts, not server/tools; neither service nor shared data imports UI/providers | PASS |
| Existing app constraints | All four current tabs under 004/015, one selected provider, permission/issuer guards, explicit loading and `st.cache_data` preserved; 015's tracked tab exception is not extended by this work | PASS within existing exception |
| Observable failures | Typed service/acquisition states; no success-shaped stale fallback; injected clocks and faults | PASS |
| Compatibility | Versioned delivery and cache formats, v1/v2 payload validation, migration gates and import aliases | PASS |

No additional constitution exception or amendment is introduced. The existing fourth-tab
exception is owned by 015 and [issue #2](https://github.com/cempting/stocks-speckit/issues/2),
with its original pre-merge expiry/remediation gate unchanged. File-only catalog authority is
preserved inside the service; replica/observation files are not new catalog authorities.
Post-design review covers the contracts and data model below.
Refinement recheck: **PASS**. Shared/exclusive locks use the already selected POSIX
primitive; exact grammar and terminal gap reuse reduce ambiguity/waste. Permission
guards enforce the existing rights/migration obligations without becoming approval
authorities. All decisions have controlled validation scenarios and no new collectors.

## Project Structure

### Documentation (this feature)

```text
specs/013-market-structure-service/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── checklists/requirements.md
└── contracts/
    ├── market-structure.openapi.json
    ├── observation-policies.schema.json
    ├── snapshot-format.md
    └── observation-cache.md
```

The refreshed [tasks.md](tasks.md) follows the approved refinements and records
implementation progress.

### Source Code (planned ownership)

```text
pyproject.toml                       # root market-leadership distribution/workspace
uv.lock
packages/market-data/
├── pyproject.toml
└── src/market_data/                 # move current namespace; preserve import identity
    ├── domain/market_structure.py   # delivery/source/index/policy DTOs and invariants
    ├── catalog.py                  # existing v1/v2 reader/validator
    ├── company_evidence.py
    ├── structure.py                # shared bundle validation, not HTTP/server logic
    └── schemas/                    # existing catalog schemas + delivery/registry schemas
services/market-structure/
├── pyproject.toml
└── src/
    ├── market_structure/
    │   ├── app.py                  # Starlette routes/readiness
    │   ├── store.py                # published object allowlist and snapshot reader
    │   └── cli.py                  # serve and local reviewed snapshot publication
    └── market_data_tools/          # move existing offline tools; legacy stays opt-in
src/market_leadership/
├── config.py
├── bootstrap.py                    # inject one pinned structure/acquisition context
├── app.py
├── observation_admin.py            # explicit retention prune/status, no remote fetch
├── application/
│   ├── ports.py                    # structure/identity/observation request boundaries
│   ├── load_market_structure.py
│   ├── request_market_data.py      # coverage planning + gated provider calls
│   └── load_stock_history.py       # preserve reviewed continuity
├── infrastructure/
│   ├── market_structure_client.py  # HTTPX; conditional bounded downloads
│   ├── structure_replica.py
│   ├── observation_store.py
│   └── yfinance_provider.py        # raw adapter; explicit index-volume handling
└── ui/
    ├── cache.py                    # st.cache_data includes identity/generation context
    └── workflows/                  # Discovery, Deep-Dive, Yahoo preview and Find a stock
tests/
├── contract/                       # HTTP, payload, imports, cache semantics
├── integration/                    # delivery/bootstrap/reuse/recovery/benchmarks
├── app/                            # coherent views, offline gates, stable navigation
└── fixtures/market_structure/      # synthetic authoring data and recording harness only
```

**Structure Decision**: Move existing shared/tools namespaces rather than maintain two
copies. Root app depends on `market-data`; its optional `maintenance` extra preserves
explicit old CLI delegates. Service distribution owns `market-structure`, `market-catalog`,
`market-company-evidence`, and `market-universe-legacy` entry points. Legacy CLI compatibility
without the extra fails with actionable installation guidance, not an unexplained import.
Update packaging/test source-root references and Pyright include paths together.

## Delivery Slices and Integration

1. **Independent structure delivery (US1)**: Workspace/wheel boundary tests first;
   exact-byte bundle validation/publication; read-only routes, ETags, schemas and
   service import isolation. Serve catalog v1/v2 and independently reviewed registries.
2. **Validated consumer and demand bootstrap (US2)**: Replica staging and pinned
   `StructureReadContext`; service configuration; initial blocked/offline states;
   app automatic empty-store creation with recording-provider tests.
3. **Reusable durable coverage (US3)**: Stable target resolution, direct series lookup,
   interval planning, monthly partition publication, locks and attempt outcomes.
   Run A-to-B-to-A, restart, gaps, corrections and exact concurrency assertions.
4. **Revision-safe reorganization (US4)**: Preserve 012 stock/issuer continuity and
   deduplicated memberships; invalidate only derived context on membership changes.
   Publisher requires bindings explicitly valid for the candidate catalog revision;
   the app never silently rewrites reviewed association records.
5. **Offline and recovery completion (US5)**: Permission-gated retained reads across
   all price/financial/research entry points; rejected-candidate and outage recovery.
   Run final whole-suite, package-isolation and exact performance gates.

All slices are test-first. Offline restrictions are introduced with the consumer slice,
not deferred until a partially integrated app could acquire during an outage.
Introduce the exact policy grammar and publisher guard in US1, replica guards and shared
read locks in US2, unavailable-gap retries and reader/pruner concurrency in US3, and
complete rollback/reapproval output fences in US4/US5. Do not defer core guards to polish.

The refreshed backlog places exact grammar/shared publisher guards in T013-T030,
replica guards and initial read locks in T031-T049, unavailable-gap reuse and safe
pruning in T050-T066, final revision/outage fences in T067-T086, and guard-preserving
maintenance/operations in T087-T092. These are execution gates, not completion claims.

### Every production entry point must be wired

- Replace local-authority reads in `app.py`, Discovery, Industry Deep-Dive,
  Yahoo Classification Preview and Find a stock with
  the same injected read context. A replica's local catalog path is an implementation
  detail of validation, not a configurable alternate production authority.
- Preserve all four tabs and separate lookup state under 015; apply 012's exact
  identity/listing rules to lookup before any history or evidence action. Preview
  source checks must use the same service-registry permissions and remain explicit;
  preview output never becomes reviewed membership or another catalog authority.
- Resolve stock/ETF targets from reviewed listing identities and true index targets
  from the index registry before provider dispatch. Ambiguous symbols require IDs.
- Refactor `RequestMarketData`, `build_request_provider`, member/selected-listing history
  caches, Discovery benchmark/representation acquisition, and daily snapshot CLI paths
  together. Do not leave a symbol-only production route around the identity/mode gate.
- Replace bootstrap reads of mutable local source assessments/bindings with the pinned
  service registry. Keep `CompanyEvidenceFiles` for permitted fetched observations,
  financial snapshots and stored research claims, not a second review authority.
- Evaluate online/offline mode and current permission before `st.cache_data` reuse,
  before external acquisition, and before publication. Cache keys include identity,
  observation generations, structure context for derived output, and permission
  fingerprints; never credentials or user selections.
- Preserve `prepare_listing_history_window` and evidence revalidation. Observation
  continuity keys exclude membership/catalog revision but never bypass binding validity.

## Migration and Operational Boundaries

Implementation must ship explicit candidate validation, inventory/dry-run reports,
backup/rollback instructions, expected-current activation, and no production cutover
as a side effect of install/startup. Details are in [quickstart.md](quickstart.md).

Existing request-hash caches are not silently relabeled as identity-safe coverage.
Offer an explicit importer that verifies request metadata, source permissions, listing
and issuer continuity for every interval. Ambiguous/unverifiable entries remain
quarantined in the old cache with reasoned reports. Accepted data retains original
retrieval times; migration does not renew freshness or rights. A clean separate cache
root is the default until this review is completed.

013 does not complete unfinished 010 governed-review migration or 012 peer/evidence
implementation. Their invariants remain regression requirements, not completed tasks.

## Verification and Requirement Coverage

| Requirements | Design / evidence to add |
|---|---|
| FR-001, FR-004 | Independent wheels/venvs, import blockers, no shared service paths |
| FR-002--003, FR-005--007 | Snapshot/OpenAPI contracts; v1/v2, registries, versions, checksums, news permissions |
| FR-008--009 | Recording provider, empty store, active-view-only loads and partial failures |
| FR-010--013 | Stable target keys; overlap/basis handling; reclassification and ticker-reuse tests |
| FR-014--016 | Clock-boundary/retention tests; explicit refresh; process locks, failure and crash tests |
| FR-017 | SC-005/006 benchmarks plus assertions of selected series/partitions, not global scans |
| FR-018--019 | Offline/blocked AppTests and acquisition guards, including cached financial/research paths |
| FR-020--022 | Existing 010/011/012, navigation/score regressions; migration and end-to-end harness |

Run the smallest story selectors while building, then the full non-live suite and the
exact SC workload. Tests must inspect rendered output, identities, row counts, gaps,
call accounting and timestamps as well as elapsed time. Existing catalog-only 10,000-row
timings do not establish the 2.52-million-observation performance target.

## Complexity Tracking

No unresolved gate violations. The extra deployment and distributions implement the
confirmed service boundary; partitioning/locks implement explicit incremental/read/
concurrency requirements using the existing filesystem/Parquet stack. No distributed
coordination, new database, or constitution exemption is proposed.
