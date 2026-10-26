---
id: PER-01
title: Active rule-based trader
layers: [CORE, METHOD, PROFILE, MACRO]
status: draft
sources: [S01, S05, S07, S13, S14, S15, S16, S17, S18, S19, S20, S23, S25, S29, S30]
decisions: [D-H, D-X, D-S14, D-C01, D-C02, D-C03, D-C04, D-C05, D-C06, D-C07, D-C08, D-C09, D-C10, D-C11, D-C12, D-C13, D-C15, D-C15b, D-C21, D-C23, D-C24, D-C25, D-C26, D-C27, D-C28, D-C29, D-OPEN-1, D-OPEN-2, D-OPEN-3, D-OPEN-4, D-R01, D-R02, D-R03, D-R04, D-R07, D-R08, D-R09, D-R11, D-R12, D-R14, D-R15, D-R16, D-R18, D-R20, D-R22, D-R24, D-R25, D-R28, D-R30, D-R31, D-R33, D-R34, D-R35, D-R36, D-R37, D-R39, D-R40, D-R41, D-R42, D-R43, D-R44, D-R45, D-DEF-18, D-DEF-23, D-DEF-25, D-DEF-36]
aspects_used: [A01, A02, A03, A04, A05, A06, A07, A08, A09, A10, A11, A12, A13]
---
# PER-01 — Active rule-based trader

Rules owned by other aspects are referenced by aspect and parameter or decision (e.g. "R-A07-* trend exit, D-C26"), because their numbers are assigned in parallel. A12/A13 rules are cited by number.

## 1. Profile & context
- A self-directed private investor with a brokerage account (US, EU, UK, APAC or Korea). They trade their own money in a taxable account and/or a [[tax-wrapper]].
- They follow the canonical [[follow-the-money]] method ([[three-step-system]]: scoreboard → basket → exit) under `PRF-follow-the-money`. They may instead choose a non-canonical profile: [[prf-beginner-index]] while learning, [[prf-momentum-rotation]] for a purely quantitative monthly approach (A13).
- **Time budget:** one fixed weekly session on a market-closed day, default Saturday (D-C28), of roughly 1–2 h. That is 2–3 h while learning (S13) and 3–5 h/week during the 90-day plan (S07). A monthly review is added (D-C04). On market days they do not trade by hand; alerts and resting orders do the work ([[daily-automation]]).
- **Experience range:** from "completed the 90-day plan" to experienced. They hold or watch 15–30 positions (S07) across industry baskets ([[basket]], D-C21) and occasional single stocks.
- **Tools expected:** charting with volume, SMAs and ATR, a broker supporting stop, market-on-open and limit-on-open orders ([[market-on-open-order]], D-R16), and [[price-alert]]s/[[volume-alert]]s. In this app: the scoreboard, watchlist, position and portfolio-exposure views, and the review log, plus the LLM coach.
- **Mindset:** observes what money has done instead of predicting ([[timing-the-market]] rejected). Accepts that only the [[three-outcomes]] are allowed and wants the system to protect them from the [[fourth-outcome]].

## 2. Goals
1. Own what institutional money is buying, i.e. industries on the green side of the scoreboard, and be out of what it is selling (A02, A04).
2. Enter only on confirmed setups (A06): a [[heartbeat-breakout]] on ≥2× volume, price above the rising 50-SMA, never below the 150-SMA (D-C06/C07, D-C01, D-H).
3. Have every exit decided before the buy: trend exit, protective stop and profit-taking (A07, D-X).
4. Keep every loss small: risk per position ≤ 1% of equity, and no single name or industry able to sink the portfolio (A08, A09; D-C09/C10, D-C11).
5. Spend about one session a week, make no intraday decisions, and get good sleep ([[stomach-test]]).
6. Get better at the process over time, measured by rule adherence rather than single-trade P/L (A12).

## 3. Pains & anti-goals (what the method protects them from)

| Pain / failure mode | Protection | Where |
|---|---|---|
| Good company in a bad industry falls anyway | Industry-first: buy only in green, top-RS industries | A02 `scoreboard.*` (D-C15/C16), A05 [[industry-first-selection]] |
| Buying a [[falling-knife]] or chasing an extended move | Entry checklist; close-confirmed entry; never buy below the 150-SMA; class-scaled no-chase threshold and earnings blackout; wait for the next base | A06 (D-C06/C07, D-R03, D-R07, D-R08), R-A12-058 |
| Small loss turning into a big loss ([[holding-and-hoping]], "it will come back") | Stop placed in the same sitting as the buy; stops only move up; automated trend exit | A07 (D-C12, D-C26), R-A12-051, R-A12-053 |
| Selling winners too early, or never selling losers ([[two-halves-of-loss]]) | Mechanical profit-taking + 150-SMA trail; discretionary sells never blocked but warned, journaled as rule deviations and reviewed next session (D-C29) | A07 (D-C12/C13, D-OPEN-4), R-A12-005 |
| Stop knocked out by noise ([[knocked-out]]) | Stop at the last swing low − 1 × ATR(14), validated against the volatility class (LOW/MEDIUM/HIGH/EXTREME); a wider stop means a smaller size; raised at each weekly review to the new last buyer area (D-R34) | A07/A08 (D-C08, D-X, D-R04, D-R11, D-R34) |
| Position too big, overnight [[gap]] | Risk-based sizing plus the overnight-gap weight cap | A08 `sizing.max_risk_pct` (D-C09/C10), [[overnight-gap-test]] (D-OPEN-3) |
| [[hidden-concentration]] (same bet through 4 funds) | Look-through exposure; sector/industry ≤ 25%, company ≤ 10% (look-through, D-R36), theme ≤ 30%, single foreign country ≤ 60%, contrarian scenario ≤ 15% (D-R45); buys into a breached bucket are blocked, a buy that would create a breach is warned | A09 (D-C11, D-R14, D-R36, D-R45) |
| Idle cash quietly eroding, or no cushion for life events | [[emergency-buffer]] outside the portfolio; eroding-cash flag; cash-like instruments | A09 (D-C24), A10 |
| Acting on headlines, macro stories, forecasts | Macro = Theses + Observations, bias only; forecasts shown as signals, not guarantees | A11 (D-C22), A03 (D-C25), R-A12-015, R-A12-057 |
| Screen-watching, emotional intraday trades, revenge trades | Weekly/monthly cadence; daily activity automated only; emotion tags in the journal | A12 R-A12-003/004, R-A12-054 |
| Changing rules mid-trade, "this time is different" | Signed rule set; revisions only in a session and never loosening open exits | R-A12-020…025, [[three-covenants]] |
| Tax tail wagging the dog | Taxes are never a decision input | R-A12-050 |

## 4. Responsibilities & decisions they make

| Step | The trader decides | The system decides / enforces (not overridable) | Key parameters they may set |
|---|---|---|---|
| **0. Setup** | Profile (A13); review day; parameter values in the PersonalRuleSet; personal rules (e.g. single-stock condition); trigger sheet and scenario plans; emergency-buffer months | Rule set must be signed before live trading (R-A12-020); values within ranges (R-A12-021); one active profile (R-A13-003) | `routine.weekly_review_day`; `cash.*` emergency buffer months (3–12, D-C24); `profile.active_id` |
| **1. Scoreboard** (A02) | Which green industries to research this week; drill-down level (default GICS Industry, D-R24); benchmark view (local vs global, D-C15b) | Status computation: green = RS > 0 and rising, red = RS < 0 and falling (D-C15/C16); top RS group (D-OPEN-1); local green gates, global red warns (D-R18); RS-deterioration flag + buy block (D-C27) | A02 `scoreboard.*` weights (3m/6m/12m default 40/30/30) and top-group share (default 20%), D-OPEN-1 |
| **2. Basket / selection** (A05, A06) | Basket vs single stock (default single-stock condition, D-DEF-18); which candidate from the watchlist; whether to keep the default 60/40 split (60% at the breakout, 40% reserved for a [[second-chance-entry]], D-R44) or disable it | Survival veto for single stocks (D-C03); entry checklist pass/fail (D-C06/C07); concentration block (D-C11) | A04 `volume.*` breakout multiple (≥2×, D-C01); A04 base minimum (3 months, D-C02); "rising" MA definition via A02 `scoreboard.ma_slope_window_sessions` and `scoreboard.ma_slope_flat_band_pct` (D-OPEN-2, confirmed D-R01); A08 risk % (0.5–1); A09 limits within ranges |
| **3. Exit** (A07) | Buyer-area level (conservative mode: lowest of the last 2–3 swing lows); whether to enable optional breakeven and gain-threshold raise rules; trim-to-cap items for gap-test breaches (D-R12); the manual sale of a physical gold holding when its alert fires (D-R39) | Stop placed with the buy; stops only up and raised to the new last buyer area at each weekly review (D-R34); any close below the 150-SMA fires the trend exit (no buffer, no slope, D-R35); close below the 150-SMA → next-session market-on-open sell with the broker stop live in parallel (D-R16); discretionary sells never blocked but journaled as rule deviations (D-C29); broker stop executes; first trigger wins; RS loss never auto-exits under canonical (D-C12, D-C26, D-C27) | A07 `exit.*` trend MA length (150, D-C05); conservative stop mode; profit matrix values (D-OPEN-4, confirmed D-R02; EXTREME row D-R31) |
| **Review** (A12) | Revisions after closed-trade review; profile switches (at least 13 weeks apart); dismissing or acting on flags | Session only while market closed; revision log; journal fields mandatory | `routine.*` settings; loss-review threshold is A08 `risk.fourth_outcome_review_drawdown_pct` (25%, range 15–25, D-DEF-36) |

## 5. Jobs-to-be-done / user stories

**US-01 Read the scoreboard.** As an active trader, I want to see industries ranked and coloured by relative strength, in my local and the global benchmark, so that I only research where money is arriving.
- AC1: Each industry shows its RS composite (3/6/12m weighted per D-OPEN-1, weekly close), its status green/neutral/red per D-C15/C16, and top-RS-group membership (R-A02-*). The default level is GICS Industry (74) with drill-up to industry groups and sectors and drill-down to sub-industries (R-A02-042, D-R24).
- AC5: Every industry shows its proxy and proxy type (ETF, index or equal-weight basket) and can be charted and filtered (R-A01-043..046, R-A02-044, D-R21).
- AC6: A "who is investing" panel per industry shows dated, sourced institutional evidence (ETF fund flows, 13F changes, insider and congressional trades, volume footprint) with its lag; it never changes the status (R-A02-043, R-A04-039..044, D-R20, D-R22).
- AC2: Local and global (MSCI ACWI, USD) views are shown side by side (D-C15b; R-A02-*). Local green gates buys; global red shows a warning only (R-A02-041, D-R18).
- AC3: An industry flagged for RS deterioration (D-C27) shows the flag and "new buys blocked" (R-A12-013).
- AC4: The view labels itself a record of past flows, not a forecast (R-A12-056).

**US-02 Build a watchlist of baskets.** As a trader, I want to add the basket or industry proxy for a green industry, with alerts, so that the system watches for me.
- AC1: The basket's look-through holdings and the instrument's market availability are shown (R-A01-*, R-A05-*, R-A09-*).
- AC2: Adding an entry offers the alerts "crosses above 50-SMA, daily, once per day" and a volume alert at the A04 multiple (R-A12-009; R-A04-*).
- AC3: An instrument from a red industry can be watched but is marked "not buyable" under the canonical profile (R-A02-*, R-A13-020).

**US-03 Check an entry.** As a trader, I want a pass/fail entry checklist per candidate so that I buy only confirmed breakouts.
- AC1: The checklist shows: heartbeat base ≥ 3 months (D-C02, R-A04-*), breakout volume ≥ 2× the 50-day average (D-C01), price above the rising 50-SMA (D-OPEN-2), price not below the 150-SMA (D-C06/C07, R-A06-*).
- AC2: For single stocks, a failed survival check (cash runway ≥ 2 years without dilution) vetoes the buy (D-C03, R-A05-*).
- AC3: Record quarter and the Quality / Growth / Cash Flow scorecard (lens-dependent weights, pass ≥ 60; valuation as context only) are shown as optional confirmations only (D-C03, D-R28, D-R29, R-A05-*).
- AC4: A buy cannot be placed outside a review session (R-A12-003); an entry armed in a session is bought in the next session after a confirmed close, unless the open exceeds the class no-chase threshold or an earnings blackout applies (R-A06-017, R-A06-019, R-A06-030).
- AC5: Strong insider or institutional buying (≥ 2 independent positive sources within 90 days, D-R33) raises the watchlist priority but never passes a check (R-A06-035, D-R25).
- AC6: A fading-volume pattern on a setup shows a warning but does not block arming (R-A06-038, D-R44).
- AC7: By default 60% of the sized position is bought at the breakout and 40% is reserved for a pullback to the ceiling; both tranches together stay within the risk budget (R-A06-037, D-R44).

**US-04 Size a position.** As a trader, I want the system to compute shares from my risk %, stop and volatility class so that one loss costs ≤ 1%.
- AC1: shares = equity × risk% / (entry − stop), with risk% within 0.5–1 (D-C09/C10, R-A08-*); whole shares unless the broker supports fractional shares (R-A08-035, D-R40); the first 3 live trades use 0.5% (D-DEF-25).
- AC2: The weight is capped by the overnight-gap test (stock 30% gap → max loss 2% ⇒ ≤ 6.67%; fund 15% ⇒ ≤ 13.33%, D-OPEN-3, R-A08-*).
- AC3: A stop wider than the volatility class band reduces the size. The system never suggests a tighter stop (D-C08, R-A07-*, R-A08-*). An EXTREME-class single stock is sized at 0.5% risk at most (R-A08-031, D-R11).
- AC4: A buy into an already-breached concentration bucket (sector/industry 25%, position 10%, user-set in range) is blocked; a buy that would create a breach shows a warning with the suggested maximum (D-C11, D-R14, R-A09-012).

**US-05 Place buy and exit together.** As a trader, I want the breakout entry (close-confirmed by default) and its protective stop created in one step so that I never hold a position without an exit.
- AC1: Order creation fails unless a protective stop at the last buyer area (swing low) − 1 × ATR(14) is attached (D-C08, D-R04, R-A07-010).
- AC2: A TradeRecord with rationale, stop plan, size, risk % and emotional state is created (R-A12-030).
- AC3: An open live position without a resting stop raises a critical alert (R-A12-053).

**US-06 Let exits run automatically.** As a trader, I want exits to fire without me so that I don't need to watch the market.
- AC1: A daily close below the 150-SMA (the 50-SMA while fewer than 150 sessions exist) generates a market-on-open sell order for the next session, with the broker stop live in parallel (D-C26, D-R16, D-R17, R-A07-*, R-A12-004).
- AC2: The broker stop executes automatically, and the first trigger to fire wins. Profit-taking may be partial (D-C26, R-A07-*).
- AC3: No snooze/skip action exists on an exit trigger (R-A12-051).

**US-07 Trail and take profits.** As a trader, I want weekly stop-raise suggestions and profit-taking rules so that I keep gains without guessing.
- AC1: At each weekly review the stop is raised to the new last buyer area (swing low − 1 × ATR(14)) when that is higher; a stop is never lowered (D-C12, D-R34, R-A07-017).
- AC2: Take half on an extension above the 50-SMA per the volatility-class × market-regime matrix, or, only in a bearish regime, on a quick win of 4/5/6/6% by class; the remainder exits below the 50-SMA; otherwise the 150-SMA trail applies (D-C12/C13, D-OPEN-4, D-R02, D-R15, R-A07-*).
- AC3: Breakeven-after-rally and the gain-threshold (+10%) raise are off by default and can be enabled in the rule set (D-C12/C13).
- AC4: A physical gold holding has no broker stop; its stop and trend exit are price alerts that create a manual sale task, and it is listed as a sanctioned exception (R-A07-043, D-R39).

**US-08 Run my Saturday review.** As a trader, I want a guided weekly session in a fixed order so that I finish all decisions in one sitting.
- AC1: Steps follow PR-A12-01. Mandatory steps must be marked done before closing (R-A12-006/007).
- AC2: Every fired alert and every open position's stop is presented (R-A12-008).
- AC3: Positions with a drawdown from entry >= 25% (A08 `risk.fourth_outcome_review_drawdown_pct`) are flagged for review (R-A12-033); positions with an insider-flip review flag (R-A07-041) and gap-test trim-to-cap items (R-A08-034) are listed.
- AC5: Discretionary sells made since the last session are listed as rule deviations with their reasons for review (R-A12-005, D-C29).
- AC4: Decisions and evidence are written to the ReviewLog (R-A12-012).

**US-09 Run my monthly review.** As a trader, I want a monthly RS ranking, concentration audit and cycle check so that I catch slow deterioration.
- AC1: RS deterioration per D-C27 sets a flag and blocks buys, with no auto-sell under canonical (R-A12-013).
- AC2: The look-through concentration audit lists breaches (R-A09-*).
- AC3: The cycle phase is shown as bias with evidence and confidence and produces no orders (R-A03-*, R-A12-015, D-C25).
- AC4: Thesis invalidation signs are checked (R-A11-*, R-A12-014).

**US-10 Keep a signed rule set.** As a trader, I want to write, sign and version my rules so that a signed rule is harder to break than a thought.
- AC1: Live mode requires a signed rule set (R-A12-020).
- AC2: Revisions happen only in a market-closed session and are logged with a reason. A revision citing a closed-trade review links that trade (R-A12-023, R-A12-025).
- AC3: Revisions never loosen exits on open positions (R-A12-024).

**US-11 Review a closed trade.** As a trader, I want each closed trade judged on process first so that I improve the system, not my luck.
- AC1: rules_followed is required before P/L is shown (R-A12-031, R-A12-073).
- AC2: A fourth outcome opens a mandatory review item (R-A12-032).

**US-12 Ask the coach.** As a trader, I want an LLM coach that answers from my rules with my numbers so that I get feedback without being talked out of my system.
- AC1: Answers cite the rules and parameters applied and show the active profile (R-A12-070, R-A13-008).
- AC2: Requests to break hard rules are declined with the rule restated (R-A12-071).
- AC3: No certainty claims and no price targets or ratings. Backtests are labelled hypothetical, with source, or "unattributed" when no named study exists (R-A12-076, R-A12-079, R-A12-080).
- AC4: Intraday decision requests are deferred to the next session (R-A12-081).

**US-13 Try an alternative profile.** As a trader, I want to switch to the momentum-rotation profile, or start with the beginner index profile, so that the strategy fits my time and skill.
- AC1: The switch only happens in a review session (R-A13-061).
- AC2: Pending entry orders are cancelled and protective stops kept (R-A13-062). Open positions keep their entry-profile exits (R-A13-063).
- AC3: Paper mode is suggested (R-A13-064). Profile backtests are shown as hypothetical (R-A13-013).
- AC4: Under the beginner profile, fixed allocation 2–5% is treated as size, with risk capped at 1% (R-A13-031/032, D-S14).

**US-14 Practise on paper.** As a learner, I want paper trading under identical rules and a 90-day path so that I can prove the process before risking money.
- AC1: Paper trades follow the same rules and are excluded from live performance (R-A12-040); paper fills use the next-session open plus class slippage (R-A12-084, D-R41).
- AC2: The live-gate warning lists the unmet criteria (≥ 6 trades, ≥ 1 loss with stop respected) (R-A12-041).
- AC3: Skill-gap bands route the plan (R-A12-043…045).

**US-15 Manage cash and safe assets.** As a trader, I want my emergency buffer separate and idle cash flagged so that I neither starve my life nor let cash erode.
- AC1: The buffer (default 6 months, range 3–12) is excluded from investable equity (D-C24, R-A09-*).
- AC2: Investable idle cash is flagged "eroding" when the real yield is < 0. T-bill or short-Treasury ETFs count as cash-like (D-C24, R-A09-*, R-A10-*).

## 6. Weekly / monthly journey

| When | Activity | Process |
|---|---|---|
| Mon–Fri (market open) | Nothing manual. Alerts are evaluated, resting stops and buy-stops execute, system exits are generated; non-urgent ideas are queued | PR-A12-03; A07 exit processes (D-C26) |
| Saturday (default, D-C28) | Alerts → scoreboard → MAs → exits/stop ratchet → health flags → candidates and entry checklist → sizing and concentration → orders (buy + stop) → watchlist → journal and rules | PR-A12-01; A02 scoreboard update; A06 entry check; A07 stop ratchet; A08 sizing; A09 headroom |
| First session after month end | Monthly block: RS ranking, RS deterioration, concentration audit, cycle check, thesis signs, behaviour metrics; profile rebalance if momentum | PR-A12-02; A13 PR-A13-03; A03 cycle assessment; A09 concentration audit; A11 thesis review |
| On close of a trade | Process-first trade review; revision candidates go to the next session | PR-A12-06 |
| On demand, in a session | Rule-set revision; profile switch | PR-A12-05; PR-A13-02 |
| Onboarding | Skill gap → 90-day plan (Foundation → Application → Execution) → live | PR-A12-04; PR-A13-01 |

## 7. Permissions & constraints

**Hard rules the trader cannot override** (any profile; R-A13-006):
- A protective stop is set in the same sitting as the buy. Stops only move up (D-C12; R-A07-*).
- Price-based exits are automatic and independent, and the first to fire wins (D-C26; R-A07-*). Exit triggers have no snooze (R-A12-051).
- Risk per position ≤ 1% of equity, user range 0.5–1 (D-C09/C10; R-A08-*); ≤ 0.5% for an EXTREME-class single stock (D-R11). The overnight-gap cap applies (D-OPEN-3).
- A breached concentration bucket blocks new buys into it; a buy that would create a breach is warned, not blocked (D-C11, D-R14; R-A09-*). Total open risk is displayed, not capped (D-R09).
- The survival veto applies to single stocks (D-C03; R-A05-*).
- Canonical profile: no buy unless the entry checklist passes (D-C06/C07; R-A06-*). No buys in industries flagged for RS deterioration (D-C27).
- No margin, no leverage, no leveraged ETFs (R-A08-*).
- Emergency buffer kept outside the investable portfolio (D-C24).
- Discretionary entries, rule changes and profile switches happen only in a market-closed session (R-A12-003, R-A13-061). A discretionary sell between sessions is never blocked, but it needs a mandatory reason, is journaled as a rule deviation and is reviewed in the next weekly session (R-A12-005, D-C29). Live trading requires a signed rule set (R-A12-020). Rule changes never loosen open exits (R-A12-024).
- Journal records are mandatory and append-only (R-A12-030, R-A12-034). Taxes are never a decision input (R-A12-050).
- Exactly one active profile per portfolio (R-A13-003).

**Parameters the trader can set** (within owning-aspect ranges, recorded in the signed rule set):
- Risk % per position (0.5–1, A08), position cap (3–10%), sector/industry cap (15–40%) (A09, D-C11).
- Emergency-buffer months (3–12, D-C24); review day (any market-closed day, D-C28).
- Stop mode: standard or conservative buyer area (D-C08). Optional profit/trailing variants: breakeven, weekly +10% raise (D-C12/C13). Optional fractional-Kelly mode (D-C09/C10).
- Scoreboard weights and top-group share (D-OPEN-1), breakout volume multiple (≥ 2×, D-C01), base minimum (D-C02). MA lengths are not trader-settable (150 canonical, D-C05); only the regime-filter length (200d/10m) can differ, via a profile (A13).
- Confirmed defaults: rising-MA slope definition (D-OPEN-2, D-R01), profit-taking matrix with regime definition (D-OPEN-4, D-R02, EXTREME row D-R31) and stop-raise mode structure (D-R34). Practitioner defaults D-DEF-01…42 apply until the user reviews them (decisions.md).
- Theme (30%), country (60%) and scenario (15%) caps within their ranges (D-R45).
- Active profile and that profile's own parameters (A13 §4).
- Free-text personal rules, trigger sheet, scenario plans (R-A12-027).

## 8. Information needs per screen/view

| View | Must show | Rules/aspects |
|---|---|---|
| **Scoreboard** | Industries (default GICS Industry level, drill-up/down) with proxy and proxy type, RS composite, 3/6/12m components, RS trend vs its 50d average, status colour, top-RS-group marker, local/global benchmark toggle with global-red warning, day/week/month heatmap view, RS-deterioration flags, "who is investing" smart-money panel per industry (fund flows, 13F, insider, congressional, volume footprint; dated, with lag), held/watched markers, as-of date (weekly close) | A02 (D-C15/C16, D-C15b, D-OPEN-1, D-R18, D-R24), A01 (D-R21), A04 (D-R22, D-R25), D-C27, R-A12-056 |
| **Watchlist** | Per entry: industry and status, basket/proxy, volatility class (threshold basis), base length and major-base tag (≥18 months), ceiling/breakout level, distance to ceiling vs the class setup distance, no-chase limit, next earnings date and blackout, 50-SMA and 150-SMA state and slope, last volume multiple, checklist pass/fail with reasons and warnings, survival check (stocks), scorecard pillars (optional), smart-money evidence and priority, planned entry, stop, size and risk %, alert status | A04, A05, A06, A08 (D-R05, D-R07, D-R08, D-R25); R-A12-009 |
| **Position** | Entry date and price, entry profile and rule-set version, current stop and its history (monotonic), buyer areas (swing lows) and ATR offset, volatility class (ATR%) and stop validation, distance to 150-SMA (or 50-SMA substitute) and 50-SMA, active exit triggers with state, profit-taking stage (quick win only in bearish regime), P/L, risk % now, weight, gap-test status and trim-to-cap item, review flags incl. insider flip, smart-money evidence, alerts, journal entries | A07 (D-X, D-C08, D-C12/C13, D-C26, D-R04, D-R15, D-R17, D-R25), A08 (D-R10, D-R12), R-A12-030, R-A13-007 |
| **Portfolio exposure** | Equity and investable equity (excluding the emergency buffer); look-through exposure by sector, industry, position, country and theme against limits; headroom per bucket; blocked buckets and concentration warnings; total open risk (Σ risk at stop, display only, no cap, D-R09); cash and cash-like with eroding flag; emergency-buffer shortfall warning (no block, D-R13); active profile banner | A09 (D-C11, D-C24, D-R13, D-R14), A08 (D-R09), A10, R-A13-008 |
| **Review** | Session checklist (PR-A12-01/02) with step status, agenda of queued items, fired alerts, flags (loss review, missing stop, RS deterioration, concentration, fading volume, thesis signs), orders to place, rule set (current version), revision log, closed-trade reviews, monthly metrics (adherence rate, emotional-trap tags, outcome classes, win rate, avg gain/loss) | A12, A03 (cycle bias), A11 (theses) |
| **Coach panel** | Active profile, cited rules and parameters, computed numbers, evidence and confidence for any assessment, hypothetical labels | R-A12-070…083, R-A13-008, R-A13-013 |

## 9. Success metrics
- **Rule adherence:** share of closed trades with rules_followed = true. Target trend: rising; reviewed monthly (R-A12-054).
- **No fourth outcome:** count of closed trades classified `FOURTH_OUTCOME` (A08); `LOSS_EXCEEDED_PLAN` counted separately. Target 0.
- **Realised risk discipline:** maximum risk % at entry across trades ≤ the configured cap. Target 100% compliance (A08).
- **Exit integrity:** share of positions that always had a resting stop (R-A12-053), and the number of downward stop moves (must be 0, D-C12).
- **Cadence:** weekly sessions held out of scheduled sessions (S07 guide: ≥ 10 of 12), and monthly reviews held.
- **Time on task:** session duration within the user's budget (informational).
- **Concentration:** months with no limit breach at audit (A09).
- **Learning:** skill-gap total improvement from week 1 to week 12, and gates passed (A12).
- **Outcome (secondary, never primary):** win rate, average gain vs average loss, return vs a passive index fund over the same period (S07 90-day review).

## 10. Traceability to aspects

| Persona element | Aspects |
|---|---|
| Scoreboard, benchmarks, RS deterioration | A02, A01 (classification, D-C14) |
| Cycle bias, style regime | A03 |
| Heartbeat, volume multiples, fading volume | A04 |
| Basket selection, survival check, scorecards | A05 |
| Entry checklist, breakout buy orders | A06 |
| Exit triggers, stops, profit-taking, precedence | A07 |
| Risk-based sizing, gap test, volatility class | A08 |
| Look-through exposure, limits, emergency buffer, cash | A09 |
| Cash-like instruments, real yield | A10 |
| Theses, observations, invalidation signs | A11 |
| Routine, rule set, journal, paper, 90-day plan, coach | A12 |
| Profiles, switching, parameter comparison | A13 |
