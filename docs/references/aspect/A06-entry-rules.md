---
id: A06
title: Entry Rules
context: CTX-C
layers: [CORE, METHOD]
status: draft
sources: [S01, S02, S03, S05, S07, S08, S13, S15, S16, S17, S22, S23, S25, S28, S30]
decisions: [D-H, D-X, D-C01, D-C02, D-C03, D-C04, D-C05, D-C06, D-C07, D-C08, D-C09, D-C11, D-C15, D-C17, D-C23, D-C26, D-C27, D-C28, D-OPEN-2, D-R01, D-R03, D-R05, D-R07, D-R08, D-R11, D-R14, D-R17, D-R18, D-R25, D-R39, D-R40, D-R44]
depends_on: [A01, A02, A04, A05, A07, A08, A09, A12]
---
# A06 — Entry Rules

## 1. Purpose & scope
Defines when a selected candidate (A05) may be bought and how the buy is placed: the entry conditions (D-C06/D-C07),
the [[entry-checklist]] ("Power Moves" is only an informal synonym, D-C17), the watchlist lifecycle, the
[[technical-setup]] record, order placement with the exit set in the same sitting, and the blocking rules
(never below the 150-SMA, red industry blocks buys, concentration and RS-deterioration blocks).

Excludes: industry status/ranking (A02), volume and base detection (A04), selection and survival gate (A05),
stop level and exit logic (A07), share count and risk budget (A08), concentration limits (A09), routines (A12).
Pure momentum rotation (S16/S17) is a separate profile (A13, D-C07) and does not use these entry rules.

## 2. Concepts
- [[entry-checklist]] — the all-must-pass gate before any buy (D-C06, D-C17).
- [[heartbeat-breakout]] — first-class signal HeartbeatBreakout (A04 Breakout CONFIRMED).
- [[rising-50-sma]] / [[yellow-line]] — first-class signal Rising50SMA; the entry trend line (D-C05).
- [[purple-line]] — 150-SMA; entry is never allowed below it (covenant 1).
- [[ma-slope]], [[simple-moving-average]] — "rising" per D-OPEN-2 (owned by A02).
- [[volume-spike]], [[breakout-volume]] — volume confirmation (D-C01, owned by A04).
- [[record-quarter]] — optional confirmation (D-C03); [[triple-confirmation]] — highest grade when all align.
- [[scoreboard-green]], [[scoreboard-red]], [[top-rs-group]], [[rs-deterioration]] — industry gates (D-C06, D-C27).
- [[survival-check]] — mandatory veto for single stocks (A05, D-C03).
- [[concentration-limit]] — breach blocks buys in that bucket (A09, D-C11).
- [[breakout]], [[weak-breakout]], [[false-breakout]], [[breakout-setup]] — breakout states.
- [[close-confirmed-entry]] — default order mode: buy in the next session after a qualifying close (D-R03).
- [[setup-distance]], [[no-chase-threshold]], [[earnings-blackout]] — class-scaled entry thresholds (D-R07, D-R08, D-R11; class basis A08 R-A08-032).
- [[smart-money-evidence]] — may raise watchlist priority; never an entry condition (D-R25).
- [[breakout-buy-order]], [[buy-stop-order]], [[limit-order]], [[market-order]], [[market-on-open-order]], [[order]] — order mechanics; the resting buy-stop is a non-canonical variant (D-R03).
- [[second-chance-entry]] — optional add on pullback to the breakout level.
- [[exit-plan]], [[protective-stop]], [[buyer-area]], [[stop-loss-order]], [[price-alert]] — exit placed in the same sitting (A07).
- [[risk-per-position]], [[risk-based-position-sizing]], [[overnight-gap-test]] — size computed before the order (A08).
- [[watchlist]] — holds candidates through the lifecycle below.
- [[wait-for-confirmation]], [[timing-the-market]], [[falling-knife]], [[averaging-down]], [[ipo-trap]], [[selling-the-book]] — prohibitions.
- [[weekly-review]], [[daily-automation]] — cadence: decisions weekly, fills/alerts daily (D-C04).
- [[three-covenants]] — "never buy below the line" is covenant 1.

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| TechnicalSetup | id, instrumentId, asOf | date | separate from ResearchReport | D-C23 |
| | baseId, baseTier, ceiling, floor | ref, price | from A04 HeartbeatBase | |
| | sma50, sma50Slope, sma150, sma150Slope | price, enum UP/FLAT/DOWN | D-OPEN-2 | |
| | close, distanceToCeilingPct | price, % | — | |
| | lastBreakout {date, class, volumeMultiple} | ref | A04 Breakout | |
| | nextEarningsDate | date | optional | R-A06-019 |
| | thresholdVolClass | enum LOW/MEDIUM/HIGH/EXTREME | A08 R-A08-032 | stock: own class; fund/basket: industry-proxy class |
| | sessionsOfHistory | int | — | < 150 → C4 N_A (D-R17) |
| Watchlist | id, ownerId, name, reviewDay | — | one default per user | A12 review day (D-C28) |
| WatchlistEntry | id, watchlistId, instrumentId, industryId, candidateId (A05), state, stateSince, setupId | — | lifecycle below | |
| | plannedBreakoutBuyPrice, plannedStopPrice, plannedShares, plannedRiskPct, breakoutTrancheShares, reservedSecondChanceShares | price, shares, % | computed in ARMED; tranche split per R-A06-037 | A07/A08; D-R44 |
| | blockReasons[] | enum | non-empty iff BLOCKED | |
| | warnings[] | enum {GLOBAL_RED, CONCENTRATION_CREATED, FADING_VOLUME, …} | never block | D-R14, D-R18, D-R44 |
| | priority, smartMoneyEvidenceRefs[] | int, ref A04 `SmartMoneyEvidence` | evidence may raise priority only | D-R25 |
| EntryChecklist | id, watchlistEntryId, evaluatedAt, mode (WEEKLY_REVIEW, DAILY_FILL_CHECK) | — | immutable after evaluation | stored with each order |
| | checks[] {checkId, result PASS/FAIL/N_A, value, evidenceRef} | — | all hard checks PASS to allow order | R-A06-001 |
| | confirmations {volumeGrade, recordQuarterGrade, tripleConfirmation} | — | informational | D-C03, D-C17 |
| | verdict | enum ALLOW, BLOCK | — | |
| Signal | type (HeartbeatBreakout, Rising50SMA, VolumeSpike, RecordQuarter), instrumentId, date, payload | — | first-class (D-C17) | produced by A04/A05/A06 |
| Order | id, instrumentId, side BUY, type (LIMIT_ON_OPEN, MARKET_ON_OPEN, LIMIT, BUY_STOP, BUY_STOP_LIMIT), triggerPrice, limitPrice, shares, timeInForce, status, linkedExitOrderIds[], entryChecklistId, placedAt | — | BUY requires linked exit (R-A06-024); default LIMIT_ON_OPEN at the no-chase level (R-A06-030) | A01 order types |
| StopOrder | id, positionId/orderId, stopPrice, placedAt | — | owned by A07 | must exist in same sitting |
| ExitPlan | id, instrumentId, trendExit, protectiveStop, profitRules, writtenAt | — | writtenAt <= buy placedAt | A07 |
| Position | id, instrumentId, entryDate, entryPrice, shares, entryChecklistId, tranche (BREAKOUT, SECOND_CHANCE), entryQuality (CONFIRMED, UNCONFIRMED) | — | created on fill | A09 owns portfolio |

WatchlistEntry lifecycle (state):
```
CANDIDATE   selected by A05; industry eligible; survival PASS (or N_A for funds)
  -> BASING    A04 base FORMING (tier SHORT) or no base yet
  -> SETUP     base QUALIFIED, close below ceiling, sma50 rising, close >= sma150      ([[breakout-setup]])
  -> ARMED     entry pre-authorised in a weekly review: close-confirmed trigger (default) or variant buy-stop, linked exit, size (R-A06-022..027, R-A06-030)
  -> TRIGGERED buy filled -> Position created (entry quality per R-A06-029)
any non-terminal -> BLOCKED   a block reason holds (R-A06-008..013); orders of ARMED entries cancelled
BLOCKED -> previous state when all block reasons cleared at a review
any -> REMOVED  base BROKEN_DOWN, industry no longer selected, or user removal
TRIGGERED, REMOVED = terminal for the entry; a new base creates a new entry
```

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `entry.trend_ma_length_days` | 50 | fixed 50 (param) | sessions | D-C05 |
| `entry.ma_type` | SMA | {SMA} | — | S13, S25 "Simple, not exponential." |
| `entry.min_breakout_volume_multiple` | = A04 `volume.breakout_min_multiple` (2.0) | >= 2.0 | x avg | D-C01 |
| `entry.min_base_months` | = A04 `volume.base_min_months` (3) | >= 3 | months | D-C02 |
| `entry.require_record_quarter` | false | bool | — | D-C03, D-C17 |
| `entry.require_survival_check` | true | true | — | D-C03 |
| `entry.order_mode` | CLOSE_CONFIRMED | {CLOSE_CONFIRMED, RESTING_BUY_STOP (variant, non-canonical)} | — | D-R03; S07, S30 |
| `entry.buy_stop_offset_pct` | — (not used in the default mode) | > 0 | % above ceiling | D-R03; variant mode only (S07 example 2.5%) |
| `entry.setup_max_distance_pct[low/medium/high/extreme]` | 3 / 5 / 8 / 12 | > 0 | % below ceiling (close) | D-R07, D-R11 |
| `entry.max_chase_pct[low/medium/high/extreme]` | 3 / 5 / 8 / 12 | > 0 | % next-session open above ceiling | D-R07, D-R11 |
| `entry.earnings_blackout_sessions[low/medium/high/extreme]` | 2 / 5 / 10 / 10 | >= 0 | sessions before scheduled earnings | D-R08, D-R11; S30 example 2 days |
| `entry.gating_view` | = A02 `scoreboard.gating_view` (local) | — | — | D-R18 |
| `entry.second_chance_enabled` | true | bool (user MAY disable) | — | S13, S07; D-R44 (default entry behaviour) |
| `entry.breakout_tranche_pct` | 60 (100 only if the user disables `entry.second_chance_enabled` or a profile overrides it) | 1–100 | % of intended position | D-R44 (S13 template blank) |
| `entry.second_chance_tranche_pct` | 40 (= 100 − breakout tranche) | 0–99 | % of intended position, reserved for the pullback to the ceiling | D-R44 |

Referenced, owned elsewhere: first-live-trades minimum size = A08 `sizing.initial_live_risk_pct` and `sizing.initial_live_trades_count` (R-A08-007); threshold class basis A08 `risk.vol_class_threshold_basis` (R-A08-032).

## 5. Rules
Where to look vs when to buy (D-C06, D-C07)
- **R-A06-001** (hard, METHOD) — A buy order MUST NOT be placed unless an EntryChecklist evaluated in the same sitting has verdict ALLOW, i.e. every hard check of R-A06-002..013 passes. _Sources: S07 "Reference it before every investment decision.", S13, S25. Decision: D-C06, D-C17_
- **R-A06-002** (hard, METHOD) — Check C1 industry: the instrument's industry is GREEN in the local view and in the top RS group (A02); a RED status in the global view adds warning GLOBAL_RED but does not fail C1. Ranking only determines where to look; it is never sufficient for a buy. _Sources: S13, S25, S05. Decision: D-C06, D-C15, D-R18_
- **R-A06-003** (hard, METHOD) — Check C2 heartbeat breakout: a HeartbeatBreakout signal exists, i.e. a daily close above the ceiling of a base of >= 3 months with breakout volume >= 2x the 50-day average (A04 R-A04-022). _Sources: S13, S30, S07, S05, S17. Decision: D-H, D-C01, D-C02, D-C06_
- **R-A06-004** (hard, METHOD) — Check C3 trend: close > SMA50 AND SMA50 slope = UP (Rising50SMA, "rising" per D-OPEN-2); a FLAT or DOWN slope fails. _Sources: S13 "No buying while the 50-day line is sloping down.", S25 "Above it and sloping up, or you are not buying." Decision: D-C05, D-C06, D-OPEN-2_
- **R-A06-005** (hard, METHOD) — C2 and C3 MUST hold on the same chart at the same evaluation ("One out of two is not the rule."). _Sources: S13_
- **R-A06-006** (hard, METHOD) — Check C4 covenant 1: the last daily close MUST be >= SMA150; if price is below or only a fraction below, a buy is allowed only after a daily close above it. For an instrument with fewer than 150 sessions of history C4 is N_A (D-R17). _Sources: S23 "Never buy below the line" / "he would buy it only if it closed above." Decision: D-C06, D-R17_
- **R-A06-007** (hard, METHOD) — Check C5 survival: for a single stock (and each custom-basket member) the A05 survival check is PASS for the latest fiscal period; for fund baskets N_A. _Sources: S13, S30. Decision: D-C03_
- **R-A06-008** (hard, METHOD) — Check C6 red block: if the industry is RED, no buy order may be placed and any resting buy order for that industry MUST be cancelled at the next review. _Sources: S13 "Nothing on the red side is cheap", S25 "Red means stay away." Decision: D-C06, D-C15_
- **R-A06-009** (hard, METHOD) — Check C7 RS deterioration: an industry with an active deterioration flag blocks new buys. Per D-C27 the block applies immediately when the industry is red (see also C6) and after 2 consecutive monthly reviews outside the top RS group. _Decision: D-C27_
- **R-A06-010** (hard, METHOD) — Check C8 concentration: if the bucket (industry/sector or company, look-through, A09) is already breached, the buy is blocked (D-C11). If the buy would only create a breach, C8 passes with warning CONCENTRATION_CREATED and the suggested maximum (A09 R-A09-012). _Decision: D-C11, D-R14_
- **R-A06-011** (hard, METHOD) — Check C9 exit and size: a written ExitPlan (A07) with a protective stop level exists and the A08 size gives risk <= the risk budget and passes the overnight-gap weight cap; otherwise blocked. _Sources: S23, S25, S07 "Is your total risk on this position <= 1%". Decision: D-C08, D-C09_
- **R-A06-012** (hard, METHOD) — Check C10 falling knife: an instrument with SMA50 or SMA150 sloping DOWN together with a SellingSpike in the last review period is blocked. _Sources: S07 "stocks with institutional selling and downward-sloping moving averages", S30_
- **R-A06-013** (hard, METHOD) — Check C11 data: insufficient history for the SMA50 and its slope test, the 50-day volume average or a qualifying base of >= 3 months blocks the buy ([[ipo-trap]]: no day-one IPO buys). Fewer than 150 sessions does not block (C4 N_A, A07 50-SMA substitute trend exit). _Sources: S03 "Do NOT plan to buy any IPO on day one". Decision: D-C02, D-R17_
- **R-A06-014** (soft, METHOD) — RecordQuarter, VolumeSpike strength and triple confirmation are recorded as confirmations and MAY raise watchlist priority; they MUST NOT be required unless `entry.require_record_quarter` = true. _Sources: S07, S03. Decision: D-C03, D-C17_
- **R-A06-015** (hard, METHOD) — The informal name "Power Moves" MAY be displayed only as a label for the EntryChecklist; differing source lists (S01, S03, S07) MUST NOT define separate checklists. _Decision: D-C17_

Prohibitions
- **R-A06-016** (hard, METHOD) — No buy because something is in the news, on a story, or on valuation alone; only the checklist decides. _Sources: S25 "by then I am the exit", S22 "because the chart confirms the story", S30. Decision: D-C06_
- **R-A06-017** (hard, METHOD) — Never chase: if the next-session open is more than `entry.max_chase_pct[class]` (LOW 3, MEDIUM 5, HIGH 8, EXTREME 12%) above the ceiling, the entry is not filled; the instrument waits for a second-chance pullback or the next base. _Sources: S13 "I never chase. If it has already run, I wait for the next base". Decision: D-R07, D-R11_
- **R-A06-018** (hard, CORE) — No averaging down: no additional buy of an open position below its average entry price, and no buy into an unconfirmed base. Exception: the pre-written pullback tranche of the entry plan (second-chance add, R-A06-031) allowed by A08 R-A08-024, which still keeps total position risk <= `sizing.risk_pct` against the current stop. _Sources: S30 "I do not buy more of a loser.", "he waits for the confirmed break", S13, S07. Decision: D-C09_
- **R-A06-019** (hard, METHOD) — [[earnings-blackout]]: no new buy may be armed or filled within `entry.earnings_blackout_sessions[class]` (LOW 2, MEDIUM 5, HIGH 10, EXTREME 10) sessions before a scheduled earnings date; the entry stays SETUP. Buying after the report is allowed. _Sources: S30 ("Watch list. Risky before earnings."). Decision: D-R08, D-R11_
- **R-A06-020** (hard, METHOD) — A WEAK or FALSE breakout (A04) never satisfies C2; the entry remains SETUP. _Sources: S30 "A break on no volume is a warning.", S07. Decision: D-C01_
- **R-A06-021** (hard, METHOD) — A StaircaseUptrend never satisfies C2. _Sources: S03. Decision: D-H_

Order placement and same-sitting exit
- **R-A06-022** (hard, METHOD) — Entry decisions and order placement happen in the weekly review on a market-closed day; between reviews only automated fills, alerts, the next-session orders of entries pre-authorised as close-confirmed triggers (R-A06-030) and the post-fill checks of R-A06-029 run. _Sources: S13, S25, S07, S05. Decision: D-C04, D-C28_
- **R-A06-023** (soft, METHOD) — The default order mode is `CLOSE_CONFIRMED` (R-A06-030). A resting breakout buy-stop at ceiling × (1 + `entry.buy_stop_offset_pct`) is a non-canonical variant (`RESTING_BUY_STOP`) that the user MAY enable; the offset is not used in the default mode. _Sources: S07 "breakout buy prices — the price ABOVE resistance", S05 "We don't buy at the breakout. We buy slightly above it." Decision: D-R03_
- **R-A06-024** (hard, METHOD) — Every buy order MUST be submitted in the same sitting together with its exit: a linked protective stop order (level per A07 buyer-area rule, D-C08) contingent on the fill, plus the 150-SMA close alert (A07). A buy without a linked exit MUST be rejected by the app. _Sources: S23 "The sell order goes in during the same sitting as the buy order", S13, S07 "Always place your buy order and your stop-loss order at the same time.", S30. Decision: D-X, D-C08, D-C26_
- **R-A06-025** (hard, METHOD) — The exit level MUST be written (ExitPlan.writtenAt) before the buy order is placed. _Sources: S23 "He writes down his sell point before he ever buys a stock", S25, S22_
- **R-A06-026** (hard, METHOD) — Shares MUST be computed by A08 from entry trigger price and protective stop (shares = equity × risk% / (entry − stop)) and capped by the overnight-gap test; a stop that seems too wide reduces shares, never tightens the stop. _Sources: S15, S23, S30. Decision: D-C08, D-C09_
- **R-A06-027** (soft, CORE) — Orders SHOULD use broker order types that cannot fill far above the planned price where available (buy-stop-limit); with a plain buy-stop the app warns that gaps can fill above the trigger. _Sources: S23 (stop becomes market order, no price guarantee), S25. Cross-ref: A01_
- **R-A06-028** (hard, METHOD) — At each review, ARMED orders MUST be re-validated against R-A06-002..013; failing entries become BLOCKED and their buy orders cancelled. _Sources: S13, S25. Decision: D-C06, D-C27_
- **R-A06-029** (hard, METHOD) — After a fill, the app evaluates the fill session at its close (DAILY_FILL_CHECK): if close > ceiling and VM >= 2, entryQuality = CONFIRMED; otherwise UNCONFIRMED, which raises a review flag. The protective stop and price-based exits (A07) remain the only automatic exits. _Sources: S07, S30. Decision: D-C01, D-C26, D-C27_
- **R-A06-030** (hard, METHOD) — [[close-confirmed-entry]] (default): no resting buy-stop is used. An entry ARMED in a weekly review becomes an order only when a daily close above the ceiling on >= 2x volume (CONFIRMED breakout, A04) occurs; the checklist is then evaluated on that close (mode DAILY_FILL_CHECK) and a next-session limit-on-open order with limit = ceiling × (1 + `entry.max_chase_pct[class]`/100) is placed with its linked exit, so an open beyond the no-chase threshold does not fill (R-A06-017). _Sources: S07 "closes above the upper boundary", S30. Decision: D-R03, D-R07_

Second chance and tranches
- **R-A06-031** (soft, METHOD) — If `entry.second_chance_enabled` (default true), a second tranche MAY be bought when price pulls back to the breakout level (old ceiling) and holds above the protective stop, provided all checklist items still pass; total risk of both tranches stays within the A08 budget. The split is `entry.breakout_tranche_pct` (60%) at the breakout and `entry.second_chance_tranche_pct` (40%) reserved for the pullback (R-A06-037). _Sources: S13 "The old ceiling becomes the floor.", S07 "first buy on breakout, second buy on pullback to support". Decision: D-C09, D-R44_
- **R-A06-032** (soft, METHOD) — A pullback to the breakout level is labelled "second chance — normal", not as system failure; it creates no sell action by itself. _Sources: S13 "That is the plan working, not failing.", S15_
- **R-A06-033** (soft, METHOD) — While learning, the first A08 `sizing.initial_live_trades_count` live entries are sized with A08 `sizing.initial_live_risk_pct` (A08 R-A08-007, A12 R-A12-042). _Sources: S07 "Deploy real capital using the SMALLEST position size in your model"_

Round-2 additions (2026-10-26)
- **R-A06-034** (hard, METHOD) — [[setup-distance]]: a QUALIFIED base advances to SETUP only while the last close is below the ceiling by at most `entry.setup_max_distance_pct[class]` (LOW 3, MEDIUM 5, HIGH 8, EXTREME 12%); farther below it stays BASING. _Sources: S30 (OKE ~2%), S22 (RGTI 7%). Decision: D-R07, D-R11_
- **R-A06-035** (soft, METHOD) — [[smart-money-evidence]] (A04) on the instrument or its industry MAY raise the WatchlistEntry priority (strong insider or institutional buying); it MUST NOT satisfy, replace or override any checklist item and never creates an order. _Decision: D-R25, D-R22, D-C06_
- **R-A06-036** (hard, METHOD) — The class used for every class-scaled entry threshold (setup distance, no-chase, earnings blackout) is the threshold class of A08 R-A08-032: the stock's own class, or the industry-proxy class for a fund or basket. _Decision: D-R05_

Round-3 additions (2026-10-26)
- **R-A06-037** (hard, METHOD) — Under the canonical profile every entry is split (default entry behaviour; `entry.second_chance_enabled` defaults to true): the intended position (A08 final size for the full risk budget) is divided into: breakout tranche = floor(`entry.breakout_tranche_pct` (60%) × intended shares), reserved second-chance tranche = the remainder (40%), bought only on a pullback to the old ceiling per R-A06-031. Both tranches together MUST stay within the same `sizing.risk_pct` budget measured against the current stop (A08 R-A08-024); the reserved tranche is the pre-written pullback tranche that R-A06-018 allows. If the pullback never comes, the position stays at the breakout tranche. Whole-share or fractional rounding follows A08 R-A08-035. Profiles MAY override the split (A13: beginner lots, momentum rotation 100% at rebalance). _Decision: D-R44, D-R40, D-C09_
- **R-A06-038** (soft, METHOD) — A FadingVolumeRally pattern (A04) on a SETUP entry adds warning FADING_VOLUME to the WatchlistEntry and checklist; it MUST NOT block arming. The CONFIRMED breakout (≥ 2× volume, C2) is still required for any buy. _Decision: D-R44, D-C01_

## 6. Processes
**PR-A06-01 Weekly entry pass** — trigger: weekly review (default Saturday, D-C28) after A02 scoreboard and A05 selection. Inputs: A05 candidates, A04 bases/breakouts/volume, MAs, A07 exit levels, A08 sizing, A09 exposure.
1. Update every WatchlistEntry: refresh TechnicalSetup (base tier, ceiling, MAs, distance).
2. Apply block checks C1, C6–C8, C10–C11; move to BLOCKED (cancel ARMED orders) or clear blocks (R-A06-008..013, R-A06-028).
3. Advance states: BASING → SETUP when base QUALIFIED, SMA50 rising, close >= SMA150 (N_A below 150 sessions) and within `entry.setup_max_distance_pct[class]` of the ceiling (R-A06-034); apply the earnings blackout (R-A06-019); attach smart-money evidence as priority (R-A06-035).
4. For SETUP entries the user chooses to arm: write ExitPlan (A07) → compute stop and shares (A08) → evaluate EntryChecklist (C1–C11 with the breakout planned) → pre-authorise the close-confirmed trigger (R-A06-030; variant: place a buy-stop, R-A06-023) with linked stop (R-A06-024) → state ARMED.
5. For entries whose CONFIRMED breakout happened since the last review without an armed trigger: evaluate the checklist and place a next-session limit-on-open order at the no-chase level (R-A06-017, R-A06-030).
6. Record checklists and decisions in the ReviewLog (A12).
Output: orders, updated states. Cadence weekly.

**PR-A06-02 Daily fill handling (automated)** — trigger: broker fill event / daily close (D-C04).
0. On a daily close that confirms the breakout of an ARMED entry (close > ceiling, VM >= 2): re-run the hard checks on that close and place the next-session limit-on-open order with its linked exit (R-A06-030).
1. On fill: create Position (tranche), activate the linked protective stop, confirm the 150-SMA alert exists.
2. At the fill session's close: run DAILY_FILL_CHECK (R-A06-029); flag UNCONFIRMED entries for the next review.
3. No discretionary buys between reviews.

**PR-A06-03 Second-chance add (optional)** — trigger: alert "price returns to breakout level" on a TRIGGERED position. Steps: at the next review re-run checklist; size the add within total budget; place order + update linked stop for the combined position (R-A06-031).

## 7. Calculations
```
rising(SMA50)        = slope_state(SMA50, D-OPEN-2) == UP           # N=20 sessions, flat band 0.025 %/session (D-R01), owned by A02
C2_breakout          = A04.Breakout.class == CONFIRMED AND base.baseMonths >= 3 AND VM >= 2.0
C3_trend             = close > SMA50 AND rising(SMA50)
C4_not_below_150     = close_last >= SMA150                          # N_A if sessions_of_history < 150 (D-R17)
entryLimit           = ceiling * (1 + max_chase_pct[class]/100)      # next-session limit-on-open (D-R03, D-R07)
buyStopTrigger       = ceiling * (1 + buy_stop_offset_pct/100)      # variant RESTING_BUY_STOP only
distanceToCeilingPct = (ceiling - close) / ceiling * 100
chasePct             = (open_next - ceiling) / ceiling * 100         # no fill if > max_chase_pct[class]
setup                = 0 <= distanceToCeilingPct <= setup_max_distance_pct[class]
blackout             = sessions_until_earnings <= earnings_blackout_sessions[class]
stopDistancePct      = (entry - stop) / entry * 100                  # A07 stop, A08 sizing
riskPct              = weightPct * stopDistancePct / 100              # must be <= A08 risk budget
checklist.verdict    = ALLOW iff all hard checks C1..C11 in {PASS, N_A}
```

## 8. Examples / fixtures
**EX-A06-01 Full pass (S07, June 2026 chart read)** — Given heartbeat ~8 months (PREFERRED), ceiling $24.00, close $24.80 (first close above), volume "400% spike" = 5.0x, SMA50 rising, close > SMA150, industry GREEN (local)/top RS, survival PASS, equity $100,000, risk 1%, next-session limit-on-open (limit 24.00 × 1.08 = $25.92 for class HIGH) filled at the open $25.00 (4.17% above the ceiling ≤ 8%, no chase), structural stop $21.00 (16.0%). The stock's ATR% is ~2%/day → class HIGH (A08 R-A08-009), band 20–25%: A07 widens the stop to $20.00 (20%, R-A07-011, D-C08; never tighter). When the checklist runs. Then C1–C11 PASS → ALLOW; A08 intended size = floor(100,000 × 1% / (25 − 20)) = 200 shares = $5,000 (5.0% ≤ 6.67% gap cap, ≤ 10% position cap), full-size risk $1,000 = 1.0%. Breakout tranche (R-A06-037) = floor(0.60 × 200) = 120 shares = $3,000 (3.0%), risk 120 × 5.00 = $600 = 0.6%; 80 shares reserved for a pullback to the ceiling $24.00 (adding 80 × 4.00 = $320 → total $920 ≤ $1,000, EX-A06-17). Order placed for 120 shares with linked stop $20.00 (EX-A07-10, EX-A08-04).
- Source context only: S07 sized the trade at "about 3% of portfolio" with the $21.00 stop (risk 3% × 16% = 0.48%); that figure is not the A08 sizing.

**EX-A06-02 Pay-more breakout buy (S07; variant RESTING_BUY_STOP, non-canonical, D-R03)** — Given price $16, resistance $20. When armed in the variant mode with a 2.5% offset (example value). Then buy-stop trigger = $20.50 (= 20 × 1.025); no fill unless price trades >= $20.50. In the default mode no buy-stop is placed.

**EX-A06-03 One out of two (S13, 8 Aug 2026 session)** — Given a CONFIRMED breakout while SMA50 still slopes DOWN. Then C3 FAIL → BLOCK. Given SMA50 rising but no breakout yet → state SETUP (or ARMED as a close-confirmed trigger), no order.

**EX-A06-04 Covenant 1 (S23, 15 Aug 2026)** — Given SMA150 = 50.00 and last close 49.80 (a fraction below) with a fresh breakout signal. Then C4 FAIL; after a later daily close of 50.40 (>= SMA150) C4 PASS.
- Edge: close exactly 50.00 = SMA150 → PASS (>=).

**EX-A06-05 S30 grading table (24 Oct 2026) mapped to states**
| Case | Facts | Expected |
|---|---|---|
| EOG | break on ~1.5x | C2 FAIL (WEAK) → stays SETUP (D-C01 overrides source "broke out") |
| KDP | broad heartbeat, break, cash check passed, volume multiple not stated | C2 undetermined → requires VM >= 2 on break day; survival PASS |
| eBay | volume "popped a little" | SETUP (WEAK) |
| ECL | big but fading volume, no close above | SETUP |
| OKE | break line ~2% above price | SETUP (distance 2% ≤ 3% even for class LOW, R-A06-034) |
| Real-estate services | at break point, no volume, earnings in 2 sessions | SETUP, not ARMED: inside the blackout for every class (2 ≤ 2/5/10/10, R-A06-019) |
| TEAM 2nd break | ~1x volume | WEAK → no buy |
| Gold | ~1-month base, breakdown, SMA50 falling | REMOVED (base BROKEN_DOWN; C3 FAIL) |

**EX-A06-06 Red industry blocks (S25, 22 Aug 2026)** — Given an ARMED buy-stop on a software stock and the scoreboard turning software RED at the weekly review. Then state BLOCKED, buy order cancelled (R-A06-008/028); no buy even if the breakout fires later in the week.

**EX-A06-07 Wait for confirmation (S22, 14 Aug 2026)** — Given RGTI trigger $20 (ideal push to $27), price $18.60. Then not triggered: distance to trigger = (20 − 18.60)/20 = 7.0%; no position ("not broken → don't own"). The 7.0% distance qualifies as SETUP only for class HIGH (≤ 8%) or EXTREME (≤ 12%); for MEDIUM (5%) the entry stays BASING (R-A06-034). Edge: no RGTI checklist can pass while its industry lacks local GREEN status, regardless of the trigger.

**EX-A06-08 Pullback mode (S08, 6 Jul 2026)** — Given 50 gold/silver miners, 0 qualifying setups, group 20–62% below highs. Then no ARMED entries; "do not buy the dip, do not chase the bounce" (R-A06-016/017).

**EX-A06-09 No same-sitting exit (edge)** — Given a user tries to submit a buy-stop without a linked stop order. Then the app rejects the order (R-A06-024); the entry stays SETUP.

**EX-A06-10 Gap fill and post-fill check (synthetic; variant RESTING_BUY_STOP)** — Given ARMED buy-stop $20.50 (ceiling $20.00), stock gaps to open $21.40, closes $20.30 on VM 1.4. Then fill at ~$21.40 (above plan, warning per R-A06-027); DAILY_FILL_CHECK: close > ceiling but VM < 2 → entryQuality UNCONFIRMED, review flag; no automatic sale; protective stop active (R-A06-029).

**EX-A06-11 Concentration warning vs block (synthetic, D-C11 defaults, D-R14)** — Given semiconductor look-through exposure 23% (including funds) and a planned semiconductor buy of 4% weight. Then post-trade exposure 27% > 25% → C8 PASS with warning CONCENTRATION_CREATED (suggested maximum 2%); the buy is allowed. Edge: current exposure 25.5% (already breached) → C8 FAIL, BLOCKED (D-C11).

**EX-A06-12 Second chance (S13, 8 Aug 2026)** — Given bought the break, up ~10%, pulled back to the entry/breakout level, touched the 150-SMA without a close materially below it. Then position held (A07); if `entry.second_chance_enabled` and checklist passes, an add is allowed within total risk budget (R-A06-031/032).

**EX-A06-13 No-chase by class (synthetic, D-R07)** — Given ceiling $50.00, class MEDIUM (5%), a CONFIRMED close at $50.90 and a next-session limit-on-open at $52.50. When the next open is $52.40 (+4.8%) → filled. When the next open is $52.60 (+5.2%) → not filled; the entry waits for a second-chance pullback (R-A06-017). Class LOW (3%): limit $51.50, so both opens miss.

**EX-A06-14 Setup distance by class (synthetic, D-R07)** — Given ceiling $50.00 and close $47.60 (4.8% below). Then class MEDIUM (5%) → SETUP; class LOW (3%) → stays BASING; class EXTREME (12%) → SETUP.

**EX-A06-15 Young listing (synthetic, D-R17)** — Given a stock listed 120 sessions ago with a QUALIFIED 3.5-month base, a CONFIRMED breakout and a rising SMA50. Then C4 is N_A (no SMA150 yet), C11 PASS; the entry may proceed; A07 uses the 50-SMA substitute trend exit until 150 sessions exist. With a 2.5-month base → C2 FAIL (base < 3 months).

**EX-A06-16 Global red is a warning (D-R18)** — Given the industry GREEN and in the top RS group in the local view but RED in the global view. Then C1 PASS with warning GLOBAL_RED shown on the checklist; local NEUTRAL with global GREEN → C1 FAIL.

**EX-A06-17 Tranche split 60/40 (R-A06-037; D-R44)** — Given the EX-A06-01 plan (equity $100,000, risk 1%, entry $25.00, stop $20.00 → intended 200 shares) with `entry.second_chance_enabled` = true (default). Then the breakout tranche = floor(0.60 × 200) = 120 shares at $25.00 (risk 120 × 5.00 = $600 = 0.60%) and 80 shares are reserved. When price pulls back to the old ceiling $24.00 and holds above the stop: 80 shares at $24.00 add risk 80 × 4.00 = $320; total risk vs the $20.00 stop = $920 = 0.92% ≤ 1.0%; position 200 shares, average entry (120 × 25.00 + 80 × 24.00) / 200 = $24.60, value $4,920 (4.92%). The add below the first entry is allowed because it is the pre-written pullback tranche (R-A06-018, A08 R-A08-024). Edge: 201 intended shares → breakout floor(120.6) = 120, reserved 81.

**EX-A06-18 Fading volume on a SETUP (R-A06-038; D-R44)** — Given a SETUP whose last 5 sessions averaged 0.5× and the first 5 sessions of the 20-session window 1.0× the 50-day volume (fadingRatio 0.5 ≤ 0.6, A04). Then warning FADING_VOLUME is shown and the entry may still be ARMED. A later close above the ceiling on 1.8× volume is WEAK → no buy (C2 FAIL); on 2.3× → CONFIRMED → next-session limit-on-open order.

## 9. Variants & open points
Variants not chosen:
- S07 checklist requiring volume spike 300%+ and record quarter as hard checks → volume per D-C01 (>= 2x), record quarter optional (D-C03, D-C17).
- S05 "fund crosses above its 50-DMA (with volume increase) → buy" → insufficient alone; heartbeat breakout and rising 50-SMA required (D-C06).
- S01 "Power Moves" = heartbeat (staircase sense), 50-DMA, volume; S03 = institutional buying, staircase, record quarter → single EntryChecklist (D-C17, D-H).
- S16/S17 monthly top-N momentum entries → PRF-momentum-rotation profile (A13, D-C07).
- S28 "set buy levels while calm" (UBS $4,000 gold) → allowed only as watchlist price alerts; a buy of any gold form still requires the checklist (D-R39, A11 R-A11-041).

- S07/S05 resting buy-stop placed weekly above the ceiling → non-canonical variant `RESTING_BUY_STOP`; default is close-confirmed (D-R03).

Open points:
- Closed by D-R44 — OPEN-A06-6 (tranches 60% breakout / 40% second chance within the same risk budget).
- Closed by D-R44 — OPEN-A06-7 (FADING-volume flag on a SETUP is a warning only).

Closed by round-2 decisions (2026-10-26): OPEN-A06-1 (D-R03), OPEN-A06-2 (D-R03, obsolete for the default mode), OPEN-A06-3 (D-R07), OPEN-A06-4 (D-R07), OPEN-A06-5 (D-R08).

**Glossary additions (merged into glossary v0.2.0):**
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| linked-exit-order | Linked Exit Order | CORE | Exit order (e.g. protective stop) submitted together with a buy order and activated when the buy fills (contingent/bracket order). | S07, S23 |
| buy-stop-limit-order | Buy-Stop-Limit Order | CORE | Buy-stop that, once triggered, becomes a limit order, capping the fill price on gaps. | S23 (order semantics) |

## 10. Traceability
| Rule/Concept | Sources |
|---|---|
| R-A06-001..005 checklist, breakout + rising 50-SMA | S07, S13, S25, S05, S17, S30; D-C06, D-C01, D-C02, D-C05, D-OPEN-2 |
| R-A06-006 never below 150-SMA | S23; D-C06 |
| R-A06-007 survival | S13, S30; D-C03 |
| R-A06-008..010 red, deterioration, concentration blocks | S13, S25; D-C06, D-C27, D-C11 |
| R-A06-011 exit and size before buy | S23, S25, S07; D-C08, D-C09 |
| R-A06-012..013 falling knife, IPO | S07, S30, S03 |
| R-A06-014..015 confirmations, Power Moves label | S07, S03, S01; D-C03, D-C17 |
| R-A06-016..021 prohibitions | S25, S22, S13, S30, S03; D-H, D-C01 |
| R-A06-022..030 order placement, same sitting | S13, S23, S25, S07, S05, S30, S15; D-C04, D-C08, D-C09, D-C26 |
| R-A06-031..033 second chance, first trades | S13, S07, S15 |
| R-A06-034..036 setup distance, smart-money priority, threshold class | S30, S22; D-R05, D-R07, D-R22, D-R25 |
| R-A06-037..038 tranche split, fading-volume warning | S13, S07, S30; D-R40, D-R44 |
| Watchlist lifecycle | S07, S30, S22, S02 |
