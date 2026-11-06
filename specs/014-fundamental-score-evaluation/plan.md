# Implementation Plan: Fundamental Score Evaluation

**Branch**: `main` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-fundamental-score-evaluation/spec.md`

## Summary

Evaluate the current Quality, Growth, and Cash Flow component scores and their stock-list
Total Score for calculation correctness, context consistency, and usefulness as risk-analysis
evidence. Preserve the existing industry-relative percentiles, missing-data states, explicit
load behavior, and five-column stock list unless an evaluation result supports a proposed,
explicitly approved, versioned rule change. Keep peer-relative scores distinct from absolute
financial condition and make missing, zero, or negative cash flow unambiguous.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Existing `market-data` domain package, Streamlit application, pandas,
pytest. No new dependency is planned.

**Storage**: No new persisted score or finding store. Reuse existing in-memory score results,
explicit market-data cache, and documentation/test fixtures.

**Testing**: pytest with controlled financial facts, peer cohorts, and UI inputs; existing Ruff
and strict Pyright gates.

**Target Platform**: Existing local Streamlit application and Python workspace.

**Project Type**: Streamlit web application with a shared pure-domain scoring library.

**Performance Goals**: Do not add remote requests, hidden score loads, or new mandatory work to
ordinary table rendering. Preserve current explicit score-load behavior and avoid a measurable
regression in the existing scoring path.

**Constraints**:

- The selected yfinance financial-data path remains the sole provider; no provider fallback,
  source expansion, or copied provider data is introduced.
- Peer calculations use only eligible observations available by the common analysis cutoff,
  in comparable periods and currencies.
- Missing or invalid metric evidence remains explicit; no zero filling, partial means, stale
  success-shaped results, or silent weight redistribution.
- The stock-list five-column contract and existing three-component Total Score rule remain
  unchanged until explicit approval of a documented, versioned alternative.
- Cash-flow gaps and reported zero/negative values remain distinct and prominent; scores are
  historical decision support, not investment or trading advice.

**Scale/Scope**: Existing US industry peer cohorts, six current peer metrics, three component
scores, and their stock-list aggregate. No new market, scoring domain, data source, or
portfolio-level risk model.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle or constraint | Gate | Plan evidence |
|---|---|---|
| I. Keep It Simple | PASS | Reuse the current pure score function and existing surfaces; add no service, provider, or storage layer. |
| II. Lean Delivery | PASS | Limit work to evaluating and clearly presenting the three components and stock-list total. |
| III. YAGNI | PASS | Do not add new metrics, weighting options, investment recommendations, or configurable methodologies without an approved finding. |
| IV. Avoid Waste | PASS | Use deterministic fixtures and existing on-demand loads; no extra provider requests for presentation or evaluation. |
| V. Separation of Concerns | PASS | Keep financial retrieval, pure score calculations, and UI disclosure in their existing layers. |
| VI. High Cohesion, Low Coupling | PASS | Extend narrow existing score and display contracts; do not make the shared domain depend on Streamlit or provider code. |
| Python/Streamlit and single-provider constraints | PASS | The existing app and selected financial source remain in place; no additional provider is introduced. |
| Explicit cache/freshness and failure visibility | PASS | Preserve explicit score loading, cutoff/source context, and non-success states; no stale result is presented as fresh. |
| Data and privacy boundaries | PASS | Use controlled local tests and current permitted source; do not send unrelated or private user data. |
| Test-first workflow | PASS | Add controlled regression cases for formula, state, aggregate, and presentation behavior before implementation changes. |

No constitution exception or complexity justification is required.

## Project Structure

### Documentation (this feature)

```text
specs/014-fundamental-score-evaluation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── score-presentation.md
└── tasks.md              # Created by /speckit-tasks, not by this plan
```

### Source Code (repository root)

```text
packages/market-data/src/market_data/domain/
└── peer_scores.py                         # Pure peer metric and component calculations

src/market_leadership/
├── application/
│   └── score_industry.py                  # Explicit cohort loading and score context
└── ui/
    ├── components/
    │   ├── progressive_tape.py            # Stock-list Total Score
    │   ├── stock_detail.py                # Component score and evidence context
    │   └── fundamental_matrix.py          # Dated raw fundamental evidence
    └── workflows/
        ├── discovery_page.py              # Explicit score loading and user context
        └── fundamental_grading.py         # Fundamental evidence presentation

tests/
├── unit/domain/test_peer_scores.py
├── unit/ui/test_progressive_tape.py
├── app/test_stock_detail.py
└── integration/                            # Existing scoring/load behavior coverage
```

**Structure Decision**: Keep calculations in the existing shared `market_data` domain module,
orchestration in the app application layer, and disclosures on the existing Discovery and
fundamental-detail surfaces. Add tests beside those current responsibilities. No new package,
service, migration, or database is warranted.

## Phase 0: Research

Research is consolidated in [research.md](research.md). It confirms the current rule baseline,
records secondary-source limitations, and documents three implementation findings: the live
yfinance adapter currently cannot provide verified publication vintages or matching dated
market capitalization; the score detail retains six metric results but displays only the three
components; and `score_industry()` labels every non-error stock insufficient, suppressing a
numeric list total even when all components are available. The latter two findings require
targeted implementation and regression coverage. No result authorizes new score rules, source
fallback, or hidden data loading.

## Phase 1: Design and Contracts

- `data-model.md` captures normalized financial facts, metric results, component scores, peer
  context and provenance, stock-list total states, risk signals, and evaluation findings.
- `contracts/score-presentation.md` records the user-visible score, context, risk-disclosure,
  metric-evidence, and non-numeric state invariants without adding stock-list columns or hidden
  loading.
- `quickstart.md` describes deterministic validation of exact formulas, score consistency,
  state propagation, metric evidence, cash-flow edge cases, and app presentation; live provider
  access is not required.

The post-design constitution check remains PASS: the design adds no dependency, provider,
remote data path, persistence model, or extra service. The targeted score-state correction and
detail evidence display are directly required to make the existing results correct and
interpretable; scoring-rule changes remain gated on explicit approval.

## Complexity Tracking

No constitution violations.
