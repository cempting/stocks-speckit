# Implementation Plan: Industry ETF Momentum

> **2026-10-31 alignment:** SQLite/static catalog storage below is pre-cutover history.
> [Feature 010](../010-manifest-csv-catalogs/spec.md) requires manifest-registered hierarchy,
> ETF listing/mapping CSVs, and file-based approvals/provenance, with no embedded runtime roster.
> Feature 008's explicitly reviewed baskets remain labeled alternatives, not ETF momentum.
> Preserve completed task/test history; plan the new file boundary rather than reapplying SQL work.

**Branch**: `007-industry-etf-momentum` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Provide reviewed ETF-based momentum for industry and sub-industry rows by storing an explicit,
region-and-classification keyed ETF mapping, loading only those mapped instruments, and projecting
the mapped ETF identifier plus an explicit coverage/evidence state in the industry momentum table.
The existing stock-member industry momentum remains separate; no parent, sector, broad-market, or
single-stock proxy may be silently substituted for a missing ETF mapping.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12

**Primary Dependencies**: Streamlit, pandas, yfinance, pytest

**Storage**: Existing reviewed regional SQLite hierarchy and static reviewed fixture/catalog data

**Testing**: pytest AppTest, unit tests, integration tests; Ruff and strict Pyright

**Target Platform**: Local Streamlit web application

**Project Type**: Single Python Streamlit application

**Performance Goals**: One batched daily-history request for the distinct mapped ETFs selected by
the visible industry scope; no provider call for unmapped classifications

**Constraints**: Mappings are explicit and reviewed; price evidence must honor the selected as-of
date; no implicit substitutions; preserve existing stock-member discovery behavior

**Scale/Scope**: Existing US reviewed industry/sub-industry hierarchy and its mapped ETFs

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1 design.*

- **Keep It Simple / Lean Delivery / YAGNI**: Reuse the current daily-history loading and
  performance calculation. Add one explicit mapping catalog rather than a generalized
  representation-selection system or automatic ETF discovery.
- **Avoid Waste**: Request only distinct, approved ETF symbols for classifications in the active
  table scope. Do not fetch history for unmapped/invalid rows.
- **Separation of Concerns / High Cohesion**: Keep mapping validation and ETF-row construction in
  domain/application code; keep history retrieval in the existing workflow/provider boundary; keep
  table rendering in the UI component.
- **Application and Data Constraints**: Preserve explicit unavailable/error states and selected
  as-of semantics. No new runtime provider, hidden request, or persistence system is required.

**Post-design result**: PASS. The design introduces no constitution violation or complexity
exception.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/market_leadership/
├── domain/
│   ├── industry_momentum.py
│   └── industry_etf_mappings.py
├── application/
│   └── discover_sectors.py
├── infrastructure/
│   └── region_database.py
└── ui/
    ├── components/progressive_tape.py
    └── workflows/discovery_page.py

tests/
├── unit/
│   ├── test_industry_etf_mappings.py
│   └── ui/test_progressive_tape.py
├── integration/test_stock_evidence.py
└── app/test_sector_stock_explorer.py
```

**Structure Decision**: Extend the existing single Streamlit application. The mapping catalog and
row-state rules are cohesive domain concerns; existing discovery orchestration retrieves the mapped
symbols; the progressive tape owns visual projection.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
