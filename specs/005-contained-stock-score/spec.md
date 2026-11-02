# Feature 005: Consolidated into Stock Comparison Table

**Status**: Superseded by consolidation on 2026-11-02; no independent implementation scope.

The active specification is [feature 006](../006-stock-table-columns/spec.md).
It owns both the complete three-component Total Score and the current five-column presentation.
The [historical specification](historical-spec.md) preserves original stories, requirement IDs,
success criteria, and status; consolidation does not claim implementation or new test results.

## Requirement traceability

| Historical 005 requirement | Current 006 requirement | Disposition |
|---|---|---|
| FR-001 | FR-001, FR-006 | One aggregate; its current label is Total Score, not Score |
| FR-002 | FR-006 | One consistent calculation |
| FR-003 | FR-006 | Equal-weight mean only with all three components |
| FR-004 | FR-010 | Numeric, not loaded, insufficient, unavailable, and error states |
| FR-005 | FR-008 | Explicit loading only |
| FR-006 | FR-001, FR-011 | No Observed or Chart Status columns |
| FR-007 | FR-002, FR-003, FR-011 | Chart-cell disclosures remain |
| FR-008 | FR-001, FR-007 | Charts and identity retained; separate price/name columns superseded by the five-column amendment |
| FR-009 | FR-009 | Exact effective membership and selective reconciliation |

Historical SC-001 and SC-003 map to 006 SC-001; SC-002 maps to SC-006;
SC-004 maps to SC-004; SC-005 maps to SC-005.
Existing [plans](plan.md), [tasks](tasks.md), research, data models, checklists, and contracts
remain historical evidence, not an independent backlog. Earlier column names/order MUST NOT
override 006 or its [stock-table contract](../006-stock-table-columns/contracts/stock-table.md).
Reconcile older artifacts before execution; retain task completion markers and prior test evidence.
