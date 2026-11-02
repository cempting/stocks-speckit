# Feature Specification: Industry Representations and Momentum

**Feature Branch**: `008-industry-representation-tools`  
**Created**: 2026-10-31  
**Status**: Draft  
**Updated**: 2026-11-02 (absorbs feature 007)

**Consolidates**: [007: Industry ETF momentum](../007-industry-etf-momentum/spec.md).
This document owns both reviewed ETF/basket representation and its momentum evidence.
Original requirement IDs and acceptance criteria are mapped in the redirect. Existing plans,
tasks, research, data models, checklists, and contracts must be reconciled before further execution;
their completion markers and historical test evidence remain unchanged.
**Input**: User description: "Realize the tooling to investigate, find and implement the mapping of industries or sub industries to the relevent and apropriate ETF. In some cases there will not be an ETF representation, in these cases we need to put in an alternative."

## Catalog and Review Authority

The [feature 010 specification](../010-manifest-csv-catalogs/spec.md) supersedes database-backed
storage/commands while retaining this feature's approval and basket semantics. Worklists use
manifest-registered reviewed hierarchy; ETF mappings/listings, basket constituents/weights,
sources, decisions, and audit history persist in files. One stock CSV per region references exact
industries and optional sub-industries, linked through the hierarchy to sectors.
No catalog database, embedded constituent list, automatic basket, or parent substitution is allowed.

[Feature 004](../004-sector-stock-explorer/spec.md) owns the consuming table/chart controls and
tooltips, not representation approval. [009](../009-local-etf-discovery/spec.md) collects candidate
evidence but does not approve it; [010](../010-manifest-csv-catalogs/spec.md) owns file publication.
[Feature 012](../012-stock-industry-memberships/spec.md) separately owns the custom hierarchy
migration: existing ETF/basket approvals retain exact node, scope, dates, and provenance and
require reviewed applicability before reuse in the new scheme. Overlapping memberships never
create a representation or authorize approval automatically.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Industry Representations (Priority: P1)

A research reviewer can inspect every industry or sub-industry lacking an approved representation,
evaluate candidate ETFs, and record a reviewed ETF mapping when one accurately represents it.

**Why this priority**: Complete, auditable ETF representation is required before users can trust
industry momentum.

**Independent Test**: A reviewer can list unmapped classifications, record a suitable ETF mapping,
and verify that it appears as the classification’s representation.

**Acceptance Scenarios**:

1. **Given** a reviewed hierarchy with unmapped classifications, **When** a reviewer opens the
   representation worklist, **Then** every unmapped industry/sub-industry is identifiable.
2. **Given** a reviewer approves an appropriate ETF, **When** the mapping is saved, **Then** the
   mapped classification, ETF, effective date, source, and approval reference are retained.
3. **Given** a manifest-backed reviewed file release and no catalog database, **When** approval
   is published, **Then** mapping/listing/scope/date prerequisites are checked and mapping plus
   governance evidence are published together; failure leaves no partial approval.

### User Story 2 - Use Reviewed Stock-Basket Alternatives (Priority: P2)

A reviewer can define a reviewed constituent-stock basket when no suitable ETF exists, so the
classification still has a transparent alternative representation.

**Why this priority**: Specialized classifications often lack an ETF; a reviewed basket provides
coverage without implying an ETF exists.

**Independent Test**: Define a basket for an ETF-less classification and verify its momentum is
identified as a stock-basket alternative, not ETF momentum.

**Acceptance Scenarios**:

1. **Given** no appropriate ETF exists, **When** a reviewer approves a stock basket, **Then** the
   classification records the basket constituents, weights, effective dates, source, and approval.
2. **Given** a user views momentum for that classification, **When** the basket is active, **Then**
   the representation is labeled as a stock-basket alternative and the displayed momentum comes
   only from its approved constituents.

### User Story 3 - Trust Each Node's Momentum Evidence (Priority: P1)

An investor can identify the exact ETF or approved basket behind each industry's momentum and
distinguish absent approval from insufficient market history.

**Independent Test**: Display independently mapped parent/child nodes, an uncovered node, an
invalid mapping, and an approved ETF without adequate history; verify identities and every
distinct evidence state at the selected as-of date.

**Acceptance Scenarios**:

1. **Given** independently approved parent/child ETF mappings with sufficient history, **When**
   momentum is displayed, **Then** each row identifies and uses only its own approved ETF.
2. **Given** the same ETF is suitable for two nodes, **When** both rows use it, **Then** each
   mapping has its own explicit reviewed applicability; sharing a parent supplies no approval.
3. **Given** no approved representation, invalid mapping, or approved ETF with missing history,
   **When** rows render, **Then** these conditions remain distinguishable, the known ETF stays
   identified, and no parent, sector, broad-market, or arbitrary instrument is substituted.
4. **Given** an out-of-period mapping or wrong classification scope, **When** the as-of date is
   applied, **Then** the mapping cannot supply momentum and the affected reason is visible.

### Edge Cases

- A classification has neither an approved ETF nor an approved basket: it remains explicitly not
  covered.
- A basket has missing, inactive, or invalid constituent evidence: its momentum is unavailable or
  insufficient and no substitute is fabricated.
- A basket’s weights do not total 100%: it cannot be approved.
- A mapping or basket is outside its effective date range: it cannot be used for that as-of date.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a review worklist for every active industry/sub-industry
  without an approved effective representation.
- **FR-002**: The system MUST let reviewers record an approved ETF representation with
  classification identity, source, approval reference, and effective dates.
- **FR-003**: The system MUST let reviewers record a stock-basket alternative only when no
  appropriate ETF is approved.
- **FR-004**: A stock-basket alternative MUST identify all approved constituents and weights; its
  weights MUST total exactly 100%.
- **FR-005**: The system MUST validate that every ETF or basket constituent is a reviewed,
  verified listing for the intended region and effective date.
- **FR-006**: The momentum table MUST visibly distinguish ETF representations, stock-basket
  alternatives, and not-covered classifications.
- **FR-007**: The system MUST calculate alternative momentum only from the approved active basket
  constituents and weights.
- **FR-008**: The system MUST retain source and approval evidence for every approved mapping or
  alternative.
- **FR-009**: Worklists, verified listing identities, exact classification relationships,
  approvals, baskets, and audit history MUST use manifest-registered file sources only.
  Publication MUST be coherent and reject invalid references, effective-period conflicts,
  changed source identity, or concurrent publication conflicts without partial approval.
- **FR-010**: File-only migration MUST retain each existing reviewed node, listing, ETF/basket,
  constituent weight, approval reference, and provenance identity or explicitly quarantine it
  with an actionable reason. Retirement of database commands MUST provide migration guidance;
  migrated source lists MUST NOT fabricate new approvals.
- **FR-011**: Every covered industry or nested industry node MUST have an exact approved
  representation for its region, classification/version, node, listing, and effective dates.
  Displayed ETF momentum MUST derive solely from that node's approved ETF; an approved basket
  MAY supply labeled alternative momentum only when no effective appropriate ETF is approved.
  Parent and descendant mappings MUST be validated independently, even if they share an ETF.
- **FR-012**: Each covered ETF row MUST visibly identify its ETF beside momentum. A basket
  MUST be labeled as a stock-basket alternative, never ETF evidence. Status/type explanations
  MAY use the name-button tooltips specified by 004; this requirement adds no removed columns.
- **FR-013**: A missing, invalid, or inapplicable representation MUST NOT be replaced with a
  parent, sector, broad-market, index, automatically selected stock/basket, or arbitrary ETF.
- **FR-014**: Rows MUST distinguish available, insufficient evidence, unavailable evidence,
  not covered, and invalid mapping. No approved mapping MUST remain distinct from an approved
  ETF whose price history is missing, inactive, or too short; retain its known ETF identity.
- **FR-015**: The selected as-of date MUST apply consistently to representation applicability,
  verified listings, and momentum observations. Out-of-period evidence MUST be visibly invalid
  or unavailable rather than used as current evidence.
- **FR-016**: Every active reviewed node in the selected scope MUST remain discoverable,
  including nodes without stock members or approved representations. Required-source identity
  failures MUST be explicit and MUST NOT silently preserve an unchecked mapping.

### Key Entities

- **Representation Review Item**: A classification needing an approved ETF or basket.
- **ETF Representation**: A reviewed ETF mapped to one classification and effective period.
- **Stock-Basket Alternative**: A reviewed weighted set of verified constituent listings used only
  where no ETF representation is approved.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of active reviewed classifications appear in the worklist with an explicit
  representation status.
- **SC-002**: 100% of displayed ETF and basket momentum rows identify their representation type.
- **SC-003**: 100% of approved stock baskets have verified constituents and weights totaling 100%.
- **SC-004**: No classification without an approved effective representation displays substituted
  momentum.
- **SC-005**: With the catalog database unavailable, controlled worklist and ETF/basket approval
  scenarios preserve 100% of exact scope/listing/date/weight/provenance checks. Failed publication
  leaves zero partial approvals, and migration accounts for every legacy governed record.
- **SC-006**: In controlled covered rows, 100% identify the correct approved ETF and calculate
  momentum from that ETF's own observations.
- **SC-007**: In controlled uncovered/invalid cases, zero rows substitute momentum; every valid
  basket row identifies its alternative source and zero baskets are labeled ETF evidence.
- **SC-008**: Every parent and nested-node mapping in a controlled hierarchy is independently
  verifiable against its exact approval, including shared-ETF cases.
- **SC-009**: For every controlled non-numeric momentum row, no mapping, invalid mapping, and
  unavailable/insufficient approved-ETF history are distinguishable with the correct explanation.
- **SC-010**: With the database unavailable, 100% of controlled mappings resolve from the
  active files to the exact listing/date. Reviewed changes affect only relevant requests/results
  without code edits; altered/invalid sources cause zero fallback instruments or automatic approvals.

## Assumptions

- ETF suitability and basket membership are reviewed decisions, not automatically inferred.
- Stock baskets are explicitly approved alternatives only when no appropriate ETF is approved,
  not automatically generated fallback data. Missing constituent history is never reweighted away,
  and basket price/volume charts are not fabricated.
- Existing GICS sector mapping governance, source approval, and effective-date behavior apply.
