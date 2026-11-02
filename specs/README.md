---
id: SPEC-README
title: Domain specification — Financial markets, trading & investing
version: 0.2.0
status: draft
date: 2026-11-02
---

# Domain specification: Financial markets, trading & investing

This folder contains the normative domain specifications used for spec-driven development of an app
with four capabilities: a **screener / rotation analyzer**, a **portfolio & risk tracker**, a
**learning / coaching app** and a **rule-based trading assistant**. Supporting domain references,
including the glossary and persona, live under `../docs/`. The material describes vocabulary,
entities, rules, processes, and worked examples without prescribing an implementation. It was
distilled from 30 source documents (see the source index at the end). Their boilerplate
(disclosures, bios, promotions, exercises) was stripped first. The content is educational domain
modelling, not financial advice.

## Current Application Authority (2026-11-02)

The numbered feature specifications define the implemented or accepted screener scope; the
domain aspects describe broader educational concepts, not permission to add portfolio, coaching,
trading, international-taxonomy, or automatic-proxy capabilities to this release.
The [constitution](../.specify/memory/constitution.md) governs development.
For overlapping application requirements, use the following explicit authority map rather than
treating every historical plan as a simultaneous implementation instruction:

There are **nine active application specifications**. Overlapping features 003, 005, and 007
have been merged into 004, 006, and 008 respectively; their original paths now redirect to the
owning specification and map every original functional requirement. Distinct features remain
separate. Educational aspects and their decisions have not been merged into application scope.

| Active feature | Sole ownership | Dependencies and boundaries |
|---|---|---|
| [001: Technical analysis and component scores](001-market-leadership-screener/spec.md) | Technical criteria, adaptive consolidation heuristic, financial metric definitions and peer percentiles | No root navigation, index controls, table layout, or aggregate-score authority; cohort context follows 012 on adoption |
| [002: Fundamental matrix](002-fundamental-grading-layout/spec.md) | Three-column/eight-metric layout, commentary, EPS consistency and quarterly history | Rendered on current stock surfaces, not a third root tab; does not redefine 001 scores or 011 risk warnings |
| [004: Live Discovery and explorer](004-sector-stock-explorer/spec.md) | Two root tabs, yfinance-only live path, progressive tapes, industry momentum, chart/control baseline and stable navigation; absorbs 003 | Consumes 006 table, 008 representations and 010 releases; 012 adds versioned nested membership and within-Discovery stock lookup |
| [006: Stock comparison table](006-stock-table-columns/spec.md) | Exactly five columns, CAP Type thresholds, complete equal-weight Total Score, explicit loading and evidence states; absorbs 005 | Component formulas remain 001; peer membership/context follows 012, without hidden loads or changed aggregate weights |
| [008: Industry representations and momentum](008-industry-representation-tools/spec.md) | Exact approved ETF/basket momentum, all active-node statuses, review worklists, weights, dates and approval provenance; absorbs 007 | 004 owns display controls, 009 collects candidates, 010 publishes files; new custom scopes need reviewed applicability |
| [009: Local ETF research](009-local-etf-discovery/spec.md) | Safe literal collection, immutable occurrences/decisions, conflicts/currentness and provenance | Candidate research is not representation approval; optional failures do not remove unrelated approved coverage |
| [010: Manifest CSV catalogs](010-manifest-csv-catalogs/spec.md) | File/source authority, file-only review storage, release validation/publication and safe legacy cutover | Lifecycle/file foundation and runtime snapshot consumption exist; governed review, reconciliation and retirement are not claimed complete |
| [011: Company-risk evidence](011-company-risk-evidence/spec.md) | Cash-flow risk warnings, structured issuer evidence, business/moat/orders, source permissions and safe acquisition | Preserves 001/002/006 calculations and layout; enrichment never approves or changes classification |
| [012: Stock identity and memberships](012-stock-industry-memberships/spec.md) | Custom overlapping stock memberships, deeper single-parent hierarchy, identity ownership, deduplicated rollups, contextual peers and migration | Bounded versioned revision of 010 cardinality/hierarchy; reviewed migration remains required, not implied by documentation or partial code |

### Consolidation and precedence

| Replaced feature | Active owner | Preserved baseline |
|---|---|---|
| [003: Industry momentum](003-industry-momentum-table/spec.md) | [004](004-sector-stock-explorer/spec.md) | [Original stories, FR/SC IDs and assumptions](003-industry-momentum-table/historical-spec.md) |
| [005: Contained stock score](005-contained-stock-score/spec.md) | [006](006-stock-table-columns/spec.md) | [Original stories, FR/SC IDs and assumptions](005-contained-stock-score/historical-spec.md) |
| [007: Industry ETF momentum](007-industry-etf-momentum/spec.md) | [008](008-industry-representation-tools/spec.md) | [Original stories, FR/SC IDs and assumptions](007-industry-etf-momentum/historical-spec.md) |

1. The constitution governs development; this map assigns requirement ownership, not new scope.
2. Read the active owner for overlapping behavior. Replaced feature IDs remain historical
   references, not additional backlogs. Qualify repeated IDs by feature (for example `006 FR-006`).
3. 004 owns current navigation: exactly Discovery and Industry Deep-Dive, one progressive tape
   at a time, no provider/fixture modes, no restored index or obsolete multi-sector controls.
   The one-day calculation remains defined without requiring a removed one-day selector.
4. 006 owns the latest stock-table amendment: **Price chart + 50 MA, Volume chart, Ticker
   (including company name), CAP Type, Total Score**. No separate Name/price/component-score/
   status/date columns. Sector/industry metadata uses 004's existing tooltips and context.
5. 010 overrides earlier database, embedded-catalog, and automatic-proxy proposals. 012 overrides
   only its explicitly revised identity, cardinality, hierarchy, rollup, peer-context and lookup
   behavior through a reviewed version boundary. Neither ordinary enrichment nor this merge
   migrates releases or transfers approvals to a new classification.
6. Plans, research, data models, contracts, quickstarts, checklists and tasks retain original
   evidence and IDs. Conflicting historical instructions are not current implementation authority;
   reconcile them against their active owner and 010/012 before execution. Preserve completed
   markers and test records; documentation consolidation is not implementation verification.

Feature 012 is the active specification for the mapping revision. It requires a reviewed,
versioned migration rather than silently changing existing releases. The unchanged issuer-evidence
safeguards in [feature 011](011-company-risk-evidence/spec.md) remain a separate dependency;
company enrichment does not authorize classification changes. Feature 012 has an
[implementation plan](012-stock-industry-memberships/plan.md), [research](012-stock-industry-memberships/research.md),
[data model](012-stock-industry-memberships/data-model.md),
[migration/interface contracts](012-stock-industry-memberships/contracts/), and
[test-first implementation tasks](012-stock-industry-memberships/tasks.md).
The approved 2026-11-02 refinements define per-request evidence reuse, separately
permitted stored business/moat sharing, and listing/issuer-bounded history observations.
The [active feature pointer](../.specify/feature.json) remains 012. Run `/speckit-analyze` for that
feature next; consolidation does not change the pointer or claim either migration is implemented.

### File-only catalog invariants

- One stock CSV per region: effective rows reference exact reviewed industries, optionally
  sub-industries in the legacy 010 model. On reviewed adoption of 012, explicit dated membership
  associations support concurrent industries and deeper single-parent nesting in one named custom
  scheme; root industries own a sector and descendants inherit it. Do not claim official GICS
  authority for that custom scheme. Retained old releases keep their original interpretation.
- One manifest consolidates hierarchy, stocks/listings, sector/industry/sub-industry ETFs,
  benchmark configuration, and retained governance/research source roles.
- Instrument listings are distinct from approved classification mappings. Blank hierarchy
  fields in the existing sector ETF CSV do not establish reviewed GICS relationships.
- No production embedded ETF/stock/benchmark catalogs, automatic approval, parent replacement,
  or automatic largest-stock/index/basket selection. Synthetic fixtures stay test-only.
- Missing/invalid required sources prevent activation; altered active sources are explicitly
  invalid/unavailable. Optional research failures remain partial/failed research, not proof of
  removal or loss of unrelated approved coverage.
- Preserve scoped identities, listing verification, dates, approvals, basket weights, and
  provenance. File-only migration accounts for legacy records without silently approving or
  deleting them. The provider, calculations, valid UI behavior, and market-data caches are not
  replaced by this catalog redesign.

### Historical artifacts and implementation status

Plans, research, data models, contracts, quickstarts, and task records retain design and
implementation evidence. In particular, supporting artifacts under replaced features 003/005/007
are historical unless explicitly retained by the active owner as a compatible supporting contract.
Their SQL schemas,
separate JSON catalog configuration, fixed ticker assumptions, and automatic proxy proposals
are superseded wherever they conflict with 010. Explicit notices identify the affected storage
artifacts; this directory-wide precedence also applies when opening an older task or checklist alone.
Completed task markers and prior test results are retained, not reopened or claimed as validation
of the new requirements. Unfinished historical tasks must be reconciled before further execution.

Feature 010 has design artifacts and partially implemented file-release/runtime work, not a
completed legacy migration. Its [tasks](010-manifest-csv-catalogs/tasks.md) track remaining work;
do not reset its status to specification-only, replay a database plan, or invent command flags.
Features 011 and 012 have their own design artifacts/tasks and remain separate requirements.
Neither draft status nor checked historical tasks establish that all current acceptance criteria pass.
Broader aspect rules and example tickers remain educational/test reference material, not seeds
for production catalogs or automatic representation approval. See [D-F010](decisions.md).

## Layout

```
specs/
  README.md                ← you are here: conventions, reading order, source index
  decisions.md             ← binding decisions that settle source conflicts (D-…)
  open-points.md           ← open-points register (0 open; all closed by D-R… or reviewable D-DEF… defaults)
  aspect/
    contexts/CTX-A…E-*.md  ← 5 bounded-context overviews (purpose, relations, invariants)
    A01…A13-*.md           ← 13 aspect specs (557 rules in total)

docs/
  glossary/
    glossary.yaml          ← machine-readable vocabulary for the DSL (429 terms, v0.4.0)
    glossary.md            ← generated human-readable view of glossary.yaml
    term_ids.txt           ← slug | term | layer | primary aspect
  persona/
    PER-01-active-rule-based-trader.md
  tools/gen_glossary.py    ← regenerates glossary.md / term_ids.txt and validates glossary.yaml
```

## Reading order

For application work, start with the authority map above, then the active owning specification,
its directly relevant contracts, and the reconciled plan/tasks. Read 010 for publication and 012
for the pending identity/membership boundary. Do not start a new feature from a replaced spec.

For the separate educational domain:

1. `../docs/glossary/glossary.md`: learn the vocabulary first.
2. `decisions.md`: understand which source conflicts were settled, and how.
3. `aspect/contexts/`: the big picture in five bounded contexts.
4. `../docs/persona/PER-01-…`: who uses this and what they need to achieve.
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

- **DSL vocabulary:** generate types and enums from `../docs/glossary/glossary.yaml` (`kind`, `layer`, `parameters`, `formula`). Rules refer to terms only by slug.
- **Configuration schema:** the parameter tables (section 4 of each aspect) form the configuration surface. Owner prefixes are `market.*`, `instrument.*` and `classification.*` (A01); `scoreboard.*` (A02); `cycle.*` (A03); `volume.*` (A04); `selection.*` and `fundamentals.*` (A05); `entry.*` (A06); `exit.*` (A07); `sizing.*` and `risk.*` (A08); `portfolio.*` and `cash.*` (A09); `bonds.*` (A10); `macro.*` (A11); `routine.*` (A12); `profile.*` (A13). Strategy profiles override these.
- **Acceptance tests:** each `EX-…` fixture (Given / When / Then with concrete numbers) maps 1:1 to an executable test. Hard rules are invariants for property-based tests.
- **Traceability:** every rule cites its sources (S01–S30) and decisions (D-…). Section 10 of each aspect holds the trace table.
- **Change process:** all open points are closed; `D-DEF-…` defaults await user review. To change one, or to settle a new open point → add a `D-…` entry to `decisions.md` → update the aspect (parameter, rule, example) → regenerate the glossary with `uv run --with pyyaml python ../docs/tools/gen_glossary.py` if terms changed.

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
