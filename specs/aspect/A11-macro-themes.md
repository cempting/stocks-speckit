---
id: A11
title: Macro Themes
context: CTX-B
layers: [MACRO, CORE]
status: draft
sources: [S03, S04, S06, S08, S09, S10, S12, S21, S22, S24, S26, S27, S28, S29, S30]
decisions: [D-C22, D-C25, D-C24, D-C11, D-C04, D-C06, D-C07, D-C21, D-C23, D-R27, D-R39, D-DEF-32, D-DEF-33, D-DEF-34, D-DEF-35]
depends_on: [A01, A02, A03, A05, A06, A09, A10, A12]
---
# A11 — Macro Themes

## 1. Purpose & scope
Models macro and thematic domain knowledge as **Observations** (dated facts) and **Theses** (causal claims with
invalidation signs), per D-C22. Themes covered: Fed/central banks, liquidity and money printing, the dollar
(petrodollar, de-dollarization, weaponized dollar), gold and silver (incl. gold buying rules), AI capex/credit and
the AI bubble, quantum, space, drones/defence, energy and geopolitics.

Core invariant: **macro never triggers trades.** A Thesis may only set bias tags, propose watchlist entries,
activate exposure checks (A09) and create review items. Signals and orders come only from A06/A07 rules.

Excluded: business-cycle phase scoring and style regime (A03; "value is dead" thesis owned by A03, D-C25);
industry RS scoreboard (A02); bond instruments and yields math (A10); exposure computation (A09).

## 2. Concepts
- [[macro-observation]] — dated fact; [[observation-conflict]] — same metric/date/type disagreeing.
- [[macro-thesis]] — recorded causal claim; [[invalidation-sign]] — pre-stated condition proving it wrong.
- [[macro-theme]] — structural theme mapped to industries/baskets; [[macro-scenario]] — mutually exclusive pathways.
- Fed/central banks: [[federal-reserve]], [[fomc]], [[fed-funds-rate]], [[policy-rate]], [[dot-plot]], [[forward-guidance]], [[fed-put]], [[dual-mandate]], [[higher-for-longer]], [[rate-divergence]], [[central-bank]], [[central-bank-balance-sheet]].
- Liquidity/debt: [[liquidity-macro]], [[quantitative-easing]], [[quantitative-tightening]], [[stealth-printing]], [[treasury-buyback]], [[treasury-general-account]], [[national-debt]], [[interest-bill]], [[financial-repression]], [[crowding-out]], [[margin-debt]], [[long-bond-yield]], [[real-yield]].
- Dollar: [[reserve-currency]], [[petrodollar]], [[de-dollarization]], [[dollar-weaponization]], [[debasement]], [[debasement-trade]], [[gold-window]], [[strategic-petroleum-reserve]].
- Metals: [[gold-asset]], [[silver-asset]], [[hard-asset]], [[safe-haven-asset]], [[central-bank-gold-buying]], [[gold-custody]], [[opportunity-cost-non-yielding]], [[bullion]], [[spot-price]], [[exchange-traded-commodity]].
- AI: [[hyperscaler]], [[hyperscaler-capex]], [[ai-debt]], [[circular-financing]], [[ai-bubble-thesis]], [[index-concentration]], [[credit-default-swap]], [[project-finance]].
- Tech themes: [[technology-adoption-curve]], [[index-inclusion-effect]], [[ipo-trap]], [[picks-and-shovels]], [[toll-booth-business]].
- Energy: [[five-waves-of-capital-flow]].

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Observation | id, metric, value, unit, asOf, measureType, source | key, number/range/text, unit, date or period, enum, ref | all required (D-C22) | facts only |
| Observation | origin, citedBy, region, note | text, Sxx, ISO, text | origin = primary publisher if known | e.g. origin "EIA", citedBy "S21" |
| Observation | measureType | enum {spot, close, auction, decision, nowcast, estimate, survey, trailing_12m, smoothed_3m, ytd, period_total, projection, forecast, target_level, event} | | forecasts are signals, not facts |
| Observation | conflict_flag, conflict_with[] | bool, ids | set by R-A11-004 | never reconciled |
| Thesis | id, title, theme_id, statement, causal_chain[], author, created, sources[], horizon | | statement ≠ rule | |
| Thesis | supporting_observations[], counter_observations[] | Observation ids | | |
| Thesis | invalidation_signs[] | InvalidationSign | count ≥ `macro.min_invalidation_signs` to activate | S28 style |
| Thesis | status | enum {draft, active, under_review, weakened, retired} | lifecycle below | |
| Thesis | bias_targets[{industry/theme/asset, direction ±}] | | effects limited by R-A11-010 | |
| InvalidationSign (new) | name, worry_condition, metric, threshold, data_source, cadence, state {not_turned, turned}, last_checked | | threshold may be qualitative | |
| MacroTheme (new) | id, name, industries[], companies[], baskets[], theses[] | | feeds A09 ThemeMap | |
| MacroScenario (new) | id, pair_id, name, causal_chain[], triggers[], sector_impacts[{sector, hurt/helped}], probability_user | | pairs mutually exclusive | S06 |
| MacroReview (new) | date, theses_checked, signs_turned[], actions | | monthly | in ReviewLog (A12) |

Thesis lifecycle: `draft → active` (≥ min signs written) · `active → under_review` (≥1 sign turned) · `under_review → weakened` (all signs turned) · `under_review/weakened → active` (signs revert) · any `→ retired` (user).

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `macro.min_invalidation_signs` | 3 | ≥1 | count | S28 |
| `macro.review_cadence` | monthly | {monthly} (not intraday) | – | S28 ("once a month, not once an hour"); D-C04 |
| `macro.one_sign_action` | review position size of theme exposure | – | – | S28 |
| `macro.all_signs_action` | thesis weakened; review all bias | – | – | S28 |
| `macro.conflict_tolerance` | max(1% of \|value\|, one unit of the last reported digit), after unit normalisation | ≥ 0 | unit of metric | D-C22; D-DEF-32 |
| `macro.approx_value_tolerance_pct` | 5 | 1–10 | % (values marked "~" are compared as ±5% intervals; ranges conflict only if they do not overlap) | D-DEF-32 |
| `macro.real_yield_series` | FRED DFII10 | – | series id | S28 |
| `macro.cb_gold_baseline_t_month` | 17 | – | tonnes/month | S28 (pre-2022 avg, Goldman/WGC) |
| `macro.gold_premium_max_pct` | 10 | – | % over spot, standard 1 oz coin/bar | S28 |
| `macro.gold_premium_indicative` | 1 oz coin 3–8; small bars 1–100 g 5–15+; 1 kg 1–3 | – | % | S28 |
| `macro.gold_storage_kind` | allocated | {allocated} | enum | S28 ("always choose allocated") |
| `macro.observation_stale_days` | daily market series 5 sessions; weekly 14; monthly releases 45; quarterly 120; annual, estimates and forecasts 400 | > 0 | days (sessions for daily) per metric family | D-DEF-33 |
| `macro.vault_recommend_min_usd` | 25,000 | > 0 | USD equivalent of physical holdings | D-DEF-34 |

## 5. Rules

### 5.1 Observations (D-C22)
- **R-A11-001** (hard, MACRO) — Every macro fact MUST be stored as an Observation with metric, value, unit, asOf, measureType and source; a value without asOf MUST be rejected. _Decision: D-C22_
- **R-A11-002** (hard, MACRO) — Observations MUST NOT be averaged, reconciled or overwritten; a new value is a new Observation. _Decision: D-C22_
- **R-A11-003** (hard, MACRO) — Second-hand figures MUST record `origin` (e.g. EIA, IMF COFER, Goldman) and `citedBy` (Sxx). _Sources: S21, S24, S28, S29_
- **R-A11-004** (hard, MACRO) — If two Observations share metric, asOf and measureType but values differ beyond `macro.conflict_tolerance` (max of 1% and one unit of the last reported digit; "~" values as ±`macro.approx_value_tolerance_pct` intervals; ranges only when they do not overlap), both MUST get `conflict_flag`; different measureTypes (e.g. spot vs auction) or different asOf never conflict. _Decision: D-C22, D-DEF-32_
- **R-A11-005** (soft, MACRO) — Third-party forecasts, targets and projections MUST use measureType forecast/target_level/projection and be displayed as "signal of direction, not guarantee". _Sources: S27, S28_
- **R-A11-006** (soft, MACRO) — Observations SHOULD be refreshed in the monthly macro review; an Observation older than `macro.observation_stale_days` for its metric family (daily 5 sessions, weekly 14, monthly 45, quarterly 120, annual/estimate/forecast 400 days) is greyed as stale. _Sources: S28. Decision: D-C04, D-DEF-33_

### 5.2 Theses and invalidation
- **R-A11-007** (hard, MACRO) — A Thesis MUST be stored separately from Observations and MUST reference the Observations it relies on. _Decision: D-C22_
- **R-A11-008** (hard, MACRO) — A Thesis MUST NOT become `active` until at least `macro.min_invalidation_signs` InvalidationSigns are written (worry condition + data source). _Sources: S28_
- **R-A11-009** (soft, MACRO) — Signs MUST be checked at `macro.review_cadence`; one turned → status `under_review` and a size review of related theme exposure; all turned → `weakened`. A turned sign never auto-sells. _Sources: S28. Decisions: D-C27, D-C26_
- **R-A11-010** (hard, MACRO) — A Thesis (any status) MUST NOT create a Signal, Order, ExitTrigger, stop change or sizing change. Permitted effects: bias tags on industries/themes, watchlist proposals, activation of A09 exposure checks, coaching prompts. _Decisions: D-C25, D-C06/C07 (entry needs A06 checklist)_
- **R-A11-011** (hard, METHOD) — An instrument suggested by a Thesis MAY enter the Watchlist; a buy still requires the A06 checklist (heartbeat breakout on volume, rising 50-SMA, above 150-SMA) and the A09 gate. _Sources: S30 ("the rules do not change with what you are buying"), S22. Decisions: D-C06, D-C07_
- **R-A11-012** (soft, METHOD) — Short-term drivers and the long-term story of a theme SHOULD be recorded as separate Theses so a short-term scare does not retire the long-term one. _Sources: S28_
- **R-A11-013** (soft, METHOD) — When credit-market and equity-market Observations disagree for a theme, the Thesis view SHOULD note credit as the earlier signal ("behaviour beats opinion"). _Sources: S21, S26, S27, S30_
- **R-A11-014** (soft, METHOD) — A user SHOULD NOT hold a single-asset thesis without written invalidation signs ("don't fall in love with any single asset"). _Sources: S28_

### 5.3 Scenarios
- **R-A11-020** (soft, MACRO) — MacroScenarios MUST come in mutually exclusive pairs with causal chains and user-defined triggers; they feed A09 scenario exposure checks only. _Sources: S06. Decision: D-C25_
- **R-A11-021** (soft, MACRO) — Triggers (e.g. oil levels, Fed/ECB decisions, jet-fuel futures) are written in advance and, when hit, create review items, not orders. _Sources: S06. Decision: D-C25_

### 5.4 Theme mapping
- **R-A11-030** (hard, MACRO) — Each MacroTheme MUST list the industries (per ClassificationScheme), companies and baskets it covers, so A09 can compute [[theme-exposure]] including index funds. _Sources: S27, S29, S30. Decisions: D-C11, D-C21_
- **R-A11-031** (soft, METHOD) — Within a theme, supplier/toll-booth companies ("who owns the pipes") SHOULD be tagged so A05 can prefer them; tagging is information, not selection. _Sources: S22, S24_
- **R-A11-032** (soft, MACRO) — A technology theme SHOULD carry an adoption-curve phase (hype, crash, boredom, second wave) as an Observation of type estimate. _Sources: S22_

### 5.5 Gold & silver buying rules
- **R-A11-040** (soft, METHOD) — Decide size before timing: a gold allocation target (A09 `portfolio.gold_allocation_target_pct`) SHOULD be set before any purchase. _Sources: S28_
- **R-A11-041** (hard, METHOD) — Every gold form (physical/allocated, ETFs/ETCs, miners) goes through the signal engine: a buy requires the A06 entry checklist (heartbeat breakout on ≥ 2× volume) and exits follow A07. Price levels written while calm (S28 "add toward $4,000") MAY only be stored as watchlist price alerts; level-based buying is not canonical. Size before timing still applies (R-A11-040, A08 sizing, A09 concentration). _Sources: S28, S30. Decisions: D-R39, D-C06/C07_
- **R-A11-042** (hard, CORE) — A premium above `macro.gold_premium_max_pct` over spot on a standard 1 oz bullion coin or bar MUST be flagged "walk away" (collector pieces excepted). _Sources: S28_
- **R-A11-043** (hard, CORE) — Vault storage MUST be allocated (specific bars in the owner's name); unallocated claims MUST be flagged as unsecured-creditor risk. _Sources: S28_
- **R-A11-044** (soft, CORE) — Dealers SHOULD be long-established, in the LBMA good-delivery chain, with live pricing and a published buyback price; physical holdings above `macro.vault_recommend_min_usd` ($25,000) SHOULD go to a professional allocated vault. _Sources: S28. Decision: D-DEF-34_
- **R-A11-045** (soft, CORE) — EU investors get physical gold via ETCs (single-commodity gold cannot be a UCITS fund); the app MUST label such products as ETC, not fund (A01). _Sources: S28_
- **R-A11-046** (soft, MACRO) — Gold and silver miners MUST be tagged as leveraged, sentiment-driven exposure to the metal, distinct from bullion; uncertain single-miner timing → industry basket (GDX/SIL) preferred. _Sources: S08, S30. Decision: D-C21_
- **R-A11-047** (soft, MACRO) — Non-yielding assets MUST be shown against the risk-free rate hurdle ([[opportunity-cost-non-yielding]]); rising real yields are a headwind indicator for the gold thesis. _Sources: S08, S28_
- **R-A11-048** (soft, MACRO) — At data integration, conflicting Observations about an official decision (e.g. an FOMC vote) SHOULD be verified against the issuing body's primary statement; the verified value is stored as a new Observation with that statement as source and linked to the conflicting ones, which stay unchanged and flagged (no overwrite, R-A11-002). _Decision: D-R27, D-C22_

### 5.6 Round-3 additions (2026-10-26)
- **R-A11-049** (hard, METHOD) — Physical gold (bullion, allocated vault) has no live broker stop: its protective stop and trend exit are implemented as price alerts with a manual sale task (A07 R-A07-043), and the holding carries the sanctioned flag UNPROTECTED_EXCEPTION. _Decision: D-R39_
- **R-A11-050** (soft, MACRO) — Every invalidation sign SHOULD state a measurable threshold, its metric and data source (§8.2); sourced qualitative signs (TH-07, S28) are kept in the source's wording. _Sources: S28. Decision: D-DEF-35_

## 6. Processes
**PR-A11-01 Observation intake** — Trigger: research document, data feed, user entry. Steps: parse metric/value/unit/asOf/type/source → normalise unit → store → conflict check (R-A11-004) → link to Theses.

**PR-A11-02 Thesis authoring** — Trigger: user or research report. Steps: statement + causal chain → supporting/counter Observations → write ≥3 invalidation signs (metric, worry condition, source) → bias targets → activate (R-A11-008).

**PR-A11-03 Monthly macro review** (within monthly review, D-C04) — Steps: refresh Observations of each active Thesis → evaluate each sign → update status (R-A11-009) → list bias changes → trigger A09 PR-A09-05 for active scenarios → write MacroReview to ReviewLog. Not run intraday.

**PR-A11-04 Gold purchase plan** (S28 four steps, adapted per D-R39) — 1 separate short-term story (rates, dollar, forced selling) from long-term story (CB buying); 2 size before timing (A09 target, A08 sizing); 3 set watchlist alert levels while calm (alerts only, no level-based buying); 4 check real return of cash/pension (A09 eroding). Then choose route: physical (premium check), allocated vault, gold-backed fund/ETC, miners; buy only on an A06 confirmed breakout; exits per A07 (alert-based for physical, R-A11-049).

## 7. Calculations
```
conflict(a,b)       = a.metric == b.metric and a.asOf == b.asOf and a.measureType == b.measureType
                      and |norm(a.value) − norm(b.value)| > macro.conflict_tolerance
signs_turned        = count(sign.state == turned)
status              = active if signs_turned == 0; under_review if 0 < signs_turned < n; weakened if == n
premium_pct         = (price_paid − spot × fine_oz) / (spot × fine_oz) × 100
cb_buying_multiple  = monthly_tonnes / macro.cb_gold_baseline_t_month
tonnes_to_oz        = tonnes × 32,150
purchasing_power    = CPI_base / CPI_now                    # $1 (1971) ≈ $0.12 today → −88%
real_yield          = nominal − inflation                    # A10
```

## 8. Examples / fixtures
### 8.1 Dated observation tables (values as cited; `≈` kept)
**Fed / central banks**
| Metric | Value | Unit | asOf | measureType | Source |
|---|---|---|---|---|---|
| fed_funds_target_range | 3.50–3.75 | % | 2026-06 (FOMC) | decision | S08, S09, S06 |
| fomc_dots_expecting_hike | 9 of 18 | count | 2026-06 | projection | S08 |
| fomc_dots_expecting_cut | 1 of 18 | count | 2026-06 | projection | S08 |
| fomc_vote | unanimous | text | 2026-06 meeting | decision | S08 |
| fomc_vote | 8–4 split ("most divided since 1992") | text | 2026-06 (meeting not named) | decision | S06 |
| us_nonfarm_payrolls_change | +57,000 | jobs | 2026-06 | close | S08 |
| us_cpi_yoy | 4.2 | % | 2026-05 | close | BLS via S09 |
| ecb_policy_rate | 2.25–2.40 (hiking) | % | 2026-06 | decision | S06 |
| eurozone_gdp_q1 | −0.2 | % | 2026-Q1 | close | S06 |
| fed_balance_sheet | > 6.7 | USD tn | 2026-06 | spot | S06 |
| fed_hike_probability_oct | ~70 | % | 2026-09-28 | estimate (market-implied) | UBS via S28 |
| hikes_priced_by_end_2027 | 3 (UBS expects 1, Dec) | count | 2026-09-28 | estimate / forecast | UBS via S28 |

**Liquidity / debt / bond market**
| Metric | Value | Unit | asOf | measureType | Source |
|---|---|---|---|---|---|
| us_national_debt | > 39.4 | USD tn | 2026-07 | spot | JEC via S09 |
| us_national_debt | 39+ (rising ~8 bn/day) | USD tn | 2026-08 | spot | S26 |
| us_national_debt | ~40 ("about to pass") | USD tn | 2026-10 | spot | BofA via S28 |
| us_federal_deficit | ~2 (5 revenue vs 7 spending) | USD tn | FY2026 | projection | CBO via S09 |
| us_interest_bill | 1.4 | USD tn | 2026-08 | trailing_12m | S26 |
| us_interest_bill | ~1.7 /yr by 2028-11 | USD tn | 2026-10 | projection | Hartnett via S28 |
| treasury_buyback_per_operation | 2 → ≥4 | USD bn | from 2026-09-09 | event | S26, S27 |
| tga_balance | ~1 | USD tn | 2026-08-24 | spot | CNBC via S27 |
| us_margin_debt | ~1.5 (≈4.7% of GDP) | USD tn | 2026 mid | spot | FINRA via S12 |
| ust_30y_yield | 5.27 ("highest since 2007") | % | 2026-08 | spot | S26 |
| ust_30y_yield | ~5.25 | % | 2026-08-19/24 | spot | CNBC via S27 |
| ust_30y_auction_yield | 5.126 ("highest in 25 years") | % | 2026-08 | auction | BofA via S28 |
| ust_10y_yield | 5.00 | % | 2026-10 | spot | S29 |
| ust_10y_real_yield (DFII10) | 2.67 | % | 2026-10 | spot | FRED via S28/S29 |
| bond_etf_inflows | 300 | USD bn | 2026-H1 | period_total | SSGA via S09 |

**Dollar / energy / geopolitics**
| Metric | Value | Unit | asOf | measureType | Source |
|---|---|---|---|---|---|
| usd_share_allocated_reserves | < 57 (lowest since 1995) | % | 2026-08 (as cited) | spot | IMF COFER via S24 |
| usd_purchasing_power_vs_1971 | ~0.12 | USD per 1971 USD | 2026 | estimate | BLS CPI via S27, S28 |
| us_spr_level | ~298.7 (lowest since 1983) | mn bbl | 2026-08-10 | spot | EIA via S21, S24 |
| sanctions_action | ~60 entities, 5 sectors incl. gold ("Operation Economic Outcast") | text | 2026-08-24 | event | S27 |
| global_oil_demand | ~93 | mn bbl/day | 2026-08 | estimate | S24 |
| oil_scenario_war | 120–150 | USD/bbl | 2026-06 | projection | S06 |
| oil_scenario_peace | 60–70 | USD/bbl | 2026-06 | projection | S06 |
| us_tariff_foreign_drones | up to 100 | % | 2026-08 | event | S24 |
| china_share_small_drone_supply | ~80 | % | 2026-08 | estimate | WisdomTree/AUVSI via S24 |
| energy_vs_sp500_1m | +12 | pp | 2026-10-24 | period_total | S30 |

**Gold & silver**
| Metric | Value | Unit | asOf | measureType | Source |
|---|---|---|---|---|---|
| gold_spot | > 5,500 (pre-crash) | USD/oz | 2026-01-30 | spot | S08 |
| gold_one_day_change | −18 | % | 2026-01-30..02-02 | close | S08 |
| silver_change_crash | −30+ (from > 120) | % | 2026-01-30..02-02 | close | S08 |
| gold_spot | 4,600–4,700 (above 200-day, first since 2023) | USD/oz | 2026-08 | spot | Kitco/Reuters via S27 |
| gold_target_ye2026 | 4,900 | USD/oz | 2026-08 | forecast | Goldman via S27 |
| spec_gold_futures_buying | ~22 in ~3 weeks | USD bn | 2026-08 | period_total | Reuters/Bloomberg via S27 |
| gold_add_level | ~4,000 (pullbacks) | USD/oz | 2026-09-28 | target_level | UBS via S28 |
| cb_gold_buying | 79 | t | 2026-08 | nowcast | Goldman (2026-10-19) via S28 |
| cb_gold_buying | 85 | t/month | 2026-08 | smoothed_3m | Goldman via S28 |
| cb_gold_buying | 100 | t/month | 2026-06 | smoothed_3m | Goldman via S28 |
| cb_gold_buying | ~1,000 /yr for 4 yrs | t | 2026-09-28 | estimate | UBS/WGC via S28 |
| cb_managers_expect_to_add | 89 | % | 2026 | survey | WGC via S27 |
| nyfed_foreign_gold_custody_change | −40 | t | 2026-08 | period_total | S28 |
| boe_gold_custody_change | +46 | t | 2026-08 | period_total | S28 |
| gold_miners_fcf_yield | ~10 (50-yr avg ~4.1) | % | 2026-08-10 | estimate | via S21 |
| gold_miners_p_nav | ~0.8 (50-yr avg ~1.44) | x | 2026-08-10 | estimate | via S21 |
| miners_qualifying_setups | 0 of 50 (20–62% below highs) | count | 2026-07 | spot | S08 |
| silver_options_target | 90 within ~3 months | USD/oz | 2026-08 | forecast (positioning) | S27 |

**AI capex / credit / bubble**
| Metric | Value | Unit | asOf | measureType | Source |
|---|---|---|---|---|---|
| hyperscaler_ai_capex | ~725 (2025: ~400–410) | USD bn | 2026 (as of 2026-07) | estimate | via S12 |
| big_tech_ai_spend | ~700 | USD bn | 2026 (as of 2026-08) | estimate | S27 |
| ai_bond_issuance | ~240 (18% of IG supply) | USD bn | 2026-H1 | period_total | Goldman via S10 |
| ai_related_debt | ~1.8 | USD tn | 2026-06 | estimate | S06 |
| hyperscaler_leverage | 0.9x → 1.8x | x | 2026-06 | estimate | S06 |
| hyperscaler_capex_to_ocf | ~100 | % | 2026-07 | estimate | S10 |
| nvda_5y_cds | ~41.6 (late May) → ~77.5; record ~83.7 on 2026-07-29 | bp | 2026-08-10 | spot | via S21 |
| hyperscaler_net_buybacks | −147 (2024: +190) | USD bn/yr | 2026-08-11 | estimate | Nomura via S21 |
| usd_project_finance_issuance | ~105 (old record ~25) | USD bn | 2026-10-13 | ytd | S29 |
| junk_datacentre_spread_change | > 2x since late June | ratio | 2026-10 | spot | Goldman/iBoxx via S29 |
| sp500_top10_weight | 38–40 | % | 2026-06 | spot | S04 |
| sp500_top10_weight | 36–37 (norm 18–23) | % | 2026-07 | spot | RBC via S12 |
| sp500_nvda_weight / top5 | ~8 / ~30 | % | 2026-10-24 | spot | S30 |
| boom_tech_share_of_market | 49 (bubbles burst ~40) | % | 2026-10-24 | estimate | S30 |
| sp500_trailing_pe | 31.83 (long-term avg 16.22) | x | 2026-06-05 | spot | multpl via S04 |
| ai_basket_corr_sp500 | 0.73 → 0.91 | coef | since 2026-10-14 | estimate | Goldman via S29 |
| gs_pb_tech_net_selling_2w | −3.3 | SD | 2026-10-19 | estimate | Goldman via S29 |
| nasdaq_drawdown_from_2026-10-06_peak | ~7 | % | 2026-10-24 | close | S30 |
| ai_bust_sp500_impact | −30 | % | 2026-10 | forecast | T.S. Lombard via S30 |

**Quantum / space / drones**
| Metric | Value | Unit | asOf | measureType | Source |
|---|---|---|---|---|---|
| quantum_market_2040 | ~850 (~30%/yr) | USD bn | 2026-08-14 | forecast | S22 |
| us_gov_quantum_stakes | ~2 in 9 companies (CHIPS Act) | USD bn | 2026-05 | event | S22 |
| quantum_stocks_below_oct2025_peak | 45–70 | % | 2026-08-14 | spot | S22 |
| quantum_adoption_phase | boredom / build-out | phase | 2026-08-14 | estimate | S22 |
| ionq_q2_revenue | 80.1 (+287% YoY) | USD mn | 2026-Q2 | close | S22 |
| spacex_ipo_valuation_expected | > 200 | USD bn | 2026-06-07 | forecast | S03 |
| index_inclusion_forced_selling | ~200 (Tesla Dec 2020 precedent ~50) | USD bn | 2026-06-07 | estimate | S03 |
| spacex_2056_bond_price | ~84 (issued 100, 6.6% coupon) | % of par | 2026-10 | spot | S30 |
| drone_vs_tank_cost | ~500 vs ~10,000,000 (20,000x) | USD | 2026-08 | estimate | S24 |

### 8.2 Theses (status as of 2026-10-26; TH-07 signs from S28, all other numeric signs are defaults per D-DEF-35, pending user review)
| Id | Theme | Statement (causal chain) | Sources | Invalidation signs |
|---|---|---|---|---|
| TH-01 | Fed | Forward guidance switched off, Fed put may be gone → more volatility; selling rules matter more | S08 | (1) FOMC statements carry explicit forward-guidance language at 2 consecutive meetings; (2) the chair's projection is again shown in the dot plot; (3) VIX 3-month average < 15 (Cboe) |
| TH-02 | Fed | Higher-for-longer → debt-laden/zombie firms hurt first; quality favoured | S08, S28 | (1) ≥ 3 FOMC cuts totalling ≥ 75 bp within 12 months (FOMC statements); (2) 5y Treasury yield < 3.25% (Hartnett level for the interest bill; FRED DGS5); (3) fed funds upper bound ≤ 3.00% |
| TH-03 | Liquidity | Bills bought by the Fed + Treasury buybacks = stealth printing → cash loses purchasing power → hard assets, toll booths | S26 | (1) buyback size per operation back to ≤ $2 bn (Treasury); (2) Fed bill holdings flat or falling over 3 months (H.4.1); (3) 3-month T-bill yield − CPI YoY ≥ +1.5 pp for 6 consecutive months |
| TH-04 | Debt | Interest bill + debt → financial repression (rates below inflation) | S28 | (1) 3-month T-bill yield − CPI YoY ≥ +1.5 pp for 6 consecutive months; (2) DFII10 ≥ 2.0% for 6 consecutive months (FRED); (3) CBO interest-bill projection revised down ≥ 10% |
| TH-05 | Dollar | Petrodollar trust erodes, de-dollarization gradual ("a dam, not a switch") | S24 | (1) USD share of allocated reserves rises in 2 consecutive quarters (IMF COFER); (2) USD share back ≥ 60%; (3) share of oil trade invoiced in USD reported rising year on year |
| TH-06 | Dollar | Weaponised dollar → reserve managers diversify into gold | S27, S28 | (1) WGC survey: share of central banks expecting to add gold < 50% (from 89%); (2) CB gold buying (3-month smoothed) < 25 t/month (WGC/Goldman); (3) no new sanctions actions involving reserve assets for 12 months |
| TH-07 | Gold | Central banks buying ~5x pre-2022 pace give gold a structural floor | S28 | (1) DFII10: savers paid comfortably above inflation, persistently; (2) CB buying drifts back toward 17 t/month (WGC/Goldman); (3) feared Fed hikes arrive one after another (FOMC statements) |
| TH-08 | Gold | Debt-financed AI accident → policy printing → hard assets rise ("direction, not timing") | S21, S08 | (1)–(3) as TH-07, plus (4) TH-10 retired or weakened |
| TH-09 | Silver | Dual precious/industrial demand independent of Fed; paper/physical gap adds volatility | S08 | (1) industrial silver demand down ≥ 5% year on year (Silver Institute); (2) gold/silver ratio ≥ 100 (3-month average); (3) silver ETP holdings down ≥ 10% over 6 months |
| TH-10 | AI | AI bubble: concentration + leverage = fragility (capex ≈ OCF, circular financing, CDS, project finance); not a crash forecast | S06, S10, S12, S21, S29, S30 | (1) NVDA 5y CDS < 50 bp for 3 months; (2) hyperscaler capex/OCF < 70% for 2 consecutive quarters; (3) data-centre junk spreads back to their late-June 2026 level (change ratio ≤ 1.0x) |
| TH-11 | Quantum | Adoption curve: second wave after boredom; owners of supply chain win | S22 | (1) pure-play aggregate revenue growth < 20% YoY for 2 consecutive quarters; (2) US government quantum funding below the prior year; (3) 3 consecutive positive catalysts without the industry proxy's RS turning positive within 3 months (stall) |
| TH-12 | Space | Mega-IPO index inclusion forces funds to sell other holdings; never buy IPO day one | S03 | event thesis: (1) inclusion completed; (2) 3 months passed after the inclusion date → retire; (3) index provider changes fast-entry rules |
| TH-13 | Drones/defence | Cheap drones shift military spend; tariffs/NDAA protect US suppliers | S24 | (1) US tariff on foreign drones cut below 50%; (2) China share of small-drone supply < 60%; (3) US defence drone procurement budget falls year on year |
| TH-14 | Energy | Oil decides war vs peace pathway; capital flows in five lagged waves; Fed/ECB divergence favours US | S06 | (1) Brent between $70 and $120 for 3 months (neither pathway); (2) Fed and ECB move in the same direction at 2 consecutive meetings; (3) user-defined scenario triggers |
| TH-15 | Cash | Debt reset devalues USD/EUR/GBP → cash is not a safe haven | S30, S26 | (1) real cash yield (3-month T-bill − CPI YoY) > 0 for 3 consecutive months (A09 eroding clears); (2) CPI YoY < 3% for 6 months; (3) real cash yield ≥ +1.5 pp |

### 8.3 Fixtures
**EX-A11-01 Conflict flag (D-C22)** — Given Observation A {fomc_vote, "unanimous", 2026-06 meeting, decision, S08} and B {fomc_vote, "8–4", 2026-06, decision, S06}. When intake runs. Then both Observations are kept and flagged `conflict` (D-R27: the user decided not to pick one); S06's meeting is not named, so its asOf stays "2026-06 (unresolved)". At data integration both are checked against the Fed's published statement; the verified record is linked as a third, primary-source Observation and the two originals stay unchanged (R-A11-048).

**EX-A11-02 No conflict across measure types** — Given 30y yield 5.27% (spot, S26, Aug 2026) and 5.126% (auction, S28, Aug 2026). Then no conflict flag; both displayed with their type.

**EX-A11-03 No reconciliation** — Given S&P top-10 weight 38–40% (2026-06, S04) and 36–37% (2026-07, S12). Then two Observations remain; no average is stored.

**EX-A11-04 Thesis activation** — Given TH-10 drafted with 2 invalidation signs, `min_invalidation_signs` = 3. When the user activates. Then rejected; adding the third sign allows `active`.

**EX-A11-05 Sign turns (S28)** — Given TH-07 active with 3 signs, and a review finds CB buying at 17 t/month. Then 1 of 3 turned → `under_review`; A09 shows a size review of gold exposure; no sell order. If all 3 turn → `weakened`.

**EX-A11-06 Macro never trades (S30, 24 Oct 2026)** — Given TH-07 active with bias "+gold", and the gold chart shows a short (~1 month) heartbeat, weak break, breakdown and falling 50-day line. When the weekly routine runs. Then gold stays on the watchlist with grade "no money behind it"; no Signal is created (R-A11-010, R-A11-011).

**EX-A11-07 Rate-divergence check (S06, June 2026)** — Given TH-14 active (Fed hold 3.50–3.75% vs ECB hiking 2.25–2.40%) and Europe look-through 16.5%. Then A09 flags "drag risk" (≥15%); no allocation change is made automatically.

**EX-A11-08 Gold premium (S28)** — Given spot $4,000/oz. A standard 1 oz coin at $4,440 → premium 11.0% > 10 → "walk away"; at $4,300 → 7.5% → within the 3–8% indicative range, OK. Edge: a collector coin at 11% → no flag.

**EX-A11-09 CB buying multiple (S28)** — 79 t / 17 = 4.6x ("well over 4 times"); 85 / 17 = 5.0x ("nearly 5 times"); 1 t = 32,150 oz.

**EX-A11-10 Purchasing power (S27/S28)** — $1 in 1971 ≈ $0.12 today → loss 88%.

**EX-A11-11 Breakeven (derived, Oct 2026)** — 10y 5.00% − real 2.67% = 2.33 pp market-implied inflation; compared with S09's CPI 4.2% (May 2026) this is a different measure, not a conflict.

**EX-A11-12 Forecast labelling** — Given Goldman's $4,900 year-end gold target (S27). Then it is stored as `forecast` and displayed "signal, not guarantee"; it never feeds real-yield or exposure calculations.

**EX-A11-13 IPO thesis (S03, June 2026)** — Given TH-12 and a user's thin, low-RS holding. Then the review flags it "vulnerable to index-inclusion selling"; a SpaceX day-one buy is rejected by A06 (IPO trap), not by A11.

**EX-A11-14 Unallocated storage** — Given a vault product offering unallocated gold. Then flag "unsecured creditor — choose allocated" (R-A11-043).

**EX-A11-15 Conflict tolerance (D-DEF-32)** — Same metric, asOf and measureType: 5.27 vs 5.25 → difference 0.02 ≤ max(1% × 5.25 = 0.0525, 0.01) → no conflict; 39.4 vs 40 (tn) → 0.6 > max(0.40, 0.1) → conflict; "~40" vs 39.4 → ±5% interval 38–42 contains 39.4 → no conflict; ranges 3.50–3.75 vs 3.75–4.00 overlap → no conflict.

**EX-A11-16 Staleness (D-DEF-33)** — On 2026-10-26 the CPI Observation for 2026-05 (released mid-June) is older than 45 days → stale; the 10y yield of 2026-10-23 (1 session old) is current; the COFER reading as of 2026-08 is current until 120 days have passed.

**EX-A11-17 Gold through the engine (D-R39)** — Given UBS's "add toward $4,000" level (S28) and TH-07 active. Then the level is stored as a watchlist price alert only; when spot touches $4,000 no buy is created. A buy of a gold ETC, a miner basket or coins follows only a CONFIRMED heartbeat breakout (A06) sized per A08; coins then carry the alert-based exit of A07 (EX-A07-30). A household with $30,000 of coins at home gets the vault recommendation ($30,000 > $25,000, D-DEF-34).

## 9. Variants & open points
- S30 vs S06 on cash: S30 (Oct) "money does not go to cash, inflation eats it"; S06 (Jun) peace scenario "inflation dies" — kept as separate Theses (TH-15, TH-14) with different asOf.
- S08 (July) "wait, 0 of 50 miners qualify" vs S21 (Aug) "miners cheapest in 50 years": valuation Observation vs technical state; entry follows A06 (D-C06/C07).
- "Danger money" used for 30y auction yield (S28) and credit spread (S29): two metrics.
- Gold drivers: S08 debasement/Fed, S21 AI accident, S28 central banks — modelled as TH-07/TH-08 plus short-term story.
- Variant (not chosen): S28 level-based buying of strategic physical gold outside the signal engine — all gold forms go through A06/A07 (D-R39).
- Closed by D-DEF-32 — OPEN-A11-1 (conflict tolerance; pending user review).
- Closed by D-DEF-33 — OPEN-A11-2 (staleness per metric family; pending user review).
- Closed by D-R39 — OPEN-A11-3 (all gold forms through the engine; physical exits via alert and manual sale).
- Closed by D-DEF-34 — OPEN-A11-4 (vault above $25,000; pending user review).
- Closed by D-DEF-35 — OPEN-A11-6 (numeric invalidation signs in §8.2; pending user review).

Closed by round-2 decisions (2026-10-26): OPEN-A11-5 (D-R27; keep both FOMC-vote Observations, flag the conflict, verify against the Fed statement at data integration).

**Glossary additions (merged into glossary v0.2.0):**
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| measure-type | Measure Type | MACRO | Kind of observation value (spot, auction, nowcast, survey, forecast, ...), part of the conflict key. | D-C22 |
| allocated-storage (merged; synonym "allocated gold") | Allocated Gold | CORE | Specific numbered bars held in the owner's name, off the vault's balance sheet; unallocated = unsecured claim. | S28 |
| bullion-premium | Bullion Premium | CORE | Amount paid above spot for a coin or bar, covering minting and dealer margin. | S28 |

## 10. Traceability
| Rule/Concept | Sources / Decisions |
|---|---|
| R-A11-001..006 observations | S21, S24, S27, S28, S29; D-C22, D-C04 |
| R-A11-007..014 theses | S21, S22, S26, S27, S28, S30; D-C22, D-C25, D-C26, D-C27, D-C06, D-C07 |
| R-A11-020..021 scenarios | S06; D-C25 |
| R-A11-030..032 themes | S22, S24, S27, S29, S30; D-C11, D-C21 |
| R-A11-040..047 gold & silver | S08, S28, S30; D-C21, D-C06, D-C07 |
| R-A11-048 primary-source verification of conflicts | S06, S08; D-C22, D-R27 |
| R-A11-049..050 physical gold exit, numeric invalidation signs | S28; D-R39, D-DEF-35 |
| R-A11-004, R-A11-006, R-A11-041, R-A11-044 tolerance, staleness, gold engine, vault threshold | S28; D-R39, D-DEF-32, D-DEF-33, D-DEF-34 |
| §8.1 observation tables | S03, S04, S06, S08, S09, S10, S12, S21, S22, S24, S26, S27, S28, S29, S30 |
| TH-01..TH-15 | as listed in §8.2 |
