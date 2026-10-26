---
id: A13
title: Strategy Profiles
context: CTX-E
layers: [CORE, METHOD, PROFILE]
status: draft
sources: [S13, S14, S15, S16, S17, S19, S20, S23, S25, S07]
decisions: [D-S14, D-C06, D-C07, D-C05, D-C09, D-C10, D-C11, D-C12, D-C13, D-C24, D-C26, D-C27, D-OPEN-3, D-C15b, D-R03, D-R36, D-R37, D-R40, D-R44, D-DEF-39, D-DEF-40, D-DEF-41, D-DEF-42]
depends_on: [A01, A02, A06, A07, A08, A09, A12]
---
# A13 — Strategy Profiles

## 1. Purpose & scope
Defines the `StrategyProfile` entity: a named, versioned set of parameter overrides and rule-group toggles on top of CORE. The canonical [[follow-the-money]] method is the default profile. Non-canonical alternatives live in the PROFILE layer.

In scope:
- the override and resolution mechanism, and the invariants no profile can touch;
- the three profiles: canonical `PRF-follow-the-money`, [[prf-beginner-index]] (S14, D-S14) and [[prf-momentum-rotation]] (S16/S17, D-C06/C07);
- the parameter comparison, the "one active profile per portfolio" rule, and switching rules.

Excluded: the rules themselves (owned by A02–A12). This aspect only selects, parameterises and toggles them. Backtest *results* appear only as labelled, unattributed source claims, never as expectations.

## 2. Concepts
- [[strategy-profile]]: the entity defined here.
- [[follow-the-money]], [[three-step-system]]: the canonical method, scoreboard → basket → exit.
- [[prf-beginner-index]]: one-instrument S&P 500 protocol ([[sp-500]]) with fixed allocation and tiered exits.
- [[fixed-allocation-sizing]]: the beginner profile's size rule. It sets *size*, not risk (D-S14 correction).
- [[salami-profit-taking]]: the beginner profile's tiered profit-taking.
- [[prf-momentum-rotation]]: monthly ranking with top-N holding ([[top-n-rotation]]) using [[momentum-score]], [[dual-momentum]] ([[absolute-momentum]] + relative ranking) and a [[regime-filter]].
- [[two-hundred-day-sma]]: the long trend filter permitted for regime filtering (D-C05).
- [[risk-per-position]], [[position-size]], [[overnight-gap-test]]: the A08 constraints every profile must satisfy.
- [[concentration-limit]], [[look-through-exposure]], [[hidden-concentration]]: the A09 constraints. The S&P 500's tech weight is the S13 example.
- [[cash-like-instrument]], [[treasury-bill]]: the parking place when the regime is off or capacity is unused (D-C24).
- [[rebalancing]], [[equal-weighting]], [[inverse-volatility-weighting]]: momentum-profile weighting.
- [[backtest]]: evidence attached to profiles, always hypothetical.
- [[paper-trading]]: the recommended first run of any newly selected profile (A12).

## 3. Entities

| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| StrategyProfile | id | string `PRF-<slug>` | unique, stable | `PRF-follow-the-money`, `PRF-beginner-index`, `PRF-momentum-rotation` |
| | name, description | text | | |
| | layer | enum {METHOD, PROFILE} | METHOD only for the canonical profile | |
| | canonical | bool | exactly one profile true (R-A13-002) | |
| | version | semver | immutable once published (R-A13-007) | |
| | status | enum {draft, published, deprecated} | only `published` can be activated | |
| | parameter_overrides | map param → value | value within owning aspect's range (R-A13-005) | keys use owning-aspect prefixes |
| | range_narrowing | map param → [min,max] | ⊆ owning aspect's allowed range | user values must lie inside it |
| | rule_group_toggles | map rule_group → {enabled, disabled, replaced_by} | only groups the owning aspect marks *profile-switchable* | |
| | added_rules | list of R-A13-xxx | profile-specific rules defined here | |
| | instrument_universe | {allowed_types[], allowed_instruments[] or selector} | | |
| | backtest_claims | list {source, period, metric, value, attribution ∈ {named, unattributed}} | display-only (R-A13-013) | |
| | sources, decisions | refs | | |
| ProfileAssignment | portfolio_id, profile_id, profile_version, active_from, active_to, ruleset_version | ref, date | exactly one with active_to = null per Portfolio (R-A13-003) | history of switches |
| ProfileSwitch | id, portfolio_id, from_profile, to_profile, review_session_id, reason, pending_orders_cancelled[], positions_migrated[] | ref | created only in a ReviewSession (R-A13-061) | |
| Position (extension) | entry_profile_id, entry_profile_version | ref | frozen at entry | governs the exit plan (R-A13-063) |
| MomentumRanking | as_of (month-end), universe[], scores {instrument → momentum_score}, rank, passes_absolute, regime_on, selected[] | date, % | one per rebalance | PRF-momentum-rotation only |

Profile lifecycle: `draft → published → deprecated`. A deprecated profile stays valid for assignments that are already active. It cannot be newly activated.

## 4. Parameters

Profile-owned parameters (A13 is their owner):

| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `profile.active_id` | `PRF-follow-the-money` | any published profile | id | D-S14, D-C06/C07 |
| `profile.switch_min_interval` | 13 | ≥ 13 (stricter only) | weeks since the last switch | D-DEF-39 |
| `profile.paper_first_on_switch` | true (soft) | bool | — | S14, S07 |
| `profile.beginner_index.instruments` | S&P 500 index exposure: SPX-tracking liquid ETF/UCITS available in user's market (e.g. SPY) | S&P 500 trackers only | list | S14 |
| `profile.beginner_index.allocation_pct` | user picks one value (no default) | 2–5 | % of portfolio equity, per trade | S14; D-S14 (size, not risk) |
| `profile.beginner_index.tranche_fraction` | 1/3 | fixed; each tranche floored, remainder to the last tranche | fraction of entry shares | S14; D-R40 |
| `profile.beginner_index.profit_targets_pct` | +10, +15, +25 | 3 values, strictly ascending, each 5–50 | % above entry | S14 ("example structure"); D-DEF-40 |
| `profile.beginner_index.max_concurrent_lots` | 3 | 1–3 | open lots, each with its own stop and targets | D-R37 |
| `profile.beginner_index.trail_after_first_target` | false | bool | — | S14 "consider"; D-C12 (breakeven/trailing variants optional) |
| `profile.momentum_rotation.universe` | 11 SPDR Select Sector ETFs (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLB, XLU, XLRE, XLC) for US; local sector proxies elsewhere | user list of liquid sector/industry ETFs | list | S17; S16 (+15–25 industry ETFs); D-C14/D-C15b |
| `profile.momentum_rotation.score_lookbacks_months` | [6] | any subset of {1, 3, 6, 12} | months | S17 starter, S16 starter (alt: 3, 12, avg 3/6, composite 1/3/6) |
| `profile.momentum_rotation.skip_last_month` | false | bool | — | S17 Strategy B (12-1) |
| `profile.momentum_rotation.score_weights` | equal across chosen lookbacks | sum = 1 | — | S16 ("average of 3- and 6-month"), S17 C |
| `profile.momentum_rotation.top_n` | 3 | 2–4 (sector universe); 4–6 (with industry ETFs) | count | S17 ("2–4 better than 1 or all 11"), S16 starter |
| `profile.momentum_rotation.rebalance` | monthly (month-end close) | monthly | — | S17 ("Monthly is the most common"), S16 |
| `profile.momentum_rotation.absolute_filter` | `price_above_own_200sma` | {price_above_own_200sma, ret_12m_gt_0, ret_12m_gt_tbill, off} | enum | S17 starter, S17 A/C, S16 |
| `profile.momentum_rotation.regime_filter` | `benchmark_above_200sma` | {benchmark_above_200sma, benchmark_above_10msma, benchmark_ret_12m_ge_0, off} | enum | S17 starter / C / B; D-C05 (200d/10m allowed) |
| `profile.momentum_rotation.regime_benchmark` | local benchmark of the portfolio's market (US: S&P 500 / SPY) | A02 benchmarks | id | S17; D-C15b |
| `profile.momentum_rotation.risk_off_target` | cash-like (T-bill / short-Treasury ETF) | A09 cash-like set | — | S17 B, starter; D-C24 |
| `profile.momentum_rotation.weighting` | equal | {equal, inverse_volatility} | enum | S17, S16 (risk-parity); D-C09/C10 |
| `profile.momentum_rotation.trailing_exit` | `under_150sma` | {under_150sma, fixed_trailing_pct} | enum | S17 starter ("rising" slope condition dropped per D-C26); D-C05 |
| `profile.momentum_rotation.fixed_trailing_pct` | — (used only if selected) | 15–20 | % below highest close | S17 starter |
| `profile.momentum_rotation.breadth_overlay` | off | bool | — | S17 optional |
| `profile.momentum_rotation.breadth_trigger_pct` | 50 | 50–80 | % of universe members below their own 200-SMA at month end (trigger when above) | D-DEF-41 |
| `profile.momentum_rotation.breadth_reduction_pct` | 50 | 25–100 | % cut of every actual equity weight when triggered | D-DEF-41 |

Overrides that profiles apply to parameters owned by other aspects use exactly the owning aspects' parameter keys from their §4 (A02–A09), with no aliases (R-A13-070, D-DEF-42). The comparison of all dimensions is in §8.0. Current overrides:

| Profile | Overridden key (owner) | Value | Reason |
|---|---|---|---|
| PRF-beginner-index | `entry.second_chance_enabled` (A06) | true | a second-chance pullback to the rising 50-SMA opens a new lot (R-A13-037, R-A13-067, D-R37) |
| PRF-beginner-index | `entry.breakout_tranche_pct` (A06) | 100 | each lot is one full fixed allocation; lots replace the 60/40 split (D-R37) |
| PRF-momentum-rotation | `entry.breakout_tranche_pct` (A06) | 100 | targets are bought in full at the rebalance (S17); no second-chance tranche |
| PRF-momentum-rotation | `entry.second_chance_enabled` (A06) | false | the A06 entry rules are disabled (R-A13-049) |
| PRF-beginner-index | `exit.quick_win_enabled` (A07) | false | the profit-taking group is replaced by salami targets (R-A13-034) |
| PRF-momentum-rotation | `exit.quick_win_enabled` (A07) | false | no profit-taking; rotation replaces it |
| PRF-momentum-rotation | `exit.fixed_trailing_stop_pct` (A07) | = `profile.momentum_rotation.fixed_trailing_pct` (15–20) | only when `trailing_exit = fixed_trailing_pct` (R-A13-046) |

## 5. Rules

### 5.1 Profile mechanism (all profiles)
- **R-A13-001** (hard, CORE): A StrategyProfile MUST declare id, layer, canonical flag, version, parameter overrides, range narrowings, rule-group toggles, instrument universe, sources and decisions. _Sources: S14, S16, S17_
- **R-A13-002** (hard, CORE): Exactly one published profile, `PRF-follow-the-money`, is canonical (layer METHOD). All other profiles are layer PROFILE and MUST be labelled "non-canonical" wherever they are shown. _Decision: D-S14, D-C06/C07_
- **R-A13-003** (hard, CORE): Every Portfolio MUST have exactly one active profile at any time. The default is `PRF-follow-the-money`. Running two profiles needs two Portfolios. _Sources: S14 ("Trade one instrument" protocol is exclusive), S17_
- **R-A13-004** (hard, CORE): Effective parameter values MUST resolve in this order: (1) hard invariant (R-A13-006), (2) the user's signed PersonalRuleSet value (A12), which must lie in the effective range, (3) the profile override, (4) the owning aspect's default. _Decision: D-C09, D-C11 (user parameters)_
- **R-A13-005** (hard, CORE): A profile MAY set a value inside the owning aspect's allowed range, MAY narrow that range, and MAY toggle rule groups that the owning aspect marks profile-switchable. It MUST NOT widen a range, invent a parameter of another aspect, or touch an invariant. Publishing a profile that breaks this rule MUST be rejected. _Sources: design consequence of D-S14, D-C06/C07_
- **R-A13-006** (hard, CORE): No profile can disable or loosen these invariants:
  (a) stops only move up (A07, D-C12);
  (b) a protective stop placed in the same sitting as the buy (A07; S13, S14, S07);
  (c) risk per position ≤ `sizing.max_risk_pct` with its cap of 1% (A08, D-C09/C10);
  (d) the overnight-gap weight cap (A08, D-OPEN-3);
  (e) price-based exits fire automatically and independently (A07, D-C26);
  (f) a concentration breach blocks new buys (A09, D-C11);
  (g) no margin, no leverage, no [[leveraged-etf]] (A08; S13);
  (h) the emergency buffer stays outside the investable portfolio (A09, D-C24);
  (i) the survival veto for single stocks (A05, D-C03);
  (j) A12 hard rules: signed rule set, journal, no mid-trade rule changes, taxes never drive decisions, coach hard rules.
  _Decision: D-C03, D-C09, D-C10, D-C11, D-C12, D-C24, D-C26, D-OPEN-3_
- **R-A13-007** (hard, CORE): Profiles are versioned and a published version is immutable. Every Position records the `entry_profile_id` and `entry_profile_version` it was opened under. _Sources: S14 ("no rule changes mid-trade")_
- **R-A13-008** (hard, CORE): Every view and coach answer that gives a recommendation MUST show the active profile's name and whether it is canonical. _Sources: S14, S17 (contrasts the canonical profile with monthly ranking)_
- **R-A13-013** (hard, CORE): Backtest claims attached to a profile MUST be displayed as hypothetical, with source, period and attribution. They MUST NOT be presented as expected returns. S16/S17 figures are `unattributed`. _Sources: S16, S17 caveats; S14 (~75% win rate unsourced)_

### 5.2 Canonical profile `PRF-follow-the-money`
- **R-A13-020** (hard, METHOD): `PRF-follow-the-money` applies every owning-aspect default with no overrides. Its rules are:
  - the scoreboard gate: buy only where the scoreboard is [[scoreboard-green]] (A02);
  - basket-first selection (A05);
  - the A06 entry checklist: a [[heartbeat-breakout]] on ≥2× volume, price above the rising 50-SMA, never below the 150-SMA (D-C06/C07, D-C01);
  - risk-based sizing (A08);
  - the full A07 exit set: the 150-SMA trend exit, a protective stop below the buyer area, and profit-taking (D-X, D-C12/C13, D-C26);
  - RS deterioration produces a flag only (D-C27);
  - the A12 weekly and monthly cadence.
  _Sources: S13, S15, S23, S25. Decision: D-X, D-C05…C13, D-C26, D-C27_

### 5.3 `PRF-beginner-index` (S14, D-S14)
- **R-A13-030** (hard, PROFILE): The instrument universe is limited to `profile.beginner_index.instruments` (S&P 500 trackers). Orders for single stocks, single-name options, crypto, forex or any other instrument MUST be rejected while this profile is active. _Sources: S14 Rule 1_
- **R-A13-031** (hard, PROFILE): Sizing uses [[fixed-allocation-sizing]]. The user picks one `allocation_pct` in 2–5%, and every trade uses that same value. Changing it is a PersonalRuleSet revision (A12 R-A12-023…025). _Sources: S14 Rule 2 "Always use the same percentage"_
- **R-A13-032** (hard, PROFILE): `allocation_pct` is a position size, not risk. Risk = allocation × stop distance and MUST be ≤ the effective `sizing.risk_pct` (the user's setting, itself ≤ `sizing.max_risk_pct`, A08 R-A08-026). If it is not, the position size MUST be reduced to the risk-based size (equity × risk_pct / stop distance), and the reduction is shown to the user. _Decision: D-S14 (conflation fix), D-C09/C10_
- **R-A13-033** (hard, PROFILE): A hard protective stop MUST be placed before or with the entry order. Its distance follows the A07/A08 volatility-class rules (D-C08), and it is never moved further away (invariant a). _Sources: S14 Rule 3. Decision: D-C08, D-C12_
- **R-A13-034** (hard, PROFILE): The profile replaces the canonical profit-taking group (A07 half-on-extension / quick win, D-C12/C13) with [[salami-profit-taking]]. `tranche_fraction` of the entry shares is sold at each of `profit_targets_pct`. All tranches are resting limit orders placed at entry where the broker supports them. _Sources: S14 Rule 3 "Automate both stops and profit targets"_
- **R-A13-035** (soft, PROFILE): After the first target fills, the user MAY switch the remaining stop to a trailing stop (`trail_after_first_target`, default false). It may only ever move up. _Sources: S14 "consider converting the stop to a trailing stop". Decision: D-C12_
- **R-A13-036** (hard, PROFILE): The A02 scoreboard gate and A05 basket/company selection are disabled because there is one instrument. The scoreboard stays available as an information view. _Sources: S14 ("No need to research individual company earnings")_
- **R-A13-037** (hard, PROFILE): The entry signal is the canonical A06 entry checklist applied to the S&P 500 tracker: a heartbeat-base breakout on ≥ 2× volume above a rising 50-SMA, or a second-chance entry on a pullback to the rising 50-SMA (A06 R-A06-031). The A07 150-SMA trend exit applies. All parameters not named above are inherited from the canonical profile. _Decision: D-R37, D-X (all exit mechanisms), D-C06/C07_
- **R-A13-038** (hard, PROFILE): Every trade MUST pass the S14 per-trade checklist before order placement: instrument in universe; size = fixed allocation (or the reduced risk-based size); hard stop set; tiered targets defined; TradeRecord created (A12 R-A12-030). _Sources: S14 Quick Reference Checklist_
- **R-A13-039** (soft, PROFILE): Under this profile the coach SHOULD use the S14 framing ("Trade one instrument. Size every trade the same. Automate exits.") and redirect off-protocol requests (A12 R-A12-072). It MUST NOT quote the S14 "~75% win rate" except as an unsourced claim (R-A13-013). _Sources: S14_

### 5.4 `PRF-momentum-rotation` (S16/S17, D-C06/C07)
- **R-A13-040** (hard, PROFILE): The universe is `profile.momentum_rotation.universe`. Members MUST be liquid sector or industry funds ([[sector-etf]], [[exchange-traded-fund]]). Outside the US, local sector or industry proxies from the A02 classification scheme are used. _Sources: S17 §2, S16 §6, S19. Decision: D-C14, D-C15b_
- **R-A13-041** (hard, PROFILE): At each rebalance every universe member gets a [[momentum-score]] = weighted trailing total return over `score_lookbacks_months`, skipping the last month if `skip_last_month`. Members are ranked in descending order. _Sources: S17 A/B/C, S16 1/4/starter_
- **R-A13-042** (hard, PROFILE): Rankings MUST use month-end closes (the last trading day of the month). The resulting orders are created in the next A12 ReviewSession while the market is closed, for execution in the following session. _Sources: S17 "At the end of each month"; A12 R-A12-003. Decision: D-C04_
- **R-A13-043** (hard, PROFILE): A member is eligible only if it passes `absolute_filter` (default: month-end close above its own 200-SMA). _Sources: S17 starter "Only hold a sector if its price is above its own 200-day SMA", S16 starter_
- **R-A13-044** (hard, PROFILE): If `regime_filter` fails at month end (default: regime benchmark close ≤ its 200-SMA), the portfolio MUST hold no equity funds until the next month-end that passes. All equity holdings are sold and capacity goes to `risk_off_target`. _Sources: S17 starter, S17 B "move entirely to short-term Treasuries". Decision: D-C05, D-C24_
- **R-A13-045** (hard, PROFILE): The target set is the top `top_n` eligible members. A holding outside the target set at a rebalance MUST be sold. This replaces the canonical RS-deterioration "flag only" group (D-C27), as D-C06/C07 allow for this separate profile. _Sources: S17 A "Hold until the next month-end rebalance", S16 "Exit: Relative strength deterioration". Decision: D-C06/C07, D-C27_
- **R-A13-046** (hard, PROFILE): Between rebalances the A07 price-based exits remain active (invariant e). By default (`trailing_exit = under_150sma`) this is the A07 trend exit: a daily close below the 150-SMA produces a next-session sell, with no slope condition (D-C26). If `trailing_exit = fixed_trailing_pct`, the stop sits `fixed_trailing_pct` below the highest close and only moves up. _Sources: S17 starter step 4, S16 starter. Decision: D-C05, D-C12, D-C26_
- **R-A13-047** (soft, PROFILE): A member stopped out between rebalances SHOULD NOT be re-bought before the next rebalance, even if it remains ranked in the top N. _Sources: S17 A "Hold until the next month-end rebalance"_
- **R-A13-048** (hard, PROFILE): The target weight is 1/`top_n` of investable equity (equal), or inverse-volatility weights. The actual weight per holding MUST be min(target weight, A08 risk-based weight = effective `sizing.risk_pct` (user setting, ≤ `sizing.max_risk_pct`) / stop distance, A08 overnight-gap cap for funds, A09 sector/industry cap on a look-through basis; diversified sector/industry funds are not positions for the 10% per-company cap, D-R36). Unused capacity is held in `risk_off_target`. _Sources: S17 §5 ("Apply the fixed ~1% portfolio risk rule … at the individual ETF level"), S16 starter. Decision: D-C09/C10, D-C11, D-OPEN-3, D-C24, D-R36_
- **R-A13-049** (hard, PROFILE): The canonical A06 entry checklist (heartbeat breakout, volume multiple, rising 50-SMA) and the A02 green-only gate are disabled. Selection is by R-A13-041…045 alone. _Sources: S17 (monthly ranking contrasted with the canonical profile, S17 D). Decision: D-C06/C07_
- **R-A13-050** (soft, PROFILE): `top_n` SHOULD be 2–4 for a sector-only universe and 4–6 when industry ETFs are included. _Sources: S17 §4, S16 §6_
- **R-A13-051** (soft, PROFILE): If `breadth_overlay` is on and more than `breadth_trigger_pct` (50%) of universe members close below their own 200-SMA at month end, every actual equity weight (after caps, R-A13-048) SHOULD be cut by `breadth_reduction_pct` (50%), with the residual in `risk_off_target`. _Sources: S17 §5. Decision: D-DEF-41_
- **R-A13-052** (soft, PROFILE): A cycle overlay (S17 Strategy E) MAY be used only as an A03 [[phase-bias]] for display. It MUST NOT change the ranking or produce orders. _Sources: S17 E, S18, S20. Decision: D-C25_

### 5.5 Profile switching
- **R-A13-060** (hard, CORE): A profile switch MUST be a PersonalRuleSet revision with `reason_category = profile_switch`, re-signed, and recorded as a ProfileSwitch (A12 R-A12-022, R-A12-025). _Sources: S14, S13_
- **R-A13-061** (hard, CORE): A switch MUST be executed only inside an A12 ReviewSession while the market is closed. Requests at other times are queued for the next session. _Sources: S18, S20 "Make switching decisions when markets are closed". Decision: D-C04_
- **R-A13-062** (hard, CORE): At the switch, every pending entry order created under the old profile (e.g. armed close-confirmed breakout entries or variant buy-stops) MUST be cancelled. Protective stops and exit orders of open Positions MUST NOT be cancelled. _Sources: S13 (exit set with entry), invariant b_
- **R-A13-063** (hard, CORE): Open Positions keep the exit plan of their entry profile version until closed. The user MAY migrate a Position to the new profile's exit plan in the same session, but only if the migration does not lower the stop, raise the risk or remove an exit trigger (A12 R-A12-024). _Decision: D-C12, D-C26_
- **R-A13-064** (soft, CORE): After switching to a profile the user has no paper history for, the portfolio SHOULD run in paper mode until `routine.paper_trades_min_before_live` trades under that profile are documented (A12 R-A12-041). _Sources: S14 "Paper trade first", S07_
- **R-A13-065** (hard, CORE): Concentration limits and risk caps are evaluated on the whole Portfolio, including positions still managed under the old profile. A switch never creates headroom by itself. _Decision: D-C11_
- **R-A13-066** (soft, CORE): A switch request SHOULD state a process reason, e.g. skill level, available time or instrument access. The coach SHOULD flag a request whose only stated reason is the P/L of recent trades as a possible [[emotional-trap]]. _Sources: S14 (process over outcome), S07_

### 5.6 Round-3 additions (2026-10-26)
- **R-A13-067** (hard, PROFILE): Under PRF-beginner-index up to `max_concurrent_lots` (3) lots of the S&P 500 tracker MAY be open at the same time; each lot has its own entry checklist, fixed-allocation size (capped by risk, R-A13-032), protective stop and salami targets. An entry that would open a fourth lot MUST be rejected. _Decision: D-R37_
- **R-A13-068** (hard, PROFILE): Salami tranches are computed per lot: each of the first two tranches = floor(entry shares × 1/3) and the last tranche = the remainder; with fractional shares (A08 R-A08-035) the tranches are floored to the broker's increment in the same way. _Decision: D-R40_
- **R-A13-069** (hard, CORE): A profile switch MUST NOT be executed earlier than `profile.switch_min_interval` (13 weeks) after the previous switch of the same Portfolio; an earlier request is queued with its earliest allowed session. The first activation is not a switch. _Decision: D-DEF-39_
- **R-A13-070** (hard, CORE): Every parameter override of a profile MUST use exactly the owning aspect's parameter key as declared in its §4 (A02–A09 and the other aspects); a key that no aspect declares MUST be rejected at publishing (R-A13-005). _Decision: D-DEF-42_

## 6. Processes

**PR-A13-01 Profile activation (first setup)** (trigger: onboarding):
1. Show the three profiles with their comparison table (§8.0) and the non-canonical labels.
2. Suggest a profile from the A12 skill-gap band, the user's instrument access and their time budget. This is a suggestion only.
3. The user selects a profile, and a ProfileAssignment is created.
4. The user fills the PersonalRuleSet within the effective ranges, then signs it (A12).
5. Paper mode starts by default (R-A13-064).

**PR-A13-02 Profile switch** (trigger: user request, executed in a ReviewSession):
1. Validate the session and market-closed state (R-A13-061).
2. Show a diff of the effective parameters between the old and new profile.
3. List the pending entry orders that will be cancelled (R-A13-062).
4. Per open Position, choose "keep entry-profile exit plan" (default) or "migrate" (validated per R-A13-063).
5. Record the PersonalRuleSet revision and re-sign (R-A13-060).
6. Close the old ProfileAssignment and open the new one.
7. Set paper mode if R-A13-064 applies.
8. Write a ReviewLog entry.

**PR-A13-03 Momentum monthly rebalance** (trigger: the first ReviewSession after the month-end close; PRF-momentum-rotation):
1. Build a MomentumRanking from month-end closes (R-A13-041/042).
2. Regime test (R-A13-044). If it fails, generate sell orders for all equity funds plus buys of `risk_off_target`, then end.
3. Apply the absolute filter (R-A13-043) and pick the top_n eligible members (R-A13-045).
4. Holdings not in the target set get sell orders.
5. For each target: compute the stop (R-A13-046), the risk-based weight, the gap cap and the A09 caps, then the actual weight (R-A13-048).
6. Generate buy or resize orders, each with a protective stop in the same session.
7. Put residual capacity in `risk_off_target`.
8. Record the A12 monthly review step 7.

**PR-A13-04 Beginner trade** (PRF-beginner-index, in a ReviewSession):
1. Check that the entry conditions hold (A06 checklist on the tracker, R-A13-037) and that fewer than 3 lots are open (R-A13-067).
2. Size = allocation_pct × equity, then the risk check (R-A13-032).
3. Set the stop per its volatility class.
4. Create the entry order, protective stop and three target limit orders together.
5. Run the per-trade checklist (R-A13-038) and create the TradeRecord.

## 7. Calculations
```
# Resolution (R-A13-004)
effective(p) = invariant(p) if p is invariant
             else clamp_check(ruleset.value(p), effective_range(p)) if ruleset defines p
             else profile.override(p) if defined
             else owner_default(p)
effective_range(p) = owner_range(p) ∩ profile.range_narrowing(p)

# Beginner sizing (R-A13-031/032)
alloc_value      = equity × allocation_pct
stop_distance    = (entry − stop) / entry
risk_value       = alloc_value × stop_distance
position_value   = alloc_value                         if risk_value ≤ equity × risk_pct      # effective sizing.risk_pct ≤ max_risk_pct
                 = equity × risk_pct / stop_distance       otherwise
tranche_shares_k = floor(entry_shares × tranche_fraction) for k = 1,2; tranche_3 = remainder   # D-R40 (floor to the fractional increment if supported)
target_price_k   = entry × (1 + profit_targets_pct[k]/100)

# Momentum score (R-A13-041); TR = total return incl. distributions
TR(L)            = close[m_end − skip] / close[m_end − skip − L months] − 1      # skip = 1 month if skip_last_month else 0
momentum_score   = Σ_L w_L × TR(L)
eligible         = passes_absolute ∧ regime_on
target_set       = top_n(eligible, by momentum_score)

# Momentum weight (R-A13-048)
w_target   = 1 / top_n                     (equal)    | (1/σ_i) / Σ(1/σ_j)  (inverse volatility)
w_risk     = risk_pct / stop_distance_i      # effective sizing.risk_pct ≤ max_risk_pct
w_gap      = gap_max_loss_pct / assumed_fund_gap_pct  # D-OPEN-3: 2% / 15% = 13.33%
w_actual   = min(w_target, w_risk, w_gap, sector cap headroom)   # diversified funds are not positions for the 10% cap (D-R36)
w_actual  *= (1 − 0.50) if breadth_overlay and share_below_200sma > 50%   # D-DEF-41
cash_like  = 1 − Σ w_actual
```

## 8. Examples / fixtures

### 8.0 Parameter comparison of all profiles

| Dimension (owner) | PRF-follow-the-money (canonical) | PRF-beginner-index | PRF-momentum-rotation |
|---|---|---|---|
| Layer | METHOD | PROFILE | PROFILE |
| Instrument universe (A01/A05) | industry baskets first; single stocks under survival veto | S&P 500 tracker only | liquid sector (+ industry) ETFs |
| Unit of analysis (A02) | industry (~150) via scoreboard | none (single index) | sector / industry fund |
| Selection gate (A02) | green status, top RS group | disabled | top N by momentum score |
| Ranking metric (A02) | RS composite 3/6/12m, 40/30/30 (D-OPEN-1) | — | trailing TR, default 6m; alternatives 3/12/12-1/composite |
| Ranking cadence | weekly scoreboard, monthly RS ranking | — | monthly, month-end |
| Entry signal (A06) | heartbeat breakout ≥2× vol, above rising 50-SMA, never below 150-SMA | canonical A06 checklist on the S&P 500 tracker; second chance on a pullback to the rising 50-SMA (D-R37) | rank + absolute filter + regime filter |
| Base minimum (A04) | 3 months (D-C02) | inherited | n/a |
| Regime filter (A02) | none as entry gate (regime used for profit matrix, D-OPEN-4) | none | benchmark > 200-SMA (alt 10m SMA, 12m TR ≥ 0) |
| Absolute filter | price above rising 50-SMA / not below 150-SMA | — | own price > 200-SMA (alt 12m TR > 0 / > T-bill) |
| Protective stop (A07) | below last buyer area, validated vs volatility class (D-C08) | hard stop before entry, vol-class validated | per A07 (invariant) |
| Trend exit (A07) | close below 150-SMA → next-session sell (D-C26) | close below 150-SMA (D-R37) | close below 150-SMA (A07 trend exit), or 15–20% fixed trail |
| Profit-taking (A07) | half on extension / quick win (bearish regime only), rest below 50-SMA (D-C12/C13, D-OPEN-4, D-R02, D-R15) | 1/3 at +10, +15, +25% | none (rotation replaces it) |
| Trailing after profit | 150-SMA trail; breakeven optional (D-C12) | optional after 1st target (default off) | as trend exit |
| RS deterioration (A02/A07) | flag + block new buys, no auto exit (D-C27) | n/a | sold at rebalance |
| Sizing method (A08) | risk-based, shares = equity×risk%/(entry−stop) | fixed allocation 2–5%, capped by risk | equal or inverse-vol target, capped by risk |
| Max risk per position (A08) | ≤ 1% (0.5–1) | ≤ 1% (invariant) | ≤ 1% (invariant) |
| Gap-test cap (A08) | stock 30% gap → 2% loss ⇒ ≤ 6.67%; fund 15% ⇒ ≤ 13.33% | fund case | fund case |
| Position cap (A09) | ≤ 10% per company, look-through (3–10) | look-through of the S&P 500 constituents counts; the tracker itself is not a position (D-R36) | not applied to diversified sector funds; sector cap applies (D-R36) |
| Sector / industry cap (A09) | ≤ 25% look-through (15–40) | look-through of S&P 500 counts (tech weight) | ≤ 25% (15–40); S17 cites 25–40% |
| Number of holdings | S07: 15–30 positions (A09) | up to 3 concurrent lots (D-R37) | top_n (2–4 / 4–6) |
| Risk-off holding | idle cash flagged if eroding (D-C24) | same | cash-like T-bill / short-Treasury ETF |
| Review cadence (A12) | weekly Saturday + monthly | weekly Saturday + monthly | weekly (stops) + monthly rebalance |
| Leverage / margin | forbidden | forbidden | forbidden |
| Paper first (A12) | soft (≥ 6 trades) | hard to go live without written rules (S14); paper first | soft |

### 8.1 Fixtures
**EX-A13-01 Beginner sizing, source fixture (S14).** Given equity $20,000 and allocation_pct 5%. Then the position is $1,000, tranches are ≈ $333.33 of cost each, and the sale values are $366.67 at +10%, $383.33 at +15% and $416.67 at +25%. Total profit if all three fill = $166.67 (+16.67%). S14's statement "risk 5%" is corrected: 5% is the *size* (D-S14).

**EX-A13-02 Beginner sizing, share-based.** Given equity $60,000, allocation 5%, SPY-equivalent entry $500.00, and a stop at $465.00 (7%, inside the low volatility class 5–8%, D-C08). Then the position = $3,000 = 6 shares, risk = 6 × $35 = $210 = 0.35% of equity (≤ 1%, accepted). Targets: 2 shares at $550.00, 2 at $575.00, 2 at $625.00 → +$100, +$150, +$250 = +$500 (+16.67%).

**EX-A13-03 Beginner risk-cap edge.** Given equity $60,000, allocation 5% ($3,000), and a stop distance of 25% (mis-set). Then risk = $750 = 1.25% > 1% (effective `sizing.risk_pct` = 1%). The size is reduced to $600 / 0.25 = $2,400 (4.0% of equity), and the reduction is shown (R-A13-032). *Edge:* allocation_pct 6% → rejected (range 2–5). Changing from 5% to 3% between trades without a rule-set revision → rejected (R-A13-031).

**EX-A13-04 Beginner universe block.** Given PRF-beginner-index is active. When the user enters a buy for a single chip stock, then the order is rejected (R-A13-030) and the coach redirects to the protocol (R-A12-072).

**EX-A13-05 Momentum rebalance (synthetic numbers).** Given equity $100,000, as_of 2026-09-30, regime benchmark above its 200-SMA (regime on), and 6m TR ranks XLK 1st, XLI 2nd, XLB 3rd, all above their own 200-SMA. Stop distances to the 150-SMA are 9%, 11% and 14%, with top_n 3, equal weight, risk_pct 1% (= max), gap cap 13.33%, position cap 10% and sector cap 25%.
- Weights (diversified sector funds are not positions for the 10% cap, D-R36): XLK min(33.33, 11.11, 13.33, 25) = 11.11%; XLI min(…, 9.09, …) = 9.09%; XLB = 7.14%.
- Invested 27.34%, cash-like 72.66%.
- Orders are created in the review session of Sat 2026-10-03 for the 2026-10-05 session (R-A13-042, R-A13-048).

**EX-A13-06 Momentum regime off.** Given at month-end 2026-10-30 the regime benchmark closes below its 200-SMA. Then the session of Sat 2026-10-31 generates sells for all equity funds and buys of the cash-like target for 2026-11-02 (R-A13-044). *Edge:* the benchmark closes exactly at its 200-SMA → the regime fails, because the rule is "above".

**EX-A13-07 Momentum drop-out compared with canonical.** Given XLB ranks 5th at month-end 2026-10-30 (top_n 3) and is still above its 150-SMA. Under PRF-momentum-rotation it is sold at the rebalance (R-A13-045). Under the canonical profile the same drop out of the top RS group only raises a flag after 2 consecutive monthly reviews (D-C27).

**EX-A13-08 Momentum stop between rebalances.** Given XLI closes on Wed 2026-10-14 below its 150-SMA. Then a sell is generated for 2026-10-15 (D-C26). At the 2026-10-30 ranking XLI is still in the top 3, but it is not re-bought before that rebalance session (R-A13-047). It is eligible again at that session.

**EX-A13-09 Switch in session.** Given the canonical profile with 4 open positions and 2 armed breakout entries (close-confirmed triggers). When on Sat 2026-10-31 the user switches to PRF-momentum-rotation, then both armed entries are cancelled while the 4 protective stops stay (R-A13-062). The positions keep their canonical exit plans (R-A13-063), rule set v5 is signed (R-A13-060), and paper mode is suggested (R-A13-064). *Edge:* the same request on Tue 2026-10-27 is queued, not executed (R-A13-061).

**EX-A13-10 Invariant override attempt.** Given a draft profile that sets `sizing.max_risk_pct = 2` or disables the protective-stop group. Then publishing is rejected (R-A13-005/006). A draft that overrides `exit.trailing_pct` (no aspect declares this key) is rejected too (R-A13-070).

**EX-A13-11 Beginner lots and tranches (D-R37, D-R40).** Given equity $60,000, allocation 5% ($3,000) and an S&P 500 tracker entry at $400.00 with a 7% stop ($372.00). Then 3,000 / 400 = 7.5 → 7 whole shares ($2,800), risk 7 × $28 = $196 = 0.33% (≤ 1%); tranches floor(7/3) = 2, 2 and the remainder 3. With a fractional-share broker (increment 0.001): 7.5 shares, tranches 2.5, 2.5, 2.5. Two lots are already open → this third lot is accepted; a fourth lot is rejected (R-A13-067).

**EX-A13-12 Breadth overlay (D-DEF-41).** Given EX-A13-05 with `breadth_overlay` on and 7 of 11 sectors below their own 200-SMA at month end (63.6% > 50%). Then the actual weights are halved: XLK 5.56%, XLI 4.55%, XLB 3.57% (invested 13.67%, cash-like 86.33%). With 5 of 11 below (45.5%) no reduction applies.

**EX-A13-13 Switch interval (D-DEF-39).** Given a switch executed on Sat 2026-08-01. A new switch request on Sat 2026-10-24 (12 weeks later) is queued; the earliest allowed session is Sat 2026-10-31 (13 weeks).

## 9. Variants & open points
- S14 calls 2–5% both "risk" and "position size". D-S14 resolves it as size (`fixed-allocation-sizing`), with risk derived and capped (R-A13-032).
- S17 "buy the top 3 equally (33% each)" conflicts with A08/A09 caps. Kept as the target weight only. Actual weights are capped and the residual goes to cash-like (R-A13-048, EX-A13-05).
- Momentum score alternatives not chosen as default: 3m, 12m, 12-1 (S17 B), composite 1/3/6 (S17 C), average 3/6 (S16). All are selectable through `score_lookbacks_months`, `skip_last_month` and `score_weights`.
- S16 Strategy 2 (hybrid: rank sectors, then industries inside the top 2–3 sectors) is not modelled as a separate profile. Candidate future variant.
- S17 "median sector rotation" and S17 E cycle-allocation strategy were not adopted as profiles. The cycle stays bias only (D-C25).
- S19 global stock-level top-down workflow is covered by the canonical profile plus A05 industry-first stock selection.
- Closed by D-DEF-39 — OPEN-A13-1 (13 weeks between switches; pending user review).
- Closed by D-R37 — OPEN-A13-2 (canonical A06 checklist and A07 trend exit on the tracker) and OPEN-A13-8 (up to 3 concurrent lots).
- Closed by D-DEF-40 — OPEN-A13-3 (targets strictly ascending, each 5–50%; pending user review).
- Closed by D-DEF-41 — OPEN-A13-4 (halve equity weights when > 50% of members are below their 200-SMA; pending user review).
- Closed by D-R40 — OPEN-A13-5 (floor per tranche, remainder to the last; fractional iff the broker supports it).
- Closed by D-DEF-42 — OPEN-A13-6 (override keys = owning aspects' parameter keys; pending user review).
- Closed by D-R36 — OPEN-A13-7 (diversified funds are not positions for the 10% cap; the sector cap applies).

## 10. Traceability

| Rule/Concept | Sources / Decisions |
|---|---|
| R-A13-001…008, 013 profile mechanism | S14, S16, S17; D-S14, D-C06/C07, D-C09, D-C11 |
| R-A13-006 invariants | S13, S14, S07; D-C03, D-C09/C10, D-C11, D-C12, D-C24, D-C26, D-OPEN-3 |
| R-A13-020 canonical | S13, S15, S23, S25; D-X, D-C01…C13, D-C26, D-C27 |
| R-A13-030…039 beginner index | S14; D-S14, D-C08, D-C09, D-C12 |
| R-A13-040…052 momentum rotation | S16, S17, S19, S18, S20; D-C04, D-C05, D-C06/C07, D-C09…C11, D-C14, D-C15b, D-C24…C27, D-OPEN-3 |
| R-A13-060…066 switching | S13, S14, S07, S18, S20; D-C04, D-C11, D-C12, D-C26 |
| R-A13-067…070 beginner lots, tranche rounding, switch interval, override keys | S14; D-R37, D-R40, D-DEF-39, D-DEF-42 |
| Comparison table §8.0 | all above |
