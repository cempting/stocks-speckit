# Research: Industry ETF Momentum

## Decision: Use a reviewed, classification-keyed ETF mapping catalog

**Rationale**: The existing `IndustryRepresentation` tuple is a limited static list keyed only by
industry identifier/name/sector, while the reviewed discovery hierarchy has explicit region,
classification, and hierarchy identity. A mapping keyed by the reviewed row identity makes the ETF
selection auditable and supports both parent industries and sub-industries.

**Alternatives considered**:

- Infer an ETF from the classification name: rejected because naming matches cannot establish
  appropriate exposure.
- Reuse a parent/sector ETF where no mapping exists: rejected by FR-004 because it fabricates
  classification momentum.
- Use the highest-cap stock as a fallback: rejected because it is not ETF evidence and would
  change the intended metric.

## Decision: Keep ETF momentum separate from stock-member momentum

**Rationale**: The progressive discovery workflow currently builds industry results from reviewed
stock memberships and price histories. An ETF mapping is a different representation and must be
identified as such rather than replacing that existing calculation implicitly.

**Alternatives considered**:

- Replace all stock-member industry results with ETF results: rejected because it changes the
  existing discovery product outside this feature.
- Combine ETF and stock-member returns into one value: rejected because users could not determine
  what the reported momentum represents.

## Decision: Load only distinct mapped ETF symbols in the active scope

**Rationale**: The existing provider supports batched symbol history. Deduplicating valid mappings
avoids requests for non-covered rows and avoids duplicate requests where parent and child are
explicitly approved to share an ETF.

**Alternatives considered**:

- Load the full static ETF catalog: rejected as unnecessary provider work.
- Load one ETF per row: rejected as duplicate work and avoidable request overhead.

## Decision: Represent coverage and evidence independently

**Rationale**: A row can have no approved ETF, an invalid mapping, a mapped ETF with unavailable
history, insufficient history, or a usable momentum result. Those conditions need distinct labels
to prevent an unavailable number from being interpreted as performance.

**Alternatives considered**:

- Use one generic `Unavailable` state: rejected because it hides whether a mapping exists.
- Omit non-covered rows: rejected because completeness of the reviewed hierarchy is required.
