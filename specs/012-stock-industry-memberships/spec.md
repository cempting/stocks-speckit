# Feature Specification: Stock Identity and Industry Membership Revision

**Feature Branch**: `main` (unchanged; no feature branch created)

**Feature Directory**: `specs/012-stock-industry-memberships`

**Created**: 2026-11-01

**Last Refined**: 2026-11-02

**Status**: Draft

**Input**: User description:

1. Define company-level financial/business/moat evidence separately from stock
   instruments and listing-specific price/volume histories; preserve nullable
   identifiers without guessing them.
2. Reuse membership identity for dated stock-to-industry associations with
   classification scope and review provenance; decide classification versus
   business-exposure membership first.
3. Define industry nesting, parent ownership, inherited sectors, cycle prevention,
   and permitted depth.
4. Deduplicate parent/sector stock lists, reuse company facts, and contextualize
   peer scores by industry and date.
5. Bound the mapping revision, require migration design and test-first coverage
   for overlap, nested filtering, historical reassignment, duplicate listings,
   and stable navigation; enrichment must not change classifications automatically.

**Clarifications confirmed on 2026-11-01**:

- Membership meaning: replace the current single-assignment model with one custom
  multi-industry scheme. This is not a separate canonical/exposure overlay and
  must not be presented as official GICS classification.
- Nesting: support multiple nested industry levels, with at most one industry
  parent per industry. Do not restrict the model to industry plus one sub-industry
  level.

## Ownership and Consolidation Boundary

This remains the active, distinct identity/membership revision after the 2026-11-02 application
consolidation; the active feature pointer and existing design/task artifacts remain unchanged.
[010](../010-manifest-csv-catalogs/spec.md) owns manifest publication and file-only lifecycle;
this feature owns the reviewed version boundary, issuer/instrument/listing identity, custom
membership/hierarchy, descendant deduplication, peer context and within-Discovery lookup.

The merged owners are [004](../004-sector-stock-explorer/spec.md) for Discovery/navigation
(including former 003), [006](../006-stock-table-columns/spec.md) for the five-column stock
comparison/Total Score (including former 005), and
[008](../008-industry-representation-tools/spec.md) for exact ETF/basket representation
(including former 007). [001](../001-market-leadership-screener/spec.md) retains component-score
formulas, [002](../002-fundamental-grading-layout/spec.md) the raw financial matrix,
[009](../009-local-etf-discovery/spec.md) candidate collection, and
[011](../011-company-risk-evidence/spec.md) company-risk/evidence safeguards.
None of those dependencies broadens this revision or makes its migration complete.
See the [authority map](../README.md).

## Clarifications

### Session 2026-11-01

- Q: How should users open a stock that has no active industry membership? → A: Stock lookup within existing Discovery, including retained identified unassigned stocks; listing and issuer-evidence verification rules still apply.
- Q: Should migration keep existing reviewed industry assignments when their meaning is unchanged, or require every assignment to be reviewed again? → A: Preserve compatible existing assignments and original approval provenance through an explicitly reviewed migration; separately review changed or new assignments.

### Session 2026-11-02

- Acquisition accounting is per unchanged, still-valid issuer/evidence request, not
  a ban on explicitly loading previously unrequested peers in a different cohort.
  Whole-universe prefetch is not an acceptable way to satisfy reuse.
- Stored business-model and moat evidence must be reusable across independently
  verified share classes with separate research permissions, provenance and
  historical cutoffs. Financial approval grants no research access; new collectors
  remain out of scope.
- Permissible price/volume observation periods follow reviewed listing and issuer
  continuity, not industry membership. Exclude predecessor observations after ticker
  reuse and explain unverifiable periods; separate request identities alone do not
  establish observation ownership.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand a stock without conflating its identities (Priority: P1)

As a stock researcher, I want to see which company a stock represents, which
listing supplies its chart, and which reviewed industries it belongs to, so that
business evidence and tradable price histories are not confused.

**Why this priority**: Correct ownership is necessary before either shared company
facts or overlapping classifications can be trusted.

**Independent Test**: Open stock details for two share classes with a reviewed
common issuer, an instrument with two listings, and a stock with an unresolved
company identifier. Verify ownership, evidence attribution, and explicit missing
states without requiring any hierarchy changes. Include permitted stored business/
moat claims, denied/revoked research access, historical cutoffs and returned price/
volume observations spanning a reused ticker's issuer transition.

**Acceptance Scenarios**:

1. **Given** two distinct share-class instruments with independently verified
   associations to a reviewed common issuer and eligible stored business-model and
   moat claims, **When** I explicitly load their evidence, **Then** they reuse
   eligible company financial and stored qualitative evidence with original
   provenance, while retaining distinct instrument identities. Research access
   requires its own valid permissions; financial approval alone, denied/revoked
   research access or a capture after the requested historical day's end must not
   authorize the affected claims.
2. **Given** one instrument with two independently reviewed exchange listings,
   **When** I view a selected listing, **Then** its symbol, exchange, trading
   currency, price history, and trading volume belong to that listing and are not
   combined with the other listing. If a provider's returned history spans ticker
   reuse, only observations within reviewed continuity for the selected listing
   and issuer are shown; predecessor observations are excluded and unverifiable
   periods are explained as unavailable, independently of membership dates.
3. **Given** eligible reviewed issuer evidence with a nullable company identifier,
   **When** I inspect the stock, **Then** the identifier stays null, the reviewed
   association and provenance remain visible, and a name or ticker alone does not
   establish an issuer match.
4. **Given** a retained identified instrument without an active industry membership,
   **When** I look it up within Discovery and open its details, **Then** the correct
   instrument is accessible, membership and industry comparisons are explicitly
   unassigned/unavailable, and eligible listing history and company evidence remain
   available independently of classification.
5. **Given** a retained identified instrument without a usable reviewed listing,
   **When** I look it up within Discovery, **Then** its details remain accessible,
   price unavailability is explained, and no unverified listing is requested.

---

### User Story 2 - Review overlapping memberships and nested industries (Priority: P1)

As a classification reviewer, I want to assign a stock to multiple industries in
one custom scheme and organize industries into a deeper hierarchy, so that the
scheme represents reviewed business activities rather than forcing one label.

**Why this priority**: This is the requested cardinality and hierarchy change;
automatic enrichment must not become classification authority.

**Independent Test**: Review a candidate containing simultaneous memberships,
three nested industry levels, an effective-date boundary, and invalid parent
relationships. Verify valid assignments and explicit rejection of invalid ones.

**Acceptance Scenarios**:

1. **Given** independently reviewed associations with two industries in the same
   custom classification scope, **When** both associations are effective on the
   requested date, **Then** the stock belongs to both, including when those
   industries belong to different sectors.
2. **Given** three nested industry levels in one sector, **When** the hierarchy is
   reviewed, **Then** each child has one parent and the same inherited sector;
   the third industry level is accepted.
3. **Given** a proposed second parent, cycle, missing parent, cross-sector parent,
   or child period extending beyond its parent, **When** the candidate is
   validated, **Then** activation is blocked with the affected identities and reason.
4. **Given** an old membership ending on one date and a new membership starting the
   next day, **When** I inspect either date, **Then** only the applicable association
   is active and the original review history remains available.
5. **Given** newly collected company evidence suggesting another business activity,
   **When** enrichment is refreshed, **Then** no membership, hierarchy relationship,
   review state, or classification version changes without a separate review.

---

### User Story 3 - Browse deduplicated stocks and contextual peer evidence (Priority: P2)

As a stock researcher, I want an industry's descendants and a sector's industries
to roll up into consistent stock lists, while keeping comparative results specific
to the industry I selected.

**Why this priority**: Overlap is useful only if it does not duplicate stocks,
inflate cohorts, or make a score's comparison group ambiguous.

**Independent Test**: Browse a controlled hierarchy with direct and descendant
memberships, a stock in two sibling industries, multiple listings, and two share
classes of one company. Compare exact stock sets and peer-context labels.

**Acceptance Scenarios**:

1. **Given** an industry with a direct member and members in a child and grandchild,
   **When** I open its stock list, **Then** the list includes the union of all three
   sets and each instrument appears once.
2. **Given** one stock assigned to two sibling industries,
   **When** I open their common parent or sector, **Then** the stock appears once;
   opening either sibling still includes it.
3. **Given** two listings of one instrument and two instruments of one company,
   **When** I open a rollup, **Then** the first instrument appears once and the two
   distinct share classes remain two stocks; listing count is not stock count.
4. **Given** a stock belonging to industries with different eligible peers,
   **When** I change the selected industry, **Then** comparative results identify
   the selected industry, classification version, effective date, and eligible
   cohort; neither result overwrites or averages the other.
5. **Given** overlapping but different industry cohorts and already acquired
   company evidence that remains eligible, **When** I move from industry A to B
   and back to A, **Then** each unchanged issuer/evidence request is reused with
   zero repeat acquisition and comparative results retain the appropriate context.
   Previously unrequested peers may load only through explicit loading for the
   active view; switching context alone does not collect their evidence. No
   whole-universe prefetch is performed to manufacture the reuse result.
6. **Given** a sector rollup without one selected industry comparison context,
   **When** I inspect a stock's comparative evidence, **Then** no arbitrary
   industry score is selected; the missing comparison context is explained.
7. **Given** unchanged source evidence, instrument membership set, listing, and
   comparison rules, **When** only the catalog representation is migrated,
   **Then** metric and aggregate results, mandatory stock-table columns, root
   workflows, and listing charts match the prior baseline.

---

### User Story 4 - Adopt the revised mapping without losing history or navigation (Priority: P2)

As a catalog maintainer, I want a reviewed, versioned migration with a complete
reconciliation, so that existing identities, prior approvals, and valid stock
selections survive adoption of the new custom scheme.

**Why this priority**: A new data model must not silently reclassify existing stocks
or invalidate unrelated evidence and navigation.

**Independent Test**: Reconcile a prior reviewed release into a candidate custom
release, activate a valid candidate, reject an invalid candidate, and explicitly
restore the prior release. Check stock identity, history, and selection outcomes.

**Acceptance Scenarios**:

1. **Given** a prior release with industry and optional sub-industry assignments,
   **When** the migration is reviewed, **Then** every original record has an explicit
   disposition, original identities and provenance are traceable, and no extra
   membership or issuer identity is inferred; migration guidance identifies the
   version boundary, affected contracts, and unchanged behavior.
2. **Given** an invalid or unapproved candidate,
   **When** adoption is attempted, **Then** activation fails visibly and the
   previously selected release is unchanged.
3. **Given** a valid new custom release and a selected stock/listing whose identities
   remain valid, **When** adoption or an ordinary navigation rerun occurs, **Then**
   those selections survive; only industry, date, or listing selections that are
   no longer applicable are cleared with an explanation.
4. **Given** a reviewed reassignment or industry reparenting,
   **When** I inspect the retained prior release and its date, **Then** its original
   memberships, hierarchy, and peer context are reproduced rather than rewritten.
5. **Given** an explicitly requested restoration of a valid prior reviewed release,
   **When** restoration succeeds, **Then** its original membership results return
   and dependent selections are revalidated; restoration is not a silent fallback.
6. **Given** an existing ETF or basket approval for an exact historical node and
   scope, **When** the custom scheme changes that scope or node meaning, **Then**
   the approval is retained historically but does not automatically authorize a
   representation for the changed scope.
7. **Given** an existing eligible reviewed assignment with unchanged identity and
   meaning, and another assignment whose meaning changes without a new review,
   **When** the migration is reviewed, **Then** the unchanged assignment can be
   carried forward with original approval lineage and documented compatibility,
   while the changed assignment remains non-operational until separately reviewed.

### Edge Cases

- A stock has several direct memberships, including both an ancestor and its child:
  preserve the separately reviewed assertions, but include the stock only once in
  a rollup. Ancestor inclusion never invents a direct ancestor membership.
- Compatible assertions with different review sources remain traceable; conflicting
  uses of the same logical membership identity block activation.
- Membership dates are inclusive. An end date is inactive from the following day;
  different industries may legitimately overlap on the same day.
- A hierarchy branch is deeper than three industry levels: depth alone is not an
  error. Multiple parents, cycles, unresolved references, and invalid periods are.
- A child has no direct stocks or an industry is empty: retain the reviewed node;
  report its direct membership and descendant coverage without inventing members.
- A provider reuses a ticker for another issuer: do not attach the predecessor's
  company evidence or listing history without a separately reviewed dated identity.
  A response containing both issuers' observations must be bounded by reviewed
  listing/issuer continuity before display or calculation; current listing
  eligibility or separate request identities alone do not validate earlier dates.
- A stock's membership starts after its reviewed listing history or expires before
  it: do not trim otherwise eligible history to the membership interval.
- Stored business/moat claims have valid financial approval but missing, denied,
  expired or revoked research permission: block affected claim attachment, including
  previously loaded claims, without suppressing independently eligible financials.
- A historical qualitative capture is later than the requested UTC day's end:
  exclude it rather than treating currently known claims as historical evidence.
- Industry B contains uncached peers not present in A: require explicit loading
  before acquisition, while reusing valid requests shared by A and B. Returning to
  A does not repeat still-valid requests or trigger unrelated prefetch.
- Company identifiers are blank across many stock records: do not collapse companies
  by blank values, similar names, or matching tickers.
- A stock has no effective verified primary listing: retain its classification
  membership, explain chart unavailability, and do not silently choose another listing.
- A historical date is outside retained classification or evidence coverage: report
  unavailable context rather than substituting current memberships or company facts.
- A selected stock remains valid but its selected membership expires: preserve the
  instrument selection where applicable and clear the invalid comparison context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The model MUST distinguish company/issuer, stock instrument, and
  exchange listing. Company financial statements and quality, growth, cash-flow,
  business-model, and moat evidence belong to the company; memberships belong to
  the instrument; tradable symbols, trading currencies, and price/volume histories
  belong to the listing.
- **FR-002**: Company evidence MUST be reused across instruments only through an
  eligible, independently reviewed, dated issuer association. Existing attribution,
  units, reporting basis, freshness, permission, and missing-evidence rules remain
  applicable. Ticker, exchange, or name matching alone MUST NOT establish ownership.
  Stored business-model and moat claims MUST support reuse across independently
  verified share classes with original provenance and separately authorized research
  access. Financial approval MUST NOT authorize research. Current permissions,
  including denial/revocation, MUST be checked on reuse; historical claims MUST be
  captured no later than the requested UTC day's end. This does not require new
  qualitative collectors.
- **FR-003**: Stable company, instrument, listing, and membership identities MUST
  remain distinct. Nullable company and listing identifiers MUST remain nullable
  unless supported by reviewed identity evidence; blank identifiers MUST NOT be
  treated as a common issuer identity.
- **FR-004**: Listing-specific price and trading-volume observations MUST retain
  listing identity and dates. Multiple listings MUST NOT have their histories
  merged or silently substituted. Existing verified-listing eligibility and
  explicit unavailable-data behavior MUST be preserved.
  Every displayed or calculation-eligible observation MUST fall within reviewed
  continuity for the selected listing and issuer, intersected with the requested
  history window, not the membership interval. Returned predecessor observations
  after ticker reuse MUST be excluded; periods without verifiable continuity MUST
  remain explicitly unavailable. Separate request identities or a valid listing
  on the selected date alone MUST NOT authorize the entire returned lookback.
- **FR-005**: The revised operational classification MUST be one explicitly named,
  reviewed, versioned custom multi-industry scheme, replacing single-assignment
  behavior within the selected regional scope. It MUST NOT claim official GICS
  authority or create a second canonical/exposure overlay. Prior scopes and versions
  MUST remain historically distinguishable.
- **FR-006**: An identified stock instrument MUST be allowed concurrent reviewed
  memberships in multiple industries within that custom scope, including across
  sectors. Membership MUST be an explicit dated association with a stable logical
  identity, exact instrument and industry, region, classification identity/version,
  inclusive start and optional end dates, source, review state, and approval reference.
- **FR-007**: The existing logical membership identity concept MUST be retained.
  Listing copies of an assertion MUST NOT become distinct memberships. Compatible
  independently sourced assertions MAY coexist without multiplying stocks;
  contradictory assertion fields under one membership identity MUST block activation.
- **FR-008**: An industry MUST have at most one industry parent and support multiple
  nested levels without a fixed one-child-level limit. Root industries MUST belong
  to one sector; descendants MUST inherit that same sector. Parents and sectors
  MUST resolve within the identical regional classification scope.
- **FR-009**: Self-parenting, cycles, multiple parents, missing references,
  cross-sector parents, conflicting hierarchy periods, and child periods not covered
  by their ancestors MUST block activation with actionable identity-specific errors.
- **FR-010**: Membership and hierarchy changes MUST be dated and separately reviewed.
  Queries MUST use the selected classification version and effective date, and
  memberships MUST be valid within the effective periods of their target hierarchy.
  Historical reassignment and reparenting MUST NOT rewrite a retained prior release.
- **FR-011**: An industry's stock list MUST be the union of its direct effective
  members and all effective descendant members. A sector's list MUST be the union
  of the effective members of all its industries at every depth.
- **FR-012**: Each such list and peer cohort MUST contain an eligible instrument at
  most once, regardless of memberships, assertion provenance, descendant paths, or
  listing rows. Distinct share classes MUST remain distinct instruments. This
  revision MUST NOT introduce company-level stock-count aggregation.
- **FR-013**: Stock details MUST identify all effective direct industry memberships
  and their ancestor/sector paths in the selected scope and date, distinguishing
  approved direct membership from inherited rollup inclusion. Custom classification
  meaning and coverage limitations MUST be visible.
- **FR-014**: Comparative peer results MUST retain the instrument, exact selected
  industry, regional classification/version, membership date, financial observation
  basis, and eligible cohort identity. Cohorts MUST follow the same descendant and
  instrument-deduplication rules while preserving existing peer eligibility rules.
- **FR-015**: Raw eligible company facts MUST be reusable across industry contexts;
  peer scores MUST be separately contextualized. Membership overlap MUST NOT average
  scores across industries, arbitrarily choose a score for a sector, or change
  existing metric formulas, component requirements, or aggregate weighting.
  Context-only switches MUST NOT repeat unchanged, still-valid issuer/evidence
  requests. Acquisition for previously unrequested peers MUST require explicit
  loading for the active view. Whole-universe prefetch MUST NOT be used to satisfy
  the reuse requirement.
- **FR-016**: Missing membership or industry comparison context MUST make the
  affected membership/peer evidence explicitly unavailable without suppressing
  independently eligible listing history or company evidence. An insufficient
  eligible cohort, unresolved listing, or unavailable historical evidence MUST
  produce an explicit unavailable state for the affected evidence rather than an
  inferred classification, invented score, fabricated history, or successful-looking
  fallback.
- **FR-017**: Company enrichment MUST NOT create, remove, approve, redate, or reparent
  memberships or industries, nor select a different classification version.
  Classification changes MUST require their own review provenance.
- **FR-018**: Adoption MUST use a reviewed candidate and an explicitly versioned
  compatibility boundary. Migration guidance MUST identify affected membership,
  hierarchy, filtering, peer-context, and navigation contracts and distinguish
  changed behavior from unchanged listing and company-evidence behavior.
- **FR-019**: Migration reconciliation MUST account for every original record as
  preserved, explicitly transformed, retained historical, or unresolved with a
  reason. Existing stable identities MUST be retained where identity is unchanged;
  transformed associations MUST retain original scoped identities and approval
  lineage. No stock, listing, membership, or review history may disappear silently.
- **FR-020**: Legacy industry/sub-industry paths MUST remain traceable without
  assigning unreviewed additional industries, inventing company identifiers, or
  interpreting provider labels or ETF holdings as authoritative new classifications.
  Empty and unassigned retained records MUST remain explicitly distinguishable
  from reviewed operational membership.
  Existing reviewed assignments with unchanged identity and meaning MUST be eligible
  for carry-forward through an explicitly reviewed migration without mandatory
  individual re-review, provided their periods, source permissions, and approvals
  remain valid. Migration review MUST document compatibility and retain original
  approval lineage. Changed or new assignments MUST be separately reviewed before
  becoming operational; unreviewed records MUST NOT gain approval through migration.
- **FR-021**: Prior reviewed releases MUST remain reproducible. Invalid or unapproved
  candidates MUST NOT change the selected release. Explicit restoration MUST
  revalidate the requested prior release and dependent selections; silent rollback
  or silent use of altered active data is prohibited.
- **FR-022**: Existing ETF/basket approvals MUST retain their exact approved node,
  scope, period, and provenance. A changed custom classification MUST require
  explicit reviewed applicability before using a representation in its new scope.
  Membership overlap or nesting MUST NOT authorize parent substitution, an ETF,
  a basket, or a direct index automatically.
- **FR-023**: Existing Discovery and stock-detail navigation MUST use stable scoped
  identities. Ordinary reruns and compatible release changes MUST preserve valid
  selections and clear only dependent invalid selections, explaining the reason.
  Industry names or file order MUST NOT select replacement stocks or classifications.
  Discovery MUST allow lookup and detail access for retained identified instruments
  in the selected release and region, including those without active memberships.
  Lookup MUST resolve the instrument explicitly and MUST NOT invent memberships,
  establish issuer ownership, or authorize an unverified listing request.
- **FR-024**: The revision MUST preserve existing root workflows, mandatory stock
  table columns, market-data source choices, chart behavior, and approved calculation
  rules except for the explicitly specified membership, hierarchy, rollup,
  peer-context, and within-Discovery stock-lookup changes.

### Key Entities *(include if feature involves data)*

- **Company / Issuer**: Owner of financial and attributed business/moat evidence.
  Its identifier may be null; shared evidence requires a reviewed issuer association,
  not a guessed grouping.
- **Stock Instrument**: An equity security representing a company. Has a stable
  instrument identity, zero or more reviewed industry memberships, and zero or more
  separately identified listings. Different share classes are different instruments.
- **Exchange Listing**: A dated tradable manifestation of an instrument, with
  reviewed symbol, exchange, currency, source, eligibility, and listing-specific
  price/volume observations.
- **Issuer Association**: Independently reviewed, dated evidence linking an
  instrument/listing to an issuer and establishing which company evidence is eligible.
- **Custom Classification Scope**: Named regional scheme and immutable reviewed
  version with explicit meaning, effective dates, coverage, source, and approval.
- **Sector**: A reviewed root grouping within a classification scope; owns root
  industries and the inherited sector identity of their descendants.
- **Industry**: Reviewed, dated grouping with at most one industry parent.
  Existing sub-industry designations remain traceable, but do not impose a fixed
  nesting depth or establish an official external classification rank.
- **Industry Membership**: Explicit reviewed association between one instrument and
  one industry in one scope and period, with logical membership identity and provenance.
- **Peer Comparison Context**: Selected industry and its eligible deduplicated
  instrument cohort, classification/version, effective date, observation basis,
  and applicable unchanged comparison rules.
- **Catalog Release and Migration Reconciliation**: Retained approved snapshot and
  reviewed accounting of how original records relate to a candidate revised release.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the controlled identity cases, 100% of company evidence is attached
  only through eligible reviewed issuer associations; zero identifiers are guessed,
  and zero listing histories are combined across listings or successor issuers.
  Both independently verified share classes reuse eligible stored business-model
  and moat claims with original provenance; 100% of financial-only permission,
  denied/revoked research and post-cutoff capture cases block the affected claims.
  Zero returned predecessor observations appear in successor charts or calculations;
  unverifiable periods are explicitly unavailable and membership-only date changes
  do not remove otherwise eligible history.
- **SC-002**: A stock with at least two simultaneous reviewed memberships in one
  custom scope appears in both industry lists, including a cross-sector case.
  All tested dates return exactly the applicable reviewed associations.
- **SC-003**: Hierarchies with three and four nested industry levels are accepted;
  100% of the enumerated invalid-parent, cycle, scope, and period cases are blocked
  with an explanation before activation.
- **SC-004**: For every controlled parent, industry, and sector case, the visible
  stock set exactly equals the expected effective descendant union, with zero
  duplicate instruments. Two listings count as one stock; two share classes count
  as two stocks.
- **SC-005**: In 100% of the two-industry and historical comparison cases, users can
  identify the industry, classification version, effective date, and eligible cohort
  for each peer result; zero results are pooled across industries or shown with an
  arbitrary industry context.
- **SC-006**: Migration reconciliation accounts for 100% of original records and
  preserves traceability to every original membership and approval. Rejected
  candidates leave the selected release unchanged in all failure cases.
- **SC-007**: Valid instrument/listing selections survive 100% of the ordinary-rerun
  and compatible-cutover cases. Every invalid dependent selection is cleared with
  an explanation, without clearing unrelated valid selections. In 100% of the
  controlled unassigned-stock and unusable-listing lookup cases, users can open the
  correct instrument details without fabricating membership or bypassing evidence
  eligibility.
- **SC-008**: Retained historical releases reproduce the expected membership and
  hierarchy sets in 100% of reassignment, reparenting, and explicit-restoration cases.
  Enrichment-only refreshes cause zero classification or approval changes.
- **SC-009**: In A-to-B-to-A cases with overlapping but different cohorts, each
  unchanged, still-valid issuer/evidence request incurs zero repeat acquisitions
  while the appropriate peer context is re-evaluated. Validity includes the reviewed
  issuer association, requested evidence, applicable date, source permissions and
  freshness. Previously unrequested peers incur zero acquisitions before explicit
  loading for the active view; after that action, necessary new requests are allowed
  and counted separately from repeat requests. Zero unrelated whole-universe
  prefetch acquisitions are used to satisfy this criterion.

## Assumptions

- The stock instrument is the foundational classification and navigation identity;
  this does not merge company, instrument, and exchange-listing ownership.
- The user's confirmed choice is one custom multi-industry scheme, not official
  GICS and not two parallel canonical/exposure views. Custom memberships describe
  reviewed business activities; overlap does not establish revenue weights,
  pure-play status, exact index membership, or ETF suitability.
- Multiple industry parents are out of scope. A single-parent hierarchy may have
  deeper nesting; no configurable depth limit or generic multiple-parent network
  is requested.
- Date intervals retain the current inclusive-date convention. Current and historical
  views require an explicitly resolved scope/date; unavailable historical coverage
  is not filled from current data.
- Company facts are not issuer-deduplicated stock cohorts. The selected industry's
  eligible instrument cohort remains the comparison unit, using existing eligibility
  and financial comparison rules.
- Existing source permissions, reviewed listing gates, publication safeguards,
  and file-backed catalog authority from
  [feature 010](../010-manifest-csv-catalogs/spec.md) remain applicable except where
  this specification explicitly changes membership cardinality and hierarchy.
- Company evidence depends on the separately specified identity, acquisition,
  attribution, and reuse safeguards in
  [feature 011](../011-company-risk-evidence/spec.md). This revision does not claim
  that feature 011 is implemented or use enrichment work as a migration mechanism.
  Stored qualitative reuse requires the shared reviewed-claim types, permission
  checks and historical selection boundary, not new disclosure acquisition.
- Listing-history continuity uses reviewed dated listing/issuer identity evidence;
  it neither requires a financial load nor grants financial/research access.
  Industry membership is not proof of listing inception or issuer continuity.
- Subsequent planning must reconcile the affected feature 010 contracts, provide
  migration/version-impact design, and generate test-first tasks covering all
  acceptance cases, especially overlap, deeper filtering, historical reassignment,
  duplicate listings, stable navigation, and invalid activation. This specification
  does not generate the implementation plan or task list.
- Delivery follows the [constitution](../../.specify/memory/constitution.md):
  acceptance tests must first detect absent or defective behavior before the
  corresponding behavior is implemented. Checklist completion means specification
  quality, not completed migration or application validation.
- Out of scope: automatic taxonomy inference or bulk reclassification, company
  enrichment acquisition expansion, new market-data providers, direct-index support,
  new ETF research or approval, exposure-weighted portfolio analytics, a new root
  stock-browser workflow, and a replacement persistence system.
