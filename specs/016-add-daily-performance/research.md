# Research: Add Daily Performance

**Date**: 2026-11-06
**Status**: Complete; no unresolved design clarifications.

## 1. Keep daily arithmetic independent

**Decision**: Add a pure scalar daily helper in the existing market-data
[sector performance module](../../packages/market-data/src/market_data/domain/sector_performance.py).
Do not extend `PerformancePeriod` or `PerformanceResult`. Keep the absolute calculator's default
five-period results unchanged; allow selecting one existing period to evaluate its availability
without requiring unrelated horizons.

**Rationale**: Existing functions calculate calendar-offset periods together and raise if a
longer-period start is unavailable. The spec requires independent daily availability and unchanged
longer-period behavior. Their results are fractions; the tape converts them to percentage units.
The prior industry specification defines one-session semantics, but the current shared calculator
does not expose a daily result.

**Alternatives considered**: Extending every five-period API with `1d` affects unrelated callers.
A configurable period engine or a new service is unnecessary. A narrow existing-period selector
is sufficient for the user's later independent-availability decision.

## 2. Resolve exact sessions outside domain arithmetic

**Decision**: Reuse the typed
[exchange calendar boundary](../../src/market_leadership/application/exchange_calendar.py)
and [completed-session resolver](../../src/market_leadership/application/market_sessions.py).
The application supplies explicit adjacent official-session dates to domain helpers.
Resolve the ending session with `latest_completed_us_session(requested_as_of, now=...)`
and its exact calendar predecessor once per table context. Observed dates and available prices
do not determine this pair.

**Rationale**: The current discovery path uses US completed-session and observed-date context.
`previous_session` already exists in the protocol. Explicit endpoints distinguish weekends and
holidays from missing evidence and permit deterministic clock/calendar tests.
The [2026-11-06 clarification](spec.md#clarifications) explicitly rejects moving daily endpoints
back to a stale observed date. This keeps entity and benchmark comparisons on one requested-date
interval. Missing exact closes produce `Unavailable`, while existing observed-date/freshness
disclosures and valid longer-period values remain unchanged.

**Alternatives considered**: `iloc[-2:]`, dropping missing values, and calendar-day subtraction
can turn a gap into a misleading multi-session return. Embedding wall-clock/calendar calls in
pure arithmetic would violate the existing separation of concerns. Re-anchoring to an older
observed date would display historical daily movement instead of the selected date's required
interval and was rejected by the user. Preserve observed-date cropping only for existing charts
and longer-period calculations, not the new daily lookup.

## 3. Retain approved ETF and basket behavior

**Decision**: At the user's request, extend
[representation_performance](../../packages/market-data/src/market_data/domain/industry_representations.py)
itself to all six periods by default, rather than retaining a separate daily representation helper.
The user explicitly selected independent unavailable-period handling. Return a
`RepresentationPeriodResult` containing `.value` and `.reason` for each period. Use existing
validity/effectivity checks and exact approved constituent weights.

**Rationale**: Both live sector and industry tapes can receive `reviewed_by_id`; the shared
workflow uses reviewed ETF/basket representations, not the older standalone industry momentum
frame. Basket daily returns must use the same two dates for every constituent, with no weight
renormalization or substitute instruments.

**Alternatives considered**: Only handling ETF symbols misses approved baskets. Adding a daily
key to the old all-or-nothing calculator requires a year's history for a daily value.
A bare nullable dictionary loses failure context; fabricated zeros or silent omissions are invalid.
The unified API keeps each period independent and migrates ranking/snapshot callers to their
existing five-period all-required contract. No persisted snapshot schema changes are needed.

## 4. Separate daily absolute and benchmark-relative validity

**Decision**: Calculate the entity's daily return independently. Only relative mode requires
the benchmark's two matching endpoints. Handle each unavailable period independently and append
daily-specific context to existing tooltips. Valid longer-period values keep their prior math;
short histories can now expose supported weekly/monthly cells rather than losing them to a missing
yearly start. This availability change is the user's explicit implementation choice.

**Rationale**: The existing symbol-only `_entity_performance` requires benchmark history even in
Absolute mode. Changing that legacy behavior would exceed scope; the daily path must nevertheless
fulfill the new spec without a benchmark dependency in Absolute mode. Relative daily returns are
entity minus benchmark, not a ratio or an absolute-return fallback.

**Alternatives considered**: Sharing one exception block could blank all periods. Returning zero
or silently displaying Absolute would misrepresent missing evidence.

Daily helpers inspect already-loaded histories at the required requested-date endpoints;
the existing chart/long-period projection's observed-date crop must not remove valid daily
evidence. If the loaded history lacks either endpoint, report insufficiency rather than
fetching extra data or shifting the interval.

## 5. Extend the shared rendering surface

**Decision**: Insert `1d` in the tape frame and prepend it to
[PERFORMANCE_COLUMNS](../../src/market_leadership/ui/performance_table.py).
Reuse [progressive_tape](../../src/market_leadership/ui/components/progressive_tape.py).

**Rationale**: The renderer follows frame order and styles recognized columns independently,
already formatting two-decimal percentages and `Unavailable`. Ticker/ETF metadata remains hidden
but available to entity buttons. The stock projection does not contain performance columns.

**Alternatives considered**: A bespoke daily renderer duplicates formatting and can diverge
between themes. Adding a daily thumbnail option or ranking control is not requested.

## 6. Validation and documentation boundaries

**Decision**: Extend existing domain, representation, workflow, and renderer tests before
implementation; validate exact heading/cell counts, endpoint math, and unchanged behavior.
Use a browser for real width/theme checks. Record 016's narrow precedence in the active authority
map and supporting 004 artifacts; retain completed historical task evidence.

**Rationale**: Renderer regressions currently hard-code five return cells, and workflow tests
assert complete backing-column order. Those are directly affected, unlike legacy snapshot callers.
The existing completed-session tests in
[test_build_snapshot.py](../../tests/integration/test_build_snapshot.py) cover weekends,
holidays, open sessions, and future requests; extend that boundary for exact adjacent dates.
The setup script's `BRANCH` is the resolved feature identifier while the actual git branch remains
`main`; directory resolution is independent of branch creation.

**Alternatives considered**: Merely testing that `1d` exists misses wrong units, skipped sessions,
benchmark mismatch, and loss of formatting. Reopening historical completed tasks conflates
planning with new implementation evidence.

The task backlog was regenerated on 2026-11-06 after this design reconciliation to replace its
observed-date endpoint instructions with the selected-date rule. Task generation does not claim
implementation completion or alter historical validation evidence.
