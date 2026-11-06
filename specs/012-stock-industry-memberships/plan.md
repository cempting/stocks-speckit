# Implementation Plan: Stock Identity and Industry Membership Revision

**Branch**: `main` (observed during refinement; no branch created/switched) | **Date**: 2026-11-01 | **Refined**: 2026-11-02 | **Spec**: [spec.md](spec.md)

**Input**: Clarified feature 012 specification, now including the approved
2026-11-02 refinements. Initial planning used an attachment-matching specification;
the read-only attachment and feature 011 remain untouched.

**Status**: Phase 0 research, Phase 1 design and [task generation](tasks.md) complete;
the three acceptance-boundary refinements below are integrated. Implementation,
migration and source approvals remain pending.

## Summary

Extend the existing file catalog, not its persistence architecture. Introduce release
v2 and typed instrument/membership/listing projections from one stock CSV per region.
Permit reviewed overlapping memberships and deeper single-parent industry trees.
Retained v1 data keeps its original operational validation and classification meaning.

Reuse MembershipId, reviewed listing gates, immutable publication, stable scoped
identities, existing charts, and unchanged calculation functions. Use the dedicated
Find a stock workflow owned by 015 and separate instrument selection from industry comparison.
Share eligible issuer-owned facts through the feature 011 acquisition boundary,
never by substituting an entire listing-bound financial bundle.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`, from [pyproject.toml](../../pyproject.toml).

**Primary Dependencies**: Existing Streamlit, pandas, NumPy, jsonschema, yfinance,
PyArrow, exchange-calendars. No new dependency or provider-selection changes.

**Storage**: Existing manifest-managed CSV/JSONL releases, captured hashes, writer
lock, staging, and atomic CURRENT publication. Company evidence remains in 011's
separate evidence store, never stock CSVs.

**Testing**: pytest, Streamlit AppTest, Ruff, strict Pyright; synthetic temporary
catalogs and injected clocks/providers, without live services in acceptance tests.

**Target Platform**: Existing macOS/Linux local/server Streamlit deployment.
Retain POSIX locking; no new Windows support.

**Project Type**: Single Python application with existing domain/application/
infrastructure/UI layers.

**Performance Goals**: Preserve the existing 10,000-instrument/500-node reference
test's cold <=5 s, warm <=1 s and no-warm-reparse bounds. Planning baseline:
one test passed, 1.49 s test-call duration and 2.13 s total pytest duration.
These are not separate cold/warm measurements. Extend the reference workload
with overlapping assertions and deeper branches; record phase timings and memory
on the same reference environment.

**Constraints**: Retain 64 MiB artifact and 1 MiB manifest/record limits, observable
failures, identity-aware cache hits, explicit financial/research loading, all current
root workflows under 004/015, and existing mandatory stock-table columns.

**Scale/Scope**: Existing US catalog and retained records; existing 10,000-instrument
benchmark plus membership/listing copies. No new regional coverage, configurable
depth cap, multiple-parent network, provider, or portfolio capability.

## Constitution Check

*Evaluated before research and again after design.*

| Gate | Before | Post-design evidence |
|---|---|---|
| Simplicity / lean delivery / YAGNI | Pass | Joined regional CSV retained; one migration-report role; no new database/framework |
| Avoid waste | Pass | Deduplicated instrument cohorts, selected-subtree traversal, issuer/price reuse |
| Separation / narrow contracts | Pass | Catalog, issuer attachment, price retrieval, calculations, and UI state stay distinct |
| Single source / permissions | Pass | Existing yfinance path; migration and lookup grant no listing or source permissions |
| Cache / session isolation | Pass | Integrity checks precede reuse; evidence and comparative keys are distinct; selections session-local |
| Test first / explicit errors | Pass | Each slice starts with failing unit/contract/integration/AppTest acceptance cases |
| Incompatible-change migration | Pass | Explicit v2, strict v1 data semantics, complete reconciliation and guarded restoration |

No exception is required. Full feature acceptance depends on the minimum 011
identity/acquisition/reuse integration below. Fixture stubs do not waive a missing
production issuer gate.

## Project Structure

### Documentation (this feature)

```text
specs/012-stock-industry-memberships/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  checklists/requirements.md
  contracts/
    catalog-v2.md
    membership-migration.md
    membership-migration.schema.json
    navigation-peer-context.md
  tasks.md                     # generated; all implementation tasks remain unchecked
```

### Source Code (repository root)

```text
packages/market-data/src/market_data/
  catalog.py
  domain/catalog.py
  domain/stock_selection.py
  domain/peer_scores.py                   # unchanged formulas/eligibility
  schemas/catalog-manifest-v2.schema.json
  schemas/membership-migration.schema.json # planned packaged resource
services/market-structure/src/market_data_tools/
  membership_migration.py                 # planned bounded converter/reconciler
  catalog_admin.py
src/market_leadership/
  application/score_industry.py
  application/industry_representations.py
  infrastructure/catalog_files.py         # compatibility alias, not implementation owner
  infrastructure/stock_membership.py
  ui/cache.py
  ui/navigation.py
  ui/workflows/discovery_page.py
  ui/workflows/industry_deep_dive.py
  ui/workflows/stock_lookup.py
tests/
  unit/
  contract/
  integration/
  app/
```

**Structure Decision**: Extend existing layers and stock-detail components.
The tools-owned migration module isolates preparation from shared catalog reading/publication.
Reuse the 011 acquisition/store boundary and 015 placement; no new provider, evidence
store, generic graph engine, or parallel scoring service.

On 013 adoption, the current four root workflows consume one pinned validated service
context, including retained-stock lookup. This reconciliation does not complete US3/US4,
change identity/listing rules, or relax the tracked fourth-tab exception.

## Phase 0 - Research

[research.md](research.md) resolves format dispatch, joined-file ownership, dated
forest validation, descendant queries, cache/selection separation, 011 prerequisites,
immutable migration reports, historical governance, restoration and baseline validation.
There are no unresolved technical clarification markers.

## Phase 1 - Design and Contracts

- [Data model](data-model.md): ownership, fields, immutable projections, periods and states.
- [Catalog v2](contracts/catalog-v2.md): exact format/header boundary and shared queries.
- [Migration](contracts/membership-migration.md) and
  [report schema](contracts/membership-migration.schema.json): source accounting,
  compatible approval carry-forward, guarded adoption and cross-version restoration.
- [Navigation/peers](contracts/navigation-peer-context.md): retained lookup, membership
  paths, independent selection, company/listing keys and exact comparative contexts.
- [Quickstart](quickstart.md): runnable current baseline and prospective end-to-end checks.

## Delivery Order and Acceptance Coverage

Add failing tests first in each slice; concrete IDs are in [tasks.md](tasks.md).

| Slice | Required outcomes | Coverage |
|---|---|---|
| 1. Versioned projections | Strict v1 data, explicit v2, nullable identity, independent instrument/listing inventory | FR-001, FR-003-FR-005, FR-007; SC-001 |
| 2. Membership / dated forest | Overlap, temporal parents, exact all-depth sets, deduplicated instruments | FR-006, FR-008-FR-012; SC-002-SC-004, SC-008 |
| 3. Migration / lifecycle | Complete reconciliation, compatible approvals, immutable history, rejected adoption, restoration | FR-018-FR-022; SC-006, SC-008 |
| 4. Navigation / comparisons | Unassigned lookup, all paths, valid selection retention, separate industry results | FR-013-FR-016, FR-023-FR-024; SC-005, SC-007 |
| 5. Issuer attachment / reuse | Reviewed per-consumer gate, shared company facts, no enrichment reclassification | FR-002, FR-015-FR-017; SC-001, SC-009 |
| 6. End-to-end / performance | All stories, unchanged layout/formulas/providers, exact sets and request counts | FR-001-FR-024; SC-001-SC-009 |

### Feature 011 dependency reconciliation

011 remains planned, not completed. Core catalog/navigation development may proceed
first, but full 012 acceptance requires the production issuer gate and eligible
fact-reuse path. Reuse 011 T006-T013 and their fixture/foundation prerequisites;
T028 with T022/T024/T025; and reviewer binding/approval commands T047 with T044/T046.
Their current dependencies include broader stories: task generation must explicitly
reconcile and schedule the narrow prerequisites, not silently complete them or require
all qualitative collectors.

012 adds an issuer-owned statement-fact projection with distinct per-listing consumer
attachments. This explicitly reconciles company ownership with 011's prohibition on
whole cross-listing financial-bundle substitution. Preserve dated binding, profile
corroboration, permissions, reporting basis and cache-hit gates.
Absent those gates, affected production company evidence is unavailable: no
symbol-only fallback, membership-as-issuer proof, or full-acceptance claim.

### Acceptance-boundary refinements (2026-11-02)

- Account for SC-009 per unchanged, still-valid issuer/evidence request. Test
  overlapping but different A -> B -> A cohorts with per-request counters, zero
  repeats, explicit-only new peer loads and no eager whole-universe prefetch.
- Include CompanyResearchClaim and research-scope envelopes in the shared 011
  types/store/application slice. Test positive stored business-model/moat reuse
  across independently verified share classes, original provenance, separate
  research permissions, denial/revocation/expiry and historical cutoff. No new
  collectors or automatic financial-to-research authorization.
- Bound history by the requested range and reviewed listing/issuer continuity,
  independently of membership. Test mixed predecessor/successor response dates,
  inclusive boundaries and unverifiable gaps before charting/calculation and on
  cache reuse. Use existing dated listing/source references, not a new financial
  acquisition requirement or catalog identity inference.

## Complexity Tracking

No violations. V2 and an immutable report role are necessary because v1 data forbids
overlap, deeper parents and unassigned stock rows. Retain legacy archives unchanged.
For restoration, add only an explicitly versioned nonoperational report-history role
to the new reader's v1 metadata support; v1 data validation stays strict. An old
binary unable to read that history extension must fail explicitly.

## Planning Validation

- Existing catalog performance baseline: 1 passed; phase bounds are retained,
  not claimed as measurements of future v2 behavior.
- Seven design Markdown artifacts: relative links resolve, code fences balance,
  and no unresolved clarification markers remain.
- Migration schema passes Draft 2020-12 schema validation. Four valid summary/record
  variants and three invalid approval/unknown-field variants were checked.
  Complete source accounting and target/source approval applicability remain
  semantic implementation tests, not JSON Schema guarantees.
- Initial planning prerequisite resolution found research, data model, contracts
  and quickstart; task generation subsequently added tasks.md with 60 unchecked tasks.
- At initial planning, the repository spec matched its read-only attachment checksum.
  The approved 2026-11-02 refinements subsequently changed only feature documentation;
  no runtime code, company-evidence artifacts, catalog data or configuration changed.
- No extension hooks file was present before or after planning. No branch or
  commit was created by this command.
