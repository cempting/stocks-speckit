# Feature 007: Consolidated into Industry Representations and Momentum

**Status**: Superseded by consolidation on 2026-11-02; no independent implementation scope.

The active specification is [feature 008](../008-industry-representation-tools/spec.md).
It owns reviewed ETF/basket approval and the momentum evidence consumed by Discovery.
The traceability table below and [task-history ledger](../task-history.md) preserve requirement
ownership and retirement evidence. Original T001-T011 are superseded, not completed;
consolidation claims no new implementation or tests.

## Requirement traceability

| Historical 007 requirement | Current 008 requirement | Disposition |
|---|---|---|
| FR-001 | FR-002, FR-011 | Exact approved ETF mapping for each covered node |
| FR-002 | FR-003, FR-007, FR-011 | Approved ETF only, or explicitly labeled approved basket alternative |
| FR-003 | FR-006, FR-012 | ETF identity remains visible beside momentum |
| FR-004 | FR-013 | No parent, sector, broad-market, or arbitrary substitution |
| FR-005 | FR-014 | Explicit mapping and market-evidence states |
| FR-006 | FR-014 | No mapping differs from missing mapped-ETF history |
| FR-007 | FR-005, FR-009, FR-011 | Exact scoped node/listing validation |
| FR-008 | FR-015 | Consistent as-of and effective dates |
| FR-009 | FR-001, FR-009, FR-016 | One file release, visible active nodes, no unchecked fallback |

Historical SC-001-SC-005 are retained by 008 SC-006-SC-010, respectively.
The obsolete independent plan, backlog and full historical specification were removed.
Research, data models, checklists and older contracts remain historical evidence,
not an independent backlog. Use [008's plan](../008-industry-representation-tools/plan.md)
and [tasks](../008-industry-representation-tools/tasks.md) for the active scope.
Reconcile them with 008 and its [representation contract](../008-industry-representation-tools/contracts/representation-workflow.md)
before execution. Preserve task completion markers and prior test results; do not replay database
plans or treat an old ETF-only description as a ban on explicitly approved basket alternatives.
