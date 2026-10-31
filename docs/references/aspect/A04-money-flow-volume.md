---
id: A04
title: Money Flow & Volume
context: CTX-B
layers: [CORE, METHOD]
status: draft
sources: [S01, S02, S03, S05, S07, S08, S13, S22, S23, S25, S27, S28, S29, S30]
decisions: [D-H, D-C01, D-C02, D-C04, D-C06, D-C15, D-C17, D-C26, D-C27, D-R05, D-R06, D-R11, D-R20, D-R22, D-R25, D-R32, D-R33, D-R43, D-R44, D-DEF-13, D-DEF-14, D-DEF-15, D-DEF-16, D-DEF-17]
depends_on: [A01, A02]
---
# A04 — Money Flow & Volume

## 1. Purpose & scope
Covers how the app reads the visible footprint of [[institutional-money]] in price and volume:
volume normalisation against the 50-day average, volume classification and spikes (D-C01), up/down-day volume,
the rising-price/fading-volume warning, distribution warnings, insider activity as information,
sector-wide "kill switch" reversals, detection of the [[heartbeat]] base (D-H, D-C02, class-scaled per D-R06) and its
breakout event, and the dated money-flow evidence (ETF fund flows, 13F holdings, insider and congressional trades)
combined into the [[smart-money-evidence]] panel per industry and per stock (D-R22, D-R25).
The [[staircase-uptrend]] is modelled as a separate, non-entry pattern (D-H).

Excludes: the buy decision itself and order placement (A06), exits and stop placement (A07), industry RS and
scoreboard status (A02), position sizing (A08), alert delivery mechanics and routines (A12), instrument/bar data model (A01).

Principle ([[follow-the-money]]): the app observes where money has been; it never forecasts where it goes
(S13 "Reading the tracks is the whole skill. Predicting them is not part of the job.").

## 2. Concepts
- [[follow-the-money]] — governing principle: decide on price and volume, not narrative.
- [[institutional-money]] — the actor whose size makes its activity visible.
- [[price-formation]] — price = balance of buyers and sellers; news is attached afterwards.
- [[volume]], [[average-volume]], [[volume-multiple]] — raw and normalised volume (50-day average, D-C01).
- [[volume-day-direction]] — up-day vs down-day volume, from close-to-close change, never from bar colour.
- [[extended-hours-trading]] — reason bar colour misleads after gaps.
- [[volume-spike]] — first-class signal VolumeSpike (D-C17), thresholds 2x / 3x / 10x (D-C01).
- [[low-volume-noise]] — volume at or below normal carries no institutional information.
- [[accumulation]] / [[distribution]] — sustained institutional buying / selling.
- [[fading-volume-rally]] — rising price on shrinking volume (Move 1 / PROTECT): review flag, never auto-sell.
- [[breakout-volume]] — volume multiple on the breakout session; confirms at >= 2x (D-C01).
- [[base]], [[support]], [[resistance]] — the range geometry of a base.
- [[heartbeat]] — canonical sideways base after a decline, ending in a breakout (D-H); min 3 months (D-C02).
- [[major-base]] — heartbeat with base >= 18 months (D-C02).
- [[short-heartbeat]] — range shorter than the minimum base; sellers not finished.
- [[breakout]], [[weak-breakout]], [[false-breakout]], [[heartbeat-breakout]] — breakout classification; consumed by A06.
- [[staircase-uptrend]] — higher highs / higher lows pattern; separate term, not a heartbeat (D-H).
- [[insider-turnaround]] — former insider buyer turning seller; information, not a sell signal.
- [[sector-kill-switch]] — whole-sector simultaneous peak within 72 h.
- [[institutional-tailwind]] — structural forced buying (mandates, index rules); context attribute.
- [[selling-the-book]] — why buying on publicity means buying from sellers (context for A06 "no news buys").
- [[leverage-liquidation-cascade]], [[net-selling]], [[percentile-rank]], [[standard-deviation]] — positioning/forced-flow context terms; descriptive only.
- [[volume-alert]] — automated alert on volume multiple (delivery owned by A12).
- [[volatility-class]] — threshold class (A08 R-A08-032) that scales base-detection thresholds (D-R05, D-R06).
- [[fund-flow]], [[institutional-holding-13f]], [[insider-transaction]], [[congressional-trade]] — dated, lagged money-flow evidence sources (D-R22).
- [[smart-money-evidence]] — combined, sourced evidence panel per industry and per stock; never a trigger (D-R25).

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| PriceBar | instrumentId, date, open, high, low, close, volume | price, shares | owned by A01; regular-session OHLC | input to all A04 calculations |
| VolumeProfile | instrumentId, date | date | one per instrument per session | derived daily |
| | volume | shares | >= 0 | from PriceBar |
| | avgVolume50 | shares | requires 50 prior sessions | R-A04-002 |
| | volumeMultiple | ratio | avgVolume50 > 0 | R-A04-003 |
| | dayDirection | enum UP, DOWN, FLAT | from close vs prior close | R-A04-005 |
| | volumeClass | enum NOISE, NORMAL, SPIKE, STRONG, EXCEPTIONAL | R-A04-007 | |
| Signal (VolumeSpike) | instrumentId, date, multiple, direction, class | — | emitted when class >= SPIKE | first-class signal (D-C17) |
| Signal (SellingSpike) | instrumentId, date, multiple | — | VolumeSpike with direction DOWN | warning; feeds A07 review |
| Signal (FadingVolumeRally) | instrumentId, rallyStart, asOf, priceChangePct, volumeRatio | — | R-A04-012 | review flag only |
| HeartbeatBase | id, instrumentId | — | — | the base of a heartbeat |
| | source | enum DETECTED, MANUAL | — | MANUAL = user-drawn ceiling/floor (S07) |
| | priorPeakDate, priorPeakPrice, declinePct | date, price, % | decline precedes base | R-A04-016 |
| | baseStart, baseEnd | date | baseEnd = breakout or invalidation date | |
| | ceiling, floor | price | ceiling > floor | [[resistance]] / [[support]] |
| | widthPct | % | (ceiling-floor)/floor | R-A04-017 |
| | ceilingTouches | int | >= `volume.base_min_ceiling_touches` | |
| | baseMonths | months (calendar) | computed | R-A04-018 |
| | tier | enum SHORT, QUALIFYING, PREFERRED, MAJOR | R-A04-019 | |
| | state | enum see lifecycle | — | |
| Breakout | id, baseId, date, close, ceiling, volumeMultiple | — | close > ceiling | |
| | class | enum CONFIRMED, WEAK, FALSE | R-A04-022..024 | CONFIRMED -> HeartbeatBreakout signal (A06) |
| | volumeGrade | enum MIN, STRONG, EXCEPTIONAL | only for CONFIRMED | D-C01 |
| StaircaseUptrend (new) | instrumentId, start, asOf, higherHighs, higherLows, maxPullbackPct, upDownVolumeRatio | — | R-A04-026 | informational pattern |
| InsiderTransaction (new) | instrumentId, insiderName, role, date, type (OPEN_MARKET_BUY, OPEN_MARKET_SELL, OPTION_RELATED_SALE, OTHER), shares, value, filingType (e.g. FORM_4), filingDate, lagDays, market, source | currency, days | filing data; lagDays = filingDate − date | S23; D-R22 |
| FundFlow (new) | fundInstrumentId, industryId, periodStart, periodEnd, creationsUsd, redemptionsUsd, netFlowUsd, aumUsd, netFlowPctAum, source, asOf | USD, % | netFlow = creations − redemptions; daily or weekly data | D-R22 |
| InstitutionalHolding (new) | companyId, filerId, filerName, reportPeriodEnd, filingDate, lagDays, shares, valueUsd, changeShares, changePct, holderCountChange, coverage = US, source = 13F | shares, USD, days | quarterly; lag ~45 days after quarter end | D-R22 |
| CongressionalTrade (new) | instrumentId, memberId, chamber, transactionDate, disclosureDate, lagDays, type (PURCHASE, SALE, EXCHANGE), amountRangeUsd, filingRef (PTR), coverage = US, source | USD range, days | STOCK Act periodic transaction report; lag up to 45 days | D-R22 |
| SmartMoneyEvidence (new) | subjectType (INDUSTRY, STOCK), subjectId, asOf, entries[] {kind (FUND_FLOW, INSTITUTIONAL_13F, VOLUME_FOOTPRINT, INSIDER, CONGRESSIONAL), direction (BUYING, SELLING, MIXED), magnitude, eventDate, availableDate, lagDays, coverage, source, ref}, summary {institutionalDirection, insiderDirection}, evidenceStrength (STRONG_BUYING, HEAVY_SELLING, NONE), positiveSources[], priorityHint (RAISE, NONE), reviewFlag (INSIDER_FLIP, HEAVY_SELLING, NONE) | — | every entry dated and sourced; read-only evidence | D-R22, D-R25; consumed by A02 views, A05, A06, A07 |
| Signal (InsiderTurnaround) | instrumentId, insiderName, priorBuyValue, sellValue, sellDate | — | R-A04-030 | information only |
| Signal (SectorKillSwitch) | industryId, windowStart, windowEnd, memberPeaks[] | — | R-A04-033 | review flag |
| TechnicalSetup | instrumentId, asOf, baseId, staircaseId, latestVolumeProfile | — | owned by A06 | A04 supplies pattern facts |

HeartbeatBase lifecycle (state):
```
DECLINING -> FORMING (range established, baseMonths < min)          [SHORT tier]
FORMING   -> QUALIFIED (baseMonths >= volume.base_min_months)       [QUALIFYING/PREFERRED/MAJOR]
FORMING|QUALIFIED -> BROKEN_DOWN (daily close < floor)              terminal; a new base may start
QUALIFIED -> BROKEN_OUT (Breakout.class = CONFIRMED)                terminal for this base
QUALIFIED -> QUALIFIED (Breakout.class in {WEAK, FALSE}; base continues, event recorded)
FORMING   -> FORMING (close > ceiling before min length: ceiling is re-set, no breakout event)
```
After BROKEN_OUT a pullback to the old ceiling is the [[second-chance-entry]] zone (A06); a new base after the
run is a new HeartbeatBase ("second heartbeat", S13).

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `volume.avg_window_sessions` | 50 | fixed 50 (param) | sessions | D-C01 |
| `volume.spike_min_multiple` | 2.0 | >= 2.0 | x avg | D-C01 |
| `volume.spike_strong_multiple` | 3.0 | > spike_min | x avg | D-C01 |
| `volume.spike_exceptional_multiple` | 10.0 | > strong | x avg | D-C01 |
| `volume.breakout_min_multiple` | 2.0 | >= 2.0; one value for all instruments (no per-industry or per-class values) | x avg | D-C01, D-DEF-16 (consumed by A06) |
| `volume.noise_max_multiple` | 1.0 | 0.5–1.0 | x avg | glossary [[low-volume-noise]] ("at or below normal") |
| `volume.alert_min_multiple` | 2.0 | >= 1.5 | x avg | D-C01 (S07's "300%" alert = 4.0x, allowed user value) |
| `volume.base_min_months` | 3 | 3–24 | months | D-C02, S13, S07 |
| `volume.base_preferred_months` | 6 | >= base_min | months | S13 |
| `volume.major_base_min_months` | 18 | >= 12 | months | D-C02, S05 |
| `volume.base_prior_decline_min_pct[low/medium/high/extreme]` | 15 / 25 / 35 / 35 | > 0 | % from prior peak | D-R06, D-R11 |
| `volume.base_max_width_pct[low/medium/high/extreme]` | 20 / 30 / 50 / 65 | > 0 | % of floor | D-R06, D-R11 ("tight zigzag", S13) |
| `volume.base_ceiling_touch_tolerance_pct[low/medium/high/extreme]` | 2 / 3 / 5 / 8 | > 0 | % below ceiling | D-R06, D-R32 |
| `volume.base_min_ceiling_touches` | 2 | >= 2 | count | D-R06 (S13 "connect the tops") |
| `volume.base_ceiling_basis` | CLOSE (highest close in the base) | {CLOSE} | — | D-R06 |
| `volume.threshold_class_basis` | = A08 `risk.vol_class_threshold_basis` | — | — | D-R05 |
| `volume.fading_window_sessions` | 20 | 10–63 | sessions | D-DEF-13 |
| `volume.fading_segment_sessions` | 5 | 3–10, <= window/2 | sessions (k) | D-DEF-13 |
| `volume.fading_ratio_max` | 0.6 | (0,1) | ratio | D-DEF-13 |
| `volume.staircase_swing_strength` | 5 | 5 | sessions on each side of a swing point | D-DEF-14 (= D-R04 buyer-area swing) |
| `volume.staircase_min_swings` | 3 | >= 2 | consecutive higher swing highs and higher swing lows | D-DEF-14 |
| `volume.staircase_max_pullback_pct[low/medium/high/extreme]` | 8 / 15 / 25 / 35 | = class stop-band maximum (A08) | % from swing high | D-DEF-14 |
| `volume.insider_lookback_months` | 12 | 6–24 | months | S23 ("over the last year") |
| `volume.kill_switch_window_hours` | 72 | 24–120 | hours | S22 |
| `volume.kill_switch_min_member_share` | 60 | 50–100 | % of tracked industry members | D-DEF-15 |
| `volume.kill_switch_min_members` | 3 | >= 3 | tracked members | D-DEF-15 |
| `volume.evidence_sources` | {FUND_FLOW, INSTITUTIONAL_13F, VOLUME_FOOTPRINT, INSIDER, CONGRESSIONAL} | subset | — | D-R22 (retail flow not selected) |
| `volume.evidence_lookback_months` | 12 | 6–24 | months shown in the panel | = `volume.insider_lookback_months` (S23) |
| `volume.evidence_window_days` | 90 | 30–180 | days (available date) for STRONG BUYING | D-R33 |
| `volume.strong_min_sources` | 2 | >= 2 | independent positive sources | D-R33 |
| `volume.strong_etf_inflow_pct_aum` | 5 | > 0 | % of AUM, net inflow over 4 weeks | D-R33 |
| `volume.strong_13f_ownership_change_pp` | 2 | > 0 | pp institutional ownership, QoQ | D-R33 |
| `volume.strong_insider_cluster_buys` | 2 | >= 2 | open-market insider buys | D-R33 |
| `volume.strong_congressional_buys` | 2 | >= 2 | congressional purchases | D-R33 |
| `volume.heavy_insider_sells` | 3 | >= 2 | open-market insider sells | D-R33 |
| `volume.heavy_insider_window_days` | 30 | 10–90 | days | D-R33 |
| `volume.heavy_13f_ownership_change_pp` | −3 | < 0 | pp institutional ownership, QoQ (down 3 pp or more) | D-R33 |
| `volume.insider_sources` | per market, see R-A04-047 | official regulatory feeds | — | D-R22, D-DEF-17 |

## 5. Rules
Volume normalisation and classification
- **R-A04-001** (hard, CORE) — Volume MUST be judged relative to the instrument's own normal volume, never in absolute shares across instruments. _Sources: S13, S07, S30. Decision: D-C01_
- **R-A04-002** (hard, CORE) — Average volume MUST be the mean of the prior `volume.avg_window_sessions` (default 50) regular sessions, excluding the current session; with fewer than 50 prior sessions avgVolume50 and all multiples are undefined. _Sources: S07, S05 (window unspecified). Decision: D-C01_
- **R-A04-003** (hard, CORE) — volumeMultiple = volume / avgVolume50. Source percentages MUST be normalised: "N% above average" = (1 + N/100)x (S07 "300% above" = 4.0x). _Sources: S07, S05. Decision: D-C01_
- **R-A04-004** (hard, METHOD) — Bar colour MUST NOT be used to classify buying vs selling. _Sources: S13 "The height is what matters.", S07 candle-colour warning_
- **R-A04-005** (hard, CORE) — dayDirection = UP if close > prior close, DOWN if close < prior close, else FLAT (regular-session closes). _Sources: S13, S07. Glossary: [[volume-day-direction]]_
- **R-A04-006** (hard, METHOD) — A session with volumeMultiple >= `volume.spike_min_multiple` MUST emit a VolumeSpike signal carrying multiple, direction and class. _Sources: S07, S05, S03. Decision: D-C01, D-C17_
- **R-A04-007** (hard, METHOD) — volumeClass: NOISE if VM <= `volume.noise_max_multiple`; NORMAL if noise_max < VM < 2; SPIKE if 2 <= VM < 3; STRONG if 3 <= VM < 10; EXCEPTIONAL if VM >= 10 (thresholds = parameters). _Sources: S05 "double ... Triple is better. 10 times is exceptional.", S07. Decision: D-C01_
- **R-A04-008** (soft, METHOD) — Price moves on NOISE volume MUST NOT generate any signal; the app labels them "noise". _Sources: S07 "amateurs trading with each other", S01_
- **R-A04-009** (soft, METHOD) — A VolumeSpike with direction UP is labelled "possible accumulation — investigate"; it is not by itself an entry (A06 requires a heartbeat breakout). _Sources: S07, S03, S01. Decision: D-C06_
- **R-A04-010** (soft, METHOD) — A VolumeSpike with direction DOWN (SellingSpike) on an instrument held or watched MUST raise a "distribution warning" review flag; existing stops are respected, no automatic sale is generated by this flag. _Sources: S07 "respect your stop", S30. Decision: D-C26, D-C27_
- **R-A04-011** (soft, CORE) — Declines on NOISE volume are labelled "limited selling pressure"; no action. _Sources: S01_

Rising price / fading volume (Move 1)
- **R-A04-012** (soft, METHOD) — For a held instrument in a rally (close higher than `volume.fading_window_sessions` (20) sessions earlier), if the average volume of the last `volume.fading_segment_sessions` (5) sessions of the window divided by the average volume of its first 5 sessions is <= `volume.fading_ratio_max` (0.6), the app MUST raise a FadingVolumeRally review flag. _Sources: S30 Ch.5 (three stages: heavy-volume start, rising price on shrinking volume, selling spike). Decision: D-DEF-13_
- **R-A04-013** (hard, METHOD) — A FadingVolumeRally flag MUST NOT create, modify or trigger any order; it prompts the user to decide profit-taking/risk reduction in the next review (A07 profit rules). On a watched SETUP the same pattern is a warning only and does not block arming (A06 R-A06-038). _Sources: S30 "Pay attention; it is not an order to sell." Decision: D-C27 (only price-based exits are automatic), D-R44_
- **R-A04-014** (soft, METHOD) — When a FadingVolumeRally is followed by a SellingSpike on the same instrument, the flag severity escalates to "stage 3 selling" in the review queue. _Sources: S30 ("The next big spike in volume was the selling")_

Heartbeat base detection (D-H, D-C02)
- **R-A04-015** (hard, METHOD) — The term heartbeat MUST denote only a sideways base after a decline that ends in a breakout; a series of higher highs/higher lows MUST be classified as [[staircase-uptrend]], never as heartbeat. _Sources: S13, S25, S30, S07, S05 vs S01, S03 (deprecated). Decision: D-H_
- **R-A04-016** (hard, METHOD) — A DETECTED base requires a prior decline from a peak of at least `volume.base_prior_decline_min_pct[class]` (LOW 15, MEDIUM 25, HIGH 35, EXTREME 35%) before the range starts. _Sources: S13 "Price falls for a while, stops falling", S07, S30. Decision: D-R06, D-R11_
- **R-A04-017** (hard, METHOD) — A DETECTED base requires all closes inside [floor, ceiling], where ceiling = highest close and floor = lowest close in the base, with widthPct <= `volume.base_max_width_pct[class]` (LOW 20, MEDIUM 30, HIGH 50, EXTREME 65%) and at least `volume.base_min_ceiling_touches` (2) closes within `volume.base_ceiling_touch_tolerance_pct[class]` (LOW 2, MEDIUM 3, HIGH 5, EXTREME 8%) below the ceiling; touches on separate swings count once each. _Sources: S13 "tight zigzag", S07 "between support and resistance". Decision: D-R06, D-R11, D-R32_
- **R-A04-018** (hard, METHOD) — baseMonths = calendar months from baseStart to the evaluation date (or baseEnd). _Sources: S13, S07. Decision: D-C02_
- **R-A04-019** (hard, METHOD) — tier: SHORT if baseMonths < `volume.base_min_months` (3); QUALIFYING if 3 <= baseMonths < 6; PREFERRED if 6 <= baseMonths < 18; MAJOR if baseMonths >= `volume.major_base_min_months` (18). Only QUALIFYING or higher can produce a CONFIRMED breakout. _Sources: S13, S07, S05, S30. Decision: D-C02_
- **R-A04-020** (soft, METHOD) — Longer bases rank higher in watchlists (MAJOR > PREFERRED > QUALIFYING); this is a ranking preference only, never a forecast of move size. _Sources: S13 "History, not a guide", S30 "The longer the heartbeat, the better."_
- **R-A04-021** (hard, METHOD) — A daily close below the floor sets the base to BROKEN_DOWN ("breakdown"); any open setup on it is invalidated (A06). _Sources: S30 "a weak break, then a breakdown"_
- **R-A04-022** (hard, METHOD) — Breakout.class = CONFIRMED iff the base is QUALIFIED, the daily close > ceiling and volumeMultiple on that session >= `volume.breakout_min_multiple` (2.0). An intraday move above the ceiling without a close above is not a breakout. _Sources: S07 "closes above the upper boundary with a significant volume spike", S30, S05. Decision: D-C01, D-C02_
- **R-A04-023** (hard, METHOD) — Breakout.class = WEAK if close > ceiling but VM < `volume.breakout_min_multiple`; it is recorded as a warning and MUST NOT emit HeartbeatBreakout. _Sources: S30 "A break on no volume is a warning." Decision: D-C01_
- **R-A04-024** (soft, CORE) — A CONFIRMED or WEAK breakout whose price closes back below the ceiling within the next evaluation (weekly review or next session per A06 mode) is re-labelled FALSE. _Sources: S07 "false breakouts vs. confirmed breakouts"_
- **R-A04-025** (soft, METHOD) — MANUAL bases (user-drawn ceiling/floor) are allowed and evaluated with the same R-A04-018..024; DETECTED and MANUAL bases on the same instrument are shown side by side, never merged. _Sources: S07 "draw the upper resistance and lower support boundaries"_

Staircase uptrend (separate pattern)
- **R-A04-026** (soft, CORE) — A StaircaseUptrend is recorded when at least `volume.staircase_min_swings` (3) consecutive higher swing highs and higher swing lows occur (swing points with `volume.staircase_swing_strength` (5) sessions on each side), every pullback from a swing high to the next swing low is <= `volume.staircase_max_pullback_pct[class]` (LOW 8, MEDIUM 15, HIGH 25, EXTREME 35%, threshold class per R-A04-038), and average volume on up legs exceeds that on pullback legs. _Sources: S03, S01. Decision: D-H, D-DEF-14_
- **R-A04-027** (hard, METHOD) — A StaircaseUptrend MUST NOT satisfy any entry condition of A06 and MUST NOT be labelled "heartbeat"; S03's advice to avoid sideways stocks is not adopted. _Sources: S03, S30. Decision: D-H, D-C06_
- **R-A04-028** (soft, METHOD) — After a CONFIRMED breakout, a staircase forming above the old ceiling MAY be displayed as trend context for trailing stops (A07: stop moved under each higher low). _Sources: S13 ("each time it made a new low above the old one")_

Insider activity
- **R-A04-029** (hard, METHOD) — OPTION_RELATED_SALE transactions MUST be excluded from insider signals (routine executive selling is noise). _Sources: S23 "They are always selling."_
- **R-A04-030** (soft, METHOD) — If an insider with net OPEN_MARKET_BUY value > 0 over `volume.insider_lookback_months` subsequently makes an OPEN_MARKET_SELL, the app MUST emit an InsiderTurnaround signal on held/watched instruments. _Sources: S23 Ch.14_
- **R-A04-031** (hard, METHOD) — InsiderTurnaround is information for the next review: it MUST NOT trigger an exit and MUST NOT change a stop. _Sources: S23 "not infallible and not a sell signal on its own". Decision: D-C27_
- **R-A04-032** (soft, METHOD) — The review shows per held instrument the insider balance over the lookback as BUYERS / SELLERS / MIXED (excluding option-related sales). _Sources: S23 Ch.14 exercise_

Sector-wide flows
- **R-A04-033** (soft, METHOD) — If an industry has at least `volume.kill_switch_min_members` (3) tracked members and at least `volume.kill_switch_min_member_share` (60%) of them set their peak close within `volume.kill_switch_window_hours` (72) and reverse, the app MUST raise a SectorKillSwitch review flag on that industry. _Sources: S22. Decision: D-DEF-15_
- **R-A04-034** (soft, METHOD) — SectorKillSwitch and SellingSpike flags are inputs to the weekly review only; industry status remains governed by A02 RS (D-C15) and buy blocking by D-C27. _Sources: S22, S30. Decision: D-C15, D-C27_

General
- **R-A04-035** (hard, METHOD) — Narrative inputs (news, opinions, forecasts, "famous investor buying") MUST NOT be inputs to any A04 classification. _Sources: S30 "Watch what the money does", S25 selling the book, S27 "Behaviour beats opinion."_
- **R-A04-036** (soft, METHOD) — The same volume and base rules apply to any traded instrument with a volume series (stocks, funds, commodity ETFs/ETCs, crypto funds); instruments without reliable volume (e.g. some indices) produce no volume signals. _Sources: S30 "The rules do not change with what you are buying."_
- **R-A04-037** (soft, CORE) — Instruments below the A01 liquidity floors (`instrument.min_liquidity.*`: stocks $5M, ETFs AUM $100M and $2M average daily traded value; A01 R-A01-049) are excluded from volume signals ("invest where there is volume"). _Sources: S07. Decision: D-R43_

Round-2 additions (2026-10-26)
- **R-A04-038** (hard, METHOD) — Base-detection thresholds (R-A04-016/017) MUST use the threshold class of A08 R-A08-032: the stock's own volatility class, or the industry-proxy class for a fund or basket. _Decision: D-R05, D-R06_
- **R-A04-039** (hard, CORE) — Every money-flow evidence record (`FundFlow`, `InstitutionalHolding`, `InsiderTransaction`, `CongressionalTrade`) MUST carry its event or period date, the date it became available (filing/disclosure date), the resulting lag in days, its market coverage and its source; records without these fields MUST be rejected. 13F holdings are quarterly with a lag of about 45 days (US only); congressional disclosures (STOCK Act PTRs) have a lag of up to 45 days (US only); fund flows are daily or weekly; the volume footprint (VolumeProfile, Signals) covers all markets in real time. _Decision: D-R22, D-C22 (dated facts)_
- **R-A04-040** (hard, METHOD) — Money-flow evidence and the [[smart-money-evidence]] panel MUST NOT trigger, modify or cancel any entry, exit, order or stop, and MUST NOT change scoreboard status (A02); entry stays per D-C06, exits per D-C26. _Decision: D-R22, D-R25, D-C06, D-C26, D-C27_
- **R-A04-041** (soft, METHOD) — The app MUST build a `SmartMoneyEvidence` panel per stock and per industry (aggregating member stocks and the industry's ETFs) that combines fund flows, 13F holding changes, the volume footprint, insider transactions and congressional trades as dated, sourced entries with their lag; A02 shows the industry panels as the "who is investing" view. _Decision: D-R20, D-R22, D-R25_
- **R-A04-042** (soft, METHOD) — STRONG BUYING in the panel (R-A04-045) sets `priorityHint = RAISE` (consumed by A06 watchlist priority); an InsiderTurnaround / insider flip (R-A04-030) sets `reviewFlag = INSIDER_FLIP` and HEAVY SELLING (R-A04-046) sets `reviewFlag = HEAVY_SELLING`, both consumed by A07 REVIEW_INSIDER. _Sources: S23. Decision: D-R25, D-R33_
- **R-A04-043** (hard, METHOD) — Retail money flow is not modelled; the panel MUST NOT present any figure as retail flow. _Decision: D-R22_
- **R-A04-044** (soft, CORE) — The panel MUST show each entry's age (days since the event) and label entries older than `volume.evidence_lookback_months` as stale; lagged sources MUST NOT be presented as current positioning. _Decision: D-R22, D-R25_

Round-3 additions (2026-10-26)
- **R-A04-045** (soft, METHOD) — `evidenceStrength = STRONG_BUYING` iff at least `volume.strong_min_sources` (2) independent sources are positive with an available date within the last `volume.evidence_window_days` (90): FUND_FLOW positive if the industry ETF's net inflow over 4 weeks > `volume.strong_etf_inflow_pct_aum` (5%) of AUM; INSTITUTIONAL_13F positive if institutional ownership rose >= `volume.strong_13f_ownership_change_pp` (2 pp) quarter on quarter; INSIDER positive if >= `volume.strong_insider_cluster_buys` (2) open-market insider buys (cluster); CONGRESSIONAL positive if >= `volume.strong_congressional_buys` (2) purchases. The positive sources are listed in `positiveSources`. _Decision: D-R33, D-R25_
- **R-A04-046** (soft, METHOD) — `evidenceStrength = HEAVY_SELLING` iff >= `volume.heavy_insider_sells` (3) open-market insider sells (option-related sales excluded, R-A04-029) within `volume.heavy_insider_window_days` (30), or institutional ownership changed by <= `volume.heavy_13f_ownership_change_pp` (−3 pp) quarter on quarter. HEAVY SELLING takes precedence over STRONG BUYING on the same panel. _Decision: D-R33, D-R25_
- **R-A04-047** (soft, CORE) — Insider transactions outside the US MUST come from the market's official regulatory feed with `lagDays` up to the statutory maximum: EU/UK MAR Art. 19 PDMR notifications 3 business days; CA SEDI 5 calendar days; AU ASX Appendix 3Y 5 business days; KR DART executive ownership reports 5 business days; JP officer trading reports by the 15th of the following month; IN SEBI PIT 4 trading days. Markets without such a feed show insider evidence as "not covered". _Decision: D-R22, D-DEF-17_
- **R-A04-048** (hard, METHOD) — The breakout volume minimum `volume.breakout_min_multiple` (2.0) MUST be the same for every instrument; per-industry or per-volatility-class breakout multiples are not allowed. _Decision: D-C01, D-DEF-16_

## 6. Processes
**PR-A04-01 Daily volume classification** — trigger: daily after close (automated, D-C04). Inputs: PriceBar history.
1. For each tracked instrument compute avgVolume50, volumeMultiple, dayDirection (R-A04-002..005).
2. Classify volumeClass (R-A04-007); emit VolumeSpike / SellingSpike (R-A04-006, R-A04-010).
3. If instrument is held/watched and VM >= `volume.alert_min_multiple`, hand an Alert to A12.
Outputs: VolumeProfile rows, Signals, Alerts. No orders.

**PR-A04-02 Heartbeat base detection** — trigger: daily after close (automated) and on demand in the weekly review. Inputs: PriceBars, existing HeartbeatBase records.
1. Determine the threshold class (R-A04-038); locate the latest peak and the decline after it; require declinePct >= `volume.base_prior_decline_min_pct[class]` (R-A04-016).
2. From the decline low, grow the range window while closes stay within the width limit; set ceiling = highest close and floor = lowest close; count closes within the touch tolerance below the ceiling (R-A04-017).
3. Compute baseMonths and tier (R-A04-018/019); set state FORMING or QUALIFIED.
4. If close < floor → BROKEN_DOWN (R-A04-021); start over from step 1 on later data.
5. If close > ceiling: if state FORMING → reset ceiling, no event; if QUALIFIED → create Breakout, classify CONFIRMED / WEAK (R-A04-022/023).
6. CONFIRMED → state BROKEN_OUT, emit HeartbeatBreakout input to A06; WEAK → record, keep QUALIFIED.
7. On next evaluation, re-label FALSE where applicable (R-A04-024).
Outputs: HeartbeatBase, Breakout. Thresholds per the threshold class (R-A04-038); MANUAL bases remain available (R-A04-025).

**PR-A04-03 Fading-volume and distribution check (Move 1)** — trigger: weekly review (D-C04), on held positions.
1. For each position in a rally, compute volume ratio over `volume.fading_window_sessions` (R-A04-012).
2. Raise FadingVolumeRally flags; escalate if a SellingSpike followed (R-A04-014).
3. Present flags with A07 profit-taking options; record user decision in ReviewLog (A12).
Outputs: review flags only (R-A04-013).

**PR-A04-04 Insider check** — trigger: on new filings (automated ingest) and weekly review.
1. Ingest InsiderTransactions; drop OPTION_RELATED_SALE from signal logic (R-A04-029).
2. Compute per-insider net buying over lookback; detect turnaround (R-A04-030).
3. Show BUYERS/SELLERS/MIXED and turnaround flags in review (R-A04-032).

**PR-A04-05 Sector kill-switch scan** — trigger: daily after close. Inputs: industry membership (A01/A02), peak dates. Steps: per industry, collect members' peak-close timestamps over the recent window; if the share within 72 h ≥ threshold and members are reversing, raise flag (R-A04-033).

**PR-A04-06 Money-flow evidence ingest and panel** — trigger: on new data per source (fund flows daily/weekly, 13F quarterly, Form 4 and PTR filings on publication) and at the weekly review. Steps: (1) validate dates, lag, coverage and source (R-A04-039); (2) attach to stock and industry (A01 classification, industry ETFs); (3) aggregate direction per source; (4) set priorityHint / reviewFlag (R-A04-042); (5) publish panels to A02, A05, A06, A07; no orders (R-A04-040).

## 7. Calculations
```
AVGVOL_50(t)  = mean(volume[t-50 .. t-1])                         # shares; undefined if < 50 prior sessions
VM(t)         = volume(t) / AVGVOL_50(t)                          # ratio
pct_above_to_multiple(p) = 1 + p/100                              # "300% above average" -> 4.0x
dayDirection(t) = sign(close(t) - close(t-1))                     # UP / DOWN / FLAT
volumeClass(VM) = NOISE        if VM <= noise_max (1.0)
                  NORMAL       if VM < spike_min (2.0)
                  SPIKE        if VM < strong (3.0)
                  STRONG       if VM < exceptional (10.0)
                  EXCEPTIONAL  otherwise
declinePct    = (priorPeakPrice - lowAfterPeak) / priorPeakPrice * 100      # >= 15/25/35/35 by class
ceiling       = max(close in base) ; floor = min(close in base)             # D-R06
widthPct      = (ceiling - floor) / floor * 100                             # <= 20/30/50/65 by class
touch(t)      = close(t) >= ceiling * (1 - touch_tolerance_pct/100)        # 2/3/5/8 by class; >= 2 touches
baseMonths    = calendar_months_between(baseStart, t)            # fractional, e.g. 17.9
tier          = SHORT (<3) | QUALIFYING (3..<6) | PREFERRED (6..<18) | MAJOR (>=18)
breakout(t)   = state==QUALIFIED AND close(t) > ceiling
CONFIRMED     = breakout(t) AND VM(t) >= breakout_min_multiple (2.0)
WEAK          = breakout(t) AND VM(t) <  breakout_min_multiple
fadingRatio   = mean(volume[last k sessions of window]) / mean(volume[first k sessions of window])
                # window 20, k 5; flag if close(t) > close(t-20) AND fadingRatio <= 0.6 (D-DEF-13)
strongBuying  = count(positive sources within 90 days) >= 2                  # D-R33
heavySelling  = insider_open_market_sells(30 days) >= 3 OR delta_inst_ownership_pp <= -3
insiderNet(i) = sum(value of OPEN_MARKET_BUY) - sum(value of OPEN_MARKET_SELL) over lookback, per insider i
netFlow       = creationsUsd - redemptionsUsd ; netFlowPctAum = netFlow / aumUsd * 100
lagDays       = availableDate - eventDate                                   # 13F ~45, PTR <= 45
```

## 8. Examples / fixtures
**EX-A04-01 Volume multiple and class (synthetic)** — Given AVGVOL_50 = 1,000,000 and volume today 2,400,000, close above prior close. When classified. Then VM = 2.4, class SPIKE, direction UP, VolumeSpike emitted, not STRONG.
- Edge: volume 1,990,000 → VM 1.99 → NORMAL, no signal. Volume 3,000,000 → VM 3.0 → STRONG (boundary inclusive). Volume 10,000,000 → EXCEPTIONAL.
- Edge: only 49 prior sessions (e.g. recent IPO) → VM undefined, no signal (R-A04-002).

**EX-A04-02 Percentage normalisation (S07, June 2026)** — Given S07 rule "volume surges 300%+ above average". When normalised. Then threshold = 4.0x; a user may set `volume.alert_min_multiple` = 4.0; default remains 2.0 (D-C01). S07's chart example "400% volume spike" = 5.0x → class STRONG.

**EX-A04-03 Misleading green candle (S13, 8 Aug 2026 session)** — Given prior close 100.00, pre-market gap to open 90.00, session close 90.90 (+1% from open, green candle). When dayDirection computed. Then close-to-close = −9.1% → DOWN; with VM >= 2 the event is a SellingSpike, not accumulation (R-A04-004/005).

**EX-A04-04 Rising price, fading volume (S30, 24 Oct 2026)** — Given Beyond Meat: volume ~5x normal at rally start, fading while $10,000 grew to ~$36,000; next big spike was selling; end value ~$4,000. When PR-A04-03 runs mid-rally with early-window mean VM 5.0 and late-window mean VM 0.8. Then fadingRatio = 0.8 / 5.0 = 0.16 ≤ 0.6 → FadingVolumeRally flag; no order created (R-A04-013); the later DOWN spike escalates to "stage 3 selling" (R-A04-014).
- Peloton fixture (S30): heavy volume only at start; $10,000 → ~$65,000 → ~$5,400 (share ~$170 → $6). Expected: same flag pattern.

**EX-A04-05 Base tiers (S13, S07, S05, S30)** — Given bases of 1 month (gold, autumn 2026, S30), 3–4 months (gold, summer 2025, S30), 8 months (S07 chart read), 18 months (AMN, S05, June 2026), ~3 years (Tesla 2017–2019, S07), ~2 years (Rocket Lab, S07). When tiered. Then SHORT, QUALIFYING, PREFERRED, MAJOR, MAJOR, MAJOR.
- Edge: baseMonths 17.9 → PREFERRED; 18.0 → MAJOR (inclusive). 2.95 → SHORT (no breakout possible).

**EX-A04-06 Breakout classification (S30 grading table, 24 Oct 2026)**
| Case | Base | Close vs ceiling | VM | Expected class |
|---|---|---|---|---|
| NVIDIA historic (S30) | textbook heartbeat | above, share ~$60 | ~2.0 | CONFIRMED, grade MIN |
| Gold summer 2025 (S30) | 3–4 months | above, near $3,400 | ~2.0 | CONFIRMED |
| EOG (S30) | heartbeat | above | ~1.5 | WEAK (source said "broke out on volume"; D-C01 overrides) |
| TEAM 2nd break (S30) | heartbeat | above | ~1.0 | WEAK ("no money behind it") |
| ECL (S30) | heartbeat | not closed above | big but fading | no breakout (setup only) |
| Gold autumn 2026 (S30) | ~1 month | weak break then close < floor | low | SHORT base → BROKEN_DOWN |
| Tesla early 2020 (S07) | ~3 years | above | ~10 | CONFIRMED, EXCEPTIONAL, MAJOR base |

**EX-A04-07 Intraday poke (edge, synthetic)** — Given a QUALIFIED base with ceiling 20.00; session high 20.60, close 19.80, VM 2.5. Then no Breakout (R-A04-022); VolumeSpike UP still emitted (R-A04-006).

**EX-A04-08 Close above ceiling during FORMING (edge, synthetic)** — Given base 2 months old, ceiling 50.00, close 51.00 on VM 3.0. Then no Breakout event; ceiling reset to the new high; tier SHORT (R-A04-019, PR-A04-02 step 5).

**EX-A04-09 Staircase is not a heartbeat (S03, 7 Jun 2026)** — Given a stock with four consecutive higher highs and higher lows, volume higher on up legs. When classified. Then StaircaseUptrend recorded; no HeartbeatBase; A06 entry check "heartbeat breakout" = false (R-A04-027).

**EX-A04-10 Insider turnaround (S23, 15 Aug 2026 session)** — Given a semiconductor director with heavy open-market buying in the prior 12 months, then an $89M open-market sale one day after the peak. Then InsiderTurnaround emitted; no exit, stop unchanged (R-A04-031).
- Edge: CEO receives options and sells shares on vesting each quarter (OPTION_RELATED_SALE) → no signal (R-A04-029).
- Restaurant-chain CEO (regular buyer) sells $3M days before collapse → InsiderTurnaround.

**EX-A04-11 Sector kill switch (S22, 14 Aug 2026)** — Given quantum names QBTS peak 2025-10-15, RGTI peak 2025-10-15, IonQ peak 2025-10-13, then −53%, −67%, −45%. When PR-A04-05 runs (members tracked = 3). Then peaks span 48 h <= 72 h; 3 tracked members (>= 3), share = 100% >= 60% → SectorKillSwitch flag. Edge: 5 tracked members with 2 peaks inside 72 h → 40% < 60% → no flag.

**EX-A04-12 Class-scaled base detection (synthetic, D-R06)** — Given a stock with prior peak close 100.00, a decline to 70.00 (declinePct 30.0%), then 4 months of closes between 70.00 and 88.00 with closes of 88.00, 86.50 and 85.90 on three separate swings. When classified with threshold class MEDIUM (decline ≥ 25, width ≤ 30, tolerance 3%). Then widthPct = 18/70 = 25.7% ≤ 30, touch level 88 × 0.97 = 85.36 → 3 touches ≥ 2 → QUALIFIED (QUALIFYING tier). Same series with class LOW: decline 30 ≥ 15 but width 25.7 > 20 → no DETECTED base. Class HIGH: decline 30 < 35 → no DETECTED base. Touch tolerance for class EXTREME is 8% (D-R32): a ceiling of 88.00 accepts touches at closes >= 80.96.

**EX-A04-13 Smart-money evidence panel (synthetic, D-R22/D-R25/D-R33)** — Given asOf 2026-10-24 and for one stock: a 13F filing for quarter end 2026-06-30 filed 2026-08-14 (lag 45 days; 71 days before asOf) showing institutional ownership 61.0% → 64.5% (+3.5 pp >= 2 → positive); a congressional PTR for one purchase on 2026-09-10 disclosed 2026-10-20 (lag 40 days; 1 < 2 buys → not positive); one insider open-market buy of $250,000 on 2026-10-06 filed 2026-10-08 (1 < 2 → no cluster); its industry ETF with net creations of $120M over 4 weeks on AUM $5.0B = 2.4% (<= 5% → not positive). Then the panel lists four dated, sourced entries with their lags, institutionalDirection = BUYING, positive sources = 1 < 2 → no STRONG BUYING, priorityHint = NONE. When a second insider buys in the open market on 2026-10-15, the insider source becomes positive (cluster of 2) → 2 positive sources → STRONG_BUYING, priorityHint = RAISE (R-A04-045). No order, no stop change and no status change result (R-A04-040). A later InsiderTurnaround on the same stock sets reviewFlag = INSIDER_FLIP (A07 REVIEW_INSIDER).

**EX-A04-14 Heavy selling (synthetic, D-R33)** — Given open-market insider sells on 2026-10-01, 2026-10-09 and 2026-10-20 (3 sells within 19 days <= 30) → HEAVY_SELLING, reviewFlag = HEAVY_SELLING (A07 REVIEW_INSIDER), no order. Edge: two open-market sells plus one OPTION_RELATED_SALE → 2 < 3 → no flag (R-A04-029). Institutional ownership 64.5% → 61.0% QoQ (−3.5 pp <= −3) → HEAVY_SELLING; −2.5 pp → no flag.

## 9. Variants & open points
Variants not chosen:
- S01/S03 "heartbeat" = higher highs/higher lows → deprecated; modelled as [[staircase-uptrend]] (D-H).
- S07 volume threshold "300%+ above average" (4x) as entry confirmation → replaced by >= 2x (D-C01); 4x remains a user alert setting.
- S30 "~1.5x decent for energy" → not adopted: below the D-C01 minimum (allowed range >= 2.0); no per-industry relaxation (R-A04-048, D-DEF-16).
- S03 "avoid sideways stocks" → rejected (D-H).
- S05 heartbeat "18 months pretty good" as minimum → 18 months is the MAJOR tag, not the minimum (D-C02).

- Ceiling on the session high → not chosen; ceiling = highest close (D-R06).
- Retail money flow as a scoreboard input → not selected (D-R22).

Open points:
- Closed by D-DEF-13 — OPEN-A04-4 (fading window 20, k 5, ratio 0.6; pending user review).
- Closed by D-DEF-14 — OPEN-A04-5 (staircase swing strength 5, 3 swings, class-scaled pullback; pending user review).
- Closed by D-DEF-15 — OPEN-A04-6 (kill switch 60% of >= 3 tracked members; pending user review).
- Closed by D-DEF-16 — OPEN-A04-7 (one breakout multiple for all instruments; pending user review).
- Closed by D-DEF-17 — OPEN-A04-8 (official non-US insider feeds with statutory lag; pending user review).
- Closed by D-R32 — OPEN-A04-9 (EXTREME touch tolerance 8%).
- Closed by D-R33 — OPEN-A04-10 (STRONG BUYING / HEAVY SELLING thresholds).

Closed by round-2 decisions (2026-10-26): OPEN-A04-1 (D-R06), OPEN-A04-2 (D-R06), OPEN-A04-3 (D-R06).

**Glossary additions (merged into glossary v0.2.0):**
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| insider-transaction | Insider Transaction | CORE | A reported trade by a company insider in the company's own shares, typed as open-market buy, open-market sell or option-related sale. | S23 |
| swing-point | Swing High / Swing Low | CORE | A local price high (low) that is higher (lower) than the surrounding sessions; building block of staircase and base detection. | S03, S13 |

## 10. Traceability
| Rule/Concept | Sources |
|---|---|
| R-A04-001..003 volume normalisation | S07, S05, S30, S13; D-C01 |
| R-A04-004..005 direction not colour | S13, S07 |
| R-A04-006..011 spikes, noise, distribution | S07, S05, S03, S01, S30; D-C01, D-C17 |
| R-A04-012..014 fading-volume rally | S30 |
| R-A04-015..025 heartbeat base and breakout | S13, S25, S30, S07, S05; D-H, D-C01, D-C02 |
| R-A04-026..028 staircase uptrend | S03, S01, S13; D-H |
| R-A04-029..032 insider activity | S23 |
| R-A04-033..034 sector kill switch | S22 |
| R-A04-035..037 general | S30, S25, S27, S07 |
| R-A04-038 threshold class for base detection | D-R05, D-R06 |
| R-A04-039..044 money-flow evidence, smart-money panel | S23; D-R20, D-R22, D-R25 |
| R-A04-045..048 evidence thresholds, non-US insider feeds, uniform breakout multiple | S23; D-C01, D-R22, D-R33, D-DEF-16, D-DEF-17 |
| [[institutional-tailwind]] | S02 |
| [[leverage-liquidation-cascade]] | S08, S28 |
| [[net-selling]], [[percentile-rank]] | S29 |
