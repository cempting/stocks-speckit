# Data Model: Contained Stock Score Summary

## Existing Input Records

### Contained Stock Row

The existing row retains stable instrument identity, ticker, name, price/chart evidence,
placeholder state, `PeerScorecard?`, score evidence state, and score reason. This feature does
not add storage fields or change selection identity.

### Peer Scorecard

The existing scorecard supplies three named blocks: Quality, Growth, and Cash Flow. Each block
has a value and an availability state. It remains the source of truth for component scores.

## Derived Projection

### Overall Score

Fields: `value?`, `state` (`available | not_loaded | insufficient | unavailable | error`),
`reason?`.

Validation rules:

- `available` requires all three component blocks to be `available` with finite values from 0 to
  100 inclusive.
- Its `value` is `(quality + growth + cash_flow) / 3`.
- A missing scorecard with row state `not_loaded` produces `not_loaded`.
- An error row state produces `error`.
- Any insufficient component or row state produces `insufficient`.
- Any other missing, invalid, placeholder, or unavailable component produces `unavailable`.
- Non-`available` states have no numeric value and are never represented as zero.

### Contained-Stock Table Projection

Visible fields, in order: Price chart, Volume chart, Ticker, Name, Price, Score.

Internal fields: Instrument ID and Resolution remain available only to support existing row
selection and rendering behavior.

Removed fields: Observed, Chart Status, Quality, Growth, Cash Flow, Score Status.

## State Transitions

| Prior score evidence | User action or result | Overall Score state |
|---|---|---|
| Not loaded | No score-load request | `not_loaded` |
| Not loaded | Explicit score request returns three available components | `available` |
| Not loaded | Explicit score request returns an error | `error` |
| Not loaded | Explicit score request lacks one or more sufficient components | `insufficient` |
| Any | Component is missing, invalid, or unavailable | `unavailable` |

The feature adds no state transitions to selection, membership, or market-data evidence.
