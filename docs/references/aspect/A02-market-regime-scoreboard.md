---
id: A02
title: Market Regime & Scoreboard
context: CTX-B
layers: [CORE, METHOD]
status: draft
sources: [S01, S03, S05, S08, S10, S13, S16, S17, S19, S20, S25, S27, S29, S30]
decisions: [D-C04, D-C05, D-R35, D-C06, D-C07, D-C14, D-C15, D-C15b, D-C25, D-C26, D-C27, D-C28, D-OPEN-1, D-OPEN-2, D-OPEN-4, D-R01, D-R02, D-R18, D-R20, D-R21, D-R22, D-R24, D-R25, D-DEF-02, D-DEF-03, D-DEF-04, D-DEF-05, D-DEF-06]
depends_on: [A01, A04, A05]
---
# A02 — Market Regime & Scoreboard

## 1. Purpose & scope
Specifies step 1 of the method ("Read the Scoreboard"): how industries are ranked by what money has actually been doing in them, how each gets a green / neutral / red status, which industries form the top RS group, when RS deterioration is flagged, the shared "rising moving average" test, the overall market regime, the heatmap view, the default ranking level (GICS Industry) with drill-down, and the per-industry "who is investing" view built from A04 money-flow evidence (D-R20, D-R22, D-R24).

Excluded: classification and benchmarks as data (A01), volume confirmation (A04), proxy/basket construction and stock selection (A05), entry checklist (A06), exits and profit-taking matrix (A07), exposure limits (A09), business-cycle and style regime (A03), momentum-rotation profile (A13).

## 2. Concepts
- [[scoreboard]], [[scoreboard-status]], [[scoreboard-green]], [[scoreboard-neutral]], [[scoreboard-red]] — weekly per-market ranking and status of industries.
- [[relative-strength]], [[rs-composite]], [[rs-trend]], [[top-rs-group]], [[rs-deterioration]] — the RS computation chain.
- [[industry-proxy]], [[industry]], [[sector]], [[classification-scheme]], [[gics]] — the scoreboard rows (classification and `IndustryProxy` from A01; default level Industry, D-R24).
- [[smart-money-evidence]], [[fund-flow]], [[institutional-holding-13f]], [[congressional-trade]] — per-industry "who is investing" view (A04 evidence, D-R22, D-R25); view only.
- [[benchmark]], [[local-benchmark]], [[global-benchmark]] — the two views (D-C15b).
- [[rotation]], [[industry-momentum]], [[momentum]] — why industries, not companies, come first.
- [[simple-moving-average]], [[ma-slope]], [[trend]], [[two-hundred-day-sma]], [[exponential-moving-average]] — trend tests (SMA canonical; EMA not used).
- [[market-regime]], [[regime-filter]], [[absolute-momentum]], [[dual-momentum]] — broad-market state; filters are profile variants.
- [[scoreboard-heatmap]] — day/week/month, absolute/relative view.
- [[market-breadth]], [[correction]], [[bear-market]], [[parabolic-move]], [[pullback-mode]] — context labels.
- [[defensive-sector]], [[growth-sector]], [[cyclical-sector]] — used for rotation reading (A03 owns the cycle).

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Scoreboard | market | Market | | one per market × view |
| | view | enum {local, global} | | D-C15b |
| | benchmark | Benchmark | local benchmark or MSCI ACWI | A01 |
| | as_of | date | last session of the week | D-C15 |
| | level | classification level | = `classification.scoreboard_level` (default industry) or a drill-down level | A01; D-R24 |
| | entries | ScoreboardEntry[] | one per node with proxy | |
| ScoreboardEntry | node | ClassificationNode | | |
| | proxy | `IndustryProxy` (A01): ETF, INDEX or EQUAL_WEIGHT_BASKET | exactly 1 primary | R-A02-002; D-R21 |
| | proxy_type | enum {ETF, INDEX, EQUAL_WEIGHT_BASKET} | shown on every row | D-R21 |
| | smart_money_panel | ref A04 `SmartMoneyEvidence` (subjectType INDUSTRY) | optional | D-R22, D-R25 |
| | global_status_warning | bool | global view red while local view is used | D-R18 |
| | rs_3m, rs_6m, rs_12m | % points | | R-A02-005 |
| | rs_comp | % points | | R-A02-006 |
| | rs_comp_sma50 | % points | | R-A02-007 |
| | status | enum {green, neutral, red} or null | null iff data_quality = insufficient | |
| | rank, percentile | int, % | rank 1 = highest rs_comp | |
| | in_top_group | bool | | R-A02-013 |
| | weeks_in_status, newly_green | int, bool | | R-A02-017 |
| | data_quality | enum {ok, insufficient} | | R-A02-008 |
| RelativeStrength | subject, benchmark, lookback_months, value, as_of | | | per series |
| MovingAverageState | instrument, length_days, value, normalized_slope, slope_state {rising, flat, falling, undefined} | | | R-A02-025 |
| MarketRegime | market or global, benchmark, as_of, close, sma, slope_state, regime {bullish, sideways, bearish} | | | R-A02-027 |
| DeteriorationRecord (new) | node, market, view, review_dates[], consecutive_count, flag {none, active}, raised_at, cleared_at | | | D-C27 |
| RotationEvent (new) | scoreboard, as_of, entered_top[], left_top[], status_changes[] | | | R-A02-018 |
| HeatmapView (new) | cells (proxy, return, strength {strong, moderate, weak}), benchmark, timeframe {day, week, month}, mode {absolute, relative} | | view only; strength per R-A02-045 | S29; D-DEF-05 |
| DrillDownView (new) | scoreboard, from_level, to_level, parent_node, rows[] (ScoreboardEntry at the target level) | | view only; same rules per level | D-R24 |
| WhoIsInvestingView (new) | scoreboard, industry, period, fund_flow_net_usd, institutional_13f_change, insider_net, congressional_net, volume_footprint, lag_notes | | view only; retail flow not shown | D-R20, D-R22 |
| Alert | type {rs_deterioration, rs_crossover, regime_change, index_inclusion_review} | | | shared entity with A12 |

Status lifecycle per entry (evaluated weekly): `insufficient → {green | neutral | red}`; any status may move to any other at the next weekly snapshot. Deterioration flag lifecycle (monthly): `none → counting(1) → active`; `active → none` at the first monthly review with `cond_m` = false and a status other than red (R-A02-024, D-DEF-03).

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `scoreboard.lookbacks_months` | [3, 6, 12] | fixed set | calendar months | D-C15; S20 |
| `scoreboard.weights` | 3m 0.40 / 6m 0.30 / 12m 0.30 | each 0..1, Σ = 1 | — | D-OPEN-1 |
| `scoreboard.rs_method` | return_difference | {return_difference} | % points | glossary `relative-strength` |
| `scoreboard.evaluation_close` | weekly close (last session of week) | — | — | D-C15 |
| `scoreboard.rs_trend_ma_sessions` | 50 | > 0 | sessions | D-C15 |
| `scoreboard.top_rs_group_pct` | 20 | 5..50 | % of ranked entries | D-OPEN-1 |
| `scoreboard.top_rs_group_rounding` | ceil | {ceil, floor, round} | — | D-DEF-02 |
| `scoreboard.gating_view` | local (global red = warning only) | {local} | — | D-C15b, D-R18 |
| `scoreboard.drill_down_levels` | sector (11), industry group (25), industry (74), sub-industry (163) | levels of the market's scheme | — | D-R24 (default level owned by A01 `classification.scoreboard_level` = industry) |
| `scoreboard.deterioration_reviews` | 2 | ≥ 1 | consecutive monthly reviews (top-group drop only; red acts immediately) | D-C27 |
| `scoreboard.ma_slope_window_sessions` | 20 | ≥ 2 | sessions | D-OPEN-2, D-R01 |
| `scoreboard.ma_slope_flat_band_pct` | 0.025 | ≥ 0 | % of SMA per session | D-OPEN-2, D-R01 |
| `scoreboard.regime_ma_length_days` | 150 | {150, 200} or 10-month | sessions | D-OPEN-4, D-R02, D-C05 |
| `scoreboard.heatmap_default_mode` | relative | {absolute, relative} | — | S29 |
| `scoreboard.correction_threshold_pct` | 10 | > 0 | % below recent high | S10, S29 |
| `scoreboard.bear_threshold_pct` | 20 | > correction threshold | % below high | glossary `bear-market`; D-DEF-06 |
| `scoreboard.drawdown_high_lookback` | 252 | ≥ 63 | sessions (highest daily close) | D-DEF-04 |
| `scoreboard.heatmap_strong_multiple` | 1.0 | > weak multiple | × ATR%(14, 63-session avg) of the proxy × √(sessions in timeframe) | D-DEF-05 |
| `scoreboard.heatmap_weak_multiple` | 0.5 | > 0 | same unit | D-DEF-05 |
| `scoreboard.universe_size_hint` | none (guidance: 40–80 global proxies; beginner ~11–12 sectors) | ≥ 1 | proxies | S19, S13 |

Referenced: `classification.scoreboard_level`, `market.local_benchmark`, `market.global_benchmark` (A01); monthly/weekly review timing (A12 `routine.*`, D-C04, D-C28); volume averages (A04 `volume.*`).

## 5. Rules

### 5.1 Scoreboard construction
- **R-A02-001** (hard, METHOD) — For every enabled market the app MUST build two scoreboards per week: the local view (local benchmark, local currency) and the global view (MSCI ACWI, USD); rows are the nodes at `classification.scoreboard_level`. _Sources: S13, S19. Decision: D-C14, D-C15b_
- **R-A02-002** (hard, METHOD) — Each row MUST have exactly one primary `IndustryProxy` (A01 R-A01-043..046): the most liquid pure-play ETF of the node available in that market, otherwise the official industry index, otherwise a computed equal-weight basket of the node's most liquid members (min 5). _Sources: S13, S19 ("When no clean ETF exists … construct a small equal-weight basket"). Decision: D-C21, D-R21_
- **R-A02-003** (soft, CORE) — A global universe SHOULD hold roughly 40–80 liquid industry proxies rather than all 163 sub-industries. _Sources: S19_
- **R-A02-004** (soft, METHOD) — A beginner MAY start with the sector level (about 11–12 sector funds on one watchlist) before moving to the full industry list. _Sources: S13 ("Start with twelve, not a hundred and fifty")_
- **R-A02-005** (hard, CORE) — For each lookback L in `scoreboard.lookbacks_months`, `RS_L = return(proxy, L) − return(benchmark, L)` on the same return basis; local view in local currency, global view with proxy converted to USD (A01 R-A01-015, R-A01-016). _Sources: S19, S20. Decision: D-C15, D-C15b_
- **R-A02-006** (hard, METHOD) — `RS_comp = Σ w_L · RS_L` with `scoreboard.weights`. _Decision: D-C15, D-OPEN-1_
- **R-A02-007** (hard, METHOD) — RS_comp MUST be computed for every session from daily closes (to form its 50-session average); status, rank and top group MUST be evaluated at the weekly close. _Decision: D-C15_
- **R-A02-008** (hard, CORE) — If the proxy or benchmark lacks the history needed for the 12-month lookback plus `scoreboard.rs_trend_ma_sessions` RS values, the entry MUST get `data_quality = insufficient`, `status = null`, and MUST NOT be eligible for new buys. _(Covers new ETFs and recent IPO-driven baskets.)_

### 5.2 Status, ranking, eligibility
- **R-A02-009** (hard, METHOD) — `status = green` iff `RS_comp > 0` AND `RS_comp > SMA_50(RS_comp)`. _Sources: S13, S25. Decision: D-C15_
- **R-A02-010** (hard, METHOD) — `status = red` iff `RS_comp < 0` AND `RS_comp < SMA_50(RS_comp)`. _Sources: S13, S25. Decision: D-C15_
- **R-A02-011** (hard, METHOD) — Otherwise `status = neutral` (including equality cases). _Decision: D-C15_
- **R-A02-012** (hard, METHOD) — The scoreboard MUST be presented as a record of past money flow, not a forecast. _Sources: S13 ("a record, not a forecast")_
- **R-A02-013** (hard, METHOD) — Entries with a status are ranked by RS_comp descending; the top RS group is the first ceil(`scoreboard.top_rs_group_pct` % × number of ranked entries) entries (`scoreboard.top_rs_group_rounding` = ceil). _Decision: D-OPEN-1, D-DEF-02_
- **R-A02-014** (hard, METHOD) — An industry is a candidate for new buys ("where to look") only if `status = green` AND `in_top_group = true` AND no active deterioration flag; neutral industries are watched, not bought. A buy still requires the A06 entry checklist. _Sources: S13 ("Shop in green"), S25, S30 ("Look only inside the rising industries"). Decision: D-C06, D-C07, D-C27_
- **R-A02-015** (hard, METHOD) — An industry with `status = red` MUST block new buys of its proxy and of any stock classified in it immediately (from the weekly snapshot that shows red), and MUST raise the RS-deterioration review/reduce flag on holdings with look-through exposure to it at the next weekly session; no monthly count is needed. _Sources: S13 ("Nothing on the red side is cheap; it is being sold"), S25. Decision: D-C27_
- **R-A02-016** (hard, METHOD) — Eligibility (R-A02-014/015) uses the local view: local green is required. The global view is shown side by side and used for cross-market comparison; a global red status is a warning only (R-A02-041). _Decision: D-C15b, D-R18_
- **R-A02-017** (soft, METHOD) — Each entry SHOULD carry `weeks_in_status` and `newly_green` (green now, not green at the previous weekly snapshot) so recently turned industries are highlighted. _Sources: S05 ("Look for industries that have turned bullish recently")_
- **R-A02-018** (soft, METHOD) — Each weekly snapshot SHOULD emit a RotationEvent listing industries that entered and left the top RS group; A07/A09 use it for rotate decisions. _Sources: S20 ("When a new industry enters the top group and the previous leader falls out … rotate"), S13_
- **R-A02-019** (hard, METHOD) — Macro or cycle context (A03, A11) MUST NOT change any status, rank or eligibility; the scoreboard (RS + price structure) stays primary. _Sources: S20 ("Economic conditions provide context and bias, not automatic triggers"). Decision: D-C25_

### 5.3 RS deterioration
- **R-A02-020** (hard, METHOD) — At each monthly review, evaluate per industry `cond_m = (in_top_group = false)` on the latest weekly snapshot dated on or before the review date. A red status is not counted here; it is handled immediately by R-A02-015. _Decision: D-C27 (clarified), D-C04_
- **R-A02-021** (hard, METHOD) — If `cond_m` is true at `scoreboard.deterioration_reviews` consecutive monthly reviews, the app MUST raise an RS-deterioration flag: a review/reduce Alert on every holding with look-through exposure to that industry (A09) and a block on new buys in that industry. _Sources: S16, S17, S20 ("drops out of top group for 1–2 months"). Decision: D-C27 (clarified: 2 reviews apply to the top-group drop only)_
- **R-A02-022** (hard, METHOD) — RS deterioration MUST NOT create a sell order; only price-based exits are automatic (A07). _Decision: D-C27, D-C26_
- **R-A02-023** (hard, METHOD) — Weekly statuses between monthly reviews MUST NOT count toward the consecutive count; a review with `cond_m = false` resets the count to 0. _Decision: D-C27_
- **R-A02-024** (hard, METHOD) — An active flag MUST clear at the first monthly review with `cond_m = false` and a status other than red; while the industry is red, the block of R-A02-015 stays in force. _Decision: D-C27, D-DEF-03_

### 5.4 Moving-average slope ("rising" test)
- **R-A02-025** (hard, CORE) — An SMA is `rising` if its normalized linear-regression slope over the last `scoreboard.ma_slope_window_sessions` values is > `scoreboard.ma_slope_flat_band_pct`, `falling` if < −band, else `flat`. Every "rising"/"falling" test in A02 and A06 (rising 50-SMA) MUST use this test; the A07 trend exit has no slope condition (`exit.trend_requires_rising_ma` fixed false, D-R35). SMA, not EMA. _Sources: S13 ("Simple moving average, not exponential"), S07, S25. Decision: D-OPEN-2, D-R01, D-C05_
- **R-A02-026** (hard, CORE) — With fewer than `scoreboard.ma_slope_window_sessions` SMA values the slope is `undefined` and MUST be treated as not rising.

### 5.5 Market regime
- **R-A02-027** (hard, CORE) — For each market (local benchmark) and for the global benchmark: `bullish` if close > SMA_N AND SMA_N rising; `bearish` if close < SMA_N AND SMA_N falling; otherwise `sideways`; N = `scoreboard.regime_ma_length_days`, rising/falling per R-A02-025. _Decision: D-OPEN-4, D-R02_
- **R-A02-028** (hard, CORE) — The regime is computed on daily closes and published with each weekly snapshot; a consumer (e.g. A07 profit-taking matrix, D-OPEN-4) MUST use the regime of the local benchmark of the instrument's market; the global regime is informational. Consumers include the A07 extension matrix and the bearish-only quick win (D-R15). _Decision: D-OPEN-4, D-R02, D-R15_
- **R-A02-029** (soft, CORE) — Regime filters on 200-day / 10-month SMA or 12-month return > 0 (absolute momentum) are permitted only as profile options (A13), not as METHOD exits. _Sources: S16, S17, S27. Decision: D-C05_
- **R-A02-030** (soft, CORE) — A benchmark or proxy MUST be labelled `correction` when its close is ≥ `scoreboard.correction_threshold_pct` (10) below its recent high and `bear` when ≥ `scoreboard.bear_threshold_pct` (20) below; the recent high is the highest daily close of the last `scoreboard.drawdown_high_lookback` (252) sessions; labels are context, not signals. _Sources: S10, S29. Decision: D-DEF-04, D-DEF-06_
- **R-A02-031** (soft, METHOD) — When a large IndexEvent (A01) occurs, holdings in that index whose industry is red and whose volume is below average (A04) SHOULD receive a review Alert (vulnerable to forced index selling). _Sources: S03 ("Weak relative strength + no volume = vulnerable")_

### 5.6 Heatmap and rotation reading
- **R-A02-032** (hard, METHOD) — The heatmap is a view on proxies; it MUST NOT compute or override scoreboard status. _Sources: S29, S01. Decision: D-C15_
- **R-A02-033** (hard, METHOD) — Heatmap cells show the 11 sector proxies plus the benchmark (or the industry proxies) for timeframes day (last session), week (calendar week to date) and month (trailing calendar month), in `absolute` (proxy return) or `relative` (proxy return − benchmark return) mode; default mode = `scoreboard.heatmap_default_mode`. _Sources: S29 (the method's most-used view), S01 (FINVIZ heat map)_
- **R-A02-034** (soft, METHOD) — A move SHOULD be read as having staying power only if the cell's relative return has the same sign in day, week and month views; day-only moves are labelled `wobble`. _Sources: S29, S01 ("sustained positive performance across multiple timeframes")_
- **R-A02-035** (soft, METHOD) — If on one day technology's relative return < 0, every defensive sector's (staples, utilities, health care) relative return > 0 and the equal-weight benchmark return ≥ 0, the day SHOULD be labelled `rotation_mirror` ("money moving rooms, not leaving"). _Sources: S29_
- **R-A02-036** (soft, METHOD) — If the mean relative return of defensive sectors exceeds that of growth sectors (groups per A03 `cycle.sector_groups`) on both week and month views, the app SHOULD record a `defensive_leadership` Observation (input to A03 market confirmation). _Sources: S29 ("when defensive squares beat growth for weeks, investors are getting nervous"), S30_
- **R-A02-037** (soft, METHOD) — When RS_comp crosses from ≤ SMA_50(RS_comp) to > SMA_50(RS_comp), the app SHOULD emit an `rs_crossover` event (used by A06 as the sector-RS confirmation). _Sources: S08 ("Sector RS crosses back above 50-day average")_
- **R-A02-038** (soft, METHOD) — An industry whose status is not green and whose qualifying-setup count (A06) is 0 SHOULD be labelled `pullback_mode`; A06 forbids buying the dip there. _Sources: S08_
- **R-A02-039** (soft, CORE) — The app SHOULD publish breadth per scoreboard: share of entries green, and share of proxies above a rising regime-length SMA; breadth is informational (exposure reduction on breadth is a profile variant, A13). _Sources: S01, S17, S20_

### 5.7 Cadence
- **R-A02-040** (hard, METHOD) — Scoreboards, regime and heatmap are computed for the weekly review (closing data of the last session before the review day); deterioration counting runs at the monthly review; between reviews only automated alerts run. _Sources: S13, S17 ("Weekly or daily ranking increases turnover and noise" for allocation). Decision: D-C04, D-C28_

### 5.8 Round-2 additions (2026-10-26)
- **R-A02-041** (soft, METHOD) — If an industry is green in the local view but red in the global view, the entry MUST carry `global_status_warning` and the warning is shown on the scoreboard, the watchlist and the A06 checklist; it never blocks a buy. _Decision: D-R18_
- **R-A02-042** (hard, METHOD) — The default ranking level is the A01 `classification.scoreboard_level` (GICS Industry, 74 in the US). The user MUST be able to drill up (industry group, sector) and down (sub-industry) from any row; every level is computed with the same rules (R-A02-005..013) on its own proxies. Eligibility and buy blocks are evaluated at the default level. _Decision: D-R24, D-R21_
- **R-A02-043** (soft, METHOD) — Each industry row SHOULD offer a "who is investing" view built from its A04 `SmartMoneyEvidence` panel: ETF fund flows, 13F institutional holding changes, insider and congressional trades and the volume footprint, each dated with its lag; retail flow is not shown. The view MUST NOT change status, rank, top-group membership or eligibility (R-A02-019). _Decision: D-R20, D-R22, D-R25, D-C15_
- **R-A02-044** (hard, METHOD) — Every row MUST show its proxy's type (ETF, INDEX, EQUAL_WEIGHT_BASKET) and be chartable and filterable by it; an INDEX proxy is not a buyable basket (A05). _Decision: D-R21_

### 5.9 Round-3 additions (2026-10-26)
- **R-A02-045** (soft, METHOD) — Each heatmap cell SHOULD carry a strength label scaled by the proxy's volatility: with v = ATR%(14, 63-session average, A08) of the proxy and n = sessions in the timeframe (day 1, week 5, month 21), the cell is `strong` if \|return\| ≥ `scoreboard.heatmap_strong_multiple` × v × √n, `weak` if < `scoreboard.heatmap_weak_multiple` × v × √n, otherwise `moderate` (relative return in relative mode, absolute return in absolute mode). The label is a reading aid; it MUST NOT change any status (R-A02-032). _Sources: S29 (colour only). Decision: D-DEF-05, D-X (volatility drives levels)_

## 6. Processes
**PR-A02-01 Weekly scoreboard build** — trigger: weekly close before the review day (D-C28). Inputs: daily closes of proxies, benchmarks, FX (A01). Steps: (1) per market × view compute RS_3m/6m/12m and RS_comp for each session; (2) compute SMA_50(RS_comp); (3) apply R-A02-008 data check; (4) assign status (R-A02-009..011); (5) rank, mark top RS group; (6) update weeks_in_status/newly_green; (7) emit RotationEvent and rs_crossover events; (8) compute breadth. Outputs: Scoreboard × 2 per market, eligible-industry list (R-A02-014). Cadence: weekly.

**PR-A02-02 Monthly RS review** — trigger: monthly review (A12). Steps: (1) take latest weekly snapshot; (2) evaluate cond_m per industry; (3) update DeteriorationRecord counts; (4) raise/clear flags (R-A02-021, R-A02-024); (5) emit review/reduce Alerts for affected holdings via A09 look-through. Output: flags, alerts. Cadence: monthly.

**PR-A02-03 Market regime update** — trigger: daily close (automated), published weekly. Steps: SMA_N of benchmark → slope state (R-A02-025) → regime (R-A02-027) → `regime_change` Alert if changed → drawdown labels (R-A02-030).

**PR-A02-04 Rotation read on the heatmap** — trigger: sell-off day or weekly review. Steps (S29): (1) day view, absolute; (2) week view — same pattern?; (3) month view — wobble or building?; (4) switch to relative; (5) look for the mirror (R-A02-035) and defensive leadership (R-A02-036). Output: Observations for A03; no status change.

## 7. Calculations
```
r(X, L)        = TR_X(t) / TR_X(t_L) - 1          # t_L = last session on/before t minus L calendar months
RS_L           = r(proxy, L) - r(benchmark, L)    # percentage points; global view: proxy in USD
RS_comp(t)     = 0.40*RS_3m + 0.30*RS_6m + 0.30*RS_12m
RS_sma50(t)    = mean(RS_comp[t-49 .. t])          # sessions
green          = RS_comp > 0 and RS_comp > RS_sma50
red            = RS_comp < 0 and RS_comp < RS_sma50
neutral        = otherwise
top_group_size = ceil(top_rs_group_pct/100 * n_ranked)        # D-DEF-02

# MA slope (D-OPEN-2, confirmed by D-R01)
b              = OLS slope of SMA values y[t-N+1 .. t] on x = 0..N-1     # price units per session
slope_norm_pct = b / SMA(t) * 100                                         # % per session
state          = rising if slope_norm_pct > band; falling if < -band; flat otherwise   # N=20, band=0.025

# Market regime (D-OPEN-4, confirmed by D-R02), N = 150
bullish  = close > SMA_N and state(SMA_N) = rising
bearish  = close < SMA_N and state(SMA_N) = falling
sideways = otherwise

drawdown_pct   = (1 - close / max(close over last 252 sessions)) * 100   # drawdown_high_lookback, D-DEF-04
heat_relative  = r(proxy, tf) - r(benchmark, tf)
heat_scale     = ATR%_63(proxy) * sqrt(n_tf)        # n_tf = 1 (day), 5 (week), 21 (month)
strength       = strong if |ret| >= 1.0*heat_scale; weak if |ret| < 0.5*heat_scale; else moderate   # D-DEF-05
```

## 8. Examples / fixtures
**EX-A02-01 RS composite (R-A02-005, R-A02-006)**
- Given proxy returns 3m +12%, 6m +20%, 12m +35%; benchmark 3m +4%, 6m +8%, 12m +15%.
- Then RS = 8, 12, 20 pp; RS_comp = 0.4×8 + 0.3×12 + 0.3×20 = 3.2 + 3.6 + 6.0 = **12.8**.

**EX-A02-02 Status (R-A02-009..011)**
| RS_comp | SMA_50(RS_comp) | Status |
|---|---|---|
| 12.8 | 10.5 | green |
| 12.8 | 14.0 | neutral (positive, fading) |
| −3.0 | −1.0 | red |
| −3.0 | −5.0 | neutral (negative, improving) |
| 0.0 | −2.0 | neutral (edge: not > 0) |
| 4.0 | 4.0 | neutral (edge: equality) |

**EX-A02-03 Top RS group size (R-A02-013, ceil per D-DEF-02)**
- n = 11 → 2.2 → 3; n = 12 → 2.4 → 3; n = 74 → 14.8 → 15; n = 150 → 30; n = 163 → 32.6 → 33.
- Edge: an industry ranked 31 of 150 that is green is not a buy candidate (R-A02-014).

**EX-A02-04 Local vs global view with FX (R-A02-005, R-A02-016)**
- Given KR semiconductor proxy +10.0% over 3m in KRW; KRW −5.0% vs USD; KOSPI +6.0%; MSCI ACWI +3.0% (USD).
- Then RS_3m local = 10.0 − 6.0 = 4.0 pp; USD return = 1.10 × 0.95 − 1 = 4.5%; RS_3m global = 4.5 − 3.0 = 1.5 pp.

**EX-A02-05 Insufficient data (R-A02-008)**
- Given an industry ETF listed 9 months ago. Then rs_12m undefined → status null, not eligible, shown as "insufficient data".
- Source illustration S05 (≈ June 2026, 6-month performance only): Electronic Components +82%, Aluminium +80%, Construction & Engineering +54%; Managed Health Care −67%, Publishing −30%, Auto Parts −22%, Shoes & Fashion −21%. A 6-month-only list is a valid ranking view but cannot produce D-C15 status without 3m and 12m data.

**EX-A02-06 RS deterioration (R-A02-020..024)**
| Monthly review | Weekly snapshot used | status | in_top | cond_m | count | flag |
|---|---|---|---|---|---|---|
| M1 | wk ending before M1 | green | yes | false | 0 | none |
| M2 | … | green | no (rank 34 of 150) | true | 1 | none |
| M3 | … | neutral | no | true | 2 | **active**: review/reduce alerts on holdings, new buys blocked; no sell order |
- Edge A: M2 out of the top group (count 1), M3 green & top (count reset 0) → no monthly flag. If instead the industry is red at any weekly snapshot (e.g. the one used at M2), new buys are blocked immediately and the review/reduce flag is raised at that weekly session (R-A02-015), with no monthly count.
- Edge B: out of the top group on three weekly snapshots between M1 and M2 but green & top at M2 → count stays 0 (R-A02-023).
- Edge C: flag active at M3; industry green & top at a weekly snapshot after M3 → still blocked until M4 review (R-A02-024).

**EX-A02-07 MA slope test (R-A02-025, R-A02-026; N = 20, band 0.025, D-R01)**
| SMA path over 20 sessions | slope b | SMA(t) | slope_norm | state |
|---|---|---|---|---|
| 100.00 → 101.90 (+0.10/session) | 0.100 | 101.90 | 0.0981%/session | rising |
| 100.00 → 100.38 (+0.02/session) | 0.020 | 100.38 | 0.0199% | flat |
| 100.00 → 99.05 (−0.05/session) | −0.050 | 99.05 | −0.0505% | falling |
| 100.00 → 100.475 (+0.025/session) | 0.025 | 100.475 | 0.0249% | flat (edge: just inside band) |
| only 15 SMA values available | — | — | — | undefined → not rising |

**EX-A02-08 Market regime (R-A02-027)**
| Benchmark close | SMA_150 | SMA_150 state | Regime |
|---|---|---|---|
| 5,800 | 5,600 | rising | bullish |
| 5,500 | 5,600 | rising | sideways |
| 5,500 | 5,600 | falling | bearish |
| 5,800 | 5,600 | falling | sideways |
| 5,700 | 5,600 | flat | sideways (edge) |

**EX-A02-09 Rotation mirror (R-A02-035)** — source fixture S29, Oct 2026 sell-off day.
- Given day returns: Nasdaq 100 −2.9% (~$1.2T erased); technology −3.23%; consumer defensive +3.13%; equal-weight S&P 500 (RSP) closed higher; Dow flat.
- When the heatmap is read (relative mode needs the S&P 500 day return; if S&P 500 ≈ −1%, tech ≈ −2.2 pp, staples ≈ +4.1 pp).
- Then label `rotation_mirror` provided utilities and health care are also > 0 relative; no status is changed (R-A02-032).

**EX-A02-10 Defensive leadership (R-A02-036)** — source fixture S30, month to 24 Oct 2026, relative to S&P 500.
- Given month relative returns: Energy +12%, Consumer Staples +8%, Utilities +8%, Communication Services −5%, Technology −5%.
- Then defensive mean (staples, utilities) = +8.0; growth (technology −5, communication services −5, per A03 `cycle.sector_groups`, D-DEF-12) = −5.0; spread +13.0 pp on the month view → if the week view agrees, record `defensive_leadership` Observation for A03.

**EX-A02-11 Correction label (R-A02-030)** — source fixture S29, Oct 2026.
- Given Nikkei 225 peak > 70,000 (use 70,000) and close ≈ 61,685 two weeks later.
- Then drawdown = 1 − 61,685/70,000 = 11.88% ≥ 10% → `correction`; < 20% → not `bear` (recent high = highest close of the last 252 sessions, D-DEF-04).
- Edge: a peak 260 sessions ago is outside the 252-session lookback and is not the recent high.

**EX-A02-12 Red blocks buys (R-A02-015)**
- Given a stock with a valid heartbeat breakout (A06) in an industry with status red. Then the entry is rejected at the scoreboard gate regardless of the stock's chart.

**EX-A02-13 Index inclusion review (R-A02-031)** — S03 (Tesla, Dec 2020).
- Given IndexEvent (S&P 500 addition, ≈ $50B forced selling of other constituents) and a holding whose industry is red with volume below its 50-day average. Then a review Alert is raised; no order.

**EX-A02-14 Global red is a warning (R-A02-016, R-A02-041; D-R18)**
- Given a KR industry with local RS_comp +4.0 above its rising RS average (green, top group) and global RS_comp −2.5 below its average (red).
- Then the industry is eligible for new buys with `global_status_warning`; with local neutral and global green it is not eligible.

**EX-A02-15 Default level and drill-down (R-A02-042; D-R24)**
- Given the US scoreboard at the industry level (74 rows → top RS group ceil(14.8) = 15).
- When the user drills up from "Semiconductors & Semiconductor Equipment" (industry) to Information Technology (sector, 11 rows → top 3) and down to "Semiconductors" (sub-industry, 163 rows → top 33). Then each level shows its own proxies and statuses; eligibility still follows the industry row.

**EX-A02-16 Heatmap strength (R-A02-045; D-DEF-05)** — synthetic.
- Given a sector proxy with ATR%(14, 63-session average) = 1.5 %/day and a relative return of +2.0 pp in each timeframe.
- Day: scale 1.5 × √1 = 1.50 → 2.0 ≥ 1.50 → `strong`. Week: 1.5 × √5 = 3.354; weak below 1.677 → 2.0 → `moderate`. Month: 1.5 × √21 = 6.874; weak below 3.437 → 2.0 → `weak`.
- The same +2.0 pp on a proxy with ATR% 3.0 is `moderate` on the day view (scale 3.0, weak below 1.5).

## 9. Variants & open points
- Variant (not chosen): binary green/red (S13, S25) — replaced by three states (D-C15).
- Variant (not chosen): single-lookback rankings (6-month in S05; 3/6/12 or 12-1 in S16/S17), 1/3/6 composites (S17 Strategy C), monthly-only ranking (S17, S20) — D-C15 fixes 3/6/12 weighted on weekly close; monthly ranking review remains for deterioration (D-C04).
- Variant (not chosen): RS vs global benchmark only (S19) — D-C15b requires both views.
- Variant: regime filters on 200-day / 10-month SMA or SPY 12-month return < 0 → cash (S16, S17); allowed as profile options (D-C05, A13).
- Variant: daily/weekly/monthly multi-timeframe RS (S01) is covered by the heatmap view, not by status.
- Closed by D-DEF-02 — OPEN-A02-2 (top-group rounding = ceil; pending user review).
- Closed by D-DEF-03 — OPEN-A02-3 (flag clears at the first monthly review with `cond_m` false and status not red; pending user review).
- Closed by D-DEF-04 — OPEN-A02-4 (recent high = 252-session high; pending user review).
- Closed by D-DEF-05 — OPEN-A02-5 (volatility-scaled heatmap strength; pending user review).
- Bear-market threshold 20 % confirmed by D-DEF-06 (pending user review).
- Variant (not chosen): global view or both views gating eligibility — local green gates, global red warns (D-R18).

Closed by round-2 decisions (2026-10-26): OPEN-A02-1 (D-R18). MA slope N = 20 / band 0.025%/session (D-OPEN-2) and the regime definition with N = 150 (D-OPEN-4) are confirmed (D-R01, D-R02).

### Glossary additions (merged into glossary v0.2.0)
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| rotation-mirror | Rotation Mirror | METHOD | Heatmap pattern where growth sectors fall while defensive sectors rise on the same day and the equal-weight market holds up: money is moving between sectors, not leaving the market. | S29 |
| newly-green | Newly Green | METHOD | Scoreboard flag for an industry whose status changed to green at the latest weekly snapshot ("turned bullish recently"). | S05 |

## 10. Traceability
| Rule/Concept | Sources / Decisions |
|---|---|
| R-A02-001..008 construction | S13, S19, S20; D-C14, D-C15, D-C15b, D-C21, D-OPEN-1 |
| R-A02-009..019 status, ranking, eligibility | S05, S13, S20, S25, S30; D-C06, D-C07, D-C15, D-C25, D-OPEN-1 |
| R-A02-020..024 RS deterioration | S16, S17, S20; D-C04, D-C26, D-C27 |
| R-A02-025..026 MA slope | S07, S13, S25; D-C05, D-OPEN-2 |
| R-A02-027..031 regime, labels | S03, S10, S16, S17, S27, S29; D-C05, D-OPEN-4 |
| R-A02-032..039 heatmap, rotation reading | S01, S08, S17, S20, S29, S30; D-C15 |
| R-A02-040 cadence | S13, S17; D-C04, D-C28 |
| R-A02-041..044 global warning, drill-down, who-is-investing view, proxy type | D-R18, D-R20, D-R21, D-R22, D-R24, D-R25 |
| R-A02-045 heatmap strength | S29; D-DEF-05 |
| R-A02-024, R-A02-030 flag clearing, drawdown labels | D-DEF-03, D-DEF-04, D-DEF-06 |
| EX-A02-05, -09, -10, -11, -13 | S05, S29, S30, S29, S03 |
