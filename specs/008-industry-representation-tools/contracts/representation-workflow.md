# Representation Workflow Contract

Worklists and approval records use one manifest-backed file release under
[feature 010](../../010-manifest-csv-catalogs/spec.md), without a catalog database.
Exact region/classification/version/node/listing identities, source approvals, and full effective
periods must agree. Publish mapping/basket and governance/provenance coherently; conflicts/failure
leave no partial approval. Basket constituents reference reviewed listings in the same scoped
sources, not embedded stock lists. Migration retains or explicitly quarantines historical evidence.

| Status | Display | Momentum source |
|---|---|---|
| ETF | ETF symbol and `ETF` | Approved active ETF only |
| Basket | Basket name and `Stock basket alternative` | Approved weighted constituents only |
| Not covered | `Not covered` | None |
| Invalid/insufficient | Representation identity and state | None |

Review records require region, classification, node, source, approval reference, and effective
dates. Baskets additionally require verified active constituents with weights totaling 100%.
Missing basket histories cannot be silently reweighted, and traded-fund price/volume charts
must not be fabricated for a basket. Optional research failure does not imply approval or
invalidate unrelated complete approved source evidence.
