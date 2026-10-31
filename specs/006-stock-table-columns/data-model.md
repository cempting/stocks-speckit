# Data Model: Stock Table Columns

## Existing Input Records

### Fundamental Bundle

The existing in-memory fundamental bundle gains optional current capitalization evidence:
`market_cap?`, `market_cap_as_of?`, and the profile currency already associated with the bundle.

Validation rules:

- Capitalization must be numeric, finite, and greater than zero.
- `market_cap_as_of` is the profile fetch date.
- A missing, non-numeric, non-finite, or non-positive value is unavailable and is not retained as
  a number.
- This current evidence does not replace historical capitalization evidence used by peer scores.

### Stock Score Evidence

The existing per-stock score evidence gains `market_cap?` and `market_cap_as_of?` copied from its
explicitly loaded fundamental bundle. It continues to own scorecard, score state, and reason.

### Stock Tape Row

The row gains `market_cap?`. It remains optional so rows before score loading, error rows,
placeholders, and stocks without valid current capitalization can render normally.

## Derived Projection

### CAP Type

Values: `Large`, `Mid`, `Small`, `Unavailable`.

Validation rules:

- `Large`: capitalization >= $10,000,000,000.
- `Mid`: capitalization >= $2,000,000,000 and < $10,000,000,000.
- `Small`: capitalization > 0 and < $2,000,000,000.
- `Unavailable`: no valid current capitalization evidence.

### Total Score

Total Score is the existing overall-score result: its equally weighted Quality, Growth, and Cash
Flow average only when all three scores are valid; otherwise its explicit non-numeric state.

### Stock Table Projection

Visible fields, in order: Price chart + 50 MA, Volume chart, Ticker, CAP Type, Total
Score.

Internal fields: Name remains available for the combined ticker/company-name button and detail
identity. Instrument ID and Resolution remain available for existing selection behavior.

## State Transitions

| Prior evidence | User action/result | CAP Type |
|---|---|---|
| No score evidence | Normal table render | `Unavailable` |
| Valid current capitalization | Explicit score load completes | `Large`, `Mid`, or `Small` |
| Missing/invalid capitalization | Explicit score load completes | `Unavailable` |
| Placeholder or score load error | Normal table render | `Unavailable` |

No selection, membership, chart, or peer-score state transition changes.
