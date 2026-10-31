# Feature Specification: Local ETF Mapping Discovery

**Feature Branch**: `main` (unchanged; no branch-creation hook configured)

**Created**: 2026-10-31

**Status**: Draft

**Updated**: 2026-10-31 (file-only research and review alignment)

**Input**: User description: "take in local resources to identify etf ticker for industries mappings:
- ~/Documents/learn/invest_screener/sector_rotation
- ~/Claude/Projects/SectorStockScreener/Analyzer
- ~/Claude/Projects/SectorStockScreener/stockviewer
- ~/Claude/Projects/SectorStockScreener/stockfinder"

## Catalog and Research Authority

The [feature 010 specification](../010-manifest-csv-catalogs/spec.md) makes the manifest the
consolidated source register for catalog files and optional local research inputs. The four
user-supplied roots below are an initial documented research roster, not embedded approved
ETF catalogs or independently authoritative runtime defaults. Their corrected locations and
selected catalogs must be explicitly registered.

Collection observations, immutable evidence, exact review decisions, and approval provenance
persist in files; the implemented schema 3 tables/CLI contracts remain pre-cutover migration
evidence. Optional research failure remains explicit and does not invalidate unrelated complete
approved catalog sources. Examples of candidate tickers are research examples, never production seeds.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect Local ETF Mapping Evidence (Priority: P1)

A research reviewer gathers existing industry-to-ETF declarations from the four specified local
projects into one reviewable candidate inventory instead of manually comparing separate catalogs.
Each candidate preserves its original classification label, ticker, stated scope, and source location.

**Why this priority**: The local projects already contain useful research leads. Collecting them
with provenance reduces repeated research without claiming that their mappings are accurate.

**Independent Test**: Inspect controlled local resources containing explicit mapping catalogs,
duplicate declarations, and one missing directory. Every supported declaration is represented
with provenance, and the missing resource is reported without losing other candidates.

**Acceptance Scenarios**:

1. **Given** readable local catalogs with explicit industry-to-ticker declarations, **When** a
   reviewer collects candidates, **Then** each declaration is retained with its source project,
   file, precise location, original label, ticker, and any stated regional/classification scope.
2. **Given** the same label and ticker appear in multiple places, **When** candidates are grouped,
   **Then** one candidate retains every supporting occurrence rather than losing provenance.
3. **Given** a resource is missing, unreadable, or contains unsupported mapping content, **When**
   collection finishes, **Then** the reviewer sees its status and actionable reason alongside
   successful results; an incomplete inspection is not reported as complete.
4. **Given** project code contains mapping declarations and unrelated executable behavior,
   **When** evidence is collected, **Then** only mapping evidence is read, with no project execution,
   network requests, or modification of the source projects.
5. **Given** optional research roots registered in the manifest and no catalog database, **When**
   collection runs with one missing root, **Then** file-based evidence retains successful
   occurrences, collection reports partial status, and unrelated approved catalog data is unchanged.

---

### User Story 2 - Reconcile Candidates Against Reviewed Classifications (Priority: P2)

A reviewer compares local candidate labels with the active reviewed industry/sub-industry
hierarchy, identifies conflicting ETF choices, and distinguishes precise candidates from broad
sector, thematic, commodity, index, or otherwise unqualified proxies.

**Why this priority**: The source catalogs mix classification schemes and proxy scopes. A shared
name or a locally declared ticker must not become a misleading classification representation.

**Independent Test**: Present two different ETF candidates for one classification, an unmatched
provider label, and an industry declaration pointing to a known sector ETF. All alternatives and
qualification issues remain visible; none is silently selected or approved.

**Acceptance Scenarios**:

1. **Given** one source associates Semiconductors with SOXX and another with SMH, **When** the
   reviewer reconciles that label to a reviewed node, **Then** both alternatives and their
   supporting sources are visible, with no winner chosen by file or project order.
2. **Given** a provider label differs from a reviewed classification label, **When** reconciliation
   is attempted, **Then** the original label is preserved and exact node binding requires an
   existing reviewed equivalence or a new explicit reviewer decision.
3. **Given** an industry declaration points to a known broad-sector ETF or a non-ETF instrument,
   **When** it is assessed, **Then** its declared use and qualification issue are visible, and it
   is not treated as a suitable industry ETF merely because it appeared in an industry catalog.
4. **Given** an active reviewed hierarchy includes nodes with no matching local evidence, **When**
   the reviewer views coverage, **Then** every such node remains visible as having no candidate;
   a candidate alone does not change approved coverage.

---

### User Story 3 - Promote Reviewed Evidence Through Existing Approval (Priority: P3)

A reviewer selects a suitable local candidate, records the exact classification identity and
suitability decision, and prepares it for the existing reviewed ETF approval workflow. Local
discovery does not bypass verified listings, source approval, or effective dates.

**Why this priority**: Discovery delivers value only if reviewed evidence can be used by the
representation tools without weakening their existing governance.

**Independent Test**: Select a candidate for a verified regional ETF listing, retain its local
provenance, and approve it through the existing workflow. A second candidate missing listing,
approval, scope, or date evidence cannot become an active representation.

**Acceptance Scenarios**:

1. **Given** a reviewer accepts a candidate's suitability for an exact node, **When** the mapping
   is prepared for approval, **Then** it retains region, classification, node, verified listing,
   source evidence, approval reference, effective dates, and the local evidence supporting it.
2. **Given** a candidate lacks required approval evidence or a verified active listing, **When**
   promotion is attempted, **Then** the missing prerequisites are identified and no active
   mapping, verified listing, or approval is fabricated.
3. **Given** an ETF mapping or basket is already approved, **When** local candidates are collected
   again, **Then** the existing representation is unchanged until an explicit valid approval
   decision is made.
4. **Given** a previously reviewed source declaration changes or disappears, **When** collection
   is repeated, **Then** changed evidence is identified for re-review without silently replacing
   the existing approval or losing the evidence supporting that approval.
5. **Given** an accepted candidate and all normal approval prerequisites, **When** file-based
   publication fails or encounters a concurrent change, **Then** neither a partial mapping nor
   a dangling approval-provenance link becomes active.

### Edge Cases

- An explicitly requested root is absent, inaccessible, or contains no mapping catalog: distinguish
  those outcomes and report partial inspection rather than inventing candidates.
- Every root fails: report collection failure with per-resource reasons, not a successful empty
  inventory. Readable catalogs with no relevant declarations may legitimately yield no candidates.
- Repeated labels occur within one catalog, including contradictory duplicate declarations:
  retain all occurrences and expose different ticker choices rather than silently overwriting them.
- Labels differ in whitespace, case, punctuation, or taxonomy: preserve originals; display grouping
  does not constitute reviewed classification equivalence.
- A ticker has an exchange suffix, represents an index, is obsolete, or has unknown instrument type:
  preserve its identity and require reviewed instrument/listing evidence before ETF approval.
- A source declares a different region or no region: do not inherit the reviewer's target region
  silently. Unknown scope remains unresolved until explicitly reviewed.
- Several classifications reference the same ETF: each exact classification mapping requires its
  own reviewed suitability and effective scope; approval does not propagate to related nodes.
- A source contains credentials, private portfolios/watchlists, generated logs, bulk price caches,
  or unrelated project files: exclude those contents from candidate collection and reports.
- A candidate is rejected or no suitable ETF exists: retain the gap for the existing basket review
  workflow or explicit not-covered state; do not generate a basket or parent-sector substitute.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support the four user-specified local resource roots as initial
  manifest-registered optional research sources. A reviewer MUST explicitly register corrected
  locations and selected catalogs; no hidden alternate root or runtime ticker catalog is invented.
- **FR-002**: Collection MUST inspect supported explicit classification-label-to-ticker catalogs
  and accompanying mapping metadata. Arbitrary program outputs, unrelated stock universes, and
  inferred mappings from fund names alone are outside this feature's scope.
- **FR-003**: Each candidate MUST preserve its original label and ticker, source project/file and
  precise declaration location, declared mapping level/type, stated region/classification when
  available, observation date, and source revision or content identity. Missing metadata MUST be
  represented as unknown, not inferred approval.
- **FR-004**: Collection MUST be read-only, local, and limited to the specified resources. It MUST
  NOT execute another project, initiate remote requests, modify its files, or collect credentials,
  private portfolio/watchlist content, generated logs, or bulk price caches.
- **FR-005**: Collection MUST report each requested resource as inspected, inspected with issues,
  missing, inaccessible, or unsupported, with counts of declarations and actionable issue reasons.
  Overall results MUST distinguish complete, partial, and failed collection.
- **FR-006**: Identical candidates MAY be grouped only when their declared label, ticker, and
  scope agree; every contributing occurrence MUST remain traceable. Different ticker choices or
  conflicting scope MUST remain separate, regardless of source order.
- **FR-007**: Reconciliation MUST use exact reviewed region, classification, and node identities.
  Provider labels and other taxonomies MUST remain distinguishable from GICS. An alias or label
  equivalence MUST require an existing reviewed equivalence or an explicit new reviewer decision.
- **FR-008**: For the selected active reviewed hierarchy, the reviewer MUST see every industry
  and sub-industry with its existing representation status and local candidate state: no candidate,
  needs classification reconciliation, needs suitability review, conflicting evidence, or
  reviewer accepted/rejected. Candidate discovery MUST NOT count as approved representation coverage.
- **FR-009**: Candidate assessment MUST expose known broad-sector, thematic, commodity, index,
  regional, and instrument-identity qualification issues. Local declarations or cross-project
  agreement MUST NOT establish suitability, ETF identity, listing verification, or source approval.
- **FR-010**: Reviewers MUST be able to record acceptance or rejection for an exact candidate/node
  relationship, including the decision reason and evidence reviewed. Conflicting choices MUST
  remain unresolved until an explicit reviewer selection.
- **FR-011**: An accepted candidate MUST be usable by the existing ETF approval workflow only
  after exact scope, a verified regional listing, reviewed source/approval evidence, suitability,
  and effective dates satisfy that workflow. Supporting local provenance MUST remain attached
  or durably referenced; source discovery MUST NOT auto-approve mappings or create verified listings.
- **FR-012**: Repeated collection of unchanged resources MUST produce the same candidate identities,
  grouping, and provenance without duplicate review items. Changed or removed supporting evidence
  MUST be identifiable for re-review while preserving earlier approved evidence.
- **FR-013**: Collection and candidate review MUST leave existing approved ETFs, baskets, hierarchy
  memberships, and momentum unchanged. Only the existing explicit approval workflow may alter
  representations; no parent-sector substitution or automatic basket construction is permitted.
- **FR-014**: Collection/reconciliation/review MUST use manifest-registered inputs and durable
  file-based histories without legacy catalog database access. Approval MUST publish a mapping
  and its provenance coherently after normal listing/source/suitability/scope/date checks.
  Missing optional research MUST be reported separately from required catalog-source failure.
- **FR-015**: Migration MUST retain or explicitly quarantine every collection run, evidence
  occurrence, run/evidence relationship, exact manual decision, selected-evidence link, and
  representation-provenance link with its identity and ordering. Research-only persistence
  MUST NOT implicitly activate or alter approved membership/representation evidence.

### Key Entities *(include if feature involves data)*

- **Local Resource Inspection**: A requested source root, inspection outcome, declaration counts,
  observation identity, and any issues limiting completeness.
- **Mapping Evidence Occurrence**: One explicit local label/ticker declaration with its source
  location, original text values, declared scope, and source observation identity.
- **ETF Mapping Candidate**: A reviewable label/ticker/scope combination supported by one or more
  evidence occurrences; discovery is not an approval state.
- **Classification Reconciliation**: An explicit reviewed relationship between a source label and
  an exact region/classification/industry or sub-industry node.
- **Candidate Review Decision**: Acceptance or rejection for an exact candidate/node relationship,
  with suitability rationale and retained supporting evidence.
- **Approved ETF Representation**: The existing governed mapping that may consume accepted evidence
  only after all listing, source, approval, and effective-date prerequisites are satisfied.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four requested resource roots appear in the inspection summary with an explicit
  outcome; no unavailable or partially inspected source is presented as completely inspected.
- **SC-002**: In a controlled collection containing supported explicit mapping catalogs, 100% of
  relevant declarations are recoverable from the candidate inventory with their original labels,
  tickers, and precise source locations, including repeated and conflicting declarations.
- **SC-003**: 100% of active reviewed industries/sub-industries in the selected scope have a
  candidate state and approved representation status, including nodes with no local candidate.
- **SC-004**: Across conflicting candidates, unknown scope, unmatched labels, broad-sector proxies,
  non-ETF instruments, and missing approval evidence, zero mappings become active automatically.
- **SC-005**: Every approved mapping derived from local discovery is traceable to an exact reviewed
  node, verified listing, effective period, review decision, and retained local supporting evidence.
- **SC-006**: Repeating unchanged collection produces zero additional duplicate candidate/review
  items; changing or removing evidence identifies every affected reviewed relationship without
  silently altering an approved representation.
- **SC-007**: A reviewer can complete candidate collection, conflict comparison, and preparation
  of one valid ETF approval using the consolidated evidence without manually searching each
  source project again.
- **SC-008**: With the legacy catalog database unavailable, controlled collection/review/approval
  scenarios retain 100% of evidence identities, explicit decisions, and provenance links.
  Partial research yields zero automatic approvals, failed publication yields zero partial links,
  and migration accounts for every legacy research/review record.

## Assumptions

- This feature extends the reviewed industry representation workflow from feature 008; feature
  007's exact classification identity and no-substitution rules remain applicable.
- US industry/sub-industry review is the initial use case. Other explicitly declared regional
  evidence may be retained as research, but it is not automatically applied to US nodes.
- The four initial roots are exactly those supplied in the user input. Missing resources are
  recoverable inspection issues, not permission to search unrelated directories.
- Local catalogs supply research leads, not verified issuer holdings, current listing evidence,
  effective dates, source approvals, or a complete GICS hierarchy.
- Initial inspection found explicit industry catalogs in
  `sector_rotation/src/constants.py`, `Analyzer/config.py`, and
  `stockfinder/src/stockfinder/data.py`. They contain provider-label mappings and broad proxies,
  with concrete alternatives such as SOXX versus SMH and IBB versus XBI. These observations
  describe unreviewed source evidence, not accepted mappings.
- The supplied `stockviewer` root was unavailable during specification. Its intended place in
  the resource set is retained; no substitute project or missing catalog contents are assumed.
- The supported collection boundary is explicit mapping catalogs and their accompanying metadata,
  not unrestricted project analysis or automatic extraction from arbitrary narrative documents.
- Reviewer-led suitability research may still be necessary. Online research, provider changes,
  runtime market-data retrieval, new discovery UI layouts, and automatic mapping approval are
  outside this feature.
