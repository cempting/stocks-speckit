# Implementation Plan: US Industry and Theme ETF Discovery

**Branch**: `main` (working branch; setup feature key: `018-market-catalog-discovery`)
**Date**: 2026-11-12
**Spec**: [spec.md](spec.md)

**Input**: Feature 018 uses the user-provided US industry/theme CSVs as candidate sources for the
existing Discovery workflow. It also requires exact yFinance symbol support, unambiguous
multi-classification selection, and governed catalog publication.

## Summary

Use the existing manifest-managed catalog release model, specifically its implemented
`market-catalog-release-2` custom-classification support, instead of introducing a new catalog
format. Treat `docs/markets/US/` as authoring input only: it is structurally compatible and its
current cross-file IDs resolve, but generic source references and missing release companions mean
it is not approved or publishable as-is.

Add explicit active-classification selection to catalog-backed workflows, preserve the current
single-classification behavior, and present every approved ETF mapped to a category rather than
silently taking the first file row. Request the exact verified `ProviderSymbol` values through the
existing yFinance-only history path, reuse its cache, and expose per-symbol history failures.
Preserve the current app navigation and never infer stock membership or benchmark approval.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`.

**Primary Dependencies**: Existing Streamlit, `market-data`, pandas, jsonschema, and yfinance
dependencies. No dependency or provider additions.

**Storage**: Manifest-managed catalog releases and CSV/JSONL artifacts. The app reads
`MARKET_CATALOG_MANIFEST_PATH` or `.data/catalog/CURRENT.json`; the latter is absent in this
checkout. The `docs/markets/US/` files are not auto-discovered or read directly at runtime.

**Testing**: pytest, Streamlit AppTest, Ruff, strict Pyright, and an opt-in live yFinance check
guarded by `RUN_LIVE_MARKET_DATA=1`. Default tests use synthetic releases and injected providers.

**Target Platform**: Existing local macOS/Linux Streamlit application.

**Project Type**: Existing Python/Streamlit application with shared market-data packages and
catalog maintenance services.

**Performance Goals**: Keep one batched request for the distinct provider symbols required by the
visible Discovery context, use existing market-data caching, and preserve the current
approximately 550-calendar-day history window used for annual comparisons. Do not fetch hidden
classifications or the whole catalog on each widget rerun.

**Constraints**:

- Keep yFinance as the sole runtime market-history provider; use the approved listing's exact
  `ProviderSymbol`, not a guessed ticker transformation.
- Preserve existing release-v1 and release-v2 dispatch. No catalog-v3 schema is justified.
- A region may contain multiple simultaneously active classifications; do not resolve scope by
  row order or silently default to one.
- A category may have multiple approved ETF mappings; display all options with independent
  availability rather than selecting the first.
- Keep catalog source, domain calculations, remote history, UI state, and publication as separate
  responsibilities.
- Do not activate candidate data without valid source, approval, suitability, audit, stock, and
  benchmark artifacts. Never fabricate missing evidence.
- Do not infer stock membership from an ETF or its disclosed holdings.
- Preserve the four existing root tabs and all unrelated worktree changes.

**Scale/Scope**: Current candidate data contains 65 hierarchy rows, 86 unique ETF listings/provider
symbols, and 98 ETF mappings (47 sector, 28 industry, 23 sub-industry); the app must also retain
normal performance with any pre-existing catalog data.

## Constitution Check

*Evaluated before research and re-checked against the completed design.*

| Gate | Status | Evidence / constraint |
|---|---|---|
| I. Keep It Simple | PASS | Reuse release v2, existing provider/cache, and current UI; add no database, provider, or theme node type. |
| II. Lean Delivery | PASS | Limit changes to classification resolution, representation projections, Discovery, its scope-dependent Deep-Dive compatibility, and focused tests/docs. |
| III. YAGNI | PASS | No new catalog version, automated taxonomy inference, holdings ingestion, or speculative admin framework. |
| IV. Avoid Waste | PASS | Fetch distinct symbols for visible categories only; use existing cache and stable catalog fingerprints. |
| V. Separation of Concerns | PASS | Scope and mapping resolution remain in market-data/application boundaries; widgets render typed results; yFinance stays behind the existing provider. |
| VI. High Cohesion / Low Coupling | PASS | Add explicit multi-scope and representation-option projections; retain `scope_on` for unambiguous legacy callers. |
| Single-provider and cache constraints | PASS | yFinance remains sole provider; exact symbols, request context, cache freshness, and explicit failures are preserved. |
| Session state and UI architecture | PASS | Stable namespaced classification keys, dependent-selection clearing, no root-tab change. |
| Responsive UI quality gate | PASS | AppTest plus browser checks at 1440px and 390px are required; automated rendering alone is insufficient. |
| Versioning, evidence, and errors | PASS | Keep v1/v2 readers; do not activate unreviewed sources or silently substitute missing listings/history. |
| Provider-use gate | CONDITIONAL | Local research validation may proceed; public publication/hosting requires a review of Yahoo data terms and rights. |

No design exception is required. Catalog activation is a separate evidence prerequisite: this
checkout has no default `CURRENT.json`, and the new authoring folder lacks several release-required
artifacts and review evidence. Tests and UI work must not imply that these inputs are approved.

## Project Structure

### Documentation (this feature)

```text
specs/018-market-catalog-discovery/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── us-market-catalog-input.md
│   └── discovery-classification-ui.md
├── checklists/requirements.md
└── tasks.md                         # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
docs/markets/US/                      # Candidate authoring files; preserve as supplied
packages/market-data/src/market_data/
├── catalog.py                        # Existing v1/v2 reader and typed snapshot
└── domain/catalog.py                 # Scope, node, listing, and mapping domain types
src/market_leadership/
├── application/discover_sectors.py   # Visible category symbols and performance projections
├── application/industry_representations.py
├── infrastructure/yfinance_provider.py
└── ui/
    ├── cache.py
    └── workflows/
        ├── discovery_page.py
        └── industry_deep_dive.py     # Explicit classification selection when needed
services/market-structure/src/market_data_tools/
└── catalog_admin.py                  # Existing validation/publication tools; no new parallel importer
tests/
├── contract/test_catalog_v2.py
├── integration/test_discover_sectors.py
├── app/test_discovery.py
├── app/test_progressive_tabs.py
└── live/test_us_catalog_etf_retrieval.py  # Opt-in validation for published ETF symbols
```

**Structure Decision**: Extend existing catalog and application layers. Keep authoring CSVs
unchanged; validate/capture/publish through the established catalog lifecycle. Do not add a direct
filesystem scan or a second catalog-loading path.

## Phase 0 - Research

Research and decisions are recorded in [research.md](research.md). No unresolved technical
clarifications remain. Key decisions:

1. Use the already implemented release-v2 custom classification contract; do not create v3.
2. Add explicit scope enumeration/selection because `scope_on(region, date)` currently requires
   exactly one active classification.
3. Preserve all active ETF mappings per node because the current representation worklist chooses
   the first eligible mapping.
4. Keep yFinance batch retrieval and provider-symbol identity; add offline coverage and an
   opt-in, per-symbol live report rather than relying on unverified assumptions.
5. Keep activation blocked until the source evidence and all required release artifacts are
   available; do not manufacture approvals or benchmarks.

## Phase 1 - Design and Contracts

- [Data model](data-model.md) defines the release-scoped classification, node, ETF listing,
  mapping-option, history-availability, and session-selection projections. It reuses existing
  catalog records and adds no persistence store.
- [US catalog input contract](contracts/us-market-catalog-input.md) records accepted artifact
  roles, cross-file identity rules, missing required release material, and review/publication
  gates.
- [Discovery UI contract](contracts/discovery-classification-ui.md) specifies multi-scope
  selection, progressive hierarchy navigation, multiple ETF options, availability states,
  selection reset, and responsive acceptance.
- [Quickstart](quickstart.md) defines offline validation, browser checks, and opt-in live ETF
  retrieval checks.

## Execution Preconditions

Before any real release is activated, the reviewer must provide or identify valid source,
approval, suitability, audit, benchmark, and stock-artifact evidence for a complete release.
The current source files use `source-1` throughout and have blank `CandidateReviewId` values;
cross-file reference integrity is not approval. The repository's existing release data may be
considered only through its own manifest and evidence, not assumed to approve the new mappings.

The optional live check must report each active ETF listing's exact provider symbol, returned
history state, and useful date coverage. It is not part of offline CI. Unavailable symbols require
review and visible status; they must not be replaced with another provider or ticker.

## Complexity Tracking

No constitution violations or exceptions.
