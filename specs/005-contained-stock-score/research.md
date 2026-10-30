# Research: Contained Stock Score Summary

## Decisions

### 1. Derive Score from the existing peer scorecard

**Decision**: Calculate Score as the equally weighted arithmetic mean of Quality, Growth, and
Cash Flow only when all three values are finite, within the accepted 0–100 range, and available.

**Rationale**: The feature defines fixed equal weighting and the current scorecard already
provides the three peer-relative component scores. Reusing those values keeps score acquisition
and peer eligibility unchanged.

**Alternatives considered**: Average only the components that are available; show one component
as the Score; add a persisted aggregate. Partial averages make rows incomparable, one component
does not meet the requested overall summary, and persistence adds scope without value.

### 2. Preserve distinct non-numeric score states

**Decision**: Retain `not loaded`, `error`, `insufficient`, and `unavailable` as distinct Score
display states. A placeholder is unavailable unless its existing score evidence explicitly
supports a more specific state.

**Rationale**: A numeric average is valid only for three complete component values. The user must
be able to distinguish score evidence that has not been requested from evidence that cannot
produce a score.

**Alternatives considered**: Display zero, a blank, or a generic unavailable value for every
non-numeric case. These lose evidence meaning or falsely imply a score.

### 3. Remove metadata columns without changing chart disclosures

**Decision**: Remove Observed and Chart Status only from the contained-stocks projection. Keep
the existing price and volume chart-cell captions for unavailable or insufficient evidence.

**Rationale**: Chart cells already convey the evidence condition at the point where it matters.
The removed metadata would otherwise duplicate or distract from comparison information.

**Alternatives considered**: Keep Chart Status for failures; remove the chart-cell captions too.
The first fails the requested simplification, and the second hides required evidence states.

## Resolved Technical Context

- The existing `PeerScorecard` contains Quality, Growth, and Cash Flow blocks with a value and
  state.
- `StockTapeRow` already carries that scorecard plus table-level score state/reason.
- The contained-stocks projection currently owns the legacy component, status, observed, and
  chart-status columns.
- Explicit score loading remains in the Discovery workflow and must not be moved into the table
  projection.
- No new dependency, provider request, cache entry, persistence record, or session-state key is
  needed.
