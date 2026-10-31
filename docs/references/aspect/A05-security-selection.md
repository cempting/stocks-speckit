---
id: A05
title: Security Selection
context: CTX-C
layers: [CORE, METHOD]
status: draft
sources: [S01, S02, S03, S04, S05, S06, S07, S08, S10, S11, S12, S13, S16, S19, S20, S21, S22, S23, S24, S25, S28, S29, S30]
decisions: [D-C02, D-C03, D-C04, D-C06, D-C11, D-C14, D-C15, D-C17, D-C18, D-C19, D-C20, D-C21, D-C22, D-C23, D-C25, D-C27, D-C28, D-OPEN-1, D-R11, D-R19, D-R21, D-R23, D-R25, D-R26, D-R28, D-R29, D-R30, D-R43, D-DEF-18, D-DEF-19, D-DEF-20, D-DEF-21]
depends_on: [A01, A02, A04]
---
# A05 — Security Selection

## 1. Purpose & scope
Defines how a candidate instrument is chosen once A02 says where money is going: the drill-down
green industry → [[basket]] (industry fund or custom basket) → individual holdings ([[industry-first-selection]]),
the mandatory fundamental [[survival-check]] veto gate (D-C03, independent debt veto D-R23/D-R30), the optional transparent scorecard
with the pillars Quality / Growth / Cash Flow, lens-dependent weights and a pass score of 60 (D-C18..D-C20, D-R26,
D-R28), valuation as context only (D-R29), the [[record-quarter]]
confirmation signal, and the `ResearchReport` entity (fundamentals only, D-C23).

Excludes: industry RS and status (A02), chart patterns and volume (A04), entry conditions, watchlist states and
orders (A06), stops/exits (A07), sizing (A08), concentration and look-through limits (A09), macro theses (A11).
A selection result is never a buy instruction: buys happen only through the A06 entry checklist.

## 2. Concepts
- [[industry-first-selection]] — the order: industry first, then vehicle.
- [[scoreboard-green]], [[scoreboard-red]], [[scoreboard-neutral]], [[top-rs-group]] — A02 inputs defining "where to look" (D-C06).
- [[rs-deterioration]] — A02 flag that blocks new selections in an industry (D-C27).
- [[basket]] — industry exposure instrument (fund or equal-weight group), D-C21.
- [[custom-industry-basket]] — fallback when no suitable fund exists in the user's market.
- [[industry-proxy]] — the instrument or index used by A02 for RS (owned by A01, D-R21); an ETF proxy is often the preferred basket, an index proxy is not buyable.
- [[smart-money-evidence]] — dated insider/institutional evidence shown on candidates; may raise priority, never eligibility (D-R25).
- [[exchange-traded-fund]], [[ucits]], [[isin-domicile]], [[expense-ratio]], [[fund-size]], [[liquidity]] — fund screening attributes (A01).
- [[look-through-exposure]], [[equal-weight-index]] — inspecting what a fund holds.
- [[industry-relative-strength]], [[rs-rating]] — ranking holdings inside a basket.
- [[survival-check]], [[cash-runway]], [[cash-burn]], [[dilution]], [[share-count]], [[net-debt]], [[interest-coverage]], [[danger-zone-flag]], [[zombie-company]] — the veto gate.
- [[scorecard]], [[scorecard-pillar]], [[scorecard-lens]], [[scorecard-score]], [[quality-scorecard]], [[growth-scorecard]], [[quality-stock]] — optional confirmations (pillars Quality / Growth / Cash Flow, D-R26, D-R28).
- [[gross-margin]], [[operating-margin]], [[net-margin]], [[roic]], [[cash-conversion]], [[levered-fcf-margin]], [[free-cash-flow]], [[operating-cash-flow]], [[debt-to-equity]], [[financial-leverage]], [[pe-ratio]], [[forward-pe]], [[earnings-consistency]], [[earnings-per-share]], [[moat]], [[pricing-power]] — scorecard metrics.
- [[total-addressable-market]], [[market-penetration]] — growth-scorecard hard criterion (TAM >= 25x).
- [[capex-to-ocf]], [[capex]] — optional criterion for capex-heavy companies.
- [[external-score]] — imported vendor score (e.g. Winston Score), attribute only (D-C20).
- [[record-quarter]], [[profitability-inflection]], [[revenue-inflection]], [[catalyst]], [[re-rating]], [[guidance]], [[remaining-performance-obligations]] — fundamental confirmations and context.
- [[research-report]] — fundamentals-only document (D-C23); chart view lives in [[technical-setup]] (A06).
- [[three-filter-screen]], [[ten-x-checklist]] — non-canonical screening variants.
- [[picks-and-shovels]], [[toll-booth-business]], [[pure-play]], [[thematic-ladder]], [[tracked-basket]] — qualified theme vocabulary (D-C21).
- [[ipo-trap]], [[value-investing]], [[valuation]], [[price-to-sales]] — rejected or subordinate selection logics.
- [[watchlist]] — destination of selected candidates (states owned by A06).

## 3. Entities
| Entity | Attribute | Type/unit | Constraints | Notes |
|---|---|---|---|---|
| Industry | id, schemeNodeId, marketId, status, inTopRsGroup, rsDeteriorationFlag | — | from A02 / A01 (D-C14) | read-only here |
| Basket | id, kind (FUND, CUSTOM_EQUAL_WEIGHT), industryId, marketId | — | D-C21 | an Instrument for FUND |
| | instrumentId (FUND), wrapper (ETF, UCITS, INDEX_FUND), isin, domicile | — | must be purchasable in user's market | A01 |
| | expenseRatioPct, aumCcy, avgDollarVolume | %, currency | — | ranking inputs |
| | industryPurity | % of holdings in target industry | 0–100 | "tracks exposure cleanly" (S19) |
| | top10WeightPct, weighting (CAP, EQUAL) | % | — | concentration inside fund (S12) |
| | externalScores[] | ExternalScore | never used in rules | D-C20 |
| BasketConstituent (new) | basketId, instrumentId, weightPct, asOf | % | sum ≈ 100 | holdings of a fund or custom basket |
| Company | id, name, instrumentIds[], industryNodeId, marketCap, ipoDate | — | — | A01 |
| FinancialSnapshot (new) | companyId, fiscalPeriodEnd, currency, revenue, grossMarginPct, operatingMarginPct, netMarginPct, roicPct, leveredFcfMarginPct, ocf, capex, fcf, cash, totalDebt, totalEquity, interestExpense, epsDiluted, sharesOutstanding, source, retrievedAt | currency, % | one per company per fiscal period | all metrics dated |
| FundamentalCheck | id, companyId, kind = SURVIVAL, asOf, fiscalPeriodEnd | — | mandatory before entry for STOCK | D-C03 |
| | quarterlyCashBurn | currency/quarter | >= 0; 0 if self-funding | from OCF − capex, non-cash items excluded; GAAP-loss proxy when nothing else exists (D-R19) |
| | burnBasisUsed, proxyFlag | enum {OCF_MINUS_CAPEX, ADJ_OPERATING_LOSS, GAAP_LOSS_PROXY}, bool | proxyFlag = true unless OCF_MINUS_CAPEX | D-R19 |
| | interestCoverTtm, interestCoverMin, marketCapTierUsd, volClass, financialsExempt | x, x, enum {MEGA_LARGE, MID, SMALL_MICRO}, enum, bool | interestCoverMin from `fundamentals.min_interest_cover` | D-R23 |
| | dataAgeQuarters | int | > `fundamentals.max_quarters_stale` → INSUFFICIENT_DATA | D-R19 |
| | runwayYears | years | INF if self-funding | — |
| | dangerZone | bool | R-A05-016 | — |
| | shareCountChangeYoYPct | % | — | dilution info |
| | result | enum PASS, FAIL, INSUFFICIENT_DATA | — | — |
| | reasons[] | text | non-empty if not PASS | — |
| Scorecard | id, version, pillars [QUALITY, GROWTH, CASH_FLOW], criteria[], lensWeights {MATURE: 40/20/40, GROWTH: 20/50/30}, passScore 60 | — | each criterion has explicit threshold and weight | D-C18, D-R26, D-R28 |
| ScorecardCriterion | id, pillar (QUALITY, GROWTH, CASH_FLOW), metric, comparator, threshold, thresholdKind (ABSOLUTE, PEER_RELATIVE, BOOLEAN_EVIDENCE), weight, hard, lensScope (BOTH, GROWTH_ONLY) | — | threshold MUST be set to be active | D-C18, D-R26 |
| ScorecardResult (new) | scorecardId, version, companyId, asOf, lens (MATURE, GROWTH), rows[] {criterionId, value, status PASS/FAIL/N_A, evidence}, pillarScores {QUALITY, GROWTH, CASH_FLOW} (0–100 or N_A), score, verdict (PASS, FAIL), hardFailures[], valuationContext | 0–100 | rows with N_A excluded; valuationContext never scored | D-C18, D-C19, D-R28, D-R29 |
| ValuationContext (new) | companyId, asOf, metrics {pe, forwardPe, evToSales, priceToSales, fcfYield …}, peerMedians, peerGroupId | x, % | display only; never in a score, rank or gate | D-R29 |
| PeerGroup (new) | companyId, peers[] (2–4), rationale, asOf | — | peers in same industry node unless justified | S11 |
| ExternalScore | provider, name, value, scale, asOf | — | attribute only | D-C20 |
| Signal (RecordQuarter) | companyId, fiscalPeriodEnd, metric (EPS, REVENUE), grade (VERY_STRONG, STRONG, MODERATE, WEAK) | — | R-A05-026 | first-class signal (D-C17) |
| ResearchReport | id, title, publishedDate, author, coverage[] (companyIds), peers[], dataWindow, dataSources[], sections[], financials[] (FinancialSnapshot refs), scorecardResults[], peerComparison, catalysts[], riskFactors[], lowerRiskAlternatives[] (Basket refs), watchItems[], citations[] | — | R-A05-030..034 | D-C23 |
| | rating, priceTarget | — | MUST be null | D-C23 |
| | scenarios[] {description, assumptions, label = HYPOTHETICAL} | — | label mandatory | D-C23 |
| SelectionCandidate (new) | id, runDate, industryId, vehicle (BASKET, STOCK), instrumentId, rank, rankInputs, survivalCheckId, scorecardResultIds[], smartMoneyEvidenceRef, status (SELECTED, REJECTED), rejectReasons[] | — | output of PR-A05-01 | goes to A06 Watchlist; evidence never changes status (D-R25) |

## 4. Parameters
| Parameter | Default | Allowed range | Unit | Decision/Source |
|---|---|---|---|---|
| `selection.eligible_status` | GREEN | {GREEN} | — | D-C06 |
| `selection.require_top_rs_group` | true | true | bool | D-C06 (group size owned by A02, D-OPEN-1 top 20%) |
| `selection.basket_first` | true | bool | — | S13, S25 |
| `selection.single_stock_condition` | default rule set (R-A05-047): survival PASS; RS vs industry proxy > 0 over 3 and 6 months; effective class not EXTREME; company ≥ 5% of the proxy or in its top 10; written one-line reason | user MAY add stricter conditions | — | S13/S25 blank; D-DEF-18 |
| `selection.fund_compare_count` | 3 | 2–3 | funds | S05 ("Compare 2–3 options") |
| `selection.custom_basket_min_members` | 3 | 3–8 | names | S19 |
| `selection.custom_basket_max_members` | 8 | 3–8 | names | S19 |
| `selection.holdings_shortlist_max` | 8 | 3–8 | names | S19 ("top 3–8 names") |
| `selection.min_industry_purity_pct` | 60 | ≥ 60 | % of fund holdings in the target industry | D-R43 (= A01 `classification.proxy_min_purity_pct`) |
| `selection.min_avg_dollar_volume` | = A01 `instrument.min_liquidity.*` (stocks $5M; ETFs AUM $100M, $2M) | — | USD equivalent | S19, S07; D-R43 |
| `selection.require_scorecard_pass` | false | bool | — | D-C03 (optional confirmation) |
| `fundamentals.min_cash_runway_years` | 2 | >= 2 | years | D-C03, S02 |
| `fundamentals.burn_basis` | OCF_MINUS_CAPEX (fallback ADJ_OPERATING_LOSS, then GAAP_LOSS_PROXY flagged "proxy") | {OCF_MINUS_CAPEX, ADJ_OPERATING_LOSS, GAAP_LOSS_PROXY} | — | S30, S22 (non-cash items excluded); D-R19 |
| `fundamentals.max_quarters_stale` | 2 | 2 | quarters (older → INSUFFICIENT_DATA = veto) | D-R19 |
| `fundamentals.market_cap_tiers_usd` | MEGA_LARGE > 10B; MID 2–10B; SMALL_MICRO < 2B | — | USD equivalent | D-R23 |
| `fundamentals.min_interest_cover[tier][low/medium/high/extreme]` | MEGA_LARGE 1.5 / 2 / 3 / 4; MID 2 / 3 / 4 / 5; SMALL_MICRO 3 / 4 / 5 / 6 | > 0 | x (EBIT / interest, TTM) | D-R23 |
| `fundamentals.debt_veto_independent_of_runway` | true | true | — | D-R30 (amends D-R23: the interest-cover veto no longer requires runway < 2 years) |
| `fundamentals.debt_veto_financials_exempt` | true | true | — | D-R23 (own regulatory ratios) |
| `fundamentals.growth_min_tam_multiple` | 25 | >= 25 | x revenue | D-C18 (hard) |
| `fundamentals.capex_to_ocf_safe_max_pct` | 60 | — | % | S06 |
| `fundamentals.capex_to_ocf_danger_min_pct` | 90 | — | % | S06 |
| `fundamentals.eps_consistency_quarters` | 4 | 2–8 | quarters | S12 example; D-DEF-19 |
| `fundamentals.peer_count` | 4 | 2–4 | companies | S11, S12 |
| `fundamentals.peer_relative_rule` | >= peer median | {>= median} | — | D-R28 |
| `fundamentals.peer_selection` | same GICS sub-industry (else industry), same market-cap tier preferred, nearest TTM revenue (\|ln ratio\|), up to `fundamentals.peer_count`; < 2 peers → N_A | — | — | D-DEF-20 (R-A05-048) |
| `fundamentals.scorecard_lens` | per company: GROWTH or MATURE | {MATURE, GROWTH} | — | D-R28; S10–S12 |
| `fundamentals.scorecard_pillar_weights.mature` | Quality 40 / Growth 20 / Cash Flow 40 | each >= 0, sum 100 | points | D-R28 |
| `fundamentals.scorecard_pillar_weights.growth` | Quality 20 / Growth 50 / Cash Flow 30 | each >= 0, sum 100 | points | D-R28 |
| `fundamentals.scorecard_criterion_weights` | equal within a pillar | > 0 | — | D-R28 (pillar weights), D-DEF-21 |
| `fundamentals.scorecard_pass_score` | 60 | 0–100 | points (composite >= 60 passes) | D-R28 |

## 5. Rules
Drill-down: industry → basket → holdings
- **R-A05-001** (hard, METHOD) — Selection MUST start from an industry whose scoreboard status is GREEN and which is in the top RS group; RED or NEUTRAL industries produce no candidates. _Sources: S13 "Shop in green.", S25, S30 "Look only inside the rising industries." Decision: D-C06, D-C15_
- **R-A05-002** (hard, METHOD) — An industry with an active RS-deterioration flag MUST produce no new candidates. _Sources: S16, S20. Decision: D-C27_
- **R-A05-003** (hard, METHOD) — Selection MUST NOT start from a company, a news item or a valuation screen; a company enters only as a holding of an eligible industry. _Sources: S13 "The first one is which industry.", S05 "Follow the industry, not the stock."_
- **R-A05-004** (soft, METHOD) — For each eligible industry the default vehicle is a basket; a single stock is selected only when `selection.single_stock_condition` (default R-A05-047) is met and recorded. _Sources: S13, S25 "I buy the basket first." Decision: D-C21, D-DEF-18_
- **R-A05-005** (hard, CORE) — A fund is eligible only if it is purchasable in the user's market/wrapper (e.g. UCITS for EU/UK retail) at the user's broker; availability is checked before any comparison. _Sources: S13 "Filter by region first, then sort by cost.", S25, S21. Cross-ref: A01_
- **R-A05-006** (soft, CORE) — Among eligible funds for one industry, the app MUST compare up to `selection.fund_compare_count` funds on: industry purity, expense ratio (lower better), fund size and liquidity (larger better), geographic exposure, weighting and top-10 concentration. _Sources: S05, S13, S19, S12_
- **R-A05-007** (hard, CORE) — A fund whose holdings do not track the target industry cleanly (purity < `selection.min_industry_purity_pct`, 60%) is not a valid basket for that industry. _Sources: S19 "prefer liquid industry ETF when it tracks exposure cleanly". Decision: D-R43_
- **R-A05-008** (hard, CORE) — Before using any fund as a basket, its holdings and weights MUST be loaded; a cap-weighted fund dominated by few names is labelled "concentrated" and its look-through exposure goes to A09. _Sources: S12 "'Diversified' does not always mean 'equally weighted.'", S13, S30. Decision: D-C11_
- **R-A05-009** (soft, METHOD) — If no eligible fund exists for the industry in the user's market, the app MAY propose a custom equal-weight basket of the `selection.custom_basket_min_members`..`max_members` most liquid names of the industry node. _Sources: S19. Decision: D-C21_
- **R-A05-010** (hard, METHOD) — Every member of a custom basket and every single-stock candidate MUST pass the survival check (R-A05-013..019). _Sources: S13, S23, S30. Decision: D-C03_
- **R-A05-011** (soft, METHOD) — Holdings inside the basket are ranked by: liquidity filter passed, industry-relative strength > 0, RS rating, and trend facts from A06 (above rising 50-SMA, not below 150-SMA); at most `selection.holdings_shortlist_max` names are shortlisted. _Sources: S19 "Prefer stocks that are outperforming their own industry", S01_
- **R-A05-012** (soft, METHOD) — Theme qualifiers ([[picks-and-shovels]], [[toll-booth-business]], [[pure-play]]) MAY be stored as tags on candidates to explain a preference; they MUST NOT override R-A05-001..011. _Sources: S22, S24, S11. Decision: D-C21_

Survival veto gate (mandatory, D-C03)
- **R-A05-013** (hard, METHOD) — Every single-company candidate MUST have a FundamentalCheck SURVIVAL with result PASS dated from the latest reported fiscal period before it can reach the A06 entry checklist. _Sources: S13, S23, S25, S30 "The cash check can only reject it." Decision: D-C03_
- **R-A05-014** (hard, METHOD) — The survival check can only reject; a PASS is never a reason to buy and never raises a rank. _Sources: S13 "Never as the reason to buy.", S30. Decision: D-C03_
- **R-A05-015** (hard, METHOD) — runwayYears MUST be computed from existing cash only (no assumed share issuance or new borrowing); a company with quarterlyCashBurn = 0 (self-funding: OCF − capex >= 0) has unlimited runway. Runway < `fundamentals.min_cash_runway_years` (2) → FAIL. _Sources: S02 "survive at least two years without selling more shares", S30. Decision: D-C03_
- **R-A05-016** (hard, METHOD) — Debt veto (dangerZone), independent of the runway test: interestCoverTtm = EBIT / interest expense over the trailing twelve months; dangerZone = interestCoverTtm < `fundamentals.min_interest_cover[tier][volClass]`, whatever the runway; dangerZone = true → FAIL with reason DEBT_SERVICE. The runway test (R-A05-015) remains a separate veto. The tier comes from market cap in USD equivalent (MEGA_LARGE > $10B, MID $2–10B, SMALL_MICRO < $2B) and volClass is the stock's own class (A08). Financials (banks, insurers and other companies under regulatory capital ratios) are exempt. _Sources: S29, S28 danger zone filter, S08 zombie companies. Decision: D-C03, D-R23, D-R30_
- **R-A05-017** (hard, METHOD) — Cash burn MUST exclude non-cash accounting items (e.g. warrant revaluations); GAAP net loss alone MUST NOT be used as burn when cash-flow data or an adjusted operating loss exist. When only a GAAP loss is available, it MAY be used as the burn proxy (`GAAP_LOSS_PROXY`), the check MUST carry proxyFlag = true and the reason "proxy basis"; this is allowed and does not by itself yield INSUFFICIENT_DATA. _Sources: S22 IonQ "$1.58B of that is a non-cash accounting item". Decision: D-R19_
- **R-A05-018** (hard, METHOD) — Missing data, or a latest fiscal period older than `fundamentals.max_quarters_stale` (2) quarters, → result INSUFFICIENT_DATA, which is a veto and blocks entry like FAIL (fail-safe). _Sources: derived from D-C03 (mandatory gate). Decision: D-R19_
- **R-A05-019** (soft, CORE) — A rising share count (dilution) is shown as information on the check; a falling share count is shown as favourable. Neither changes the result unless it changes runway. _Sources: S30, S02, S04_
- **R-A05-020** (hard, METHOD) — For FUND baskets the survival check is not applicable (single-company risk removed); the candidate record states N_A. _Sources: S13, S25 "You literally cannot pick the wrong company if you own all of them."_

Optional scorecard: pillars Quality / Growth / Cash Flow (D-C18..D-C20, D-R26, D-R28)
- **R-A05-021** (hard, METHOD) — Every active scorecard criterion MUST have an explicit, documented threshold (absolute, peer-relative or boolean-with-evidence) and weight; criteria without a configured threshold are inactive and shown as "not configured". _Decision: D-C18_
- **R-A05-022** (hard, METHOD) — The scorecard MUST group its criteria into three [[scorecard-pillar]]s: **Quality** — gross margin, operating margin, ROIC and interest cover (each >= peer median), earnings consistency (EPS non-decreasing over `fundamentals.eps_consistency_quarters`), moat evidence (cost, scale, switching cost, patents/brand/licences; boolean with evidence); **Growth** — revenue growth YoY >= industry median, EPS growth YoY > 0, TAM multiple (R-A05-027, growth lens only), three written competitive reasons (R-A05-028); **Cash Flow** — levered FCF margin > 0, levered FCF margin >= peer median, profit turns into cash (R-A05-024), capex/OCF <= 60% where capex is material (R-A05-033). Valuation is not a pillar (R-A05-045). _Sources: S12, S10, S11. Decision: D-C18, D-R26_
- **R-A05-023** (hard, METHOD) — ROIC is the canonical return metric; a source value labelled ROCE is stored as ROIC with the label preserved in evidence. _Sources: S12, S10. Decision: D-C19_
- **R-A05-024** (soft, METHOD) — Cash criterion: a company with net margin > 0 and levered FCF margin <= 0 fails "profit turns into cash". _Sources: S12 "A company that reports profits but never produces cash is a warning sign."_
- **R-A05-025** (soft, METHOD) — Peer-relative criteria MUST use a PeerGroup of `fundamentals.peer_count` (2–4) true peers and pass when the company's value is >= the peer median (`fundamentals.peer_relative_rule`; <= median for criteria where lower is better); ratios only for peers reporting in other currencies. _Sources: S11 "Comparing a company only against its true peers", S12 (TSMC in NT$). Decision: D-R28; peer selection per R-A05-048 (D-DEF-20)_
- **R-A05-026** (soft, METHOD) — RecordQuarter grade: VERY_STRONG if latest quarterly EPS > 0 and the prior quarter's EPS <= 0 (profitability inflection); STRONG if latest EPS = max of all reported quarters; MODERATE if latest > prior but not a record; WEAK if latest < prior. The signal is an optional confirmation only. _Sources: S07, S03. Decision: D-C03, D-C17_
- **R-A05-027** (hard, METHOD) — Growth pillar under the growth lens: TAM / current annual revenue >= `fundamentals.growth_min_tam_multiple` (25) is a hard criterion; failing it sets verdict FAIL regardless of score. Under the mature lens the TAM criterion is N_A. _Sources: S10, S12 "Large target market with 25x TAM or more." Decision: D-C18, D-R28_
- **R-A05-028** (soft, METHOD) — Growth-lens evidence criteria (Growth and Quality pillars): revenue growth above the industry median; survival check PASS (cash to survive a crash); low debt; high operating margin where applicable; boolean evidence for brand, technology leadership, R&D, founder/CEO invested; and exactly three written reasons the company beats competitors (fewer than three → criterion FAIL). Criteria not yet applicable to pre-profit companies are N_A. _Sources: S10, S12, S04 "focus on the metrics that are available"_
- **R-A05-029** (soft, METHOD) — The [[scorecard-lens]] is chosen per company and recorded: mature (including mature cyclical) companies use the mature lens, fast growers with little history the growth lens (S10–S12 quality vs growth lens). _Sources: S11, S10, S12. Decision: D-R28_
- **R-A05-030** (hard, METHOD) — Each pillar score = 100 × Σ(w_i × pass_i) / Σ(w_i) over its active, non-N_A criteria (0–100; N_A if none); the composite score = Σ(W_p × pillar_p) / Σ(W_p) over non-N_A pillars with the lens weights W (mature 40/20/40, growth 20/50/30); verdict PASS iff composite >= `fundamentals.scorecard_pass_score` (60) and no hard criterion failed. The formula, lens, weights and thresholds version are stored with every result. _Decision: D-C18, D-R28_
- **R-A05-031** (hard, METHOD) — An ExternalScore (e.g. Winston Score) MAY be stored and displayed with provider and date but MUST NOT be used in any rule, rank, gate or score. _Sources: S11, S05. Decision: D-C20_
- **R-A05-032** (hard, METHOD) — Scorecard results are optional confirmations: they MUST NOT gate entry unless the user sets `selection.require_scorecard_pass` = true in the PersonalRuleSet. _Decision: D-C03_
- **R-A05-033** (soft, METHOD) — For companies where capex is material, capex/OCF <= 60% is labelled "safe", >= 90% "danger" (optional criterion). _Sources: S06_
- **R-A05-034** (soft, METHOD) — Valuation is context only (R-A05-045); a valuation figure MUST carry its asOf date and is shown as stale after the next reported period. _Sources: S10 "least important of our metrics", S12 "a fixed number would be stale". Decision: D-R29_
- **R-A05-035** (soft, METHOD) — "Best business" and "best entry now" are separate: a scorecard PASS MUST NOT be shown as an entry signal. _Sources: S10 "Quality of the business ≠ safety of the entry price." Decision: D-C23_

ResearchReport (D-C23)
- **R-A05-036** (hard, METHOD) — A ResearchReport MUST contain no rating and no price target (fields null). _Sources: S10, S11, S12. Decision: D-C23_
- **R-A05-037** (hard, METHOD) — Chart, pattern and volume assessments MUST NOT be stored in a ResearchReport; they are stored as TechnicalSetup (A06) linked by instrument and date. _Sources: S04 (chart section, spring effect) vs S10–S12 policy. Decision: D-C23_
- **R-A05-038** (hard, METHOD) — Any upside/capture scenario MUST be labelled HYPOTHETICAL with its assumptions and MUST NOT be compared to price as a target. _Sources: S04 "illustrative, not a price target". Decision: D-C23_
- **R-A05-039** (hard, CORE) — Every financial figure in a report MUST reference a FinancialSnapshot with fiscalPeriodEnd and source; macro figures reference A11 Observations. _Sources: S12 (period-end dates, two-source corroboration). Decision: D-C22_
- **R-A05-040** (soft, METHOD) — A report SHOULD list risk factors and at least one lower-risk basket alternative. _Sources: S10, S11, S12, S04_

Rejected selection logics
- **R-A05-041** (hard, METHOD) — Cheap valuation alone (low P/E, low P/NAV, high FCF yield) MUST NOT make a candidate; selection follows R-A05-001. _Sources: S30, S13 "Nothing on the red side is cheap". Decision: D-C25_
- **R-A05-042** (hard, METHOD) — A newly listed company without enough history for a qualifying base (A04 `volume.base_min_months`) cannot be selected for entry ([[ipo-trap]]). _Sources: S03 "Do NOT plan to buy any IPO on day one". Decision: D-C02_
- **R-A05-043** (soft, METHOD) — A theme the user likes but cannot underwrite at company level SHOULD be held via a basket rather than a single stock. _Sources: S11, S24 thematic ladder. Decision: D-C21_

Round-2 additions (2026-10-26)
- **R-A05-044** (soft, METHOD) — Each SelectionCandidate SHOULD show the A04 [[smart-money-evidence]] panel of the stock and its industry; strong insider/institutional buying MAY raise the candidate's rank among otherwise equal holdings, but evidence MUST NOT make an ineligible candidate eligible, override the survival gate or create a buy. _Decision: D-R25, D-R22, D-C06_
- **R-A05-045** (hard, METHOD) — Valuation metrics (P/E, forward P/E, EV/sales, P/S, FCF yield …) MUST be shown only as a `ValuationContext` with a peer comparison (peer medians); they MUST NOT enter any pillar, composite score, rank or gate. _Sources: S10, S12. Decision: D-R29_
- **R-A05-046** (hard, METHOD) — The composite scorecard remains an optional confirmation: its verdict gates entry only if `selection.require_scorecard_pass` = true (R-A05-032). _Decision: D-C03, D-R28_

Round-3 additions (2026-10-26)
- **R-A05-047** (hard, METHOD) — The default single-stock condition is met only if all hold and are recorded on the SelectionCandidate: (a) survival check PASS; (b) the stock's RS vs its industry proxy is > 0 over both 3 and 6 months; (c) its effective volatility class (A08) is not EXTREME; (d) the company is ≥ 5% of the industry proxy or among its top 10 holdings; (e) a one-line written reason. Otherwise the basket is the vehicle. The user MAY add stricter conditions in the PersonalRuleSet, never looser ones. _Sources: S13, S25 (basket first). Decision: D-DEF-18_
- **R-A05-048** (soft, METHOD) — The PeerGroup MUST be built reproducibly: candidates from the same GICS sub-industry (else industry) in any market, same market-cap tier preferred, ranked by \|ln(TTM revenue_peer / TTM revenue_company)\|, the first `fundamentals.peer_count` (4) taken; with fewer than 2 peers all peer-relative criteria are N_A. The rationale is stored with the group. _Sources: S11, S12. Decision: D-DEF-20_

## 6. Processes
**PR-A05-01 Selection drill-down** — trigger: weekly review (D-C04, D-C28) after the A02 scoreboard update; RS universe refresh monthly. Inputs: scoreboard, classification (A01), fund universe, financial snapshots, A04/A06 chart facts.
1. Take industries with status GREEN, in top RS group, no deterioration flag (R-A05-001/002).
2. For each: list funds available in the user's market (R-A05-005); load holdings (R-A05-008); compare up to 3 (R-A05-006/007); pick the basket.
3. If no fund: propose custom basket of 3–8 liquid names; run survival check per member (R-A05-009/010).
4. If the user's single-stock condition applies: rank holdings (R-A05-011), shortlist ≤ 8, run survival check (PR-A05-02).
5. Optionally run scorecards (PR-A05-03) and attach results.
6. Emit SelectionCandidates (SELECTED / REJECTED with reasons) → A06 watchlist.
Output: candidate list per industry; no orders.

**PR-A05-02 Survival check** — trigger: new candidate; each new fiscal period for held/watched stocks.
1. Load latest FinancialSnapshot; if missing or older than 2 quarters → INSUFFICIENT_DATA (R-A05-018).
2. Compute quarterlyCashBurn = max(0, −(OCF − capex)) per quarter, excluding non-cash items; fall back to adjusted operating loss, then GAAP-loss proxy with proxyFlag (R-A05-017).
3. runwayYears = cash / (4 × burn), INF if burn = 0; FAIL if < 2 (R-A05-015).
4. Unless financials-exempt: compute interestCoverTtm, look up the minimum by tier × class, set dangerZone (R-A05-016); FAIL if true.
5. Record share-count change (R-A05-019); write FundamentalCheck with reasons.

**PR-A05-03 Scorecard evaluation (optional)** — trigger: user request or new report.
1. Choose the lens per company (R-A05-029).
2. Build PeerGroup (2–4) (R-A05-025).
3. Evaluate criteria per pillar (R-A05-022) against explicit thresholds and peer medians; mark N_A where not applicable.
4. Apply hard criteria (TAM, growth lens) (R-A05-027); compute pillar and composite scores (R-A05-030); verdict at >= 60; store version.
5. Attach the ValuationContext with peer medians (R-A05-045), never scored.

**PR-A05-04 Research report production** — trigger: ad hoc. Steps: create report shell with null rating/target (R-A05-036); attach dated snapshots (R-A05-039); attach scorecard results; label scenarios HYPOTHETICAL (R-A05-038); move any chart content to a linked TechnicalSetup (R-A05-037); add risks and lower-risk baskets (R-A05-040).

## 7. Calculations
```
quarterlyCashBurn = max(0, -(OCF_q - capex_q))            # currency per quarter; non-cash items excluded
runwayYears       = cash / (4 * quarterlyCashBurn)        # INF if burn = 0
TAM_multiple      = TAM / revenue_annual                  # hard >= 25 (growth scorecard)
penetration       = revenue_annual / TAM
cash_conversion   = levered_FCF_margin / net_margin
DE                = total_debt / total_equity
net_debt          = total_debt - cash
interest_cover    = EBIT_TTM / interest_expense_TTM            # debt veto if < min[tier][class], independent of runway (D-R30)
peer_distance     = |ln(revenue_peer / revenue_company)|      # rank ascending, take 4 (D-DEF-20)
tier              = MEGA_LARGE (mcap_usd > 10B) | MID (2B..10B) | SMALL_MICRO (< 2B)
dataAgeQuarters   = count of fiscal quarter-ends after fiscalPeriodEnd up to the evaluation date   # > 2 → INSUFFICIENT_DATA
capex_to_ocf      = capex / OCF * 100                     # % ; <=60 safe, >=90 danger
IRS               = return(stock, L) - return(industry_proxy, L)
pillar_p          = 100 * sum(w_i * pass_i) / sum(w_i)    # per pillar; active, non-N_A criteria only
composite         = sum(W_p * pillar_p) / sum(W_p)        # non-N_A pillars; W mature 40/20/40, growth 20/50/30
verdict           = PASS iff composite >= 60 and no hard failure
recordQuarter     = EPS_q(latest) == max(EPS_q(all reported))
```

## 8. Examples / fixtures
**EX-A05-01 Drill-down (S25, Saturday 22 Aug 2026 snapshot)** — Given GREEN: computer hardware, oil and gas, engineering; RED: IT services, casinos, software. When PR-A05-01 runs. Then candidates only from the three green industries (if also in top RS group); no candidate from software even for a "very large software business" (R-A05-001/003).

**EX-A05-02 Fund availability (S25, Aug 2026, illustrative)** — Given drone funds: 9 in US, 1 in UK. Then a UK user's comparison contains 1 fund (no padding to 3); a US user's up to 3 (R-A05-005/006).
- Edge: an EU retail user and a US-listed ETF only → not eligible; app proposes the UCITS equivalent or a custom basket (R-A05-005/009).

**EX-A05-03 Survival check pass/fail (S02, 2 Jun 2026; S30, 24 Oct 2026)**
| Company | Cash | Burn / quarter | Runway | Expected |
|---|---|---|---|---|
| BETA (S02) | $1.59B | ~$120M | 13.25 q = 3.31 y | PASS |
| RGTI (S02) | $569M, $0 debt | ~$26M op loss (proxy) | 21.9 q = 5.47 y | PASS |
| KDP (S30) | ~$3.3B | none (~$700M generated last quarter) | INF | PASS |
| Synthetic edge | $100M | $13M | 1.92 y | FAIL (< 2) |
| Synthetic edge | $104M | $13M | 2.00 y | PASS (boundary inclusive) |
A PASS adds no rank (R-A05-014). RGTI later fails S02's own valuation filter (P/S > 700x) — irrelevant to the gate.

**EX-A05-04 Non-cash loss (S22, 14 Aug 2026)** — Given IonQ Q2 2026 GAAP net loss $1.87B of which $1.58B non-cash warrant items; adjusted operating loss ~$120M; cash ~$2.0B pro-forma. When burn basis ADJ_OPERATING_LOSS. Then burn $120M/q, runway = 2.0B/(4×0.12B) = 4.17 y → PASS; using GAAP loss would give 0.27 y → wrongly FAIL (R-A05-017).

**EX-A05-05 ADPT growth scorecard (S04, data Q1 2026, report 2026-06-08)** — Given TAM $5.5–6.2B (~$6B), FY2026 revenue ~$270M (guidance), cash $237.2M (2026-03-31), Q1 adj. EBITDA −$2.5M, net loss −$20M, revenue +35% YoY, 53% clinical CAGR 2021–2025. When PR-A05-03 runs. Then:
- TAM_multiple = 6.0B / 0.27B = 22.2x (range 20.4–23.0x) < 25 → hard FAIL → growth verdict FAIL, although S04 marked it ✓ (D-C18 fail fixture).
- penetration = 4.5% (4.4–4.9%).
- Survival: no cash-flow figure in source; with the GAAP net loss as burn proxy (`GAAP_LOSS_PROXY`, allowed by D-R19) runway = 237.2/(4×20) = 2.97 y → PASS; proxyFlag = true, reason "proxy basis".
- Scenario "25% capture × $6B = $1.5B revenue vs $2.7B market cap" stored as HYPOTHETICAL, not compared to price (R-A05-038).
- S04's chart content (peak $67.74 Jan 2021, low < $5 2023, ~4-year base, 52-week range $9.90–$20.76) goes to TechnicalSetup, not the report (R-A05-037).

**EX-A05-06 NVDA quality inputs (S12, published 2026-07-22, Winston data)**
| Quarter end | Revenue | GM | OM | ROIC | EPS | Net m. | LFCF m. | D/E |
|---|---|---|---|---|---|---|---|---|
| 2025-04-27 | $44.06B | 60.5% | 49.1% | 23.4% | 0.77 | 42.6% | 59.4% | 0.10 |
| 2025-07-27 | $46.74B | 72.4% | 60.8% | 26.2% | 1.08 | 56.5% | 28.8% | 0.08 |
| 2025-10-26 | $57.01B | 73.4% | 63.2% | 28.3% | 1.31 | 56.0% | 38.8% | 0.07 |
| 2026-01-25 | $68.13B | 75.0% | 65.0% | 26.7% | 1.77 | 63.1% | 51.2% | 0.05 |
Expected: EPS strictly rising over 4 quarters → earnings consistency PASS (default `fundamentals.eps_consistency_quarters` = 4, D-DEF-19); revenue +54.6% Q1→Q4; D/E Q4 = 8.47/157.29 = 0.054; cash_conversion Q4 = 51.2/63.1 = 0.81; R-A05-024 not triggered (LFCF > 0); ROIC not monotonic (peak Q3) — no rule requires monotonic ROIC.
- Peers (latest quarter): AVGO GM 65.6% / ROIC 5.9% / D/E 0.83; AMD 54.3% / 2.6% / 0.06; TSM 66.2% / 9.6% / 0.17 (TSM EPS in NT$ → ratios only, R-A05-025). With rule ">= peer median": NVDA GM 75.0 vs median 65.6 → PASS; ROIC 26.7 vs 5.9 → PASS.
- RecordQuarter: Q4 EPS 1.77 = max of the four reported → STRONG (assuming no higher earlier quarter in full history).
- Pillars, growth lens (D-R28; `eps_consistency_quarters` = 4, equal criterion weights D-DEF-21): Quality GM PASS, ROIC PASS, consistency PASS, operating margin and interest cover N_A (no peer data) → 100; Cash Flow LFCF margin 51.2% > 0 PASS, profit turns into cash PASS, peer LFCF N_A → 100; Growth N_A (no YoY or TAM data in S12) → composite over Quality and Cash Flow = (20 × 100 + 30 × 100)/50 = 100 → PASS (optional confirmation only). P/E and peers go to ValuationContext only (R-A05-045).

**EX-A05-07 NSC mature cyclical (S11, published 2026-07-17)** — Given NSC GM 45.3%, net margin 21.9%, ROIC 7.3%, LFCF 31.4%, cash $1.34B, debt $17.10B, equity $15.80B, interest cover 5.0x, P/E 27.6x, fwd P/E 21.7x, EPS −26.6% YoY, Winston Score 40. Peers UNP/CSX/CPKC/CNI: ROIC 11.6/8.7/5.4/8.7, LFCF 23.1/29.2/13.4/20.7, GM 45.7/37.5/48.3/41.9, interest cover 7.6/5.6/6.2/7.1. Then:
- net debt = 15.76B; D/E = 1.08x; cash_conversion = 31.4/21.9 = 1.43.
- With ">= peer median": ROIC 7.3 < 8.7 FAIL; LFCF 31.4 >= 21.9 PASS; GM 45.3 >= 43.8 PASS; interest cover 5.0 < 6.65 FAIL.
- Mature lens (R-A05-029): Quality = GM PASS, ROIC FAIL, interest cover FAIL (operating margin, moat N_A) → 33.3; Growth = EPS growth −26.6% YoY FAIL (others N_A) → 0; Cash Flow = LFCF 31.4% > 0 PASS, LFCF ≥ peer median PASS → 100; composite = 0.4 × 33.3 + 0.2 × 0 + 0.4 × 100 = 53.3 < 60 → FAIL (optional confirmation; no effect on entry unless the user requires a pass). P/E 27.6x and fwd P/E 21.7x are ValuationContext only; fwd P/E < P/E → "earnings growth expected" label.
- Debt veto: large cap (> $10B), interest cover 5.0x ≥ the MEGA_LARGE minimum for any class (≤ 4) → no dangerZone.
- Winston Score 40 (and CPKC 64 despite lowest ROIC) stored as ExternalScore only; ignored by score and rank (R-A05-031).

**EX-A05-08 Fundamentals do not override flows (S02 2 Jun 2026 vs S30 24 Oct 2026)** — Given ORCL passed all three S02 filters in June 2026; by October 2026 ORCL ~60% below its high. Then a scorecard PASS creates no entry and no hold reason; exits remain price-based (A07, D-C26) (R-A05-035).

**EX-A05-09 Record-quarter grades (synthetic, S07 rule)** — EPS series −0.10, −0.05, 0.02 → VERY_STRONG; 0.30, 0.40, 0.55 (all-time high) → STRONG; 0.80 (2024 high), 0.50, 0.60 → MODERATE; 0.60, 0.50 → WEAK.

**EX-A05-11 Debt veto by tier × class (synthetic, D-R23, D-R30)** — Given a small cap ($1.4B, SMALL_MICRO), class HIGH (minimum 5.0x), interest cover TTM 3.2x. When runway is 1.5 y → FAIL with reasons RUNWAY and DEBT_SERVICE. When runway is 3.0 y → still FAIL with reason DEBT_SERVICE (3.2 < 5.0; the debt veto is independent of runway, D-R30). Same company as a mid cap ($3B, MID, HIGH → 4.0x) → 3.2 < 4.0 → FAIL (DEBT_SERVICE). Interest cover 5.0x as a small cap → 5.0 ≥ 5.0 → no debt veto; with runway 3.0 y → PASS. A bank with interest cover 0.8x → exempt; regulatory ratios out of scope.

**EX-A05-12 Stale data and burn proxy (synthetic, D-R19)** — Given evaluation date 2026-10-31 and the latest FinancialSnapshot for the fiscal quarter ending 2025-12-31 (quarter-ends since: 2026-03-31, 06-30, 09-30 → age 3 > 2) → INSUFFICIENT_DATA, veto. With the 2026-06-30 quarter loaded (age 1) and only a GAAP loss of $10M/quarter, cash $90M → proxy runway = 90/(4 × 10) = 2.25 y → PASS with proxyFlag.

**EX-A05-13 Composite pass edge (synthetic, D-R28)** — Given pillar scores Quality 50, Growth 60, Cash Flow 70. Then growth lens 0.2 × 50 + 0.5 × 60 + 0.3 × 70 = 61 → PASS; mature lens 0.4 × 50 + 0.2 × 60 + 0.4 × 70 = 60 → PASS (edge, >= 60). Quality 50, Growth 55, Cash Flow 70 under the mature lens → 59 → FAIL.

**EX-A05-14 Single-stock condition and fund purity (synthetic, D-DEF-18, D-R43)** — Given an industry ETF with 72% of holdings in the industry → valid basket; another with 48% → not a valid basket for that industry (R-A05-007). A stock in that industry with survival PASS, RS vs the ETF +3.1 pp (3 months) and +5.4 pp (6 months), effective class HIGH, weight 6.2% of the ETF and the written reason "largest supplier, beats its basket" → single-stock condition met (R-A05-047). The same stock with effective class EXTREME, or with 6-month RS −0.8 pp → condition not met → the basket is the vehicle.

**EX-A05-15 Peer selection (synthetic, D-DEF-20)** — Given a company with TTM revenue $10B and same-sub-industry candidates with $8B, $12B, $25B, $3B and $40B. Then distances \|ln\| = 0.223, 0.182, 0.916, 1.204, 1.386 → peers (4) = $12B, $8B, $25B, $3B; the $40B company is dropped. With only one candidate in the sub-industry and none in the industry → peer-relative criteria N_A (R-A05-048).

**EX-A05-10 Valuation alone (edge)** — Given gold miners with FCF yield ~10% vs 50-y avg ~4.1% and P/NAV ~0.8x (S21, Aug 2026) while S08 (July 2026) found 0 of 50 miners with a qualifying setup and the group 20–62% below highs. Then no candidate from valuation (R-A05-041); miners become candidates only when their industry is GREEN and setups appear (A06).

## 9. Variants & open points
Variants not chosen:
- S25 "survival 'yes, could cease to exist' → smaller position" → replaced by veto (D-C03).
- S07/S03 record quarter as required Power Move → optional confirmation only (D-C03, D-C17).
- S02 three-filter screen (cash runway, institutional tailwind, revenue inflection) and S04 ten-x checklist → optional screens; S02 counts product launches as "tailwind" (definition loosened), S04 applied steps differ from its own intro.
- Winston Score / fund "Winstons" as rank inputs → external attribute only (D-C20).
- S08 three-question quality filter (makes money, growing earnings, survive 3 more years of high rates) → available as a quick QUALITY scorecard preset; thresholds per D-C18.
- S01 "review basic fundamentals before any investment" as general review → subsumed by survival gate.

- S12 "four simple questions in order" (profitable → cash → stable → valued) as scorecard structure → replaced by the pillars Quality / Growth / Cash Flow (D-R26).
- Valuation as a scored group → context only (D-R29).
- D/E ratio veto in the survival gate → not adopted; interest-cover veto per D-R23.

Open points:
- Variant (not chosen): interest-cover veto only when runway < 2 years (D-R23 as first decided) — independent veto (D-R30).
- Closed by D-DEF-18 — OPEN-A05-1 (default single-stock condition; pending user review).
- Closed by D-R43 — OPEN-A05-2 (industry purity ≥ 60%).
- Closed by D-DEF-19 — OPEN-A05-5 (4 quarters; pending user review).
- Closed by D-DEF-20 — OPEN-A05-6 (peer selection method; pending user review).
- Closed by D-R30 — OPEN-A05-9 (independent debt veto).
- Equal criterion weights within a pillar confirmed by D-DEF-21 (pending user review).

Closed by round-2 decisions (2026-10-26): OPEN-A05-3 (D-R19), OPEN-A05-4 (D-R23), OPEN-A05-7 (D-R28), OPEN-A05-8 (D-R19).

**Glossary additions (merged into glossary v0.2.0):**
| slug | term | layer | definition | sources |
|---|---|---|---|---|
| peer-group | Peer Group | CORE | The 2–4 closest comparable companies against which peer-relative scorecard criteria are judged; ratios only across currencies. | S11, S12 |

## 10. Traceability
| Rule/Concept | Sources |
|---|---|
| R-A05-001..004 industry-first, basket-first | S13, S25, S05, S30, S16, S20; D-C06, D-C27, D-C21 |
| R-A05-005..009 fund screening, custom basket | S13, S25, S05, S19, S12, S21; D-C11, D-C21 |
| R-A05-010..020 survival veto gate | S02, S13, S23, S25, S30, S22, S28, S29, S08; D-C03 |
| R-A05-021..035 scorecards, record quarter | S10, S11, S12, S04, S06, S07, S03; D-C17..D-C20, D-C03 |
| R-A05-036..040 ResearchReport | S04, S10, S11, S12; D-C22, D-C23 |
| R-A05-041..043 rejected logics | S30, S13, S03, S11, S24; D-C02, D-C25, D-C21 |
| R-A05-044..046 smart-money evidence, valuation context, optional composite | S10, S12; D-C03, D-R22, D-R25, D-R28, D-R29 |
| R-A05-047..048 single-stock condition, peer selection | S11, S12, S13, S25; D-DEF-18, D-DEF-20 |
| R-A05-007, R-A05-016 purity, independent debt veto | S19, S28, S29; D-R30, D-R43 |
| EX-A05 fixtures | S02, S04, S08, S11, S12, S21, S22, S25, S30 |
