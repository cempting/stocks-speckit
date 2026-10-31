---
id: A09
title: Portfolio Construction
context: CTX-D
layers: [CORE, METHOD, MACRO]
status: draft
sources: [S01, S04, S05, S06, S07, S08, S09, S11, S12, S13, S17, S19, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30]
decisions: [D-C11, D-C24, D-C04, D-C09, D-C10, D-OPEN-3, D-C14, D-C21, D-C22, D-C25, D-C27, D-R09, D-R13, D-R14, D-R36, D-R39, D-R45, D-DEF-26, D-DEF-27]
depends_on: [A01, A02, A08, A10, A11, A12]
---
# A09 — Portfolio Construction

## 1. Purpose & scope
Covers how the `Portfolio` is assembled and audited as a whole: look-through exposure across direct holdings and
funds, concentration limits (D-C11), the index-fund trap and hidden concentration, diversification, the two-engine
portfolio (growth + income), the emergency buffer, cash-like instruments and idle-cash erosion (D-C24), theme,
country and scenario exposure checks, and the pre-trade portfolio gate.

Excluded (owned elsewhere): per-trade risk and share count (A08 `sizing.*`, `risk.*`), overnight-gap weight cap
(A08, D-OPEN-3), entry signals (A06), exits (A07), bond selection and yields (A10 `bonds.*`), macro theses and
observations (A11 `macro.*`), instrument master data and fund holdings feed (A01), review cadence (A12).

## 2. Concepts
- [[portfolio]] — the aggregate this aspect constrains; [[portfolio-equity]] (A08) is the denominator of all weights.
- [[position]] — one holding; its weight and look-through contributions feed every exposure.
- [[look-through-exposure]] — canonical exposure measure: direct weights plus weights inside funds.
- [[hidden-concentration]] — the same company/industry reached through several vehicles ("one bet wearing four names").
- [[concentration-limit]] — user caps per industry/sector and per position (D-C11); buys into a breached bucket are blocked, a buy that would create a breach gets a warning (D-R14).
- [[total-open-risk]] — sum of risk at stop, shown in the portfolio view; no cap (D-R09, owned by A08).
- [[concentration-risk]] — the risk the limits exist to contain.
- [[concentration-audit]] — monthly recomputation of exposures vs limits (D-C04).
- [[index-fund-trap]] / [[index-concentration]] — a [[cap-weighted-index]] can be a concentrated bet on a few giants.
- [[dilution]] — share issuance by index heavyweights dilutes passive holders; also "diluted thesis" when diversifying.
- [[diversification]] — across industries that do not move together; [[correlation]] measures it.
- [[basket]] — industry fund used to own an industry without single-company risk (D-C21).
- [[theme-exposure]] — look-through share riding on one [[macro-theme]] (e.g. the "AI number").
- [[country-exposure]] — look-through share in a country/region.
- [[macro-scenario]] — scenario pairs from A11 used only for exposure checks.
- [[two-engine-portfolio]] — growth engine (stocks) + income engine (bonds, A10).
- [[emergency-buffer]] — months of expenses held outside the investable portfolio.
- [[investable-cash]] — idle cash inside the portfolio; [[cash-erosion]] flags it when [[real-yield]] < 0.
- [[cash-like-instrument]] — [[treasury-bill]] and short-Treasury ETFs counted as cash.
- [[buy-and-hold]] — only for a broad self-cleaning index with long horizon.
- [[opportunity-cost-of-holding]] — return lost by waiting for break-even instead of rotating.
- [[rebalancing]], [[asset-allocation]], [[equal-weighting]], [[hedge]], [[gold-asset]] — allocation vocabulary.
- [[overnight-gap-test]], [[single-position-impact]], [[position-tier]] (A08) — weight constraints referenced here.

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Portfolio | id, base_currency | ISO 4217 | required | one or more accounts |
| Portfolio | equity | money | = Σ holding market values + investable cash; excludes EmergencyBuffer | A08 [[portfolio-equity]] |
| Portfolio | engine_shares {growth, income, cash} | % | sum = 100 | PR-A09-04 |
| Holding | instrument_id, quantity, market_value, weight | -, -, money, % | weight = market_value / equity | Position (A08/A07) carries stops/exit |
| Holding | look_through_mode | enum {direct, fund_full, fund_partial, fund_opaque} | | from FundComposition coverage |
| FundComposition (new) | fund_id, as_of, constituents[{instrument_id, weight}], industry_weights, country_weights, coverage_pct | date, %, % | Σ constituent weights ≤ 100; coverage_pct = Σ known weights | fed by A01; e.g. top-10 only → partial |
| Exposure | bucket_type | enum {company, industry, sector, theme, country, scenario, asset_class} | | |
| Exposure | bucket_id, value_pct, direct_pct, via_funds_pct, unresolved_pct, as_of | %, date | value_pct = direct + via_funds | R-A09-002 |
| ConcentrationLimit | bucket_type, bucket_id ('*' = all), max_pct, scope (pre-trade, audit) | % | in allowed range of §4 | D-C11 |
| ConcentrationLimit | state | enum {ok, breached} | breached ⇒ BuyBlock | R-A09-010 |
| BuyBlock (new) | bucket, reason, since, cleared_at | | auto-clears when exposure ≤ limit | never forces a sell |
| ConcentrationWarning (new) | order_draft_id, bucket, post_trade_pct, limit_pct, suggested_max_amount, acknowledged_at | %, money | buy that would create a breach; never blocks | D-R14 |
| EmergencyBuffer | months_target, monthly_expenses, held_amount, location | int, money, money | months_target in [3,12] | outside Portfolio.equity |
| CashLike | instrument_id, kind {cash, t_bill, short_treasury_etf}, yield_pct, real_yield_pct, eroding | %, %, bool | eroding ⇔ real_yield_pct < 0 | D-C24 |
| ScenarioExposureCheck (new) | scenario_id (A11), hurt_pct, benefit_pct, band | % | | S06 oil score etc. |
| ThemeMap (A11-owned) | theme_id → industries/companies | | | consumed here for theme exposure |

States: ConcentrationLimit `ok ⇄ breached` (recomputed on every price/holding change and pre-trade);
CashLike.eroding `false ⇄ true` (recomputed when a new inflation or yield Observation arrives, A11).

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `portfolio.max_industry_pct` | 25 | 15–40 | % of equity, look-through | D-C11; S13, S17, S01 (15–25) |
| `portfolio.max_sector_pct` | 25 | 15–40 | % of equity, look-through | D-C11; S01, S17 |
| `portfolio.max_position_pct` | 10 | 3–10 | % of equity per company | D-C11, D-R36; S05 (implied ≤10) |
| `portfolio.position_cap_basis` | company look-through (all holdings incl. funds); diversified sector/industry funds are not positions for this cap | {company look-through} | enum | D-R36 |
| `portfolio.classification_level` | per market ClassificationScheme | industry/sector levels of scheme | enum | D-C14 |
| `portfolio.max_theme_pct` | 30 | 10–50 | % look-through, per theme | D-R45; S25, S30 (left blank) |
| `portfolio.max_country_pct` | 60 | 20–100 | % look-through, per single country other than the home market | D-R45; S05, S19 |
| `portfolio.home_market` | primary Market of the Portfolio | any Market | — | D-R45 (home market exempt from the country cap) |
| `portfolio.target_positions_min` / `_max` | 15 / 30 | ≥1 | count | S07 (soft guidance) |
| `portfolio.scenario_exposure_max_pct` | 15 | 10–20 (source) | % of equity, per contrarian macro scenario | S06; D-R45 |
| `portfolio.oil_score_bands` | low <15, moderate 15–<35, high ≥35 | – | % of equity | S06 |
| `portfolio.europe_drag_threshold_pct` | 15 | – | % look-through | S06 |
| `portfolio.ai_shock_pct` | 30 | – | % fall applied to AI theme exposure | S30 |
| `portfolio.buy_and_hold_min_horizon_years` | 10 | 10–20 | years | S23 |
| `portfolio.gold_allocation_target_pct` | unset (user) | – | % | S28 ("mid-single-digit", ~5 illustrative only) |
| `portfolio.max_speculative_names` | 1 | ≥0 | count of Tier-3 names | S22 (see A08 [[position-tier]]) |
| `portfolio.fund_holdings_max_age_days` | 35 | 7–92 | days since FundComposition.as_of | D-DEF-26 |
| `portfolio.high_correlation_threshold` | 0.85 | 0.5–1 | coefficient (daily returns) | S29 (0.91 cited as "no longer diversified"); D-DEF-27 |
| `portfolio.correlation_lookback_sessions` | 63 | 21–252 | sessions | D-DEF-27 (= A08 volatility window) |
| `cash.emergency_buffer_months` | 6 | 3–12 | months of expenses | D-C24; S27 (3–6), S29 (user) |
| `cash.inflation_metric` | headline CPI YoY, latest Observation | – | % | S09 (BLS CPI); A11 Observation |
| `cash.cash_like_kinds` | {cash, t_bill, short_treasury_etf} | – | enum set | D-C24 |
| `cash.erosion_threshold_real_pct` | 0 (flag when < 0) | fixed | % | D-C24; S28 |

## 5. Rules

### 5.1 Look-through exposure
- **R-A09-001** (hard, METHOD) — Every exposure figure used for limits, audits or coaching MUST be a [[look-through-exposure]]: direct holdings plus each fund's constituent/industry/country weights multiplied by the fund's portfolio weight. _Sources: S13, S23, S25, S30. Decision: D-C11_
- **R-A09-002** (hard, CORE) — `Exposure.value_pct = Σ_i weight_i × share_of_bucket_in_i`, where a direct holding has share 1 (or 0) for its own company/industry. _Sources: S13, S06. Decision: D-C11_
- **R-A09-003** (hard, CORE) — When a fund's composition covers < 100% of its weight (e.g. top-10 only), the uncovered part MUST be reported as `unresolved_pct` for that fund and MUST NOT be silently assigned to any bucket. _Sources: S29 (top-10 factsheets). Decision: —_
- **R-A09-004** (hard, CORE) — A fund with no composition data (`fund_opaque`) MUST be mapped to the industry/sector of its stated category (e.g. an industry [[basket]] to that industry) and flagged "unverified"; a broad index with no data MUST be flagged and excluded from company-level caps until data exists. _Sources: S12, S30. Decision: D-C21_
- **R-A09-005** (soft, METHOD) — Before a fund is treated as diversifying, its top holdings and weights SHOULD be shown; a cap-weighted fund dominated by a few names MUST be labelled with its [[index-concentration]] (top-10 weight). _Sources: S12, S29_
- **R-A09-006** (hard, CORE) — An ETF/fund removes single-company risk only; its industry, sector, country and market exposure MUST still count fully in look-through buckets. _Sources: S12, S30_
- **R-A09-007** (soft, METHOD) — When two or more held funds share constituents in their top-10, the overlap per company SHOULD be reported as [[hidden-concentration]]. _Sources: S13, S29_

### 5.2 Concentration limits (D-C11)
- **R-A09-010** (hard, METHOD) — If look-through exposure of an industry or sector bucket exceeds `portfolio.max_industry_pct` / `portfolio.max_sector_pct`, the bucket state is `breached` and new buys of any instrument that adds exposure to that bucket MUST be blocked. _Sources: S13, S17, S01. Decision: D-C11_
- **R-A09-011** (hard, METHOD) — The per-position cap applies per company, measured look-through across all holdings including funds (`portfolio.position_cap_basis`). If a company's exposure exceeds `portfolio.max_position_pct`, further buys adding to that company (directly or through a fund) MUST be blocked. A diversified sector or industry fund is not a position for this cap; its weight is limited by the sector/industry cap (R-A09-010). _Sources: S25, S05. Decision: D-C11, D-R36_
- **R-A09-012** (hard, METHOD) — The pre-trade gate MUST evaluate exposures *after* the proposed order fills; an order into a bucket that is not yet breached but whose post-trade exposure would exceed a limit MUST NOT be rejected: it gets a `ConcentrationWarning` showing the bucket, the post-trade exposure and the max admissible amount as a suggestion. Orders into an already-breached bucket stay blocked (R-A09-010/011). _Sources: S13. Decision: D-C11, D-R14_
- **R-A09-013** (hard, METHOD) — A breached limit MUST NOT trigger an automatic sell; it raises a review flag in the weekly/monthly routine. Only price-based exits are automatic. _Decision: D-C11, D-C27, D-C26_
- **R-A09-014** (hard, METHOD) — A `BuyBlock` MUST clear automatically when the bucket's exposure returns to ≤ its limit. Equality (exposure = limit) is not a breach. _Decision: D-C11_
- **R-A09-015** (hard, METHOD) — The hard maximum weight of a new position is `min(A08 overnight-gap cap, A08 risk-based weight)`; the suggested maximum is `min(hard maximum, company headroom, industry/sector headroom)`, where company headroom = `portfolio.max_position_pct` − current company exposure (basis `portfolio.position_cap_basis`, look-through) and industry/sector headroom = `portfolio.max_industry_pct` / `portfolio.max_sector_pct` − current look-through bucket exposure. Exceeding the suggested maximum raises a `ConcentrationWarning` (R-A09-012); A09 MUST NOT override the A08 values. _Decisions: D-C09, D-C10, D-C11, D-OPEN-3, D-R14_
- **R-A09-016** (hard, CORE) — Industry/sector buckets MUST be taken from the ClassificationScheme of the instrument's Market (GICS for US); a fund spanning markets is decomposed by its constituents' schemes, with a cross-scheme mapping provided by A01. _Decision: D-C14_
- **R-A09-017** (soft, METHOD) — A [[concentration-audit]] MUST run in the monthly review (and MAY run weekly); it lists every bucket's exposure, limit, headroom and blocks. _Sources: S05. Decision: D-C04_

### 5.3 Index-fund trap, dilution, buy-and-hold
- **R-A09-020** (soft, METHOD) — Broad cap-weighted index holdings MUST contribute their constituents to company, industry and theme exposure; the app SHOULD display the index's top-N weight vs. the historical norm as an [[index-fund-trap]] warning. _Sources: S04, S05, S12, S21, S23, S25, S30_
- **R-A09-021** (soft, CORE) — A [[buy-and-hold]] flag (position without an exit plan) MAY be set only on a broad, self-cleaning index holding and only if the user's horizon ≥ `portfolio.buy_and_hold_min_horizon_years` and the money is not needed in that time; for single stocks, industry baskets and narrow funds it MUST be rejected. _Sources: S23, S25, S30_
- **R-A09-022** (soft, CORE) — Material share issuance by index heavyweights (net issuance, equity offerings) SHOULD be surfaced to index holders as [[dilution]] of their look-through ownership (link A05 `share-count`). _Sources: S04, S21_
- **R-A09-023** (soft, METHOD) — The diversification "dial" (single stock → industry basket → broad sector fund) MUST be presented as a trade-off: more diversification = smaller swings but a diluted thesis; high conviction in a specific company → stock, liking the theme only → fund. _Sources: S11, S24_
- **R-A09-024** (soft, METHOD) — When a position is exited, freed capital SHOULD be offered to the next confirmed setup in a rising industry (A06); exiting alone is not the goal. No automatic re-buy. _Sources: S07, S13, S25_
- **R-A09-025** (soft, METHOD) — For a losing holding the review SHOULD show the [[opportunity-cost-of-holding]] versus rotating into a top-RS industry (A02) over the same period. _Sources: S05, S23, S25_

### 5.4 Diversification
- **R-A09-030** (soft, METHOD) — Diversification MUST be measured by industries/sectors held (look-through) and their [[correlation]], not by the count of tickers; several stocks or funds in one theme count as one bet. _Sources: S05, S23, S25, S29_
- **R-A09-031** (soft, METHOD) — The number of positions SHOULD stay within `portfolio.target_positions_min..max`; outside the range the audit shows a coaching note, never a block. _Sources: S07_
- **R-A09-032** (soft, CORE) — Holdings in foreign currency MUST record currency and hedged/unhedged status; the audit reports currency exposure so the user decides on hedging. _Sources: S09, S19_
- **R-A09-033** (soft, METHOD) — A single speculative (Tier-3) name SHOULD be the limit (`portfolio.max_speculative_names`); a second one raises a warning. Tier sizing itself is A08. _Sources: S22_
- **R-A09-034** (soft, METHOD) — If gold exposure is 0 or above `portfolio.gold_allocation_target_pct`, the monthly review SHOULD ask the user to confirm it is deliberate (own none "on purpose"; large piles → consider [[rebalancing]] into other commodities). The target sizes gold exposure (size before timing); buys of any gold form still require the A06 checklist and exit per A07 (A11 R-A11-041). _Sources: S28. Decision: D-R39_

### 5.5 Theme, country and scenario exposure
- **R-A09-040** (hard, METHOD) — The app MUST compute [[theme-exposure]] for each theme in the A11 ThemeMap (e.g. "AI number" incl. index funds) and compare it with `portfolio.max_theme_pct` (30%): a buy into a theme already above the cap MUST be blocked (as D-C11); a buy that would create the breach gets a `ConcentrationWarning` (as D-R14). _Sources: S27, S29, S30. Decision: D-R45, D-C11, D-R14_
- **R-A09-041** (soft, METHOD) — A theme stress figure MUST be shown: `theme_exposure × portfolio.ai_shock_pct` for AI (generalised: × user shock per theme). _Sources: S30, S25_
- **R-A09-042** (soft, MACRO) — For an active A11 [[macro-scenario]], the app MAY compute a scenario exposure check (sum of weights hurt / helped); an oil-scenario score ≥ 35% MUST be labelled "high". _Sources: S06_
- **R-A09-043** (hard, MACRO) — Exposure to a contrarian macro scenario (weights tagged "helped" by that scenario, PR-A09-05) is capped at `portfolio.scenario_exposure_max_pct` (15%): a buy that would create a breach gets a `ConcentrationWarning`; buys adding to an already-breached scenario bucket MUST be blocked. No order is ever generated. _Sources: S06. Decision: D-R45_
- **R-A09-044** (soft, MACRO) — [[country-exposure]] to Europe ≥ `portfolio.europe_drag_threshold_pct` MUST be flagged "drag risk" only while an A11 rate-divergence Thesis is active. _Sources: S06_
- **R-A09-045** (hard, MACRO) — Scenario, theme and country checks MUST NOT create orders or signals; they produce flags, warnings, blocks on new buys into breached buckets (theme, country, scenario caps) and review items only. _Decisions: D-C22, D-C25, D-R45_

### 5.6 Two-engine portfolio
- **R-A09-050** (soft, METHOD) — Each holding MUST be assigned to an engine: equities/equity funds → growth; bonds and bond funds except cash-like → income; cash and [[cash-like-instrument]] → cash. _Sources: S09_
- **R-A09-051** (soft, METHOD) — If the income engine is 0% while short rates are high, the review MAY show an informational note pointing to the A10 staircase; no target % is imposed. _Sources: S09_
- **R-A09-052** (soft, CORE) — High-yield bonds MUST be tagged as economy-sensitive (they behave partly like equities in downturns) when summarising engine diversification. _Sources: S09_

### 5.7 Emergency buffer, cash-like and idle cash (D-C24)
- **R-A09-060** (hard, METHOD) — The [[emergency-buffer]] target = `cash.emergency_buffer_months × monthly_expenses`; it is held outside the investable portfolio and MUST NOT count toward Portfolio.equity, sizing or exposure. _Sources: S27, S29. Decision: D-C24_
- **R-A09-061** (soft, METHOD) — If `held_amount < target`, the app MUST show a shortfall warning in every review until funded; the shortfall MUST NOT block buys. _Sources: S27, S29. Decision: D-C24, D-R13_
- **R-A09-062** (hard, CORE) — T-bills and short-Treasury ETFs MUST be classified as cash-like (asset class cash for allocation, engine "cash"), not as income bonds. _Decision: D-C24; S09 (Step 1 "parking cash; emergency fund")_
- **R-A09-063** (hard, METHOD) — For [[investable-cash]] and each cash-like holding: `real_yield = yield − inflation(cash.inflation_metric)`; if `real_yield < 0` the holding MUST be flagged "eroding" ([[cash-erosion]]). The emergency buffer is never flagged. _Sources: S09, S26, S27, S28. Decision: D-C24_
- **R-A09-064** (hard, METHOD) — The eroding flag is informational: it MUST NOT trigger a buy; it links to the watchlist/next-setup prompt (R-A09-024) and the A10 staircase. _Decisions: D-C24, D-C25_
- **R-A09-065** (soft, METHOD) — Holding some investable cash with a written plan is valid (a sell-off becomes an entry); the app SHOULD show "all cash is a decision too" when investable cash exceeds the user's stated intent. _Sources: S12, S27_

### 5.8 Round-2 additions (2026-10-26)
- **R-A09-066** (soft, METHOD) — The portfolio exposure view MUST show A08 [[total-open-risk]] (sum of risk at stop, currency and % of equity) next to the exposures; there is no portfolio cap on it and it never blocks a buy. _Decision: D-R09_
- **R-A09-067** (hard, METHOD) — A `ConcentrationWarning` MUST be shown before the order is confirmed and recorded with the order in the Journal (A12); proceeding past it is allowed and is not a rule deviation. _Decision: D-R14_

### 5.9 Round-3 additions (2026-10-26)
- **R-A09-068** (hard, METHOD) — [[country-exposure]] to any single country other than `portfolio.home_market` is capped at `portfolio.max_country_pct` (60%, look-through): a buy that would create a breach gets a `ConcentrationWarning`; buys adding to an already-breached country bucket MUST be blocked. _Sources: S05, S19. Decision: D-R45, D-C11, D-R14_
- **R-A09-069** (soft, CORE) — A FundComposition older than `portfolio.fund_holdings_max_age_days` (35) MUST be flagged stale; exposures derived from it are still computed and shown with a "stale" marker until fresh data arrives. _Decision: D-DEF-26_
- **R-A09-070** (soft, METHOD) — The monthly audit MUST compute the correlation of daily returns over `portfolio.correlation_lookback_sessions` (63) between holdings and between theme/industry buckets; a pair at or above `portfolio.high_correlation_threshold` (0.85) is flagged "low diversification" (coaching flag, never a block or order). _Sources: S29. Decision: D-DEF-27_

## 6. Processes
**PR-A09-01 Pre-trade portfolio gate** — Trigger: any proposed buy (A06 signal → Order draft). Inputs: Portfolio, holdings, FundCompositions, limits, proposed order. Steps:
1. Compute post-trade weights (equity unchanged by a buy funded from investable cash).
2. Compute post-trade look-through exposures for company, industry, sector, theme, country and active scenarios.
3. Apply R-A09-010/011, R-A09-040, R-A09-043 and R-A09-068: buckets already breached → block; apply R-A09-012: buckets that the order would breach → ConcentrationWarning with max admissible amount.
4. Apply R-A09-015 (take A08 caps); return `allowed_amount = min(requested, A08 caps)` and `suggested_amount = min(allowed_amount, all headrooms)`.
5. Output: allow / allow-with-warning (suggested reduce-to) / block + reasons; write to Journal (A12). Cadence: per order.

**PR-A09-02 Monthly concentration audit** — Trigger: monthly review (D-C04). Steps: refresh fund compositions (age check, R-A09-069) → recompute all exposures → correlation check (R-A09-070) → list breaches, blocks, unresolved %, overlaps (R-A09-007) → index-concentration warning → theme stress (R-A09-041) → positions count note → gold/hedge prompts → output audit report into ReviewLog.

**PR-A09-03 Cash review** — Trigger: new inflation/yield Observation (A11) or weekly review. Steps: check buffer shortfall (R-A09-061) → recompute real yield of investable cash and cash-like holdings → set/clear eroding → show staircase link.

**PR-A09-04 Engine & allocation summary** — Trigger: weekly review. Steps: classify holdings (R-A09-050) → engine shares → asset-class [[asset-allocation]] → currency exposure (R-A09-032).

**PR-A09-05 Scenario exposure check** — Trigger: an A11 MacroScenario or rate-divergence Thesis becomes active; monthly. Steps: map holdings to "hurt/helped/neutral" per scenario (user-confirmed mapping) → sum weights → band → contrarian cap warning (R-A09-043) → Europe drag check (R-A09-044).

## 7. Calculations
```
weight_i            = market_value_i / equity                      # %, equity excludes EmergencyBuffer
exposure_k          = Σ_i weight_i × share_k_in_i                   # share=1 for direct match, fund weights otherwise
unresolved_i        = weight_i × (1 − coverage_pct_i)               # partial fund data
headroom_k          = limit_k − exposure_k                          # admissible new exposure
max_buy_amount_k    = headroom_k × equity / share_k_in_candidate    # candidate fund or stock
theme_stress        = theme_exposure × shock_pct                    # AI: shock 30%
scenario_score      = Σ weight_i  for holdings tagged "hurt" in scenario
europe_exposure     = Σ_i weight_i × europe_share_i
buffer_target       = cash.emergency_buffer_months × monthly_expenses
real_yield_cash     = cash_yield − inflation_yoy                    # percentage points
eroding             = real_yield_cash < 0
top_n_concentration = Σ weight of the N largest index constituents
engine_share_e      = Σ weight_i for holdings with engine e
country_k           = Σ_i weight_i × country_share_k_in_i        # cap 60 % for k ≠ home market (D-R45)
composition_stale   = (today − FundComposition.as_of) > 35 days  # D-DEF-26
low_diversification = corr(daily returns, 63 sessions) >= 0.85    # D-DEF-27
```

## 8. Examples / fixtures
**EX-A09-01 Hidden concentration (S13)** — Given holdings S&P 500 fund, semiconductor ETF, AI ETF and the largest chip company directly. When look-through is computed. Then the chip company appears in 4 vehicles and is reported once with summed exposure and an overlap note (R-A09-001, R-A09-007).

**EX-A09-02 Tech industry breach (synthetic, S23/S25 shares)** — Given equity $100,000: S&P-type fund 40% (tech share 40%), Nasdaq fund 20% (tech 100%), tech stocks 15%, limit 25%. When exposure is computed. Then tech = 0.40×0.40 + 0.20×1.00 + 0.15 = 51% → `breached`; a buy of another software basket is blocked; no sell is generated (R-A09-010, R-A09-013).

**EX-A09-03 "60% in one bet" stress (S25)** — Given ~60% look-through in tech and a last severe tech-index drawdown of 78%. When the theme stress is shown with shock 78%. Then portfolio impact ≈ 0.60 × 0.78 = 46.8% ("about half the account").

**EX-A09-04 Company cap via look-through (synthetic; NVIDIA ≈8% of S&P 500, S30, Oct 2026)** — Given S&P 500 fund 50%, semis ETF 10% holding the company at 20%, direct position 5%, `max_position_pct`=10, basis = company look-through. Then exposure = 0.5×0.08 + 0.1×0.20 + 0.05 = 11% > 10% → further buys of the company blocked, directly or through a fund holding it, although the direct position is only 5% (D-R36). The S&P 500 fund and the semis ETF themselves are not positions for the 10% cap; the semis ETF's weight counts against the 25% industry cap.

**EX-A09-05 Post-trade check edge (D-R14)** — Given industry exposure 24.0%, limit 25%, equity $100,000, candidate is a pure industry basket. When a buy of $2,000 is proposed. Then post-trade = 26% → ConcentrationWarning, not rejected; suggested max admissible = $1,000 (→ 25.0%, equality allowed) (R-A09-012, R-A09-014). If the user proceeds, the bucket is breached and later buys into it are blocked (R-A09-010). Edge: exposure already 25.5% → any adding buy is blocked.

**EX-A09-06 AI number (S30, 24 Oct 2026)** — Given S&P 500 fund + NASDAQ fund + Tesla + Palantir + SpaceX giving an AI number of 55%. Then AI theme stress = 0.55 × 0.30 = 16.5% portfolio fall for a 30% AI drop. With the default `max_theme_pct` = 30 → 55% > 30% → AI theme breached → new AI-adding buys blocked (D-R45). Edge: at 28% a planned AI buy raising it to 33% gets a ConcentrationWarning (suggested maximum 2%), not a block.

**EX-A09-07 Oil exposure score (synthetic, bands S06 June 2026)** — Given energy producers 20%, oil services 10%, airlines 5% (helped). Then hurt-by-oil-drop score = 30% → "moderate"; with producers at 25% the score is 35% → "high" (boundary inclusive).

**EX-A09-08 Europe drag (synthetic, S06 "Total International funds 40–50% Europe")** — Given Total International fund 30% with 45% Europe and a European stock 3%. Then Europe = 0.30×0.45 + 0.03 = 16.5% ≥ 15 → "drag risk" only if A11 rate-divergence Thesis is active; otherwise no flag.

**EX-A09-09 Index concentration (S12, July 2026; S04, June 2026)** — Given S&P 500 top-10 weight 36–37% (S12) vs historic norm 18–23%. Then the index-trap warning shows "top 10 ≈ 2× norm"; a June 2026 snapshot of 38–40% (S04) is a different asOf and is stored separately (no conflict, D-C22).

**EX-A09-10 Dilution (S04, 2026-06-02)** — Given Alphabet's $80B equity offering (SEC filing). Then index holders see a dilution note on that constituent (R-A09-022).

**EX-A09-11 Emergency buffer** — Given monthly expenses $4,000, `emergency_buffer_months` = 6, held $18,000. Then target $24,000, shortfall $6,000 warning, no buy block (D-R13); the $18,000 is excluded from equity. Edge: user sets 2 months → rejected (range 3–12).

**EX-A09-12 Cash erosion (S09, July 2026; CPI 4.2% May 2026)** — Given investable cash in a savings account at 0.38% and SGOV (cash-like) at ~3.8%. Then real yields −3.82 pp and −0.40 pp → both "eroding". Edge: a cash-like yield of exactly 4.2% → real 0.00 → not eroding (strict <).

**EX-A09-13 Opportunity cost (S05/S25)** — Given $50,000 in tech flat for 2 years vs rotated into energy → $75,000. Then the review shows $25,000 forgone; compounding both at 10%/yr the gap is $40,263 after 5 years and $64,844 after 10 years.

**EX-A09-14 Two-engine summary** — Given equities 70%, LQD 15%, HYG 5%, SGOV 10%. Then engines: growth 70%, income 20% (HYG tagged economy-sensitive), cash 10% (SGOV cash-like, eroding if CPI > yield).

**EX-A09-15 Correlation (S29, Oct 2026)** — Given AI Leaders basket vs S&P 500 correlation rising 0.73 → 0.91 since 2026-10-14. Then the audit notes that the broad index no longer diversifies AI exposure ("AI down = everything down"); 0.91 ≥ 0.85 over the last 63 sessions → "low diversification" flag (R-A09-070, D-DEF-27); 0.73 alone would not flag.

**EX-A09-17 Country and scenario caps (synthetic, D-R45)** — Given home market US, a Japan fund 35%, Japanese stocks 10% and a global fund 20% with 40% Japan. Then Japan = 35 + 10 + 0.20 × 40 = 53% ≤ 60% → ok; a further 10% Japan-fund buy → 63% > 60% → ConcentrationWarning with suggested maximum 7%; if the user proceeds, the next Japan-adding buy is blocked (R-A09-068). US exposure of 80% is not capped (home market). A contrarian scenario bucket at 12% plus a 5% buy → 17% > 15% → warning; further adding buys blocked (R-A09-043).

**EX-A09-18 Stale fund composition (D-DEF-26)** — Given evaluation date 2026-10-24 and a fund composition as of 2026-09-15 → 39 days > 35 → exposures from that fund are marked stale; as of 2026-09-20 → 34 days → current.

**EX-A09-16 Total open risk in the exposure view (D-R09)** — Given four positions with risk at stop $532, $1,000, $800 and $0 (stop above entry) on equity $100,000. Then the view shows total open risk $2,332 = 2.33% of equity; a fifth buy adding $1,000 risk is not blocked by any total-risk cap (R-A09-066).

## 9. Variants & open points
Variants not chosen:
- Sector cap 15–25% (S01) and 25–40% (S17): both inside the D-C11 range; default 25 (D-C11).
- Hold 2–4 sectors (S17): belongs to PRF-momentum-rotation (A13), not the canonical method.
- Fixed allocation % to bonds (none given by S09): not imposed; R-A09-051 is informational.
- S06 "overweight US, underweight Europe": kept as a flag under an active thesis, never an allocation rule (D-C25 bias only).
- S28 gold "~5%": illustration of UBS wording; kept as optional user target, not a default.

Open: none.
- Closed by D-R36 — OPEN-A09-1 (position cap per company, look-through; diversified funds are not positions).
- Closed by D-R45 — OPEN-A09-2 (theme 30%, country 60% excluding the home market; breach-creating buys warn, buys into breached buckets blocked) and OPEN-A09-3 (scenario 15%).
- Closed by D-DEF-26 — OPEN-A09-4 (fund composition stale after 35 days; pending user review).
- Closed by D-DEF-27 — OPEN-A09-5 (correlation ≥ 0.85 over 63 sessions; pending user review).

Closed by round-2 decisions (2026-10-26): OPEN-A09-6 (D-R14), OPEN-A09-7 (D-R13).

**Glossary additions (merged into glossary v0.2.0):**
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| oil-exposure-score | Oil Exposure Score | MACRO | Sum of portfolio weights hurt by a large oil-price drop; bands <15 low, 15–35 moderate, ≥35 high. | S06 |
| fund-composition | Fund Composition | CORE | Dated constituent, industry and country weights of a fund with coverage %, used for look-through. | S12, S29, S30 |
| buy-block | Buy Block | METHOD | State that rejects new buys adding to a bucket whose exposure exceeds its limit; clears automatically. | D-C11 |

## 10. Traceability
| Rule/Concept | Sources / Decisions |
|---|---|
| R-A09-001..007 look-through | S12, S13, S23, S25, S29, S30; D-C11, D-C21 |
| R-A09-010..017 limits | S01, S05, S13, S17, S25; D-C11, D-C14, D-C27, D-C26, D-C09, D-C10, D-OPEN-3, D-C04 |
| R-A09-020..025 index trap, dilution, buy-and-hold | S04, S05, S07, S11, S12, S13, S21, S23, S24, S25, S30 |
| R-A09-030..034 diversification | S05, S07, S09, S19, S22, S23, S25, S28, S29 |
| R-A09-040..045 theme/country/scenario | S06, S25, S27, S29, S30; D-C22, D-C25 |
| R-A09-050..052 two-engine | S09 |
| R-A09-060..065 buffer & cash | S09, S12, S26, S27, S28, S29; D-C24, D-C25, D-R13 |
| R-A09-066..067 total open risk display, concentration warning | D-R09, D-R14 |
| R-A09-068..070 country cap, stale compositions, correlation flag | S05, S19, S29; D-R45, D-DEF-26, D-DEF-27 |
| R-A09-011, R-A09-040, R-A09-043 company look-through cap, theme and scenario caps | S06, S25, S27, S29, S30; D-R36, D-R45 |
| EX-A09-01..15 | S04, S05, S06, S09, S12, S13, S25, S29, S30 |
