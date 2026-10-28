<!--
Sync Impact Report
- Version change: 1.1.0 -> 2.0.0
- Modified principles:
	- IV. Simple Streamlit-First Architecture: allow a single-file app OR a simple three-step
	  st.tabs layout; remove the mandatory Market/Sector/Industry tab sequence
- Modified constraints: one free on-demand data provider, reusable st.cache_data requests,
  session-local sector/industry/stock-list state, and preserved engineering safeguards
- Added sections: none
- Removed sections: none
- Follow-up: existing plans/tasks and application navigation must be reconciled in a separate
  specification/planning workflow; this amendment does not implement application changes
- Follow-up TODO placeholders: none
- Review note: remove this temporary Sync Impact Report before committing the amendment
-->
# stocks-speckit Constitution

## Core Principles

### I. Deliberate Design Before Code
Every change MUST begin with an explicit problem statement, acceptance criteria, and identification
of the owning component. Non-trivial changes MUST describe data flow, interfaces, dependencies, and
failure modes before implementation. Design decisions MUST be grounded in requirements, repository
evidence, or measured behavior; speculative "vibe coding" and unverified assumptions are prohibited.
The depth of design documentation MAY scale with risk, but the reasoning MUST remain reviewable.

### II. Small, Cohesive Units
Code MUST be organized into small units with one clear responsibility and explicit inputs, outputs,
and side effects. Functions, classes, and modules MUST remain independently understandable and
testable. Boundaries MUST follow domain responsibilities rather than arbitrary file size or reuse
predictions. A unit that requires unrelated setup, broad state, or many reasons to change MUST be
split or accompanied by a documented justification.

### III. Tests Are Required Evidence
Behavior changes MUST be specified by automated tests that fail for the missing or defective
behavior before implementation, then pass after the change. Tests MUST cover normal behavior,
meaningful edge cases, and failure paths at the lowest effective level. Integration tests MUST
protect contracts across module, persistence, service, or external-system boundaries. A change MUST
NOT merge with failing required checks, reduced relevant coverage, or skipped tests without an
approved, documented exception and follow-up plan.

### IV. Simple Streamlit-First Architecture
The Market Leadership Screening app MUST use Python and Streamlit. Its primary user experience
MUST use either a simple single-file app or a simple three-step progressive layout using `st.tabs`.
Tabs do not require one source file: small helper functions or cohesive Python modules MAY support
either option when they keep data access, calculations, and rendering independently testable.
Additional page-routing layers, backend services, provider frameworks, or a separate frontend MUST
NOT be introduced without a documented requirement and an approved architecture exception.
Simplicity is measured by the user journey and necessary responsibilities, not by forcing all logic
into one large function.

### V. Maintainability Is a Feature
Code MUST communicate intent through precise names, straightforward control flow, explicit types
or contracts, and minimal hidden state. Duplication MUST be removed when it represents shared
knowledge; similar-looking code with distinct responsibilities MUST remain separate. Public
behavior and non-obvious decisions MUST be documented near their source. Refactoring MUST preserve
behavior with tests, and each change MUST leave the touched area no harder to understand, test, or
modify.

## Application and Data Constraints

- The application MUST use Python and Streamlit for Market Leadership Screening. UI work MUST
  follow the single-file or three-step `st.tabs` architecture; tab labels and feature scope are
  specified in the feature requirements, not inferred from this constitution.
- Market data MUST be fetched on the fly using `yfinance` or a single free financial API selected
  for the application. A deployment MUST use only that selected source for runtime market-data
  requests; silent provider switching,
  multi-provider pooling, or unapproved paid data sources are prohibited. Provider terms and
  permitted display/derived-data rights MUST be reviewed before results are published or hosted.
- Remote market-data responses MUST use `st.cache_data` with keys that identify the provider,
  symbols, date range, and relevant request parameters. Cache lifetime and freshness MUST be
  explicit and compatible with provider limits. Refresh MUST bypass or invalidate only the relevant
  cached request; failures MUST NOT be cached as successful data or hidden by stale success-shaped
  fallbacks.
  Reusable data fetches and expensive deterministic transformations MUST be cached so ordinary
  widget reruns reuse valid data rather than repeat API calls. Cached responses MUST NOT contain
  user-specific selections or credentials in returned values.
- User selections for markets, sectors, industries, and any stock list MUST use namespaced,
  session-local `st.session_state` keys and stable identifiers. Valid selections MUST survive
  ordinary reruns; changing a parent or evidence mode MUST clear only dependent invalid selections.
  Session state MUST NOT be used as shared cross-user data storage.
- API requests MUST be limited to the data needed for the active view and MUST respect provider
  rate limits. Missing, stale, unauthorized, or incomplete data MUST be identified rather than
  silently substituted.
- Dependencies MUST be pinned or constrained, with a documented purpose. External services,
  clocks, and filesystem access MUST be isolated sufficiently for deterministic tests; this does
  not require a separate service or adapter framework.
- Errors MUST preserve actionable context and remain observable without exposing credentials or
  sensitive data. Optimizations beyond the required caching MUST be justified by measurements.
- Backward-incompatible interface or data changes MUST document migration guidance and versioning
  impact. Existing feature plans MUST be reconciled with this constitution before further
  implementation; updating governance alone does not migrate the application.

## Development Workflow and Quality Gates

1. Define the requirement, acceptance criteria, affected contracts, and smallest viable change.
2. Record design decisions for non-trivial work, including rejected alternatives and tradeoffs.
3. Add or update tests first and confirm they detect the absent or defective behavior.
4. Implement in small, reviewable increments while preserving clear ownership boundaries.
5. Run the relevant unit and integration suites, then run the full test suite when practical.
6. Review the diff for unnecessary complexity, undocumented behavior, dead code, and scope creep.

Every review MUST verify constitution compliance. Reviewers MUST reject changes whose behavior
cannot be explained, whose tests do not demonstrate the claimed result, or whose complexity is
unsupported by a present requirement. Any approved exception MUST identify its owner, rationale,
expiry condition, and remediation issue.

## Governance

This constitution governs all project development practices and supersedes conflicting local
guidance. Amendments MUST be proposed in writing with rationale, affected principles, migration
impact, and a semantic version bump. Approval requires explicit maintainer review and recorded
acceptance before the amendment takes effect.

Constitution versions follow semantic versioning: MAJOR for incompatible governance changes or
removed principles, MINOR for new principles or materially expanded guidance, and PATCH for
clarifications that do not change obligations. Compliance MUST be reviewed for every change and
during release readiness. Periodic architecture reviews MUST identify unjustified complexity,
oversized units, test gaps, and expired exceptions. Violations MUST be corrected before merge unless
an exception meeting the workflow requirements above is approved.

**Version**: 2.0.0 | **Ratified**: 2026-10-26 | **Last Amended**: 2026-10-28
