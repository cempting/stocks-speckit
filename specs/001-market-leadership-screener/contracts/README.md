# Contract Status

The [revised specification](../spec.md) and [plan](../plan.md) govern the progressive
screener. These documents describe planned interfaces, not implemented capabilities.

## Current Design

| Contract | Responsibility |
|---|---|
| [workflow.md](workflow.md) | Three-tab UX, state, selection, chart and error behavior |
| [market-data-provider.md](market-data-provider.md) | One runtime source, canonical inputs, cache and coverage |
| [fundamental-scoring.md](fundamental-scoring.md) | Pure financial calculations, peer percentiles and blocks |
| [consolidation.md](consolidation.md) | Versioned indicators, variable-duration intervals and chart evidence |

These are local Python/UI contracts, not HTTP endpoints, a database schema or a new
provider plugin framework. Version calculation semantics explicitly when they change.

## Historical Compatibility

| Preserved artifact | Status |
|---|---|
| [legacy/workflow.md](legacy/workflow.md) | Former routed registry interface; not the new primary journey |
| [legacy/market-data-provider.md](legacy/market-data-provider.md) | Former snapshot/canonical provider interface; retained for existing consumers |
| [weekly-leadership.md](weekly-leadership.md) | Existing calculated weekly publication/read behavior; not the new five-session return |
| [deferred-evidence.md](deferred-evidence.md) | Historical weekly-product backlog; old story/phase numbering |
| [us-industry-proxies.md](us-industry-proxies.md) | Historical candidate-source review; no live enablement |
| [snapshot-manifest.schema.json](snapshot-manifest.schema.json) | Unchanged legacy daily input schema |
| [weekly-snapshot-manifest.schema.json](weekly-snapshot-manifest.schema.json) | Unchanged legacy weekly output schema |

Do not delete or reinterpret stored snapshots or change legacy schemas to fit new records.
Keep old builders/readers and compatibility tests separate from the new runtime path.
In particular, no stock proxy is inserted into a legacy weekly representation enum.
