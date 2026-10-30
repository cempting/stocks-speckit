# Implementation Plan: Fundamental Grading Layout

**Branch**: `main` | **Date**: 2026-10-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-fundamental-grading-layout/spec.md`,
plus the user's compact blocks, 60-pixel bar charts, cached yfinance bundle, and
approved expansion to the missing three-tab foundation and balance-sheet fetch.

**Setup identity**: `setup_plan.py` reported `BRANCH=002-fundamental-grading-layout`
as a feature-derived identifier. Actual Git branch remains `main`; no hook created
or switched a branch. Feature discovery uses `.specify/feature.json`.

## Summary

Replace the current routed Discovery/Industry Discovery entry experience with one
three-stage `st.tabs` app. Reuse existing discovery calculations and dated evidence,
add validated industry-member stock selection, and render each requested stock's
fundamental matrix with `st.columns(3)`. Each metric uses a small container with
Markdown label/value/commentary followed by `st.bar_chart(..., height=60)` when
four to eight comparable quarterly points exist.

One cached retrieval constructs `yf.Ticker(symbol)` and reads `.info`,
`.quarterly_financials`, `.quarterly_cashflow`, and the approved
`.quarterly_balance_sheet`. A pure transformation supplies all eight metric slots
from the same evidence bundle. Missing evidence stays missing; eight-quarter EPS
Consistency will commonly be unavailable with Yahoo's short quarterly history.

The expanded foundation does not silently implement the entire parent screener.
New adaptive consolidation, technical filters, ranking formulas, aggregate peer
grades, and unauthorized membership acquisition remain outside this plan.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`; local interpreter 3.12.15.

**Primary Dependencies**: Existing Streamlit `>=1.50,<2` (lock 1.66.1),
yfinance `>=0.2.66,<1` (lock 0.2.66), pandas `>=2.2,<3`, NumPy and Altair already
present. No new runtime dependency is required. User-approved quality-gate
remediation adds development-only `pandas-stubs`, `pyarrow-stubs`, and
`types-jsonschema` to check the existing integrations without weakening strict
typing. Narrow typed boundaries cover incomplete upstream annotations. Use APIs supported by the manifest floor,
not new tab `.open`/`on_change` APIs without raising the dependency floor.

**Storage**: `st.cache_data` for successful financial evidence and deterministic
transforms; session-local selection keys; existing snapshots for legacy evidence.
A small configured dated membership JSON catalog plus fixtures, not a new database.
No new persistent financial-history store or second runtime provider.

**Testing**: Existing pytest, `streamlit.testing.v1.AppTest`, Ruff, strict Pyright.
Injected ticker factories/clocks and fixture catalogs; no network in required tests.

**Target Platform**: Existing local/Community Cloud Streamlit app, desktop-first
three-column rendering with readable narrow-screen reflow.

**Project Type**: Single Python Streamlit application with existing domain,
application, infrastructure, and UI boundaries; no service or frontend framework.

**Performance Goals**: Fresh identical requests invoke the bundle fetch once;
no financial requests before explicit grading; fetch only the visible page of
selected stocks, five per page. Chart plots contain at most eight points, height
exactly 60; source request timeout/retry behavior remains visible, not hidden behind
an invented end-to-end latency promise.

**Constraints**: One selected live provider, yfinance, for this workflow. Cache TTL
3,600 seconds, maximum 256 financial bundles; cache keys include provider, symbol,
requested cutoff/window, quarterly frequency, and bundle schema version. No cached
errors, credentials, user selections, provider switching, padded histories, or
unverified live membership. Statement data is not point-in-time revision history.

**Scale/Scope**: US stock membership selection and eight-metric scorecards; three
tabs, five scorecards per page, four quarterly source components per stock. A single
Ticker object does not imply one HTTP request; yfinance may make multiple requests
internally. Synchronous bounded requests are adequate; no worker pool is needed.

## Constitution Check

*Initial gate evaluated before research; post-design gate evaluated after contracts.*

| Principle / constraint | Initial finding and resolution | Post-design |
|------------------------|--------------------------------|-------------|
| I. Deliberate design | Scope, missing foundation, and source limits identified; user approved expanding foundation and balance sheet | PASS: explicit data flow, formulas, failure paths, acceptance contracts |
| II. Cohesive units | Reuse current layers, add small financial and membership units | PASS: acquisition, calculation, and rendering independently testable |
| III. Tests as evidence | No implementation in this command | PASS for design: red-first unit, cache integration, and AppTest scenarios required before implementation |
| IV. Streamlit-first | Current `st.navigation` conflicts with v2.0.0 | PASS for target design: replace routed shell with three `st.tabs`, not a fourth route |
| V. Maintainability | Existing workflow top-level effects and `st.stop()` cannot be embedded unchanged | PASS: extract render functions, configure page once, use local returns |
| Single live source | Current settings permit multi-provider selections | PASS: new workflow admits only one yfinance live source or explicit offline fixtures; reject incompatible config, no silent fallback |
| Cache / freshness | Existing caches do not cover fundamental data | PASS: keyed TTL cache, targeted invalidation, no cached ambiguous fetch outcomes |
| Membership / rights | No verified live stock catalog or hosted display approval exists | PASS by fail-closed gate: fixture/local catalog flow; live requests/publication require reviewed rights and coverage |
| State / errors | Existing routed handoff is one-shot and page-oriented | PASS: namespaced stable state, dependent invalidation, visible structured component errors |

No constitutional exception is requested. Passing design review does not certify
live-provider licensing, an implemented three-tab app, or passing implementation tests.
Publication and live membership remain blocked until their explicit evidence gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/002-fundamental-grading-layout/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md              # concurrent artifact, reconciled by explicit user approval
├── checklists/requirements.md
└── contracts/
    ├── fundamental-data.md
    └── fundamental-ui.md
```

An existing concurrent `tasks.md` was discovered during final validation. The user
selected this plan as authoritative and requested reconciliation; its four
uncompleted IDs were retained and corrected to this scope. No implementation was
performed. `/speckit-tasks` may further refine the reconciled tasks if requested.

### Source Code (repository root)

```text
streamlit_app.py                         # retain cloud entrypoint
src/market_leadership/
├── app.py                               # replace routed shell with three tabs
├── bootstrap.py                         # compose existing helpers and new readers
├── config.py                            # optional membership catalog path; source guard
├── domain/
│   ├── models.py                        # reuse Company/Instrument/classification IDs
│   ├── fundamentals.py                  # new typed observations and pure calculations
│   └── stock_selection.py               # new dated membership/context validation
├── infrastructure/
│   ├── yfinance_provider.py             # leave daily-history contract intact
│   ├── yfinance_fundamentals.py          # new injected Ticker bundle reader
│   ├── stock_membership.py              # new bounded local catalog loader
│   └── provider_errors.py               # reuse sanitized request-error vocabulary
└── ui/
    ├── cache.py                         # extend with keyed financial cache helpers
    ├── navigation.py                    # retire runtime routing use; no new routes
    ├── components/fundamental_matrix.py # new compact metric/three-column renderer
    └── workflows/
        ├── discovery_page.py            # extract callable, remove routed handoff
        ├── industry_discovery.py        # embed existing discovery in first tab
        ├── industry_detail.py           # retain industry evidence rendering
        ├── industry_deep_dive.py        # new membership/stock selection stage
        └── fundamental_grading.py       # new explicit load/refresh/pagination stage
tests/
├── unit/                                # formulas, validation, commentary, state
├── integration/                         # fake Ticker, cache keys, errors, catalogs
├── app/                                 # real entrypoint, tabs, matrix, no eager fetch
└── fixtures/acceptance/                  # additive dated membership/fundamental fixtures
```

**Structure Decision**: Extend existing layers rather than introduce a provider
framework. Reuse strict dataclass validation patterns, stable instrument identities,
provider error vocabulary, and existing AppTest fixtures. Avoid modifying legacy
snapshot schemas or daily-history source-selection machinery for this UI feature.

## Phase 0 - Research Resolution

See [research.md](./research.md). Resolved decisions:

1. App shell and stock selection do not exist; build them here with approved scope.
2. Use all four yfinance components; ROCE requires actual balance-sheet evidence.
3. Treat statement-wide empty responses as ambiguous acquisition failures, not
   cacheable all-missing success, because installed yfinance swallows some errors.
4. Use only actual comparable quarterly points; four to eight bars are a display
   bound, not a promise that Yahoo supplies eight quarters.
5. Keep neutral commentary unless a financially defensible rule exists; do not
   infer premium pricing from an arbitrary gross-margin threshold.
6. Preserve legacy discovery meanings and data-source gates; no fabricated live
   catalog and no claim that legacy weekly ranking satisfies new parent ranking.

No unresolved design clarifications remain.

## Phase 1 - Design and Integration

### Data flow

1. Configure the page once in `app.py`; load settings and validate one-provider
   mode before rendering the three tab bodies. Existing discovery functions become
   callable renderers without page transitions, nested page config, or `st.stop()`
   that would terminate later tabs.
2. First tab reuses discovery calculations and dated industry evidence. Selected
   industry ID and evidence context feed a validated local membership catalog.
   Missing live catalog/rights produces a visible limitation, not guessed members.
3. Industry Deep-Dive displays eligible members, provenance/date/coverage and a
   stock multiselect. Preserve valid IDs on rerun; invalidate dependent selections
   before instantiating widgets when context changes.
4. Fundamental Grading has explicit Load/Refresh actions. Tabs can execute eagerly
   at the supported minimum, so tab placement alone never authorizes network calls.
   Load fetches only the requested page (five stocks); page changes invalidate
   displayed results and require explicit load. Refresh clears only those cache keys.
5. Bundle reader attempts each of four components once, with bounded retries only
   for identified transient failures using existing error classification. Normalize
   successful components and aggregate explicit failures. Empty whole statements
   are uncertain retrieval outcomes, not confirmed absence.
6. Successful nonempty bundles enter the cache. If a component failed or is
   ambiguous, raise a typed acquisition error containing safe partial evidence;
   the cache records no result. UI shows the error and can render valid metrics
   from that partial evidence for the current action without claiming full success.
   Do not store exception objects or partial failure bundles as shared cached data.
7. Pure metric construction aligns statement periods and derives values, comments,
   and histories under the [data contract](./contracts/fundamental-data.md). Reuse
   deterministic transforms keyed by evidence fingerprint and schema version.
8. Render the [UI contract](./contracts/fundamental-ui.md); keep provenance and
   errors outside metric fallback text. Existing implemented aggregate results,
   if present in an integration branch, stay outside the matrix and unchanged.

### Migration and scope reconciliation

- Root/Cloud entrypoint remains `streamlit_app.py`; remove runtime `st.navigation`,
  `st.Page`, and `st.switch_page` handoffs from the active journey.
- Document that old `/discovery` and `/industry-discovery` routed URLs are retired;
  direct users to the root and the corresponding first tab. Do not retain a parallel
  router solely to preserve obsolete URLs. This is the explicitly approved behavior
  change; update README and navigation tests in implementation.
- Keep existing fixture mode and legacy evidence labels. A current profile from
  `.info` must never be shown as evidence from a historical weekly snapshot.
  Live financial grading uses current evidence only; historical fixture grading
  uses matching fixture bundles. Unsupported historical live cutoffs fail clearly.
- A configured live catalog must document classification/coverage and display rights
  before activation. Fixtures prove end-to-end behavior without claiming live coverage.
- Parent `001` design/tasks remain historical and unreconciled; this plan supersedes
  only navigation, membership handoff, and displayed fundamental metric surfaces.
  It does not declare parent technical screening or relative grading implemented.

### Implementation order and required evidence

1. T001: Add failing formula/fake-Ticker/cache tests, then implement the typed
   calculations, bundled reader, and targeted cache/refresh helpers.
2. T002: Add failing entrypoint/membership/state tests, then establish validated
   membership, context transitions, and callable tab rendering.
3. T003: Add failing matrix/history tests, then implement the compact renderer.
4. T004: Add failing grading-action/integration tests, then wire Load/Refresh,
   paging, partial failures, and provenance into the root app.
5. Validate complete, partial, missing, failing, historical, and multi-session flows;
   update directly related README migration, source, freshness, and coverage docs.

Use the [quickstart](./quickstart.md) for executable validation commands and expected
outcomes. Run focused tests first, then full non-live regression because app-shell
migration crosses existing discovery/navigation behavior. Live calls are optional
and gated; they cannot establish missing-data correctness or eight-quarter coverage.

## Complexity Tracking

No justified constitution violations or new architectural layers. Scope growth is
explicitly user-approved, and the proposed modules follow existing repository layers.
