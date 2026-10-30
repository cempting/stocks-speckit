# stocks-speckit
SDD + Python = Awesome App for Stock Screening

## Local configuration

Copy the tracked environment template and set the reviewed membership evidence only in the ignored
local file:

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

## Live Discovery

The root app contains exactly two tabs: **Discovery** and **Industry Deep-Dive**.
Discovery uses one fail-closed yfinance request path; it does not offer fixture,
snapshot, acceptance, weekly-leadership, or provider-selection controls.

1. Select an as-of date and refresh live Discovery data when needed.
2. Compare sector outcomes, then compare the industry's one-week, one-month,
   three-month, six-month, and 12-month trends across one or more parent sectors.
   Return cells use a gain/loss color scale.
3. Select an eligible industry to inspect its own price, moving-average, trend, and
   official-session volume evidence. These displays are historical, not forecasts.
4. Open Industry Deep-Dive to inspect reviewed dated membership and retain only
   stock selections valid for the active catalog, sector, and industry.

Each industry uses a documented US industry ETF representation. Missing or
insufficient representation history remains visibly insufficient; the app never
substitutes sector data or fabricated returns.

### Experimental provider-label catalog

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

### Industry momentum representations

The live momentum table uses the following focused US industry ETFs. Broad-sector
and multi-industry thematic funds are deliberately excluded rather than being
shown as a single industry.

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

Set `STOCK_MEMBERSHIP_CATALOG` to a local JSON catalog and
`FUNDAMENTAL_DISPLAY_APPROVAL` to its reviewed `approval_reference`. These values
record an actual review; arbitrary matching strings do not grant display rights.
The catalog must declare schema version 1, US market, live evidence mode, source,
observation date, coverage, approval reference, and dated stock entries with stable
instrument/company identifiers. A current reviewed catalog is required; historical,
invalid, or unverified membership remains blocked.

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

The yfinance market-data provider needs no secret. Configure only the reviewed
`STOCK_MEMBERSHIP_CATALOG` path and matching `FUNDAMENTAL_DISPLAY_APPROVAL` in the
deployment environment. Do not commit `.streamlit/secrets.toml` or any credentials.