---
id: CTX-E
title: Process & Coaching
type: bounded-context
layers: [METHOD, PROFILE]
aspects: [A12, A13]
status: draft
---

# CTX-E — Process & Coaching

## 1. Purpose

Organises the human side: the weekly routine (default Saturday) and the monthly review, with daily work limited to automation (D-C04, D-C28). It holds the written PersonalRuleSet with its revision history, the trade journal and review log, paper trading, the 90-day learning path, behavioural guardrails and the rules for an LLM coach. It also owns StrategyProfiles: the canonical method plus the non-canonical prf-beginner-index and prf-momentum-rotation, which override parameters of the other contexts.

## 2. Aspects in this context

| Aspect | Title | Rules | Processes | Examples |
|---|---|---|---|---|
| [A12](../A12-process-routine-psychology.md) | Process, Routine & Psychology | 64 | 6 | 13 |
| [A13](../A13-strategy-profiles.md) | Strategy Profiles | 44 | 4 | 13 |

## 3. Entities owned or primarily shaped here

`Routine`, `PersonalRuleSet`, `RuleSetRevision`, `LearningPath`, `SkillAssessment`, `Alert`, `StrategyProfile`, `ProfileAssignment`, `ProfileSwitch`, `MomentumRanking`

The full attribute tables are in the aspect specs (section 3 of each).

## 4. Context relations

- **Upstream:** All contexts (states, alerts, exposures, signals).
- **Downstream:** All contexts, through the active StrategyProfile's parameter overrides and the PersonalRuleSet.

## 5. Context invariants

- Exactly one active StrategyProfile per Portfolio (R-A13-003); switches at least 13 weeks apart (R-A13-069, D-DEF-39).
- Paper trading fills at the next-session open plus class slippage (R-A12-084, D-R41).
- Rules are changed only through a dated PersonalRuleSet revision, never in the heat of the moment (R-A12-*).
- The coach presents scoreboard and money-flow data as a record, not a forecast, and never recommends a trade on cycle, style or macro grounds alone (R-A12-056, R-A12-077).
