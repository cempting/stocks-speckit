# Feature Specification: Fundamental Grading Layout

**Feature Branch**: `main` (existing branch; no branch-creation hook registered)

**Created**: 2026-10-28

**Status**: Draft

**Updated**: 2026-10-28 (planning scope confirmed by user)

**Input**: Modify Tab 3 (Fundamental Grading) to reproduce a three-column layout:
Quality contains Gross Margin, Operating Margin, and ROCE; Growth contains Sales YoY,
EPS YoY, and EPS Consistency displayed as X/8 quarters; Cash Flow contains Cash
Conversion and FCF Margin. Stack each column's metrics vertically, place dynamic
analytical commentary underneath every metric value, and show "N/A" with
"Data not available" for missing metrics.

## Planning Clarifications

- The user approved expanding this feature to build the missing three-tab flow
  and stock-selection foundation, rather than waiting for the parent feature.
- The user approved adding quarterly balance-sheet evidence to support ROCE.
- Metric blocks must be compact, with quarterly historical bar charts using
  four to eight actual comparable quarters when available. Commentary remains
  directly underneath the metric value; charts do not interrupt that association.
- Source coverage may be shorter than eight quarters. Do not invent historical
  observations or a complete EPS Consistency count.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the Exact Fundamental Matrix (Priority: P1)

As an investor reviewing a stock in Fundamental Grading, I want a predictable
three-column matrix so I can locate and compare its financial characteristics.

**Why this priority**: The specified grouping and ordering are the core requested
change and make the scorecard consistently readable.

**Independent Test**: Open Tab 3 for a stock with all eight metrics available and
compare its headings, metric labels, order, and values with the reference matrix.

**Acceptance Scenarios**:

1. **Given** a stock with complete fundamental data, **When** its Tab 3 scorecard
   appears at a desktop viewport, **Then** three equally sized structural columns
   appear from left to right as Quality, Growth, and Cash Flow.
2. **Given** the three columns, **When** the user reads top to bottom, **Then**
   each contains exactly the metric sequence in FR-002, without moving metrics
   between columns or turning each metric into a separate structural column.
3. **Given** a valid EPS Consistency count of six, **When** the metric appears,
   **Then** its value reads exactly "6/8 quarters"; counts zero and eight read
   "0/8 quarters" and "8/8 quarters".
4. **Given** multiple displayed stocks, **When** the user compares their scorecards,
   **Then** every stock uses the same headings, labels, and metric order.

---

### User Story 2 - Interpret Each Metric in Context (Priority: P2)

As an investor, I want a short analytical comment immediately underneath each
metric value so I can understand what that value means without confusing it with
a neighboring metric's interpretation.

**Why this priority**: Commentary makes the matrix informative rather than a list
of unexplained numbers.

**Independent Test**: Present controlled stock data and associated metric-specific
commentary, change the selected stock, and verify that each comment appears below
its own value and changes with the corresponding evidence.

**Acceptance Scenarios**:

1. **Given** a negative Operating Margin and the associated comment "Losing money
   on operations", **When** the metric appears, **Then** that string appears
   immediately beneath its value within the Quality column.
2. **Given** a Gross Margin interpretation of "Premium pricing power", **When**
   the scorecard appears, **Then** the comment is beneath Gross Margin, not a
   column-wide subtitle or another metric's comment.
3. **Given** a change of stock or updated financial evidence, **When** the
   scorecard refreshes, **Then** all values and comments refer to the current
   stock and evidence, with no retained comments from the previous scorecard.
4. **Given** long commentary, **When** it wraps onto multiple lines, **Then**
   it remains in its own column and before the next metric's label.

---

### User Story 3 - Recognize Missing Evidence (Priority: P1)

As an investor, I want unavailable metrics to remain in their expected positions
with explicit missing-data text so I do not mistake absent data for weak or zero
performance.

**Why this priority**: Incomplete financial coverage must not mislead the user or
break comparisons.

**Independent Test**: Omit each of the eight metrics in turn, then omit all metrics,
and verify the exact fallback text, stable layout, and preservation of valid data.

**Acceptance Scenarios**:

1. **Given** a missing metric, **When** its scorecard appears, **Then** its label
   remains in place, its value is exactly "N/A", and the text directly beneath
   it is exactly "Data not available".
2. **Given** one missing metric and seven valid metrics, **When** the scorecard
   appears, **Then** only the missing metric uses the fallback; valid metrics
   retain their own values and commentary.
3. **Given** all eight metrics are unavailable, **When** the stock's scorecard
   appears, **Then** all three headings and eight labelled slots remain visible
   with the required fallback pair in every slot.
4. **Given** fewer than eight comparable EPS quarters, **When** EPS Consistency
   appears, **Then** it shows the fallback pair rather than implying eight
   observed quarters.

---

### User Story 4 - Reach Grading Through the Three-Step Flow (Priority: P1)

As an investor, I want to select an industry, inspect its dated available stock
members, and choose stocks for grading without switching between routed pages.

**Why this priority**: Repository inspection established that neither Tab 3 nor
its stock-selection handoff currently exists.

**Independent Test**: Use a dated, explicitly labelled fixture catalog to select
a sector, an industry, and two stocks, then review their fundamental scorecards.

**Acceptance Scenarios**:

1. **Given** the app entrypoint, **When** it opens, **Then** the progressive stages
   are Sector/Industry Screen, Industry Deep-Dive, and Fundamental Grading.
2. **Given** verified dated membership, **When** an industry is selected, **Then**
   Industry Deep-Dive shows its available members with membership date/source and
   lets the user select stocks for grading.
3. **Given** selected stocks, **When** grading is requested, **Then** only the
   requested displayed stocks are fetched and their scorecards appear in Tab 3.
4. **Given** an ordinary rerun, **When** parent context remains valid, **Then**
   selections persist; changing industry, evidence mode, or membership context
   clears only dependent invalid selections with visible explanation.
5. **Given** no verified membership or unapproved live display rights, **When**
   the user reaches the affected stage, **Then** an actionable limitation appears
   and no guessed members or unauthorized live financial requests are used.

### User Story 5 - Inspect Recent Financial History (Priority: P2)

As an investor, I want small historical bar charts within the metric blocks so I
can inspect recent quarterly evidence without leaving the matrix.

**Independent Test**: Provide eight, five, four, and three comparable quarterly
observations and inspect chart presence, chronological order, and missing history.

**Why this priority**: Compact history adds context without changing metric values
or the required three-column structure.

**Acceptance Scenarios**:

1. **Given** four through eight comparable quarterly observations for a metric,
   **When** the block appears, **Then** a compact chronological bar chart shows
   those actual values after the commentary, with reporting periods available.
2. **Given** more than eight comparable observations, **When** history appears,
   **Then** only the latest eight are shown.
3. **Given** fewer than four comparable observations, **When** the block appears,
   **Then** no misleading chart is drawn and "Insufficient quarterly history"
   appears separately from the current value and its commentary.

### Edge Cases

- Zero and negative numeric values remain visible when valid; they are not
  missing merely because they are non-positive.
- Missing, non-finite, or mathematically undefined metrics use the fallback pair
  rather than showing raw nulls, invalid numbers, or guessed values.
- EPS Consistency accepts whole counts from zero through eight only; an invalid
  count is unavailable rather than clamped or presented as a valid observation.
- Cash Conversion can be unavailable because its denominator is invalid while
  FCF Margin and all other valid metrics remain visible.
- A missing analytical interpretation for an otherwise valid value must not
  erase the value or imply missing financial data; use neutral metric-specific
  text as described in FR-006.
- A narrow viewport may stack the structural columns in Quality, Growth, Cash
  Flow order; it must retain within-column order and value/comment association.
- Financial data retrieval failures retain the application's actionable error
  reporting; metric fallback text must not disguise a failed request as success.
- Missing or unverified industry membership prevents stock selection for that
  industry; a guessed symbol list is not a substitute for dated membership.
- A metric can have a valid current value but fewer than four comparable history
  points. Keep the current value and explain the missing chart separately.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Tab 3, labelled Fundamental Grading, MUST display each stock's metric
  matrix in exactly three equal-width structural columns on desktop, headed
  Quality, Growth, and Cash Flow from left to right.
- **FR-002**: The columns MUST contain the following exact labels and top-to-bottom
  order; the empty final Cash Flow cell means no ninth metric is introduced:

  | Position | Quality | Growth | Cash Flow |
  |----------|---------|--------|-----------|
  | First | Gross Margin | Sales YoY | Cash Conversion |
  | Second | Operating Margin | EPS YoY | FCF Margin |
  | Third | ROCE | EPS Consistency | |

- **FR-003**: Each of the eight metric slots MUST present its label, then its
  value, then its own commentary text immediately underneath the value. Slots
  within a column MUST be stacked vertically.
- **FR-004**: EPS Consistency MUST display an available whole count X from zero
  through eight as the exact string "X/8 quarters". Other metrics MUST retain
  their established units, precision, and period context without changing their
  underlying financial meaning.
- **FR-005**: Each available metric MUST support a dynamic, metric-specific
  analytical string derived from or supplied with the current stock's financial
  evidence. Commentary MUST update with the value and MUST NOT be a single static
  phrase reused regardless of the metric or evidence. The supplied example
  phrases are illustrative, not newly mandated financial thresholds.
- **FR-006**: If a valid metric has no analytical interpretation, its commentary
  MUST use a neutral string containing that metric's label and formatted value,
  without asserting unsupported financial strength or weakness.
- **FR-007**: An unavailable metric MUST show the exact value "N/A" and exact
  helper text "Data not available", replacing analytical commentary for that
  slot. Missing data MUST NOT be replaced with zero or another stock's data.
- **FR-008**: Every metric label and column heading MUST remain visible regardless
  of data sufficiency. One missing metric MUST NOT suppress another valid metric
  or the enclosing column.
- **FR-009**: The matrix MUST apply consistently to every stock presented in Tab 3,
  including stocks reached through existing pagination or selection controls.
- **FR-010**: This feature MUST replace earlier displayed raw-metric lists only
  where they conflict with FR-002. It MUST NOT change industry-peer grading
  formulas, peer populations, financial cutoffs, stock eligibility, filters, or
  valid selection persistence. The approved navigation migration in FR-012 is the
  sole exception to preserving navigation. Existing aggregate grades and evidence
  disclosures may remain outside the eight-slot matrix; this feature does not
  invent aggregate grading logic that is absent from the current implementation.
- **FR-011**: Metric availability MUST remain distinct from operational errors.
  Existing data-source failure, freshness, and sufficiency disclosures MUST remain
  accessible alongside the updated matrix.
- **FR-012**: The app MUST provide the three stages named in Story 4 as one
  progressive tabbed experience, replacing routed page transitions and providing
  migration guidance for existing entry links.
- **FR-013**: Industry Deep-Dive MUST allow selection only from available dated,
  sourced industry stock membership, distinguish fixture from live evidence,
  display coverage limits, and pass stable stock identities to Tab 3.
- **FR-014**: Stock selections MUST be session-local, survive valid reruns, and
  clear only when invalidated by a parent/evidence context change.
- **FR-015**: Metric blocks MUST use compact label/value/commentary presentation
  rather than standard dashboard metric tiles. Each block MUST support a
  historical bar chart of its latest four to eight comparable quarterly values.
- **FR-016**: Charts MUST use actual chronological reporting observations without
  padding, interpolating, duplicating annual figures as quarters, or filling gaps
  with zero. Fewer than four comparable points MUST show the separate history
  limitation specified in Story 5. EPS Consistency history requires complete
  eight-quarter windows for every historical count.
- **FR-017**: The financial retrieval operation MUST supply one stock's available
  evidence for all eight metrics together, including balance-sheet evidence for
  ROCE, with explicit freshness and source context. Repeated grading requests for
  unchanged fresh evidence MUST reuse that evidence; refresh MUST affect only the
  requested stock/context, and failures MUST remain visible rather than becoming
  successful cached results.

### Key Entities *(include if feature involves data)*

- **Stock Fundamental Scorecard**: The current stock and financial observation
  context with its ordered Quality, Growth, and Cash Flow metric groups.
- **Fundamental Metric**: A named financial measure with a value, units, reporting
  period, availability state, and associated analytical commentary.
- **EPS Consistency Observation**: A count of qualifying quarters across eight
  completed quarters, including whether the full comparison window is available.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every stock in complete-data acceptance examples, users see
  exactly three ordered headings and eight metric labels matching FR-002, with
  zero misplaced, omitted, or additional matrix metrics.
- **SC-002**: Every available metric in acceptance examples has a non-empty
  commentary string immediately beneath its value; changing the stock or evidence
  produces zero mismatched value/comment pairs.
- **SC-003**: Across eight single-missing-metric examples and one all-missing
  example, 100% of unavailable slots show exactly "N/A" and "Data not available",
  and 100% of unaffected valid slots preserve their values.
- **SC-004**: EPS Consistency examples covering all nine valid counts from zero
  through eight display the exact required count format; incomplete-window and
  invalid-count examples never claim a valid eight-quarter observation.
- **SC-005**: In a walkthrough using one complete and one partially populated
  scorecard, the reviewer can locate all eight measures, associate each comment
  with its value, and distinguish missing evidence from valid zero or negative
  performance without consulting external documentation.
- **SC-006**: Existing filtering, valid retained selections, implemented aggregate
  grading outcomes, and financial evidence disclosures remain unchanged in
  regression scenarios; the intentional navigation migration passes Story 4.
- **SC-007**: A fixture-based walkthrough completes all three stages for two
  selected stocks; invalid parent changes leave zero invalid selected stock IDs.
- **SC-008**: Four-, five-, and eight-quarter chart examples show exactly four,
  five, and eight chronological bars; a three-quarter example shows the history
  limitation without hiding an otherwise available current value.
- **SC-009**: Two identical fresh grading requests cause one financial retrieval
  operation; targeted refresh causes one new operation for that stock and none
  for unrelated stocks. A failed operation is never reused as successful evidence.

## Assumptions

- The textual matrix supplied in the request is the authoritative layout reference;
  no additional screenshot-specific colors, typography, spacing, or decorations
  are inferred.
- This is a presentation-focused extension of the
  [Progressive Stock Screener specification](../001-market-leadership-screener/spec.md).
  It overrides that specification's displayed raw-metric list for Tab 3, but does
  not redefine its scoring formulas or expand the screening journey.
- The owning surfaces are the app entrypoint, the approved three-step selection
  foundation, and a new Fundamental Grading scorecard. This workflow specifies
  the change only; implementation and tests follow in planning and tasks.
- Existing financial definitions, formatting conventions, and analytical rules
  are reused where available. Planning must identify evidence sources for all
  eight metrics; unavailable evidence is disclosed rather than fabricated.
- In the absence of an established definition, EPS Consistency means the number
  of the latest eight completed fiscal quarters with strictly positive diluted
  EPS. Zero EPS does not qualify, and fewer than eight comparable quarters makes
  this metric unavailable.
- A valid value without an interpretation uses the neutral commentary fallback;
  this request does not introduce new financial-rating thresholds or investment
  recommendations.
- Existing stock controls are absent, so the approved foundation introduces them.
  Adaptive consolidation, new technical filters, revised ranking algorithms, and
  new peer-scoring algorithms from the larger parent feature are not implicitly
  included. Existing discovery calculations are reused with accurate labels;
  legacy weekly evidence is not relabelled as one-day/one-week price performance.
- No complete authorized live industry membership source has been established.
  The foundation supports a validated dated catalog and deterministic fixtures;
  live operation requires provenance, coverage, and display-rights review first.
- Desktop is the reference three-column view; narrow-screen reflow preserves
  reading order.
