# Implementation Plan: Local ETF Mapping Discovery

> **2026-10-31 alignment:** Additive schema 3, default source configuration, SQL transactions,
> and database command flags below describe implemented pre-cutover behavior.
> [Feature 010](../010-manifest-csv-catalogs/spec.md) requires manifest-registered optional
> research sources and file-only immutable evidence/review/provenance history. Preserve safe AST
> extraction, identities, currentness, explicit decisions, and approval prerequisites.
> Export/reconcile all six audit relations; completed tasks/tests do not prove file-only cutover.

**Branch**: `main` (unchanged; feature key `009-local-etf-discovery`) |
**Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-local-etf-discovery/spec.md`.
The setup script reports the feature key as BRANCH; it does not create a Git branch.

## Summary

Collect literal ETF declarations from the specified local projects into an auditable candidate
inventory. Use a bounded standard-library AST reader, deterministic candidate/evidence identities,
and additive SQLite audit storage. Extend the existing reviewer CLI for collection, comparison,
and explicit suitability decisions; reuse ETF approval with an optional transactional provenance
link. No local candidate becomes runtime momentum evidence automatically.

The three available catalogs supply direct literal mappings; the missing stockviewer root is
an explicit recoverable inspection issue. Classification aliases, source agreement, sector
proxies, and source code imports are never treated as reviewed mapping authority.

## Technical Context

**Language/Version**: Python 3.12, matching the existing manifest.

**Primary Dependencies**: Standard-library ast, tokenize, hashlib, json, pathlib, sqlite3;
existing application types and argparse CLI. No new dependency or manifest changes.

**Storage**: Existing regional SQLite database, additive schema 3. Six evidence/audit tables;
candidate inventories, alias bindings, and currentness are derived projections.

**Testing**: Existing pytest, Ruff, strict Pyright. Synthetic local catalog fixtures and
temporary databases; no user-owned directory or online-provider dependence.

**Target Platform**: Local administration CLI on the application's supported Python environment.

**Project Type**: Existing Python/Streamlit application with reviewer administration CLI.

**Performance Goals**: Read each selected source file once per explicit collection; zero network
requests, recursive project scans, or automatic widget-triggered collections. Repeated unchanged
collection adds zero duplicate candidate/evidence or review items.

**Constraints**: Read-only source access; exact source scope; all duplicate occurrences retained;
unknown classifications/instrument types remain unapproved; immutable approval provenance;
partial input cannot masquerade as current complete evidence.

**Scale/Scope**: Four named source roots, initially three known literal catalog files and the
active reviewed industry/sub-industry hierarchy. Explicit extra catalog descriptors are allowed
inside those roots. No general parser/plugin framework, portfolio system, new UI, or provider.

## Constitution Check

Gates evaluated before research and re-evaluated after design:

| Gate | Pre-research | Post-design evidence |
|---|---|---|
| Keep It Simple / Lean Delivery | PASS | One static collector, one application workflow, existing CLI/database; no new service or UI |
| YAGNI | PASS | Verified literal catalog forms and required provenance relations; nested runtime interpretation rejected |
| Avoid Waste | PASS | Explicit bounded reads, deterministic grouping, zero market-data calls and no candidate cache |
| Separation of Concerns | PASS | AST/filesystem access in infrastructure; pure types/grouping in domain; orchestration in application |
| High Cohesion / Low Coupling | PASS | RegionDatabase owns SQLite operations and existing approval validation |
| Data governance / fail-closed evidence | PASS | Candidate review is separate from source approval; exact scope/listing/date checks and atomic provenance |
| Existing UI/session/cache constraints | PASS | No Discovery/scoring changes; existing universe revision untouched by research-only writes |
| Migration and deterministic validation | PASS | Schema 1/2-to-3 backup/upgrade; injected roots/clock and migration/approval rollback tests |

No unresolved planning questions or constitution exceptions remain. Decisions and rejected
alternatives are recorded in [research.md](./research.md).

## Project Structure

### Documentation (this feature)

```text
specs/009-local-etf-discovery/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── local-etf-review-cli.md
└── checklists/
    └── requirements.md
```

`tasks.md` is the next `/speckit-tasks` output and is not created by this command.

### Source Code (repository root)

Planned additions/extensions, not implemented by this planning command:

```text
src/market_leadership/
├── domain/local_etf_evidence.py              # new pure evidence/identity/review types
├── infrastructure/local_etf_sources.py       # new bounded static source reader
├── infrastructure/region_database.py         # schema 3, evidence accessors, approval link
├── application/discover_etf_candidates.py    # new collection/review orchestration
├── application/industry_representations.py  # reused approved hierarchy/worklist boundary
└── universe_admin.py                        # new review commands; optional approve-etf link
tests/
├── fixtures/local_etf_discovery/
├── unit/test_local_etf_evidence.py
├── unit/test_local_etf_sources.py
├── unit/test_universe_admin.py
├── integration/test_local_etf_discovery.py
├── integration/test_industry_representations.py
└── contract/test_local_etf_discovery.py
```

**Structure Decision**: Extend the current single-project boundaries. Do not add a repository
layer, second database, generic registry, independent alias module, or new research UI.
Existing `tests/unit/__init__.py` preserves test module namespacing.

## Phase 0 - Research Outcome

- Accepted source grammar and exclusions are bounded by verified catalog declarations.
- Candidate identity preserves original label/ticker/scope differences and duplicate provenance.
- Schema 3 retains immutable evidence, review history, and atomic approval links.
- Source change/removal/currentness distinguishes complete and partial observation.
- Local candidates cannot satisfy listing, source approval, or suitability gates automatically.

## Phase 1 - Design and Validation

See [data-model.md](./data-model.md) for audit entities and state transitions,
[CLI contract](./contracts/local-etf-review-cli.md) for literal grammar and command schemas,
and [quickstart.md](./quickstart.md) for future end-to-end validation.

Implementation sequence for subsequent task generation:

1. Write parser/identity/duplicate tests and implement bounded collection.
2. Add transactional schema 3 migration and immutable evidence persistence tests/accessors.
3. Add collection CLI and complete/partial/failed reports; preserve every selected occurrence.
4. Add hierarchy projections and explicit candidate/node decisions, including re-review for
   changed/removed/unobservable evidence and rejection without selection fallback.
5. Extend existing ETF approval with current accepted selection and atomic provenance checks.
6. Validate end-to-end flows, unchanged reruns, source recovery, rollback, old approval retention,
   zero market-data calls, exact hierarchy coverage, Ruff, and strict Pyright.

Migration: back up the regional database, then run existing `universe_admin init` after feature
implementation. Upgrade supported schema 1/2 through the existing migration chain to schema 3;
reject unsupported versions before writes. New DDL/version changes must commit atomically without
`executescript` prematurely committing a transaction. Preserve legacy hierarchy/listings/ETFs/
baskets and revisions; collection must never populate sources or listings. Older schema 2
application versions will not recognize schema 3.

## Complexity Tracking

No constitution violations or exceptions. The six audit tables model required immutable entities
and evidence relationships; candidates and reviewed label equivalences are computed rather than
separately persisted.
