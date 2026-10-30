# Implementation Plan: Simplified Live Discovery

**Branch**: `003-industry-momentum-table` | **Date**: 2026-10-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-industry-momentum-table/spec.md`

## Summary

Simplify the root Streamlit interface to two tabs: Discovery and Industry Deep-Dive. Discovery
uses yfinance as its only live source with no mode or provider controls. Industry Deep-Dive uses
only reviewed live membership evidence. Remove fixture, snapshot, comparison, weekly-leadership,
and Fundamental Grading choices from the user journey; preserve explicit failure messages and
session-local dependent-selection clearing.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Streamlit, pandas, Altair, yfinance

**Storage**: Session-local selection state and the existing local live-response cache; no user
selectable snapshot or fixture data source

**Testing**: pytest, Streamlit AppTest, Pyright, Ruff; deterministic test doubles remain test-only

**Target Platform**: Browser-hosted Streamlit application

**Project Type**: Single Python web application

**Performance Goals**: With cached valid live data, 95% of ordinary Discovery reruns complete
within two seconds; live initial loads show progress rather than hiding provider latency.

**Constraints**: Exactly one live provider, yfinance; no provider switching or fixture/snapshot
fallback; live data and live membership failures are explicit; only the data required by the active
screen is requested.

**Scale/Scope**: US Discovery and Industry Deep-Dive only. Fundamental grading, account storage,
saved screens, alerts, portfolio actions, multi-market comparisons, snapshots, and synthetic
runtime evidence are excluded.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-design evaluation: PASS**

- **Deliberate design**: The revised feature decision, current runtime dependencies, failure
  behavior, data model, UI contract, and validation guide are recorded in this feature directory.
- **Small cohesive units**: Simplification removes UI branches and reuses the existing live request,
  cached provider, and reviewed-membership boundaries. It does not add a service, route, or
  provider abstraction.
- **Test evidence**: AppTests will assert the two-tab live-only journey and error behavior.
  Unit tests continue using deterministic doubles instead of live network calls.
- **Simple Streamlit-first architecture**: The root remains a two-tab Streamlit interface.
- **Data/session constraints**: yfinance is the sole runtime provider; the existing cache and
  namespaced session state remain in use. Missing/incomplete evidence never receives a substitute.

**Post-design evaluation: PASS** — The design removes runtime modes and dependencies rather than
adding architectural complexity. It preserves caching, source/date disclosure, scoped requests,
and explicit failure behavior required by the constitution.

## Project Structure

### Documentation

```text
specs/003-industry-momentum-table/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code

```text
src/market_leadership/
├── app.py
├── bootstrap.py
├── config.py
├── infrastructure/
│   ├── yfinance_provider.py
│   └── stock_membership.py
└── ui/workflows/
    ├── discovery_page.py
    └── industry_deep_dive.py

tests/
├── app/
│   ├── test_discovery.py
│   └── test_progressive_tabs.py
└── unit/
    ├── test_config.py
    └── test_stock_selection.py
```

**Structure Decision**: Keep the current single application and remove unused runtime branches
from its existing root, configuration, and workflow modules. Preserve fixture code only where it
is used by tests.

## Complexity Tracking

No constitution violations or exceptions are required.
