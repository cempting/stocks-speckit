# Stock Table Contract

## Scope

This contract applies only to the contained-stocks table after an industry is selected. Sector,
industry, and stock-detail views are unchanged.

## Visible Columns

The table renders exactly these visible columns, in order:

1. Price chart + 50 MA
2. Volume chart
3. Ticker
4. Name
5. CAP Type
6. Total Score

Internal Instrument ID and Resolution fields may remain for selection but must not render as
visible columns.

## CAP Type

| Evidence | Display |
|---|---|
| Current valid capitalization >= $10B | `Large` |
| Current valid capitalization >= $2B and < $10B | `Mid` |
| Current valid capitalization > $0 and < $2B | `Small` |
| Missing, invalid, non-positive, unloaded, failed, or placeholder evidence | `Unavailable` |

CAP Type is available only from the established explicit score-load result. Rendering the table
does not make a provider request.

## Total Score and Chart Evidence

Total Score preserves the existing overall Score calculation and non-numeric states. The price
chart retains its 50 MA and insufficient-moving-average disclosure; the volume chart retains its
unavailable/insufficient disclosure. Neither behavior changes when CAP Type is unavailable.

## Acceptance Evidence

- Unit tests cover provider profile extraction, capitalization validation, all threshold
  boundaries, Total Score rename, and exact table column order.
- Integration tests prove current capitalization travels only through the explicit score-load
  result and is unavailable for failed/missing evidence.
- App tests prove no hidden load, preserved chart disclosures/placeholder identity, and six
  visible columns.
