# ETF Universe and Industry Proxy Sources

## Recommended source hierarchy

Use exchange symbol directories to establish that a US-listed ETF exists, then enrich those symbols
from official issuer catalogs. Do not treat an issuer page or aggregator as a complete exchange
universe.

| Priority | Source | Useful fields | Role and constraints |
| --- | --- | --- | --- |
| 1 | [Nasdaq Trader symbol directory](https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs) | Symbol, security name, listing exchange, ETF and test-issue flags | Best free US-listing backbone. Parse `nasdaqlisted.txt` and `otherlisted.txt`, keep `ETF=Y` and exclude test issues. The files are structured and normally refreshed each trading day, but contain no industry classification. |
| 1 | [Cboe listed symbols](https://www.cboe.com/us/equities/market_statistics/listed_symbols/) | Cboe-listed symbols with CSV/XML downloads | Exchange cross-check for Cboe listings. It is not a classification source and the displayed market-statistics fields should not be mistaken for fund fundamentals. |
| 2 | [iShares ETF catalog](https://www.ishares.com/us/products/etf-investments) | Ticker, objective, benchmark, asset class, expense ratio, NAV/AUM, downloadable holdings | Official metadata for iShares sector and industry funds. Product-screener and holdings downloads are preferable to page scraping when their terms permit automated use. |
| 2 | [State Street SPDR fund finder](https://www.ssga.com/us/en/intermediary/etfs/fund-finder) | Ticker, strategy, benchmark, expense ratio, AUM and holdings | Official source for Select Sector and SPDR industry funds. The site has jurisdiction/terms gates, so ingestion must retain the accepted market context and avoid bypassing access controls. |
| 2 | [Vanguard ETF list](https://investor.vanguard.com/investment-products/list/etfs) | Ticker, category, objective, benchmark, expense ratio and portfolio data | Strong official source for broad sector proxies. Vanguard offers fewer narrow industry funds, so it should enrich its own products rather than define the whole industry universe. |
| 2 | [VanEck ETF catalog](https://www.vaneck.com/us/en/investments/etfs/) | Ticker, asset class/style, objective, fees and product documents | Useful official source for specialized industry and thematic funds. The catalog is rendered dynamically; prefer linked fund guides or product data over brittle HTML selectors. |
| 2 | [Global X funds](https://www.globalxetfs.com/funds) | Ticker, theme/category, objective, expense ratio, AUM and holdings | Useful for thematic and emerging-industry candidates. Treat issuer-defined themes as labels that still require mapping to the app taxonomy. |
| 2 | [Xtrackers US](https://etf.dws.com/en-us/) | Ticker, objective, benchmark, fee and holdings documents | Official source for Xtrackers products. Cookie/locale gates and dynamic rendering make downloadable documents safer than crawling page markup. |
| 3 | [Finviz ETF screener](https://finviz.com/screener/etf) | Single category, tags, price, volume and descriptive metadata | Good discovery and cross-check source with broad coverage. Its HTML, pagination, access limits and export entitlements make it unsuitable as canonical truth without a licensed integration. |
| 3 | [Wikipedia US ETF list](https://en.wikipedia.org/wiki/List_of_American_exchange-traded_funds) | Human-curated sector and industry groupings | Useful seed/cross-check only. It explicitly does not guarantee completeness, can be stale, and reuse must comply with CC BY-SA attribution requirements. |
| 4 | justETF | UCITS classifications and European listings | Useful for European/UCITS research, not the canonical source for a US-listed industry universe. |
| 4 | Trading Economics | Macro, country, commodity and market indicators | Valuable for later macro context, but not an ETF catalog or fund-classification source. |

## Representative-proxy policy

Build candidates from exchange-confirmed ETFs and map each fund to a versioned internal industry
taxonomy using the issuer objective, benchmark and holdings. Name matching alone is insufficient.
Exclude inverse, leveraged, option-income, single-stock and defined-outcome products unless a
workflow explicitly asks for them.

Choose a representative proxy deterministically using, in order:

1. Taxonomy and holdings purity for the target industry.
2. Sufficient listing history and complete adjusted-price coverage.
3. Median daily dollar volume and bid/ask liquidity.
4. Assets under management and closure risk.
5. Expense ratio, tracking difference and concentration.
6. Stable ticker ordering as the final tie-breaker.

Common seed candidates include `XBI` for biotechnology, `SOXX` for semiconductors, `IGV` for
software, `ITA` for aerospace and defense, `IYT` for transportation, `XHB` for homebuilders, `KRE`
for regional banks, `OIH` for oil services, and `XME` for metals and mining. These are candidates,
not hard-coded winners; the dated selection record must explain why each proxy was chosen.

## Refresh and local storage

Keep reference metadata separate from price history:

- Refresh exchange symbol files daily after the listing directories update.
- Refresh product metadata weekly; refresh holdings daily only when holdings purity is recalculated.
- Fetch adjusted daily prices from the explicitly selected provider after the latest completed
  session. `yfinance` remains the default personal-use source and must never be silently replaced.
- Store canonical tables as Parquet with a JSON manifest containing source URL/provider, retrieval
  timestamp, normalized request, schema version, coverage and SHA-256 checksum.
- Publish immutable generation directories and atomically replace a small `CURRENT` pointer. A
  failed refresh therefore leaves the prior valid generation readable.
- Use request fingerprints for exact cache identity. `force=True` bypasses reads but publishes only
  after a complete successful write.

SQLite is unnecessary at the present scale: the workload reads whole time-series slices and rarely
updates individual rows. Parquet is smaller and type-preserving, while JSON keeps provenance and
integrity checks inspectable. Reconsider DuckDB or SQLite only when the application needs ad hoc
cross-fund queries, concurrent writers, or incremental row-level updates.