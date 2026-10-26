---
id: A01
title: Market Structure & Instruments
context: CTX-A
layers: [CORE, METHOD]
status: draft
sources: [S03, S04, S05, S07, S08, S09, S12, S13, S14, S15, S17, S19, S21, S23, S25, S28, S29, S30]
decisions: [D-C14, D-C15b, D-C21, D-C26, D-C28, D-OPEN-3, D-S14, D-R16, D-R20, D-R21, D-R24, D-R39, D-R40, D-R42, D-R43, D-DEF-01]
depends_on: []
---
# A01 — Market Structure & Instruments

## 1. Purpose & scope
Defines the neutral market-data foundation every other aspect builds on:
- Markets, exchanges, trading calendars, currencies and FX conversion.
- The per-market classification scheme (GICS for all markets, D-R42) and the invariant Market → Industry hierarchy → Company.
- The `IndustryProxy` of every classification node: the ETF, index or equal-weight basket that makes each industry chartable and filterable (D-R20, D-R21).
- Benchmarks per market (local currency) plus the global USD benchmark (D-C15b, D-R42); liquidity floors for instruments and proxies (D-R43).
- Instrument types: stocks, ETFs/UCITS/index funds, ETCs, indices, bonds (structure only), futures, options, crypto, bullion; gold exposure forms.
- Order types and their execution semantics (market, limit, stop, buy-stop, trailing stop).

Excluded (owned elsewhere): RS/scoreboard computation (A02), volume analysis (A04), fund/stock *selection* and custom-basket construction (A05), entry levels (A06), stop placement and exit precedence (A07), sizing and the overnight-gap test (A08), exposure and cash-like classification (A09), bond analytics (A10), gold/currency theses (A11), the S14 instrument restriction (A13).

## 2. Concepts
- [[market]] — top-level container: region, currency, exchanges, benchmark, classification scheme.
- [[classification-scheme]], [[gics]], [[sector]], [[industry]] — per-market hierarchy assigning companies to industry nodes.
- [[industry-proxy]] — one representative instrument or index per node, with its proxy type (D-R21).
- [[benchmark]], [[local-benchmark]], [[global-benchmark]], [[market-index]], [[sp-500]] — reference series for RS (consumed by A02).
- [[cap-weighted-index]], [[equal-weight-index]], [[index-inclusion-effect]] — index construction and its flow effects.
- [[financial-instrument]], [[asset-class]], [[stock]], [[exchange-traded-fund]], [[ucits]], [[index-fund]], [[sector-etf]], [[thematic-etf]], [[leveraged-etf]], [[exchange-traded-commodity]], [[futures-contract]], [[option]], [[bitcoin]], [[bullion]], [[spot-price]] — instrument taxonomy.
- [[expense-ratio]], [[fund-size]], [[isin-domicile]], [[withholding-tax]], [[tax-wrapper]], [[nav-discount]], [[liquidity]], [[market-capitalization]] — fund/instrument attributes.
- [[order]], [[market-order]], [[market-on-open-order]], [[limit-order]], [[buy-stop-order]], [[stop-loss-order]], [[trailing-stop]], [[broker]] — order model; stop placement rules live in A07.
- [[extended-hours-trading]], [[trading-halt]], [[gap]] — conditions under which orders do not execute as planned.
- [[long-position]], [[short-selling]], [[ipo]] — position direction and listing events.

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Market | id | string | unique, e.g. `US`, `UK`, `EU`, `DE`, `JP`, `KR`, `CN`, `AU`, `CA`, `IN` | |
| | region | enum | | |
| | base_currency | ISO 4217 | required | local-currency view of A02 |
| | exchanges | Exchange[] | ≥1 | |
| | classification_scheme | ClassificationScheme | exactly 1 active | D-C14 |
| | local_benchmark | Benchmark | required | D-C15b |
| | trading_calendar | TradingCalendar | required | market-closed days for D-C28 |
| Exchange | mic | string | unique | |
| | market | Market | exactly 1 | |
| | timezone | IANA tz | required | |
| | regular_session | time range | required | official close = daily close |
| | extended_sessions | time range[] | optional | pre-market / after-hours |
| TradingCalendar | trading_days, holidays, half_days | date sets | per exchange | |
| FxRate | base, quote, close, as_of | decimal, date | same-date use (R-A01-016) | new entity |
| ClassificationScheme | id, name, version, effective_from | string, date | | GICS, or other per market |
| | levels | ordered list | ≥1; level 1 = sector-equivalent | GICS: sector, industry group, industry, sub-industry |
| ClassificationNode | id, scheme, level, name, parent | | parent at next-higher level; root has none | Sector / IndustryGroup / Industry / SubIndustry are nodes of a level (new generic entity) |
| Company | id, name, primary_market | | exactly 1 primary market = market of the primary listing; governs scheme node and benchmark (R-A01-048) | D-R42 |
| | classification | node per level | exactly 1 primary node per level, one chain | revenue-based (S19) |
| Instrument | id, ticker, exchange, isin?, name | | ticker unique per exchange | |
| | type | enum {Stock, ETF, IndexFund, ETC, Index, Bond, Future, Option, Crypto, Bullion} | exactly 1 | Fund = ETF ∪ IndexFund ∪ UCITS wrapper |
| | trading_currency | ISO 4217 | required | |
| | avg_daily_value_traded | currency/day | ≥0 | [[liquidity]] |
| Stock | company | Company | exactly 1 | |
| | market_cap | currency | ≥0 | |
| | index_memberships | Index[] | | |
| Fund (ETF/IndexFund/ETC) | wrapper | enum {US-ETF, UCITS, ETC, other} | required | |
| | domicile | ISO country | derived from ISIN prefix | IE, LU … |
| | expense_ratio | %/yr | ≥0 | |
| | aum | currency | ≥0 | [[fund-size]] |
| | holdings | (Instrument, weight %, as_of)[] | weights sum ≈100% | look-through (A09) |
| | weighting | enum {cap, equal, other} | | |
| | replication | enum {physical, synthetic, futures} | | futures-based flag |
| | share_class | enum {acc, dist} | | |
| | currency_hedged | bool | | |
| | leverage_factor | decimal | default 1; ≠1 = leveraged/inverse | |
| | covered_node | ClassificationNode? | optional | industry proxy candidate (A02) |
| | redeemable_for_metal | bool | ETC/ETF on metal | S28 |
| | eligible_residences | Market[] | | availability (R-A01-020) |
| Index | id, name, currency, weighting, constituents | | | |
| IndustryProxy (new) | node | ClassificationNode | exactly 1 primary per node and market, every level | D-R20, D-R24 |
| | market | Market | | |
| | proxy_type | enum {ETF, INDEX, EQUAL_WEIGHT_BASKET} | shown wherever the proxy is shown | D-R21 |
| | instrument / index | Fund instrument (ETF) or Index | set for ETF / INDEX | |
| | members | Stock[] with equal weights | ≥ `classification.proxy_basket_min_members` (5), same node; set for EQUAL_WEIGHT_BASKET | D-R21 |
| | selection_rank, purity_pct, avg_daily_value_traded, as_of | int, %, currency/day, date | rank 1 = ETF, 2 = INDEX, 3 = BASKET; ETF purity_pct ≥ `classification.proxy_min_purity_pct` (60) | D-R21, D-R43 |
| | buyable | bool | false for INDEX | A05 |
| Benchmark | index, market?, currency, return_basis | | market null = global | {total_return, price} |
| PriceBar | instrument, date, open, high, low, close, volume, change_vs_prior_close | | close = official regular-session close | |
| IndexEvent | index, date, added, removed, size_estimate | | | S03, new entity |
| BullionItem | form {coin, small_bar, kg_bar}, fine_oz, price, dealer, storage {home, allocated_vault, unallocated} | | | S28, new entity |
| Order | id, instrument, side {buy, sell}, qty, type, trigger_price?, limit_price?, trail?, tif {day, gtc}, linked_order?, status | | see R-A01-035 | |
| Broker | name, supported_order_types, order_semantics, residences, supports_fractional, fractional_increment | -, -, -, -, bool, shares | fractional_increment set iff supports_fractional | S07, S23; D-R40 (A08 R-A08-035) |

Order status lifecycle: `draft → submitted → working → (triggered) → filled | partially_filled | cancelled | expired | rejected`. A stop/buy-stop is `working` until triggered; on trigger it becomes a market (or limit for stop-limit) order.

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `market.local_benchmark` | US: S&P 500; UK: FTSE All-Share; EU: STOXX 600; DE: CDAX; JP: TOPIX; KR: KOSPI; CN: CSI 300; AU: S&P/ASX 200; CA: S&P/TSX Composite; IN: Nifty 500 | any Index of that market | index id | D-C15b, D-R42 |
| `market.global_benchmark` | MSCI ACWI (USD) | MSCI ACWI, MSCI World | index id | D-C15b, S19 |
| `market.base_currency` | US: USD; UK: GBP; EU: EUR; DE: EUR; JP: JPY; KR: KRW; CN: CNY; AU: AUD; CA: CAD; IN: INR | ISO 4217 | — | D-C15b (local currency) |
| `market.benchmark_return_basis` | total_return | {total_return, price} | — | S17, S19 ("total return") |
| `classification.scheme` | GICS (all markets) | GICS | — | D-C14, D-R42; S19 (GICS applied worldwide) |
| `classification.scoreboard_level` | industry (GICS: 74) | {sector, industry_group, industry, sub_industry} | level | D-R24; S19 (74 "practical working level"), S13 (~150) |
| `classification.proxy_selection_order` | ETF > INDEX > EQUAL_WEIGHT_BASKET | fixed | — | D-R21 |
| `classification.proxy_basket_min_members` | 5 | ≥ 5 | members | D-R21 |
| `instrument.min_liquidity.stock_adv_usd` | 5,000,000 | ≥ 5,000,000 (stricter only) | USD-equivalent 20-session average daily traded value | D-R43 |
| `instrument.min_liquidity.etf_aum_usd` | 100,000,000 | ≥ 100,000,000 | USD-equivalent AUM | D-R43 |
| `instrument.min_liquidity.etf_adv_usd` | 2,000,000 | ≥ 2,000,000 | USD-equivalent 20-session average daily traded value | D-R43 |
| `classification.proxy_min_purity_pct` | 60 | ≥ 60 | % of fund holdings in the node | D-R43, D-R21 |

Referenced, not declared here: overnight-gap assumptions per instrument type (A08 `risk.gap_assumed_pct.*`, `risk.gap_max_loss_pct`, D-OPEN-3), bullion premium limit (A11 `macro.gold_premium_max_pct`), weekly review day (A12 `routine.*`, D-C28).

## 5. Rules

### 5.1 Markets, exchanges, calendars
- **R-A01-001** (hard, CORE) — Every Market MUST define base currency, ≥1 Exchange, a trading calendar, exactly one active ClassificationScheme and a local benchmark. _Sources: S19. Decision: D-C14, D-C15b_
- **R-A01-002** (hard, CORE) — Every Exchange MUST belong to exactly one Market and declare timezone and regular session; extended sessions MAY be declared. _Sources: S07, S13_
- **R-A01-003** (hard, CORE) — The daily close used for moving averages, RS and exit tests MUST be the official regular-session close of the listing exchange; extended-hours prints MUST NOT replace it. _Sources: S07 ("pre-market and after-hours activity is NOT reflected in candle color"), S13_
- **R-A01-004** (hard, CORE) — PriceBar MUST expose `change_vs_prior_close` in addition to open/close; up-day/down-day classification (A04) MUST use the change vs prior close, not candle colour. _Sources: S07, S13 ("can gap down 10%, rise 1% intraday, print green")_
- **R-A01-005** (hard, CORE) — Market-closed days MUST be derived from the TradingCalendar; A12 uses them to validate the weekly review day. _Sources: S13, S23. Decision: D-C28_

### 5.2 Classification
- **R-A01-006** (hard, CORE) — Invariant: Market → ClassificationScheme → ordered node hierarchy → Company. No Company may be analysed in a market without a classification in that market's scheme. _Decision: D-C14_
- **R-A01-007** (hard, CORE) — Every market MUST use GICS with levels sector (11), industry group (25), industry (74), sub-industry (163), so that the global view is consistent. _Sources: S19. Decision: D-C14, D-R42_
- **R-A01-008** (hard, CORE) — A market MAY register an additional local scheme as an information view; a scheme is pluggable if it provides ordered levels, nodes with parent links and level 1 as the sector-equivalent. GICS remains the scheme for the scoreboard, exposure and the global view in every market. _Decision: D-C14, D-R42_
- **R-A01-009** (hard, CORE) — Each Company MUST have exactly one primary node at every level of its market's scheme, assigned mainly by revenue. _Sources: S19 ("one primary classification at each level based mainly on revenue")_
- **R-A01-010** (hard, CORE) — A Company's nodes MUST form a single parent chain (the node at level k+1 is a child of its node at level k).
- **R-A01-011** (soft, CORE) — The scoreboard unit is the node level `classification.scoreboard_level`, set per market; A02 consumes it. _Sources: S13, S19_
- **R-A01-012** (soft, CORE) — Classification assignments SHOULD be effective-dated so historical RS series use the membership valid at each date.
- **R-A01-013** (hard, CORE) — The global view MUST NOT treat nodes of different schemes as equivalent unless an explicit mapping exists; with GICS in every market (R-A01-007) no mapping is needed for the canonical views. _Decision: D-C14, D-R42_

### 5.3 Benchmarks & currency
- **R-A01-014** (hard, CORE) — Each Market MUST have a local benchmark in its base currency; all markets share the global benchmark `market.global_benchmark` in USD. _Decision: D-C15b_
- **R-A01-015** (hard, CORE) — A proxy and its benchmark MUST use the same return basis (`market.benchmark_return_basis`); total-return series SHOULD be used where available. _Sources: S17, S19_
- **R-A01-016** (hard, CORE) — Conversion to USD for the global view MUST use the FxRate of the same close date as the price. _Sources: S19 (currency risk)_
- **R-A01-017** (soft, CORE) — A holding whose trading currency differs from the investor's base currency SHOULD be flagged with FX risk; if a currency-hedged share class exists it SHOULD be shown. _Sources: S09, S19_

### 5.4 Instruments
- **R-A01-018** (hard, CORE) — Every Instrument MUST have exactly one type, one listing Exchange, one trading currency and a ticker unique per exchange; ISIN SHOULD be stored when available.
- **R-A01-019** (hard, CORE) — A Stock MUST reference exactly one Company; a Company MAY have several listed instruments.
- **R-A01-020** (hard, CORE) — A Fund MUST NOT be offered as buyable to a user whose residence is not in `eligible_residences`; US-listed ETFs are not eligible for EU/UK retail investors, who use the UCITS equivalent. _Sources: S13 ("Filter by region first"), S21 ("US-listed ETFs like IQLT generally cannot be sold to UK and EU retail investors"), S25_
- **R-A01-021** (soft, CORE) — A UCITS equivalent SHOULD be matched by the tracked index (strategy), not by ticker. _Sources: S21_
- **R-A01-022** (hard, CORE) — Fund `domicile` MUST be derived from the ISIN country prefix (e.g. `IE` = Ireland, `LU` = Luxembourg). _Sources: S21_
- **R-A01-023** (soft, CORE) — For non-US investors, Irish-domiciled UCITS SHOULD be ranked ahead of US-domiciled equivalents for US-source income (withholding 15% vs 30%) and to limit US estate-tax exposure above $60,000; tax facts are dated (as of 2026) and user-overridable. _Sources: S09, S21_
- **R-A01-024** (soft, CORE) — If the user needs no income, the accumulating share class SHOULD be preferred. _Sources: S21_
- **R-A01-025** (hard, CORE) — Leveraged and inverse ETFs (incl. single-stock) MUST carry `leverage_factor ≠ 1`; METHOD and the beginner profile exclude them (A08 no-leverage rule, A13). _Sources: S12, S13 ("no leveraged index funds")_
- **R-A01-026** (soft, CORE) — Futures-based funds MUST set `replication = futures` and SHOULD display a "may diverge from spot" warning. _Sources: S08_
- **R-A01-027** (hard, CORE) — Index and Fund MUST record their weighting (cap vs equal); "diversified" MUST NOT be inferred without holdings and weights. _Sources: S04, S12, S29_
- **R-A01-028** (soft, CORE) — Index additions/removals SHOULD be recorded as IndexEvent; a large addition triggers the review check of A02 R-A02-031. _Sources: S03 (Tesla Dec 2020 ≈ $50B sold of the other 499)_
- **R-A01-029** (hard, METHOD) — A Basket is either a Fund instrument or an equal-weight group of Stocks; all constituents of a custom basket MUST belong to the same ClassificationNode (construction rules in A05). _Sources: S13, S19. Decision: D-C21_
- **R-A01-030** (soft, METHOD) — Canonical METHOD signals generate long positions only; short exposure is not part of canonical rules and, where used, is taken via options. _Sources: S13, S30 ("Rarely... When he does, he uses options")_

### 5.5 Gold exposure forms
- **R-A01-031** (hard, CORE) — Gold exposure MUST be modeled as one of: physical bullion (coin, small bar, kg bar), allocated vault holding, unallocated claim, gold-backed fund (US ETF or EU ETC), futures, or miner equity. Miner equity is a Stock in its own industry, not gold. _Sources: S08, S28, S30_
- **R-A01-032** (hard, CORE) — In EU markets a single-commodity gold product MUST have wrapper `ETC` (UCITS diversification rules exclude it). _Sources: S28 ("the European gold products are not funds at all")_
- **R-A01-033** (hard, CORE) — If the bullion premium of a standard 1-oz coin or bar exceeds A11 `macro.gold_premium_max_pct` (same check as R-A11-042), the item MUST be flagged "walk away" unless marked as a collector piece. _Sources: S28_
- **R-A01-034** (hard, CORE) — Vault storage MUST be `allocated`; an unallocated holding MUST be flagged as an unsecured-creditor claim. _Sources: S28 ("Always choose allocated.")_
- **R-A01-035** (soft, CORE) — A bullion dealer SHOULD be long-established, in the LBMA good-delivery chain, with live pricing and a published buyback price. _Sources: S28_

### 5.6 Orders
- **R-A01-036** (hard, CORE) — Supported order types: market, market-on-open, limit, limit-on-open, sell stop (stop-loss), buy-stop (conditional buy above the market), trailing stop (amount or %); stop-limit MAY be supported if the broker offers it. _Sources: S07, S13, S23, S25. Decision: D-R16_
- **R-A01-037** (hard, CORE) — A triggered stop order MUST be modeled as becoming a market order: the fill price is not guaranteed. For risk calculations the expected fill of a sell stop on a gap is `min(trigger, open)`. _Sources: S23 ("A stop order becomes a market order when triggered"), S25_
- **R-A01-038** (hard, CORE) — Stops MUST NOT be modeled as executing while the market is closed or the instrument is halted; overnight gaps and halts are handled by position size (A08). _Sources: S13 ("Stops do not trigger when the market is closed"), S25. Decision: D-OPEN-3_
- **R-A01-039** (hard, CORE) — A buy-stop triggers when the price trades at or above its trigger price. _Sources: S07_
- **R-A01-040** (soft, CORE) — Orders that implement weekly decisions SHOULD be standing orders (time-in-force GTC or the broker's equivalent) so they execute without the user during the week. _Sources: S13, S23. Decision: D-C26_
- **R-A01-041** (soft, CORE) — The Broker profile SHOULD record each supported order type's real semantics; the app MUST NOT assume a semantics the broker does not offer. _Sources: S23 ("Understand what your broker's order actually does")_
- **R-A01-042** (hard, CORE) — A sell order MAY link to its buy order (`linked_order`) so the "same sitting" rule of A07 can be verified. _Sources: S23, S07_

### 5.7 Industry proxies (round 2, 2026-10-26)
- **R-A01-043** (hard, METHOD) — Every ClassificationNode of an enabled market, at every level (GICS: 11 sectors, 25 industry groups, 74 industries, 163 sub-industries), MUST have exactly one primary `IndustryProxy` so that each node can be charted and filtered. _Decision: D-R20, D-R24_
- **R-A01-044** (hard, METHOD) — The proxy MUST be chosen in the order `classification.proxy_selection_order`: the most liquid pure-play ETF covering the node, else the node's official industry index (S&P, MSCI …), else a computed equal-weight basket of the node's most liquid members. _Decision: D-R21_
- **R-A01-045** (hard, METHOD) — A computed proxy basket MUST hold at least `classification.proxy_basket_min_members` (5) members of the node, equally weighted; a node with fewer eligible members and no ETF or index has no valid proxy: it is shown under its parent node with `data_quality = insufficient` (A02 R-A02-008), its companies are not buy-eligible through that node, and it is re-checked at each monthly review. _Decision: D-R21, D-DEF-01_
- **R-A01-046** (hard, METHOD) — The proxy type MUST be stored and shown with every proxy; an INDEX proxy is a reference series only (not buyable). _Decision: D-R21_
- **R-A01-047** (hard, CORE) — A market-on-open order MUST be modeled as executing in the opening auction of the next session at the opening price, without price guarantee; a limit-on-open order executes there only if the opening price is at or better than its limit, otherwise it expires unfilled. _Decision: D-R16 (exits), D-R03/D-R07 (entries)_

### 5.8 Round-3 additions (2026-10-26)
- **R-A01-048** (hard, CORE) — A company listed in several markets MUST be governed by its primary listing market: that market's GICS node assignment, local benchmark and calendar apply to every listing of the company; secondary listings reference the same Company. _Decision: D-R42_
- **R-A01-049** (hard, CORE) — Liquidity floors (USD equivalent, converted per R-A01-016): a Stock is tradable and usable as a basket member or proxy-basket member only if its 20-session average daily traded value ≥ `instrument.min_liquidity.stock_adv_usd` ($5M); a Fund only if AUM ≥ `instrument.min_liquidity.etf_aum_usd` ($100M) and 20-session average daily traded value ≥ `instrument.min_liquidity.etf_adv_usd` ($2M). Instruments below the floors are shown but not buyable. _Sources: S05, S19 ("most liquid"). Decision: D-R43_
- **R-A01-050** (hard, METHOD) — An industry ETF qualifies as the node's ETF proxy (and as an A05 industry basket) only if at least `classification.proxy_min_purity_pct` (60 %) of its holdings belong to that node; otherwise the next proxy type of R-A01-044 is used. _Decision: D-R43, D-R21_
- **R-A01-051** (hard, METHOD) — Every gold exposure form (R-A01-031) is an instrument of the A06/A07 signal engine; physical bullion and allocated vault holdings cannot carry a live broker stop and use the alert-based exit of A07 R-A07-043. _Decision: D-R39_

## 6. Processes
**PR-A01-01 Market onboarding** — trigger: new market enabled. Steps: (1) register exchanges, sessions and calendar; (2) set base currency; (3) assign GICS (D-R42); (4) set local benchmark and return basis; (5) set `classification.scoreboard_level` (default industry, D-R24); (6) select one `IndustryProxy` per node and level (R-A01-043..046). Output: valid Market (R-A01-001). Cadence: once, revisited on scheme version change.

**PR-A01-02 Fund availability & UCITS equivalent** — trigger: user selects a fund or A05 shortlists one. Steps: (1) check user residence against `eligible_residences`; (2) if not eligible, identify tracked index; (3) search funds tracking that index with wrapper UCITS; (4) derive domicile from ISIN (prefer IE/LU per R-A01-023); (5) choose share class (acc if no income); (6) flag FX risk / hedged option. Output: eligible instrument or "no equivalent". _Sources: S21 (~90 seconds), S13, S25_

**PR-A01-03 Classification refresh** — trigger: scheme vendor update. Steps: import nodes → validate chain (R-A01-010) → effective-date new assignments (R-A01-012) → notify A02 to recompute affected proxies.

**PR-A01-04 Gold route selection** — trigger: user wants gold exposure (allocation size owned by A09/A11). Steps: (1) choose route: physical / allocated vault / fund / miners; (2) physical: compute premium, apply R-A01-033, dealer checks R-A01-035; (3) vault: require allocated; (4) fund: US ETF or EU ETC per residence, compare expense ratio, redeemability; (5) every route is bought only through the A06 entry checklist and exited per A07; physical and vault holdings use the alert-based exit of A07 R-A07-043 (R-A01-051). _Sources: S28. Decision: D-R39_

## 7. Calculations
```
domicile            = ISO country of ISIN[0:2]                       # "IE..." -> Ireland
bullion_premium_pct = (item_price / (spot_per_oz * fine_oz) - 1) * 100
annual_fund_cost    = position_value * expense_ratio
cap_weighted_ret    = sum_i(w_i * r_i), w_i = mcap_i / sum(mcap)
equal_weighted_ret  = mean_i(r_i)
usd_return          = (1 + r_local) * (FX_t / FX_t0) - 1             # FX quoted as USD per local unit
expected_stop_fill  = min(stop_trigger, open_price)                  # sell stop, gap scenario
loss_at_fill        = (entry - expected_stop_fill) * shares
```

## 8. Examples / fixtures
**EX-A01-01 Classification invariant (R-A01-006, R-A01-009, R-A01-010)**
- Given US market (GICS) and Company X with nodes Information Technology → Semiconductors & Semiconductor Equipment → Semiconductors & Semiconductor Equipment → Semiconductors.
- When validated, Then accepted.
- Edge: Company Y has two sub-industry nodes → rejected (R-A01-009). Company Z's industry node is not a child of its industry-group node → rejected (R-A01-010).

**EX-A01-02 Benchmarks per market (R-A01-014)**
- Given markets US, EU, KR, JP. Then local benchmarks S&P 500 (USD), STOXX 600 (EUR), KOSPI (KRW), TOPIX (JPY); every market also shows MSCI ACWI (USD).
- Further defaults (D-R42): UK FTSE All-Share (GBP), DE CDAX (EUR), CN CSI 300 (CNY), AU S&P/ASX 200 (AUD), CA S&P/TSX Composite (CAD), IN Nifty 500 (INR).
- Edge: a market `SG` registered without a local benchmark → Market invalid (R-A01-001).

**EX-A01-03 Candle colour vs prior close (R-A01-004)** — source fixture S13.
- Given prior close 100.00, open 90.00 (gap down 10% pre-open), close 90.90.
- Then candle colour = green (close > open) but `change_vs_prior_close` = −9.1% → down day.

**EX-A01-04 Stop becomes market order on a gap (R-A01-037, R-A01-038)** — numbers from S15 sizing fixture.
- Given equity $100,000, the breakout tranche of 79 shares bought at $50.00 (60% of the A08-capped 133, EX-A08-01; 54 reserved), sell stop $46.00 (planned loss 79 × 4 = $316 = 0.32%).
- When the stock opens at $41.00 after an overnight gap.
- Then expected fill = min(46, 41) = $41.00; loss = (50 − 41) × 79 = $711 = 0.71% of equity (2.25× the planned loss); with both tranches (133 shares) it would be $1,197 = 1.20%. A08's overnight-gap test (weight 6.65% ≤ 6.67%) keeps it within the 2% gap budget; the order type is not the control.
- Edge: open $47.00, trades down to $45.80 intraday → stop triggers in session; fill near $46.00 (market order, not guaranteed).

**EX-A01-05 Buy-stop (R-A01-039)** — source fixture S07.
- Given price $16.00, resistance $20.00, buy-stop trigger $20.50 (level chosen by A06).
- Then the order stays `working` while price < $20.50; it triggers on the first trade at ≥ $20.50 (+2.5% above resistance).

**EX-A01-06 UCITS equivalent (R-A01-020..024)** — source fixture S21 (Aug 2026).
- Given a UK-resident user selecting US-listed IQLT.
- Then IQLT is not buyable; equivalent = iShares MSCI World Quality Factor UCITS ETF (same tracked index); ISIN prefix IE → domicile Ireland; acc class preferred if no income needed.
- Withholding illustration (synthetic): $1,000 US-source dividends → $150 withheld at 15% vs $300 at 30%.

**EX-A01-07 Bullion premium (R-A01-033)** — threshold from S28.
- Given spot $4,000/oz and a standard 1-oz coin.
- Price $4,200 → premium 5.0% → OK. Price $4,480 → 12.0% → "walk away".
- Edge: price $4,400 → exactly 10.0% → not above threshold → OK. Collector piece at $4,480 → no flag.

**EX-A01-08 Gold fund forms (R-A01-031, R-A01-032)** — expense ratios from S28 (Oct 2026).
- Given $10,000 in each: GLD 0.40% → $40/yr; GLDM 0.10% → $10/yr; IAUM 0.09% → $9/yr; EU physical-gold ETC ~0.12% → ~$12/yr.
- For an EU resident, the gold product type is ETC (not UCITS); gold-miner ETF GDX is classified as equity of the gold-mining industry, not as gold.

**EX-A01-09 Cap-weighted vs equal-weight (R-A01-027)** — synthetic, illustrating S29 (Oct 2026: Nasdaq 100 −2.9% while RSP closed green).
- Given 3 constituents, market caps 800/150/50, day returns −4%, +2%, +3%.
- Then cap-weighted = 0.80×(−4) + 0.15×2 + 0.05×3 = −2.75%; equal-weight = (−4 + 2 + 3)/3 = +0.33%.

**EX-A01-10 Leveraged fund (R-A01-025)**
- Given a 3x semiconductor ETF (`leverage_factor = 3`). Then it is flagged leveraged and excluded from METHOD buy candidates (A08).

**EX-A01-11 Index inclusion (R-A01-028)** — source fixture S03.
- Given IndexEvent: Tesla added to S&P 500, Dec 2020, ≈ $50B of other constituents sold by index funds.
- Then the event is recorded and A02 R-A02-031 runs on holdings in that index.

**EX-A01-12 Industry proxy selection (R-A01-043..046; D-R21)** — synthetic.
- Given three US industry nodes: A with two pure-play ETFs (avg daily value $900M and $150M) → proxy = the $900M ETF, type ETF; B with no ETF but an official S&P industry index → proxy type INDEX (chartable, not buyable); C with neither and 7 liquid members → equal-weight basket of the 5–7 most liquid members, type EQUAL_WEIGHT_BASKET.
- Edge: node D with 4 members, no ETF, no index → no valid proxy, `data_quality = insufficient`, shown under its parent node, members not buy-eligible through D (D-DEF-01).
- Edge: node A's $900M ETF holds only 55 % in the node (< 60 %) → not a valid ETF proxy; the $150M ETF with 82 % purity becomes the proxy (R-A01-050, D-R43).

**EX-A01-13 Liquidity floors (R-A01-049; D-R43)** — synthetic.
- Given a stock with 20-session average daily traded value €4.8M and EUR/USD 1.08 → $5.184M ≥ $5M → tradable. At €4.5M → $4.86M < $5M → shown, not buyable.
- Given an ETF with AUM $95M and ADV $3.1M → fails the AUM floor ($100M) → not buyable and not an industry basket; AUM $140M, ADV $1.9M → fails the ADV floor ($2M).

**EX-A01-14 Multi-listed company (R-A01-048; D-R42)** — synthetic.
- Given a company with its primary listing in Japan (TOPIX) and an ADR in the US. Then both instruments use the company's GICS node and TOPIX as local benchmark for RS; the ADR's prices are converted per R-A01-016 for the global view.

## 9. Variants & open points
- Variant (not chosen as default): S13 "about twelve broad sectors / ~150 industries" vs GICS 11/25/74/163 (S19). S13's ~150 ≈ GICS sub-industries. Resolved by D-C14 (GICS for US) plus per-market `classification.scoreboard_level`.
- Variant: S14 beginner protocol restricts instruments to S&P 500 (SPX/SPY) — modeled as profile PRF-beginner-index in A13 (D-S14), not as an A01 rule.
- Variant (not chosen): local classification schemes per market (D-C14 originally allowed them) — GICS for all markets (D-R42); local schemes only as additional views (R-A01-008).
- Closed by D-R42 — OPEN-A01-1 (GICS for all markets), OPEN-A01-4 (local benchmarks), OPEN-A01-5 (primary listing market governs).
- Closed by D-R43 — OPEN-A01-3 (liquidity floors).
- Closed by D-DEF-01 — OPEN-A01-6 (node without a valid proxy stays `insufficient`; pending user review).

Closed by round-2 decisions (2026-10-26): OPEN-A01-2 (D-R24; default level GICS Industry with drill-down).

### Glossary additions (merged into glossary v0.2.0)
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| accumulating-share-class | Accumulating Share Class (Acc) | CORE | Fund share class that reinvests distributions instead of paying them out. | S21 |
| currency-hedged-share-class | Currency-Hedged Share Class | CORE | Fund share class that hedges the fund's currency exposure back to the share-class currency. | S09 |
| futures-based-etf | Futures-Based ETF | CORE | Fund gaining exposure through futures rather than the spot asset; may diverge from spot. | S08 |
| allocated-storage | Allocated Storage | CORE | Vault storage of specific numbered bars in the owner's name, off the vault's balance sheet; contrast unallocated (unsecured claim). | S28 |
| bullion-premium | Bullion Premium | CORE | Amount paid above spot for a coin or bar (minting plus dealer margin); falls with bar size. | S28 |

## 10. Traceability
| Rule/Concept | Sources / Decisions |
|---|---|
| R-A01-001..005 markets, calendars, close | S07, S13, S19, S23; D-C14, D-C15b, D-C28 |
| R-A01-006..013 classification | S13, S19; D-C14 |
| R-A01-014..017 benchmarks, FX | S09, S17, S19; D-C15b |
| R-A01-018..030 instruments, funds, basket | S03, S04, S08, S09, S12, S13, S19, S21, S25, S29, S30; D-C21 |
| R-A01-031..035 gold forms | S08, S28, S30 |
| R-A01-036..042 orders | S07, S13, S23, S25; D-C26, D-OPEN-3, D-R16 |
| R-A01-043..046 industry proxies | S13, S19; D-R20, D-R21, D-R24 |
| R-A01-047 opening-auction orders | D-R16, D-R03, D-R07 |
| R-A01-048..051 primary listing, liquidity floors, proxy purity, gold forms in the engine | S05, S19, S28; D-R39, D-R42, D-R43 |
| EX-A01-03, -04, -05, -06, -07, -08, -09, -11 | S13, S15, S07, S21, S28, S29, S03 |
