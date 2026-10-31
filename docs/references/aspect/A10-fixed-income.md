---
id: A10
title: Fixed Income
context: CTX-D
layers: [CORE, METHOD]
status: draft
sources: [S09, S08, S10, S18, S21, S26, S28, S29, S30]
decisions: [D-C24, D-C22, D-C25, D-C11, D-C05, D-C26, D-R16, D-R38, D-DEF-28, D-DEF-29, D-DEF-30, D-DEF-31]
depends_on: [A01, A03, A09, A11, A13]
---
# A10 — Fixed Income

## 1. Purpose & scope
Covers bonds and bond funds as the income engine of the [[two-engine-portfolio]] (A09): the Risk-Reward Staircase
(five steps from Treasuries to high yield plus a municipal side step), US instrument categories (Treasuries, USD EM
sovereigns, investment grade, high yield, munis), UK/EU UCITS alternatives, real yield, tax-equivalent yield,
after-tax comparison, duration sensitivity, credit spread and risk factors. Bond funds are strategic allocation holdings bought to target weight and rebalanced monthly; only high yield also carries the 150-SMA trend exit (D-R38).

Excluded: cash-like classification and idle-cash erosion flag (A09 `cash.*`, D-C24, which consumes A10 yields);
yield curve and credit spreads as cycle indicators (A03); bond-market observations and macro theses (long-bond
yield, Treasury buybacks, AI credit; A11); fund wrapper, domicile, withholding tax and NAV discount master data (A01);
personal tax profile and risk comfort (A13 `profile.*`).

## 2. Concepts
- [[bond]] — loan to an issuer with [[coupon]] and [[maturity]]; bondholders rank before stockholders.
- [[yield]] — annual return at the current price; fund yields are SEC/distribution yields as published.
- [[bond-price-yield-inverse]] / [[duration]] — the "seesaw": price change ≈ −duration × yield change.
- [[risk-reward-staircase]] — five-step ladder; each higher step pays more and carries more risk.
- [[treasury-security]], [[treasury-bill]], [[risk-free-rate]] — Step 1 and the hurdle for non-yielding assets.
- [[investment-grade]], [[high-yield-bond]], [[credit-rating]] — Steps 3 and 4.
- [[credit-spread]] — "risk cushion" (OAS) paid for credit risk; [[credit-default-swap]] prices single-name default risk.
- [[municipal-bond]], [[tax-equivalent-yield]] — Step 5 (US tax residents only).
- [[real-yield]] — yield minus inflation ([[inflation]] = latest CPI Observation, A11).
- [[barbell]] — split between a short and a long duration fund.
- [[basis-point]], [[percentage-point]] — display units for spreads and yield changes.
- [[ten-year-yield]], [[long-bond-yield]], [[yield-curve]] — reference yields (observations in A11, cycle use in A03).
- [[ucits]], [[isin-domicile]], [[withholding-tax]], [[tax-wrapper]], [[nav-discount]] (A01) — wrapper facts used in alternatives.
- [[cash-like-instrument]] (A09) — Step 1 ultra-short funds are cash-like.
- [[project-finance]] — single-project debt (AI data centres) relevant to credit risk observations.

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Bond (Instrument) | issuer_type | enum {us_treasury, gov_other, usd_em_sovereign, ig_corporate, hy_corporate, us_municipal, cash_proxy} | required | drives step |
| Bond | coupon_pct, maturity_date, rating, currency | %, date, rating, ISO | rating in agency scale | |
| BondFund (ETF) | yield_pct, yield_type {sec, distribution}, duration_years, rating_mix, oas_bp, expense_ratio_pct, as_of, source | %, years, bp, %, date | as_of required | e.g. LQD ~8 yrs |
| BondFund | floating_rate | bool | | USFR |
| BondFund | currency, hedged | ISO, bool | | FX risk for non-USD investors |
| BondFund | duration_bucket, muni_in_state_share_pct | enum {short, intermediate, long}, % | bucket per R-A10-047; in-state share only if published | D-DEF-30, D-DEF-31 |
| BondAllocation (new) | portfolio_id, step, fund_id, target_weight_pct, last_rebalanced | %, date | Σ targets ≤ income-engine share; monthly rebalance | D-R38 |
| StaircaseStep (new) | step_no, label, lending_to, risk_level, typical_us_etfs, ucits_alternatives, best_for, side_step | int 1–5, text, enum {lowest, low_med, medium, high}, list, list, text, bool | step 5 side_step = true | S09 |
| UcitsEquivalent (new) | us_ticker, ucits_name, ucits_ticker, exchange, currency, hedged, approx_yield, as_of, mapping_confidence | | confidence {stated, reconstructed} | S09 table scrambled |
| TaxContext (new) | country, residence_state, federal_rate_pct, state_rate_pct, muni_in_state_exempt, muni_out_of_state_taxable, wrappers[{name, allowance, unit, tax_year}], as_of, source | %, money, bool | user/profile-owned values (A13); muni flags per residence state (D-DEF-31) | tax facts dated |
| IncomeComparison (new) | instrument_id, nominal_yield, after_tax_yield, real_yield, after_tax_real_yield, tey | % | derived (§7) | ranking basis |
| BondLadder | not modelled from sources | – | – | placeholder for future; see §9 |

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `bonds.inflation_input` | latest headline CPI YoY Observation (A11) | – | % | S09 (BLS CPI) |
| `bonds.rate_shock_pp` | 1.0 | > 0 | percentage points | S09 ("a 1% rate increase") |
| `bonds.hy_downturn_drawdown_pct` | 15–25 (show range) | – | % price fall | S09 |
| `bonds.hy_economy_horizon_years` | 1–2 | – | years | S09 ("next 1 to 2 years") |
| `bonds.barbell_split_short_pct` | 50 | 0–100 | % of fixed-income sleeve in short fund | S09 |
| `bonds.max_staircase_step` | 3 (every profile) | 1–4 (step 5 is a side step, R-A10-003) | step | S09 ("as high as you are comfortable"); D-DEF-28 |
| `bonds.rebalance_cadence` | monthly review | monthly | — | D-R38 |
| `bonds.hy_trend_exit` | true (step 4 only) | true | — | D-R38 (A07 trend exit, 150-SMA) |
| `bonds.tax_rate_federal_pct` | from TaxContext (no default) | 0–100 | % | S09 example 37 |
| `bonds.tax_rate_state_pct` | from TaxContext (no default) | 0–100 | % | S09 example CA 13 |
| `bonds.oas_thin_threshold_bp` | 300 | 200–450 | bp (below = "thin cushion") | S09 (246 bp "historically thin"); D-DEF-29 |
| `bonds.short_duration_max_years` | 3 | 1–4 | years (≤ = short) | S09 (SGOV/VCSH "short", LQD ~8 "long"); D-DEF-30 |
| `bonds.long_duration_min_years` | 7 | 5–10 | years (≥ = long; in between = intermediate) | D-DEF-30 |
| `bonds.muni_state_tax_treatment` | in-state exempt; out-of-state taxed at the residence state rate; national funds out-of-state unless the in-state share is published | per TaxContext | — | D-DEF-31 |
| `bonds.muni_applicable_countries` | [US] | fixed | ISO list | S09 |

## 5. Rules

### 5.1 Staircase classification
- **R-A10-001** (hard, METHOD) — Every bond and bond fund MUST map to exactly one StaircaseStep: 1 = government / cash proxy (US Treasuries, T-bill and floating-rate Treasury funds; UK/EU equivalents: short Treasury UCITS, short gilts, EUR overnight); 2 = USD-denominated EM sovereigns; 3 = investment-grade corporates; 4 = high-yield corporates; 5 = US municipals (side step). _Sources: S09_
- **R-A10-002** (hard, METHOD) — Risk levels per step MUST be: 1 lowest, 2 low–medium, 3 medium, 4 high, 5 low–medium; a step's risk label is never lowered by its yield. _Sources: S09_
- **R-A10-003** (soft, METHOD) — The user SHOULD climb only up to `bonds.max_staircase_step` (default 3, every profile); a buy above it raises a warning, and raising the maximum to 4 is a PersonalRuleSet revision (A12). The muni side step (5, risk low–medium) is available to US tax residents whenever the maximum is ≥ 2. Holdings MAY span several steps at once. _Sources: S09. Decision: D-DEF-28_
- **R-A10-004** (hard, CORE) — Step-1 funds with ultra-short maturities (T-bill / 0–3 month / 0–1 year Treasury funds) MUST be reported to A09 as [[cash-like-instrument]]. _Sources: S09. Decision: D-C24_
- **R-A10-005** (hard, CORE) — A fund's rating mix determines Step 3 vs 4: bonds below BBB-/Baa3 are high yield. _Sources: S09, S10_

### 5.2 Comparing income
- **R-A10-010** (hard, METHOD) — Income instruments MUST be ranked by after-tax real yield, never by headline yield alone. _Sources: S09_
- **R-A10-011** (hard, CORE) — Real yield = nominal yield − `bonds.inflation_input`; the inflation value and its asOf MUST be displayed next to every real figure. _Sources: S09, S28. Decision: D-C22_
- **R-A10-012** (hard, CORE) — A negative real yield MUST be labelled "losing purchasing power"; for cash-like holdings the A09 eroding flag applies. _Sources: S09. Decision: D-C24_
- **R-A10-013** (hard, CORE) — Tax-equivalent yield = muni yield ÷ (1 − federal rate) and MUST be computed only for US tax residents; for other investors Step 5 MUST show "not applicable" and no UCITS equivalent. _Sources: S09_
- **R-A10-014** (soft, CORE) — US Treasury income MUST be treated as exempt from state/local tax when computing after-tax yield for US investors with a state rate. _Sources: S09_
- **R-A10-015** (soft, CORE) — After-tax figures MUST state the tax facts' asOf; tax benefits SHOULD be shown as subject to change (no assumption that they persist). _Sources: S09_
- **R-A10-016** (soft, CORE) — Fund yields MUST carry yield type (SEC/distribution), as-of and source; "approximately" values keep their range (e.g. 4.5–5.2%). _Sources: S09_

### 5.3 Duration and rate risk
- **R-A10-020** (hard, CORE) — For every fund with a duration, the app MUST show the price impact of a `bonds.rate_shock_pp` rise: ≈ −duration × shock. _Sources: S09_
- **R-A10-021** (soft, CORE) — When the user marks rate-rise concern (or an A11 hike-expectation thesis is active), shorter-duration funds SHOULD be highlighted; this is a bias, not an order. _Sources: S09. Decision: D-C25_
- **R-A10-022** (soft, CORE) — Floating-rate Treasury funds MUST be shown as resetting with policy rates (low duration, income rises on hikes). _Sources: S09_
- **R-A10-023** (soft, METHOD) — A [[barbell]] (default 50/50 short/long) MAY be offered within Step 3; its blended yield and duration are weight averages. _Sources: S09_

### 5.4 Credit risk
- **R-A10-030** (soft, METHOD) — Before a Step-4 buy, the entry checklist MUST ask: "Will the economy stay strong enough for these issuers to pay for the next `bonds.hy_economy_horizon_years`?"; a "no" answer SHOULD abort the buy and is journaled. _Sources: S09_
- **R-A10-031** (soft, CORE) — Step-4 holdings MUST display a downturn stress of `bonds.hy_downturn_drawdown_pct`. _Sources: S09_
- **R-A10-032** (soft, CORE) — The fund's OAS MUST be displayed in basis points with asOf; below `bonds.oas_thin_threshold_bp` (300) it is labelled "thin cushion". _Sources: S09. Decision: D-DEF-29_
- **R-A10-033** (soft, CORE) — Step-2 funds MUST show sovereign/political risk (defaults have occurred) and that diversification across many countries cushions single defaults. _Sources: S09_
- **R-A10-035** (soft, CORE) — For IG bond funds, look-through issuer concentration SHOULD be shown (e.g. share of AI/hyperscaler issuers in the IG index), since IG-only mandates (most retirement funds) cannot avoid it. _Sources: S10. Decision: D-C11 (look-through, via A09)_
- **R-A10-036** (soft, CORE) — Demand for new bond deals (cover ratio / bid-to-cover of [[bond-auction]]) SHOULD be stored as A11 Observations; a falling cover ratio is labelled "appetite cooling". _Sources: S10, S28_
- **R-A10-037** (soft, CORE) — The current Step-1 yield is the [[risk-free-rate]] hurdle shown next to any non-yielding asset (gold, silver, Bitcoin) in A11. _Sources: S08, S09_
- **R-A10-034** (soft, METHOD) — Credit observations (spreads, CDS, project-finance issuance) are passed to A11 as Observations; when credit and equity disagree, A11 theses MAY weight credit as the earlier signal. Never a trade trigger. _Sources: S21, S26, S29, S30. Decisions: D-C22, D-C25_

### 5.5 Non-US investors
- **R-A10-040** (hard, CORE) — For UK/EU retail investors each US bond ETF MUST be offered with its UCITS alternative(s) from the UcitsEquivalent table (or "no direct equivalent"). _Sources: S09, S21_
- **R-A10-041** (soft, CORE) — A USD fund held by a non-USD investor without hedging MUST carry an FX-risk flag; hedged or home-currency alternatives SHOULD be listed. _Sources: S09_
- **R-A10-042** (soft, CORE) — UK wrapper facts (ISA allowance, Personal Savings Allowance, gilt CGT exemption only for directly held gilts) are dated TaxContext data and MUST be re-validated per tax year. _Sources: S09_
- **R-A10-043** (soft, CORE) — Every report MUST list the risk factors: interest rate, credit, inflation, currency, liquidity (NAV discount, A01), political/geopolitical, tax. _Sources: S09_

### 5.6 Round-3 additions (2026-10-26)
- **R-A10-044** (hard, METHOD) — Bond funds are strategic allocation holdings: they are bought to a target weight per staircase step (`BondAllocation`), rebalanced to target at the monthly review (`bonds.rebalance_cadence`), and are not subject to the A02 scoreboard gate or the A06 breakout entry. Allocation buys are still placed in a ReviewSession and pass the A09 portfolio gate. _Decision: D-R38_
- **R-A10-045** (hard, METHOD) — Exception: step-4 (high-yield) holdings additionally carry the A07 trend exit: a daily close below the 150-SMA creates a market-on-open sell for the next session (A07 R-A07-006, R-A07-040). A sold high-yield allocation is re-bought only at a later monthly review and not while its last close is below the 150-SMA. _Decision: D-R38, D-C05, D-C26, D-R16_
- **R-A10-046** (soft, CORE) — For US tax residents, muni income MUST be taxed per `bonds.muni_state_tax_treatment` using the user's `TaxContext.residence_state`: in-state munis are exempt from the state rate, out-of-state munis are taxed at it, and a national fund counts as out-of-state unless it publishes its in-state share (then pro rata). _Decision: D-DEF-31_
- **R-A10-047** (soft, CORE) — Every bond fund with a duration MUST be labelled `short` (≤ `bonds.short_duration_max_years`, 3), `long` (≥ `bonds.long_duration_min_years`, 7) or `intermediate`; the barbell (R-A10-023) pairs a short with a long fund. _Decision: D-DEF-30_

## 6. Processes
**PR-A10-01 Staircase selection** — Trigger: user explores income / A09 R-A09-051 note. Inputs: TaxContext, `bonds.max_staircase_step`, latest CPI Observation, BondFund data. Steps:
1. Explain stocks (owner) vs bonds (lender) and the seesaw (education item, A12).
2. Show steps 1..5 with yield, real yield, after-tax real yield, risk, ETFs (US or UCITS by investor domicile).
3. Compute TEY for munis if US resident; otherwise mark Step 5 n/a.
4. For Step 4 run the economy question (R-A10-030).
5. Show duration stress and risk factors; output a ranked IncomeComparison list.

**PR-A10-02 Fixed-income monitoring** — Trigger: new CPI release, monthly review. Steps: refresh yields/duration/OAS (as-of) → recompute real yields → pass cash-like real yields to A09 (eroding) → rebalance `BondAllocation` targets (R-A10-044) → refresh A11 observations (10y, real 10y, 30y). Daily: the 150-SMA trend exit for step-4 holdings runs as A07 automation (R-A10-045).

**PR-A10-03 UCITS lookup** — Trigger: non-US investor selects a US fund. Steps: identify tracked index/strategy → look up UcitsEquivalent → check domicile prefix (IE/LU) and Acc/Dist class (A01) → show currency/hedging.

## 7. Calculations
```
real_yield            = nominal_yield − inflation_yoy                      # pp
after_tax_yield       = nominal_yield × (1 − t_fed − t_state)              # simple additive model; Treasuries: t_state = 0
                                                                           # munis: t_fed = 0; t_state = 0 in-state, residence rate out-of-state (D-DEF-31)
after_tax_real_yield  = after_tax_yield − inflation_yoy
TEY                   = muni_yield / (1 − t_fed)                           # US only; in-state: muni_yield / (1 − t_fed − t_state)
after_tax_muni        = muni_yield × (1 − t_state × out_of_state_share)    # D-DEF-31
duration_bucket       = short if D ≤ 3; long if D ≥ 7; else intermediate    # D-DEF-30
after_state_yield     = yield × (1 − t_state)                              # S09 California example
price_change_pct      ≈ −duration_years × Δyield_pp                        # first-order seesaw
barbell_yield         = w_s × y_short + (1 − w_s) × y_long
barbell_duration      = w_s × D_short + (1 − w_s) × D_long
income_per_year       = principal × yield × (1 − applicable tax)
spread_bp             = (y_credit − y_government_same_maturity) × 100
breakeven_inflation   = nominal_10y − real_10y                             # derived, market-implied
```

## 8. Examples / fixtures
**EX-A10-01 Staircase snapshot (S09, July 2026; CPI 4.2% May 2026)**
| Step | Lending to | US ETFs | Yield | Real yield | Risk |
|---|---|---|---|---|---|
| 1 | US government | SGOV ~3.8%, USFR ~3.84% | ~3.8% | −0.4 pp | lowest |
| 2 | USD EM sovereigns ("countries America protects") | EMB ~5.8% (SEC 5.77%) | ~5.8% | +1.6 pp | low–medium |
| 3 | IG corporates | VCSH ~4.4%, LQD ~4.5–5.2% (~8 y duration) | 4.4–5.2% | +0.2 to +1.0 pp | medium |
| 4 | High yield (mostly BB/B) | HYG ~6.5% (SEC 6.50%, OAS 246 bp) | ~6.5% | +2.3 pp | high |
| 5 | US munis (side step) | VTEB ~3.5% (SEC 3.49%), MUB ~3.0% | 3.0–3.5% tax-free | −1.2 to −0.7 pp nominal; TEY 4.76–5.56% @37% | low–medium |
Then each fund maps to the step shown (R-A10-001) and real yields equal yield − 4.2.

**EX-A10-02 Tax-equivalent yield (S09)** — Given VTEB 3.5%, federal rate 37%. Then TEY = 3.5 / 0.63 = 5.56%. MUB 3.0% → 4.76%. Edge: investor domiciled in DE → Step 5 "not applicable" (R-A10-013).

**EX-A10-03 Muni vs savings, $1M (S09)** — Given $1,000,000, savings 3% taxed at 37% vs VTEB 3.5% federal-tax-free. Then keep $18,900 vs $35,000 → difference $16,100/yr; at $5M: $94,500 vs $175,000 → $80,500 ("$80,000+").

**EX-A10-04 Headline vs after-tax (S09 claim check)** — Given HYG 6.5% taxed at 37% and VTEB 3.5% tax-free. Then HYG after-tax = 4.10% > 3.5%; VTEB's TEY 5.56% < 6.5%. Result: at a 37% rate the muni wins only if HY credit losses exceed ~0.6 pp/yr; the app must show both numbers rather than repeat the source's claim (R-A10-010).

**EX-A10-05 State tax (S09)** — Given California 13% state tax, savings 3.8% vs SGOV 3.8%. Then savings after state tax = 3.31%; SGOV keeps 3.8% (state-exempt, R-A10-014).

**EX-A10-06 Seesaw (S09)** — Given LQD duration ~8 years, rates +1 pp. Then price ≈ −8%; funds with 7–8 years → −7 to −8%; SGOV (≈0.1–0.25 y maturity) ≈ flat. Labels (D-DEF-30): LQD ~8 y → long; SGOV → short.

**EX-A10-07 Barbell (S09)** — Given 50% VCSH (4.4%) + 50% LQD (4.5–5.2%). Then blended yield 4.45–4.80%; blended duration needs VCSH duration (not given in source → shown as unknown).

**EX-A10-08 High-yield gate (S09)** — Given a user answers "no" to the 1–2 year economy question. Then the HYG buy is aborted with journal note "coins on a train track"; answering "yes" shows the 15–25% downturn stress and "thin cushion" because OAS 246 bp < 300 bp (D-DEF-29). With the default `bonds.max_staircase_step` = 3, the HYG buy also raises the step warning (R-A10-003).

**EX-A10-09 UCITS mapping (S09 factsheets, July 2026; table reconstructed from scrambled PDF)**
| Step | US | UCITS alternative (ticker, venue) | Approx. yield | Currency note |
|---|---|---|---|---|
| 1 | SGOV/USFR | iShares $ Treasury Bond 0–1yr (IBTS, LSE) | ~3.5–4.0% | USD; hedged classes exist |
| 1 | – | Lyxor Smart Overnight Return (CSH2, Euronext) | ~3.3–3.6% | EUR cash proxy |
| 1 | – | iShares UK Gilts 0–5yr (IGLS, LSE) | ~3.5–4.2% | GBP |
| 2 | EMB | iShares J.P. Morgan $ EM Bond (IEMB, LSE) | ~5.5–6.0% | USD |
| 3 | VCSH | Vanguard USD Corporate 1–3yr (VUSC, LSE) | ~4.0–4.5% | USD |
| 3 | LQD | iShares $ Corp Bond (LQDE, LSE) | ~4.5–5.0% | USD, longer duration |
| 3 | – | iShares Core € Corp Bond (IEAC) | ~3.5–4.0% | EUR |
| 4 | HYG | iShares $ High Yield Corp (IHYU, LSE) | ~6.0–6.5% | USD |
| 4 | – | iShares € High Yield Corp (IHYG) | ~5.0–5.5% | EUR |
| 5 | VTEB/MUB | no direct equivalent (UK: ISA wrapper) | – | – |
All rows `mapping_confidence = reconstructed` for the yield column. Edge: GBP investor holding IBTS unhedged → FX-risk flag (R-A10-041).

**EX-A10-10 UK wrappers (S09, tax year 2026/27)** — ISA allowance £20,000/yr; PSA £500–£1,000 of interest depending on band; gilts CGT-exempt only when held directly, not via ETF (IGLS ETF is not exempt).

**EX-A10-11 Inflation shock (synthetic)** — Given CPI Observation rises from 4.2% to 5.0%. Then real yields: Step 1 −1.2 pp, Step 2 +0.8, Step 3 −0.6 to +0.2, Step 4 +1.5 — only Step 4 stays clearly positive (consistent with S09 "inflation risk").

**EX-A10-12 Oct 2026 reference yields (S29, S28)** — Given 10y Treasury 5.00% and 10y real (DFII10) 2.67%. Then breakeven inflation (derived) = 2.33 pp; these are A11 Observations, not A10 fund yields.

**EX-A10-13 IG issuer concentration (S10, July 2026)** — Given hyperscaler bonds ≈ 4% of the IG index and AI bond issuance ~$240B in H1 2026 (18% of supply). Then an IG fund holder sees "AI issuers ≈ 4% of index" in look-through; tech ≈ 20% of US IG issuance (record) is stored as an A11 Observation.

**EX-A10-14 Risk-free hurdle (S08/S09, mid-2026)** — Given SGOV ~3.8% (S09). Then gold needs > 3.8%/yr to beat Step 1; S08's "4–5%" wording is a separate, rounded Observation.

**EX-A10-15 Muni state tax by residence (synthetic, D-DEF-31)** — Given a California resident (federal 37%, state 13%), an in-state California muni fund yielding 3.2% and VTEB 3.5% (national, no published in-state share). Then in-state: after-tax 3.2%, TEY = 3.2 / (1 − 0.37 − 0.13) = 6.40%; VTEB: after-tax 3.5 × (1 − 0.13) = 3.045%, equivalent to 3.045 / 0.50 = 6.09% taxable. A Texas resident (no state tax) keeps 3.5% on VTEB.

**EX-A10-16 Allocation holding and high-yield exit (synthetic, D-R38)** — Given targets VCSH 10% (step 3) and, after a rule-set change to max step 4, HYG 5%. At the monthly review VCSH has drifted to 8.6% → rebalanced to 10% (no breakout needed). HYG closes on a Wednesday below its 150-SMA → market-on-open sell on Thursday (R-A10-045); VCSH has no trend exit. At the next monthly review HYG's last close is still below its 150-SMA → no re-buy.

## 9. Variants & open points
- S08 cites "4–5% risk-free in Treasuries" vs S09 SGOV ~3.8% (both mid-2026): different measures (rounded text vs fund SEC yield); stored as separate Observations, no conflict flag (D-C22).
- BondLadder (rolling maturities) is a common entity but not described in sources; not specified.
- Bond selection uses no technical entry rules in sources; bond funds are allocation holdings (D-R38).
- Closed by D-DEF-28 — OPEN-A10-1 (max step 3 for every profile; pending user review).
- Closed by D-DEF-29 — OPEN-A10-2 (thin OAS < 300 bp; pending user review).
- Closed by D-DEF-30 — OPEN-A10-3 (short ≤ 3 y, long ≥ 7 y; pending user review).
- Closed by D-DEF-31 — OPEN-A10-4 (muni state tax per residence; pending user review).
- Closed by D-R38 — OPEN-A10-5 (allocation holdings; high yield gets the trend exit).

**Glossary additions (merged into glossary v0.2.0):**
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| after-tax-real-yield | After-Tax Real Yield | CORE | Yield after applicable taxes minus inflation; the ranking basis for income instruments. | S09 |
| ucits-equivalent | UCITS Equivalent | CORE | UCITS fund tracking the same strategy/index as a US-listed ETF, for UK/EU investors. | S09, S21 |
| option-adjusted-spread | Option-Adjusted Spread (OAS) | CORE | Credit spread of a bond or fund adjusted for embedded options, quoted in bp ("risk cushion"). | S09, S18 |

## 10. Traceability
| Rule/Concept | Sources / Decisions |
|---|---|
| R-A10-001..005 staircase | S09, S10; D-C24 |
| R-A10-010..016 comparing income | S09, S28; D-C22, D-C24 |
| R-A10-020..023 duration | S09; D-C25 |
| R-A10-030..037 credit, hurdle | S08, S09, S10, S21, S26, S28, S29, S30; D-C11, D-C22, D-C25 |
| R-A10-040..043 non-US | S09, S21 |
| R-A10-044..047 allocation holdings, HY trend exit, muni state tax, duration buckets | S09; D-R38, D-DEF-30, D-DEF-31 |
| EX-A10-01..12 | S09 (July 2026), S28, S29 (Oct 2026) |
