---
id: A12
title: Process, Routine & Psychology
context: CTX-E
layers: [CORE, METHOD]
status: draft
sources: [S01, S04, S05, S06, S07, S10, S13, S14, S15, S18, S20, S22, S23, S25, S27, S28, S29, S30]
decisions: [D-C04, D-C28, D-C26, D-C27, D-C29, D-C25, D-C23, D-C12, D-C09, D-C01, D-C03, D-S14, D-R03, D-R12, D-R16, D-R34, D-R41, D-DEF-36, D-DEF-37, D-DEF-38]
depends_on: [A02, A03, A06, A07, A08, A09, A11, A13]
---
# A12 — Process, Routine & Psychology

## 1. Purpose & scope
Covers the *operating discipline* around the method:
- the weekly review on a market-closed day, the monthly review, and daily activity that is automated only (D-C04, D-C28);
- the written, signed personal rule set (`PersonalRuleSet`), how it is changed, and its revision log;
- the trade journal (`TradeRecord`) and review log (`ReviewLog`), paper trading, and the 90-day onboarding/learning path with the skill-gap assessment;
- behavioural rules against known biases, and hard behaviour rules for the LLM coach.

Excluded (owned elsewhere, referenced only): scoreboard computation (A02), cycle-phase scoring (A03), volume thresholds (A04), entry checklist (A06), exit triggers, stop placement and precedence (A07), sizing and risk caps (A08), concentration limits (A09), theses and observations (A11), strategy-profile definitions and switching (A13).

## 2. Concepts
- [[three-step-system]]: the fixed order of every review: scoreboard → basket → exit.
- [[follow-the-money]]: observe where money has gone, do not predict. This is how the coach frames every answer.
- [[weekly-review]]: the one weekly session in which all discretionary decisions are made.
- [[monthly-review]]: RS ranking, concentration audit and cycle check, held once a month.
- [[daily-automation]]: on market days only alerts, resting orders and system-generated exit orders run.
- [[price-alert]], [[volume-alert]]: the "alert that does the watching" ("A rule you have to remember is not a rule. It is a hope." S13).
- [[trading-plan]]: the written, signed, dated personal rule set. Its entity is `PersonalRuleSet`.
- [[trigger-sheet]]: signal → action pairs written in advance. Part of the rule set.
- [[trade-journal]]: the per-trade record used for process review.
- [[paper-trading]]: simulated trading under identical rules.
- [[ninety-day-plan]], [[learning-levels]]: the onboarding path (Foundation → Application → Mastery).
- [[skill-gap-assessment]]: self-rating of five skills that routes the learner through the plan.
- [[emotional-trap]], [[holding-and-hoping]], [[two-halves-of-loss]], [[timing-the-market]]: the bias catalogue.
- [[three-covenants]] (A07): "this time is never different" is the behavioural core of exit discipline.
- [[three-outcomes]], [[fourth-outcome]], [[stomach-test]] (A08): journal outcome classes and the review trigger.
- [[investor-vs-trader]]: same rules at different speeds. A faster trader needs wider exits and smaller positions (see A08).
- [[speedboat-advantage]], [[crowded-trade]]: context concepts used in coaching only. They are not trading rules.
- [[rs-deterioration]], [[concentration-audit]], [[phase-bias]], [[invalidation-sign]]: inputs to the monthly review.
- [[strategy-profile]]: the active profile (A13) decides which rule families the routine runs.

## 3. Entities

| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Routine | id, portfolio_id | ref | one weekly + one monthly per Portfolio | Portfolios of one household keep separate Routines; they MAY share a review day (R-A12-086) |
| | kind | enum {weekly, monthly, daily_automation} | | |
| | day | weekday | weekly: must be a closed day of the portfolio's primary Market (R-A12-002) | default `routine.weekly_review_day` |
| | steps | ordered list of step codes | fixed order (PR-A12-01/02) | |
| ReviewSession (ReviewLog entry) | id, routine_id, started_at, ended_at | timestamp | started_at must fall while market is closed | the ReviewLog is the append-only list of sessions |
| | kind | enum {weekly, monthly} | a monthly session runs inside a weekly session | |
| | step_results | list {step_code, status ∈ {done, skipped, n/a}, note} | every step has a status | |
| | orders_placed, stops_raised, alerts_reviewed | lists of refs | | |
| | flags_raised | list {type, target_ref} | types: rs_deterioration, concentration_breach, loss_review, missing_stop, thesis_sign_turned, fading_volume, rule_deviation | |
| | decisions | list {text, evidence_refs} | written before session close (R-A12-012) | |
| PersonalRuleSet | id, portfolio_id, version | int ≥ 1 | exactly one `active` version per Portfolio | the glossary's [[trading-plan]] |
| | profile_id, profile_version | ref A13 | must reference the portfolio's active StrategyProfile | |
| | parameter_values | map param → value | each within its effective range (R-A12-021) | user-settable parameters only |
| | personal_rules | list {code, text, category ∈ {scoreboard, buy, sell_risk, size, process}} | free text; cannot contradict hard rules | e.g. "single stock only when …" (S13) |
| | triggers | list {signal, threshold, action} | the [[trigger-sheet]] | S06 |
| | scenario_plans | list {scenario, response} | scenarios: market_fall_50_78, thesis_slower_payoff, red_day | S27, S10, S29 |
| | signature | {signer_name, signed_at, content_hash} | required for status `signed` | |
| | status | enum {draft, signed, superseded} | | |
| RuleSetRevision | id, ruleset_id, from_version, to_version | int | append-only | the revision log |
| | changes | list {field, old, new} | non-empty | |
| | reason_category | enum {closed_trade_review, scheduled_review, profile_switch, onboarding} | | R-A12-025 |
| | reason_text, linked_trade_ids | text, refs | linked_trade_ids required for closed_trade_review | |
| | applies_to_open_positions | bool | true only if the change does not loosen exits or raise risk (R-A12-024) | |
| TradeRecord (Journal) | id, portfolio_id, position_id | ref | one per Position (and per paper Position) | |
| | mode | enum {paper, live} | | |
| | profile_id, profile_version, ruleset_version | ref | frozen at entry | |
| | entry_rationale | list of checklist item codes (A06) + text | non-empty | which signals were present |
| | stop_plan | {method, price, distance_pct, volatility_class} | from the ExitPlan (A07) | |
| | size | {shares, weight_pct, risk_pct} | risk_pct ≤ the A08 cap | |
| | emotional_state_entry, emotional_state_exit | enum list of [[emotional-trap]] tags + text | | |
| | wanted_vs_system | text | | S07 "what you wanted to do vs. what the system said" |
| | exit | {trigger (A07 ExitTrigger), date, price} | | |
| | outcome_class | enum {BIG_WIN, SMALL_WIN, SMALL_LOSS, LOSS_EXCEEDED_PLAN, FOURTH_OUTCOME} | exactly the A08 `Position.outcome` enum (R-A08-027) | see A08 [[three-outcomes]] |
| | pnl_abs, pnl_pct | money, % | | |
| | rules_followed | bool + list {rule_ref, followed: bool, note} | required at close (R-A12-031) | |
| | known_weaknesses | text | | S10 "write those flags down" |
| LearningPath | id, user_id, start_date, phase | enum {foundation, application, execution, completed} | | the [[ninety-day-plan]] |
| | weekly_effort_h | number | informational | S07 3–5 h |
| | milestones | list {gate_code, criteria[], met: bool, met_at} | | PR-A12-04 |
| | extensions | list {phase, weeks, reason} | | |
| SkillAssessment | id, user_id, taken_at | timestamp | | |
| | ratings | map {volume_analysis, heartbeat_pattern, record_quarters, risk_management, emotional_discipline} → int 1–10 | all 5 required | S07 skills; total and band |
| | extra_ratings | map {scoreboard_reading, exit_discipline} → int 1–10 | optional | coaching focus only, not in total (R-A12-085, D-DEF-37) |
| | total, band | int 5–50, enum {advanced, intermediate, beginner, starting_from_zero} | computed (§7) | |
| Alert | id, instrument_id, condition, timeframe, frequency, created_at, active | | timeframe daily, frequency once per day (default) | shared entity; also used by A07/A04 |

ReviewSession lifecycle: `scheduled → open (market closed) → closed`. When closed, the session is immutable and corrections are appended as new notes.
PersonalRuleSet lifecycle: `draft → signed (active) → superseded`. A new version starts as `draft` and replaces the active one only when signed.

## 4. Parameters

| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `routine.weekly_review_day` | Saturday | any weekday on which the portfolio's primary market is closed | weekday | D-C28, D-C04; S23 (moved from Sunday), S30 |
| `routine.weekly_review_duration_h` | informational, not enforced | — | h | S13 ~1 h (2–3 h while learning); S23/S25 2 h; S07 15–30 min |
| `routine.monthly_review_slot` | first weekly session after the last trading day of the month | fixed | — | D-C04 (review finding: one monthly review per month-end) |
| `routine.daily_mode` | `automated_only` | fixed | enum | D-C04 |
| `routine.alert_frequency` | once per day | once per day | — | S13, S23 |
| `routine.alert_timeframe` | daily bars | daily | — | S13 |
| `routine.paper_trades_min_before_live` | 6 | ≥ 0 (user may lower, soft rule) | trades | S07 Month 2 gate |
| `routine.paper_losing_trade_required` | true | bool | — | S07 Month 2 gate ("≥1 losing paper trade with stop respected") |
| `routine.max_checks_per_day_first_live` | 1 | ≥ 1 | views/day | S07 week 9 |
| `routine.skill_gap_bands` | advanced 40–50; intermediate 25–39; beginner 10–24; starting_from_zero 5–9 | fixed | points | S07 |
| `routine.month1_extension_weeks` | 2 | fixed | weeks | S07 (beginner band) |
| `routine.month2_extension_weeks` | 2–4 (user picks) | 2–4 | weeks | S07 |
| `routine.ninety_day_min_trades` | 12 | ≥ 0 | trades (paper + live) | S07 completion criteria |
| `routine.ninety_day_min_research_weeks` | 10 of 12 | 0–12 | weeks | S07 |
| `routine.weekly_effort_h` | 3–5 | informational | h/week | S07 (timelines scale proportionally) |
| `routine.paper_fill_model` | next-session open + slippage; stops at the worse of stop price and gap open | fixed | — | D-R41 |
| `routine.paper_slippage_pct[low/medium/high/extreme]` | 0.05 / 0.1 / 0.2 / 0.4 | ≥ 0 (stricter only) | % of price, against the trader | D-R41 |
| `routine.extra_skills` | scoreboard_reading, exit_discipline | fixed | — | D-DEF-37 |

Parameters of other aspects that the routine reads: A02 `scoreboard.*` (status, top RS group), D-C27 RS deterioration (red: immediate buy block + flag at the next weekly session; top-group drop: 2 consecutive monthly reviews), A04 `volume.*` (volume-alert multiple, D-C01 ≥2×), A07 `exit.*` (trend MA 150, alert on cross below), A06 `entry.*` (50-SMA alert), A08 `sizing.max_risk_pct`, `sizing.risk_pct`, `sizing.initial_live_risk_pct`, `sizing.initial_live_trades_count` (3) and `risk.fourth_outcome_review_drawdown_pct` (loss review, 25, range 15–25, D-DEF-36), A09 `portfolio.*` concentration limits.

## 5. Rules

### 5.1 Cadence: weekly, monthly, daily
- **R-A12-001** (hard, METHOD): Every Portfolio in paper or live mode MUST have exactly one weekly Routine scheduled on `routine.weekly_review_day`. _Sources: S13, S23, S25, S30. Decision: D-C04, D-C28_
- **R-A12-002** (hard, METHOD): The weekly review day MUST be a day on which the primary Market of the Portfolio is closed. A regular trading weekday MUST be rejected. _Sources: S13 (the method's review is done while the market is shut), S25. Decision: D-C28_
- **R-A12-003** (hard, METHOD): New buy orders, new or modified entry orders, PersonalRuleSet revisions and profile switches (A13) MUST only be created inside an open ReviewSession while the market is closed. _Sources: S13, S25 "He does not buy or sell during the week", S18, S20 "Make switching decisions when markets are closed". Decision: D-C04_
- **R-A12-004** (hard, METHOD): Outside a ReviewSession the system MUST run only [[daily-automation]]: alert evaluation, resting broker orders (protective stops; variant breakout buy-stops placed in a session), the next-session orders of entries pre-authorised in a session as close-confirmed triggers (A06 R-A06-030, D-R03), and the system-generated exit orders defined by A07, e.g. a daily close below the 150-SMA producing a sell order for the next session (D-C26). These automated exits MUST NOT wait for the next review. _Sources: S13, S23, S25. Decision: D-C04, D-C26_
- **R-A12-005** (hard, METHOD): A discretionary sell outside a review session that no exit trigger requested MUST NOT be blocked, because reducing risk is always permitted. Before sending it the system MUST show a [[two-halves-of-loss]] warning and require a reason (mandatory, non-empty). The sell MUST be journaled as a `rule deviation` with that reason and MUST be added as a review item to the next weekly session. Discretionary *buys* between reviews stay blocked (R-A12-003). _Sources: S23 "Half the money is lost in the selling, and half in the not selling", S13, S25. Decision: D-C29_
- **R-A12-006** (soft, METHOD): The weekly review SHOULD run its steps in the fixed order of PR-A12-01, "same day, same order". _Sources: S30, S13, S15_
- **R-A12-007** (hard, METHOD): Each ReviewSession MUST record a status for every step. A session cannot be closed while a mandatory step (PR-A12-01 steps 1, 4, 5, 8) is not `done`. _Sources: S07 weekly review protocol, S13, S23_
- **R-A12-008** (hard, METHOD): Every weekly review MUST check every alert fired since the previous session and the ExitPlan and stop of every open Position. Stop raises follow A07 (stops only move up, D-C12). _Sources: S13, S23, S07_
- **R-A12-009** (soft, METHOD): Every open Position SHOULD carry a [[price-alert]] "close crosses below 150-SMA, daily, once per day", and every watched basket SHOULD carry "crosses above 50-SMA, daily, once per day" plus a [[volume-alert]] at the A04 multiple. Alert creation is recorded with its date. _Sources: S13, S23, S07. Decision: D-C01, D-C05_
- **R-A12-010** (soft, METHOD): The system SHOULD NOT send intraday price notifications beyond configured alerts and order fills. During the first live trades, position views SHOULD be limited to `routine.max_checks_per_day_first_live`. _Sources: S14 "Set orders and walk away", S07 week 9_
- **R-A12-011** (hard, METHOD): A monthly review MUST run exactly once per month-end, inside the first weekly session after the last trading day of that month (`routine.monthly_review_slot`); two monthly reviews can therefore fall in the same calendar month (e.g. Sat 2026-10-03 for September and Sat 2026-10-31 for October). It covers: RS ranking of industries (A02), the [[concentration-audit]] (A09), and the cycle check (A03). _Sources: S16, S17, S19, S20, S05. Decision: D-C04_
- **R-A12-012** (hard, METHOD): Every decision taken in a review session MUST be written to the ReviewLog together with its evidence references before the session closes. _Sources: S18 "Have I written the decision and the evidence while markets are closed?", S20_
- **R-A12-013** (hard, METHOD): [[rs-deterioration]] follows D-C27 (A02 R-A02-015, R-A02-020..021): an industry that turns red is blocked for new buys immediately and gets a review/reduce flag at the next weekly session; an industry outside the [[top-rs-group]] at 2 consecutive monthly reviews gets the same flag and buy block at that monthly review. Under the canonical profile the flag MUST NOT generate a sell order (A13 may override, see R-A13-045). _Sources: S20. Decision: D-C27_
- **R-A12-014** (soft, MACRO): The monthly review SHOULD check the [[invalidation-sign]]s of every active Thesis (A11). One turned sign → re-check position size (no full sale implied). All signs turned → flag the thesis as materially weakened. _Sources: S28 "check them once a month (not hourly)"_
- **R-A12-015** (hard, CORE): The cycle-check result MUST be used only as [[phase-bias]]. No order may be generated from a cycle phase or a macro thesis alone. _Sources: S18 hard rule 6, S20. Decision: D-C25_

### 5.2 Personal rule set
- **R-A12-020** (hard, METHOD): A Portfolio MUST NOT be in live mode unless it has an active PersonalRuleSet with status `signed`. Without one, only paper mode is allowed. _Sources: S14 "If rules are not written and followed exactly, do not trade live capital", S13, S30_
- **R-A12-021** (hard, METHOD): Every value in `parameter_values` MUST lie within the effective range: the owning aspect's allowed range intersected with the active profile's narrowed range (A13). Hard rules MUST NOT appear as editable fields. _Sources: S13 template, S23, S30. Decision: D-C09, D-C11_
- **R-A12-022** (hard, METHOD): Signing records signer name, timestamp and a content hash. Any change creates a new version that needs a new signature, and earlier versions stay immutable. _Sources: S13 "a signed rule is much harder to break than a thought", S30_
- **R-A12-023** (hard, METHOD): A rule-set revision MUST be created only inside a ReviewSession while the market is closed. _Sources: S13, S14, S20_
- **R-A12-024** (hard, METHOD): A revision applies to new entries. It applies to open Positions only if it does not loosen their exit or raise their risk: no lower stop, no disabled exit trigger, no higher risk %, no wider stop offset. Otherwise open Positions keep the rule-set version frozen in their TradeRecord. _Sources: S14 "Changing rules mid-trade … is forbidden". Decision: D-C12_
- **R-A12-025** (hard, METHOD): Each RuleSetRevision MUST record its field changes, `reason_category` and reason text. A `closed_trade_review` revision MUST link at least one closed and reviewed TradeRecord. _Sources: S14 "Update the written rules only after a trade is closed and reviewed", S23 "Rewrite this page whenever a rule turns out to be wrong"_
- **R-A12-026** (soft, METHOD): The active rule set SHOULD be shown during every weekly review (step 10) and kept visible next to the order screen. _Sources: S13 "keep beside order screen", S30_
- **R-A12-027** (soft, METHOD): The rule set SHOULD contain scenario plans for a 50–78% market fall, a slower-than-expected thesis payoff, and a "red day", plus a trigger sheet of signal → action pairs written in advance. _Sources: S27, S10, S29 "Panic makes a terrible fund manager", S06_

### 5.3 Journal & review log
- **R-A12-030** (hard, METHOD): Every Position, paper or live, MUST have a TradeRecord created at order placement. It contains entry rationale, stop plan, size (shares, weight %, risk %), profile and rule-set version, emotional state at entry, and wanted-vs-system note. _Sources: S07 "Every trade documented with: entry rationale, stop placement, position size, outcome", S14 checklist_
- **R-A12-031** (hard, METHOD): A TradeRecord cannot be closed without `rules_followed` (overall and per rule) and outcome. The process question "were the written rules followed?" is answered before P/L is displayed. _Sources: S14 "Did you follow the written rules?" is more important than "Did you make money today?"_
- **R-A12-032** (soft, METHOD): Closed trades SHOULD be classified per A08 [[three-outcomes]]. A `FOURTH_OUTCOME` or `LOSS_EXCEEDED_PLAN` MUST open a mandatory review item in the next weekly session. _Sources: S13, S23_
- **R-A12-033** (soft, METHOD): An open Position whose drawdown from entry is >= A08 `risk.fourth_outcome_review_drawdown_pct` (25%), i.e. last close <= entry × (1 − 0.25), MUST raise a `loss_review` flag in the weekly review. "It will come back" MUST NOT be an accepted reason to dismiss it. _Sources: S13 exercise, S23, S25_
- **R-A12-034** (hard, CORE): ReviewLog and TradeRecords are append-only after close. Corrections are added as new dated notes. _Sources: S07 tracking sheet, S14_
- **R-A12-035** (soft, METHOD): Each closed TradeRecord SHOULD carry `known_weaknesses`, the weak flags written down rather than explained away. _Sources: S10_

### 5.4 Paper trading & onboarding
- **R-A12-040** (hard, CORE): Paper mode MUST apply the same profile, rule set, sizing, order linkage and review cadence as live mode, with fills per R-A12-084. Paper TradeRecords MUST be flagged `paper` and MUST NOT be mixed into live performance figures. _Sources: S14 "Master the protocol on a simulator", S07, S01. Decision: D-R41_
- **R-A12-041** (soft, METHOD): Before the first live trade, the user SHOULD have at least `routine.paper_trades_min_before_live` documented paper trades, including at least one losing trade with the stop respected. Going live earlier requires an explicit acknowledgement in the ReviewLog. _Sources: S07 Month 2 gate_
- **R-A12-042** (soft, METHOD): The first A08 `sizing.initial_live_trades_count` live trades SHOULD use A08 `sizing.initial_live_risk_pct` (default 0.5%, the lower bound of the A08 `sizing.risk_pct` range 0.5–1.0%); see A08 R-A08-007. _Sources: S07 "Deploy real capital using the SMALLEST position size in your model". Decision: D-C09_
- **R-A12-043** (soft, METHOD): Onboarding SHOULD offer the [[ninety-day-plan]] (PR-A12-04) as the default learning path. An `advanced` skill-gap band MAY skip directly to the execution phase. _Sources: S07_
- **R-A12-044** (soft, METHOD): A [[skill-gap-assessment]] SHOULD be taken at plan start, in week 4, week 8 and week 12. The band maps to a recommendation per §7. _Sources: S07_
- **R-A12-045** (soft, METHOD): An unmet milestone gate extends the phase: Month 1 by `routine.month1_extension_weeks` (beginner band), Month 2 by `routine.month2_extension_weeks`. _Sources: S07_
- **R-A12-046** (soft, METHOD): Plan timelines assume `routine.weekly_effort_h` and scale proportionally when the user declares a different effort. _Sources: S07_
- **R-A12-047** (soft, METHOD): Practice SHOULD include feedback. The coach (§5.6) reviews every paper trade against the rule set. _Sources: S13 "Unless you practise with someone who's going to give you feedback"_

### 5.5 Behavioural rules & biases
- **R-A12-050** (hard, METHOD): Tax consequences MUST NOT be an input to any entry or exit decision. An exit trigger MUST NOT be delayed or suppressed for tax reasons. Tax wrappers ([[tax-wrapper]]) are set up once at account level. _Sources: S07 "Taxes should never influence whether you buy or sell a stock", S05_
- **R-A12-051** (hard, METHOD): There MUST be no "snooze", "skip" or "ignore once" action on an exit trigger, whatever the news, politics, earnings date, famous buyer or macro story. _Sources: S23 covenant 3 "There is no exception", S20 "Never abandon the predefined exit … because the macro story still sounds good", S05 "When an exit alert fires, do not ignore it"_
- **R-A12-052** (hard, METHOD): Manual stop changes MUST carry a reason and MUST follow A07 (only upward). An emotion-tagged reason ("worried", "hopeful") MUST NOT be accepted as the sole reason. _Sources: S07 "do NOT adjust your stop based on emotion". Decision: D-C12_
- **R-A12-053** (hard, METHOD): A live Position without a resting protective stop is a [[holding-and-hoping]] state. It MUST raise a critical alert in daily automation and block closing of the next ReviewSession until resolved. _Sources: S07, S23_
- **R-A12-054** (soft, METHOD): Journal emotional-state entries SHOULD be tagged with [[emotional-trap]] categories (FOMO, hope, fear, ego, revenge). The monthly review SHOULD report tag frequency together with rule-adherence rate. _Sources: S07_
- **R-A12-055** (soft, METHOD): A discretionary sell of a Position whose exit triggers have not fired and that is moving sideways SHOULD get a "boredom sell" warning. _Sources: S04 "they sell during the boring part", S22_
- **R-A12-056** (soft, METHOD): Views and coach MUST present the scoreboard and money-flow data as a record of what has happened, not as a forecast. _Sources: S13 "A record, not a forecast", S25 "Your job is not to predict where the money goes next"_
- **R-A12-057** (soft, CORE): Third-party forecasts (bank targets, analyst calls) MUST be shown as signals of direction or conviction, never as guarantees. Upside scenarios are labelled "hypothetical". _Sources: S27 "As signals, not guarantees." Decision: D-C23_
- **R-A12-058** (soft, METHOD): Under the canonical profile, a new entry SHOULD be preceded by a wait for confirmation (the A06 checklist). The coach treats "it's running, I'll miss it" as FOMO and points to the next base. _Sources: S07 "Patience: Wait for confirmed setups", S13 "I never chase"_
- **R-A12-059** (soft, METHOD): Position-management reasoning SHOULD keep the short-term story (rates, dollar, forced selling) apart from the long-term thesis, and SHOULD NOT let either override price-based exits. _Sources: S28, S20_

### 5.6 LLM coach behaviour
- **R-A12-070** (hard, METHOD): Every coach recommendation MUST be grounded in the active StrategyProfile (A13) and the user's signed PersonalRuleSet. It MUST cite the rule IDs or parameter names it applies. _Sources: S14 "Always reference the three rules when giving advice"_
- **R-A12-071** (hard, METHOD): The coach MUST NOT recommend or help carry out an action that breaks a hard rule, e.g. lowering a stop, skipping an exit, using margin or leveraged funds, exceeding the risk cap, buying in a blocked industry, or changing rules mid-trade. When asked, it MUST decline and restate the rule. _Sources: S14, S13 "no margin, no leverage, no leveraged index funds", S23. Decision: D-C12, D-C09_
- **R-A12-072** (hard, METHOD): A request outside the active profile, e.g. single stocks under PRF-beginner-index, MUST be redirected firmly to the profile. The coach MAY explain the profile-switch process (PR-A13-02), but MUST NOT perform a switch outside a review session. _Sources: S14 "redirect firmly to the protocol". Decision: D-S14_
- **R-A12-073** (soft, METHOD): When reviewing a closed trade, the coach MUST first ask or evaluate "were the written rules followed?" before discussing P/L. _Sources: S14_
- **R-A12-074** (soft, METHOD): The coach SHOULD restate emotional language ("I feel", "I think this will moon") as rule language, e.g. "Which checklist items are met? Where is the stop?". _Sources: S14_
- **R-A12-075** (soft, METHOD): Explanations of sizing and exits SHOULD use concrete numbers computed from the user's own parameters and equity. _Sources: S14 "use concrete examples"_
- **R-A12-076** (hard, CORE): The coach MUST NOT claim certainty about future prices, a cycle phase or outcomes, and MUST show the evidence behind every assessment. _Sources: S18 hard rules 1–2_
- **R-A12-077** (hard, CORE): The coach MUST NOT give a buy or sell recommendation that rests only on a cycle phase, a style regime or a macro thesis. Price structure, relative strength and risk rules stay primary. _Sources: S18 hard rules 4, 6; S20. Decision: D-C25_
- **R-A12-078** (hard, CORE): When asked about the cycle phase, the coach MUST follow the A03 output format. When evidence is mixed it MUST say "Transition / Mixed" ([[transition-phase]]) with lowered confidence, and it MUST note that recessions are dated only in hindsight (NBER). _Sources: S18 hard rules 3, 5_
- **R-A12-079** (hard, CORE): Historical patterns and [[backtest]] figures MUST be labelled historical tendencies or hypothetical results, with their source. Figures without a named study MUST be labelled "unattributed". _Sources: S18 hard rule 7, S16, S17 caveats, S14 (unsourced "~75% win rate")_
- **R-A12-080** (hard, METHOD): The coach MUST NOT issue buy/sell ratings or price targets for a company. Fundamental output follows A05 [[research-report]] rules. _Sources: S10, S11, S12. Decision: D-C23_
- **R-A12-081** (soft, METHOD): A decision request made while the market is open (other than one handled by automation) SHOULD be answered by noting it on the agenda of the next ReviewSession, not with an immediate trade suggestion. _Sources: S14 rule 5, S13, S25_
- **R-A12-082** (soft, METHOD): The coach SHOULD say openly when an earlier idea no longer qualifies, e.g. a top pick that did not move despite good news, and demote it. It does not defend prior statements. _Sources: S22 "It's just no longer a top pick."_
- **R-A12-083** (soft, METHOD): The coach SHOULD remind the user that the routine exists to remove constant decision-making, and point to the next scheduled session. _Sources: S14_

### 5.7 Round-3 additions (2026-10-26)
- **R-A12-084** (hard, CORE): Paper fills MUST follow `routine.paper_fill_model`: market and limit-on-open orders fill at the next-session open adjusted by `routine.paper_slippage_pct[class]` against the trader (LOW 0.05, MEDIUM 0.1, HIGH 0.2, EXTREME 0.4%, effective class per A08); a limit-on-open fills only if the adjusted open is within its limit; a stop fills at the worse of the stop price and the gap open (no extra slippage). _Decision: D-R41_
- **R-A12-085** (soft, METHOD): The skill-gap assessment SHOULD also rate `scoreboard_reading` and `exit_discipline` (1–10). These two ratings feed the coaching focus (weakest skill) but MUST NOT enter the S07 total or band. _Sources: S07. Decision: D-DEF-37, D-C03_
- **R-A12-086** (soft, METHOD): Every Portfolio keeps its own Routine, ReviewSessions, rule set and limits, also within one household. Several Portfolios MAY be scheduled on the same review day and reviewed back to back; a step done for one Portfolio does not count for another. _Decision: D-DEF-38_

## 6. Processes

**PR-A12-01 Weekly review** (trigger: `routine.weekly_review_day`, market closed; cadence weekly; inputs: alerts log, scoreboard snapshot (A02), positions, watchlist, rule set; outputs: ReviewSession, orders, flags). Order per R-A12-006:
1. *Alerts*: review every alert and order fill since the last session (mandatory). _S07, S23_
2. *Scoreboard*: read the current scoreboard (A02), green/red/neutral and top RS group. Note status changes of held and watched industries. A red industry gets the D-C27 review/reduce flag in this session (R-A12-013). _S13, S25, S30_
3. *Moving averages*: for every holding and watched basket, check the 50-SMA and 150-SMA state (rising/flat/falling, price above/below). _S13_
4. *Exits*: for every open Position, verify that the resting stop exists (or the alert-based exit of a physical holding, A07 R-A07-043), apply the A07 structure raise to the new last buyer area and the ratchet (up only), and check profit-taking triggers (mandatory). _S13, S23. D-C12, D-C13, D-R34_
5. *Health flags*: rule deviations since the last session (discretionary sells, R-A12-005, D-C29), loss review (R-A12-033), missing stop (R-A12-053), [[fading-volume-rally]] warning (A04, S30 Move 1), [[stomach-test]] check (A08) (mandatory). _S30, S23_
6. *Candidates*: inside green industries only (canonical), scan the watchlist for heartbeat breakouts. Run the A06 [[entry-checklist]] and the A05 [[survival-check]]. Under other profiles, run that profile's selection step (A13). _S30, S13_
7. *Sizing & headroom*: size each candidate per A08 and check A09 concentration headroom. A breach blocks the buy (D-C11). _S13, S15_
8. *Orders*: place next week's orders. Each breakout entry is armed (default: close-confirmed trigger, A06 R-A06-030; variant: [[breakout-buy-order]]) with its protective stop in the same session (A06/A07) (mandatory); trim-to-cap items from A08 R-A08-034 are decided and journaled if skipped (D-R12). _S13 "Set the sell order at the same moment you set the buy order", S07_
9. *Watchlist*: add and remove entries and set or refresh alerts (R-A12-009). _S07_
10. *Journal & rules*: write journal notes on what went well and what needs improvement, and read the rule set. Revise it only per R-A12-023…025. _S07, S13, S14_
11. *Monthly block*: if this session is the monthly slot, run PR-A12-02 before closing. _D-C04_

**PR-A12-02 Monthly review** (trigger: `routine.monthly_review_slot`, the first weekly session after each month-end (R-A12-011); market closed; outputs: monthly ReviewSession, flags):
1. RS ranking of industries (A02 `scoreboard.*` composite), compared with last month's top RS group.
2. RS-deterioration evaluation per D-C27, which sets flags and blocks (R-A12-013).
3. Concentration audit (A09): look-through exposure per sector, industry and position, and breaches.
4. Cycle check (A03) as bias only (R-A12-015).
5. Thesis invalidation signs (A11) (R-A12-014).
6. Behaviour metrics: rule-adherence rate, emotional-trap tag counts, outcome-class counts (R-A12-054).
7. Profile-specific monthly step, e.g. the PRF-momentum-rotation rebalance (A13 PR-A13-03).

**PR-A12-03 Daily automation** (trigger: each market session; no user action):
1. Evaluate alerts on daily closes, once per day.
2. Broker executes resting stops (and variant buy-stops); the system places next-session limit-on-open buys for armed entries whose breakout closed confirmed (A06 R-A06-030) and market-on-open exit orders (A07 R-A07-040, D-R16).
3. A07 generates exit orders for the next session (e.g. close below the 150-SMA, D-C26).
4. Raise critical alerts: missing stop (R-A12-053), order rejected.
5. Queue all non-automated items for the next ReviewSession agenda.

**PR-A12-04 90-day learning path** (trigger: onboarding; cadence weekly; S07, mapped to [[learning-levels]]):
- *Phase 1, Foundation (weeks 1–4).* Deliverables: broker and charting with volume confirmed; volume alerts (A04 multiple, D-C01) on ≥10 instruments; first watchlist of 5–10; weekly review scheduled with ≥2 sessions held; "Why" statement written; first skill-gap assessment.
  - Week 1: infrastructure, first alerts, tracking journal, schedule weekly review.
  - Week 2: volume literacy on 10 charts.
  - Week 3: heartbeat recognition on 10 charts.
  - Week 4: synthesis, watchlist, skill gap.
  - *Gate G1:* all deliverables met. Otherwise extend per R-A12-045.
- *Phase 2, Application (weeks 5–8).* Deliverables: watchlist ≥15 across sectors held for ≥3 consecutive weeks; ≥3 research sessions; 6 documented paper trades; ≥1 losing paper trade with the stop respected; can compute sizes per A08; can state entry, stop and exit trigger for each trade.
  - Week 5: first full research session.
  - Week 6: two paper trades.
  - Week 7: sizing and concentration, two more paper trades.
  - Week 8: mid-point review, skill gap again.
  - *Gate G2:* deliverables met (= R-A12-041). Otherwise extend 2–4 weeks.
- *Phase 3, Execution (weeks 9–12).*
  - Week 9: first live trade with the highest-conviction setup at minimum risk (R-A12-042), checking at most once a day.
  - Week 10: manage per A07, add 1–2 positions within limits, diversification check.
  - Week 11: advanced entries (buy-stop above resistance, second-chance entry, what not to buy).
  - Week 12: 90-day review.
- *Completion criteria:* ≥`routine.ninety_day_min_trades` trades (paper + live), every trade documented, entry checklist (A06) on every entry, buy and stop placed together every time, risk ≤ cap every time, ≥`routine.ninety_day_min_research_weeks` weekly reviews held, watchlist maintained ≥8 weeks, final skill gap improved over week 1.
- *90-day review output:* total trades, [[win-rate]], average gain, average loss, total return compared with a passive index fund, top 3 strengths, top 3 gaps, goals for the next 90 days.

**PR-A12-05 Rule-set revision** (trigger: closed-trade review, scheduled review, profile switch; inside a ReviewSession):
1. Draft a new version.
2. Validate ranges (R-A12-021).
3. Compute `applies_to_open_positions` (R-A12-024).
4. Record the revision (R-A12-025).
5. Sign (R-A12-022).
6. The previous version becomes `superseded`.

**PR-A12-06 Trade close review** (trigger: Position closed):
1. Answer rules_followed for each rule.
2. Assign the outcome class.
3. Record emotional state at exit.
4. Note known weaknesses.
5. If a rule proved wrong, add it to the next session's agenda as a revision candidate. Do not edit the rule set now.

## 7. Calculations
```
skill_gap_total = volume_analysis + heartbeat_pattern + record_quarters + risk_management + emotional_discipline   # each 1..10 → total 5..50
band = advanced            if total >= 40      → "proceed to Month 3"
       intermediate        if 25 <= total <= 39 → "follow full 90-day plan; focus on weakest skill"
       beginner            if 10 <= total <= 24 → "extend Month 1 by 2 weeks"
       starting_from_zero  if total <= 9        → "start Month 1 with extended Foundation practice"
weakest_skill = argmin(ratings ∪ extra_ratings)       # used to pick coaching focus; extra skills never enter the total (D-DEF-37)

paper_buy_fill   = open(next session) × (1 + slip[class]/100)       # slip LOW 0.05, MEDIUM 0.1, HIGH 0.2, EXTREME 0.4 (D-R41)
paper_sell_fill  = open(next session) × (1 − slip[class]/100)
paper_stop_fill  = min(stop, open) if open < stop else stop        # worse of stop price and gap open

position_risk_pct (journal) = weight_pct × stop_distance_pct / 100        # see A08 for the binding formula
stop_distance_pct = (entry − stop) / entry × 100

win_rate        = count(pnl > 0) / count(closed trades)
avg_gain_pct    = mean(pnl_pct | pnl > 0)
avg_loss_pct    = mean(pnl_pct | pnl <= 0)
adherence_rate  = count(rules_followed = true) / count(closed trades)    # monthly review
loss_review_flag = (entry − last_close) / entry × 100 >= risk.fourth_outcome_review_drawdown_pct   # A08; ⇔ last_close <= entry × (1 − 0.25)
after_tax_gain   = gain × (1 − tax_rate)                                  # informational only, never a decision input
```

## 8. Examples / fixtures

**EX-A12-01 Review day validation.** Given a Portfolio with primary market NYSE. When the user sets `routine.weekly_review_day` = Saturday, then it is accepted, and the next session is Sat 2026-10-31. *Edge:* when the user sets Wednesday, then it is rejected (R-A12-002), because Wednesday 2026-10-28 is a trading day.

**EX-A12-02 Midweek activity.** Given today is Tue 2026-10-27 (market open). When the user tries to create a new breakout buy order, then it is blocked (R-A12-003) and queued as an agenda item for Sat 2026-10-31. When a held basket closes on 2026-10-27 below its 150-SMA, then A07 generates a sell order for the 2026-10-28 session without user action (R-A12-004, D-C26). *Edge:* when the user manually sells a different position that no exit trigger requested, then the sale goes through (never blocked) after a two-halves warning and a typed mandatory reason; it is journaled as a `rule deviation` and appears on the agenda of the Sat 2026-10-31 session (R-A12-005, D-C29). A discretionary *buy* attempted the same day stays blocked.

**EX-A12-03 RS deterioration (monthly).** Given industry "IT services" is held and neutral. It was outside the top RS group at the September month-end review (Sat 2026-10-03, first weekly session after Wed 2026-09-30) and still outside at the October month-end review (Sat 2026-10-31, first weekly session after Fri 2026-10-30). Then the 2026-10-31 monthly review raises a `rs_deterioration` flag, blocks new buys in IT services, and generates no sell order under the canonical profile (R-A12-013, D-C27). *Edge:* outside on 2026-10-03 but back in the top group on 2026-10-31 → count reset, no flag. *Edge (red):* the industry turns red at the weekly snapshot used on Sat 2026-10-17 → new buys are blocked immediately and the review/reduce flag is raised in that 2026-10-17 session, without waiting for a monthly review; still no sell order.

**EX-A12-04 Rule change mid-trade.** Given rule set v3 is active with one open Position (entry $25.00, stop $21.00). When on Sat 2026-10-31 the user revises the stop offset to a wider value "for this position", then `applies_to_open_positions` = false: the open Position keeps v3 and its stop stays at $21.00 (R-A12-024), and v4 applies to new entries only. The revision is rejected outright if it is attempted on Tue 2026-10-27 (R-A12-023), or if it is filed as `closed_trade_review` without a linked closed trade (R-A12-025).

**EX-A12-05 Skill-gap bands** (S07 table).
| Ratings (VA, HB, RQ, RM, ED) | Total | Band | Recommendation |
|---|---|---|---|
| 6, 5, 3, 7, 4 | 25 | intermediate | full 90-day plan; focus = record quarters (3) |
| 5, 5, 5, 5, 4 | 24 | beginner (edge: 1 below 25) | extend Month 1 by 2 weeks |
| 8, 8, 8, 8, 8 | 40 | advanced (edge: lower bound) | skip to Month 3 (R-A12-043) |
| 1, 1, 2, 2, 2 | 8 | starting_from_zero | extended Foundation practice |

**EX-A12-06 Paper gate.** Given 5 paper trades, all winners. When the user switches the Portfolio to live, then a warning lists the unmet criteria (trades < 6, no losing trade with stop respected), and live mode needs an acknowledgement in the ReviewLog (R-A12-041). Given 6 paper trades including 1 loss stopped at its planned stop and a signed rule set, then the gate is met. *Edge:* an unsigned rule set blocks live mode regardless of trade count (R-A12-020, hard).

**EX-A12-07 Journal entry, sourced trade** (S07 "confident chart read"). Given entry $25.00, stop $21.00, weight 3% of portfolio. Then stop_distance = (25 − 21)/25 = 16.0% and risk = 3% × 16% = 0.48% (≤ 1% cap, A08). Required journal fields are filled: entry_rationale = {heartbeat ≈ 8 months, breakout close $24.80 > $24 ceiling, volume spike on green bar}, emotional_state_entry = [], wanted_vs_system = "wanted to buy at $24".

**EX-A12-08 90-day review KPIs.** Given 12 closed trades: winners +8, +15, +4, +22, +6, +11, +5 %; losers −5, −7, −4, −6, −8 %. Then win_rate = 7/12 = 58.3%, avg_gain = 71/7 = +10.14%, avg_loss = −30/5 = −6.0%. Completion requires ≥12 trades ✓.

**EX-A12-09 Tax never drives the exit** (S07/S05 fixture). Given a $1,000 gain and a 30% tax rate. If the trade is made, the user keeps $700; if not, $0. When an exit trigger fires 3 weeks before a holding-period tax threshold, then the exit order is generated as usual (R-A12-050), and the coach does not suggest delaying it.

**EX-A12-10 Loss review.** Given entry $40.00 and last close $29.60. The loss is 26.0%, above the 25 threshold, so a `loss_review` flag is raised (R-A12-033). The reason "it will come back" is rejected as a dismissal reason. *Edge:* a close of $30.00 is a 25.0% loss and also raises the flag (>=, A08 `risk.fourth_outcome_review_drawdown_pct`); a close of $30.01 (24.975%) raises no flag.

**EX-A12-11 Coach response pattern.** The user says (Tue, market open): "I feel this chip stock will moon, can I skip the stop this once?". The coach (a) declines to skip the stop, restating A07 "protective stop at entry" and R-A12-051 "no exceptions"; (b) rephrases the statement as rule questions: is the industry green? Is the A06 checklist met? Where is the buyer-area stop, and what risk % does that give at the user's equity?; (c) puts the idea on the Saturday 2026-10-31 agenda (R-A12-081); (d) makes no price prediction (R-A12-076).

**EX-A12-13 Paper fills (D-R41).** Given a paper entry armed for the next session with class MEDIUM and the next open $50.00, then the paper buy fills at 50.00 × 1.001 = $50.05. A paper market-on-open sell of a HIGH-class position opening at $60.00 fills at 60.00 × 0.998 = $59.88. A paper stop at $45.00 with a gap open of $43.00 fills at $43.00 (the worse of the two); with an open of $46.00 and an intraday low of $44.50 it fills at $45.00. *Edge:* a limit-on-open buy with limit $50.04 and adjusted open $50.05 does not fill.

**EX-A12-12 Coach and the cycle.** The user asks "We're late-cycle, so sell tech?". The coach answers in the A03 format with its evidence. If the evidence is mixed it says "Transition / Mixed", confidence Low. It states that the phase is a bias only and that no sell order follows from it (R-A12-077, R-A12-078). The holdings remain governed by their A07 exits.

## 9. Variants & open points
- Review day: S05/S07 Sunday, S13/S23/S25/S30 Saturday → D-C28 makes it a parameter, default Saturday.
- Weekly duration: 15–30 min (S07), ~1 h (S13, S30), 2 h (S23, S25). Kept informational only.
- S07 triple confirmation (volume spike + heartbeat + record quarter) on every entry is replaced by the A06 entry checklist. A record quarter is an optional confirmation only (D-C03).
- S07 volume alert "+300%" is harmonised to the A04 multiple (D-C01 ≥2×). The S07 Skill Gap "below 30" bottom line contradicts its own bands and is ignored. The band "below 10" is implemented as 5–9 (minimum total is 5).
- S14 rules (single instrument, fixed size) are not general A12 rules. They belong to PRF-beginner-index (A13, D-S14).
- S13 "three levels" coaching ladder (YouTube → workbook → one-to-one coaching) is promotional and is used only as the [[learning-levels]] labels.
- S30 "weekly money talk" (family conversation) was not adopted. It carries no testable rule.
- Monthly slot: fixed week number not adopted. The monthly review runs in the first weekly session after each month-end (R-A12-011; resolved by review finding).
- Closed by D-DEF-36 — OPEN-A12-2 (loss-review threshold range 15–25, owned by A08; pending user review).
- Closed by D-R41 — OPEN-A12-4 (paper fills at next-session open plus class slippage; stops at the worse of stop and gap open).
- Closed by D-DEF-37 — OPEN-A12-5 (two extra coaching-only skills; pending user review).
- Closed by D-DEF-38 — OPEN-A12-6 (separate routines per Portfolio; pending user review).

## 10. Traceability

| Rule/Concept | Sources |
|---|---|
| R-A12-001…004 weekly / automated-daily cadence | S13, S23, S25, S30, S18, S20; D-C04, D-C26, D-C28 |
| R-A12-005 discretionary sell = journaled rule deviation | S23, S13, S25; D-C29 |
| R-A12-006…010 session order, checks, alerts | S07, S13, S14, S15, S23, S30 |
| R-A12-011…015 monthly review | S05, S16, S17, S19, S20, S28, S18; D-C04, D-C25, D-C27 |
| R-A12-020…027 PersonalRuleSet | S13, S14, S23, S25, S30, S06, S10, S27, S29; D-C09, D-C11, D-C12 |
| R-A12-030…035 journal / review log | S07, S13, S14, S23, S25, S10 |
| R-A12-040…047 paper trading, 90-day path, skill gap | S01, S07, S13, S14; D-C09 |
| R-A12-050…059 behaviour & biases | S04, S05, S07, S13, S20, S22, S23, S25, S27, S28; D-C12, D-C23 |
| R-A12-070…083 LLM coach | S14, S18, S20, S22, S10–S12, S16, S17, S13, S25; D-C09, D-C12, D-C23, D-C25, D-S14 |
| R-A12-084…086 paper fill model, extra skills, household routines | S07; D-R41, D-DEF-37, D-DEF-38 |
| PR-A12-01 weekly review | S07, S13, S15, S23, S25, S30 |
| PR-A12-04 90-day plan | S07 |
| Skill-gap bands | S07 |
