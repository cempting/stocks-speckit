<!--
Sync Impact Report
- Version change: scaffold -> 1.0.0
- Modified principles: none (initial ratification)
- Added principles:
	- I. Deliberate Design Before Code
	- II. Small, Cohesive Units
	- III. Tests Are Required Evidence
	- IV. Lean and Extensible Architecture
	- V. Maintainability Is a Feature
- Added sections: Engineering Constraints; Development Workflow and Quality Gates
- Removed sections: none
- Follow-up TODOs: none
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

### IV. Lean and Extensible Architecture
Implementations MUST use the simplest architecture that satisfies current verified requirements.
New layers, abstractions, dependencies, configuration, and extension points MUST solve a
demonstrated need and MUST include a concrete cost-benefit justification. Extensibility MUST come
from stable, narrow interfaces and replaceable components, not speculative generalization. Existing
repository patterns and standard-library capabilities MUST be preferred when they meet the
requirement.

### V. Maintainability Is a Feature
Code MUST communicate intent through precise names, straightforward control flow, explicit types
or contracts, and minimal hidden state. Duplication MUST be removed when it represents shared
knowledge; similar-looking code with distinct responsibilities MUST remain separate. Public
behavior and non-obvious decisions MUST be documented near their source. Refactoring MUST preserve
behavior with tests, and each change MUST leave the touched area no harder to understand, test, or
modify.

## Engineering Constraints

- Dependencies MUST be pinned or constrained according to the project's package-management policy
  and MUST have a clear owner, purpose, and maintenance assessment.
- External systems, clocks, randomness, filesystem access, and network access MUST be isolated
  behind boundaries that permit deterministic tests.
- Errors MUST preserve actionable context and MUST NOT be silently ignored. User-visible and
	operational failures MUST be observable without exposing sensitive data.
- Performance optimizations MUST follow measurement and MUST include a reproducible benchmark when
	they increase complexity.
- Backward-incompatible interface or data changes MUST include migration guidance and explicit
	versioning impact.

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
removed principles, MINOR for new principles or materially expanded obligations, and PATCH for
clarifications that do not change obligations. Compliance MUST be reviewed for every change and
during release readiness. Periodic architecture reviews MUST identify unjustified complexity,
oversized units, test gaps, and expired exceptions. Violations MUST be corrected before merge unless
an exception meeting the workflow requirements above is approved.

**Version**: 1.0.0 | **Ratified**: 2026-10-26 | **Last Amended**: 2026-10-26
