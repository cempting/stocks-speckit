---
id: A07
title: Exit & Selling
context: CTX-C
layers: [CORE, METHOD]
status: draft
sources: [S01, S05, S07, S08, S13, S14, S15, S16, S17, S20, S21, S22, S23, S24, S25, S30]
decisions: [D-X, D-C05, D-C08, D-C12, D-C13, D-C26, D-C27, D-C29, D-C04, D-C28, D-OPEN-2, D-OPEN-4, D-S14, D-R01, D-R02, D-R04, D-R11, D-R15, D-R16, D-R17, D-R25, D-R31, D-R34, D-R35, D-R39]
depends_on: [A01, A02, A04, A06, A08, A09, A12]
---
# A07 — Exit & Selling

## 1. Purpose & scope
Defines how every open long position is exited: the written [[exit-plan]], the three independent exit mechanisms of the
exit model D-X — [[trend-exit]] on the [[purple-line]], [[protective-stop]] below the [[buyer-area]], and
[[profit-taking]] — their precedence ([[exit-precedence]]), the up-only stop invariant ([[stop-ratchet]]),
the review flags that are explicitly *not* exits, and the automation via [[price-alert]]s and resting broker orders.

Included: exit plan lifecycle, stop placement and validation against the [[volatility-class]], stop raising,
profit-taking thresholds by volatility class x [[market-regime]], trigger evaluation and order generation, covenants,
broker audit.
Excluded (referenced only): position size and risk budget (A08), volatility class measurement (A08), market-regime
and RS classification (A02), entry signals and the second-chance add (A06), redeploying capital after an exit (A09/A05),
weekly/monthly routine mechanics (A12), alternative exit styles of profiles S14/S16/S17 (A13).
Short positions are out of scope (the method is long-only).

## 2. Concepts
- [[exit-plan]] — written before buying, placed as live orders in the same sitting; the unit this aspect manages.
- [[three-step-selling-system]] — Protect the Money / Take the Profit / Automate All of It; frames this aspect.
- [[purple-line]] / [[simple-moving-average]] — 150-day SMA of daily closes; reference line of the [[trend-exit]].
- [[trend-exit]] — daily close below the 150-SMA creates a sell order for the next session.
- [[protective-stop]] / [[stop-loss-order]] — live broker stop below the [[buyer-area]]; executes automatically.
- [[buyer-area]] — most recent swing low (5 higher lows on each side) within the last 3 months; anchors the stop at swing low − 1 × ATR(14) (D-R04).
- [[average-true-range]] / [[atr-percent]] — ATR(14) sets the stop offset below the buyer area; ATR% sets the volatility class (A08).
- [[volatility-class]] — validates [[stop-distance]]; owned by A08.
- [[knocked-out]] — failure mode of a stop too tight for the instrument's volatility.
- [[stop-ratchet]] — a stop only moves up.
- [[trailing-stop]] / [[breakeven-stop]] — fixed-%-trailing and breakeven raises are optional variants, not defaults.
- [[profit-taking]] / [[partial-exit]] — take half on [[extension]] or, only in a bearish regime, on a [[quick-win]] (D-R15); remainder exits below the [[yellow-line]].
- [[market-on-open-order]] — order type of every next-session exit; the broker stop stays live in parallel (D-R16).
- [[smart-money-evidence]] — heavy insider selling (insider flip) raises REVIEW_INSIDER, never an exit (D-R25).
- [[extension]] — % close above the 50-SMA, compared with a threshold matrix volatility class x [[market-regime]].
- [[exit-precedence]] — all triggers independent, first to fire wins.
- [[rs-deterioration]] — review/reduce flag only, never an automatic exit (A02 classifies).
- [[three-covenants]] — never buy below the line, never ignore your sell rule, this time is never different.
- [[three-outcomes]] / [[fourth-outcome]] — purpose of the exit model: only big win, small win, small loss (A08 classifies).
- [[gap]] / [[trading-halt]] — events in which a stop cannot protect; handled by sizing (A08).
- [[price-alert]] / [[daily-automation]] — daily work is done by alerts and resting orders only.
- [[exit-liquidity]] — what holders become if they do not exit when institutions sell.
- [[one-to-one-zone]] / [[loss-recovery-asymmetry]] — why losses are cut early.
- [[averaging-down]] — forbidden (rule owned by A08).
- [[two-halves-of-loss]] / [[holding-and-hoping]] — behavioural failure modes the mechanical exit prevents (A12).

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| ExitPlan | id | id | unique | one per `Position` |
| ExitPlan | position_id | ref `Position` | required | |
| ExitPlan | written_at | timestamp | MUST be <= entry order placement | R-A07-001 |
| ExitPlan | state | enum | see lifecycle | |
| ExitPlan | trend_ma_length | int sessions | = `exit.trend_ma_length` at creation; `exit.trend_ma_substitute_length` (50) while fewer than 150 sessions exist | snapshot of parameters; D-R17 |
| ExitPlan | initial_stop | price | < entry price | R-A07-010 |
| ExitPlan | current_stop | price | >= every previous value | R-A07-016 |
| ExitPlan | stop_history | list of (timestamp, price, reason) | monotonic non-decreasing price | audit trail |
| ExitPlan | buyer_areas_used | list of ref `BuyerArea` | >= 1 | |
| ExitPlan | volatility_class | ref `VolatilityClass` | effective class from A08 | |
| ExitPlan | stop_distance_pct | % | (entry - initial_stop)/entry*100 | feeds A08 sizing |
| ExitPlan | extension_threshold_pct | % | from matrix, re-read each evaluation | depends on current regime |
| ExitPlan | partial_taken | bool | at most one partial | R-A07-024 |
| ExitPlan | remainder_ma_exit_active | bool | true after partial | R-A07-025 |
| ExitPlan | flags | set {REVIEW_RS, REVIEW_DRAWDOWN, REVIEW_VOLUME, REVIEW_INSIDER, UNPROTECTED, UNPROTECTED_EXCEPTION, GAP_EVENT, NO_TREND_HISTORY} | UNPROTECTED_EXCEPTION only for physical holdings (R-A07-043) | flags never close a position |
| ExitPlan | rationale | text | required | written exit reasoning (S23) |
| ExitTrigger | kind | enum {PROTECTIVE_STOP, TREND_EXIT_150, PROFIT_EXTENSION, PROFIT_QUICK_WIN, REMAINDER_EXIT_50, MANUAL_REVIEW, DISCRETIONARY_SELL} | | DISCRETIONARY_SELL = journaled rule deviation (D-C29) |
| ExitTrigger | fired_at | timestamp / session date | | |
| ExitTrigger | evaluation_basis | enum {INTRADAY_BROKER, DAILY_CLOSE, ALERT_MANUAL} | stop = intraday; others = daily close; ALERT_MANUAL = alert-based exit of a physical holding (R-A07-043) | |
| ExitTrigger | fraction | 0..1 | 1.0 for full exits; `exit.partial_fraction` for profit-taking | |
| ExitTrigger | resulting_order_id | ref `Order` | | |
| ExitTrigger | outcome | enum {EXECUTED, SUPERSEDED, CANCELLED} | | SUPERSEDED when another trigger closed the position first |
| BuyerArea (new) | instrument_id, level, date, evidence, swing_strength, atr14_at_placement | price, date, text, int, price | level = a swing low (low with `exit.buyer_area_swing_strength` higher lows on each side); date within `exit.buyer_area_lookback_months` | "price fell and was bought back up" (S25); D-R04 |
| StopOrder | stop_price, status, placed_at | price, enum, timestamp | placed_at same sitting as entry | CORE broker object (A01); becomes market order when triggered |
| Alert | condition, indicator, timeframe, frequency | e.g. crosses below / SMA 150 / daily / once per day | one per open position | R-A07-034 |
| Position | (ref) | | | owned by A09; outcome classification A08 |

### ExitPlan lifecycle
```
DRAFT --(stop validated, sized via A08, entry+stop orders placed same sitting)--> PENDING_ENTRY
PENDING_ENTRY --(entry cancelled/expired)--> CANCELLED
PENDING_ENTRY --(entry filled; stop live; exit alerts saved)--> ARMED
ARMED --(PROFIT_EXTENSION | PROFIT_QUICK_WIN fired)--> PARTIAL_PENDING --(partial filled)--> PARTIAL
ARMED|PARTIAL --(TREND_EXIT_150 | REMAINDER_EXIT_50 fired at close)--> EXITING --(sell filled)--> CLOSED
ARMED|PARTIAL|PARTIAL_PENDING|EXITING --(PROTECTIVE_STOP filled)--> CLOSED
ARMED|PARTIAL --(MANUAL_REVIEW reduce/close after a review flag, journaled)--> PARTIAL | CLOSED
ARMED|PARTIAL --(DISCRETIONARY_SELL between reviews; never blocked; journaled rule deviation, D-C29)--> PARTIAL | CLOSED
```
Invariants: in ARMED, PARTIAL, PARTIAL_PENDING and EXITING a live `StopOrder` exists for the full open quantity
(else flag UNPROTECTED; a physical holding instead carries UNPROTECTED_EXCEPTION with its stop alert, R-A07-043); `current_stop` never decreases; CLOSED is terminal; on CLOSED all remaining orders and alerts of
the plan are cancelled.

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `exit.trend_ma_length` | 150 | 150 canonical (other lengths only in profiles) | sessions | D-C05; S13, S23, S25 |
| `exit.trend_ma_type` | SMA | SMA | — | D-C05; S13 ("simple, not exponential") |
| `exit.trend_price_basis` | daily close | daily close | — | D-C26; S13, S23 |
| `exit.trend_close_buffer_pct` | 0 | 0 (fixed) | % below SMA | D-C26, D-R35 (any close below) |
| `exit.trend_requires_rising_ma` | false | false (fixed) | — | D-X, D-C26, D-R35 (no slope condition) |
| `exit.trend_exit_execution` | next session | next session | — | D-C26 |
| `exit.trend_exit_order_type` | market-on-open | {market-on-open} | — | D-R16 (applies to every next-session exit order) |
| `exit.trend_ma_substitute_length` | 50 | 50 | sessions (used while < 150 sessions of history) | D-R17 |
| `exit.stop_placement_mode` | standard (last buyer area) | {standard, conservative} | — | D-C08; S23 (last), S25 (lowest of 2-3) |
| `exit.buyer_area_count_conservative` | 3 | 2-3 | areas | D-C08; S25 |
| `exit.buyer_area_lookback_months` | 3 | 3 | calendar months | D-R04; S25 "last few months" |
| `exit.buyer_area_swing_strength` | 5 | 5 | higher lows on each side of the swing low | D-R04 |
| `exit.stop_offset_atr_multiple` | 1.0 | 1.0 | x ATR(14) below the buyer area | D-R04; S13/S23 "slightly below" |
| `exit.stop_raise_mode` | structure | {structure, gain_threshold, breakeven_after_rally} (the optional modes add to structure) | — | D-R34, D-C12/C13; S13 (under each higher low/new base) |
| `exit.stop_raise_gain_threshold_pct` | 10 (only if mode = gain_threshold) | > 0 | % gain | S23; optional per D-C12/C13 |
| `exit.stop_raise_cadence` | weekly review | weekly review | — | D-C04, D-C28 (A12 `routine.weekly_review_day`) |
| `exit.partial_fraction` | 0.5 | 0 < f < 1 | of open quantity | D-C12; S23, S30 |
| `exit.extension_ma_length` | 50 | 50 | sessions | D-OPEN-4 |
| `exit.extension_threshold_pct[low][bull/sideways/bear]` | 15 / 10 / 5 | > 0 | % close above 50-SMA | D-OPEN-4, D-R02 |
| `exit.extension_threshold_pct[medium][bull/sideways/bear]` | 25 / 15 / 8 | > 0 | % | D-OPEN-4, D-R02 |
| `exit.extension_threshold_pct[high][bull/sideways/bear]` | 40 / 25 / 12 | > 0 | % | D-OPEN-4, D-R02 |
| `exit.extension_threshold_pct[extreme][bull/sideways/bear]` | 60 / 35 / 18 | > 0 | % | D-R31 |
| `exit.physical_alert_exit` | true | true (fixed) | — | D-R39 (physical gold: alert + manual sale) |
| `exit.quick_win_enabled` | true | {true, false} | — | D-C12; S30 |
| `exit.quick_win_regimes` | {bearish} | {bearish} | market regime (A02) | D-R15 |
| `exit.quick_win_gain_pct[low/medium/high/extreme]` | 4 / 5 / 6 / 6 | 4-6 | % gain vs entry | D-C12, D-R15; S30 |
| `exit.quick_win_window_sessions` | 5 | >= 1 | sessions since entry | S30 ("in a week") |
| `exit.remainder_ma_length` | 50 | 50 | sessions | D-C12; S30 |
| `exit.max_partials` | 1 | 1 | per position | D-C12 (take half, remainder by rule) |
| `exit.fixed_trailing_stop_pct` | disabled | 10 (S25), 15-20 (S17) when enabled | % | variant only; D-C12 |

Parameters referenced, owned elsewhere: A08 `risk.vol_class_*` (class bands and boundaries, incl. EXTREME 25-35%), `sizing.max_risk_pct`,
`risk.fourth_outcome_review_drawdown_pct`; A02 market-regime classification and RS-deterioration parameters
(`scoreboard.*`, incl. the D-OPEN-2 slope test); A12 `routine.weekly_review_day`.

## 5. Rules

### 5.1 Exit plan and order placement
- **R-A07-001** (hard, METHOD) — An `ExitPlan` with initial stop level, trend exit and profit-taking rules MUST be written before the entry order is submitted; an entry order without a written plan MUST be rejected. _Sources: S13, S23, S25, S05, S07, S08, S22. Decision: D-X_
- **R-A07-002** (hard, METHOD) — The protective `StopOrder` MUST be submitted in the same sitting as the entry order (linked/contingent order where the broker supports it). _Sources: S13, S23, S07, S30. Decision: D-X_
- **R-A07-003** (hard, METHOD) — Every open position MUST have a live broker stop covering its full open quantity; the broker audit (PR-A07-05) MUST list every position without one as UNPROTECTED. The only sanctioned exception is a physical holding that cannot carry a broker stop (R-A07-043). _Sources: S23, S30. Decision: D-R39_
- **R-A07-004** (hard, METHOD) — A daily [[price-alert]] "price crosses below SMA 150, daily, once per day" MUST exist for every open position; the plan is ARMED only after the alert is saved. _Sources: S23, S05_
- **R-A07-005** (hard, CORE) — The system MUST treat a triggered stop as a market order without price guarantee and MUST record the actual fill price and slippage versus the stop level. _Sources: S23, S25_

### 5.2 Trend exit (150-SMA)
- **R-A07-006** (hard, METHOD) — If the daily close is below the 150-SMA (any close below; `exit.trend_close_buffer_pct` fixed 0), a TREND_EXIT_150 trigger MUST fire and a market-on-open sell order for the full open quantity MUST be generated for the next session (R-A07-040). _Sources: S13, S23, S25, S05, S17. Decision: D-C05, D-C26, D-R16, D-R35_
- **R-A07-007** (hard, METHOD) — Intraday trades below the 150-SMA that do not produce a qualifying daily close MUST NOT fire the trend exit. _Sources: S13 ("never closed materially below it"), S25. Decision: D-C26_
- **R-A07-008** (hard, METHOD) — The trend exit MUST NOT be gated by the slope of the 150-SMA and MUST NOT use a close buffer (`exit.trend_requires_rising_ma` = false and `exit.trend_close_buffer_pct` = 0 are fixed); S13's "materially below" is not adopted. _Sources: S13, S20. Decision: D-X, D-C26, D-R35_
- **R-A07-009** (hard, METHOD) — If fewer than `exit.trend_ma_length` daily closes exist, the plan MUST carry flag NO_TREND_HISTORY and the trend exit uses the `exit.trend_ma_substitute_length` (50) SMA instead: a daily close below the 50-SMA fires TREND_EXIT_150 (substitute) for the full quantity. From the session on which 150 closes exist, the 150-SMA applies and the flag clears. With fewer than 50 closes, protection relies on the protective stop alone. _Sources: derived from S13/S23 formula (SMA undefined). Decision: D-R17_

### 5.3 Protective stop
- **R-A07-010** (hard, METHOD) — The initial protective stop MUST be placed at the most recent [[buyer-area]] (mode `standard`) or the lowest of the last `exit.buyer_area_count_conservative` buyer areas (mode `conservative`) minus `exit.stop_offset_atr_multiple` (1.0) x ATR(14) at placement; it MUST NOT be placed at a round percentage chosen without reference to chart structure. The result is then validated by R-A07-011/012. _Sources: S23, S25, S07 ("below breakout"). Decision: D-C08, D-R04_
- **R-A07-011** (hard, METHOD) — The stop distance MUST be validated against the effective [[volatility-class]] of instrument and industry (A08): if the distance is below the class band minimum, the stop MUST be moved lower (to the next lower buyer area, or at least to the band minimum); the stop MUST NOT be tightened to reduce risk. _Sources: S07, S23, S30. Decision: D-C08, D-X_
- **R-A07-012** (hard, METHOD) — If the validated stop distance exceeds the class band maximum, the stop is kept and the position size MUST be reduced via A08 sizing; the plan MUST show a "wide stop" notice. _Sources: S23 ("the exit is not the problem. The position is too large"), S30. Decision: D-C08_
- **R-A07-013** (soft, METHOD) — A stop distance below the class band minimum MUST be flagged with a [[knocked-out]] warning stating the class's typical daily move (e.g. 4-6% stop on a 3-4%/day instrument). _Sources: S07, S23, S30_
- **R-A07-014** (hard, METHOD) — If the protective stop is hit intraday, the broker executes it automatically; the system MUST NOT require or wait for user confirmation. _Sources: S23, S14. Decision: D-C26_
- **R-A07-015** (hard, METHOD) — After a [[gap]] that fills a stop below its level, the exit rules MUST NOT be removed or suspended for remaining or future positions; the plan records flag GAP_EVENT and the loss is classified by A08. _Sources: S13, S25_

### 5.4 Moving the stop
- **R-A07-016** (hard, METHOD) — [[stop-ratchet]]: any stop change with new_stop < current_stop MUST be rejected; widening a stop "further away" is the same violation. _Sources: S13, S23, S25, S14. Decision: D-C12_
- **R-A07-017** (hard, METHOD) — With `exit.stop_raise_mode` = structure (default), at each weekly review the stop MUST be raised to the new last buyer area level, i.e. the most recent swing low (R-A07-042) − `exit.stop_offset_atr_multiple` (1.0) × ATR(14), whenever that level is higher than the current stop; otherwise the stop is left unchanged. R-A07-016 and R-A07-018 apply. _Sources: S13, S23. Decision: D-R34, D-C12, D-C04_
- **R-A07-018** (hard, METHOD) — A raised stop MUST still satisfy the class band minimum measured from the current close; a raise that would violate it MUST be capped at the highest compliant level. _Sources: S07, S23. Decision: D-C08_
- **R-A07-019** (soft, METHOD) — Optional modes (not default, in addition to the structure raise): `gain_threshold` considers a raise only for positions up >= `exit.stop_raise_gain_threshold_pct`; `breakeven_after_rally` moves the stop to about entry after a first rally ([[breakeven-stop]]). _Sources: S23, S07. Decision: D-C12, D-C13_
- **R-A07-020** (soft, METHOD) — A fixed-percentage [[trailing-stop]] MUST NOT be the default mechanism; it MAY be enabled as a variant via `exit.fixed_trailing_stop_pct` and is still subject to R-A07-016. _Sources: S25, S23 ("rookie move"), S17. Decision: D-C12_
- **R-A07-021** (hard, METHOD) — Stop changes are made only at the weekly review (or by automation that a weekly review configured), never as an intraday discretionary decision. _Sources: S13, S23, S14. Decision: D-C04, D-C28_

### 5.5 Profit-taking
- **R-A07-022** (hard, METHOD) — PROFIT_EXTENSION fires when a daily close is >= `exit.extension_threshold_pct[vol_class][regime]` above the 50-SMA, using the effective volatility class (A08) and the current market regime (A02) at that close; it generates a market-on-open sell order for `exit.partial_fraction` of the open quantity for the next session. _Sources: S30, S23. Decision: D-C12, D-OPEN-4, D-R02, D-R16_
- **R-A07-023** (hard, METHOD) — If `exit.quick_win_enabled` and the current market regime (A02) is in `exit.quick_win_regimes` (bearish), PROFIT_QUICK_WIN fires when, within `exit.quick_win_window_sessions` sessions of entry, a daily close is >= `exit.quick_win_gain_pct[vol_class]` (LOW 4, MEDIUM 5, HIGH 6, EXTREME 6%) above the average entry price; it generates a partial sell order like R-A07-022. In a bullish or sideways regime only the extension matrix applies. _Sources: S30. Decision: D-C12, D-R15_
- **R-A07-024** (hard, METHOD) — At most `exit.max_partials` (1) profit-taking partial is executed per position; after it, both profit-taking triggers are disabled for that plan. _Sources: S30, S23. Decision: D-C12_
- **R-A07-025** (hard, METHOD) — After the partial fills, the remainder MUST exit on a daily close below the 50-SMA (REMAINDER_EXIT_50, sell next session), in addition to the protective stop and the trend exit which stay active. _Sources: S30. Decision: D-C12_
- **R-A07-026** (soft, METHOD) — Without a partial, the position trails only via the trend exit and protective stop; no fixed profit target applies. _Sources: S13, S23. Decision: D-C12_
- **R-A07-027** (hard, METHOD) — Profit targets MUST come from the configured rules (extension matrix, quick win); manually typed round-number targets ("hope targets") are not allowed in the default profile, and a target MUST NOT be raised after it has been reached. _Sources: S23. Decision: D-C12_
- **R-A07-028** (soft, METHOD) — The extension threshold is re-evaluated on every close; when the regime changes (e.g. bull -> bear), the lower threshold applies from the next close. _Decision: D-OPEN-4_

### 5.6 Precedence and non-price signals
- **R-A07-029** (hard, METHOD) — [[exit-precedence]]: all triggers are evaluated independently and the first to fire wins; a full exit (stop, trend exit, remainder exit) supersedes any pending partial, and once the position is flat all other pending exit orders MUST be cancelled and their triggers marked SUPERSEDED. _Decision: D-C26_
- **R-A07-030** (hard, METHOD) — If a partial and a full-exit trigger fire on the same close, only the full-exit order is generated. _Decision: D-C26_
- **R-A07-031** (hard, METHOD) — [[rs-deterioration]] (A02) MUST raise flag REVIEW_RS and block new buys in that industry, and MUST NOT generate any sell order. Per D-C27 a red status blocks new buys immediately and sets REVIEW_RS at the next weekly session; a drop out of the top RS group sets it after 2 consecutive monthly reviews. _Sources: S20, S16. Decision: D-C27_
- **R-A07-032** (hard, METHOD) — Only price-based triggers (protective stop, trend exit, extension, quick win, remainder exit) are automatic; volume warnings (e.g. [[fading-volume-rally]], heavy selling days), insider selling and macro news MAY raise review flags only. _Sources: S30, S23, S07. Decision: D-C27_
- **R-A07-033** (soft, METHOD) — A review flag MAY lead to a MANUAL_REVIEW reduce or close decided at the weekly or monthly review and journaled with its reason; it MUST NOT lower the stop. _Sources: S20, S30. Decision: D-C27, D-C04_
- **R-A07-034** (soft, METHOD) — A position whose drawdown from entry is >= A08 `risk.fourth_outcome_review_drawdown_pct` (25%), i.e. last close <= entry × (1 − 0.25), MUST carry flag REVIEW_DRAWDOWN; "it will come back" is not a valid hold reason. _Sources: S23, S25_

### 5.7 Covenants and discipline
- **R-A07-035** (hard, METHOD) — [[three-covenants]] covenant 2: a fired exit trigger MUST be executed; the system MUST NOT offer "snooze", "skip" or "hold through earnings" for a fired trigger. _Sources: S23, S05, S20_
- **R-A07-036** (hard, METHOD) — Covenant 3: no exception for politics, earnings dates, news, a famous investor buying or a still-good macro story. _Sources: S23, S20, S21_
- **R-A07-037** (hard, METHOD) — A feeling, or price returning to the entry, is not an exit rule; the system MUST NOT suggest such a sell. A discretionary sell outside the triggers or a MANUAL_REVIEW MUST NOT be blocked (reducing risk is always permitted), but it MUST be recorded as ExitTrigger kind DISCRETIONARY_SELL, journaled as a `rule deviation` with a mandatory reason and put on the agenda of the next weekly session (A12 R-A12-005). Discretionary buys between reviews stay blocked. _Sources: S23, S14, S13, S25. Decision: D-C29_
- **R-A07-038** (hard, METHOD) — The exit model MUST make the [[fourth-outcome]] impossible except through gaps or trading halts (which A08 sizing bounds), so that each closed position lands in the [[three-outcomes]]. _Sources: S13, S23, S25. Decision: D-C26_
- **R-A07-039** (soft, METHOD) — Exit rules MUST NOT be edited while the position is open; rule changes apply to new plans after a closed trade is reviewed. _Sources: S14, S23_

### 5.8 Round-2 additions (2026-10-26)
- **R-A07-040** (hard, METHOD) — Every next-session exit order (TREND_EXIT_150, REMAINDER_EXIT_50, profit-taking partials) MUST be a [[market-on-open-order]]; the protective broker `StopOrder` MUST stay live in parallel until the exit order fills. The two orders MUST be linked one-cancels-other (or equivalent quantity reduction) so that the total sold never exceeds the open quantity; after a partial fill the stop covers the remaining quantity. _Decision: D-R16, D-C26_
- **R-A07-041** (soft, METHOD) — Heavy insider selling on a held instrument (InsiderTurnaround / insider flip, A04; S23) MUST set flag REVIEW_INSIDER for the next weekly review; [[smart-money-evidence]] MUST NOT generate, modify or cancel any order or stop. _Sources: S23. Decision: D-R25, D-C27_
- **R-A07-042** (hard, METHOD) — A [[buyer-area]] is a swing low: a session low with at least `exit.buyer_area_swing_strength` (5) sessions on each side whose lows are all higher, dated within the last `exit.buyer_area_lookback_months` (3) months; "most recent" = the latest such swing low. If none exists in the window, no structural stop can be set and the plan cannot leave DRAFT. _Sources: S23, S25. Decision: D-R04_

### 5.9 Round-3 additions (2026-10-26)
- **R-A07-043** (hard, METHOD) — Sanctioned exception to R-A07-003: a physical holding (bullion, allocated vault gold) that cannot carry a live broker stop MUST instead carry (a) a price alert at the protective-stop level on the spot price, (b) the 150-SMA trend-exit alert and the profit-taking alerts of its plan, and (c) flag UNPROTECTED_EXCEPTION. When an alert fires, the system MUST create a manual sale task for the next session (ExitTrigger evaluation_basis ALERT_MANUAL); the sale is a rule-mandated exit, not a discretionary sell, and its fill (dealer buyback price) and slippage are recorded. The broker audit lists such positions separately as sanctioned exceptions, not as violations, and checks that the alerts exist. The stop ratchet, band validation and sizing rules apply unchanged. _Sources: S28. Decision: D-R39, D-X_

## 6. Processes

**PR-A07-01 Create exit plan** — trigger: candidate passes the A06 entry checklist. Inputs: price history, buyer areas,
A08 volatility class. Steps: (1) identify buyer areas (swing lows, R-A07-042) within `exit.buyer_area_lookback_months`; (2) set the stop per mode at
swing low − 1 × ATR(14) (R-A07-010); (3) validate against the volatility class (R-A07-011..013); (4) hand stop distance to A08 for shares;
(5) write the rationale; (6) place entry + stop in one sitting; (7) save the 150-SMA alert; (8) state -> PENDING_ENTRY,
then ARMED on fill. Output: ARMED `ExitPlan`, live `StopOrder`, `Alert`.

**PR-A07-02 Daily trigger evaluation (automated)** — trigger: each session close (D-C04: daily = automation only).
Steps: (1) broker reports stop fills -> PROTECTIVE_STOP, CLOSED, cancel rest; (2) compute SMA150 (or the SMA50 substitute,
R-A07-009), SMA50, extension, gain since entry, current regime; (3) evaluate TREND_EXIT_150, REMAINDER_EXIT_50,
PROFIT_EXTENSION, PROFIT_QUICK_WIN (bearish regime only); (4) apply precedence R-A07-029/030; (5) create next-session
market-on-open orders, keep the broker stop live (R-A07-040), notify; (6) update REVIEW_DRAWDOWN and REVIEW_INSIDER flags. Output: orders,
`ExitTrigger` records.

**PR-A07-03 Weekly exit pass** — trigger: A12 weekly review (default Saturday, D-C28). Steps: (1) check each alert fired;
(2) confirm every position has a live stop (PR-A07-05); (3) apply the stop-raise mode (R-A07-017..019) with ratchet and
band checks; (4) place/adjust next week's orders; (5) set REVIEW_RS for holdings in industries that turned red (D-C27) and list
review flags (incl. DISCRETIONARY_SELL deviations, D-C29) for decision; (6) journal. Output: updated stops,
review list.

**PR-A07-04 Monthly review hook** — trigger: A12 monthly review. Read A02 RS deterioration; set/clear REVIEW_RS;
record any MANUAL_REVIEW decision (R-A07-033).

**PR-A07-05 Broker audit** — weekly. Compare positions held with positions holding a live stop for the full quantity
and a saved alert; list gaps with a fix date; any gap sets UNPROTECTED. Physical holdings are listed as sanctioned exceptions (UNPROTECTED_EXCEPTION) with their stop alert (R-A07-043).

**PR-A07-06 Post-exit** — on CLOSED: record fill, slippage, trigger kind, and hand the result to A08 (outcome class)
and A12 (journal); freed capital goes to the A09/A05 rotation process.

## 7. Calculations
```
SMA_N(t)          = mean(close[t-N+1 .. t])                     N = 150 (trend), 50 (extension, remainder)
trend_exit(t)     = close(t) < SMA_L(t)                          -> market-on-open sell next session (no buffer, no slope, D-R35)
                    L = 150, or 50 while fewer than 150 closes exist (D-R17)
extension_pct(t)  = (close(t) - SMA_50(t)) / SMA_50(t) * 100     [%]
extension_fire(t) = extension_pct(t) >= exit.extension_threshold_pct[vol_class][regime(t)]
quick_win_fire(t) = regime(t) == bearish AND sessions_since_entry(t) <= exit.quick_win_window_sessions
                    AND (close(t) - avg_entry) / avg_entry * 100 >= exit.quick_win_gain_pct[vol_class]   # 4/5/6/6
remainder_exit(t) = partial_taken AND close(t) < SMA_50(t)       -> sell remainder next session
swing_low(i)      = low(i) < low(j) for all j in [i-5, i-1] and [i+1, i+5]           # strength 5, within 3 months
stop_initial      = buyer_area_ref - exit.stop_offset_atr_multiple * ATR14            # 1.0 x ATR(14)
                    buyer_area_ref = last swing low (standard) | min(last k swing lows) (conservative, k = 2..3)
stop_distance_pct = (entry - stop) / entry * 100
band check        = band_min(vol_class) <= stop_distance_pct   (else move stop lower)
                    stop_distance_pct > band_max(vol_class)    -> keep stop, smaller size (A08)
ratchet           = new_stop >= current_stop                    (else reject)
structure_raise   = new_level = last_swing_low - 1.0 * ATR14; raise if new_level > current_stop (capped by band min from close)   # D-R34
extension EXTREME = 60 / 35 / 18 (bull / sideways / bear)       # D-R31
gain_since_entry  = (close - avg_entry) / avg_entry * 100
```

## 8. Examples / fixtures
- **EX-A07-01 Trend exit fires** — Given SMA150 = 100.00, buffer 0, position ARMED; When the daily close is 99.20;
  Then TREND_EXIT_150 fires and a full sell order is created for the next session.
- **EX-A07-02 Intraday touch, no close below (edge)** — Given SMA150 = 100.00; When intraday low = 98.00 and close = 100.50;
  Then no trigger fires (S13 "second chance" case: price touched the 150-day but never closed materially below).
- **EX-A07-03 Losing position still held (S25, 22 Aug 2026)** — Given a clothing-brand position at -9% from entry with
  close above SMA150 and stop not hit; Then the position stays open and the system suggests no sell; a manual sell by the user would go through but be journaled as a rule deviation (R-A07-037, D-C29).
- **EX-A07-04 2022 tech drawdown (S25/S05)** — Given $50,000 in a tech fund in 2022; When the 150-SMA rule exits about
  6% below the high versus holding to -38%; Then cost $3,000 versus $19,000.
- **EX-A07-05 Pandemic stock $2 -> $75 -> $2 (S23)** — The rule exit about 55% below the top (~$33.75) versus about 95%
  below for holding (~$3.75); used as a teaching fixture of exit vs hold.
- **EX-A07-06 Conservative stop placement (D-R04)** — Given swing lows (5 higher lows on each side) within the last 3 months
  at 44.80 (most recent), 43.50, 42.10 and ATR(14) = 0.90; When mode = conservative (k = 3); Then stop = 42.10 − 0.90 =
  41.20; mode = standard gives 44.80 − 0.90 = 43.90. Both are then checked against the volatility band (R-A07-011).
- **EX-A07-07 Stop too tight is widened, never tightened** — Given entry 50.00, effective class medium (band 10-15%),
  structural stop 47.50 (5.0%); Then stop is moved to <= 45.00 (10%), a [[knocked-out]] warning is shown, and A08 sizing
  at $100,000 / 1% gives an intended 200 shares instead of 400 (before the A08 weight caps); the breakout tranche is 120
  shares (risk $600), 80 reserved for the pullback (A06 R-A06-037).
- **EX-A07-08 Stop too tight for a high-vol stock (S07)** — Given a stock moving 3-4%/day (class high, band 20-25%) and a
  proposed 5% stop; Then validation fails (expected knock-out within 2-3 days) and the stop must be >= 20% below entry.
- **EX-A07-09 Miners (S23, 15 Aug 2026)** — Given gold/silver miners moving ~10% routinely; Then exit about 25% below entry;
  if uncomfortable, reduce size (A08), not the stop.
- **EX-A07-10 S07 chart read (June 2026)** — Entry 25.00, structural stop 21.00 -> distance 16.0%; ATR% ~2%/day
  -> class HIGH (A08 R-A08-009: 2 <= x < 4; 2-3 band HIGH confirmed by D-R11), band 20-25%: 16% < 20% -> [[knocked-out]] warning,
  stop widened to <= 20.00 (20%, next lower buyer area or band minimum; R-A07-011), never tightened. A08 sizing at
  $100,000 / 1%: floor(1,000 / 5.00) = 200 shares intended ($5,000, 5.0%; gap cap 266, position cap 400) instead of 250 at the 16%
  stop; full-size risk stays $1,000 (D-C08). Bought at the breakout: 120 shares ($3,000, risk $600 = 0.6%); 80 reserved
  for a pullback to the ceiling, total risk of both tranches ≤ $1,000 (A06 R-A06-037, D-R44).
- **EX-A07-11 Ratchet rejects lowering (edge)** — Given current_stop 45.00; When a change to 44.00 is submitted; Then it is
  rejected (R-A07-016). A change to 45.00 (equal) is accepted as no-op.
- **EX-A07-12 Raised exit (S23, 15 Aug 2026)** — Given entry 10.00, peak 20.00 (+100%), close 16.50 (+65%), current stop
  9.00, new buyer area supports a stop at 14.00; Then the stop moves to 14.00 (locks +40% if hit); 14.00 >= 9.00 and
  distance from close = 15.2%, which satisfies a medium band minimum of 10%.
- **EX-A07-13 Extension, regime-dependent** — Given class medium, SMA50 = 80.00, close = 100.50 -> extension 25.6%;
  When regime = bull (threshold 25, D-R02); Then PROFIT_EXTENSION fires: sell 50% next session (market-on-open). Given the same class
  with regime = bear (threshold 8) and close 86.60 -> extension 8.25%; Then it fires already at 86.60.
- **EX-A07-14 Extension does not fire (edge)** — Class high, regime bull (threshold 40), SMA50 = 80.00, close = 100.50
  (25.6%) -> no trigger.
- **EX-A07-15 Moderna (S30, 24 Oct 2026)** — Position up +46% after a massive break; Then take half and set the remainder to
  exit below the 50-SMA (S30 "take half off ... or keep an exit a little below the 50-day line").
- **EX-A07-16 Expensify (S30)** — Bought 18 June 2026, rose ~100%, sold at the red line at about +50%; holding would have
  been +85%. Expected: rule exits are accepted even when later price is higher (R-A07-035, R-A07-037).
- **EX-A07-17 Quick win (D-R15)** — Given entry 40.00, class MEDIUM (threshold 5%), window 5 sessions, regime bearish; When
  session 3 closes at 42.00 (+5.0%); Then PROFIT_QUICK_WIN fires (half, market-on-open). Same close with regime bull or
  sideways -> no quick win (only the extension matrix applies). Class HIGH (6%): 42.00 -> no trigger; 42.50 (+6.25%) ->
  fires. When the +5% close happens on session 8; Then no quick-win trigger.
- **EX-A07-18 Remainder exit** — Given partial taken, SMA50 = 95.00, SMA150 = 82.00; When close = 94.10; Then
  REMAINDER_EXIT_50 fires for the remaining quantity; the trend exit is not needed.
- **EX-A07-19 Precedence: stop first** — Given stop 45.00, SMA150 = 46.00; When intraday low 44.50 fills the stop and
  the close is 45.20; Then the position is CLOSED by PROTECTIVE_STOP and the trend-exit trigger is SUPERSEDED (no order).
- **EX-A07-20 Gap through the stop (edge)** — Given equity $100,000, entry 50.00, stop 46.00, the breakout tranche of 79
  shares (60% of the A08-capped 133, EX-A08-01; 54 reserved, not filled), prior close 47.00; When the next open is 41.00;
  Then the stop fills about 41.00: loss 79 x 9.00 = $711 (0.71% of equity, 2.25 R) instead of the planned 79 x 4.00 =
  $316 (0.32%); with both tranches filled near 50.00 the loss would be 133 x 9.00 = $1,197 (1.20%), flag GAP_EVENT, outcome
  LOSS_EXCEEDED_PLAN (A08); the loss stays within the 2% gap budget (A08 R-A08-015); exit rules stay active (R-A07-015).
- **EX-A07-21 RS deterioration is not an exit** — Given the industry turns red at a weekly snapshot; Then new buys are
  blocked immediately and REVIEW_RS is set at the next weekly session (no wait for monthly reviews); given instead the
  industry outside the top RS group at two consecutive monthly reviews, REVIEW_RS and the buy block are set at the second
  one. In both cases no sell order is created; the stop and trend exit remain live (D-C27).
- **EX-A07-22 Covenant: earnings** — Given a trend exit fired two days before earnings; Then the sell order is generated
  for the next session; no "hold through earnings" option exists.
- **EX-A07-23 Mental-exit slide (S23 anti-fixture)** — -8% "sell at break-even", -20% "sell at -8", -35% "sell at -20",
  -70% stops opening the app. Expected system behaviour: exit fixed in advance; every lowering rejected (R-A07-016).
- **EX-A07-24 Broker audit** — 12 positions, 11 with a live stop; Then 1 position listed UNPROTECTED with a fix date.
- **EX-A07-25 New listing (edge, D-R17)** — Instrument with 90 sessions of history; Then flag NO_TREND_HISTORY, the trend
  exit uses the 50-SMA substitute (close below SMA50 -> full sell next session), protective stop required. At session 150
  the 150-SMA takes over and the flag clears. With 40 sessions (no SMA50 yet) only the protective stop protects.
- **EX-A07-26 Buyer-area detection (D-R04)** — Given daily lows over 11 sessions 48.0, 47.5, 47.2, 46.9, 46.5, 46.1,
  46.4, 46.8, 47.0, 47.3, 47.9 (all within 3 months); Then 46.1 is a swing low (5 higher lows on each side) and the
  buyer area; with ATR(14) = 1.10 the structural stop = 46.1 − 1.10 = 45.00. A low with only 4 higher lows to its right
  is not yet a swing low.
- **EX-A07-27 Market-on-open exit with live stop (D-R16)** — Given SMA150 = 60.00, stop 55.00; When the close is 59.40;
  Then a market-on-open sell for the full quantity is queued for the next session, linked one-cancels-other with the broker
  stop at 55.00, which stays live. Next open 58.80 -> the MOO order fills at about 58.80 and the stop is cancelled. Edge:
  next open 54.00 (gap below the stop) -> exactly one of the two orders fills at about 54.00; the other is cancelled and
  its trigger marked SUPERSEDED (R-A07-029, R-A07-040).

- **EX-A07-28 Extension, EXTREME class (D-R31)** — Given class EXTREME and SMA50 = 50.00. Regime bull (threshold 60):
  close 80.00 -> extension 60.0% -> PROFIT_EXTENSION fires (inclusive); close 79.50 (59.0%) -> no trigger. Regime sideways (35):
  close 67.50 -> 35.0% fires. Regime bear (18): close 59.00 -> 18.0% fires; close 58.90 -> 17.8% no trigger.
- **EX-A07-29 Structure raise at the weekly review (D-R34)** — Given current stop 41.20, class MEDIUM (band 10-15%), a new
  swing low 47.60 (5 higher lows on each side, within 3 months) and ATR(14) = 1.20; Then the new level = 47.60 − 1.20 = 46.40
  > 41.20. With close 55.00 the distance is (55.00 − 46.40) / 55.00 = 15.6% ≥ 10% -> stop raised to 46.40. With close 50.00
  the distance would be 7.2% < 10% -> the raise is capped at 50.00 × 0.90 = 45.00 (R-A07-018), still above 41.20. Edge: the
  newest swing low gives 40.90 < 41.20 -> no change (R-A07-016).
- **EX-A07-30 Physical gold exit (D-R39)** — Given 2 one-ounce coins bought after a CONFIRMED gold breakout (A06) at spot
  $4,000, protective-stop level $3,600 (buyer area − 1 × ATR, inside the class band) and equity $100,000 (risk 2 × $400 =
  $800 = 0.8%). No broker stop exists -> flag UNPROTECTED_EXCEPTION, spot alert at $3,600, 150-SMA close alert. When spot
  trades at $3,590, the alert fires and a manual sale task is created for the next session; the dealer buys back at $3,560
  per coin -> loss 2 × $440 = $880 (slippage $40 per coin recorded). The broker audit lists the coins as a sanctioned
  exception, not as UNPROTECTED.

## 9. Variants & open points
Variants not chosen (decision ref):
- Close buffer "materially below" (S13) and a rising-150-SMA condition on the trend exit — not adopted; any close below fires (D-R35).
- Level-based buying and holding of physical gold outside the signal engine (S28) — not adopted; alert-based exit (R-A07-043, D-R39).
- Stop slightly below the 150-SMA itself as the only stop (S13) — replaced by buyer-area stop + independent trend exit (D-X, D-C08).
- Fixed % trailing stop 10% (S25) or 15-20% (S17) — optional variant only (D-C12).
- Breakeven after first rally, profit lock after second (S07); weekly raise for positions up >= 10% (S23) — optional modes (D-C12/C13).
- Salami profit-taking 1/3 at +10/+15/+25% and automated targets (S14) — profile [[prf-beginner-index]], A13 (D-S14).
- Exit on RS loss / monthly re-ranking (S16, S17, S20) — review flag only (D-C27); auto-exit by rank only in [[prf-momentum-rotation]] (A13).
- Break below 50-SMA as warning (S01) — used only for the remainder after a partial (D-C12).
- "Think twice before selling at the bottom" with extreme short positioning (S29) — does not override price exits (D-C26).

Open points: none.
- Closed by D-R35 — OPEN-A07-1 (no close buffer) and OPEN-A07-2 (no slope condition).
- Closed by D-R34 — OPEN-A07-9 (stop raise mode structure).
- Closed by D-R31 — OPEN-A07-10 (EXTREME row 60 / 35 / 18).

Closed by round-2 decisions (2026-10-26): OPEN-A07-3 (D-R16), OPEN-A07-4 (D-R04), OPEN-A07-5 (D-R04), OPEN-A07-6 (D-R15), OPEN-A07-7 (D-R17), OPEN-A07-8 (D-R02).

**Glossary additions (merged into glossary v0.2.0):**
- `remainder-exit` | Remainder Exit | METHOD | After a profit-taking partial, the remaining shares exit on a daily close below the 50-SMA. | S30; D-C12
- `unprotected-position` | Unprotected Position | METHOD | Open position without a live broker stop for its full quantity; a rule violation found by the broker audit. | S23

## 10. Traceability
| Rule/Concept | Sources |
|---|---|
| R-A07-001..002 exit before buy, same sitting | S13, S23, S25, S05, S07, S08, S22, S30; D-X |
| R-A07-003..005 live stop, alert, stop semantics | S23, S25, S05 |
| R-A07-006..009 trend exit | S13, S23, S25, S05, S17, S20; D-C05, D-C26, D-OPEN-2 |
| R-A07-010..015 protective stop, volatility validation, gaps | S07, S13, S23, S25, S30, S14; D-C08, D-X |
| R-A07-016..021 ratchet, raise modes, cadence | S13, S14, S23, S25, S07, S17; D-C12, D-C13, D-C04, D-C28 |
| R-A07-022..028 profit-taking | S30, S23, S13; D-C12, D-OPEN-4 |
| R-A07-029..034 precedence, review flags | S20, S16, S30, S23, S07, S25; D-C26, D-C27 |
| R-A07-035..039 covenants, discipline | S23, S05, S20, S21, S14, S13, S25; D-C29 |
| R-A07-040..042 MOO exits, insider review flag, buyer-area detection | S23, S25; D-R04, D-R16, D-R25 |
| R-A07-043 physical holdings: alert-based exit exception | S28; D-R39 |
| R-A07-008, R-A07-017, R-A07-022 no buffer/slope, structure raise, EXTREME row | S13, S23; D-R31, D-R34, D-R35 |
| ExitPlan lifecycle | S23, S13, S07; D-C26 |
| Fixtures | S05, S07, S13, S23, S25, S30 |
