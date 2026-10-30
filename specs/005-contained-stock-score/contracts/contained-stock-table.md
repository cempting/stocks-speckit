# Contained-Stock Table Contract

## Scope

This contract applies only to the contained-stocks table after an industry is selected. Sector,
industry, and stock-detail presentations are unchanged.

## Visible Columns

The table renders these visible columns in order:

1. Price chart
2. Volume chart
3. Ticker
4. Name
5. Price
6. Score

It must not render `Observed`, `Chart Status`, `Quality`, `Growth`, `Cash Flow`, or `Score
Status`.

## Score

Score is displayed with one decimal place only when Quality, Growth, and Cash Flow are each in
the `available` state with finite values from 0 to 100. Its value is their equally weighted
average.

Otherwise, Score displays exactly one explicit state:

| Condition | Display state |
|---|---|
| Score evidence has not been requested | `Not loaded` |
| Score request failed | `Error` |
| Any required component is insufficient | `Insufficient` |
| A component is missing, invalid, unavailable, or the row is a placeholder | `Unavailable` |

Rendering the table must not request or reload score evidence.

## Chart Evidence

The removal of `Observed` and `Chart Status` must not suppress the existing price/volume chart
cell captions for unavailable or insufficient evidence. Placeholder identity presentation remains
unchanged.

## Acceptance Evidence

- Projection tests verify exact visible/removed column names and order.
- Projection tests verify a numeric mean only for three valid components and every non-numeric
  state.
- App tests verify that contained stocks render no removed columns, preserve chart-cell
  disclosures, and do not load scores without the existing explicit action.
