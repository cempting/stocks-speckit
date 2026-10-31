# Data Model: Industry ETF Momentum

The catalog authority is the activated manifest-backed file release under
[feature 010](../010-manifest-csv-catalogs/spec.md); these logical fields are not SQL tables or
a complete new CSV contract. Exact reviewed listing identity, not a globally unique ticker,
links a mapping to market-data evidence. Feature 008 baskets remain separately labeled alternatives.

## Classification ETF Mapping

| Field | Description | Validation |
|-------|-------------|------------|
| region ID | Reviewed market/region scope | Required; must match the displayed hierarchy |
| classification ID | Reviewed classification scheme | Required; must match the displayed hierarchy |
| classification version | Exact reviewed hierarchy version | Required; must match the node and active release |
| node ID | Industry or sub-industry row identity | Required; must identify the exact mapped row |
| listing ID | Exact verified regional ETF listing | Required; source, exchange, and effective coverage must match |
| ETF symbol | Display/provider symbol from the verified listing | Required for requests; not a globally unique identity |
| ETF name | Human-readable mapped instrument | Required |
| effective from/to | Mapping validity interval | Must include the selected as-of date |
| approval state | Whether mapping is reviewed for display | Must be approved |
| source and approval reference | Retained mapping/listing review evidence | Required; registration alone is not approval |

The same ETF symbol may appear in multiple mappings only when each classification mapping is
explicitly approved. A mapping cannot be applied to another region, classification, node, or
out-of-range date.

## ETF Momentum Evidence

| Field | Description |
|-------|-------------|
| mapped ETF symbol/name | Identity retained for mapped rows even if history is unavailable |
| as-of date | Date for which history and momentum are evaluated |
| performance periods | One-week through twelve-month momentum values, when sufficient |
| state | `available`, `insufficient_evidence`, `unavailable_evidence`, `not_covered`, or `invalid_mapping` |
| reason | Clear explanation for any non-available state |

State transitions are one-way for a table render: resolve mapping, validate it for the selected
scope/date, obtain mapped ETF evidence if valid, then calculate momentum when history is
sufficient. No state may transition to `available` through an inferred substitute.

## Industry Momentum Row

Combines the reviewed classification identity with zero or one mapping and one evidence state.
Every reviewed hierarchy row yields one display row. Covered rows identify their mapped ETF;
non-covered/invalid rows retain their classification and explicit state.
