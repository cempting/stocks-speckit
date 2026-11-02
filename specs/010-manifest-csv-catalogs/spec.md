# Feature Specification: Manifest-Managed CSV Catalogs

**Feature Branch**: `main` (unchanged; feature key `010-manifest-csv-catalogs`)

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "reiterate the database for etf industries and stocks. I want ot keep the approach of the us gics sector etf representation as csv file. Breaking changes:
- For industries ans sub-industries of the us market I promote the same approach
- For stocks per industry I would create a csv as well
- we need a manifest to consolidate all the data sources
- please make suggestions if of have a more effective approach
- do not use hardcoded etf or stock listing, update the code to remove and refactor the code"

## Ownership and Versioned Membership Revision

This remains the distinct catalog-source, release-lifecycle, file-only governance-storage and
legacy-cutover feature after the 2026-11-02 consolidation.
[008](../008-industry-representation-tools/spec.md), incorporating 007, owns ETF/basket business
approval; [009](../009-local-etf-discovery/spec.md) owns candidate collection; and
[004](../004-sector-stock-explorer/spec.md), incorporating 003, owns runtime navigation/display.
The [authority map](../README.md) defines the remaining feature boundaries.

[012](../012-stock-industry-memberships/spec.md) is a separate, bounded versioned revision of this
feature's single-assignment and fixed industry/sub-industry assumptions. On reviewed adoption,
one named custom scheme supports concurrent dated memberships, deeper single-parent nesting,
deduplicated descendant rollups, and contextual peers. Earlier US GICS release semantics remain
historically reproducible; custom scope is not official GICS and old representation approvals
require explicit reviewed applicability before reuse. References below to one industry/optional
sub-industry describe the original version, not a restriction on the reviewed 012 version.
Manifest integrity, file-only storage, coherent publication and reconciliation remain binding.

Existing plans/tasks and partial file-release/runtime work are not proof that governed review,
legacy reconciliation/retirement, or either migration is complete. Consolidation changes no
schema, selected release, active feature pointer, completed task marker, or acceptance result.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain One Authoritative File-Based Catalog Release (Priority: P1)

A data reviewer maintains US GICS hierarchy and ETF representation CSVs, one stock CSV per
region, and a manifest identifying the sources that form a consistent reviewed release.
The manifest is the entry point, rather than a collection of independently configured files
or a database containing different versions of the same catalog.

**Why this priority**: A single source of authority makes the data inspectable, portable, and
maintainable without changing application code or reconciling two independently editable stores.

**Independent Test**: Prepare a controlled manifest and related CSVs, validate their references
and review evidence, and activate the release without a catalog database. Invalid or incomplete
releases cannot replace the active release.

**Acceptance Scenarios**:

1. **Given** reviewed hierarchy, ETF, and regional stock files, **When** the reviewer registers
   them in a manifest, **Then** their purpose, scope, version, source identity, review evidence,
   effective coverage, and required/optional status are explicit.
2. **Given** a stock references an industry and that industry references a sector, **When**
   validation runs, **Then** both references resolve to exact reviewed identities in the same
   region and classification version; fund/company names are not used to invent relationships.
3. **Given** a missing required file, mismatched content identity, unresolved reference, or
   conflicting effective assignment, **When** activation is attempted, **Then** it fails with
   source/row/reference context and the previously activated release is unchanged.
4. **Given** valid changes spanning several files, **When** the release is activated, **Then**
   all related views consume one consistent release, never a mixture of old and new sources.

---

### User Story 2 - Screen Stocks and ETF Representations from CSV References (Priority: P1)

A screener selects a region, sector, industry, or sub-industry and sees the stocks and approved
ETF representation supplied by the active files. Each regional stock row references its industry;
the reviewed hierarchy supplies the industry-to-sector relationship. Sub-industry references
are included only where reviewed evidence supports them.

**Why this priority**: This is the user-facing value of the new data model: a regional stock
catalog stays simple while hierarchy relationships support consistent filtering at every level.

**Independent Test**: Load a controlled release containing stocks assigned to two industries,
a reviewed sub-industry, and a hierarchy node without an ETF. Verify every filter and approved
representation. Activate a reviewed stock assignment/ETF change using files only and verify
the changed results without editing application code.

**Acceptance Scenarios**:

1. **Given** one regional stock CSV with exact industry references, **When** a sector is selected,
   **Then** the stock set is determined through reviewed industry-to-sector relationships,
   without requiring a stock CSV for each industry or duplicating sector authority on stock rows.
2. **Given** a reviewed sub-industry reference, **When** that sub-industry is selected, **Then**
   only its effective stock assignments appear; stocks known only at industry level are not
   silently assigned to a sub-industry.
3. **Given** approved US sector, industry, and sub-industry ETF records, **When** the corresponding
   view requests representation evidence, **Then** the exact effective reviewed listing is used
   with its source and approval information, not a symbol list embedded in application code.
4. **Given** an active node with no valid ETF or insufficient price history, **When** it is
   displayed, **Then** the node and its explicit gap remain visible; a parent-sector ETF,
   sample stock, or fabricated momentum is not substituted.
5. **Given** an unchanged activated release, **When** the user repeats navigation, **Then**
   validated catalog information is reused and valid selections are retained; activating a
   changed release clears only selections made invalid by that change.

---

### User Story 3 - Retain File-Based Review and Approval Governance (Priority: P2)

A reviewer collects local research, accepts or rejects exact candidate/node relationships,
and publishes reviewed ETF or membership changes through the file-based catalog workflow.
Research decisions, listing verification, suitability, source approval, and historical
provenance remain distinct and inspectable after the catalog database is removed.

**Why this priority**: Moving data into files must not turn locally declared tickers into
approved GICS representations or discard the auditability delivered by earlier features.

**Independent Test**: Collect controlled local evidence, retain an explicit review decision,
and publish one valid ETF mapping with its listing/source/date evidence. Verify invalid
promotion cannot publish data and later source changes retain the original approval history.

**Acceptance Scenarios**:

1. **Given** an optional research source is missing or contains unsupported declarations, **When**
   collection runs, **Then** its incomplete status is visible and successful research is retained,
   without treating research as authoritative catalog data or invalidating unrelated approved files.
2. **Given** an accepted candidate, **When** ETF publication is attempted, **Then** exact
   classification scope, verified regional listing, suitability, source approval, and the
   full effective period are checked; acceptance alone does not approve the mapping.
3. **Given** a previously approved mapping and retained local evidence, **When** supporting
   declarations change, disappear, or become unobservable, **Then** affected relationships are
   identified for re-review while earlier approvals and provenance remain available.
4. **Given** an explicit rejection or no suitable ETF, **When** coverage is reviewed, **Then**
   the gap remains visible for the existing explicit basket workflow or not-covered state;
   no older acceptance, parent ETF, or automatically generated basket is substituted.
5. **Given** a failed publication affecting both a mapping and its review/provenance records,
   **When** failure is reported, **Then** no partial publication or success-shaped approval remains.

---

### User Story 4 - Migrate and Retire Database/Hardcoded Catalog Paths (Priority: P3)

An administrator backs up the existing catalog and review history, exports a verifiable
file-based equivalent, and switches the application to manifest-managed sources.
Existing catalog database dependencies and embedded ETF/stock listings are removed from
all production paths, not merely bypassed in one screen.

**Why this priority**: The requested breaking change is incomplete if legacy paths can still
provide a second authority, silently restore static lists, or lose reviewed history.

**Independent Test**: Migrate a controlled legacy catalog containing listings, memberships,
ETF/basket approvals, and local research history. Compare all transferable identities, dates,
and provenance, then operate the affected workflows with the old database unavailable.
Any unreviewed or unmappable legacy data is explicitly quarantined rather than approved.

**Acceptance Scenarios**:

1. **Given** existing reviewed records and audit history, **When** migration/export is performed,
   **Then** each record is transferred with its identity and provenance or listed with an
   actionable reason preventing safe transfer; the original data is not deleted automatically.
2. **Given** a legacy static ETF map or provider-label industry catalog, **When** migration
   assesses it, **Then** it does not become reviewed GICS evidence merely by moving into a CSV.
3. **Given** a validated migrated release, **When** the old catalog database is absent, **Then**
   catalog browsing, review, research, and approval operate through files only, with no hidden
   database initialization, query, write, or fallback in those workflows.
4. **Given** retired database-only administration or configuration, **When** it is used, **Then**
   the administrator receives explicit migration instructions rather than a silently mixed
   file/database result or activation of an embedded listing.

### Edge Cases

- The existing sector ETF CSV identifies instruments but has blank Sector/Industry values:
  retain it as listing evidence, not an approved GICS crosswalk inferred from fund names.
- A regional stock references an absent industry, wrong region/classification version, or an
  inactive parent sector: reject the assignment rather than guessing a parent.
- A reviewed sub-industry references an industry whose sector differs from supplied redundant
  stock metadata: the hierarchy is authoritative and conflicting input is reported.
- A stock has multiple listings or changes industry over time: distinguish instrument identity,
  listing identity, and effective assignment periods without duplicating active membership.
- Multiple sources disagree on an ETF or stock assignment: retain alternatives for explicit
  review; manifest ordering or filenames are not approval authority.
- Required approved files are absent, edited after validation, empty contrary to declared
  coverage, or unreadable: report invalid/unavailable evidence, not a static or stale fallback.
- Optional research sources fail: mark research partial/failed without fabricating removal or
  treating their contents as approved representation data.
- A manifest references a disallowed path or unrelated credentials, private portfolios,
  watchlists, logs, or caches: reject the source and do not execute source projects.
- Publication is interrupted, or another writer publishes concurrently: expose one complete
  release or an explicit conflict/failure, never partially updated approval evidence.
- No reviewed complete GICS hierarchy is supplied: report the available scope and gaps rather
  than claiming complete market coverage from the stock or ETF files alone.
- Existing reviewed baskets are present: retain approvals/weights/history in file-based records
  and preserve their explicit no-substitution, exact-weight, and missing-history behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Catalog, hierarchy, representation, membership, local research, and approval/audit
  workflows addressed by this feature MUST use file-based records and MUST NOT require, query,
  initialize, or write the legacy catalog database after cutover.
- **FR-002**: A manifest MUST consolidate all sources used by these workflows, identifying each
  source's role, location, region/classification scope, version/content identity, provenance,
  approval or research status, effective coverage, and required/optional nature.
- **FR-003**: The system MUST retain CSV-based US GICS sector ETF representations and support
  the same reviewed file-based approach for industries and sub-industries. Instrument listings
  and exact node-to-ETF approvals MUST remain distinguishable.
- **FR-004**: There MUST be one stock catalog CSV per region, not separate stock files per
  industry. Each row MUST reference its exact industry and, when reviewed, sub-industry;
  the hierarchy MUST resolve the industry to its sector.
- **FR-005**: Stock rows MUST preserve instrument/listing identity, verified regional exchange
  and provider-symbol evidence, source/review evidence, and effective membership/listing periods.
  Multiple listings and historical assignments MUST NOT create conflicting simultaneous
  reviewed industry memberships for one instrument in the same scope.
  Explicit unresolved stocks MAY lack verified listings but MUST retain exact reviewed membership
  and unresolved status; they MUST NOT trigger market-data requests until listing verification succeeds.
- **FR-006**: Hierarchy and representation relationships MUST use stable reviewed identities
  with exact region and classification version. Parent relationships, effective dates, and
  optional sub-industry membership MUST be validated; names or similarity MUST NOT create aliases.
- **FR-007**: Required source availability, declared coverage, content identity, duplicate
  identities, conflicting intervals, and every cross-source reference MUST be validated before
  activation. Failures MUST identify source/row/reference context without exposing private content.
  Active sources that no longer match their registered identity MUST be reported as invalid or
  unavailable, not silently treated as the unchanged validated release.
- **FR-008**: Activation/publication MUST expose one consistent catalog release across sources,
  approvals, and provenance. Pre-commit failure or concurrent publication conflict MUST leave
  the prior active release unchanged and explicitly report failure. At/after the atomic commit,
  an acknowledgement or durability fault MUST report the verified publication state or explicit
  uncertainty and require reconciliation before retry; it MUST NOT claim an unverified rollback
  or expose a partial release.
- **FR-009**: All production ETF and stock listings, including benchmark instruments and
  experimental/legacy fallback lists, MUST come from registered file sources. Embedded runtime
  ticker catalogs and fallback paths MUST be removed/refactored, not retained as alternate authority.
- **FR-010**: Changing a valid reviewed file release MUST change filtering, representations,
  and requested instrument identities without application-code changes. Unchanged navigation
  MUST reuse validated catalog data; release changes MUST invalidate affected derived selections
  and results without clearing unrelated valid user state.
- **FR-011**: Every active reviewed sector, industry, and sub-industry in the selected scope MUST
  remain visible with its approved representation status and explicit gaps. Missing or invalid
  evidence MUST NOT be replaced by parent/sector data, sample listings, or fabricated returns.
- **FR-012**: Collection and review MUST remain read-only toward source projects, bounded to
  manifest-registered research inputs, local, and free of project execution or network requests.
  All retained occurrences, conflicts, original labels/scope, and resource outcomes MUST remain traceable.
- **FR-013**: Candidate acceptance/rejection MUST retain exact target, rationale, selected evidence,
  and review identity in durable file-based history. Research MUST NOT create verified listings,
  source approvals, hierarchy assignments, or runtime representations automatically.
- **FR-014**: ETF publication MUST preserve existing verified-listing, exact-scope, suitability,
  source/approval-reference, effective-period, and overlap checks, with mapping and supporting
  approval/review/provenance published together.
- **FR-015**: Unchanged recollection MUST create no duplicate evidence/review items. Changed,
  removed, newly conflicting, or unobservable support MUST identify all affected reviewed
  relationships for re-review while retaining prior approved evidence; incomplete inspection
  MUST NOT be reported as proof of removal.
- **FR-016**: Existing reviewed basket records and audit history MUST remain available after
  migration. Basket use MUST remain explicit and governed, with exactly 100% approved weights,
  no missing-constituent reweighting, and no fabricated traded-fund charts.
- **FR-017**: Migration MUST provide backup/export, validation/reconciliation, explicit cutover,
  and recovery guidance. Every legacy record MUST be accounted for as safely transferred or
  explicitly quarantined; unreviewed static mappings MUST NOT be auto-approved and original
  databases/source files MUST NOT be deleted automatically.
- **FR-018**: Legacy database-only catalog commands, settings, and production consumers MUST
  be refactored or explicitly retired with migration errors. No affected application mode
  MAY silently mix catalog database records, file releases, and embedded listings.
- **FR-019**: Existing market-data provider choice, request scoping, return calculations,
  effective-session handling, and valid user-facing workflows MUST be preserved except for
  documented catalog/storage and administration breaking changes.

### Key Entities *(include if feature involves data)*

- **Source Manifest**: The consolidated register of authoritative catalog files, retained
  governance records, and optional unreviewed research sources with their scope and identities.
- **Catalog Release**: One validated, consistently activated set of registered source versions.
- **Reviewed Classification Node**: A sector, industry, or sub-industry with exact region,
  classification/version identity, parent relationship, source approval, and effective period.
- **Regional Stock Record**: An instrument/listing and effective industry assignment in the
  region-wide stock CSV, optionally linked to a reviewed sub-industry.
- **ETF Listing Evidence**: The instrument, exchange, provider identity, source verification,
  and effective listing coverage; not an industry mapping by itself.
- **Reviewed ETF Representation**: An exact sector/industry/sub-industry relationship to verified
  ETF listing evidence, with suitability, approval, dates, and retained supporting provenance.
- **Research and Review History**: Immutable observations, original local declarations, manual
  decisions, selected evidence, and links to published approvals, retained as file-based records.
- **Reviewed Basket**: An existing explicit weighted stock representation with its constituent,
  approval, date, and history evidence retained through file-only migration.
- **Migration Reconciliation**: Accounting for every legacy record and its transferred identity
  or explicit reason for quarantine, without destroying the original source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A controlled release resolves 100% of valid stock-to-industry,
  industry-to-sector, sub-industry-to-industry, and representation-to-listing references;
  every deliberately invalid reference prevents activation with an actionable explanation.
- **SC-002**: A reviewer can publish a controlled stock reassignment and an approved ETF change
  without editing application code; 100% of affected filters and instrument requests reflect
  the newly activated release and unaffected valid selections remain intact.
- **SC-003**: 100% of active controlled hierarchy nodes appear with representation status,
  including nodes with no stocks or no suitable ETF; zero parent/sample substitutions occur.
- **SC-004**: The controlled regional dataset of 10,000 stock rows and 500 industry/sub-industry
  nodes becomes browsable within five seconds of initial local loading, and subsequent
  catalog-only filter changes complete within one second on the recorded reference environment,
  excluding remote market-data retrieval.
- **SC-005**: Across missing/invalid sources, conflicting scopes, incomplete review, invalid
  listings/dates, and interrupted publication, zero unapproved mappings or partial releases
  become active and the last explicitly activated release is not silently replaced.
- **SC-006**: Migration accounts for 100% of legacy reviewed and research records as transferred
  or explicitly quarantined; every transferred approval retains exact identity, effective
  dates, and provenance, and affected workflows function with the old catalog database unavailable.
- **SC-007**: A controlled scenario using only instruments absent from legacy embedded lists
  completes catalog browsing, review, and approval through registered sources. Every production
  catalog consumer has a file-based source or an explicit retirement/migration outcome.
- **SC-008**: Unchanged research adds zero duplicate evidence or manual reviews; source mutation
  identifies 100% of controlled affected review relationships without altering historical approvals.

## Assumptions

- **Clarification, 2026-10-31**: The user selected "Clarify FR-008 for atomic commit and uncertain
  acknowledgement": pre-commit failure preserves the old release; post-commit uncertainty requires
  explicit verification/reconciliation, not a claimed rollback.
- **Clarification, 2026-10-31**: The user selected "Remove SQLite from these workflows; use files
  for catalogs and retained review/audit history", rather than keeping it as a derived query store.
  This decision applies to catalog and reviewer workflows, not unrelated market-data storage.
- **Clarification, 2026-10-31**: The user requested "one file for all stocks per region, each row
  hold a reference to its industry, each industry holds a reference to its sector".
  This replaces the initial suggestion of separate stock-listing/membership files or per-node files.
- One regional file with stable hierarchy references is the selected simplification. Sector
  names need not be duplicated as authoritative stock-row data; hierarchy files can be reused
  for ETF coverage and stock filtering. Effective-dated rows may repeat a listing across
  non-overlapping assignment periods without becoming duplicate active membership.
- The initial ETF/classification scope is reviewed US GICS. The regional file boundary does not
  imply a new international taxonomy, provider, or expanded UI feature.
- The supplied [sector ETF CSV](../../.data/sector-etf-representations.csv) is preserved as an
  existing input, not rewritten by specification. Its blank Sector/Industry fields mean reviewed
  exact GICS references are still required before it can establish representation coverage.
- CSV files and a manifest are user-mandated artifacts, not a chosen application technology stack.
  Manifest serialization, exact column contracts, retained audit-file formats, and publication
  mechanics are resolved during planning; no database-backed catalog alternative is authorized.
- Existing reviews, local research, basket governance, classification licensing/source approvals,
  and provider terms remain applicable. A complete approved GICS hierarchy or suitable ETF for
  every node is not supplied automatically.
- Controlled test fixtures may contain test-only instruments and expected values, but must never
  serve as production catalog defaults, seeded approvals, or runtime fallback listings.
- Performance criteria cover local catalog handling on a documented reference environment,
  not live price retrieval; unchanged validated releases should be reused rather than repeatedly
  loaded on ordinary interactions.
- This invocation defines the breaking change only. Runtime refactoring, data export/cutover,
  and replacement of database-only commands occur during the later implementation workflow.
