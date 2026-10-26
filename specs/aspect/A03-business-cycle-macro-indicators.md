---
id: A03
title: Business Cycle & Macro Indicators
context: CTX-B
layers: [CORE, MACRO]
status: draft
sources: [S01, S04, S06, S09, S17, S18, S20, S29, S30]
decisions: [D-C04, D-C22, D-C25, D-C28, D-R42, D-DEF-07, D-DEF-08, D-DEF-09, D-DEF-10, D-DEF-11, D-DEF-12]
depends_on: [A01, A02, A10, A11]
---
# A03 — Business Cycle & Macro Indicators

## 1. Purpose & scope
Specifies how the app assesses the business-cycle phase from an indicator dashboard, scores it, applies the Sahm rule, maps phases to historically favoured sectors, and observes the growth/value style regime. The cycle is a **bias only** (D-C25): it annotates and orders; it never triggers, gates, sizes or exits.

Excluded: scoreboard status and eligibility (A02), yield-curve and credit-spread computation (A10), central-bank, liquidity and thematic theses and the Observation data model (A11), entry/exit (A06/A07), risk limits (A08/A09). Macro sequences such as the "five waves of capital flow" and "jet fuel leads airlines" (S06) are A11 theses, not cycle inputs.

## 2. Concepts
- [[business-cycle]], [[early-cycle]], [[mid-cycle]], [[late-cycle]], [[recession]], [[transition-phase]] — the four phases plus the mixed label.
- [[leading-indicator]], [[coincident-indicator]], [[lagging-indicator]] — dashboard categories.
- [[pmi]], [[sahm-rule]], [[inflation]], [[yield-curve]], [[credit-spread]], [[ten-year-yield]], [[policy-rate]] — key inputs (curve/spreads from A10, policy rate from A11).
- [[cycle-phase-score]] — +1/0/−1 sum.
- [[phase-bias]], [[sector-leadership-map]] — how a phase is used (tilt only).
- [[cyclical-sector]], [[defensive-sector]], [[growth-sector]] — sector groups for market confirmation.
- [[style-regime]], [[growth-style]], [[value-style]], [[valuation-spread]], [[market-breadth]] — observed style leadership and supporting signals.
- [[value-is-dead-thesis]] — recorded thesis, not a rule.
- [[rate-cycle]] — policy backdrop of each phase.
- [[shiller-pe]] — valuation context, not a phase criterion.
- [[macro-observation]], [[observation-conflict]] — storage of readings (model owned by A11).

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Observation | metric, value, unit, asOf, measureType, source | | per D-C22 | owned by A11; readings of every indicator |
| IndicatorDefinition (new) | id, name, category {leading, coincident, lagging}, unit, source_series, owner_aspect, phase_criteria_refs | | | dashboard row |
| IndicatorReading (new) | indicator, observation(s), direction {up, down, flat, unknown}, rate_of_change, score {+1, 0, −1}, evidence_text | | score 0 when direction unknown | |
| CyclePhase | id {early, mid, late, recession} | enum | | + `transition` as label only |
| CycleAssessment (new) | market, as_of, phase {early, mid, late, recession, transition}, confidence {high, medium, low}, total_score, criteria_met per phase, key_evidence (4–7), market_confirmation {cyc_def_spread, style_regime}, industry_bias {favoured[], avoid[]}, style_bias {growth, value, neutral}, risks[], next_review_trigger, written_while_closed (bool), disclaimers | | R-A03-019 | |
| SectorLeadershipMap (new) | phase → favoured sectors[], avoid sectors[] | | GICS sector names | §7 table |
| StyleRegime | market, as_of, growth_proxy, value_proxy, rs_comp, rs_comp_sma50, regime {growth_led, value_led, neutral}, shift_confirmed (bool), confirmations[] | | R-A03-027..029 | |
| Thesis | id, statement, source | | | owned by A11; e.g. value-is-dead |

CycleAssessment lifecycle: `draft → published` (only if R-A03-009 complete) `→ superseded` by the next monthly or release-triggered assessment.

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `cycle.review_cadence` | monthly (monthly review) + after major data releases | — | — | S18, S20; D-C04 |
| `cycle.majority_threshold` | > 50% of a phase's criteria | fixed | share | S18 ("if majority of") |
| `cycle.required_indicators` | yield curve, PMI, LEI, employment, inflation, credit spreads | superset allowed | — | S18 checklist |
| `cycle.key_evidence_count` | 4–7 | 4..7 | indicators | S18 |
| `cycle.pmi_threshold` | 50 | fixed | index points | S18 |
| `cycle.sahm_avg_months` | 3 | fixed | months | S18 |
| `cycle.sahm_low_lookback_months` | 12 | fixed | months | S18 |
| `cycle.sahm_threshold_pp` | 0.50 | fixed | percentage points | S18 |
| `cycle.sahm_low_basis` | 3m_average (standard Sahm definition) | {3m_average} | — | S18; D-DEF-07 |
| `cycle.score_bands` | on score_ratio = total_score / scored indicators: strongly positive ≥ +0.5; mildly positive +0.2 to < +0.5; near zero > −0.2 and < +0.2; mildly negative > −0.5 and ≤ −0.2; strongly negative ≤ −0.5 | ordered cut-offs in [−1, +1] | ratio | S18; D-DEF-08 |
| `cycle.direction_window` | monthly series: 3-month average vs 3 months earlier; weekly: 4-week average vs 13 weeks earlier; daily: 20-session average vs 63 sessions earlier | — | — | D-DEF-09 |
| `cycle.direction_flat_sigma` | 0.25 | > 0 | σ of window changes | D-DEF-09 |
| `cycle.sharp_change_sigma` | 1.5 | > flat sigma | σ of window changes ("sharp", "rapid") | D-DEF-09 |
| `cycle.sigma_lookback_months` | 60 | ≥ 36 | months of history for σ | D-DEF-09 |
| `cycle.sustained_readings` | 3 | ≥ 2 | consecutive monthly readings (13 weeks, 63 sessions) | D-DEF-09 |
| `cycle.pmi_comfortable_min` | 52 | > 50 | index points, for 3 consecutive months | D-DEF-09 |
| `cycle.pmi_well_below_max` | 45 | < 50 | index points | D-DEF-09 |
| `cycle.style_proxy_pair` | US: Russell 1000 Growth vs Russell 1000 Value (e.g. IWF/IWD); other markets: MSCI <market> Growth vs MSCI <market> Value; global: MSCI ACWI Growth vs Value | instruments or indices of the market | — | D-C25; D-DEF-10 |
| `cycle.style_confirmations_required` | rates + style RS + ≥ 1 other macro signal | ≥ 3 signals | — | S20 |
| `cycle.sector_groups` | cyclical: Financials, Consumer Discretionary, Industrials, Materials, Energy, Real Estate; defensive: Consumer Staples, Utilities, Health Care; growth: Information Technology, Communication Services | GICS sectors | — | glossary `cyclical-sector`, `defensive-sector`; S01, S20, S29; D-DEF-12 |

## 5. Rules

### 5.1 Role of the cycle (bias only)
- **R-A03-001** (hard, CORE) — A CycleAssessment MUST NOT generate buy or sell orders, change scoreboard status, rank or eligibility, position size, stops or exits. _Sources: S18 ("Do not generate buy/sell recommendations solely from phase labels"), S20. Decision: D-C25_
- **R-A03-002** (hard, CORE) — Phase bias MAY annotate and order industries inside the A02 eligible set (green and top RS group) as favoured/avoid; it MUST NOT add an industry that A02 does not mark eligible. _Sources: S20 ("Still require price confirmation"), S17 ("use the cycle as a bias and then apply a momentum ranking within"). Decision: D-C25_
- **R-A03-003** (hard, CORE) — Any portfolio change prompted by a phase view MUST still pass the predefined risk rules (A08 sizing, A07 stops, A09 concentration). _Sources: S18_
- **R-A03-004** (hard, METHOD) — A predefined exit (150-SMA trend exit, protective stop) MUST NOT be suspended because the macro story is favourable. _Sources: S20 ("Never abandon the predefined exit … just because the macro story still sounds good")_

### 5.2 Phase determination
- **R-A03-005** (hard, CORE) — Phases are Early, Mid, Late and Recession; `transition` is a label for mixed evidence, not a phase. _Sources: S18, S20_
- **R-A03-006** (hard, CORE) — A phase MUST be assigned only when more than half of that phase's criteria (§7 criteria table) hold. _Sources: S18_
- **R-A03-007** (hard, CORE) — If no phase or more than one phase meets the majority, the assessment MUST be labelled `transition` with confidence `low`. _Sources: S18 ("If data are mixed or conflicting, explicitly say 'Transition / Mixed' and lower confidence")_
- **R-A03-008** (hard, CORE) — Each indicator MUST be judged on direction and rate of change, not level; a reading without a usable prior value has direction `unknown`, scores 0 and is flagged. _Sources: S18 ("Focus on the direction and rate of change of indicators, not absolute levels")_
- **R-A03-009** (hard, CORE) — No single indicator is sufficient: an assessment MUST NOT be published unless every indicator in `cycle.required_indicators` has a current reading. _Sources: S18 ("Require a cluster of signals"; decision checklist)_
- **R-A03-010** (hard, CORE) — Each indicator reading MUST be scored +1 (clear expansionary / early-mid), 0 (neutral or mixed) or −1 (clear contractionary / late-recession); total_score = sum. _Sources: S18_
- **R-A03-011** (soft, CORE) — total_score SHOULD be checked against the assigned phase using score_ratio = total_score / number of scored indicators and `cycle.score_bands`: strongly positive (≥ +0.5) → early/mid; mildly positive (+0.2 to < +0.5) → mid/early late; near zero (> −0.2 and < +0.2) → late/transition; mildly negative (> −0.5 and ≤ −0.2) → late, recession risk rising; strongly negative (≤ −0.5) → recession risk. _Sources: S18. Decision: D-DEF-08_
- **R-A03-012** (hard, CORE) — Sahm rule (standard definition): `sahm = avg_3m(UR) − low_12m`, where low_12m is the minimum of the 3-month average over the prior 12 months; triggered iff `sahm ≥ cycle.sahm_threshold_pp` (0.50 pp). A triggered Sahm rule MUST count as the Recession criterion "rising unemployment" and score −1. _Sources: S18. Decision: D-DEF-07_
- **R-A03-013** (hard, CORE) — PMI: a cross above 50 from below is an Early criterion (+1); "comfortably > 50" (≥ `cycle.pmi_comfortable_min` 52 for 3 consecutive months) is a Mid criterion (+1); sustained < 50 (`cycle.sustained_readings` consecutive readings) scores −1; "well below 50" (≤ `cycle.pmi_well_below_max` 45) is a Recession criterion. _Sources: S18. Decision: D-DEF-09_
- **R-A03-014** (hard, CORE) — Yield curve (2s10s or 3m10y, computed by A10): re-steepening after inversion is an Early criterion (+1); flat or inverted is a Late criterion; sustained inversion scores −1. _Sources: S18, S20_
- **R-A03-015** (hard, CORE) — HY credit spreads (A10): narrowing scores +1 (risk-on/early); rapid widening scores −1 and is the Recession criterion "credit spreads widening sharply". _Sources: S18_
- **R-A03-016** (hard, CORE) — Inflation (CPI / core PCE) elevated or re-accelerating is a Late criterion; rising profit margins peaking and inventories rising while sales slow are Late criteria. _Sources: S18, S20_

### 5.3 Market confirmation and confidence
- **R-A03-017** (hard, CORE) — Every assessment MUST include market confirmation: (a) cyclicals-vs-defensives spread from sector proxies, (b) the style regime (R-A03-027). _Sources: S18 ("Always cross-check economic signals with market relative strength")_
- **R-A03-018** (soft, CORE) — If market confirmation disagrees with the economic reading (e.g. defensives leading while the reading is Early/Mid, or cyclicals leading while Late/Recession), confidence SHOULD drop one level and the disagreement MUST be listed under risks. _Sources: S18 ("Adjust final judgment with market relative-strength confirmation"), S29_
- **R-A03-019** (soft, CORE) — Base confidence SHOULD be `high` when a single phase has a majority, the score check (R-A03-011) is consistent and market confirmation agrees; each failed check lowers it one level (minimum `low`); a `transition` assessment is always `low`. _Operationalisation of S18. Decision: D-DEF-11_
- **R-A03-020** (soft, METHOD) — A02 `defensive_leadership` and `rotation_mirror` Observations SHOULD be used as evidence for (a). _Sources: S29, S30_

### 5.4 Output, cadence, honesty
- **R-A03-021** (hard, CORE) — A published assessment MUST contain: phase, confidence, 4–7 key indicators with direction, market confirmation, industry bias (favoured/avoid), style bias (growth/value/neutral), risks to the assessment, next review trigger. _Sources: S18 (required output format)_
- **R-A03-022** (hard, CORE) — The assessment MUST NOT express certainty, MUST show the evidence used, MUST note that NBER dates recessions only in hindsight, and MUST state that past cycle patterns are historical tendencies. _Sources: S18 (hard rules 1, 2, 3, 7), S20_
- **R-A03-023** (hard, CORE) — Assessments are updated at the monthly review and after major data releases, and recorded while markets are closed. _Sources: S18, S20 ("Make switching decisions when markets are closed"). Decision: D-C04, D-C28_
- **R-A03-024** (hard, MACRO) — Indicator values MUST be stored as Observations {metric, value, unit, asOf, measureType, source}; conflicting Observations for the same metric, date and measureType raise an observation-conflict flag and are not reconciled. _Decision: D-C22_

### 5.5 Sector leadership by phase
- **R-A03-025** (hard, CORE) — The SectorLeadershipMap (§7) MUST be applied to GICS sectors, which every market uses (A01 R-A01-007). _Sources: S17, S20. Decision: D-R42_
- **R-A03-026** (soft, CORE) — The UI SHOULD state that leadership is relative: in a deep bear market almost everything falls and "leaders" fall less or recover first. _Sources: S20_

### 5.6 Style regime (growth vs value)
- **R-A03-027** (hard, CORE) — The style regime MUST be observed, not inferred: compute RS_comp of the market's growth proxy vs its value proxy (`cycle.style_proxy_pair`) with the A02 algorithm; `growth_led` if it would be green, `value_led` if red, else `neutral`. _Decision: D-C25_
- **R-A03-028** (hard, CORE) — The style bias expected from macro conditions (§7 style table) MUST be shown separately from the observed regime and MUST NOT be labelled actionable unless the observed regime agrees. _Sources: S20. Decision: D-C25_
- **R-A03-029** (hard, CORE) — A style shift MUST be marked `confirmed` only if the observed regime changed AND the rates direction is consistent AND at least one further signal (inflation, yield curve, growth, valuation spread or breadth) is consistent; one data point never confirms. _Sources: S20 ("Do not switch styles on a single data point")_
- **R-A03-030** (soft, CORE) — Narrow breadth SHOULD be shown as a risk to growth leadership; broadening into cyclicals/value as confirmation of a rotation. _Sources: S20_
- **R-A03-031** (hard, MACRO) — "Value is dead" MUST be stored as a Thesis (A11) and MUST NOT act as a rule or filter. _Sources: S30. Decision: D-C25_

### 5.7 Valuation context
- **R-A03-032** (soft, CORE) — Market valuation versus its long-term average P/E (Shiller, ~16.22) MAY be shown as context; it is not a phase criterion. _Sources: S04_

### 5.8 Round-3 additions (2026-10-26)
- **R-A03-033** (hard, CORE) — An indicator's direction MUST be computed per `cycle.direction_window`: the change of the series average over the window versus the same average one window earlier; `flat` if \|change\| < `cycle.direction_flat_sigma` × σ, where σ is the standard deviation of that indicator's window changes over the prior `cycle.sigma_lookback_months`; "sharp"/"rapid" means \|change\| ≥ `cycle.sharp_change_sigma` × σ; "sustained" means the condition held on `cycle.sustained_readings` consecutive monthly readings (13 weeks for weekly, 63 sessions for daily series). _Sources: S18 ("direction and rate of change"). Decision: D-DEF-09, D-X (volatility-scaled thresholds)_

## 6. Processes
**PR-A03-01 Monthly cycle assessment** — trigger: monthly review (A12) or a major release (GDP, payrolls, CPI, PMI). Inputs: latest Observations; A10 curve/spreads; A02 sector proxies and style proxies. Steps (S18): (1) refresh `cycle.required_indicators` (R-A03-009); (2) determine direction per indicator (R-A03-008); (3) score +1/0/−1 and sum (R-A03-010); (4) count criteria met per phase, apply majority (R-A03-006/007); (5) compute market confirmation (R-A03-017); (6) set confidence (R-A03-018/019); (7) derive industry bias from the leadership map and style bias from the style table; (8) write risks and next review trigger; (9) publish with disclaimers (R-A03-022). Output: CycleAssessment. Cadence: monthly + release-driven.

**PR-A03-02 Pre-action checklist** (before acting on a phase view; S18) — readings updated? direction consistent across indicators? market RS agrees? confidence and risks noted? used as bias only? risk rules obeyed? written while markets closed? Any "no" → no phase-driven change.

**PR-A03-03 Switching checklist** (industry or style; S20) — (1) phase and evidence; (2) RS already confirms new leadership (A02)?; (3) old industry breaking down structurally (close below 150-SMA, A07)?; (4) rates, inflation and policy consistent?; (5) risk if wrong → size accordingly (A08); (6) new allocation and exits written while calm.

## 7. Calculations
```
indicator_score_i ∈ {-1, 0, +1}                 # 0 when direction unknown
total_score       = Σ indicator_score_i
score_ratio       = total_score / n_scored          # bands ±0.2 / ±0.5 (D-DEF-08)
change_w          = mean(x over last window) - mean(x over previous window)   # D-DEF-09
direction         = flat if |change_w| < 0.25σ_w; up/down by sign otherwise; sharp if |change_w| >= 1.5σ_w   # σ_w over 60 months
criteria_share_p  = criteria_met_p / criteria_total_p      # phase assigned iff > 0.5 for exactly one p

avg3(m)           = mean(UR[m-2], UR[m-1], UR[m])
low12(m)          = min(avg3[m-12 .. m-1])          # standard Sahm basis 3m_average (D-DEF-07)
sahm(m)           = avg3(m) - low12(m)              # triggered iff >= 0.50 pp

cyc_def_spread    = mean(RS_comp(cyclical sectors)) - mean(RS_comp(defensive sectors))   # A02 RS, local view
style_rs          = RS_comp(growth_proxy vs value_proxy)                                 # A02 algorithm
pe_ratio_to_avg   = trailing_PE / long_term_avg_PE
```

**Indicator dashboard (S18)**
| Indicator | Category | +1 when | −1 when | Data owner |
|---|---|---|---|---|
| Yield curve 2s10s / 3m10y | leading | steepening after inversion | sustained inversion | A10 |
| ISM / PMI manufacturing | leading | crossing above 50 from below; comfortably > 50 | sustained < 50 | A03 |
| Conference Board LEI | leading | turning up | sustained decline | A03 |
| Building permits / housing starts | leading | bottoming and rising | sharp decline | A03 |
| Initial jobless claims (4-wk avg) | leading | falling | rising sharply | A03 |
| HY credit spreads (OAS) | leading | narrowing | rapid widening | A10 |
| Real GDP growth | coincident | positive and stable/accelerating | negative / near zero | A03 |
| Industrial production | coincident | rising | falling | A03 |
| Payrolls + unemployment rate | coincident | steady gains, low/stable UR | job losses, rising UR | A03 |
| Real retail sales / personal income | coincident | growing | contracting | A03 |
| Capacity utilisation | coincident | rising | falling (caution) | A03 |
| Unemployment trend & Sahm rule | lagging | — | Sahm triggered | A03 |
| Inflation (CPI / core PCE) | lagging | — | rising/elevated (late-cycle marker) | A03 |
| Corporate profit margins | lagging | — | peaking | A03 |
| Inventory-to-sales ratio | lagging | low vs sales (early) | rising inventories + slowing sales | A03 |

**Phase criteria (majority rule, S18)**
| Phase | Criteria (n) |
|---|---|
| Early (6) | curve re-steepening after inversion; PMI back above 50; claims falling, employment stabilising then rising; credit easing; inventories low vs sales; growth accelerating from low base |
| Mid (6) | steady positive growth; PMI comfortably > 50; healthy job gains, low/stable UR; credit growing, policy ~neutral; profits and capex expanding; inventories and sales balanced |
| Late (7) | growth positive but decelerating; inflation elevated/re-accelerating; very tight labour market; policy restrictive; curve flat/inverted; inventories rising while sales slow; margins under pressure |
| Recession (5) | broad decline in activity; PMI well below 50; rising UR (Sahm triggered/approaching); falling IP, real sales, employment; credit spreads widening sharply |

**Sector leadership map (S20; "avoid" from S17)**
| Phase | Favoured | Avoid / underweight |
|---|---|---|
| Early | Financials, Consumer Discretionary, Industrials, Real Estate, Information Technology | Utilities, Consumer Staples |
| Mid | Information Technology (hardware, semis, software), Industrials, Consumer Discretionary, Materials | — |
| Late | Energy, Materials, Consumer Staples, Health Care (Utilities stabilising) | Consumer Discretionary, Information Technology |
| Recession | Consumer Staples, Health Care, Utilities (Telecom); high-quality bonds | Cyclicals, Energy, Financials |

**Style bias table (S20)** — Growth favoured: rates falling/low; inflation low/declining; curve steepening from low levels; steady-strong expansion; growth not extremely expensive; growth RS leading. Value favoured: rates rising; inflation rising/elevated; curve flattening/inverting then steepening from high rates; early recovery or late slowdown; large value discount vs history; value RS leading. Quick reference: early recovery/low rates → cyclicals, financials, discretionary, growth; steady expansion → technology, industrials, broad growth; rising inflation/tightening → energy, materials, value, staples; recession/risk-off → staples, health care, utilities, quality; falling rates after tightening → growth, long-duration, rate-sensitive cyclicals; extreme growth bubble → value, broader market.

## 8. Examples / fixtures
**EX-A03-01 Sahm rule, simple (R-A03-012)**
- Given low12 = 3.6%, avg3 = 4.1% → sahm = 0.50 pp → triggered (edge: equality triggers).
- Given avg3 = 4.0% → 0.40 pp → not triggered.

**EX-A03-02 Standard Sahm basis (R-A03-012, D-DEF-07)**
- Monthly UR M1..M15: 3.8, 3.7, 3.5, 3.8, 3.7, 3.7, 3.7, 3.8, 3.8, 3.9, 3.9, 4.0, 4.1, 4.2, 4.3.
- avg3: M3..M13 = 3.6667, 3.6667, 3.6667, 3.7333, 3.7000, 3.7333, 3.7667, 3.8333, 3.8667, 3.9333, 4.0000; M14 = 4.1000; M15 = 4.2000.
- M14, standard basis 3m_average: low12 = 3.6667 → sahm 0.4333 → not triggered. (The variant not chosen, low of the monthly rate 3.5, would give 0.60 → a premature trigger.)
- M15, basis 3m_average: 4.2000 − 3.6667 = 0.5333 → triggered.

**EX-A03-03 Score and transition (R-A03-007, R-A03-010)** — synthetic, from S18 method.
- Given curve +1, PMI −1, LEI −1, claims 0, HY OAS 0, GDP +1 → total_score = 0, score_ratio = 0/6 = 0.00 → band "near zero" (late or transition, D-DEF-08). Edge: total +3 of 6 → 0.50 → "strongly positive" (inclusive); total −2 of 6 → −0.33 → "mildly negative".
- Criteria met: Late 3/7, Mid 2/6, Early 1/6, Recession 1/5 → no majority → `transition`, confidence `low`.

**EX-A03-04 Majority edge (R-A03-006)**
- Late 5/7 = 71% → Late assigned (other phases below half).
- Edge: Early 3/6 = 50% exactly → not a majority; if no other phase has one → `transition`.

**EX-A03-05 Two majorities (R-A03-007)**
- Late 4/7 (57%) and Recession 3/5 (60%) → conflicting → `transition`, `low`.

**EX-A03-06 Incomplete dashboard (R-A03-009)**
- Given all required readings except PMI (release delayed). Then the assessment stays `draft`, shows "incomplete: PMI", and the previous published assessment remains current.

**EX-A03-07 Level-only reading (R-A03-008)** — source value S09 (July 2026).
- Given HY OAS = 246 bp ("historically thin") with no prior reading stored → direction `unknown` → score 0, flagged; level alone is not evidence.
- Given additionally a prior reading of 300 bp one month earlier (synthetic) → narrowing → +1.

**EX-A03-08 Market confirmation disagrees (R-A03-018, R-A03-020)** — uses S30 relative returns, month to 24 Oct 2026.
- Given economic criteria: Mid 4/6 (single majority), score consistent → base `high`.
- And A02 Observation `defensive_leadership`: staples +8%, utilities +8% vs technology −5% (relative to S&P 500) → defensives leading.
- Then confidence `medium`; risks include "market RS shows defensive leadership, inconsistent with Mid".

**EX-A03-09 Bias only (R-A03-001, R-A03-002)**
- Given phase Late; A02 eligible set = {Semiconductors (green, top), Oil & Gas E&P (green, top)}; Utilities neutral.
- Then Oil & Gas E&P is annotated "favoured" and listed first; Semiconductors stays eligible, annotated "phase headwind" (Information Technology is on the Late avoid list); Utilities is NOT added although favoured. No order, size or stop changes.

**EX-A03-10 Style regime and confirmation (R-A03-027..029)**
- Given growth-vs-value RS_comp = −2.5 and its 50-session average −1.0 → would be red → `value_led`.
- Given 10-year yield rising (5.00% Oct 2026, S29, vs 4.60% a quarter earlier — synthetic prior) and inflation elevated (CPI 4.2% y/y, BLS May 2026, S09) → rates + style RS + inflation = 3 signals → shift `confirmed`.
- Edge: style RS turns value_led but rates are falling → `unconfirmed`; style bias table not labelled actionable.

**EX-A03-11 Valuation context (R-A03-032)** — source S04, 2026-06-05.
- Given S&P 500 trailing P/E 31.83 and long-term average 16.22 → ratio 1.96 ("nearly 2x"). Shown as context; no effect on phase or eligibility.

**EX-A03-12 Output format (R-A03-021, R-A03-022)** — expected shape:
```
Current Phase Assessment: Transition
Confidence: Low
Key Evidence: yield curve steepening after inversion (+1); PMI below 50 and falling (-1);
  LEI declining (-1); real GDP positive, stable (+1); claims flat (0); HY OAS flat (0)
Market Confirmation: cyc_def_spread -4.0 pp (defensives leading); style regime value_led
Implications: Industry bias favoured [Energy, Materials, Consumer Staples, Health Care]
  avoid [Consumer Discretionary, Information Technology]; Style bias Value (unconfirmed)
Risks: mixed indicators; NBER dates recessions only in hindsight
Next Review Trigger: next PMI release
Note: past cycle patterns are historical tendencies only.
```

**EX-A03-13 Direction test (R-A03-013, R-A03-033; D-DEF-09)** — synthetic.
- Given monthly PMI M1..M6 = 48.0, 48.5, 49.0, 50.2, 51.0, 52.0 and σ of 3-month-average changes over 60 months = 1.5.
- Then change = mean(50.2, 51.0, 52.0) − mean(48.0, 48.5, 49.0) = 51.067 − 48.500 = +2.567 → 2.567 / 1.5 = 1.71 σ ≥ 1.5 → direction up, "sharp"; PMI crossed above 50 from below → Early criterion (+1).
- "Comfortably > 50" is not yet met (needs ≥ 52 for 3 consecutive months: 50.2, 51.0, 52.0 → no).
- Edge: change +0.30 → 0.20 σ < 0.25 σ → `flat`.

## 9. Variants & open points
- Variant (not chosen): cycle as an allocation driver (S17 Strategy E, S20 overlay rule B) — D-C25 restricts it to bias; S20 "combined rule" is implemented as bias plus A02 price confirmation.
- Variant: S01 matches sector choice to investor risk tolerance (conservative → defensives, aggressive → growth); belongs to profiles (A13), not to phase assessment.
- Variant: S20 overlay inputs (credit growth / lending standards, central-bank stance) are covered by credit spreads (A10) and policy-rate Observations (A11).
- Variant (not chosen): Sahm low on the monthly rate (S18 wording "12-mo low") — standard 3-month-average basis (D-DEF-07).
- Closed by D-DEF-07 — OPEN-A03-1 (standard Sahm basis; pending user review).
- Closed by D-DEF-08 — OPEN-A03-2 (score bands on score_ratio; pending user review).
- Closed by D-DEF-09 — OPEN-A03-3 (direction windows and σ thresholds; pending user review).
- Closed by D-DEF-10 — OPEN-A03-4 (style proxy pairs; pending user review).
- Closed by D-DEF-11 — OPEN-A03-5 (confidence operationalisation confirmed; pending user review).
- Closed by D-DEF-12 — OPEN-A03-6 (Communication Services growth, Real Estate cyclical; pending user review).

### Glossary additions (merged into glossary v0.2.0)
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| cyclical-defensive-spread | Cyclical–Defensive Spread | CORE | Mean RS composite of cyclical-sector proxies minus that of defensive-sector proxies; positive = cyclicals leading. Market cross-check of the cycle phase. | S18, S20 |
| cycle-assessment-confidence | Cycle Assessment Confidence | CORE | High/medium/low rating attached to a phase assessment; lowered by mixed evidence or disagreeing market confirmation. | S18 |

## 10. Traceability
| Rule/Concept | Sources / Decisions |
|---|---|
| R-A03-001..004 bias only | S17, S18, S20; D-C25 |
| R-A03-005..016 phase determination, Sahm, PMI, curve, spreads | S18, S20 |
| R-A03-017..020 market confirmation, confidence | S18, S29, S30 |
| R-A03-021..024 output, cadence, observations | S18, S20; D-C04, D-C22, D-C28 |
| R-A03-025..026 sector leadership | S17, S20 |
| R-A03-027..031 style regime, value thesis | S20, S30; D-C25 |
| R-A03-032 valuation context | S04 |
| R-A03-033 direction windows and σ thresholds | S18; D-DEF-09 |
| EX-A03-07, -08, -10, -11 | S09, S30, S29/S09, S04 |
