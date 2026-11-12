# Feature Specification: US Industry and Theme ETF Discovery

**Feature Branch**: `main` (unchanged; no before-specify hook configured)

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "I added market data for the US etfs of industries and themes to the docs/markets/US folder. the data have been generated corresponding to the earlier prompt in this context.
I want to take these as a sources for providing industries and sub-industries for the discovery page.
Research whether and how this data can help the app to provide a usable data source.
Make sure that yFinance , which is the current data fetcher, can fetch the respective etf  data.
Research on how to renuvate the data catalog scheme."

## Clarifications

### Session 2026-11-12

- Q: Should the individual-stock detail workflow be specified as part of feature 018, remain owned by feature 017, or be split so that feature 018 covers discovery-to-detail navigation and feature 017 covers the detail data/chart/scoring behavior? → A: Keep the full individual-stock detail workflow in feature 017; feature 018 remains focused on category and ETF discovery.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover US industries and themes (Priority: P1)

As an investor, I want to explore reviewed US industry, sub-industry, and theme categories in
Discovery and see their associated ETF performance, so I can compare market leadership at the
level that matches my research question.

**Why this priority**: The supplied hierarchy and ETF mappings are useful only if people can
discover the categories and their performance through the existing application workflow.

**Independent Test**: Load a controlled US release with separate industry and theme
classifications, ETF mappings at all supplied levels, an unmapped category, and a category with
multiple approved ETF options. Verify category navigation, correct ETF attribution, and explicit
coverage gaps.

**Acceptance Scenarios**:

1. **Given** an active US release with more than one classification, **When** a user opens
   Discovery, **Then** they can select a classification and see only its reviewed hierarchy and
   ETF mappings; the selected classification is clearly identified.
2. **Given** the user selects a category, **When** Discovery advances through the hierarchy,
   **Then** it shows only that category's reviewed children at the next level and uses only the
   approved, effective ETF mapping or mappings for the exact displayed node.
3. **Given** a node has no active approved ETF or insufficient ETF history, **When** the user
   browses that node, **Then** the node remains discoverable and its missing coverage or history
   is explained without substituting a parent ETF or inventing a result.
4. **Given** multiple approved ETFs represent the same node, **When** the user views the node,
   **Then** the approved alternatives are distinguishable and none is selected solely by file
   order or ticker sorting.
5. **Given** the user changes the selected classification or a parent node, **When** Discovery
   updates, **Then** dependent selections from the prior path are cleared and no rows from the
   prior classification remain visible.
6. **Given** a user opens and operates Discovery at desktop and phone viewport widths, **When**
   they select classifications and browse ETF performance, **Then** controls, data, and
   availability explanations remain accessible without clipping, overlap, or page-level horizontal
   scrolling.
7. **Given** a US release has multiple active classifications, **When** a user opens Discovery or
   Industry Deep-Dive, **Then** the workflow identifies the selected classification explicitly
   and does not fail or choose one silently.

### User Story 2 - Publish the supplied market data as a governed source (Priority: P1)

A market-data reviewer wants to validate and publish the US files as one coherent, versioned
source, so that Discovery uses reproducible, reviewed data instead of independent files or
hard-coded ETF symbols.

**Why this priority**: The current files contain useful hierarchy, listing, and mapping records,
but their contents must be linked, reviewed, and versioned before they can safely serve as
authoritative application data.

**Independent Test**: Validate a controlled release with matching source evidence and all
required catalog artifacts. Verify that valid cross-file references can be published together,
while missing evidence, invalid references, or corrupt artifacts leave the previously active
release unchanged.

**Acceptance Scenarios**:

1. **Given** hierarchy, ETF listing, and representation files for the US, **When** a reviewer
   prepares a release, **Then** each artifact has an explicit role, scope, revision, row count,
   and content identity, and each referenced listing and hierarchy node resolves exactly.
2. **Given** the supplied files use separate industry and theme classifications, **When** the
   release is validated, **Then** their identities and versions remain distinct and neither is
   presented as an official classification unless its evidence explicitly establishes that status.
3. **Given** a mapping has missing, placeholder, or unreviewed source, approval, or suitability
   evidence, **When** a reviewer attempts to publish it as active, **Then** publication identifies
   the missing evidence and does not treat the mapping as approved.
4. **Given** a release is incomplete or fails validation, **When** publication is attempted,
   **Then** no partial release becomes active and the last valid release remains available.

### User Story 3 - See ETF data availability without losing the rest of Discovery (Priority: P2)

As a Discovery user, I want ETF price and volume history availability to be reported per
representation, so a bad or unsupported symbol does not hide otherwise usable categories or
mislead me with stale or fabricated performance.

**Why this priority**: ETF representations become actionable only when their market history can
be retrieved and interpreted; source availability must not be confused with classification
coverage.

**Independent Test**: Request a controlled batch containing ETFs with valid history, no provider
history, and insufficient lookback. Verify valid results remain usable and each unavailable
representation has an explicit reason and no success-shaped fallback.

**Acceptance Scenarios**:

1. **Given** an approved ETF listing with a provider symbol, **When** its price history is
   requested from the current US market-data source, **Then** the history is associated with that
   exact listing and provides the observations needed for supported Discovery comparisons.
2. **Given** one symbol returns no usable history or a provider error, **When** a batch contains
   other valid symbols, **Then** the unavailable ETF is reported explicitly and valid ETF results
   remain available.
3. **Given** a provider symbol differs from the display ticker, **When** history is requested,
   **Then** the verified provider symbol is used without guessing a suffix or substituting the
   display ticker.
4. **Given** the supplied files do not include reviewed stock memberships, **When** a user reaches
   a category's contained-stocks view, **Then** the application reports that membership data is
   unavailable and does not infer constituent stocks from an ETF's holdings or name.

### Edge Cases

- Two classifications contain nodes with the same display name or identifier text; their scoped
  identities must not collide or cause mixed results.
- An ETF is mapped to multiple nodes or appears multiple times for one node; each exact mapping
  must retain its own review and suitability evidence, with no silent conflict resolution.
- A provider symbol is valid but has no recent observations, insufficient history, or a temporarily
  unavailable response; distinguish these outcomes from an invalid catalog mapping.
- A node or listing is added, removed, or becomes ineffective in a new release while a user has it
  selected; stale selections and cached results must not survive as current data.
- The source CSVs parse correctly but contain generic source identifiers or no release-level
  evidence; syntactic validity must not be mistaken for review approval.
- A theme or industry has ETF performance data but no stock-membership data; display the available
  performance without implying stock constituents are available.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Discovery MUST use the active, validated US catalog as its source for sector,
  industry, sub-industry, theme, and ETF-representation data; it MUST NOT maintain a parallel
  hard-coded list of these categories or ETFs.
- **FR-002**: Discovery MUST allow the user to select among active US classifications and MUST
  keep their category hierarchy, ETF mappings, and selection state separate.
- **FR-003**: Discovery MUST present the active hierarchy progressively from parent category to
  industry and sub-industry, preserving the existing Discovery workflow and clearing selections
  that are no longer valid after a parent or classification change.
- **FR-004**: A category's ETF performance MUST use only active, approved ETF representations
  mapped to that exact classification, node, and effective period.
- **FR-005**: The catalog MUST preserve exact provider symbols independently from display tickers,
  and the current approved US market-data source MUST be able to request daily price and volume
  history for each configured provider symbol.
- **FR-006**: ETF-history retrieval and performance MUST report unsupported symbols, missing
  observations, insufficient history, and provider failures explicitly at the affected ETF or
  category; unavailable data MUST NOT be represented as a successful result or silently replaced.
- **FR-007**: A failed ETF-history request MUST NOT prevent unrelated valid ETF representations
  from remaining available.
- **FR-008**: Catalog publication MUST validate classification scope, hierarchy parentage,
  listing references, representation references, effective periods, source evidence, suitability,
  approval, and artifact integrity before making a release active.
- **FR-009**: Industry and theme classifications MUST remain separate, versioned identities.
  Theme mappings MUST NOT be labeled as official GICS or merged into an industry classification
  without explicit reviewed evidence and approval.
- **FR-010**: Catalog format changes MUST be explicitly versioned and have documented migration
  behavior; existing valid releases MUST remain readable or have a reviewed, verifiable migration
  path.
- **FR-011**: ETF listings and representations MUST NOT be treated as stock-membership evidence.
  Where reviewed stock-membership records are absent, contained-stock results MUST be identified
  as unavailable rather than inferred from ETF holdings.
- **FR-012**: The feature MUST extend the existing Discovery page without adding a root tab or
  navigation route. The affected workflow MUST remain usable at desktop and phone widths without
  clipping, overlapping controls, or requiring page-level horizontal scrolling.
- **FR-013**: Catalog-backed workflows that resolve a classification from a region and date MUST
  retain current behavior when exactly one classification is active and MUST require an explicit
  classification when more than one is active; they MUST NOT select one by release or file order.
- **FR-014**: Individual-stock detail data loading and presentation, including its chart,
  fundamentals, and scoring, MUST remain governed by feature 017; this feature MUST NOT add or
  redefine that workflow.

### Key Entities

- **Classification**: A region-scoped, versioned scheme such as the supplied US industry taxonomy
  or US theme taxonomy; it is not interchangeable with another scheme.
- **Hierarchy node**: A reviewed sector, industry, or sub-industry with a stable scoped identity,
  display name, parent relationships, and effective period.
- **ETF listing**: A verified ETF identity and regional listing, including display ticker,
  provider symbol, exchange, currency, and effective period.
- **ETF representation**: A reviewed, effective link from an exact classification node to an ETF
  listing, supported by source, approval, and suitability evidence.
- **Catalog release**: A versioned, integrity-checked set of hierarchy, listing, representation,
  source, and governance artifacts selected as the active source.
- **ETF history availability**: The per-listing state of requested daily price and volume data,
  including valid history, no data, insufficient history, and provider failure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of hierarchy nodes in a valid release are discoverable at the correct
  classification and hierarchy level, including nodes with no ETF mapping.
- **SC-002**: 100% of active ETF mappings resolve to exactly one active listing and exact,
  reviewed classification node; invalid or unreviewed mappings cannot appear as approved.
- **SC-003**: 100% of ETF representations requested for Discovery have either usable history and
  a calculated result or a visible, specific unavailable state; no failure is silently shown as
  successful performance.
- **SC-004**: Changing classification or parent category leaves zero stale selections or results
  from the previously selected path.
- **SC-005**: The Discovery workflow remains operable at 1440px and 390px viewport widths, with
  category selection, ETF availability explanations, and performance results visible and usable.

## Assumptions

- The five files currently in `docs/markets/US/` are the candidate input for this feature:
  `hierarchy.csv`, `etf_listings.csv`, `sector_etfs.csv`, `industry_etfs.csv`, and
  `sub_industry_etfs.csv`. At specification time they contain 65 hierarchy rows, 86 ETF listing
  rows, and 98 representation rows (47 sector, 28 industry, and 23 sub-industry mappings).
- The supplied files do not include a release manifest, release governance/audit artifact, or
  stock-membership or benchmark files. Their mappings are candidates until the required release,
  source, review, membership, and benchmark evidence is supplied or explicitly retained from
  another valid release; field presence alone does not establish approval.
- The supplied theme categories are a separate custom classification, not a new hierarchy node
  type. This feature reuses the existing sector/industry/sub-industry model unless reviewed
  evidence demonstrates a present need for a new node type.
- The current market-history source is yFinance and remains the only runtime source for this
  feature. Provider-symbol support and successful price/volume retrieval must be verified for the
  released ETF listings; this specification does not claim that all current candidate symbols
  have already passed a live provider check.
- ETF performance discovery does not create or imply stock membership. A separate reviewed
  membership source is required for contained-stock views.
- Manifest and publication lifecycle remain governed by feature 010, and custom classification
  and membership semantics remain governed by feature 012. This feature does not replace those
  contracts with an unversioned catalog redesign; affected plans and tasks must be reconciled
  before implementation.
