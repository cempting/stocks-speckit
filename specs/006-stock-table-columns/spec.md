# Feature Specification: Stock Table Columns

**Feature Branch**: `006-stock-table-columns`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "the stocks table shall have price chart + 50MA, volume chart,
ticker, name, CAP type, Total Score"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Stock Table Columns (Priority: P1)

As an investor viewing the stocks table, I want one concise, predictable set of comparison
columns, so I can assess price movement, trading activity, identity, capitalization type, and
Total Score without unrelated fields.

**Why this priority**: The stocks table is the primary comparison surface after selecting an
industry.

**Independent Test**: Display stocks with complete, incomplete, and unavailable evidence and
verify that every table presents exactly the required six columns in order, while unavailable
data remains explicitly identified.

**Acceptance Scenarios**:

1. **Given** a stocks table with complete evidence, **When** it is displayed, **Then** it shows
   Price chart + 50 MA, Volume chart, Ticker, Name, CAP Type, and Total Score in that order.
2. **Given** a stock with insufficient price history for the moving average, **When** the table
   is displayed, **Then** its price chart remains visible and identifies the insufficient moving
   average.
3. **Given** a stock without a usable capitalization value, **When** the table is displayed,
   **Then** CAP Type explicitly identifies the value as unavailable rather than assigning a
   category.
4. **Given** a stock whose score evidence is incomplete, **When** the table is displayed,
   **Then** Total Score shows the existing explicit non-numeric state rather than a numeric
   fallback.

### User Story 2 - Preserve Stock Table Evidence States (Priority: P2)

As an investor, I want the simplified column set to retain evidence disclosures, so I can
distinguish unavailable data from poor investment characteristics.

**Why this priority**: A concise table must not conceal missing chart, capitalization, or score
evidence.

**Independent Test**: Render rows with unavailable charts, capitalization, score evidence, and
placeholder identity; verify the table contains the required columns and all affected values
remain explicit.

**Acceptance Scenarios**:

1. **Given** a stock with unavailable price or volume evidence, **When** the table is displayed,
   **Then** the affected chart cell remains explicitly unavailable or insufficient.
2. **Given** an unresolved placeholder, **When** the table is displayed, **Then** its identity
   remains identifiable and its CAP Type and Total Score are not fabricated.

### Edge Cases

- Stocks with missing, stale, invalid, or non-positive capitalization values do not receive a CAP
  Type.
- A stock with insufficient price history does not lose its price chart merely because its 50 MA
  is unavailable.
- A missing or unresolved listing does not produce a live capitalization request.
- Total Score remains distinct between not loaded, error, insufficient, and unavailable states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The stocks table MUST show exactly these visible columns in order: Price chart + 50
  MA, Volume chart, Ticker, Name, CAP Type, Total Score.
- **FR-002**: The Price chart + 50 MA column MUST retain the stock's own price chart and
  explicitly identify insufficient moving-average evidence without hiding available price
  evidence.
- **FR-003**: The Volume chart column MUST retain the stock's own volume chart and explicitly
  identify unavailable or insufficient evidence.
- **FR-004**: CAP Type MUST classify a stock from its current valid capitalization value as Large
  for values greater than or equal to $10 billion, Mid for values greater than or equal to $2
  billion and less than $10 billion, and Small for values below $2 billion.
- **FR-005**: CAP Type MUST display an explicit unavailable state when no valid capitalization
  value exists, rather than assigning a category.
- **FR-006**: Total Score MUST use the existing overall-score meaning: the equally weighted
  average of Quality, Growth, and Cash Flow only when all three component scores are available;
  otherwise it MUST show the existing explicit non-numeric score state.
- **FR-007**: The table MUST retain ticker, stock name, and unresolved-placeholder identity
  presentation.
- **FR-008**: Displaying the table MUST NOT initiate hidden price, capitalization, or score
  loading.

### Key Entities *(include if feature involves data)*

- **CAP Type**: A named capitalization category derived from a stock's current valid
  capitalization value, or an explicit unavailable state.
- **Total Score**: The existing aggregate stock score, presented under the renamed Total Score
  column.
- **Stock Table Row**: A stock's price and volume evidence, identity, CAP Type, and Total Score
  used for table comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In controlled complete, unavailable, insufficient, and placeholder cases, 100% of
  stocks tables display only the six required columns in the required order.
- **SC-002**: In controlled capitalization cases, 100% of valid values map to the confirmed CAP
  Type category, and 100% of missing or invalid values display as unavailable.
- **SC-003**: In controlled chart and score evidence cases, 100% of unavailable or insufficient
  data remains explicitly identified without suppressing independent available evidence.
- **SC-004**: Users can identify a stock's ticker, CAP Type, and Total Score in under 10 seconds
  in a representative comparison scenario.

## Assumptions

- The existing Score column is renamed Total Score without changing its established three-component
  equal-weight calculation or load behavior.
- The change applies only to the stocks table, not to sector, industry, or stock-detail views.
- CAP Type uses existing available capitalization evidence only; it does not introduce a new
  market-data request.
- The previously accepted 50 MA price-chart and volume-chart presentation remain unchanged.
- CAP Type uses the confirmed three-tier thresholds: Large at or above $10 billion, Mid from $2
  billion up to $10 billion, and Small below $2 billion.
