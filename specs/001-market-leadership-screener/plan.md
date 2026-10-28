# Implementation Plan: Market Leadership Screener

**Branch**: `001-market-leadership-screener` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build a weekly equity market-leadership screener that computes auditable market regimes, GICS
rankings, proxy eligibility, deterioration, and stock research gates from versioned market-data
snapshots. Keep calculations in pure Python modules, coordinate them through small application use
cases and provider protocols, and expose them through independently testable Streamlit workflow
functions registered in one explicit navigation composition root.

The Phase 2 foundation is narrower than the completed release: direct US daily price/volume
ingestion, a persistent canonical source cache, a daily input snapshot builder, and optional
immutable input-snapshot viewing. Live-provider discovery remains the Phase 2 UI default. Weekly
calculated scoreboards, additional markets, and non-price runtime contracts follow in user-story
phases.

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

**Performance Goals**: Filter, search, sort, and hierarchy interactions complete within two
seconds for 20 markets and 10,000 stocks; initial cached snapshot load targets five seconds on a
developer laptop

**Constraints**: Weekly completed-market data only; local eligibility is authoritative; no trade
execution or forecast behavior; missing evidence must fail closed; UI modules do not calculate
domain outcomes

**Scale/Scope**: 20 markets, GICS through sub-industry, approximately 10,000 stocks, four primary
workflows, one active read-only snapshot per process

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Pre-design gate | Post-design evidence | Result |
|-----------|-----------------|----------------------|--------|
| Deliberate design | Requirements and domain decisions identify formulas, dates, thresholds, and failure modes. | Research records choices and rejected alternatives; contracts define inputs and errors. | PASS |
| Small, cohesive units | Domain, orchestration, adapters, and UI need distinct owners. | Source tree gives calculations, use cases, providers, workflows, and components one responsibility each. | PASS |
| Tests as evidence | Every behavior needs deterministic controlled data. | Unit, contract, integration, and `AppTest` suites map to FR-001–FR-023. | PASS |
| Lean, extensible architecture | Two demonstrated replacement needs exist: workflows and market-data sources. | Two narrow protocols and an explicit registry address those needs; no dynamic plugin system or service tier is added. | PASS |
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
│   ├── rankings.py                # statuses, tie-breaking, and top group
│   ├── proxies.py                 # proxy qualification and fallback selection
│   ├── deterioration.py           # monthly and weekly review-state transitions
│   └── candidates.py              # industry and single-stock eligibility gates
├── application/
│   ├── ports.py                   # MarketDataProvider and SnapshotRepository protocols
│   ├── queries.py                 # typed filter/search/sort request records
│   ├── build_snapshot.py          # deterministic offline calculation pipeline
│   ├── browse_scoreboard.py       # scoreboard query use case
│   └── inspect_industry.py        # industry, stock, evidence, and provenance use case
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
    │   ├── industry_detail.py
    │   ├── stock_research.py
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
workflow registry controls pages only. The equity package accepts only `EQUITY` instruments; a future
asset category requires its own specified model and calculation path selected at the composition
boundary before equity domain code runs.

## Requirement Ownership

| Requirements | Owning implementation | Primary evidence |
|--------------|-----------------------|------------------|
| FR-001–FR-002 | `models`, `build_snapshot`, scoreboard workflow | hierarchy fixtures and default-page `AppTest` |
| FR-003 | `regimes` | slope-boundary and regime unit tests |
| FR-004–FR-007 | `relative_strength`, `rankings` | controlled calculation and tie tests |
| FR-008–FR-013 | browse use case, UI state, ranking components | query integration tests and `AppTest` |
| FR-014 | `proxies` | threshold and fallback unit/contract fixtures |
| FR-015–FR-018 | `deterioration`, `candidates` | transition and pass/fail gate tests |
| FR-019–FR-022 | snapshot contract, provenance/evidence components | contract tests and interpretation `AppTest` |
| FR-023 | category discriminator, composition boundary, and unchanged equity domain modules | frozen equity baseline compatibility test |

## Complexity Tracking

No constitution violations or justified complexity exceptions.
