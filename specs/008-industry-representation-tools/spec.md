# Feature Specification: Industry Representation Tools

**Feature Branch**: `008-industry-representation-tools`  
**Created**: 2026-10-31  
**Status**: Draft  
**Updated**: 2026-10-31 (aligned with feature 010)  
**Input**: User description: "Realize the tooling to investigate, find and implement the mapping of industries or sub industries to the relevent and apropriate ETF. In some cases there will not be an ETF representation, in these cases we need to put in an alternative."

## Catalog and Review Authority

The [feature 010 specification](../010-manifest-csv-catalogs/spec.md) supersedes database-backed
storage/commands while retaining this feature's approval and basket semantics. Worklists use
manifest-registered reviewed hierarchy; ETF mappings/listings, basket constituents/weights,
sources, decisions, and audit history persist in files. One stock CSV per region references exact
industries and optional sub-industries, linked through the hierarchy to sectors.
No catalog database, embedded constituent list, automatic basket, or parent substitution is allowed.

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

## Assumptions

- ETF suitability and basket membership are reviewed decisions, not automatically inferred.
- Stock baskets are explicitly approved alternatives only when no appropriate ETF is approved,
  not automatically generated fallback data. Missing constituent history is never reweighted away,
  and basket price/volume charts are not fabricated.
- Existing GICS sector mapping governance, source approval, and effective-date behavior apply.
