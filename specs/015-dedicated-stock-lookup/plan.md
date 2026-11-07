# Implementation Plan: Dedicated Stock Lookup

**Branch**: `015-dedicated-stock-lookup` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/015-dedicated-stock-lookup/spec.md`

## Summary

Move the existing retained-stock lookup and its detail flow out of Discovery into a dedicated
Find a stock tab. Preserve exact identity and active-listing selection, explicit history and
evidence loads, and catalog-context validation. Reuse the catalog snapshot already loaded by
the app; do not broaden lookup scope or add data requests.

The implemented root has four tabs: Discovery, Industry Deep-Dive, Yahoo Classification
Preview and Find a stock. Discovery no longer renders stock lookup.
Constitution 4.1.0 permits this approved native-tab layout without a tab-count exception.

## Technical Context

### Entity Button and Column Contract

Reuse `ui/components/progressive_tape.py` for native buttons with stable keys/callbacks,
literal escaped Markdown and scoped CSS: ticker 1.5rem above name 0.75rem (2:1).
Missing/unavailable/basket-only sector/industry evidence shows `No ticker`, never an ID.
Stock names wrap without a fixed cutoff; compact 84px sector/industry labels require complete
touch/keyboard details under [016](../016-add-daily-performance/contracts/daily-performance-ui.md).
Do not fetch tickers, change catalog contracts or weaken placeholder identity.

Hide separate sector Ticker/industry ETF columns, retaining their backing evidence.
Entity tapes have nine fields: two charts, button and six returns. 016 owns display captions,
daily arithmetic and responsive header/rows/details; its task ledger tracks pending acceptance.
Preserve chart geometry/palettes, controls, return arithmetic and the five-column stock table.

Use test-first renderer/workflow regressions and real light/dark browser measurements for
typography, full-text access, focus and selection. [Tasks](tasks.md) retain T001-T025 states;
[quickstart](quickstart.md) records historical lookup/button/column evidence, not current 016 acceptance.

**Language/Version**: Python 3.12

**Primary Dependencies**: Existing Streamlit application (`>=1.50,<2`, lockfile 1.66.1),
`market-data` catalog domain, `yfinance` history path, pytest and Streamlit AppTest.
Native Markdown button labels and existing `st.html` scoped styles need no new dependency.

**Storage**: No new persisted data. Lookup selections and request state remain session-local.

**Testing**: Targeted pytest AppTest coverage for stock lookup, stock detail, Discovery, and the
root tab entry points; shared renderer tests cover literal names, missing/basket ETF evidence,
and stable identifiers. Browser checks measure actual typography and wrapping, because AppTest
cannot prove computed CSS. Ruff and strict Pyright remain the project quality gates.

**Target Platform**: Existing local Streamlit application.

**Project Type**: Python Streamlit web application with shared market-data domain packages.

**Performance Goals**: Reuse the active catalog snapshot already loaded for the root app. Search
and tab rendering MUST NOT trigger provider history or issuer-evidence requests. History and
evidence requests remain explicit user actions. Button rendering uses only existing frame
values and adds zero catalog/provider requests.

**Constraints**:

- The new tab MUST preserve the existing retained-identity lookup rules, including exact identity
  and active verified listing selection.
- Stocks without active industry membership remain searchable; lookup MUST NOT infer or assign
  membership.
- Changes to region, date, or catalog revision MUST invalidate or revalidate dependent lookup
  state.
- Discovery's unrelated controls and workflows, the Industry Deep-Dive tab, and the existing
  Yahoo Classification Preview tab MUST remain available.

**Scale/Scope**: Existing retained catalog identities, the current region/date lookup scope, and
the existing stock-detail/history behavior, plus the three-view entity-button presentation.
No new catalog, provider, market, search domain, or persisted schema.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or constraint | Gate | Plan evidence |
|---|---|---|
| I. Keep It Simple | PASS | Reuse current lookup/detail helpers and the shared native-button tape renderer; add no service or dependency. |
| II. Lean Delivery | PASS | Limit scope to lookup relocation and the explicitly approved three-view button presentation; no unrelated redesign. |
| III. YAGNI | PASS | No new lookup source, query mode, identity model, or market-data capability is introduced. |
| IV. Avoid Waste | PASS | Root catalog loading remains shared; no hidden or duplicate provider requests are added. |
| V. Separation of Concerns | PASS | Discovery exploration and stock lookup render in separate workflows while retaining existing domain boundaries. |
| VI. High Cohesion, Low Coupling | PASS | Lookup UI owns its selection and detail flow; it continues to use the stable catalog and stock-detail contracts. |
| Python/Streamlit native tabs | PASS | Constitution 4.0.0 permits feature-defined tab counts. FR-001 specifies the approved four-tab layout; no tab-count exception is required. |
| Existing source, session-state, and explicit-load constraints | PASS | Reuse the selected catalog snapshot; keep selection state session-local and namespaced; retain explicit history/evidence actions and visible failures. |
| Test-first workflow | PASS | Preserve completed lookup/button regression tasks; any follow-up change first adds a failing focused test. Browser validation measures actual size ratio and wrapping. |

The pre-research constitution check passes under 4.0.0. The navigation amendment does not
authorize changes to existing data-source, identity, listing-verification, loading, or scoring
rules. The original tab-count tracking issue [#2](https://github.com/cempting/stocks-speckit/issues/2)
was closed on 2026-11-06; it is no longer an outstanding merge prerequisite.

## Project Structure

### Documentation (this feature)

```text
specs/015-dedicated-stock-lookup/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── stock-lookup-ui.md
└── tasks.md              # Created by /speckit-tasks, not by this plan
```

### Source Code (repository root)

```text
src/market_leadership/
├── app.py                                      # Four tabs, one shared catalog load
└── ui/
    ├── navigation.py                           # Namespaced selection invalidation
    ├── components/
    │   ├── progressive_tape.py                 # Shared escaped labels/scoped 2:1 styles
    │   ├── company_evidence.py                 # Explicit evidence controls
    │   └── stock_detail.py                     # Workflow-specific detail keys
    └── workflows/
        ├── discovery_page.py                   # Entity tapes without inline lookup
        └── stock_lookup.py                     # Dedicated lookup/detail workflow

tests/
├── unit/ui/test_progressive_tape.py             # Labels, missing tickers, stable selection
└── app/
    ├── test_sector_stock_explorer.py           # Three views and hierarchy navigation
    ├── test_stock_lookup.py                    # Identity/listing and explicit loads
    ├── test_stock_detail.py                    # Detail and stock-tape behavior
    ├── test_discovery.py                       # Discovery without inline lookup
    ├── test_progressive_tabs.py                # Four tabs and shared catalog loading
    └── test_cloud_entrypoint.py                # Application entry point
```

**Structure Decision**: Keep the new page in the existing UI workflow package and register it
from the current root app. Extract and reuse the current lookup/detail behavior rather than
duplicating it. Keep the formatter and scoped CSS in `progressive_tape.py`, where all three
button surfaces converge; no new component module or frontend framework is needed. The catalog
remains loaded at the root and shared with all tabs.

## Phase 0: Research

Pre-implementation research confirmed lookup was rendered inside `discovery_page.py`, read
retained identities from the already loaded `CatalogSnapshot`, and explicitly gated history and
company-evidence requests. The root app uses `st.tabs`; the user chose a fourth tab
rather than a standalone route. Existing AppTest coverage exercises exact identity/listing
selection and no-prefetch behavior.

The current implementation now places lookup in `stock_lookup.py`; all three entity-button
surfaces share `_render_visual_tape` in `progressive_tape.py`. Public Streamlit documentation
and source research supports reusing native Markdown labels and key-scoped styling rather
than introducing a custom component. Internal Markdown DOM selectors remain version-sensitive:
repeat browser measurements when upgrading Streamlit. Sources and rejected alternatives are
recorded in `research.md`. No unresolved technical unknowns or new technology choices remain.

## Phase 1: Design and Contracts

- `data-model.md` documents the existing instrument, listing, lookup context, and session-local
  lookup states plus the existing entity-tape presentation projection; no persistent entity is
  added.
- `contracts/stock-lookup-ui.md` records the tab boundary, lookup interactions, exact listing
  verification, explicit loading, visible failures, and the three-view button contract.
- `quickstart.md` describes deterministic AppTest scenarios and a local visual check of the four
  root tabs, measured browser font-size/wrapping checks, and previously recorded evidence.
- Existing completed tasks in `tasks.md` are preserved. Future task generation must reconcile
  with their IDs and evidence rather than resetting completed work.

The post-design constitution check passes under 4.0.0 with no tab-count exception or other
identified architecture violation. The existing data model and UI contracts remain unchanged
in behavior. This C2 reconciliation adds no implementation, schema migration, provider request,
or runtime/browser validation result.

## Complexity Tracking

None. Constitution 4.0.0 supersedes the original fixed three-step tab constraint; the approved
four-tab layout requires no exception. Issue [#2](https://github.com/cempting/stocks-speckit/issues/2)
is closed, and the feature documentation is reconciled on 2026-11-06. Preserve T015 as the
historical issue-creation record; T026 records this separate reconciliation.
