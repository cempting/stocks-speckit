---
id: CTX-B
title: Market Analysis
type: bounded-context
layers: [CORE, METHOD, MACRO]
aspects: [A02, A03, A04, A11]
status: draft
---

# CTX-B — Market Analysis

## 1. Purpose

Answers 'where is the money going, and in what environment?' It computes the industry Scoreboard (RS composite against local and global benchmarks, green/neutral/red), moving-average states and the market regime. It also detects money-flow patterns: volume multiples, heartbeat bases (thresholds scaled by volatility class, D-R06), breakouts, the staircase uptrend, and rising price on fading volume, and it keeps dated money-flow evidence (ETF fund flows, 13F holdings, insider and congressional trades) as a smart-money panel per industry and stock (D-R22, D-R25). The scoreboard ranks at the GICS Industry level by default with drill-down (D-R24). It assesses the business-cycle phase and the growth/value style regime, and it keeps macro Theses and dated Observations. Its outputs are biases, states and candidates. It never places trades.

## 2. Aspects in this context

| Aspect | Title | Rules | Processes | Examples |
|---|---|---|---|---|
| [A02](../A02-market-regime-scoreboard.md) | Market Regime & Scoreboard | 45 | 4 | 16 |
| [A03](../A03-business-cycle-macro-indicators.md) | Business Cycle & Macro Indicators | 33 | 3 | 13 |
| [A04](../A04-money-flow-volume.md) | Money Flow & Volume | 48 | 6 | 14 |
| [A11](../A11-macro-themes.md) | Macro Themes | 30 | 4 | 17 |

## 3. Entities owned or primarily shaped here

`Scoreboard`, `ScoreboardEntry`, `DrillDownView`, `WhoIsInvestingView`, `RelativeStrength`, `MovingAverageState`, `MarketRegime`, `Alert`, `Observation`, `CyclePhase`, `StyleRegime`, `Thesis`, `PriceBar`, `VolumeProfile`, `HeartbeatBase`, `Breakout`, `TechnicalSetup`, `InsiderTransaction`, `FundFlow`, `InstitutionalHolding`, `CongressionalTrade`, `SmartMoneyEvidence`

The full attribute tables are in the aspect specs (section 3 of each).

## 4. Context relations

- **Upstream:** CTX-A (PriceBar, Benchmark, ClassificationScheme, Observation sources).
- **Downstream:** CTX-C uses Scoreboard status, TechnicalSetup, Breakout, MarketRegime and Thesis. CTX-D uses MarketRegime and StyleRegime. CTX-E (the weekly and monthly routine) presents snapshots.

## 5. Context invariants

- Scoreboard is a dated snapshot computed on the weekly close; it is a record, not a forecast (D-C15).
- Cycle phase and macro theses only bias; price/RS confirms (D-C25, R-A03-*, R-A11-*).
- Observations are immutable, dated and sourced; conflicts are flagged, never reconciled (D-C22).
- Money-flow evidence is dated, sourced and lag-labelled; it never changes a status and never triggers an entry or exit (R-A04-040, D-R22, D-R25).
