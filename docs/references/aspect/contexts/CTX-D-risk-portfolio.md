---
id: CTX-D
title: Risk & Portfolio
type: bounded-context
layers: [CORE, METHOD]
aspects: [A08, A09, A10]
status: draft
---

# CTX-D — Risk & Portfolio

## 1. Purpose

Keeps the portfolio survivable. It sizes positions (risk ≤ 1 % of equity, overnight-gap cap, inverse volatility, optional fractional Kelly; D-C09/10, D-OPEN-3) and measures look-through exposure against concentration limits (D-C11). It manages the emergency buffer and cash-like holdings (D-C24) and the fixed-income staircase (A10), and it answers 'how much may I buy?' and 'what am I really exposed to?'

## 2. Aspects in this context

| Aspect | Title | Rules | Processes | Examples |
|---|---|---|---|---|
| [A08](../A08-risk-position-sizing.md) | Risk & Position Sizing | 35 | 4 | 22 |
| [A09](../A09-portfolio-construction.md) | Portfolio Construction | 46 | 5 | 18 |
| [A10](../A10-fixed-income.md) | Fixed Income | 32 | 3 | 16 |

## 3. Entities owned or primarily shaped here

`RiskBudget`, `VolatilityClass`, `InstrumentVolatility`, `SizingDecision`, `PortfolioRiskSummary`, `OversizeFlag`, `Position`, `Portfolio`, `Holding`, `Exposure`, `ConcentrationLimit`, `ConcentrationWarning`, `BuyBlock`, `EmergencyBuffer`, `CashLike`, `Bond`, `BondFund`, `BondLadder`

The full attribute tables are in the aspect specs (section 3 of each).

## 4. Context relations

- **Upstream:** CTX-A (prices, FxRate, fund composition), CTX-B (MarketRegime, volatility inputs), CTX-C (proposed entry/stop).
- **Downstream:** CTX-C (allowed quantity, buy blocks), CTX-E (exposure and risk reports).

## 5. Context invariants

- Risk at stop per position ≤ `sizing.max_risk_pct` of equity; it is never exceeded by widening a stop (D-C08).
- Exposure is always computed look-through (holdings inside funds are counted) (D-C11).
- The emergency buffer is outside the investable portfolio (D-C24); a shortfall warns but never blocks (D-R13).
- Volatility classes LOW/MEDIUM/HIGH/EXTREME come from ATR%(14), 63-session average (D-R10, D-R11).
- A breached bucket blocks buys into it; a buy that would create a breach is warned only (D-C11, D-R14); this also holds for the theme (30 %), country (60 %, excluding the home market) and contrarian-scenario (15 %) caps (D-R45). Total open risk is displayed, never capped (D-R09).
- The 10 % cap applies per company, look-through; diversified sector/industry funds are limited by the sector/industry cap only (D-R36).
- Bond funds are allocation holdings rebalanced monthly; only high yield carries the 150-SMA trend exit (D-R38).
