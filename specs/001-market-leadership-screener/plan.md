# Implementation Plan: Progressive Stock Screener

**Feature**: `001-market-leadership-screener` | **Date**: 2026-10-28
**Working branch**: `main` | **Spec**: [spec.md](spec.md)

**Scope confirmation**: Continue planning feature 001 despite the active-feature pointer moving
to feature 002 during this session. Leave that pointer, feature 002, and the branch untouched.
This plan does not incorporate feature 002's eight-metric layout.

## Summary

Replace the primary routed discovery journey with one Streamlit app containing
`st.tabs(["Sectors and Industries", "Industry Stocks", "Stock Detail"])`. Rank industries
by one or five completed trading-session returns; inspect all available industry stocks
with optional AND-combined technical criteria; compare Quality, Growth, and Cash Flow.
Keep the agreed **0-100 industry-peer percentile scale**, two metrics per block, and no
overall grade. The user's follow-up confirmation supersedes the proposed 1-100/A-F scale.

Use yfinance as the single on-demand runtime financial-data source. Use `st.cache_data`
for successful remote payloads and expensive deterministic calculations, and
`st.session_state` for private selections and loaded view state. No database, snapshot
build, Parquet cache, backend service, or new provider framework is required.

Live capability is conditional, not assumed: exhaustive dated industry/index membership,
corporate-action-comparable volume, publication dates and sufficient financial history
are not established by yfinance alone. Unsupported data produces visible insufficiency.
Controlled fixtures prove calculations but do not certify live coverage or display rights.

## Technical Context

**Language/Version**: Python `>=3.12,<3.13`, matching the existing manifest.

**Primary Dependencies**: Existing constraints: Streamlit `>=1.50,<2`, yfinance
`>=0.2.66,<1`, pandas `>=2.2,<3`, NumPy `>=2.2,<3`, Altair `>=5.5,<6`,
exchange-calendars `>=4.11,<5`. Use `uv.lock`; no dependency change in planning.
Do not depend on newer reactive-tab APIs absent from the minimum Streamlit version.

**Storage**: Process-local, nonpersistent Streamlit data cache; private session state.
Static source-qualification metadata and controlled test fixtures are not a financial
database. Existing snapshot files remain compatible but outside the new runtime path.

**Testing**: pytest for pure calculations, adapter contracts, integration and deterministic
timing cases; Streamlit AppTest for state and widget flows; browser checks for table
interaction, charts, tabs and user-visible timing. Existing Ruff and strict Pyright gates.

**Target Platform**: Local Streamlit on macOS/Linux and desktop browser. Hosted deployment
requires explicit source/display/derived-use permission; it is not authorized by this plan.

**Project Type**: One Python package, one Streamlit entrypoint, small calculation/data/UI helpers.

**Performance Goals**: SC-005: p95 at most two seconds for filter/sort/selection interactions
over 2,500 already-loaded stocks. Measure end-to-end rendering, not only a formula helper.
No cold-load latency or real-time-feed guarantee. Report remote progress and coverage.

**Constraints**: US common stocks; optional supported dated index filters; one source;
completed regular sessions; explicit errors/coverage; no silent top-N, provider fallback,
annual-for-TTM substitution, imputed publication dates, or retrospective current membership.

**Scale/Scope**: Three stories, FR-001 through FR-024, SC-001 through SC-008.
Load selected industries on demand, not the whole market's price history/fundamentals at startup.

## Constitution Check

Design compliance is distinct from passing implementation tests or qualifying a live source.

| Gate under constitution v2.0.0 | Before research | Post-design evidence | Design result |
|---|---|---|---|
| Deliberate design | Formulas and acceptance outcomes specified | Research, model and contracts resolve choices and failures | PASS |
| Cohesive units | UI, I/O and numerical policy need separate tests | Small helpers in the existing package; no new service layers | PASS |
| Tests as required evidence | Tests-first implementation required | Requirement/test matrix and quickstart define exact controlled cases | PASS; execution pending |
| Simple Streamlit-first architecture | Three tabs requested | Single app, explicit loads, no new route registry | PASS |
| Maintainability | Stable IDs, explicit inputs and reasons required | Typed records, versioned detector, cutoff and source fingerprints | PASS |
| Single free source and rights | yfinance selected, not silently supplemented | Unsupported capabilities fail closed; hosted rights are a release gate | PASS as design; source approval pending |
| Cache and state isolation | Remote reruns must reuse data | TTL/key/refresh contract; private parent-child state transitions | PASS |
| Migration safeguards | Prior work cannot be reinterpreted | Legacy schemas unchanged; contracts indexed; tasks history retained | PASS |

No architecture exception is requested. Missing live evidence must not be bypassed to claim
feature completion. No unanswered product design choice remains; source qualification and
measured acceptance remain explicit implementation/release dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/001-market-leadership-screener/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
    README.md
    workflow.md
    market-data-provider.md
    fundamental-scoring.md
    consolidation.md
    legacy/                       # preserved prior workflow/provider contracts
    ...                           # unchanged historical snapshot schemas/contracts
  tasks.md                        # historical; regenerate separately, preserving task IDs
```

### Source Code (planned changes, not implementation claims)

```text
src/market_leadership/
  app.py                          # three-tab composition; replaces primary st.navigation
  domain/
    screening.py                  # universe sets, session returns, ranks, tri-state criteria
    consolidation.py              # Wilder indicators and versioned interval detection
    fundamentals.py                # pure raw-fact validation, percentiles and block scores
    industry_proxies.py            # adapt existing qualification/selection where compatible
  infrastructure/
    yfinance_provider.py           # extend existing boundary with OHLC/actions/facts/universe
  ui/
    cache.py                      # new-path st.cache_data wrappers; legacy loaders isolated
    state.py                      # namespaced selections, loaded-view intents, invalidation
    screener.py                   # three stage-rendering functions, not a routing framework
tests/
  unit/domain/                    # financial and technical boundary fixtures
  contract/                       # mocked yfinance payloads, completeness and failure contracts
  integration/                    # cache/cutoff/cohort invariance and migration guards
  app/                            # AppTest plus targeted browser acceptance where needed
```

**Structure Decision**: Reuse the installable package and entrypoint. Helpers are needed to
keep I/O, numerical rules and rendering independently testable, not to introduce a provider
framework. No new application orchestration layer is needed. Inspect existing proxy,
session-calendar, chart and error helpers before adapting them.

The existing price adapter retains only close/volume; it cannot yet support OHLC-based
ADX/ATR/corridors. Extend the new request path without breaking legacy close/volume
consumers. The old calendar-offset performance helper and normalized-slope regime rule
do not implement session returns or the specified ADX detector; do not silently reuse
their different semantics.

## Data Flow and Delivery Order

1. Establish canonical records and controlled fixtures; write failing calculation tests.
2. Implement pure screening, consolidation and financial scoring utilities independently.
   The scoring utility accepts raw normalized facts and the full eligible peer cohort;
   it never fetches data or imports Streamlit.
3. Extend the yfinance boundary and cache wrappers with mocked contract tests first.
   Record verified capabilities; return unsupported states for unmet source requirements.
4. Wire explicit **Load industries**, **Load stocks**, **Load scorecards** and targeted
   refresh intents. Eager tab rendering alone never performs remote requests. Loading
   scorecards fetches the selected industry's entire pre-technical-filter peer cohort,
   not merely selected or paged stocks.
5. Connect dataframe industry selection, selection-only stock editor, scorecard metric
   columns and subtle consolidation charts; reconcile dependent selections on each change.
6. Validate migration and all revised acceptance criteria before retiring old primary UI
   routes. Keep legacy snapshot builders/readers and fixtures functional and separate.

Pure financial and technical modules can be implemented in parallel after shared records
are settled. UI/cache work depends on those contracts. Source qualification may proceed
independently but cannot be replaced by fixture success.

## Requirement Ownership and Evidence

| Requirements | Owner | Required evidence |
|---|---|---|
| FR-001, FR-009, FR-010, FR-017 | app, screener rendering, session state | Three-tab AppTest; immutable data columns; full pagination; dependent invalidation |
| FR-002-FR-004 | data boundary and screening | Common-stock classification; union/intersection; cap boundaries; unsupported indices |
| FR-005-FR-008 | screening and proxy selection | Exact 1/5-session endpoints; shared ranks; dated ETF/stock qualification |
| FR-011-FR-013 | screening | AND truth states; SMA equality; prior-volume-only rule and invalid parameters |
| FR-014-FR-016 | consolidation and charts | Reference indicator fixtures; long/short runs; no future information; corridor agreement |
| FR-018-FR-021 | fundamentals and scorecards | Raw ratios, financial availability, percentile ties, peer invariance and invalid denominators |
| FR-022-FR-024 | cache/data boundary and UI | Zero repeated calls while fresh; explicit expiry/errors/rights; no advice claims |
| SC-001, SC-002, SC-008 | user acceptance | At least 90% meet the specified timed/interpretation outcomes |
| SC-003, SC-004, SC-006, SC-007 | controlled integration acceptance | Exact outputs, coverage and request counts |
| SC-005 | browser timing with controlled loaded data | 2,500 stocks; p95 <= 2 seconds including visible UI update |

## Migration and Remaining Gates

This design supersedes the old snapshot-first plan, routed workflows, relative-strength
composites and Massive-selection behavior for the **new path only**. Never reinterpret
existing weekly artifacts as these returns or scores. Historical schema bytes remain
unchanged; no migration or deletion of user data is needed.

Regenerate [tasks.md](tasks.md) with an explicit feature-001 path because the active pointer
currently selects 002. Preserve completed IDs/history; mark obsolete unbuilt scope as
superseded rather than treating it as implementation evidence. Planning does not generate
or check off tasks. Feature 002 needs a separate scope reconciliation before combining work.

Live release gates: verified universe/membership scope, qualified representations, adequate
financial periods/publication metadata, comparable volume, deployment rights, and measured
acceptance. Unsupported inputs remain visible; do not claim complete live fundamental grading.

## Complexity Tracking

No constitution violations or approved exceptions. No database, service tier, new provider
registry, or additional page-routing layer is proposed.
