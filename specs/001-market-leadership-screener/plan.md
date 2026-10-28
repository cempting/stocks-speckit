# Implementation Plan: Market Leadership Screener

**Branch**: `001-market-leadership-screener` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build a weekly equity market-leadership screener that compares selected markets without pooling
their local rankings, ranks sectors before industry drill-down, and distinguishes participation,
inferred trading activity, and observed flows in versioned market-data snapshots. Keep calculations
in pure Python modules, coordinate them through small application use cases and provider protocols,
and expose them through independently testable Streamlit workflows in one navigation composition root.

The Phase 2 foundation provides direct US daily price/volume ingestion, a persistent source cache,
and daily input snapshots. Phase 3 adds controlled US/JP/GB local comparison. Phase 4 publishes
fixture-backed completed weekly sector/industry snapshots and provides separate sector and
industry discovery workflows. Industry discovery filters by one or more stable US parent-sector
IDs and preserves the source mode when launched from sector discovery. Weekly industry inspection
uses only completed weekly artifacts. Live industry proxies remain disabled unless dated ETF or
membership/capitalization inputs and market-data display/derived-data rights are verified. These
fixture workflows do not imply live non-US ingestion; constituent participation, flows, and other
live non-price contracts remain deferred.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Streamlit 1.62.x, pandas 3.x, NumPy 2.x, PyArrow 23.x; `uv` manages
the project and lockfile

**Storage**: Read-only, versioned Parquet snapshot directories with a JSON manifest; no user
database in this feature

**Testing**: pytest for unit, contract, and integration tests; Streamlit `AppTest` for workflows;
Ruff and Pyright as static quality gates

**Target Platform**: Local or hosted Streamlit server on macOS/Linux with a modern desktop or
mobile browser

**Project Type**: Single Python package with a Streamlit web UI and an offline snapshot-build
entrypoint

**Performance Goals**: Filter, sort, and hierarchy interactions complete within two seconds for
20 markets at the 95th percentile, measured against controlled data

**Constraints**: Weekly completed-market scoreboards with daily evidence inputs; local comparisons
are authoritative; no trade execution or forecast behavior; missing evidence fails closed only for
the affected result; UI modules do not calculate domain outcomes; verify source rights before live
non-price or additional-market ingestion is advertised

**Scale/Scope**: Up to 20 markets for acceptance/performance; sector and industry classifications,
five user stories, immutable read-only snapshots, no company-level research workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Pre-design gate | Post-design evidence | Result |
|-----------|-----------------|----------------------|--------|
| Deliberate design | Requirements and domain decisions identify formulas, dates, thresholds, and failure modes. | Research records choices and rejected alternatives; contracts define inputs and errors. | PASS |
| Small, cohesive units | Domain, orchestration, adapters, and UI need distinct owners. | Source tree gives calculations, use cases, providers, workflows, and components one responsibility each. | PASS |
| Tests as evidence | Every behavior needs deterministic controlled data. | Failing-first unit, contract, integration, and `AppTest` tasks map to FR-001–FR-027. | PASS |
| Lean, extensible architecture | Two demonstrated replacement needs exist: workflows and market-data sources. | Existing narrow ports and explicit registry address those needs; no dynamic plugin system or service tier is added. | PASS |
| Maintainability | Domain decisions require visible provenance and explicit state. | Immutable domain records, versioned snapshot manifests, typed boundaries, and reason codes preserve intent. | PASS |
| Engineering constraints | External data, filesystem access, dates, and Streamlit state must be isolated. | Provider/repository ports isolate I/O; evaluation dates are inputs; shared cached data is separate from session filter state. | PASS |

No constitution exception is required.

## Project Structure

### Documentation (this feature)

```text
specs/001-market-leadership-screener/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml
uv.lock
src/market_leadership/
├── app.py                         # Streamlit entrypoint; one st.navigation call
├── bootstrap.py                   # composition root and explicit workflow registry
├── config.py                      # environment and snapshot-path configuration
├── domain/
│   ├── models.py                  # immutable identifiers and result records
│   ├── regimes.py                 # normalized slope and market-regime rules
│   ├── relative_strength.py       # returns, components, and composite
│   ├── rankings.py                # statuses, tie-breaking, rank and score changes
│   ├── proxies.py                 # documented representation and qualification
│   ├── participation.py           # constituent breadth and concentration
│   └── trading_activity.py        # price/volume-derived confirmation
├── application/
│   ├── ports.py                   # MarketDataProvider and SnapshotRepository protocols
│   ├── queries.py                 # typed filter/search/sort request records
│   ├── build_snapshot.py          # deterministic offline calculation pipeline
│   │   ├── browse_scoreboard.py       # scoreboard query use case
│   ├── discover_industries.py     # live industry price discovery when source gate passes
│   ├── inspect_industry.py        # weekly industry, participation and provenance use case
│   └── flows.py                   # observed fund-flow normalization and overlap
├── infrastructure/
│   ├── parquet_provider.py        # validated canonical snapshot input
│   ├── parquet_repository.py      # atomic snapshot persistence and retrieval
│   ├── massive_provider.py        # authenticated Massive REST adapter
│   ├── yfinance_provider.py       # explicit no-key development adapter
│   ├── market_data_cache.py      # canonical source-response cache
│   └── fixture_provider.py        # deterministic acceptance-data adapter
└── ui/
    ├── navigation.py              # WorkflowSpec and st.Page construction
    ├── state.py                   # session-local filter and drill-down state
    ├── workflows/
    │   ├── scoreboard.py
    │   ├── industry_discovery.py
    │   ├── industry_detail.py
    │   └── methodology.py
    └── components/
        ├── filters.py
        ├── ranking_table.py
        ├── regime_summary.py
        ├── evidence_panel.py
        └── provenance.py

tests/
├── fixtures/                      # dated controlled snapshots and expected outputs
├── unit/domain/                   # formulas, boundaries, ties, and state transitions
├── contract/                      # provider and snapshot schema conformance
├── integration/                   # use cases over fixture and Parquet adapters
└── app/                           # Streamlit AppTest workflow tests
```

**Structure Decision**: Use one installable `src` package. The domain owns calculation policy and
has no Streamlit or filesystem imports. Application use cases depend only on domain code and ports.
Infrastructure implements those ports. UI workflows are small function-based pages assembled in
`bootstrap.py`; swapping a workflow changes one registry entry and does not alter navigation or
domain code. Components render supplied view data and never determine status or eligibility. The
workflow registry controls pages only. The equity package accepts only `EQUITY` instruments; other
asset categories and stock research remain out of scope. Phase 2 input manifests remain unchanged;
a separately versioned calculated weekly snapshot contract precedes its implementation.

**Industry discovery decision**: Keep weekly calculated industry snapshots backward-compatible.
The new live-only single-stock proxy is a distinct domain type and never enters the weekly fund,
index, or basket representation contract. ETF matching requires issuer/index evidence for an
industry-specific exposure; a broad or multi-industry fund does not qualify as one industry's proxy.
The UI can display weekly results and fail closed for live industries until sources satisfy T085 in
`tasks.md`; a source name or public factsheet alone does not grant live display rights.

## Requirement Ownership

| Requirements | Owning implementation | Primary evidence |
|--------------|-----------------------|------------------|
| FR-001–FR-006 | market/classification inputs, `regimes`, browse use case, scoreboard workflow | US/JP/GB fixture, boundary tests, selection `AppTest` |
| FR-007–FR-014 | `relative_strength`, `rankings`, `proxies`, weekly snapshot, industry inspection | basis, ties, missing history and drill-down tests |
| FR-015–FR-018 | `participation`, `trading_activity`, inspection use case | membership/weight/volume coverage and divergence tests |
| FR-019–FR-021 | observed-flow contract, `flows`, evidence panel | normalization/overlap, stale and separation tests |
| FR-022–FR-023 | browse query, session filter state, filter components | filter/sort/reset/empty `AppTest` |
| FR-024–FR-027 | provenance records, methodology workflow, evidence panels | contract and interpretation `AppTest` |

## Complexity Tracking

No constitution violations or justified complexity exceptions.
