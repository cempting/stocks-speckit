---
id: A08
title: Risk & Position Sizing
context: CTX-D
layers: [CORE, METHOD]
status: draft
sources: [S05, S07, S12, S13, S14, S15, S16, S17, S19, S20, S21, S22, S23, S24, S25, S30]
decisions: [D-X, D-C03, D-C04, D-C08, D-C09, D-C10, D-C11, D-C12, D-C24, D-C26, D-OPEN-3, D-S14, D-R05, D-R09, D-R10, D-R11, D-R12, D-R14, D-R36, D-R40, D-DEF-22, D-DEF-23, D-DEF-24, D-DEF-25, D-DEF-36]
depends_on: [A01, A02, A06, A07, A09, A13]
---
# A08 — Risk & Position Sizing

## 1. Purpose & scope
Defines how much is bought: the risk budget per position, the share formula, the [[volatility-class]] that links
volatility to both stop distance (validated in A07) and exposure, [[inverse-volatility-weighting]], the
[[overnight-gap-test]] weight cap, optional [[fractional-kelly]] sizing, loss-recovery arithmetic, outcome classification
([[three-outcomes]]) and the hard prohibitions (no [[margin-trading]], no leverage, no [[averaging-down]]).

Excluded (referenced only): stop placement and exits (A07), concentration limits and the investable-equity basis
(A09 `portfolio.*`, `cash.*`), entry tranches (A06), fixed-allocation sizing of the beginner profile (A13), macro
scenario allocations (A11).

## 2. Concepts
- [[risk-per-position]] — money lost if the protective stop is hit, % of [[portfolio-equity]]; never the same as [[position-size]].
- [[risk-based-position-sizing]] — shares = equity x risk% / (entry - stop), then capped.
- [[stop-distance]] — input from the A07 exit plan; drives size inversely.
- [[volatility]] / [[atr-percent]] / [[volatility-class]] — ATR%(14), 63-session average -> class LOW/MEDIUM/HIGH/EXTREME -> stop band (A07), conservative exposure and the class-scaled detection/entry thresholds of A04/A06 (D-R05, D-R10, D-R11).
- [[total-open-risk]] — sum of risk at stop over open positions; displayed only, no cap (D-R09).
- [[inverse-volatility-weighting]] — twice the swing, about half the size.
- [[gap]] / [[overnight-gap-test]] — stops do not protect against gaps; weight is capped so an assumed gap stays survivable.
- [[single-position-impact]] — portfolio loss = weight x drop.
- [[kelly-criterion]] / [[fractional-kelly]] / [[win-rate]] / [[sharpe-ratio]] — optional advanced mode, can only lower risk.
- [[loss-recovery-asymmetry]] / [[one-to-one-zone]] — why the risk budget is small.
- [[three-outcomes]] / [[fourth-outcome]] — big win, small win, small loss; no big loss.
- [[drawdown]] — position and portfolio decline from peak.
- [[stomach-test]] — subjective oversize check; answer is a smaller position.
- [[position-tier]] / [[asymmetric-bet]] — speculative sizing tiers (S22) as optional tags.
- [[margin-trading]] / [[leveraged-etf]] — forbidden.
- [[averaging-down]] — forbidden.
- [[fixed-allocation-sizing]] — S14 profile sizing, A13; risk must still be shown.

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| RiskBudget | portfolio_id | ref `Portfolio` | | |
| RiskBudget | equity | currency | = A09 portfolio equity (excl. `EmergencyBuffer`) | basis of all % |
| RiskBudget | risk_pct | % | `sizing.risk_pct` within 0.5-1.0 | per position |
| RiskBudget | mode | enum {RISK_BASED, FRACTIONAL_KELLY} | default RISK_BASED | |
| RiskBudget | kelly_k | {0.25, 0.5} | only in FRACTIONAL_KELLY | |
| VolatilityClass | code | enum {LOW, MEDIUM, HIGH, EXTREME} | | METHOD; D-R11 |
| VolatilityClass | atr_pct_range | % per day (ATR%(14), 63-session avg) | LOW < 1; MEDIUM 1-<2; HIGH 2-<4; EXTREME >= 4 | D-R10, D-R11 |
| VolatilityClass | stop_band_pct | [min, max] % | 5-8 / 10-15 / 20-25 / 25-35 | D-C08, D-R11 |
| InstrumentVolatility (new) | instrument_id, as_of, atr14, atr_pct_avg63, atr_period, avg_sessions, class | | measured at the weekly review | for stock and industry proxy (D-R10) |
| PortfolioRiskSummary (new) | portfolio_id, as_of, total_open_risk_amount, total_open_risk_pct, per_position[] {position_id, risk_at_stop_amount, risk_at_stop_pct} | currency, % | display only, no cap | D-R09 |
| OversizeFlag (new) | position_id, raised_at, weight_pct, gap_cap_pct, tolerance_cap_pct, trim_required, agenda_item_id, skipped_reason | | trim never automatic | D-R12 |
| SizingDecision (new) | position_id, entry, stop, stop_distance_pct, shares_risk, cap_gap, cap_kelly, shares_final, binding_cap, suggested_cap_position, suggested_cap_industry, shares_suggested, concentration_warning, risk_amount, risk_pct_actual, weight_pct | | shares_final = min(risk, gap, kelly); A09 headrooms advisory (D-R14); risk_pct_actual <= risk_pct | audit of each sizing |
| Position | planned_risk_amount, outcome | currency, enum {BIG_WIN, SMALL_WIN, SMALL_LOSS, LOSS_EXCEEDED_PLAN, FOURTH_OUTCOME} | outcome set at close | owned by A09; attributes added here |
| Position | tier | enum {T1, T2, T3} or null | optional | S22 |

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `sizing.risk_pct` | 1.0 | 0.5-1.0 | % of equity | D-C09; S13, S15, S23, S30, S07, S16, S19, S20 |
| `sizing.extreme_single_stock_risk_pct` | 0.5 | <= 0.5 | % of equity (single stock, effective class EXTREME) | D-R11 |
| `sizing.max_risk_pct` | 1.0 | hard cap | % of equity | D-C09 |
| `sizing.initial_live_risk_pct` | 0.5 | 0.5-1.0 | % | S07 ("smallest position size"); lower bound of D-C09 range |
| `sizing.initial_live_trades_count` | 3 | >= 1 | live trades | S07 weeks 9-10 (1 + 1-2 trades); D-DEF-25 |
| `sizing.share_rounding` | floor (whole shares; to `Broker.fractional_increment` when fractional shares are allowed) | floor | — | glossary formula; D-R40 |
| `sizing.allow_fractional_shares` | = A01 `Broker.supports_fractional` | {true, false} | — | D-R40 |
| `sizing.mode` | RISK_BASED | {RISK_BASED, FRACTIONAL_KELLY} | — | D-C09 (Kelly optional advanced) |
| `sizing.kelly_k` | — (user selects) | {0.25, 0.5} (maximum 0.5) | — | S15; D-C09, D-DEF-22 |
| `sizing.kelly_min_closed_trades` | 30 | >= 30 | closed live trades | D-DEF-22 |
| `risk.gap_assumed_pct.stock` | 30 | >= 30 (stricter only) | % | D-OPEN-3; S25 |
| `risk.gap_assumed_pct.fund` | 15 | >= 15 (stricter only) | % (funds, baskets) | D-OPEN-3 |
| `risk.gap_max_loss_pct` | 2 | > 0 and <= 2 (stricter only) | % of equity | D-OPEN-3 |
| `risk.vol_metric` | ATR%(14) | ATR%(14) | — | D-R10 |
| `risk.vol_atr_period` | 14 | 14 | sessions | D-R10 |
| `risk.vol_avg_sessions` | 63 | 63 | sessions (average of daily ATR%) | D-R10 |
| `risk.vol_class_atr_pct_bounds` | LOW < 1; MEDIUM 1 <= x < 2; HIGH 2 <= x < 4; EXTREME >= 4 | — | % / day | D-R11 (2-3 band = HIGH confirmed); S07, S23 |
| `risk.vol_class_stop_band_pct.low` | 5-8 | — | % below entry | D-C08; S07 |
| `risk.vol_class_stop_band_pct.medium` | 10-15 | — | % | D-C08; S07 |
| `risk.vol_class_stop_band_pct.high` | 20-25 | — | % | D-C08; S07, S23 (miners ~25%) |
| `risk.vol_class_stop_band_pct.extreme` | 25-35 | — | % | D-R11; S23 ("dragsters") |
| `risk.vol_class_combination` | max(instrument, industry proxy) | max | — | D-X ("industry+stock", "more conservative"); used for stops, sizing and exits |
| `risk.vol_class_threshold_basis` | stock: own class; fund/basket: industry-proxy class | fixed | — | D-R05; used for A04/A06 detection and entry thresholds |
| `risk.gap_breach_tolerance_multiple` | 1.5 | >= 1.0 | x gap cap (growth from gains) | D-R12 |
| `risk.stress_drop_pct` | 20 | > 0 | % position drop | S05, S13, S23 |
| `risk.stress_max_impact_pct` | 2 | > 0 | % of equity | S05 |
| `risk.fourth_outcome_review_drawdown_pct` | 25 | 15–25 (stricter only) | % drawdown from entry (flag/class when >= value) | S23, S25; sole loss-review threshold (A07, A12); D-DEF-36 |
| `risk.one_to_one_zone_max_loss_pct` | 10 | 5-10 | % | S30, S23 |
| `risk.big_win_threshold` | 2 | >= 1 | R (realised gain / planned risk) | D-DEF-23 |
| `risk.tier_stress_drop_pct.t2` / `.t3` | 50 / 100 | — | % | S22 |
| `risk.tier_stress_max_impact_pct` | 2 | > 0 and <= 2 | % of equity (T2 weight <= 4%, T3 weight <= 2%) | D-DEF-24 (= `risk.gap_max_loss_pct`) |
| `risk.total_open_risk_cap` | none (display only) | none | — | D-R09 |
| `risk.leverage_allowed` | false | false | — | S13, S12 |

Referenced, owned elsewhere: A01 `Broker.supports_fractional` / `fractional_increment` (D-R40); A09 `portfolio.max_position_pct` (10, range 3-10) per company, measured look-through on `portfolio.position_cap_basis` (diversified sector/industry funds are not positions for this cap, D-R36) and `portfolio.max_industry_pct`
(25, range 15-40) per D-C11 (a buy that would create a breach is a warning only, D-R14); A09 `cash.emergency_buffer_months`; A07 stop level and `exit.*`.

## 5. Rules

### 5.1 Risk budget and share formula
- **R-A08-001** (hard, METHOD) — Risk per position (shares x (entry - stop)) MUST NOT exceed `sizing.risk_pct` of portfolio equity, and `sizing.risk_pct` MUST lie within 0.5-1.0%. _Sources: S13, S23, S15, S07, S30, S20. Decision: D-C09_
- **R-A08-002** (hard, CORE) — Risk and position size MUST be stored and displayed as separate quantities; no screen may label a position weight as "risk". _Sources: S13 ("not the same as putting one percent in"). Decision: D-S14_
- **R-A08-003** (hard, METHOD) — Shares MUST be computed as floor(equity x risk_pct / (entry - stop)) with the stop taken from the validated A07 `ExitPlan` (floored to whole shares, or to the broker's fractional increment per R-A08-035); sizing without a stop MUST be rejected. _Sources: S15, S05, S30. Decision: D-C09, D-R40_
- **R-A08-004** (hard, CORE) — Equity for all percentages is the A09 portfolio equity, excluding the emergency buffer. _Sources: S24, S29. Decision: D-C24_
- **R-A08-005** (hard, METHOD) — The final share count is the minimum of: the risk-based shares, the overnight-gap cap, and the Kelly cap when enabled; the binding cap MUST be recorded. The remaining A09 company headroom under `portfolio.max_position_pct` (basis `portfolio.position_cap_basis`, company look-through; not computed for a diversified sector/industry fund, D-R36) and the remaining A09 industry/sector headroom (look-through) MUST be computed and shown as `shares_suggested` with a concentration warning when the final count would create a breach; they do not cap the count (D-R14). If the bucket is already breached, sizing returns 0 (buy blocked, A09 R-A09-010/011). _Decision: D-C09, D-C10, D-C11, D-OPEN-3, D-R14_
- **R-A08-006** (hard, METHOD) — If the final share count is 0, no entry order may be created. _Derived from R-A08-005_
- **R-A08-007** (soft, METHOD) — The first `sizing.initial_live_trades_count` (3) live trades of a new user SHOULD use `sizing.initial_live_risk_pct` (A06 R-A06-033 and A12 R-A12-042 reference this rule). _Sources: S07_
- **R-A08-008** (hard, METHOD) — An uncomfortable stop distance MUST be answered with a smaller position, never a tighter stop (A07 R-A07-011/012). _Sources: S23, S30. Decision: D-C08_

### 5.2 Volatility class and inverse-volatility weighting
- **R-A08-009** (hard, METHOD) — Each instrument and its industry proxy MUST have a volatility measured as [[atr-percent]]: ATR(14) / close x 100 per session, averaged over the last `risk.vol_avg_sessions` (63) sessions, and a resulting class with these boundaries: LOW < 1%/day; MEDIUM 1 <= x < 2; HIGH 2 <= x < 4; EXTREME >= 4. The 2-3%/day band (not covered by S07) is HIGH. _Sources: S07, S23. Decision: D-C08, D-R10, D-R11_
- **R-A08-010** (hard, METHOD) — The effective class of a position is the higher of the instrument class and the industry-proxy class. _Decision: D-X ("volatility of industry+stock", "more conservative exposure")_
- **R-A08-011** (hard, METHOD) — Each class carries the stop band of D-C08 (LOW 5-8%, MEDIUM 10-15%, HIGH 20-25%) and D-R11 (EXTREME 25-35%) used by A07 for stop validation. _Sources: S07, S23. Decision: D-C08, D-R11_
- **R-A08-012** (soft, METHOD) — A higher volatility MUST NOT lead to a larger risk amount; because stop distance scales with the class band, risk-based sizing gives a smaller weight to more volatile instruments. _Sources: S30, S23. Decision: D-X_
- **R-A08-013** (soft, CORE) — When weights are set without per-position stops (e.g. members of a custom equal-weight basket or splitting one allocation across several funds, A09/A05), weights SHOULD be inverse to volatility: w_i = (1/vol_i) / sum(1/vol_j). _Sources: S30, S16. Decision: D-C09_
- **R-A08-014** (soft, METHOD) — Volatility measurements and classes are reassessed at the weekly review; a class change of an open position is reported to A07 but never lowers the stop. _Decision: D-C04, D-C12, D-R10_

### 5.3 Gap and stress caps
- **R-A08-015** (hard, METHOD) — [[overnight-gap-test]]: weight x `risk.gap_assumed_pct` (stock 30%, fund/basket 15%) MUST NOT exceed `risk.gap_max_loss_pct` (2%) of equity, i.e. weight <= 6.67% for a single stock and <= 13.33% for a fund (then the A09 position cap applies). _Sources: S25, S13. Decision: D-OPEN-3, D-C10_
- **R-A08-016** (hard, METHOD) — The gap test MUST be applied at sizing time and re-checked for existing positions on every valuation update and at the weekly review; a breach MUST raise an `OversizeFlag` with the excess weight immediately (handling per R-A08-034; reduction is never automatic). _Sources: S25, S23. Decision: D-R12_
- **R-A08-017** (soft, METHOD) — Stress check: weight x `risk.stress_drop_pct` (20%) above `risk.stress_max_impact_pct` (2%) SHOULD trigger a reduce suggestion. _Sources: S05, S13, S23_
- **R-A08-018** (soft, METHOD) — If a position is tagged with a [[position-tier]], tier stress (weight x T2 50% / T3 100%) SHOULD be shown as % of equity; above `risk.tier_stress_max_impact_pct` (2%) it SHOULD trigger a reduce suggestion (T2 weight <= 4%, T3 weight <= 2%). _Sources: S22. Decision: D-DEF-24_
- **R-A08-019** (soft, METHOD) — [[stomach-test]]: a user report of worry about a position (e.g. checking the price at night) SHOULD create a reduce suggestion; the stop is not changed. _Sources: S23, S30, S21_

### 5.4 Fractional Kelly (optional advanced mode)
- **R-A08-020** (soft, CORE) — In FRACTIONAL_KELLY mode the effective risk fraction is min(`sizing.risk_pct`, k x f*), with f* = (b x p - q)/b from the user's own closed trades (p = win rate, b = average win / average loss); Kelly can only lower risk, never raise it above 1%. _Sources: S15, S16, S17, S19. Decision: D-C09_
- **R-A08-021** (soft, CORE) — If f* <= 0, FRACTIONAL_KELLY mode MUST block new entries and report a negative edge; with fewer than `sizing.kelly_min_closed_trades` (30) closed live trades the mode MUST fall back to RISK_BASED; k MUST NOT exceed 0.5. _Sources: S15 ("estimation error"). Decision: D-DEF-22_
- **R-A08-022** (hard, CORE) — Full Kelly (k = 1) MUST NOT be offered. _Sources: S15. Decision: D-C09_

### 5.5 Prohibitions
- **R-A08-023** (hard, METHOD) — No margin, no borrowed money, no leveraged or inverse leveraged funds; such orders MUST be rejected. _Sources: S13, S12_
- **R-A08-024** (hard, METHOD) — [[averaging-down]] is forbidden: an add order while the last close is below the average entry price MUST be rejected unless it is the pre-written pullback tranche of the A06 entry plan, and any add MUST keep total position risk <= `sizing.risk_pct` against the current stop. _Sources: S30, S13, S07_
- **R-A08-025** (hard, METHOD) — Company leverage and investor leverage are separate risks; a strong company balance sheet MUST NOT relax R-A08-023. _Sources: S12_
- **R-A08-026** (hard, METHOD) — Any profile using fixed-allocation sizing (A13, S14) MUST still compute and display risk = allocation x stop distance and MUST cap it at the effective `sizing.risk_pct` (the user's setting, itself <= `sizing.max_risk_pct`). _Sources: S14. Decision: D-S14, D-C09_

### 5.6 Outcomes and loss arithmetic
- **R-A08-027** (hard, METHOD) — Each closed position MUST be classified: SMALL_LOSS (loss <= planned risk), LOSS_EXCEEDED_PLAN (loss > planned risk, e.g. gap or slippage), FOURTH_OUTCOME (drawdown from entry >= `risk.fourth_outcome_review_drawdown_pct`, i.e. exit price <= entry x (1 - 0.25); the same operator is used for the open-position loss review in A07 R-A07-034 and A12 R-A12-033), SMALL_WIN (realised gain > 0 and < `risk.big_win_threshold` (2) R) or BIG_WIN (gain >= 2 R, R = planned risk amount). _Sources: S13, S23, S25. Decision: D-C26, D-DEF-23_
- **R-A08-028** (soft, METHOD) — LOSS_EXCEEDED_PLAN and FOURTH_OUTCOME results MUST be journaled with cause (gap, halt, rule violation) for the A12 review. _Sources: S13, S25, S14_
- **R-A08-029** (soft, CORE) — The app SHOULD show the gain needed to recover any open loss, R = L/(100 - L), and mark losses beyond `risk.one_to_one_zone_max_loss_pct` as outside the [[one-to-one-zone]]. _Sources: S23, S30_
- **R-A08-030** (soft, METHOD) — Capital for volatile or speculative positions SHOULD be money not needed within a year; the emergency buffer is never sized into positions (A09). _Sources: S24, S22_

### 5.7 Round-2 additions (2026-10-26)
- **R-A08-031** (hard, METHOD) — A single stock whose effective class is EXTREME MUST be sized with at most `sizing.extreme_single_stock_risk_pct` (0.5%) risk; the app SHOULD suggest gaining the exposure via a fund or basket instead. _Decision: D-R11_
- **R-A08-032** (hard, METHOD) — The class used for class-scaled detection and entry thresholds (A04 base detection, A06 setup distance, no-chase, earnings blackout) is the instrument's own class for a single stock and the industry-proxy class for a fund or basket (`risk.vol_class_threshold_basis`). Stop validation, sizing and exits keep the effective class of R-A08-010. _Decision: D-R05, D-X_
- **R-A08-033** (soft, METHOD) — The portfolio view MUST display [[total-open-risk]] = sum over open positions of shares x max(0, average entry - current stop), in currency and % of equity (a stop at or above the entry counts 0); there is no cap and the figure never blocks a buy. _Decision: D-R09_
- **R-A08-034** (hard, METHOD) — For an existing position with an `OversizeFlag`: if the weight is <= `risk.gap_breach_tolerance_multiple` (1.5) x the gap cap and the excess came from price gains, the flag is shown and no trim is required; otherwise (weight above 1.5 x cap, or a breach not caused by gains) a trim-to-cap item MUST be put on the next weekly agenda (A12). The trim is a suggestion: it is never executed automatically, and skipping it MUST be journaled with a reason. _Decision: D-R12, D-C26_

### 5.8 Round-3 additions (2026-10-26)
- **R-A08-035** (hard, METHOD) — Fractional shares are allowed iff the account's `Broker.supports_fractional` (A01) is true; then share counts are floored to `Broker.fractional_increment`, otherwise to whole shares. A final count of 0 means no trade (R-A08-006). When a position is split into tranches (A06 R-A06-037, A13 R-A13-068), each tranche is floored and the remainder is added to the last tranche. _Decision: D-R40_

## 6. Processes
**PR-A08-01 Size a new position** — trigger: A06 entry checklist passed and A07 `ExitPlan` drafted. Inputs: equity (A09),
entry, validated stop, instrument kind, effective volatility class, A09 caps and headroom, mode. Steps: (1) risk amount =
equity x risk_pct (Kelly-adjusted if enabled); (2) shares_risk = floor(risk / (entry - stop)); (3) caps: gap and
Kelly; (4) shares_final = min; EXTREME single stock -> risk 0.5% (R-A08-031); (5) compute A09 company/industry headroom
as suggestion and concentration warning, or 0 if the bucket is already breached (R-A08-005, D-R14); (6) if 0 -> no trade;
(7) record `SizingDecision` with binding cap and actual risk %; (8) split into the breakout tranche (60%) and the reserved
second-chance tranche (40%) per A06 R-A06-037 unless a profile overrides; (9) return shares to A07/A06 order placement. Output:
`SizingDecision`.

**PR-A08-02 Weekly volatility and gap check** — trigger: A12 weekly review. Refresh ATR%(14) 63-session average and class for every
holding and industry proxy (D-R10); re-run gap and stress tests on current weights; flag oversize and create trim-to-cap
agenda items per R-A08-034; report class changes to A07; refresh the total-open-risk display (R-A08-033).

**PR-A08-03 Close classification** — trigger: A07 plan CLOSED. Compute realized P/L, R-multiple, position return; set
outcome (R-A08-027); journal (A12).

**PR-A08-04 Kelly calibration (optional)** — monthly. From closed trades compute p, b, f*; set mode fallback per R-A08-021.

## 7. Calculations
```
risk_amount        = equity * risk_pct / 100                                   [currency]
stop_distance_pct  = (entry - stop) / entry * 100                              [%]
shares_risk        = floor(risk_amount / (entry - stop))
weight_risk_pct    = risk_pct / stop_distance_pct * 100                        (= shares_risk*entry/equity before floor)
cap_gap_weight     = risk.gap_max_loss_pct / risk.gap_assumed_pct[kind]        stock 2/30 = 6.67 %, fund 2/15 = 13.33 %
cap_gap_shares     = floor(equity * cap_gap_weight / entry)
company_headroom   = equity * portfolio.max_position_pct / 100 - company_exposure_amount
                     (company exposure on basis A09 `portfolio.position_cap_basis`, default company look-through)
sugg_pos_shares    = floor(company_headroom / entry)                           (A09 R-A09-011/015; advisory, D-R14)
sugg_ind_shares    = floor(industry_headroom_amount / entry)                   (A09 look-through; advisory, D-R14)
shares_final       = min(shares_risk, cap_gap_shares[, cap_kelly_shares])      (0 if bucket already breached)
shares_suggested   = min(shares_final, sugg_pos_shares, sugg_ind_shares)        warning if shares_final > shares_suggested
risk_pct_actual    = shares_final * (entry - stop) / equity * 100              <= risk_pct
TR(t)              = max(high - low, |high - close(t-1)|, |low - close(t-1)|)
ATR14(t)           = mean(TR[t-13 .. t])                                       (simple mean of 14 true ranges)
ATR%(t)            = ATR14(t) / close(t) * 100                                 [% / day]
vol_atr_pct        = mean(ATR%[t-62 .. t])                                     (63 sessions, D-R10)
class              = LOW (<1) | MEDIUM (1..<2) | HIGH (2..<4) | EXTREME (>=4)
total_open_risk    = sum_i shares_i * max(0, avg_entry_i - stop_i)             (display only, D-R09)
tolerance_cap      = risk.gap_breach_tolerance_multiple * cap_gap_weight      stock 1.5 * 6.67 = 10.0 %
inverse-vol weight = w_i = (1/vol_i) / sum_j (1/vol_j)
single impact      = weight * drop
gap loss           = weight * gap_pct * equity
recovery gain      = L / (100 - L) * 100                                       [%]
Kelly (discrete)   = f* = (b*p - q) / b,  q = 1 - p ;  risk_frac = min(risk_pct/100, k * f*)   # k <= 0.5; >= 30 closed trades
R-multiple         = realized_pnl / planned_risk_amount           # BIG_WIN if >= 2 R (D-DEF-23)
breakout_tranche   = floor(0.60 * shares_final); reserved = shares_final - breakout_tranche   # A06 R-A06-037, D-R44
fractional shares  = floor(x / increment) * increment if Broker.supports_fractional else floor(x)   # D-R40
tier stress        = weight * {0.5 (T2), 1.0 (T3)} <= 2 % of equity                                     # D-DEF-24
```

## 8. Examples / fixtures
- **EX-A08-01 S15 base fixture (verified)** — Given equity $100,000, risk 1%, entry $50, stop $46 (8%); Then risk $1,000,
  shares_risk = 1,000 / 4 = 250, position $12,500 (12.5%). Caps: single stock gap cap 6.67% -> floor(6,666.67/50) = 133
  shares; A09 10% company headroom (no existing look-through exposure to the company) -> 200 suggested, not binding. Final 133 shares = $6,650 (6.65%), actual risk $532 (0.53%), binding cap = gap. Default split (D-R44): breakout tranche 79 shares ($3,950, risk $316 = 0.32%), 54 reserved. For an
  industry fund (gap cap 13.33% -> floor(13,333.33/50) = 266): binding cap = risk -> 250 shares = $12,500 (12.5%), risk $1,000 (1.0%), split 150 at the breakout / 100 reserved; the A09 10% position cap does not apply to a diversified industry fund (D-R36); the fund's look-through exposure counts against the 25% industry cap instead.
- **EX-A08-02 Class vs stop (edge)** — Same entry $50 / stop $46 is valid only for class LOW (band 5-8%). If the effective
  class is MEDIUM, A07 widens the stop to <= $45 (10%): shares_risk = 1,000 / 5 = 200 (breakout tranche 120, 80 reserved).
- **EX-A08-03 Lower risk setting** — equity $100,000, risk 0.5%, $50 / $46 -> floor(500/4) = 125 shares ($6,250, 6.25%,
  passes the stock gap cap); breakout tranche 75 shares ($3,750, risk $300 = 0.3%), 50 reserved.
- **EX-A08-04 S07 chart read (June 2026)** — entry $25, stop $21 (16.0%); risk 1% of $100,000 -> 250 shares = $6,250
  (6.25% <= 6.67% gap cap). S07's own "about 3% of portfolio" -> risk = 3% x 16% = 0.48% of equity (source context).
  With the stock's ATR% of ~2%/day (class HIGH, R-A08-009; 2-3 band HIGH confirmed by D-R11) A07 widens the stop to $20.00 (20%): floor(1,000 / 5) = 200
  shares intended = $5,000 (5.0%), full-size risk $1,000 (1.0%); binding cap = risk; breakout tranche 120 shares ($3,000,
  risk $600 = 0.6%), 80 reserved (A06 R-A06-037, EX-A06-01, EX-A07-10).
- **EX-A08-05 Overnight gap (S25, 22 Aug 2026)** — equity $100,000, gap 30%: weight 10% -> loss $3,000 (3% > 2%: fails);
  weight 3% -> loss $900 (passes).
- **EX-A08-06 Inverse volatility (S30, 24 Oct 2026)** — Apple normal swing ±15%, Palantir ±30%; with stops at those
  distances and risk 1%: weights 6.67% vs 3.33% (Palantir about half). Without stops, inverse-vol weights 2/3 : 1/3.
- **EX-A08-07 Loss recovery (S23, S30)** — L = 1% -> +1.01%; 5% -> +5.26%; 10% -> +11.11%; 25% -> +33.33%;
  30% -> +42.86%; 50% -> +100%; 70% -> +233.33%; 90% -> +900%. L = 10% is the last value inside the one-to-one zone.
- **EX-A08-08 Single-position impact (S13, S23, S30)** — one holding -20%: 5 equal positions (20%) -> -4%; 10 (10%) -> -2%;
  20 (5%) -> -1%; 30 at ~3% -> -0.6%.
- **EX-A08-09 Stress check (S05)** — weight 12% x 20% drop = 2.4% > 2% -> reduce suggestion; weight 10% -> 2.0% passes.
- **EX-A08-10 Fractional Kelly** — p = 0.5, b = 2: f* = (1.0 - 0.5)/2 = 0.25; half-Kelly 0.125 -> effective risk stays 1%
  (cap binds). p = 0.35, b = 2: f* = 0.025; quarter-Kelly 0.00625 -> effective risk 0.625%. p = 0.30, b = 2:
  f* = -0.05 -> new entries blocked.
- **EX-A08-11 Prohibitions** — a buy funded on margin, or a 3x leveraged ETF -> rejected (R-A08-023). Average entry $50,
  last close $44, add order not in the entry plan -> rejected (R-A08-024).
- **EX-A08-12 Outcome classes** — planned risk $1,000: exit loss $950 -> SMALL_LOSS; gap exit loss $2,000 ->
  LOSS_EXCEEDED_PLAN (2.0 R); position return -30% -> FOURTH_OUTCOME (also journaled). Gains: $2,000 -> 2.0 R -> BIG_WIN
  (edge, inclusive); $1,999 -> 1.999 R -> SMALL_WIN (D-DEF-23).
- **EX-A08-13 Volatility classes (ATR%, D-R10/D-R11)** — 63-session average ATR% 0.8% -> LOW; 1.0% -> MEDIUM (edge, >= 1);
  1.5% -> MEDIUM; 2.0% -> HIGH (edge, >= 2); 2.5% -> HIGH (2-3 band, confirmed); 3.5% -> HIGH; 3.99% -> HIGH; 4.0% ->
  EXTREME (edge, >= 4); 6.0% -> EXTREME. ATR input: previous close 50.00, high 52.00, low 49.00 -> TR = max(3.00, 2.00,
  1.00) = 3.00; ATR14 = 1.50 at close 60.00 -> ATR% = 2.5% for that session.
- **EX-A08-14 Effective class** — stock LOW, industry proxy MEDIUM -> MEDIUM (band 10-15%).
- **EX-A08-15 Industry headroom (D-R14)** — A09 industry cap 25%, current look-through exposure 22% of $100,000 -> headroom
  $3,000 -> at $50 60 shares suggested. Single stock, entry $50, stop $46: shares_final = min(risk 250, gap 133) = 133
  ($6,650; breakout tranche 79 = $3,950); post-trade industry exposure with both tranches 22% + 6.65% = 28.65% > 25% ->
  concentration warning (checked on the full intended size), the buy is allowed (the
  user may reduce to the suggested 60). Edge: current exposure 26% (already breached) -> 0 shares, buy blocked (R-A09-010).
- **EX-A08-16 Zero shares (edge)** — equity $10,000, risk 1% = $100, entry $500, stop $380 (24%): 100/120 = 0.83 ->
  floor 0 -> no trade. With a broker that supports fractional shares (increment 0.001): 0.833 shares = $416.50, risk
  0.833 x 120 = $99.96 (R-A08-035, D-R40); breakout tranche floor(0.6 x 0.833) = 0.499 shares, 0.334 reserved.
- **EX-A08-17 S14 conflation fixed (D-S14)** — $20,000 x 5% = $1,000 position (a size, not risk); with a 10% stop, risk =
  $100 = 0.5% of equity, displayed separately.
- **EX-A08-18 EXTREME single stock (D-R11)** — equity $100,000; stock ATR% 5.2% -> EXTREME, band 25-35%; entry $40.00,
  stop $28.00 (30.0%, inside the band). Risk capped at 0.5% = $500 -> floor(500 / 12) = 41 shares = $1,640 (1.64%; breakout tranche 24 shares, risk $288, 17 reserved),
  far below the gap cap (166 shares); the app suggests an industry fund instead (R-A08-031).
- **EX-A08-19 Gap-test breach of a holding (D-R12)** — equity $100,000, single stock, gap cap 6.67%, tolerance 1.5 x
  6.67% = 10.0%. Weight rises from 6.0% to 9.0% on gains -> OversizeFlag shown, no trim required. Weight reaches 10.5%
  ($10,500) -> trim-to-cap item on the next weekly agenda: sell about $3,833 to return to $6,667 (6.67%); if the user
  skips it, the skip is journaled with a reason; no automatic sell (R-A08-034).
- **EX-A08-20 Total open risk display (D-R09)** — three positions with risk at stop $532, $1,000 and $800 on equity
  $100,000 -> total open risk $2,332 (2.33%) displayed in the portfolio view; no cap, no block (R-A08-033).
- **EX-A08-21 Tier stress (D-DEF-24)** — equity $100,000: a T2 position at 4% -> 4% x 50% = 2.0% (passes, edge); at 5% ->
  2.5% > 2% -> reduce suggestion to 4%. A T3 position at 2% -> 2.0% passes; at 3% -> 3.0% -> reduce to 2%.
- **EX-A08-22 Kelly sample and first live trades (D-DEF-22, D-DEF-25)** — 29 closed live trades -> FRACTIONAL_KELLY falls back
  to RISK_BASED; at 30 trades Kelly is usable with k in {0.25, 0.5}; k = 0.75 is rejected. A new user's live trades 1-3 use
  0.5% risk; trade 4 uses the configured `sizing.risk_pct` (e.g. 1%).

## 9. Variants & open points
Variants not chosen (decision ref):
- Risk/"size" 2-5% of equity per trade (S14) -> profile [[prf-beginner-index]] in A13 with explicit risk display (D-S14).
- Weight-only sizing via gap damage (S25) -> used as a cap on top of risk sizing (D-C10, D-OPEN-3).
- Survival-check "yes, could cease to exist" -> smaller position (S25) -> replaced by the mandatory survival veto in A05 (D-C03).
- Equal weighting of 2-4 sectors / top-N (S16, S17) -> profile [[prf-momentum-rotation]] (A13).
- Contrarian scenario exposure 10-20% (S06) and gold ~5% (S28) -> allocation topics in A09/A11, not position sizing.

- Volatility as average daily range over 21 sessions or standard deviation of returns -> replaced by ATR%(14), 63-session average (D-R10).
- Portfolio cap on total open risk -> not adopted; display only (D-R09).
- Automatic trim of gap-test breaches -> not adopted; agenda item, journaled if skipped (D-R12).

Open points: none.
- Closed by D-R40 — OPEN-A08-1 (fractional shares iff the broker supports them).
- Closed by D-DEF-22 — OPEN-A08-2 (Kelly needs >= 30 closed trades, k <= 0.5; pending user review).
- Closed by D-DEF-23 — OPEN-A08-4 (big win >= 2 R; pending user review).
- Closed by D-DEF-24 — OPEN-A08-5 (tier stress max 2% of equity; pending user review).
- Closed by D-DEF-25 — OPEN-A08-9 (3 initial live trades; pending user review).

Closed by round-2 decisions (2026-10-26): OPEN-A08-3 (D-R11), OPEN-A08-6 (D-R09), OPEN-A08-7 (D-R10), OPEN-A08-8 (D-R12).

## 10. Traceability
| Rule/Concept | Sources |
|---|---|
| R-A08-001..008 risk budget, formula, caps | S13, S15, S23, S30, S07, S05, S20, S24; D-C09, D-C10, D-C11, D-S14, D-C08 |
| R-A08-009..014 volatility class, inverse-vol | S07, S23, S30, S16; D-C08, D-X, D-C09 |
| R-A08-015..019 gap, stress, tier, stomach | S25, S13, S05, S23, S22, S30, S21; D-OPEN-3 |
| R-A08-020..022 fractional Kelly | S15, S16, S17, S19; D-C09 |
| R-A08-023..026 prohibitions | S13, S12, S30, S07, S14; D-S14 |
| R-A08-027..030 outcomes, recovery | S13, S23, S25, S30, S24, S22; D-C26 |
| R-A08-031..034 EXTREME class, threshold basis, total open risk, gap-breach handling | S23; D-R05, D-R09, D-R11, D-R12 |
| R-A08-035 fractional shares, tranche rounding | D-R40 |
| R-A08-018, R-A08-021, R-A08-027 tier stress, Kelly sample, big-win boundary | S15, S22; D-DEF-22, D-DEF-23, D-DEF-24 |
| Fixtures | S05, S07, S13, S14, S15, S23, S25, S30 |
