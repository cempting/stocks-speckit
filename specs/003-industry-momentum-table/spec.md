# Feature 003: Consolidated into Discovery and Sector-to-Stock Explorer

**Status**: Superseded by consolidation on 2026-11-02; no independent implementation scope.

The active specification is [feature 004](../004-sector-stock-explorer/spec.md).
It owns Discovery/Industry Deep-Dive, industry momentum, progressive navigation, and chart behavior.
Root-tab placement follows 015 and retains Yahoo Classification Preview.
The traceability table below and [task-history ledger](../task-history.md) preserve requirement
ownership and historical completion evidence; consolidation claims no new implementation or tests.

## Requirement traceability

IDs in this table are qualified by feature; historical IDs MUST NOT be reused as new requirements.

| Historical 003 requirement | Current 004 requirement | Disposition |
|---|---|---|
| FR-001 | FR-001-FR-003 | Sector and industry evidence remain accessible through progressive tapes, not simultaneous tapes |
| FR-002 | FR-035, FR-029 | Five-session momentum default retained; one-session calculation retained without adding a removed selector |
| FR-003 | FR-035 | Completed-session adjusted-price return |
| FR-004 | FR-035, FR-036 | Direction semantics retained; controls follow the current tape baseline |
| FR-005 | FR-004, FR-029, FR-038 | Evidence retained in current columns, tooltips, and context rather than extra columns |
| FR-006 | FR-002, FR-036 | Current single-sector path supersedes the older multi-sector control |
| FR-007 | FR-036 | Scoped ranking, equal ranks, deterministic ties, no insufficient rank |
| FR-008 | FR-032, FR-037 | Exact approved ETF/basket and visible uncovered nodes |
| FR-009 | FR-036 | Sorting does not mutate evidence |
| FR-010 | FR-003, FR-004, FR-012 | Stable selection and preserved context |
| FR-011 | FR-039 | Industry/sector analytic parity |
| FR-012 | FR-038 | Dated historical evidence, not forecasts |
| FR-013 | FR-039 | Each entity uses its own observations |
| FR-014 | FR-038 | Source, date, freshness, and failure disclosures |
| FR-015 | FR-033 | Original two-tab limit superseded by 015; retained Discovery/Deep-Dive and no runtime evidence/provider modes |
| FR-016 | FR-034 | yfinance only; explicit failure without fallback |
| FR-017 | FR-014, FR-022, FR-040 | One reviewed release and dependent selection invalidation |
| FR-018 | FR-014, FR-022, FR-032, FR-040 | Manifest authority and exact scoped identities |

Historical SC-001-SC-007 are retained by current 004 SC-017-SC-023.
The obsolete independent plan, backlog and full historical specification were removed.
Research, data models and checklists remain historical evidence, not execution authority.
Use [004's plan](../004-sector-stock-explorer/plan.md) and
[tasks](../004-sector-stock-explorer/tasks.md) for the active scope.
The [live UI contract](contracts/live-discovery-ui.md) remains a supporting contract for 004.
Reconcile any older artifact with 004 and the [authority map](../README.md) before further execution;
do not reopen completed tasks or replay snapshot/database plans.
