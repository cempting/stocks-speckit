# Implementation Plan: Industry Representation Tools

> **2026-10-31 alignment:** The database boundary below describes implemented pre-cutover work.
> [Feature 010](../010-manifest-csv-catalogs/spec.md) replaces it with manifest-managed file
> sources and durable review/audit records. Exact ETF/basket approval, verified constituents,
> effective dates, 100% weights, no reweighting, and explicit chart gaps remain required.
> Preserve completed tasks/history; migrate records and refactor all consumers during 010.

**Branch**: `008-industry-representation-tools` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

## Summary

Provide reviewed worklist and administration tooling for industry/sub-industry representations:
approved ETFs where suitable, otherwise explicitly reviewed weighted stock baskets. The discovery
table identifies ETF, stock-basket alternative, or no coverage and calculates only active approved
evidence.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Streamlit, pandas, pytest  
**Storage**: Existing reviewed regional SQLite database  
**Testing**: pytest, Ruff, strict Pyright  
**Target Platform**: Local Streamlit application and administration CLI  
**Project Type**: Single Python application  
**Performance Goals**: Batch only distinct active ETF/basket symbols in the displayed scope  
**Constraints**: Reviewed sources, verified listings, effective dates; no automatic inference  
**Scale/Scope**: Active GICS industries and sub-industries

## Constitution Check

PASS. Reuse existing reviewed-source, representation, and market-data boundaries. Baskets are a
current required fallback, not a generalized portfolio system. No hidden provider requests or
substitutions are introduced.

## Project Structure

```text
src/market_leadership/
├── infrastructure/region_database.py
├── domain/industry_representations.py
├── application/discover_sectors.py
├── universe_admin.py
└── ui/workflows/discovery_page.py
tests/{unit,integration,app}/
```

**Structure Decision**: Extend existing reviewed database, administration CLI, discovery workflow,
and table rendering.

## Complexity Tracking

No constitution violations or exceptions.
