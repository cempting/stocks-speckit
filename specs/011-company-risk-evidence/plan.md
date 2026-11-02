# Implementation Plan: Company Risk Evidence Scoreboard

**Branch**: `main` (unchanged) | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: `specs/011-company-risk-evidence/spec.md`. Setup returned
`011-company-risk-evidence` as its resolved feature context; `git branch --show-current`
returned `main`. No branch was created or switched.

## Summary

Add explicit company-evidence loading to Discovery stock detail. Show cash-flow gaps and
cash-generation concerns before peer scores, then a cash overview, the existing eight-slot
fundamental matrix, and cited business/competitive/order research. Reuse yfinance acquisition
and caching; preserve peer-score formulas and existing point-in-time insufficiency safeguards.

Separately approved SEC/issuer disclosures supply research, not another scored financial feed.
Use bounded HTTP and deterministic structured extraction, with reviewed factual claims where
narrative normalization requires interpretation. Persist evidence separately from catalogs.
No LLM, general scraper, Finviz/TradingView integration, or Wikipedia collector is planned.

Planning changes no application code, live datasets, source approvals, production settings,
catalog activation, or package versions.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`, matching the existing environment.

**Primary Dependencies**: Existing constrained Streamlit, yfinance, pandas and jsonschema;
standard-library HTTP, HTML parsing, JSON, hashing and filesystem facilities. No new dependency.

**Storage**: Existing `st.cache_data`; versioned JSON assessments/bindings and immutable normalized
snapshots under `.data/company-evidence`. No new database. Credentials/contact headers and
private selections never enter cache results or persisted evidence.

**Testing**: Existing pytest, Streamlit AppTest, Ruff and strict Pyright; injected ticker,
HTTP transport, UTC clock and temporary store with synthetic offline disclosures.

**Target Platform**: Existing local/hosted Streamlit app. Historical evidence requires persistent
storage; ephemeral hosts must disclose history limitations or configure a persistent directory.

**Project Type**: Python/Streamlit application with narrow file-only evidence administration CLI.

**Performance Goals**: Loaded redisplay <=1 second and zero extra research requests (SC-007);
four of five test users identify cash-flow status/warning within ten seconds (SC-002).
Record hardware, versions, sample sizes, elapsed measurements and request counts.

**Constraints**: One scored source, explicit scoped loading/refresh, no unsupported historical
Yahoo requests or fabricated vintages, actionable failures, source-use gates, no catalog writes
or private financial-data transmission.

**Scale/Scope**: One open company, plus existing complete-cohort financial loading for scores.
Research never accompanies cohort scoring or full-universe rendering. Discovery selects at
most the latest eligible annual and quarterly disclosures.

## Constitution Check

*Pre-research and post-design gates; these do not grant source permission or claim implementation.*

| Gate | Pre-research | Post-design |
|------|--------------|-------------|
| I. Keep It Simple | PASS: extend existing detail, reader and matrix. | PASS: cohesive use case, bounded reader and file store; no service framework. |
| II. Lean Delivery | PASS: company-risk scope only. | PASS: warnings/financial value before research; no catalog-governance cleanup. |
| III. YAGNI | PASS: no new root route or recommendations. | PASS: no source marketplace, scheduler, LLM, optional collector or portfolio engine. |
| IV. Avoid Waste | PASS: scoped loading and bundle reuse. | PASS: targeted caches/refresh; no qualitative cohort fetches. |
| V. Separation of Concerns | PASS: transport/domain/UI separated. | PASS: explicit reader/store inputs; domain stays Streamlit-free. |
| VI. Cohesion/Coupling | PASS: stable catalog identities. | PASS: evidence sidecar, no SQL/legacy-workflow dependency. |
| Python/Streamlit architecture | PASS: existing two tabs. | PASS: grading inside stock detail; retired workflow remains retired. |
| Single-source/permissions | PASS: yfinance alone scores. | PASS: research attribution separate; unknown/denied uses disabled. |
| Cache/freshness | PASS: existing financial TTL. | PASS: complete keys, explicit TTL/report age, uncached failures, scoped invalidation. |
| Private stable state | PASS: current selection namespaces. | PASS: mode changes invalidate only assessment; public caches contain no selections. |
| Requests/errors | PASS: explicit requests; no access bypass. | PASS: bounded transport, identity checks, partial/stale/error disclosures. |
| Dependencies/tests | PASS: no installation/live data needed. | PASS: existing packages, injected clocks/transport/store, test-first acceptance. |
| Versioning/migration | PASS: no catalog migration. | PASS: evidence formats v1, additive metadata/cache revision, compatibility tests. |

No exception is requested. Deployment still requires verified publisher access and applicable
collection/display/retention rights; design PASS is not legal or runtime approval.

## Project Structure

### Documentation (this feature)

```text
specs/011-company-risk-evidence/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
└── contracts/
    ├── company-risk-ui.md
    └── company-evidence-acquisition.md
```

`tasks.md` is created later by `/speckit-tasks`, not this command.

### Source Code (repository root)

```text
src/market_leadership/
├── config.py                           # additive root/contact settings
├── bootstrap.py                        # compose scoped acquisition
├── company_evidence_admin.py            # proposed file-only reviewer CLI
├── domain/
│   ├── fundamentals.py                 # preserve metrics; additive metadata
│   └── company_evidence.py             # proposed models/validation/warnings
├── application/
│   ├── score_industry.py               # financial reuse, never research
│   └── load_company_evidence.py         # proposed use case
├── infrastructure/
│   ├── yfinance_fundamentals.py         # reuse reader/profile acquisition
│   ├── company_disclosures.py           # proposed transport/extraction
│   └── company_evidence_files.py        # proposed store/review records
└── ui/
    ├── cache.py
    ├── components/
    │   ├── fundamental_matrix.py       # exact existing eight slots
    │   ├── stock_detail.py             # warning before peer scores
    │   └── company_risk.py              # proposed shared presentation
    └── workflows/
        ├── discovery_page.py           # actual root integration
        └── company_evidence.py          # proposed explicit controls/state
tests/
├── unit/domain/test_company_evidence.py  # proposed
├── integration/test_company_evidence.py  # proposed readers/store/cache/CLI
├── app/test_company_risk.py              # proposed root AppTests
└── fixtures/acceptance/company_evidence/ # proposed synthetic disclosures
```

**Structure Decision**: Extend the existing package. Proposed files do not exist yet. Do not
change root navigation or extend SQL-backed `universe_admin.py` for a separate evidence domain.

## Phase 0: Research

[research.md](./research.md) resolves transport, source roles, permissions, identity, dates,
freshness, cash definitions, extraction limitations, persistence and integration. Unknown rights
are disabled operational states, not assumed permission. Unverified provider depth/sign claims
are not hard-coded.

## Phase 1: Design and Contracts

See [data-model.md](./data-model.md), [UI contract](./contracts/company-risk-ui.md),
[acquisition contract](./contracts/company-evidence-acquisition.md) and
[quickstart.md](./quickstart.md).

### Integration decisions

1. Discovery supplies captured snapshot, stock/listing, settings and chart date to evidence
   controls. Revalidate catalog/identity before a request.
2. Stock detail renders the cash banner before its chart/peer row, then cash overview and
   reused fundamental matrix, followed by independently loaded research.
3. The root has no legacy grading actions; `validate_live_access()` rejects retired independent
   JSON memberships. Do not revive them. Reuse the matrix in the current detail instead.
4. Add optional immutable public profile/provenance/component metadata to the acquired bundle.
   Reuse its one ticker; do not fetch profile a second time merely for company evidence.
   Retain returned issuer discriminators and profile failure/absence separately. Verify the
   dated reviewed listing and independent issuer reference using corroborated regulator identity
   or verified issuer domain, not matching ticker/exchange alone (FR-009). Same-label successors
   with conflicting evidence are mismatches; missing/inconclusive profiles are unresolved.
   Domain-corroborated financial evidence remains valid with company ID/CIK null. Recheck this
   gate before attachment/persistence and on cache/cohort/archive reuse; no catalog mutation,
   fabricated IDs, second source, or implicit research authorization.
5. New evidence distinguishes trading and reporting currencies without conversion or identity
   inference. Preserve existing scored-metric currency requirements; no FX eligibility expansion.
6. The peer adapter intentionally lacks verified vintages. Enrichment cannot fabricate those
   dates or make presently insufficient peer scores available.
7. Richer acquisition uses a revised cache schema while preserving old request/bundle callers.
   Accepted unchanged inputs retain all eight calculations and the existing FCF-margin formula.
8. Current evidence uses an explicit current-date context/label, never an old chart date.
   Historical mode reads eligible captured snapshots only; keep the reader's historical guard.

### Delivery sequencing for later tasks

- Failing domain/provenance/identity/cash tests before models and warning logic.
- Failing acquisition/cache/store tests before reader metadata and persistence, including
  same-ticker/same-exchange successors, unresolved profiles and valid nullable-ID associations
  across acquisition, reuse and archive paths (T004/T010/T011).
- Wire the financial warning/overview/matrix into actual root detail and verify P1 value.
- Failing review/binding/disclosure/unsupported-structure tests before P2 research and reviewer CLI.
- Complete refresh/history, root regressions, documentation and exact performance/usability
  acceptance. Task generation must preserve these dependencies and test-first requirements.

### Versioning and compatibility

New evidence formats start at v1; catalogs do not migrate. Bundles lacking metadata remain
readable with explicit limitations, not research authorization or peer vintage eligibility.
Cache revisions prevent old data appearing as richer evidence. Package release synchronization
is deferred to implementation against the then-current baseline.

## Planning Validation

Both constitution checks pass without exceptions. Quickstart maps every FR/SC to design/validation.
No design clarification remains; source access/rights, target-host persistence, extraction
coverage and human usability measurements remain implementation/release gates.
Planning preserves application code, actual branch, catalogs and unrelated reference images.
