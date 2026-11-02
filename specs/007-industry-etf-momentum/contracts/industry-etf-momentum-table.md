# Industry ETF Momentum Table Contract

> Historical ETF-only contract after the 2026-11-02 consolidation. The active
> [008 specification](../../008-industry-representation-tools/spec.md) and
> [representation contract](../../008-industry-representation-tools/contracts/representation-workflow.md)
> retain these mapping/evidence semantics alongside explicitly approved baskets.
> Row layout and tooltips follow [004](../../004-sector-stock-explorer/spec.md); this historical
> roster does not mandate extra visible columns.

Mappings, exact node/listing identities, effective scope, and approval provenance resolve from
the activated manifest-backed files under [feature 010](../../010-manifest-csv-catalogs/spec.md),
not SQL or embedded ETF catalogs. The ETF state table below describes ETF evidence only;
feature 008 explicitly approved baskets have separately labeled alternative identity/momentum.
All active reviewed nodes remain visible, and no basket may be mislabeled as ETF evidence.

## Row identity and mapping

Each industry/sub-industry row contains its reviewed classification name and exact node identity.
The row must display:

1. Classification name
2. Mapped ETF symbol (and name when space permits)
3. Coverage/evidence state
4. Momentum values for the active standard periods when state is `available`

## State contract

| State | ETF identity | Momentum values | Required meaning |
|-------|--------------|-----------------|------------------|
| `available` | Display mapped ETF | Display calculated values | Valid approved mapping and sufficient as-of evidence |
| `insufficient_evidence` | Display mapped ETF | Unavailable | Valid mapping lacks enough history for one or more periods |
| `unavailable_evidence` | Display mapped ETF | Unavailable | Valid mapping has no usable as-of history |
| `not_covered` | Not mapped | Unavailable | No approved appropriate ETF exists |
| `invalid_mapping` | Display invalid symbol when known | Unavailable | Mapping is out of scope, unapproved, or otherwise invalid |

## Invariants

- The displayed ETF must be the same symbol used to calculate every displayed momentum value.
- No value may be inherited from a parent, sector, broad market, stock-member, or other ETF.
- Parent and child rows may show the same ETF only when both approved mappings explicitly name it.
- The selected as-of date applies to mapping validity and all ETF evidence.
