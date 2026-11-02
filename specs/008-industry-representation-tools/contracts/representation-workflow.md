# Representation Workflow Contract

**Active owner (2026-11-02)**: [Feature 008](../spec.md), incorporating former feature 007's
exact-ETF momentum and evidence states. [004](../../004-sector-stock-explorer/spec.md) owns the
consuming row layout/tooltips. [012](../../012-stock-industry-memberships/spec.md) separately
requires reviewed applicability before old approvals are reused in a new custom scope.

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
| Invalid mapping | Known representation identity and actionable reason | None |
| Insufficient evidence | Approved representation identity; insufficient-history reason | None for affected periods |
| Unavailable evidence | Approved representation identity; unavailable-history reason | None for affected periods |

Review records require region, classification, node, source, approval reference, and effective
dates. Baskets additionally require verified active constituents with weights totaling 100%.
Missing basket histories cannot be silently reweighted, and traded-fund price/volume charts
must not be fabricated for a basket. Optional research failure does not imply approval or
invalidate unrelated complete approved source evidence.

Each ETF row identifies the same approved fund used for its momentum. Parent/descendant nodes
are independently reviewed even when using one ETF. The as-of date governs scope, effective
approval, listings, and observations consistently. No parent/sector/broad-market/arbitrary
instrument substitutes for a missing or invalid representation. No approval remains distinct
from an approved fund without usable history. Every active reviewed node remains discoverable,
including empty/uncovered nodes; altered required sources never silently retain unchecked mappings.
