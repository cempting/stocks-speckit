# Feature Specification: Fundamental Score Evaluation

**Feature Branch**: `main` (feature key `014-fundamental-score-evaluation`; no branch hook)

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description:
> scoreboard calcualtion and stock list score have to be evaluated. The score board focusses on Quality, Growth, and Cashflow criteria. The goal is to under stand the company fundamentals to allow for a proper riskmanagment.

## Scope and Ownership

This feature evaluates whether the Quality, Growth, and Cash Flow component calculations and
the stock-list Total Score are correct, understandable, and useful as fundamental evidence for
risk analysis. The current baseline is defined by [feature 001](../001-market-leadership-screener/spec.md):
industry-relative percentiles for six financial measures, grouped into three equally weighted
components. [Feature 006](../006-stock-table-columns/spec.md) defines the stock-list Total Score
as the equal mean of all three available components. This feature owns the review of those
definitions and the consistency and interpretation of the resulting scores.

The evaluation must distinguish a relative peer ranking from an absolute statement about a
company's financial health or risk. Missing or negative cash-flow evidence is a prominent risk
signal, not a reason to fabricate a value or silently alter the component or Total Score weights.
Feature [011](../011-company-risk-evidence/spec.md) continues to own issuer evidence and
cash-flow warnings; [002](../002-fundamental-grading-layout/spec.md) owns the raw financial
matrix. The existing five-column stock-list layout remains owned by 006.

Any recommended change to metric definitions, directions, peer eligibility, thresholds, or
weights must be supported by documented evaluation results and explicitly approved before it
changes user-visible scores. This specification does not authorize a new data provider, a new
catalog authority, hidden evidence loading, investment advice, or a trade recommendation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate Score Methodology (Priority: P1)

As an investor reviewing company fundamentals, I want the Quality, Growth, Cash Flow, and
stock-list score calculations evaluated against clear examples, so I can understand what the
scores measure and where they may fail as risk signals.

**Why this priority**: Scores used to support risk analysis must be explainable and tested for
misleading results before users rely on them.

**Independent Test**: Apply the current score rules to controlled companies with positive,
zero, negative, missing, stale, extreme, and incomparable financial facts and verify the
calculation, result state, and explanation for every component and total.

**Acceptance Scenarios**:

1. **Given** a score methodology review, **When** the user inspects its outcome, **Then** each
   component's inputs, calculation, direction, peer population, time period, and missing-data
   treatment are stated in terms that distinguish peer ranking from absolute financial health.
2. **Given** valid financial facts and a sufficient peer group, **When** a component score is
   evaluated, **Then** its result matches the documented rule for each included metric and the
   documented rule for combining those metrics; an unavailable required metric does not cause
   the component to silently redistribute its weight.
3. **Given** the same instrument appears in different industries or peer groups, **When** its
   scores are compared, **Then** each score identifies its own peer context and the values are
   not presented as directly interchangeable absolute risk measures.
4. **Given** the review identifies a weakness in an existing rule, **When** a replacement is
   proposed, **Then** the evaluation records the affected examples, expected benefit, tradeoffs,
   and approval required before scores change; without approval, current user-visible scores
   remain unchanged.
5. **Given** evaluated evidence from more than one period or financial source, **When** findings
   are reported, **Then** the source, publication date, fiscal period, currency, and analysis
   cutoff are identified where available, and incomparable observations are not presented as
   equivalent.

---

### User Story 2 - Interpret Stock-List Scores (Priority: P1)

As an investor comparing stocks, I want the stock-list score to agree with the company's
Quality, Growth, and Cash Flow scorecard and to expose its limitations, so a concise ranking
does not hide which fundamentals are strong, weak, or unassessed.

**Why this priority**: Users need a consistent comparison value without mistaking an aggregate
for a complete risk assessment.

**Independent Test**: For a controlled set of stocks and a fixed industry, cutoff, and evidence
set, compare each stock-list Total Score and state with the three component scores shown for
that same context.

**Acceptance Scenarios**:

1. **Given** three available component scores for a stock, **When** the stock appears in the
   list and its scorecard, **Then** both surfaces show the same Total Score under the approved
   calculation and precision.
2. **Given** any component is not loaded, insufficient, unavailable, or in error, **When** the
   stock-list score appears, **Then** it shows the corresponding explicit non-numeric state
   and does not display zero, a partial average, or an earlier score as current.
3. **Given** a user wants to understand a displayed Total Score, **When** they inspect the
   existing scorecard or detail surface, **Then** all three component scores and the associated
   financial evidence and peer context are available without adding columns to the stock list.
4. **Given** a stock changes industry, analysis cutoff, or eligible peer cohort, **When** its
   score is recalculated, **Then** the new peer context and rules revision are identified, an
   incompatible prior score is not reused as current, and comparisons across revisions are
   explained as non-equivalent unless their comparability is established.
5. **Given** a refresh fails while an older result exists, **When** the scorecard or list is
   viewed, **Then** the failure and older observation date remain explicit and the older result
   is not described as freshly assessed.

---

### User Story 3 - Recognize Cash-Flow and Evidence Risk (Priority: P1)

As an investor assessing risk, I want missing cash-flow evidence and reported cash consumption
to remain conspicuous even when other components or peer rankings are favorable, so I do not
mistake incomplete or weak cash generation for financial safety.

**Why this priority**: Cash generation is a major part of the user's stated risk assessment,
and gaps in that evidence must not be hidden by an aggregate score.

**Independent Test**: Display controlled stocks with unloaded, missing, zero, positive, and
negative operating and free cash flow, alongside favorable and unfavorable Quality and Growth
scores; verify the warnings, values, and aggregate states remain distinct.

**Acceptance Scenarios**:

1. **Given** cash-flow evidence has not been requested or is missing, **When** the scorecard or
   stock-list context is viewed, **Then** cash flow is identified as not assessed or unavailable
   and is not described as healthy.
2. **Given** reported operating cash flow or free cash flow is zero or negative, **When** its
   risk context is shown, **Then** the actual value, definition, and period remain visible and
   the condition is not confused with missing data.
3. **Given** Quality and Growth are favorable while Cash Flow is missing or negative, **When**
   the aggregate and risk context are shown, **Then** the cash-flow limitation or concern remains
   prominent and no claim of low risk or complete assessment is made.
4. **Given** negative free cash flow is caused by reported capital spending, **When** the
   evidence is interpreted, **Then** the value is described as a cash-generation concern and
   is not by itself labeled insolvency.
5. **Given** a user views scores or risk signals, **When** the results are presented, **Then**
   they are described as historical decision-support evidence and not as personalized advice,
   guaranteed safety, or a trade instruction.

### Edge Cases

- A peer group has fewer valid observations than the existing minimum required for a metric.
- One metric is available while another metric in the same component is missing or invalid.
- The same company has different percentiles in separate industry cohorts.
- Financial data is published after the analysis cutoff, has incompatible fiscal periods or
  currencies, or contains an invalid denominator.
- An extreme value changes peer ranks substantially, or many peers have tied values.
- A stock's total is unavailable because cash-flow evidence is missing even though Quality and
  Growth scores are available.
- A refreshed result has an error while an older result exists; the older value must not be
  described as freshly assessed.
- Negative or zero cash-flow values are valid observations and must not be treated as missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The score methodology evaluation MUST cover the current Quality, Growth, and Cash
  Flow inputs, their calculation and direction, peer-group definition, observation cutoff,
  period comparability, minimum valid-peer requirements, component combination, and missing-data
  behavior.
- **FR-002**: The evaluation MUST test each component and the stock-list Total Score with
  reproducible cases that include ordinary positive values, zero and negative values, missing
  or invalid facts, insufficient peer groups, ties, extreme values, and facts unavailable by
  the analysis cutoff.
- **FR-003**: The scorecard MUST identify that component scores are relative to the stated peer
  group and analysis context; neither a percentile nor the Total Score alone MUST be described
  as an absolute measure of safety, solvency, or investment suitability.
- **FR-004**: A component MUST remain unavailable or insufficient when its required evidence or
  peer support is inadequate. Missing values MUST NOT be converted to zero, omitted to improve
  the score, or concealed by silently redistributing component weights.
- **FR-005**: The stock-list Total Score MUST use the same approved component values and
  calculation as the corresponding scorecard for the same instrument, peer group, cutoff, and
  rules revision. If any required component is not available, the list MUST display an explicit
  non-numeric state rather than a partial or stale total.
- **FR-006**: Users MUST be able to inspect the Quality, Growth, and Cash Flow components and
  the underlying dated evidence that supports a stock-list Total Score through the existing
  scorecard or detail surface. The five-column stock-list layout MUST remain unchanged.
- **FR-007**: Missing, unloaded, stale, incompatible, invalid, and failed cash-flow evidence
  MUST be distinguishable from reported zero or negative cash flow. Missing cash flow MUST
  receive a prominent not-assessed or unavailable warning.
- **FR-008**: Reported zero or negative operating or free cash flow MUST remain visible with its
  definition and period. Negative free cash flow MUST NOT alone be presented as proof of
  insolvency, and peer-relative performance MUST NOT obscure the actual reported value.
- **FR-009**: The evaluation MUST record the evidence and rationale for retaining or proposing
  changes to score inputs, directions, peer rules, thresholds, or weights. A proposed change
  MUST NOT alter user-visible scores until explicitly approved and versioned.
- **FR-010**: When an approved scoring rule changes, displayed results MUST identify the
  applicable rules revision, and scores produced under incompatible revisions MUST NOT be
  presented as directly comparable without an explicit explanation.
- **FR-011**: Score evaluation and display MUST preserve the selected financial source, cutoff,
  publication availability, fiscal period, currency, and known coverage limitations. It MUST
  NOT silently switch sources or substitute stale results after a failed refresh.
- **FR-012**: Score and risk disclosures MUST describe historical financial evidence and
  comparison context; they MUST NOT claim to provide personalized financial advice, guarantee
  safety, or direct a trade.

### Key Entities *(include if feature involves data)*

- **Financial Metric Evidence**: A dated reported or derived financial value, with its period,
  units, currency, source, and availability state.
- **Component Score**: A Quality, Growth, or Cash Flow result calculated from the defined
  component metrics for a specified instrument, peer group, cutoff, and scoring revision.
- **Peer Context**: The effective industry cohort and analysis date against which metric
  percentiles are calculated.
- **Total Score**: The stock-list aggregate of the three component scores, with its calculation
  revision and explicit availability state.
- **Cash-Flow Risk Signal**: A distinct warning for missing, zero, or negative cash-flow
  evidence; it is not itself a score or an insolvency determination.
- **Evaluation Finding**: A tested observation about score correctness, interpretation,
  limitations, or a proposed change, with its supporting case and disposition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the approved controlled evaluation set, 100% of available component and total
  scores match their documented calculations and rounding rules.
- **SC-002**: In 100% of controlled incomplete, stale, incompatible, insufficient, unavailable,
  and error cases, scores show the correct explicit state and no zero-filled or partial total.
- **SC-003**: In 100% of controlled zero, negative, and missing cash-flow cases, users can
  distinguish the reported financial condition from an evidence gap, and a missing cash-flow
  warning remains visible when other scores are favorable.
- **SC-004**: In 100% of tested comparisons, the stock-list Total Score and the corresponding
  scorecard Total Score agree for the same stock, peer group, cutoff, and scoring revision.
- **SC-005**: At least 90% of users in a representative evaluation can correctly explain whether
  a shown score is peer-relative, identify an unassessed cash-flow component, and find the
  supporting component evidence within one minute.
- **SC-006**: Every approved scoring change has a recorded rationale, before-and-after
  evaluation cases, and a distinct rules revision; unapproved proposals produce zero changed
  user-visible scores.

## Assumptions

- The current baseline remains the six financial measures and three component groups defined
  by feature 001; this feature evaluates that baseline rather than presuming new financial
  metrics.
- The existing equal-weight calculations in the component blocks and the three-component
  Total Score remain in force unless an evaluation finding is explicitly approved. The user's
  emphasis on Cash Flow establishes prominent risk disclosure, not automatic permission to
  change score weights.
- Stock-list column names and order remain those defined by feature 006; supporting detail is
  available through the existing scorecard or detail surface.
- Scores support research and risk analysis but do not replace a user's independent judgment
  or constitute personalized advice.
- Evaluation uses the currently selected and permitted financial-data source; expanding
  providers or redistributing provider-derived data is outside this feature.
