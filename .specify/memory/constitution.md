<!--
Sync Impact Report
- Version change: 2.0.0 -> 3.0.0
- Modified principles:
  - I. Deliberate Design Before Code -> I. Keep It Simple
  - II. Small, Cohesive Units -> II. Lean Delivery
  - III. Tests Are Required Evidence -> retained as a workflow quality gate
  - IV. Simple Streamlit-First Architecture -> retained as an application constraint
  - V. Maintainability Is a Feature -> V. Separation of Concerns
- Added principles:
  - III. YAGNI
  - IV. Avoid Waste
  - VI. High Cohesion, Low Coupling
- Removed sections: none
- Follow-up TODO placeholders: none
- Review note: remove this temporary Sync Impact Report before committing the amendment
-->
# stocks-speckit Constitution

## Core Principles

### I. Keep It Simple
Every solution MUST use the simplest design that satisfies the current, verified requirement.
Changes MUST minimize concepts, control flow, dependencies, configuration, and operational
burden. Complexity is permitted only when a documented present requirement, measured constraint,
or security obligation cannot be met more simply. Simplicity keeps behavior understandable,
testable, and maintainable.

### II. Lean Delivery
Changes MUST deliver a small, complete, and reviewable unit of user or operational value. Work
MUST limit scope to the accepted requirement and MUST avoid speculative abstractions, broad
refactors, and unrelated cleanup. Designs and implementation MUST favor short feedback loops and
the smallest viable set of dependencies, data, and infrastructure.

### III. YAGNI
The project MUST NOT add functionality, extension points, configuration, abstractions, or
optimizations for anticipated future needs. A capability MAY be added only when it serves a
current documented requirement or a demonstrated constraint. Existing code MUST be extended
instead of generalized unless the present use cases prove that generalization is necessary.

### IV. Avoid Waste
Development and runtime behavior MUST avoid unnecessary work, duplication, data transfer,
resource consumption, and manual repetition. Caching, automation, and reuse MUST be introduced
only when they reduce an identified cost without obscuring ownership or correctness. Data requests,
computations, and tests MUST be limited to what the active requirement needs.

### V. Separation of Concerns
Each component MUST have a clear responsibility and explicit inputs, outputs, and side effects.
User interface rendering, market-data retrieval, domain calculations, state management, and
configuration MUST remain distinct concerns. A change that mixes unrelated concerns MUST be split
or have a documented, approved exception. This separation makes changes independently
understandable and testable.

### VI. High Cohesion, Low Coupling
Code within a module, class, or function MUST serve one closely related purpose. Components MUST
depend on stable, narrow contracts rather than another component's internal state, broad mutable
state, or incidental implementation details. Dependencies MUST flow through explicit boundaries;
cycles and hidden cross-component coupling are prohibited unless a documented exception explains
why no simpler boundary is viable.

## Application and Data Constraints

- The application MUST use Python and Streamlit for Market Leadership Screening. UI work MUST
  follow the single-file or three-step `st.tabs` architecture; tab labels and feature scope are
  specified in feature requirements, not inferred from this constitution.
- Market data MUST be fetched on the fly using `yfinance` or a single free financial API selected
  for the application. A deployment MUST use only that selected source for runtime market-data
  requests; silent provider switching, multi-provider pooling, and unapproved paid data sources
  are prohibited. Provider terms and permitted display and derived-data rights MUST be reviewed
  before results are published or hosted.
- Remote market-data responses MUST use `st.cache_data` with keys that identify the provider,
  symbols, date range, and relevant request parameters. Cache lifetime and freshness MUST be
  explicit and compatible with provider limits. Refresh MUST bypass or invalidate only the
  relevant cached request; failures MUST NOT be cached as successful data or hidden by stale,
  success-shaped fallbacks. Reusable data fetches and expensive deterministic transformations MUST
  be cached so ordinary widget reruns reuse valid data rather than repeat API calls. Cached
  responses MUST NOT contain user-specific selections or credentials in returned values.
- User selections for markets, sectors, industries, and any stock list MUST use namespaced,
  session-local `st.session_state` keys and stable identifiers. Valid selections MUST survive
  ordinary reruns; changing a parent or evidence mode MUST clear only dependent invalid
  selections. Session state MUST NOT be used as shared cross-user data storage.
- API requests MUST be limited to the data needed for the active view and MUST respect provider
  rate limits. Missing, stale, unauthorized, or incomplete data MUST be identified rather than
  silently substituted.
- Dependencies MUST be pinned or constrained and have a documented present purpose. External
  services, clocks, and filesystem access MUST be isolated sufficiently for deterministic tests;
  this does not require a separate service or adapter framework.
- Errors MUST preserve actionable context and remain observable without exposing credentials or
  sensitive data. Optimizations beyond the required caching MUST be justified by measurements.
- Backward-incompatible interface or data changes MUST document migration guidance and versioning
  impact. Existing feature plans MUST be reconciled with this constitution before further
  implementation; updating governance alone does not migrate the application.

## Development Workflow and Quality Gates

1. Define the requirement, acceptance criteria, affected contracts, and smallest viable change.
2. Record design decisions for non-trivial work, including rejected alternatives and tradeoffs.
3. Add or update tests first and confirm they detect absent or defective behavior.
4. Implement in small, reviewable increments while preserving clear ownership boundaries.
5. Run the relevant unit and integration suites, then run the full test suite when practical.
6. Review the diff for unnecessary complexity, undocumented behavior, dead code, duplication, and
   scope creep.

Every review MUST verify constitution compliance. Reviewers MUST reject changes whose behavior
cannot be explained, whose tests do not demonstrate the claimed result, whose scope exceeds the
accepted requirement, or whose complexity is unsupported by a present requirement. Any approved
exception MUST identify its owner, rationale, expiry condition, and remediation issue.

## Governance

This constitution governs all project development practices and supersedes conflicting local
guidance. Amendments MUST be proposed in writing with rationale, affected principles, migration
impact, and a semantic version bump. Approval requires explicit maintainer review and recorded
acceptance before the amendment takes effect.

Constitution versions follow semantic versioning: MAJOR for incompatible governance changes or
removed or materially redefined principles, MINOR for new principles or materially expanded
guidance, and PATCH for clarifications that do not change obligations. Compliance MUST be reviewed
for every change and during release readiness. Periodic architecture reviews MUST identify
unjustified complexity, waste, oversized units, coupling, test gaps, and expired exceptions.
Violations MUST be corrected before merge unless an exception meeting the workflow requirements
above is approved.

**Version**: 3.0.0 | **Ratified**: 2026-10-26 | **Last Amended**: 2026-10-29
