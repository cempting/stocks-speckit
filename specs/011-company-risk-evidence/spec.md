# Feature Specification: Company Risk Evidence Scoreboard

**Feature Branch**: Unchanged; feature key `011-company-risk-evidence`

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description:
> the score board shall provide the information to analyse roughly the quailty, growth, cashflow propertees of a company. this data serves for the risk analysis and risk management, whether to invest or trade. Means when cash flow (major factor) is not given its a big warning sign.
> Besides that the companies business model, moat, and order book are of huge interest as well.
> - find sources to retrieve the information (xfinance, finviz, tradingview , wiki and other trustful online ressource)
> - fetch the information in a structure manner using mcp or curl or http, what ever serves the purpose
> - apply the information to the stockdata

**Amendment (2026-11-01)**:
> Specify sufficient independent issuer evidence without requiring fabricated IDs. Extend T004/T010/T011 with same-ticker/same-exchange successor-issuer, unresolved-profile and valid nullable-ID cases.

## Ownership and Dependencies

This remains a distinct company-risk/evidence feature after the 2026-11-02 consolidation.
[001](../001-market-leadership-screener/spec.md) owns component-score formulas,
[002](../002-fundamental-grading-layout/spec.md) owns the eight-slot matrix,
[006](../006-stock-table-columns/spec.md), incorporating 005, owns the comparison/Total Score,
and [004](../004-sector-stock-explorer/spec.md), incorporating 003, owns navigation.
Risk warnings and attributed business/moat/order evidence here neither redefine their calculations
nor add a root tab or mandatory stock-table column.

[012](../012-stock-industry-memberships/spec.md) separately refines verified issuer sharing,
nullable identities, listing-history continuity, per-request reuse and membership-context
boundaries. It preserves this feature's separately permitted research, provenance, source/cutoff,
and non-classification safeguards. Enrichment never approves or changes a membership, hierarchy,
representation, or classification version. [010](../010-manifest-csv-catalogs/spec.md) remains
catalog/publication authority. These scope clarifications do not claim migration or implementation
completion; see the [authority map](../README.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recognize Cash-Flow Risk and Evidence Gaps (Priority: P1)

An investor or trader opens a company's scoreboard to assess quality, growth, and cash generation.
Cash flow receives prominent attention: missing evidence must not be mistaken for satisfactory
cash generation, while reported zero or negative cash flow must be distinguishable from a data gap.

**Why this priority**: Positive growth or quality measures must not conceal that cash-generation
risk is unassessed or that the company reported cash consumption.

**Independent Test**: Present controlled companies with positive, zero, negative, missing,
unloaded, stale, and failed cash-flow evidence. Verify their warnings and explanations without
requiring business-model or backlog information.

**Acceptance Scenarios**:

1. **Given** cash-flow evidence has not been requested, **When** the scoreboard opens, **Then**
   it prominently states "Cash flow not assessed" and offers the existing explicit load action;
   it does not claim that the company has no cash flow.
2. **Given** operating or free-cash-flow evidence is missing, insufficient, incomparable, stale,
   or failed after retrieval, **When** the scoreboard appears, **Then** a high-priority cash-flow
   evidence warning identifies the affected measure, reason, period, and appropriate next action.
3. **Given** a reported zero operating cash flow, **When** risk evidence is displayed, **Then**
   the scoreboard identifies that no operating cash was generated in that period, not missing data.
4. **Given** reported negative operating cash flow or negative free cash flow, **When** the
   scoreboard appears, **Then** it highlights a cash-generation concern with the actual dated value
   and definition; negative free cash flow is not automatically described as insolvency.
5. **Given** valid quality/growth evidence but missing cash-flow evidence, **When** scores appear,
   **Then** independent valid evidence remains visible, the warning remains prominent, and no
   complete current risk assessment or imputed aggregate score is presented.

---

### User Story 2 - Inspect Structured Financial Evidence for the Correct Company (Priority: P1)

A user explicitly requests financial evidence for a stock and receives structured, dated
observations attached to that stock's verified company identity. The user can inspect underlying
values rather than rely on an unexplained score.

**Why this priority**: Risk analysis requires comparable evidence, provenance, and reliable
company matching, not an assortment of untraceable values copied from websites.

**Independent Test**: Load controlled financial evidence for two companies with similar names,
multiple listings, and different reporting periods. Verify identity, units, source links,
existing metrics, and cash-flow overview values. Include a successor issuer retaining its
predecessor's ticker/exchange, an unresolved source profile, and a verified issuer with no
catalog company identifier.

**Acceptance Scenarios**:

1. **Given** a verified stock/company association, **When** evidence is explicitly loaded,
   **Then** the scoreboard retains the existing Quality, Growth, and Cash Flow metric groups
   and adds an identifiable cash-flow overview with operating cash flow, capital expenditure,
   and free cash flow where comparable evidence exists.
2. **Given** quarterly, cumulative, annual, or restated observations, **When** values are
   displayed, **Then** their period basis, units, currency, and reported/derived status are clear;
   incompatible periods are not combined into a plausible-looking metric.
3. **Given** a missing free-cash-flow value and incomplete derivation inputs, **When** evidence
   is normalized, **Then** free cash flow remains unavailable; missing capital expenditure is
   never assumed to be zero.
4. **Given** ambiguous issuer identity, an unresolved listing, or a ticker change, **When**
   enrichment is requested, **Then** unmatched evidence is not attached to another company and
   an actionable identity limitation appears.
5. **Given** a financial source failure, **When** results are displayed, **Then** the error is
   explicit and no different provider or old successful result silently replaces it.
6. **Given** the selected financial source and separately permitted issuer research, **When**
   scores and disclosures appear together, **Then** scored numeric metrics retain their selected
   source and supplemental claims remain separately attributed rather than silently blended.
7. **Given** a successor issuer uses the predecessor's ticker and exchange but its returned
   issuer evidence conflicts with the dated reviewed association, **When** financial evidence
   is loaded or reused, **Then** the association is marked mismatched, no successor observations
   attach to the predecessor, and the user is directed to obtain a reviewed dated association.
8. **Given** ticker and exchange match but the returned profile is absent, failed, or lacks
   sufficient issuer evidence, **When** financial enrichment is requested, **Then** identity
   remains unresolved with an explicit reason and next action; observations are not attached
   or presented as verified company evidence.
9. **Given** a dated reviewed listing-to-issuer reference and returned issuer evidence
   corroborate the same issuer without conflict, while the catalog company identifier is
   missing, **When** financial evidence is loaded, **Then** permitted observations attach to
   the existing stock/listing association, the company identifier remains missing, and no
   regulator identifier or research authorization is invented.

---

### User Story 3 - Understand Business Model, Competitive Advantages, and Orders (Priority: P2)

A user examines concise company-specific information about how the business earns revenue,
reported competitive advantages, and customer order backlog. Every statement is source-linked
and distinguishes reported facts, management claims, and interpretation.

**Why this priority**: Financial ratios alone do not explain business durability or future demand,
but unsupported moat labels or invented order books would create false confidence.

**Independent Test**: Use controlled disclosures containing a business description, competitive
claims, a reported backlog, remaining performance obligations, and an issuer without comparable
order disclosures. Verify structured presentation and explicit gaps.

**Acceptance Scenarios**:

1. **Given** permitted business disclosures, **When** company research is loaded, **Then**
   the scoreboard summarizes principal products/services, revenue model, customers/markets,
   and disclosed operating segments, marking unsupported fields unavailable.
2. **Given** management claims about competitive advantages, **When** moat evidence appears,
   **Then** the claims are attributed and supporting evidence is linked; the company is not
   automatically rated as having a strong or durable moat.
3. **Given** an independently sourced interpretation, **When** it is displayed, **Then**
   it is labelled as opinion rather than verified issuer fact, with source and date.
4. **Given** backlog, bookings, or remaining performance obligations, **When** order evidence
   appears, **Then** each measure retains its own name, definition, period, units, and disclosed
   cancellation or coverage qualifications; the measures are not treated as interchangeable.
5. **Given** absent, inaccessible, conflicting, or non-comparable disclosures, **When** the
   research section appears, **Then** the limitation remains visible instead of fabricated
   backlog, an inferred zero, or an unsupported moat conclusion.

---

### User Story 4 - Evaluate Sources and Refresh Evidence Safely (Priority: P2)

A reviewer evaluates candidate information sources, approves permitted uses, and lets users
refresh company evidence explicitly. Users can follow citations and distinguish fresh evidence
from earlier observations without changing reviewed stock identity or market classifications.

**Why this priority**: Accessible content is not automatically trustworthy, current, reusable,
or permitted for automated risk analysis.

**Independent Test**: Provide approved, unapproved, blocked, stale, and conflicting source cases.
Verify source assessment, retrieval boundaries, explicit refresh, provenance, and stock association.

**Acceptance Scenarios**:

1. **Given** a candidate source, **When** it is assessed, **Then** its ownership, information
   coverage, authority, access restrictions, attribution/reuse requirements, and approval status
   are documented before automated collection or display.
2. **Given** a source whose permitted use is unknown or incompatible, **When** retrieval is
   requested, **Then** it is not used automatically; the user receives an actionable limitation
   and an appropriate reference link where permitted.
3. **Given** unchanged current evidence, **When** the user navigates normally, **Then** valid
   results and selections are reused without repeated retrieval or unwanted loading.
4. **Given** an explicit refresh or amended disclosure, **When** new evidence is collected,
   **Then** its source/date are distinguishable from retained earlier evidence and affected
   warnings/results are updated without overwriting historical provenance.
5. **Given** two sources disagree, **When** their claims are inspected, **Then** both remain
   distinguishable with dates and definitions; source order or name similarity does not silently
   determine which claim is true.
6. **Given** a selected company's explicit research request, **When** collection occurs, **Then**
   only necessary public identifiers are transmitted, private portfolio/watchlist data is excluded,
   unrelated companies are not enriched, and reviewed catalog membership remains unchanged.
7. **Given** a company's evidence and warnings, **When** the assessment is displayed, **Then**
   it supports human interpretation without buy/sell instructions, order placement, position
   management, or personal allocation recommendations.

### Edge Cases

- Cash-flow evidence is unloaded, absent, non-finite, failed, stale, zero, or negative:
  retain distinct states and never substitute zero for absence.
- A financial business or other issuer lacks comparable conventional cash-flow ratios:
  explain the comparability limitation without claiming distress or inventing replacement ratios.
- Quarterly cash-flow reporting is cumulative, a fiscal year differs from the calendar year,
  or a filing is amended: preserve period basis and availability dates.
- Reporting currency, scale, or capital-expenditure sign conventions differ:
  retain the original meaning and disclose any justified normalization.
- Cash flow is positive but older than the requested assessment context:
  it is not silently presented as current evidence.
- Multiple share classes, ADRs, renamed issuers, or recycled tickers exist:
  verify issuer association rather than joining on ticker/name alone.
- A successor retains the same ticker and exchange: conflicting issuer evidence blocks
  attachment even when listing labels match; predecessor captures cannot become successor evidence.
- A source profile lacks issuer-specific evidence or fails: matching ticker/exchange is
  insufficient, and previously verified evidence cannot silently satisfy the failed current check.
- Company and regulator identifiers are missing but reviewed issuer-domain evidence is
  corroborated: financial attachment may succeed without inventing either identifier.
- Backlog is zero, not disclosed, cancellable, sector-inapplicable, or not comparable with
  remaining performance obligations: retain those distinctions.
- Promotional management language, analyst opinion, or community-edited text describes a moat:
  label its origin and do not convert it into a verified rating.
- A publisher blocks access, rate-limits requests, or changes permitted use:
  report the limitation without bypassing restrictions or silently switching sources.
- A selected stock has no eligible verified listing:
  retain the unresolved state without guessed external requests.
- Enrichment would change active catalog membership or require exposing private portfolio data:
  do not perform it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The existing stock scoreboard/detail and per-company grading presentation MUST
  provide Quality, Growth, and Cash Flow evidence for the selected company without a new root
  workflow or additional mandatory columns in the simplified stock/industry tables.
- **FR-002**: The existing eight metric slots, available history, missing-data disclosures,
  peer-score rules, and all-three-components aggregate rule MUST remain intact. Cash-flow
  importance MUST be expressed through risk visibility, not an unrequested score-weight change.
- **FR-003**: The company view MUST present operating cash flow, capital expenditure, and free
  cash flow when available, identifying reporting period, basis, currency, scale, source,
  and whether each value is reported or derived.
- **FR-004**: Cash flow MUST distinguish not loaded, available, insufficient, unavailable,
  not comparable, stale, and error states. Zero and negative reported values MUST remain numeric
  observations, not missing-data states.
- **FR-005**: A prominent cash-flow warning MUST appear before the score summaries when cash
  flow is unassessed or operating/free-cash-flow evidence cannot support the requested assessment.
  It MUST identify the reason and next action without asserting that missing evidence proves
  financial weakness.
- **FR-006**: Zero or negative operating cash flow and negative free cash flow MUST produce a
  dated cash-generation concern distinct from an evidence-gap warning. Positive growth/quality
  measures MUST NOT conceal either warning or imply that the company is safe to invest in.
- **FR-007**: Financial observations MUST be collected into named, reusable company-evidence
  fields, not only free-form text. Derived measures MUST retain definitions and compatible
  inputs; missing values, incompatible periods, or unknown units MUST NOT be silently imputed.
- **FR-008**: Every displayed financial observation and qualitative claim MUST retain an
  attributable source, original reporting/document date when available, retrieval date,
  applicable period, and a reference permitting inspection of its evidence.
- **FR-009**: Enrichment MUST attach to a verified issuer/instrument/listing association and
  preserve stable catalog identity. Missing company identifiers MUST remain missing until
  verified; ambiguous ticker/name matches MUST NOT attach another company's information.
  Financial verification MUST require both an eligible dated reviewed listing and at least
  one independently reviewed, dated listing-to-issuer reference whose issuer-specific evidence
  is corroborated by the returned source profile. Sufficient corroboration is agreement on a
  regulator-issued issuer identifier, or agreement on an independently verified issuer-controlled
  domain; either route MUST be documented and free of conflicting issuer evidence. Ticker,
  exchange, company name, currency, and a reference derived only from those same labels are
  not sufficient issuer evidence. A conflicting issuer discriminator or documented successor
  outside the reviewed association's effective period MUST produce a mismatch; an absent,
  failed, or inconclusive profile or missing reviewed issuer reference MUST remain unresolved.
  Neither outcome may attach or present the affected observations as verified company evidence.
  This rule MUST apply to newly loaded, cached, and retained evidence against the applicable
  dated association. A verified domain-based case MUST remain eligible with missing company
  and regulator identifiers; verification MUST NOT fabricate identifiers, mutate catalog
  identity, or implicitly authorize separately governed issuer research.
- **FR-010**: The company view MUST include structured business-model fields for principal
  products/services, revenue model, customers/markets, and operating segments where disclosed,
  with explicit unavailable/not-disclosed states where appropriate.
- **FR-011**: Moat information MUST describe attributed competitive-advantage evidence and
  distinguish reported facts, management claims, and independent opinions. It MUST NOT invent
  a moat rating or treat promotional claims as independently verified competitive durability.
- **FR-012**: Order information MUST identify backlog, bookings, and remaining performance
  obligations separately where disclosed, retaining definitions, dates, units, scope, and
  material qualifications. Unavailable or non-comparable evidence MUST NOT become zero or
  an estimated order book.
- **FR-013**: Candidate sources MUST have a documented assessment of coverage, authority,
  structured availability, access restrictions, attribution, permitted retention/display,
  and approval status. Accessibility alone MUST NOT authorize automated reuse.
- **FR-014**: Numeric financial scoring MUST continue to use the application's single selected
  financial source. Separately approved issuer/regulator disclosures MAY supplement cited
  company research, but MUST NOT become silent financial-provider pooling or override scored
  observations from another source.
- **FR-015**: Automated collection MUST use only approved sources and permitted access methods,
  respect source limits, and avoid access-control circumvention, unapproved paid services,
  copying restricted prose, or unauthorized redistribution.
- **FR-016**: Collection MUST be explicit and limited to the requested verified companies;
  existing complete-cohort peer-score loading remains the justified exception. Ordinary table
  rendering/navigation MUST NOT enrich the full market universe or trigger qualitative research.
- **FR-017**: Repeated ordinary navigation MUST reuse current valid evidence and preserve valid
  private selections. Explicit refresh MUST update affected evidence and warning states while
  preserving earlier provenance; failures MUST remain observable, not successful stale fallbacks.
- **FR-018**: Conflicting, stale, blocked, incomplete, or unobservable research MUST retain its
  limitation and source context. "Not disclosed" MUST require an identified inspected disclosure
  scope; failed access MUST NOT be presented as proof that information does not exist.
- **FR-019**: Attached company evidence MUST NOT alter reviewed regional stock membership,
  classification, listing approvals, or active catalog source files merely because new company
  information was retrieved.
- **FR-020**: Retrieval and diagnostics MUST NOT disclose credentials, private portfolios,
  watchlists, account balances, or unrelated personal data. Only the public company identifiers
  and request information needed by an approved source MAY be transmitted.
- **FR-021**: The feature MUST support human company-risk assessment, not issue buy/sell
  instructions, place orders, manage positions, calculate personal portfolio allocations,
  or claim that a score establishes investment suitability.

### Key Entities *(include if feature involves data)*

- **Company Association**: Verified relationship between an issuer and existing stable stock/
  listing identities, with independent reviewed issuer evidence, corroborating source-profile
  evidence and effective context; nullable identifiers are not guessed.
- **Financial Observation**: Named financial fact or derived measure with value/state,
  period basis, units/currency, definition, inputs where relevant, and source provenance.
- **Cash-Flow Warning**: Evidence-gap or cash-generation concern with affected measures,
  dated reason, prominence, and an appropriate next action.
- **Company Research Claim**: Business-model, competitive-advantage, or order-related information,
  its fact/management-claim/opinion status, definition, source, and applicable date.
- **Source Assessment**: Coverage, trust role, permitted access/reuse, approval state,
  restrictions, and review evidence for a candidate information source.
- **Company Evidence Snapshot**: Dated observations, claims, limitations, and warnings attached
  to the correct company, distinguishable from previous observations without catalog mutation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In controlled unloaded, missing, failed, stale, incomparable, zero, and negative
  cash-flow cases, 100% display the required distinct state and warning; zero missing values
  appear as numeric zero or evidence of healthy cash generation.
- **SC-002**: In representative complete and incomplete company cases, at least four of five
  test users can identify whether cash flow is assessed and the principal warning within ten
  seconds of opening the company view.
- **SC-003**: 100% of displayed controlled observations and claims identify their source,
  dates/period, evidence status, and inspection reference; incomplete provenance is explicitly
  identified rather than fabricated.
- **SC-004**: Controlled similar-name, multiple-listing, ticker-change, same-ticker/same-exchange
  successor-issuer, and unresolved-profile cases produce zero cross-company or unresolved
  attachments and zero guessed requests for unverified listings. In 100% of controlled
  permitted domain-corroborated nullable-ID cases, observations attach to the correct existing
  stock/listing while missing company/regulator identifiers remain missing.
- **SC-005**: Controlled business-model, moat, backlog, and remaining-obligation cases retain
  100% of the required source/definition distinctions, with zero invented moat ratings,
  estimated undisclosed order books, or substitutions for absent evidence.
- **SC-006**: In controlled source denial, restriction, failure, refresh, and conflict cases,
  zero unauthorized collections, silent provider substitutions, provenance overwrites, or
  active catalog mutations occur.
- **SC-007**: After valid evidence is loaded, ordinary local navigation redisplays the company
  assessment within one second in the recorded reference environment, with zero additional
  company-research retrievals unless refresh or a changed company/evidence context requires them.
- **SC-008**: Existing controlled stock/industry navigation, all eight metric slots, peer-score
  and aggregate calculations, explicit score loading, and missing-data scenarios retain 100%
  of their established behavior apart from the specified additional company-risk presentation.

## Assumptions

- Initial scope is verified companies associated with the existing reviewed US stock catalog.
  International taxonomy expansion and mass enrichment of the full regional universe are excluded.
- Reviewers supply dated listing-to-issuer evidence independently of returned ticker/exchange
  labels. Verification uses an available regulator identifier or verified issuer-controlled
  domain, not a mandatory new identifier. Missing review evidence blocks enrichment pending
  review; discovering or approving new issuer bindings automatically is out of scope.
- "Scoreboard" means existing per-stock score/detail and company-grading surfaces, not restoration
  of an independent legacy weekly-scoreboard route or addition of another root tab.
- "Order book" means customer orders/commercial backlog, not exchange order depth.
- "Cash flow is a major factor" means prominent warnings and inspectable evidence. Existing
  equal-weight score mathematics remains unchanged unless a later requirement explicitly changes it.
- The user's "xfinance" is interpreted as the existing Yahoo Finance financial source. Listing
  a candidate source does not approve it or require all candidates to feed the same financial metric.
- Free cash flow is not assumed to be a uniform reported accounting line. Its reported or derived
  definition must be visible, and operating cash flow alone does not imply positive free cash flow.
- Issuer disclosures can be authoritative evidence of what management reported without proving
  management's moat claims. No proprietary analyst rating or automated unsourced inference is required.
- Source-access and display/reuse review is an implementation prerequisite, not approval granted
  by this specification. Public availability does not remove attribution or licensing obligations.
- This command defines requirements and evaluates source candidates only; it does not fetch
  company datasets, enrich production stock records, activate a catalog, or implement collection.

### Candidate Source Assessment

Research reviewed on **2026-11-01**. The following is a shortlist, not a runtime source approval
or a guarantee of coverage. Specific company disclosures must be verified during collection.

| Candidate | Potential information | Trust and access decision |
|-----------|-----------------------|---------------------------|
| [Yahoo Finance through the existing source](https://github.com/ranaroussi/yfinance) | Existing financial statements, cash-flow observations, and company profile information | Maintain the selected financial-source boundary. The source tool states it is unofficial and directs users to Yahoo's data-use terms; its software license does not grant data redistribution rights. |
| [SEC EDGAR and disclosed company facts](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Filed financial evidence and links to issuer reports; annual/quarterly disclosures can support business, competition, and contract research | Prioritize attributable issuer disclosures for supplementary research. Structured facts do not guarantee uniform free-cash-flow or backlog coverage. Direct documentation access returned 403 during this review; no access restriction was bypassed and deployment access must be verified. |
| Issuer annual reports and investor-relations disclosures | Business model, operating segments, risks, competitive claims, and disclosed backlog/remaining obligations | Prefer original dated disclosures. Management claims remain attributed claims; verify issuer identity, document context, and permitted reuse rather than copying report prose. |
| [Finviz](https://finviz.com/) | Screening/reference metrics and discovery of related public material | Reference candidate only at this stage. The attempted terms-document retrieval did not succeed, so automated access, retention, and redistribution are not approved by this assessment. |
| [TradingView terms](https://www.tradingview.com/policies/) | Human-readable financial/research context | Reference-only by default. Its published terms restrict non-display processing and risk-management uses; do not import its content for automated risk calculations without separately established permission. |
| [Wikipedia/Wikimedia documentation](https://www.mediawiki.org/wiki/API:REST_API) | Company background and pointers to original sources | Community-edited context, not financial or moat authority. Documented structured access is available, but identity verification, attribution, and applicable [content reuse terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) still apply. |

Technical access choices requested by the user remain planning decisions, not requirements
to scrape every candidate or bypass denied access. No source guarantees that a company discloses
an order book or that competitive durability can be determined automatically.
