---
id: CTX-C
title: Selection & Signals
type: bounded-context
layers: [CORE, METHOD]
aspects: [A05, A06, A07]
status: draft
---

# CTX-C — Selection & Signals

## 1. Purpose

Turns analysis into decisions on individual instruments. It drills down from a green industry to a basket and then to holdings, applies the mandatory survival veto (incl. the independent debt veto, D-R23, D-R30) and the optional Quality / Growth / Cash Flow scorecard (D-C03, D-C18, D-R28), and maintains watchlists. It evaluates the entry checklist (breakout on ≥2× volume, above a rising 50-SMA, never below the 150-SMA; D-C06), and it creates the ExitPlan before the buy. It also runs all exit triggers: trend exit, protective stop, profit-taking, and first-to-fire precedence (D-X, D-C26).

## 2. Aspects in this context

| Aspect | Title | Rules | Processes | Examples |
|---|---|---|---|---|
| [A05](../A05-security-selection.md) | Security Selection | 48 | 4 | 15 |
| [A06](../A06-entry-rules.md) | Entry Rules | 38 | 3 | 18 |
| [A07](../A07-exit-selling.md) | Exit & Selling | 43 | 6 | 30 |

## 3. Entities owned or primarily shaped here

`Industry`, `Basket`, `Company`, `FundamentalCheck`, `Scorecard`, `ScorecardCriterion`, `ScorecardResult`, `ValuationContext`, `ExternalScore`, `ResearchReport`, `TechnicalSetup`, `Watchlist`, `WatchlistEntry`, `EntryChecklist`, `Signal`, `Order`, `StopOrder`, `ExitPlan`, `Position`, `ExitTrigger`, `Alert`

The full attribute tables are in the aspect specs (section 3 of each).

## 4. Context relations

- **Upstream:** CTX-B (Scoreboard, TechnicalSetup, Breakout, MarketRegime), CTX-A (Instrument, fundamentals, Order), CTX-D (allowed size, buy blocks).
- **Downstream:** CTX-D (Position opened/closed, risk at stop), CTX-E (journal, review log, alerts).

## 5. Context invariants

- No buy without a complete ExitPlan and a size from CTX-D in the same sitting (R-A06-*, R-A07-*).
- An industry with red status, or one under a buy block, cannot receive new buys (D-C11, D-C27).
- Stops only move up; only price-based exits execute automatically, as market-on-open orders with the broker stop live in parallel (D-C12, D-C27, D-R16).
- Entries are close-confirmed by default and every class-scaled threshold uses the volatility class of A08 (D-R03, D-R05, D-R07, D-R08).
- Smart-money evidence may raise priority or a review flag but never passes a check or fires an exit (D-R25, D-R33).
- Every position has a live broker stop; the only sanctioned exception is a physical holding (e.g. bullion), which exits via price alert and manual sale (R-A07-043, D-R39). Stops are raised at each weekly review to the new last buyer area (D-R34); the trend exit fires on any close below the 150-SMA (D-R35).
