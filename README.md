# Stocks Speckit

A Streamlit application for exploring US market leadership by sector and industry.

## Status

The current app reads a locally published, reviewed file catalog and fetches live
market observations from yfinance when requested. A separately deployable
`market-structure` service and persistent observation cache are being implemented
([Feature 013](specs/013-market-structure-service/spec.md)). They are **not ready to
run**. The app does not yet consume that service.

There is no bundled production US universe and no command that automatically
discovers, classifies, or approves the US market. You must prepare and review the
catalog inputs described below. The small catalog under
[`tests/fixtures/catalogs/reviewed-us/`](tests/fixtures/catalogs/reviewed-us/) is
synthetic test data only; it is not suitable for production or live data requests.

## Prepare and run locally

### 1. Install

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/).

From the repository root:

```bash
uv sync --all-packages
```

### 2. Prepare a reviewed catalog

Prepare a release directory containing a manifest and its registered CSV/JSONL
artifacts. A usable catalog needs reviewed US region/classification metadata,
hierarchy, stock memberships and listings, ETF listings and mappings, benchmarks,
and governance/audit records. Do not invent approvals or infer classifications from
company names or provider labels.

The [catalog file contract](specs/010-manifest-csv-catalogs/contracts/catalog-files.md)
defines the CSV fields and validation rules. First validate your candidate:

```bash
uv run market-catalog validate-catalog \
  --release-manifest /absolute/path/to/your-release/manifest.json
```

After you have reviewed the validation result, initialize a local catalog store and
publish the candidate. For its first release, use `none`; for later releases, pass the
currently active release ID as `--expected-release`.

```bash
uv run market-catalog catalog-init --directory .data/catalog

uv run market-catalog activate-catalog \
  --manifest .data/catalog/CURRENT.json \
  --release-manifest /absolute/path/to/your-release/manifest.json \
  --expected-release none
```

Activation revalidates and copies the registered inputs into an immutable release.
Do not edit files under published releases. Author and validate a new candidate,
then activate it against the current release ID. See the
[catalog CLI guide](specs/010-manifest-csv-catalogs/quickstart.md) for lifecycle
details.

### 3. Start the app

```bash
uv run streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. The default catalog entry is
`.data/catalog/CURRENT.json`. To use another entry, set
`MARKET_CATALOG_MANIFEST_PATH`, for example:

```bash
MARKET_CATALOG_MANIFEST_PATH=/absolute/path/to/CURRENT.json \
  uv run streamlit run streamlit_app.py
```

The app has **Discovery** and **Industry Deep-Dive** tabs. It needs a valid catalog
entry to show the reviewed structure. Use the UI's refresh/load actions to request
market data; yfinance does not require an API key. Stop the app with Ctrl-C in the
terminal.

For a UI-only smoke test, you may point the app at the synthetic test manifest:

```bash
MARKET_CATALOG_MANIFEST_PATH="$PWD/tests/fixtures/catalogs/reviewed-us/manifest.json" \
  uv run streamlit run streamlit_app.py
```

This fixture is incomplete and synthetic. Do not use it to request live prices or as
a production catalog.

## Local configuration and data

The app loads `.env` if present. Catalog selection defaults to
`.data/catalog/CURRENT.json`; `MARKET_CATALOG_MANIFEST_PATH` overrides that path.
`MARKET_DATA_CACHE_PATH` sets the local market-data cache (default
`.cache/market-data`), and `MARKET_DATA_SOURCE_CACHE_PATH` can set a separate source
cache (defaults to the same location). `MARKET_DATA_RETRY_LIMIT` defaults to `2`.
These paths are local runtime data, not catalog authority.

Do not commit `.env`, credentials, published/private data, or caches. yfinance is
the current runtime market-data provider and needs no key. The Massive adapter is
not enabled by the current app configuration.

## Current ownership

| Component | Responsibility |
|---|---|
| `market_leadership` | Streamlit UI, application logic, live acquisition, app caches |
| `market_data` | Shared domain models, validation, schemas, catalog and issuer-evidence stores |
| `market_data_tools` | Offline catalog and evidence administration |
| `market_structure` | Planned independent HTTP service; publication and serving are not implemented |

The app, shared library, and service/tools are separate workspace distributions.
Install all of them for development with `uv sync --all-packages`. The app imports
shared contracts, not the service or maintenance tools. To use the app's optional
legacy administration delegates, install the `maintenance` extra.

## Development checks

```bash
uv run ruff check src packages services tests
uv run pyright
uv run pytest -m "not live" -q
```

The live-marked tests are excluded by that pytest command to avoid external data
requests.

## Further reading

- [Feature specifications](specs/README.md)
- [Market-structure service design and current implementation status](specs/013-market-structure-service/quickstart.md)
- [Catalog file format](specs/010-manifest-csv-catalogs/contracts/catalog-files.md)
- [Catalog administration commands](specs/010-manifest-csv-catalogs/contracts/catalog-cli.md)
