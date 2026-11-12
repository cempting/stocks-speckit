# Quickstart: US Industry and Theme ETF Discovery

## Prerequisites

- Python `>=3.12,<3.13` and the repository's existing locked dependencies.
- A validated catalog entry containing the US classifications, listings, representations, and all
  required release artifacts.
- Real source, approval, suitability, benchmark, stock-artifact, and audit evidence. The current
  files under `docs/markets/US/` are candidate inputs only and are not sufficient to activate a
  release on their own.
- For live provider verification only: network access permitted for yFinance and
  `RUN_LIVE_MARKET_DATA=1`.

## Offline validation

Run focused catalog, calculation, and UI tests:

```bash
uv run pytest \
  tests/contract/test_catalog_v2.py \
  tests/integration/test_discover_sectors.py \
  tests/app/test_discovery.py \
  tests/app/test_progressive_tabs.py
```

The planned coverage must verify:

- Single-classification releases retain the current UI behavior.
- Multiple active US classifications require an explicit selection and never mix scopes.
- Parent changes clear dependent selections; child nodes follow exact hierarchy relationships.
- Multiple approved ETFs per node remain separately visible and preserve their own status.
- One missing history does not remove other valid results in a partial response.
- Invalid source evidence or an incomplete release cannot replace the active catalog.
- ETF mappings do not produce contained-stock memberships.

Run repository quality checks after implementation:

```bash
uv run ruff check packages/market-data/src/market_data src/market_leadership tests
uv run pyright
```

## Browser validation

Start the application using a reviewed catalog entry:

```bash
MARKET_CATALOG_MANIFEST_PATH=/absolute/path/to/CURRENT.json \
  uv run streamlit run streamlit_app.py --server.headless true --server.port 8504
```

At 1440px and 390px viewport widths, select each active US classification, navigate sector,
industry, and sub-industry levels where present, and inspect every ETF option and its data
availability. Change the classification and parent selection to confirm that stale descendants
are removed. Confirm that Industry Deep-Dive remains usable when more than one classification is
active and that the four existing root tabs are unchanged.

Expected result: each category is shown only in its exact scope; every representation is either
usable or has a specific unavailable state; missing stock membership is not inferred.

## Opt-in live ETF retrieval

After a complete, approved catalog release is available, check all active mapped ETF provider
symbols against the current yFinance path:

```bash
RUN_LIVE_MARKET_DATA=1 \
MARKET_CATALOG_MANIFEST_PATH=/absolute/path/to/CURRENT.json \
  uv run pytest -m live tests/live/test_us_catalog_etf_retrieval.py -q
```

This network check is intentionally excluded from ordinary CI. It must report each exact
`ProviderSymbol`, whether usable daily close/volume history was returned, and the observed date
coverage. Review unavailable symbols and data rights before publishing results; do not switch
providers or guess replacement symbols.
