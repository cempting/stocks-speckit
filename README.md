# stocks-speckit
SDD + Python = Awesome App for Stock Screening

## Catalog direction and implementation status

[Feature 010: Manifest-managed CSV catalogs](specs/010-manifest-csv-catalogs/spec.md) is the
accepted catalog architecture. The file-release foundation and lifecycle CLI are implemented;
the application/review/migration cutover is **not yet complete**:

- Files only for catalogs, classification, representation, membership, research, and review/audit
  records; no regional catalog SQLite dependency after migration.
- One stock CSV per region, with exact industry references; reviewed hierarchy supplies
  industry-to-sector and optional sub-industry-to-industry links.
- Reviewed sector, industry, and sub-industry ETF CSVs, plus benchmark/listing evidence and one
  manifest consolidating all relevant source roles.
- No embedded production ETF/stock/benchmark lists, automatic approvals, or parent substitutions.
  Existing explicit basket governance, effective dates, verification, and provenance are retained.
- Validate and activate coherent releases, reject invalid references/changed source identities,
  reuse unchanged validated data, and safely reconcile/export legacy records before cutover.

The existing [sector ETF CSV](.data/sector-etf-representations.csv) has blank classification
references: it is listing evidence, not an automatically approved GICS mapping file.
See the [cross-feature authority map](specs/README.md) for alignment of all earlier specifications.
Remaining work is tracked in [feature 010 tasks](specs/010-manifest-csv-catalogs/tasks.md).

**Current runtime remains pre-cutover.** The commands below operate the implemented regional
database/research workflow. Embedded sector/benchmark and legacy catalog code still requires the
010 refactor. Do not assume these commands publish a manifest release or that documentation
alignment has migrated any data.

### Isolated file-release administration

These new commands validate and publish registered files without initializing a database:

```bash
uv run python -m market_leadership.universe_admin catalog-init \
  --directory .data/catalog-validation
uv run python -m market_leadership.universe_admin validate-catalog \
  --release-manifest tests/fixtures/catalogs/reviewed-us/manifest.json
uv run python -m market_leadership.universe_admin activate-catalog \
  --manifest .data/catalog-validation/CURRENT.json \
  --release-manifest tests/fixtures/catalogs/reviewed-us/manifest.json \
  --expected-release none
```

The fixture is synthetic test evidence: never activate it into the production store.
`--manifest` overrides `MARKET_CATALOG_MANIFEST_PATH`, then `.data/catalog/CURRENT.json`.
Validation is read-only and reports a recomputed catalog revision; activation copies captured
inputs, retains ledger history, and assigns the published identity/revision under a writer lock.
Every subsequent activation requires the exact active release ID and the prior ledger byte prefix.
Published files must not be edited; use a new authoring candidate instead.

`recover-catalog` requires a known reviewed release checksum and the current raw entry checksum.
Recovery retains known valid history; if a valid entry identifies a newer damaged release, restore
that release's reviewed backup rather than silently discard its ledger. An uncertain commit returns
exit 2 with `publication_state=unknown` and operation identity: inspect the selected entry and
retained releases before retrying. See the [lifecycle contract](specs/010-manifest-csv-catalogs/contracts/catalog-cli.md).

Both Streamlit tabs now consume one integrity-checked catalog snapshot per root rerun.
Reviewed scope/version/date, explicit ETF/basket representations and purpose-specific benchmark
listings determine requests; missing or invalid active catalog data fails closed without a database
or embedded-symbol fallback. Unaffected selections and raw provider evidence remain reusable.
Governed review commands and migration/legacy retirement remain separate, unfinished phases.
No real database export, production activation, or package-version cutover has been performed.

## Local configuration

Copy the tracked environment template and set deployment-specific paths only in the ignored
local file. Catalog approval comes from reviewed source records, not arbitrary environment strings:

```bash
cp .env.example .env
```

`yfinance` is the application's only runtime market-data source and does not require an API key.
Live responses are persisted under `.cache/market-data` by default; set
`MARKET_DATA_SOURCE_CACHE_PATH` to use another local directory. Never commit `.env`.

## Run locally

```bash
uv sync
uv run streamlit run streamlit_app.py
```

The tabs require a valid selected catalog entry. For isolated testing, select an already published
disposable entry explicitly, without activating or replacing the deployment's data:

```bash
MARKET_CATALOG_MANIFEST_PATH=/absolute/path/to/disposable/CURRENT.json \
  uv run streamlit run streamlit_app.py
```

## Live Discovery

The root app contains exactly two tabs: **Discovery** and **Industry Deep-Dive**.
Discovery uses one fail-closed yfinance request path; it does not offer fixture,
snapshot, acceptance, weekly-leadership, or provider-selection controls.

1. Select an as-of date and refresh live Discovery data when needed.
   The clickable icon to the right of **Refresh data** shows a moon in bright mode
   and a sun in dark mode, indicating the mode it will activate. It changes both tabs,
   including charts and return colors, and retains the chosen mode across session reruns.
2. Compare sector outcomes, then compare the industry's one-week, one-month,
   three-month, six-month, and 12-month trends across one or more parent sectors.
   Return cells use a gain/loss color scale.
3. Select an eligible industry to inspect its own price, moving-average, trend, and
   official-session volume evidence. These displays are historical, not forecasts.
4. Open Industry Deep-Dive to inspect reviewed dated membership and retain only
   stock selections valid for the active catalog, sector, and industry.

Use Discovery's `Region sectors > Sector > Industry > Stock` breadcrumbs to return to an
earlier tape. Ancestor links clear only descendant selections and preserve the region, date,
thumbnail period, and performance basis. Returning to the stock list also retains loaded peer scores.
Click a sector name to open its industry momentum list, then an industry name to open its stock
list. Industry Status, Representation, and Representation type are in name-button tooltips instead
of separate columns; ETF remains visible. Sector Status is likewise available in the
sector-name tooltip instead of a separate column.

Each industry/sub-industry uses an effective reviewed ETF or, where no ETF is approved,
an explicitly reviewed stock-basket alternative. Missing, invalid, or insufficient
representation evidence stays visible; the app never substitutes sector data or fabricated returns.

### Reviewing industry coverage (current pre-cutover workflow)

Run `uv run python -m market_leadership.universe_admin init` to initialize or upgrade the
regional database to schema 3. The atomic additive migration supports schema 1/2 and preserves
existing memberships, ETF mappings, baskets, approval references, and universe revision.
Back up the database before upgrading. Older application versions cannot read schema 3.

The worklist lists **all active database hierarchy nodes**, including those with no stock
memberships. It does not infer or bundle a complete GICS hierarchy. Import/register reviewed
classification evidence before assessing completeness.

```bash
uv run python -m market_leadership.universe_admin review-representations \
  --region US --classification YOUR_CLASSIFICATION --as-of 2026-10-30
# Add --uncovered-only to show only missing or invalid representations.

uv run python -m market_leadership.universe_admin review-listings \
  --region US --as-of 2026-10-30
# Use these reviewed listing IDs when defining basket constituents.

uv run python -m market_leadership.universe_admin approve-etf \
  --region US --classification YOUR_CLASSIFICATION --entity-id YOUR_NODE \
  --exchange NASDAQ --symbol YOUR_REVIEWED_ETF --source-id YOUR_SOURCE \
  --approval-reference YOUR_REVIEW --effective-from 2026-10-30

uv run python -m market_leadership.universe_admin approve-basket \
  --region US --classification YOUR_CLASSIFICATION --entity-id YOUR_NODE \
  --name "Reviewed specialist basket" --source-id YOUR_SOURCE \
  --approval-reference YOUR_REVIEW --effective-from 2026-10-30 \
  --constituent YOUR_LISTING_ID_A=60 --constituent YOUR_LISTING_ID_B=40
```

ETF suitability and basket membership require human review; these commands do not search online
or infer suitability from names. Symbols/listings must already be imported as verified evidence
for the intended region. Source and approval must match an existing reviewed local import.
Use `--effective-to` for bounded evidence; all listings and hierarchy nodes must cover the entire
approved period. Basket weights are stored as decimal percentages and must total **exactly 100%**.
A basket cannot be approved over an effective ETF period; a later approved ETF takes precedence.

Use `review-node` with `--sector-id`, `--entity-id`, `--name`, and the same review/date arguments
to register an industry without members. Add `--parent-industry-id` for a sub-industry; its parent
must belong to the same sector/classification. Sub-industries share the existing industry-node
storage and selection boundary, with explicit node type and parent metadata.

Basket momentum is the sum of approved weight fractions times constituent returns for each
period, not an inferred fund return. All constituent histories must be complete and aligned.
Weights are never renormalized around missing evidence. Basket price/volume charts are not
fabricated: the table labels the basket and shows unavailable charts.

### Discovering ETF candidates from local projects (current pre-cutover workflow)

Local discovery reads selected literal industry catalogs in these four roots:

- `~/Documents/learn/invest_screener/sector_rotation`
- `~/Claude/Projects/SectorStockScreener/Analyzer`
- `~/Claude/Projects/SectorStockScreener/stockviewer`
- `~/Claude/Projects/SectorStockScreener/stockfinder`

It never imports/executes those projects, searches recursively, requests market data, or collects
unrelated configuration, credentials, portfolios, or watchlists. Duplicate declarations retain
their locations and source evidence. Collection requires an initialized schema 3 database but
does not require an imported hierarchy.

```bash
uv run python -m market_leadership.universe_admin collect-etf-candidates

uv run python -m market_leadership.universe_admin review-etf-candidates \
  --region US --classification YOUR_CLASSIFICATION --as-of 2026-10-30

uv run python -m market_leadership.universe_admin review-etf-candidate \
  --candidate-id RETURNED_CANDIDATE --collection-run RETURNED_RUN \
  --region US --classification YOUR_CLASSIFICATION --entity-id YOUR_NODE \
  --as-of 2026-10-30 --decision accept --reason "Actual scope and suitability assessment" \
  --review-reference YOUR_RESEARCH_REVIEW --evidence-id RETURNED_OCCURRENCE \
  --confirm-etf-identity --confirm-exact-scope --confirm-suitability \
  --issue-resolution RETURNED_ISSUE="Actual assessment resolving this warning"
```

Use returned IDs, and repeat `--evidence-id` and `--issue-resolution` as needed for the selected
evidence and every applicable issue shown in the worklist. The review date is an explicit hierarchy
date, not inferred from when the source file was observed. Research acceptance does **not** approve
a listing, source, or runtime representation. Add `--candidate-review-id RETURNED_REVIEW` to the
existing `approve-etf` command only after its normal source/listing/date prerequisites are met.
The representation and retained local provenance are linked in the same transaction, including
when the mapping already exists.

Commands return versioned JSON for research, with diagnostics on stderr. A missing stockviewer
root makes default collection **partial (exit 2)**, not complete success; readable evidence is
retained. Correct a root with `--root stockviewer=/actual/project` and explicitly select its
supported catalog with `--catalog stockviewer=config.py:INDUSTRY_ETFS`, using the actual path.
No substitute directory or catalog is invented.

Candidates, unresolved labels, conflicting tickers, and proxy warnings do not increase approved
coverage. Every active reviewed industry/sub-industry stays visible, including gaps. Recollection
never changes existing ETF/basket mappings or momentum, and unchanged inputs reuse evidence.
Changed, removed, newly conflicting, or unobservable reviewed support blocks new provenance-linked
approval until resolved; missing inputs are unknown rather than proof of removal. Currentness
means the latest **persisted observation**, whose timestamp is displayed, not real-time verification.

See the [local ETF validation guide](specs/009-local-etf-discovery/quickstart.md) for isolated,
test-only examples and migration/rollback scenarios.

### Experimental provider-label catalog (legacy research input)

The optional experimental catalog merges refreshed S&P 500, Russell 2000,
NASDAQ, and NYSE universe files from another local workspace. It preserves
source priority and conflicts, but it is **not GICS** and never selects a stock
proxy or a market-cap band without dated classification and capitalization
evidence. Generate it with:

```bash
uv run python -m market_leadership.infrastructure.experimental_universe_catalog \
  --sp500 ~/Documents/learn/invest_screener/sector_rotation/ticker_universes/sp500.csv \
  --russell2000 ~/Documents/learn/invest_screener/sector_rotation/ticker_universes/russell2000.csv \
  --nasdaq ~/Documents/learn/invest_screener/sector_rotation/ticker_universes/nasdaq.csv \
  --nyse ~/Documents/learn/invest_screener/sector_rotation/ticker_universes/nyse.csv \
  --output .data/experimental-us-industry-catalog.json
```

Set `EXPERIMENTAL_UNIVERSE_CATALOG` to use another generated catalog path.
This separate configuration/output is not post-cutover catalog authority. Under feature 010,
retain useful candidates only through registered research inputs and exact manual review; do not
relabel provider labels as approved GICS or infer classifications from source priority.

### Industry momentum representations

The following historical research examples are **not an approved catalog, a GICS crosswalk, or
production seeds**. Current industry momentum uses effective reviewed representations; feature
010 moves mappings/listings and approvals into manifest-registered files. Do not copy this table
into runtime constants or infer approval from its labels. See the
[ETF source guide](specs/001-market-leadership-screener/etf-universe-sources.md) and
[local discovery specification](specs/009-local-etf-discovery/spec.md) for review context.

| Industry | Parent sector | ETF | Issuer description |
| --- | --- | --- | --- |
| Aerospace & Defense | Industrials | ITA | [iShares U.S. Aerospace & Defense ETF](https://www.ishares.com/us/products/239502/ishares-us-aerospace-defense-etf) |
| Airlines | Industrials | JETS | [U.S. Global Jets ETF](https://www.usglobaletfs.com/funds/jets/) |
| Banks | Financials | KBE | [SPDR S&P Bank ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-bank-etf-kbe) |
| Broker-Dealers | Financials | IAI | [iShares U.S. Broker-Dealers & Securities Exchanges ETF](https://www.ishares.com/us/products/239771/ishares-us-broker-dealers-securities-exchanges-etf) |
| Capital Markets | Financials | KCE | [SPDR S&P Capital Markets ETF](https://www.ssga.com/us/en/intermediary/etfs/funds/spdr-sp-capital-markets-etf-kce) |
| Cloud Computing | Information Technology | SKYY | [First Trust Cloud Computing ETF](https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker=SKYY) |
| Copper Miners | Materials | COPX | [Global X Copper Miners ETF](https://www.globalxetfs.com/funds/copx/) |
| Cybersecurity | Information Technology | CIBR | [First Trust Nasdaq Cybersecurity ETF](https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker=CIBR) |
| Regional Banks | Financials | KRE | [SPDR S&P Regional Banking ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-regional-banking-etf-kre) |
| Biotechnology | Health Care | IBB | [iShares Biotechnology ETF](https://www.ishares.com/us/products/239699/ishares-biotechnology-etf) |
| Health Care Providers | Health Care | IHF | [iShares U.S. Healthcare Providers ETF](https://www.ishares.com/us/products/239510/ishares-us-healthcare-providers-etf) |
| Oil & Gas Exploration | Energy | XOP | [SPDR S&P Oil & Gas Exploration & Production ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-oil-gas-exploration-production-etf-xop) |
| Oil & Gas Equipment & Services | Energy | XES | [SPDR S&P Oil & Gas Equipment & Services ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-oil-gas-equipment-services-etf-xes) |
| Energy Infrastructure | Energy | AMLP | [Alerian MLP ETF](https://www.alerian.com/etf/amlp/) |
| Oil Refining | Energy | CRAK | [VanEck Oil Refiners ETF](https://www.vaneck.com/us/en/investments/oil-refiners-etf-crak/overview/) |
| Homebuilders | Consumer Discretionary | XHB | [SPDR S&P Homebuilders ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-homebuilders-etf-xhb) |
| Insurance | Financials | KIE | [SPDR S&P Insurance ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-insurance-etf-kie) |
| Industrial REITs | Real Estate | INDS | [Pacer Industrial Real Estate ETF](https://www.paceretfs.com/inds/) |
| Medical Devices | Health Care | IHI | [iShares U.S. Medical Devices ETF](https://www.ishares.com/us/products/239771/ishares-us-medical-devices-etf) |
| Media | Communication Services | PBS | [Invesco Dynamic Media ETF](https://www.invesco.com/us/financial-products/etfs/product-detail?productId=PBS) |
| Metals & Mining | Materials | XME | [SPDR S&P Metals & Mining ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-metals-mining-etf-xme) |
| Gold Miners | Materials | GDX | [VanEck Gold Miners ETF](https://www.vaneck.com/us/en/gdx/) |
| Silver Miners | Materials | SIL | [Global X Silver Miners ETF](https://www.globalxetfs.com/funds/sil/) |
| Mortgage REITs | Real Estate | REM | [iShares Mortgage Real Estate Capped ETF](https://www.ishares.com/us/products/239667/ishares-mortgage-real-estate-capped-etf) |
| Pharmaceuticals | Health Care | XPH | [SPDR S&P Pharmaceuticals ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-pharmaceuticals-etf-xph) |
| Retail | Consumer Discretionary | XRT | [SPDR S&P Retail ETF](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-retail-etf-xrt) |
| Semiconductors | Information Technology | SOXX | [iShares Semiconductor ETF](https://www.ishares.com/us/products/239705/ishares-phlx-semiconductor-etf) |
| Software | Information Technology | IGV | [iShares Expanded Tech-Software Sector ETF](https://www.ishares.com/us/products/239771/ishares-expanded-techsoftware-sector-etf) |
| Steel | Materials | SLX | [VanEck Steel ETF](https://www.vaneck.com/us/en/investments/steel-etf-slx/) |
| Telecommunications | Communication Services | XTL | [SPDR S&P Telecom ETF](https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-telecom-etf-xtl) |

### Live membership gate

There is no fixture membership mode in the application. Before activating or hosting
member results, review provider display/derived-data rights and membership provenance/
coverage. No reviewed live catalog is bundled.

The implemented regional explorer reads reviewed database membership; the earlier independent
`STOCK_MEMBERSHIP_CATALOG` JSON setup is not its source of authority. Use the current reviewed
import/approval workflow above before cutover. After feature 010, both tabs must consume the same
validated manifest-backed regional stock/hierarchy release. Matching approval strings alone never
grant source or display rights. Missing, out-of-period, invalid, or unreviewed membership stays blocked.

## Development checks

`uv sync` includes development-only pandas, PyArrow, and JSON Schema stubs.
Narrow typed integration boundaries cover incomplete upstream annotations;
strict Pyright checks remain enabled.

```bash
uv run ruff check src tests
uv run pyright
uv run pytest -q tests/app tests/integration tests/contract tests/unit -m "not live"
```

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io), create an app from the repository.
3. Set the entrypoint to `streamlit_app.py` and the Python version to `3.12`.
4. Deploy. Community Cloud detects `uv.lock` and installs the project and its dependencies with
	`uv`.

The yfinance market-data provider needs no secret. For the current pre-cutover app, provision
the reviewed regional database at a readable deployment path; set `MARKET_UNIVERSE_DATABASE_PATH`
when it differs from `.data/market-universe.sqlite`. Ignored local data is not provisioned by
pushing code, and a clean deployment must not silently seed it. Feature 010 will replace this
catalog setup with the reviewed file release and manifest after implementation; its exact
configuration/migration contract remains to be planned. Do not commit `.streamlit/secrets.toml`
or any credentials.