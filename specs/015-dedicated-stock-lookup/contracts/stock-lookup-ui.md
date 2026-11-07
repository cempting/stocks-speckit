# Stock Lookup UI Contract

**016 presentation precedence**: [Daily performance](../../016-add-daily-performance/spec.md)
adds `1d` before `1 week` to sector/industry tapes, replacing only the eight-column baseline
with nine visible columns. Full entity buttons, hidden ticker evidence, and the five-column
stock projection remain unchanged; historical 015 validation is not evidence of 016 delivery.

## Navigation and Ownership

- The root application exposes exactly four native tabs: **Discovery**, **Industry Deep-Dive**,
  **Yahoo Classification Preview**, and **Find a stock**.
- The **Discovery** tab does not render stock-lookup search, identity selection, listing
  selection, or lookup-detail controls.
- Existing Discovery, Industry Deep-Dive, and Yahoo Classification Preview behavior remains
  available.
- This approved layout complies with constitution 4.0.0 without a tab-count exception.
  The original tracking issue [#2](https://github.com/cempting/stocks-speckit/issues/2) is closed;
  no navigation or data-loading change is required by the governance reconciliation.

## Search and Selection

- Search is limited to retained stock identities in the active catalog and selected region.
- An empty query has no selected result. A query with no matches displays a clear no-match state
  and does not retain stale selections.
- When multiple identities match, the user selects one exact identity before opening detail.
- When active verified listings exist for the selected date, the user selects an exact listing
  before requesting listing history.
- Stocks without active industry membership remain searchable; lookup does not assign or imply
  an industry membership.
- When no active verified listing exists, the page explains why remote listing history is
  unavailable.

## Detail and Data Requests

- Opening a stock detail does not prefetch market history or issuer evidence.
- History load and refresh are explicit user actions.
- Failures and incomplete history remain visible and are not represented as a fresh successful
  result.
- Changes to region, date, or catalog revision clear or revalidate dependent query results,
  selections, detail, and history.

## Scope Boundary

### Approved entity-button presentation

Sector performance, industry momentum and stock-list entity buttons show ticker
above the full unabbreviated name. Ticker font size is at least twice the name's;
long names wrap without clipping, ellipsis or a fixed-height cutoff. Sector/industry
buttons use their existing associated ETF ticker, or `No ticker` for absent,
unavailable, uncovered or basket-only evidence. Never substitute a node ID.
Keep literal catalog text, stable widget keys, native keyboard activation, callbacks,
tooltips and selection/navigation outcomes. Do not change chart geometry/palettes,
period/basis controls, five stock columns or data-load behavior.

The sector tape has no separate Ticker column and the industry tape has no separate
ETF column. Each shows exactly two charts, Sector/Industry and the five return
periods. Retain ticker/ETF values internally for the buttons and chart/source
identity; do not remove the stock table's Ticker column.

The shared renderer in `src/market_leadership/ui/components/progressive_tape.py` owns this
presentation for all three surfaces. Escape ticker/name Markdown before formatting; do not
interpolate catalog text into raw HTML or CSS. Restrict CSS to the entity-button containers
so load, refresh, theme, back, and other controls retain their current appearance.
A long name may occupy several physical lines; "two blocks" is not a two-line height limit.

Verification combines label/selection AppTests with browser measurements: computed
ticker/name font-size ratio >=2, full literal name visible without clipping, native focus
and keyboard activation, and stable selection at wide/narrow widths in both themes.
Repeat browser checks when Streamlit changes; internal Markdown DOM selectors are not a
guaranteed public API. See [quickstart.md](../quickstart.md) for checks and recorded evidence,
including the keyboard-automation limitation.

This is a user-interface contract only. It adds no public API, market-data source,
identity type, acquisition or persistent lookup record.
