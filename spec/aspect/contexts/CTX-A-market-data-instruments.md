---
id: CTX-A
title: Market Data & Instruments
type: bounded-context
layers: [CORE]
aspects: [A01]
status: draft
---

# CTX-A — Market Data & Instruments

## 1. Purpose

Provides the reference and price data that every other context works on: markets, exchanges and trading calendars, currencies, instruments (stocks, ETFs/UCITS funds, bonds, indices, bullion), orders and brokers. Owns the classification of companies into industries per market. The invariant is Market → ClassificationScheme → Industry hierarchy → Company; GICS is the scheme for all markets (D-C14, D-R42); local schemes are additional views only. It also defines the benchmarks: local per market, and global MSCI ACWI (D-C15b), and one `IndustryProxy` per classification node and level (ETF > official index > equal-weight basket of at least 5 members; D-R20, D-R21) so that every industry can be charted and filtered. Liquidity floors (stocks $5M, ETFs AUM $100M and $2M traded per day) and a 60 % purity minimum for industry ETFs apply (D-R43).

## 2. Aspects in this context

| Aspect | Title | Rules | Processes | Examples |
|---|---|---|---|---|
| [A01](../A01-market-structure-instruments.md) | Market Structure & Instruments | 51 | 4 | 14 |

## 3. Entities owned or primarily shaped here

`Market`, `Exchange`, `TradingCalendar`, `FxRate`, `ClassificationScheme`, `ClassificationNode`, `IndustryProxy`, `Company`, `Instrument`, `Stock`, `Index`, `Benchmark`, `PriceBar`, `IndexEvent`, `BullionItem`, `Order`, `Broker`

The full attribute tables are in the aspect specs (section 3 of each).

## 4. Context relations

- **Upstream:** External market-data, fundamentals, fund-composition and broker APIs (anti-corruption layer).
- **Downstream:** All contexts. CTX-B consumes PriceBar, Benchmark and ClassificationScheme. CTX-C consumes Instrument and Order. CTX-D consumes FxRate, Instrument and Holding valuation.

## 5. Context invariants

- Every Company belongs to exactly one leaf node of the ClassificationScheme of its governing Market; a multi-listed company is governed by its primary listing market (R-A01-048, D-R42).
- Daily close and session calendar are defined per Exchange; all 'daily close' rules use the official close of the instrument's primary exchange.
- Prices are stored in instrument currency; conversion to the portfolio base currency uses FxRate at the as-of date.
- Every classification node of an enabled market has exactly one primary IndustryProxy with a visible proxy type (R-A01-043..046, D-R21).
