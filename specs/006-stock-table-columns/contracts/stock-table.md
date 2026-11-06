# Stock Table Contract

**Active owner (2026-11-02)**: [Feature 006](../spec.md), incorporating former feature 005.
The original aggregate and current five-column presentation are one feature, not separate backlogs.

## Scope

This contract applies only to the contained-stocks table after an industry is selected. Sector,
industry, and stock-detail views are unchanged.

## Visible Columns

The table renders exactly these visible columns, in order:

1. Price chart + 50 MA
2. Volume chart
3. Ticker
4. CAP Type
5. Total Score

The Ticker button contains both ticker and company name. Name, Instrument ID and Resolution
remain internal metadata, not separate visible columns; stock-detail names remain unchanged.
Under the approved [015 presentation amendment](../../015-dedicated-stock-lookup/spec.md),
the native Ticker button shows ticker above the full wrapping company name, with
ticker font size at least twice the name's. This does not add a visible column or
change stock identity, selection, chart geometry, score loading or detail rendering.

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

Total Score is `(Quality + Growth + Cash Flow) / 3` only when all three component scores are
available. Use the established score precision; never compute a partial mean or zero-fill a
missing component. Numeric calculated, not loaded, insufficient, unavailable, and error states
remain distinct. Components retain [001's formulas](../../001-market-leadership-screener/spec.md),
not formulas inferred from the eight raw matrix metrics.

The price
chart retains its 50 MA and insufficient-moving-average disclosure; the volume chart retains its
unavailable/insufficient disclosure. Neither behavior changes when CAP Type is unavailable.

No separate Observed, Chart Status, component-score, Score Status, Name, or price column is
restored. Unchanged eligible evidence may survive catalog changes, but invalid selections and
affected peer contexts must be reconciled without implicit loading. On reviewed
[012 adoption](../../012-stock-industry-memberships/spec.md), effective descendant membership
deduplicates instruments; scores retain exact industry/cohort/date context and unchanged valid
issuer requests are reused. Previously unrequested peers require explicit loading.

## Acceptance Evidence

- Unit tests cover provider profile extraction, capitalization validation, all threshold
  boundaries, Total Score rename, and exact table column order.
- Integration tests prove current capitalization travels only through the explicit score-load
  result and is unavailable for failed/missing evidence.
- App tests prove no hidden load, preserved chart disclosures/placeholder identity, and five
  visible columns.
