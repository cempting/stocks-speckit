# Feature Specification: Industry ETF Momentum

> Historical baseline retained on 2026-11-02. This document is not an active specification.
> Current requirements and the supersession map are in [feature 008](../008-industry-representation-tools/spec.md)
> and the [feature 007 redirect](spec.md). Original requirements and status below are retained as history.

**Feature Branch**: `007-industry-etf-momentum`  
**Created**: 2026-10-31  
**Status**: Draft  
**Updated**: 2026-10-31 (aligned with feature 010)  
**Input**: User description: "the industry momentum table does not provide the industry-etf data as expected. for each industry or sub-industry a apropriate etf shall be mapped and used to show the momentung"

## Catalog Authority and Representation Revision

The [feature 010 specification](../010-manifest-csv-catalogs/spec.md) makes the reviewed hierarchy,
ETF listings/mappings, and approval evidence manifest-managed file records. Sector, industry,
and sub-industry mappings use exact region/classification/version/node/listing identities;
no catalog database or embedded ticker roster supplies them. Feature 008 adds explicitly reviewed
stock baskets where no ETF is approved. Such rows are labeled basket alternatives, never ETF
momentum; no automatic stock/index/parent substitute is permitted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Industry ETF Momentum (Priority: P1)

An investor reviewing the industry momentum table can see the appropriate mapped ETF and its
momentum for every industry or sub-industry row, so the displayed momentum represents that
classification rather than an unrelated proxy.

**Why this priority**: The table's primary purpose is to compare industry momentum; without an
appropriate mapped instrument, that comparison is misleading or incomplete.

**Independent Test**: Select a region with reviewed industry and sub-industry classifications and
verify that each covered row identifies its mapped ETF and displays momentum derived from that ETF.

**Acceptance Scenarios**:

1. **Given** an industry or sub-industry has an approved ETF mapping and sufficient price history,
   **When** an investor opens the industry momentum table, **Then** the row shows the ETF identifier
   and momentum calculated from that ETF.
2. **Given** both a parent industry and a sub-industry have different approved ETF mappings,
   **When** both rows are displayed, **Then** each row uses and identifies its own mapping.
3. **Given** a previously shown classification lacks a valid ETF mapping, **When** the investor
   views its row, **Then** ETF momentum is unavailable; only a separately approved basket may
   display labeled alternative momentum, never momentum from a different classification.

---

### User Story 2 - Trust Mapping Coverage (Priority: P2)

An investor can distinguish between an approved mapped ETF with unavailable market evidence and a
classification for which no appropriate ETF exists, so missing values are interpretable.

**Why this priority**: Clear coverage and evidence states prevent investors from treating an
unavailable value as a valid weak-momentum result.

**Independent Test**: Use classifications with a valid mapping but unavailable price history, no
mapping, and an invalid mapping; verify that each has a distinct, explanatory table state.

**Acceptance Scenarios**:

1. **Given** an approved ETF mapping has insufficient or unavailable price evidence, **When** the
   table is rendered, **Then** the ETF remains identified and its momentum state explains that
   market evidence is unavailable or insufficient.
2. **Given** a classification has neither an approved appropriate ETF nor an explicit approved
   basket, **When** the table is rendered,
   **Then** it is labeled as not covered and no momentum value is fabricated.

### Edge Cases

- A mapped ETF is inactive, returns no history, or has insufficient history for the selected
  momentum period: retain the ETF identifier and show an explicit unavailable or insufficient
  state.
- A classification is present in the reviewed hierarchy but has no appropriate ETF: show a clear
  not-covered state without substituting a sector, broad-market, or parent ETF.
- A mapping is duplicated or belongs to the wrong region/classification: reject it as invalid and
  show an explicit invalid-mapping state.
- A parent industry and a child sub-industry map to the same appropriate ETF: display the same ETF
  only when that mapping is explicitly approved for both rows.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain an approved ETF mapping for each covered industry and
  sub-industry classification in the reviewed hierarchy.
- **FR-002**: The system MUST use a row's approved ETF mapping as the sole source of displayed
  ETF momentum. A feature 008 reviewed basket MAY supply explicitly labeled alternative momentum
  only when no effective ETF is approved; it MUST NOT be presented as ETF evidence.
- **FR-003**: The industry momentum table MUST display the mapped ETF identifier beside each
  covered classification's momentum result.
- **FR-004**: The system MUST never substitute a parent, sector, broad-market, or arbitrary ETF
  when a classification has no approved ETF mapping.
- **FR-005**: The system MUST identify each row's coverage/evidence condition as available,
  insufficient evidence, unavailable evidence, not covered, or invalid mapping.
- **FR-006**: The system MUST preserve the distinction between no approved mapping and a mapped
  ETF whose price evidence cannot produce momentum.
- **FR-007**: The system MUST validate that each approved mapping is associated with the intended
  region and classification level before using it in the momentum table.
- **FR-008**: The system MUST apply the selected as-of date consistently to the mapped ETF
  momentum and visibly indicate when evidence is not valid for that date.
- **FR-009**: Hierarchy, ETF mappings/listings, and approval provenance MUST resolve from one
  activated manifest-backed file release without catalog database access or embedded listings.
  Every active reviewed node MUST remain visible; changed/invalid required sources MUST be
  reported and MUST NOT silently retain an unchecked or substituted representation.

### Key Entities *(include if feature involves data)*

- **Classification ETF Mapping**: An approved association between a region-specific industry or
  sub-industry classification and the ETF used to represent its momentum.
- **ETF Momentum Evidence**: The mapped ETF identity, applicable as-of date, momentum result, and
  coverage/evidence state used for one classification row.
- **Industry Momentum Row**: A displayed classification and its corresponding mapping/evidence
  details.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of rows with approved ETF mappings show the correct mapped ETF identifier and
  momentum derived from that same ETF.
- **SC-002**: 100% of rows without an approved ETF or explicit valid basket show a non-momentum
  state. Basket rows identify their alternative source, and zero rows display substituted ETF
  momentum or mislabel basket results as ETF momentum.
- **SC-003**: For a reviewed test hierarchy containing mapped parent and sub-industry rows, all
  rows can be independently verified against their approved mappings.
- **SC-004**: An investor can distinguish no mapping from unavailable or insufficient ETF evidence
  for every non-numeric momentum row.
- **SC-005**: With the catalog database unavailable, every controlled approved mapping resolves
  from the active files to its exact listing and period. A reviewed file-only mapping change
  changes affected requests/results without a code edit, and invalid sources create zero fallback
  instruments or automatic approvals.

## Assumptions

- The reviewed regional classification hierarchy remains the source of the industry and
  sub-industry rows shown in the table.
- ETF appropriateness is a reviewed business decision captured in the approved mapping, rather
  than inferred automatically from an ETF name or a classification name.
- Some specialized classifications may have no appropriate ETF; explicit not-covered status is a
  valid result.
- This feature changes industry/sub-industry momentum representation only; it does not change
  stock-level charts, stock scoring, or the user's selected momentum period.
