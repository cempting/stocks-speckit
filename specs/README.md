---
id: SPEC-README
title: Domain specification — Financial markets, trading & investing
version: 0.1.0
status: draft
date: 2026-10-26
---

# Domain specification: Financial markets, trading & investing

This folder is the domain-specification harness for spec-driven development of an app with four capabilities: a **screener / rotation analyzer**, a **portfolio & risk tracker**, a **learning / coaching app** and a **rule-based trading assistant**. It describes the domain (vocabulary, entities, rules, processes, worked examples) without prescribing an implementation. It was distilled from 30 source documents (see the source index at the end). Their boilerplate (disclosures, bios, promotions, exercises) was stripped first. The content is educational domain modelling, not financial advice.

## Layout

```
specs/
  README.md                ← you are here: conventions, reading order, source index
  decisions.md             ← binding decisions that settle source conflicts (D-…)
  open-points.md           ← open-points register (0 open; all closed by D-R… or reviewable D-DEF… defaults)
  glossary/
    glossary.yaml          ← machine-readable vocabulary for the DSL (429 terms, v0.4.0)
    glossary.md            ← generated human-readable view of glossary.yaml
    term_ids.txt           ← slug | term | layer | primary aspect
  aspect/
    contexts/CTX-A…E-*.md  ← 5 bounded-context overviews (purpose, relations, invariants)
    A01…A13-*.md           ← 13 aspect specs (557 rules in total)
  persona/
    PER-01-active-rule-based-trader.md
  tools/gen_glossary.py    ← regenerates glossary.md / term_ids.txt and validates glossary.yaml
```

## Reading order

1. `glossary/glossary.md`: learn the vocabulary first.
2. `decisions.md`: understand which source conflicts were settled, and how.
3. `aspect/contexts/`: the big picture in five bounded contexts.
4. `persona/PER-01-…`: who uses this and what they need to achieve.
5. The aspect specs, in the order of the method: A02 scoreboard → A04 money flow → A05 selection → A06 entry → A08 sizing → A07 exit → A09 portfolio → A12 routine. Then A01, A03, A10, A11 and A13 as reference.

## Layers

| Layer | Meaning |
|---|---|
| CORE | Neutral financial-markets domain, valid for any strategy (instrument, order, moving average, yield …). |
| METHOD | The canonical "Follow the Money" method: scoreboard → basket → exit, purple line (150-SMA), yellow line (50-SMA), heartbeat base, survival check. |
| PROFILE | Alternative, non-canonical strategy profiles: `prf-beginner-index` (S14) and `prf-momentum-rotation` (S16/S17). They override parameters (A13). |
| MACRO | Macro and thematic knowledge as `Thesis` and dated `Observation` records. It never triggers trades directly; it only provides a bias or watchlist context. |

## Bounded contexts and aspects

| Aspect | Spec | Context | Rules | Examples |
|---|---|---|---|---|
| A01 | [Market Structure & Instruments](aspect/A01-market-structure-instruments.md) | CTX-A | 51 | 14 |
| A02 | [Market Regime & Scoreboard](aspect/A02-market-regime-scoreboard.md) | CTX-B | 45 | 16 |
| A03 | [Business Cycle & Macro Indicators](aspect/A03-business-cycle-macro-indicators.md) | CTX-B | 33 | 13 |
| A04 | [Money Flow & Volume](aspect/A04-money-flow-volume.md) | CTX-B | 48 | 14 |
| A05 | [Security Selection](aspect/A05-security-selection.md) | CTX-C | 48 | 15 |
| A06 | [Entry Rules](aspect/A06-entry-rules.md) | CTX-C | 38 | 18 |
| A07 | [Exit & Selling](aspect/A07-exit-selling.md) | CTX-C | 43 | 30 |
| A08 | [Risk & Position Sizing](aspect/A08-risk-position-sizing.md) | CTX-D | 35 | 22 |
| A09 | [Portfolio Construction](aspect/A09-portfolio-construction.md) | CTX-D | 46 | 18 |
| A10 | [Fixed Income](aspect/A10-fixed-income.md) | CTX-D | 32 | 16 |
| A11 | [Macro Themes](aspect/A11-macro-themes.md) | CTX-B | 30 | 17 |
| A12 | [Process, Routine & Psychology](aspect/A12-process-routine-psychology.md) | CTX-E | 64 | 13 |
| A13 | [Strategy Profiles](aspect/A13-strategy-profiles.md) | CTX-E | 44 | 13 |

| Context | Spec |
|---|---|
| CTX-A | [Market Data & Instruments](aspect/contexts/CTX-A-market-data-instruments.md) |
| CTX-B | [Market Analysis](aspect/contexts/CTX-B-market-analysis.md) |
| CTX-C | [Selection & Signals](aspect/contexts/CTX-C-selection-signals.md) |
| CTX-D | [Risk & Portfolio](aspect/contexts/CTX-D-risk-portfolio.md) |
| CTX-E | [Process & Coaching](aspect/contexts/CTX-E-process-coaching.md) |

## IDs (stable, never reuse)
- Glossary term:  `kebab-case` slug, e.g. `purple-line`, referenced in text as [[purple-line]]
- Entity:         PascalCase, e.g. `Position`, `StopOrder`, `Scoreboard`, referenced as `Position`
- Rule:           R-<ASPECT>-<NNN>, e.g. R-A07-003   (ASPECT = A01..A13)
- Parameter:      dotted snake_case, e.g. `exit.trend_ma_length`  (declared once, in the aspect that owns it)
- Process:        PR-<ASPECT>-<NN>
- Example/fixture: EX-<ASPECT>-<NN>
- Decision:       D-C01 .. D-C29, D-H, D-X, D-S14, D-L1..D-L5, D-OPEN-1..4, D-R01 .. D-R45, D-DEF-01 .. D-DEF-42 (reviewable defaults) (see specs/decisions.md)
- Source:         S01..S30 (see specs/README.md source index)
- Persona:        PER-01
- Context:        CTX-A .. CTX-E

Normative keywords follow RFC 2119 (MUST, MUST NOT, SHOULD, MAY). Every rule is marked *hard* (the system enforces it) or *soft* (a guideline, warning or default).

## Aspect spec template (specs/aspect/Axx-<slug>.md)
```
---
id: A07
title: Exit & Selling
context: CTX-C
layers: [CORE, METHOD]
status: draft
sources: [S13, S23, S25, ...]
decisions: [D-X, D-C08, D-C26]
depends_on: [A02, A08]
---
# A07 — Exit & Selling
## 1. Purpose & scope            (what this aspect covers / explicitly excludes)
## 2. Concepts                   (bullets of glossary refs [[term]] with 1-line role in this aspect; definitions live in glossary)
## 3. Entities                   (table: Entity | Attribute | Type/unit | Constraints | Notes)  + states/lifecycle if any
## 4. Parameters                 (table: Parameter | Default | Allowed range | Unit | Decision/Source)
## 5. Rules                      (one per row/bullet: **R-A07-001** (hard|soft, LAYER) — normative statement. _Sources: S13, S23. Decision: D-C26_)
## 6. Processes                  (PR-.. numbered steps, trigger, inputs, outputs, cadence)
## 7. Calculations               (formulas with units, in code blocks)
## 8. Examples / fixtures        (EX-..: Given / When / Then with concrete numbers; dated where time-bound)
## 9. Variants & open points     (alternatives from sources not chosen, with decision ref; remaining open questions marked OPEN-Axx-n)
## 10. Traceability              (table: Rule/Concept -> Sources)
```
Keep each rule atomic and testable. Never invent parameter values: use the decisions; if neither sources nor decisions give a value, mark it `OPEN` and list it in section 9.

## How to use this in spec-driven development

- **DSL vocabulary:** generate types and enums from `glossary.yaml` (`kind`, `layer`, `parameters`, `formula`). Rules refer to terms only by slug.
- **Configuration schema:** the parameter tables (section 4 of each aspect) form the configuration surface. Owner prefixes are `market.*`, `instrument.*` and `classification.*` (A01); `scoreboard.*` (A02); `cycle.*` (A03); `volume.*` (A04); `selection.*` and `fundamentals.*` (A05); `entry.*` (A06); `exit.*` (A07); `sizing.*` and `risk.*` (A08); `portfolio.*` and `cash.*` (A09); `bonds.*` (A10); `macro.*` (A11); `routine.*` (A12); `profile.*` (A13). Strategy profiles override these.
- **Acceptance tests:** each `EX-…` fixture (Given / When / Then with concrete numbers) maps 1:1 to an executable test. Hard rules are invariants for property-based tests.
- **Traceability:** every rule cites its sources (S01–S30) and decisions (D-…). Section 10 of each aspect holds the trace table.
- **Change process:** all open points are closed; `D-DEF-…` defaults await user review. To change one, or to settle a new open point → add a `D-…` entry to `decisions.md` → update the aspect (parameter, rule, example) → regenerate the glossary with `python3 tools/gen_glossary.py` if terms changed.

## Source index

Source files live in `../docs/markdown/` (text extracted from the PDFs in the parent folder). `2026_03_09_metals_trend` is image-only and was not used.

| ID | File |
|---|---|
| S01 | 2026_01_25_Following Institutional Money Flow - A Beginner's Guide to Stock Selection.md |
| S02 | 2026_06_02_The Last Easy Wealth Opportunities in 2026 — Goat Academy Research.md |
| S03 | 2026_06_07_Space_Opportunity_Workbook.md |
| S04 | 2026_06_08_ADPT — Adaptive Biotechnologies Research Report _ Goat Academy.md |
| S05 | 2026_06_14_Index_Fund_Trap_Workbook.md |
| S06 | 2026_06_15_The Market Collision workbook.md |
| S07 | 2026_06_28_The 90-Day Playbook.md |
| S08 | 2026_07_06_Goat Academy Research _ The New Fed Chair & Your Portfolio.md |
| S09 | 2026_07_10_The Interest Income Playbook — Goat Academy Research.md |
| S10 | 2026_07_14_Goat_Academy_Nvidia_AI_Infrastructure_Report.md |
| S11 | 2026_07_17_Goat_Academy_NSC_RESEARCH_REPORT.md |
| S12 | 2026_07_22_nvidia_ai_semis_report.md |
| S13 | 2026_08_08_Goat_Academy_Trading_Workbook.md |
| S14 | 2026_08_08_felix-prehn-trading-beginner-guidelines.md |
| S15 | 2026_08_08_goat-academy-trading-rules-and-risk-management.md |
| S16 | 2026_08_08_industry-rotation-strategies-and-backtests.md |
| S17 | 2026_08_08_sector-rotation-etf-strategies-and-backtests.md |
| S18 | 2026_08_09_business-cycle-phase-determination-llm-guidelines.md |
| S19 | 2026_08_09_global-industry-rotation-and-stock-selection.md |
| S20 | 2026_08_09_when-to-switch-industries-growth-value-economic-conditions.md |
| S21 | 2026_08_12_AI and Gold and Silver - Goat Academy.md |
| S22 | 2026_08_14_Quantum Computing_ The Second Wave — Goat Academy Research.md |
| S23 | 2026_08_15_Goat_Academy_Selling_Workbook.md |
| S24 | 2026_08_17_The Petrodollar Collapse - Goat Academy Research.md |
| S25 | 2026_08_22_Goat_Academy_How_to_Invest_Like_The_1_Percent_1.md |
| S26 | 2026_08_24_The September 9th Money-Printing Flood — Goat Academy Research.md |
| S27 | 2026_08_26_The Weaponized Dollar — Goat Academy Research.md |
| S28 | 2026_10_21_get-the-last-time-central-banks-did-this-gold-went-vertical-research-report-for-free.md |
| S29 | 2026_10_23_get-the-unthinkable-is-about-to-happen-to-your-portfolio-research-report-for-free.md |
| S30 | 2026_10_24_How to Survive the AI Bubble - Prehn Institute Workbook.md |
