# Daily Performance UI Contract

**Authority**: [016 specification](../spec.md). This contract narrowly amends the five-return
column baseline in [004](../../004-sector-stock-explorer/spec.md) and its
[progressive UI contract](../../004-sector-stock-explorer/contracts/progressive-discovery.md).
Approved representations remain governed by 008; stock columns by 006; button presentation and
hidden redundant ticker columns by 015.

## Visible interface

Both Sector performance and Industry momentum show exactly nine visible columns in this order:

1. Existing price + 50-session SMA chart.
2. Existing directional-volume chart.
3. Existing Sector or Industry entity button.
4. `1d`.
5. `1 week`.
6. `1 month`.
7. `3 months`.
8. `6 months`.
9. `12 months`.

The daily header is exactly lowercase `1d`. Existing heading wording, hidden backing metadata,
button labels, tooltips, callbacks, keys, chart dimensions, row ordering, and stock projections
remain unchanged apart from an additive daily evidence explanation where needed.

No daily thumbnail option, ranking default, period/direction selector, new tab, or stock-horizon
change is authorized.

## Return and evidence contract

- One day is one consecutive completed official-session interval, not 24 hours or intraday change.
- The ending session is the latest completed official trading session on or before the selected
  as-of date, evaluated against the current completion boundary; the starting session is its
  immediately preceding official trading session. Price availability and an older observed date
  must not select or move these endpoints.
- Stale evidence retains its observed-date/freshness warning. Missing either exact required
  close displays `Unavailable`, not an older daily return, while valid longer-period values
  remain unchanged.
- Exact adjusted endpoint prices must be present, unique by date, finite, and positive.
  Missing intervening-session evidence must not produce a longer interval labeled daily.
- ETFs use their own approved symbol. Approved baskets use all their exact weighted constituents
  and the same session pair; an unavailable constituent invalidates that basket's daily value.
  Preserve existing approval/effectivity checks at the selected as-of date; missing daily prices
  do not authorize an older representation.
- Absolute displays `100 * (end / start - 1)`.
- vs S&P 500 displays the entity percentage return minus the benchmark percentage return
  over identical session dates. Missing benchmark evidence never falls back to Absolute.
- Daily evidence is evaluated independently of the five legacy periods: a daily gap does not
  blank valid longer-period cells, and short but valid daily history can display `1d` when
  longer periods are insufficient.
- Following the user's six-period API decision, each longer horizon is also independently
  available: supported weekly/monthly cells remain visible even without yearly history.
  Existing return arithmetic and labels remain unchanged; unavailable horizons retain explicit
  context. Ranking and snapshot outputs keep their original five-period all-required contract.
- Missing/invalid evidence displays `Unavailable` without gain/loss coloring. Existing row
  context/tooltips expose a `1d:` reason with symbol/session or representation context as relevant.
- Provider failures, stale dates, and uncovered/invalid representations remain explicit under
  the existing workflow; no alternate source or representation is introduced.

## Presentation and interaction contract

- Valid values are right-aligned two-decimal percentages.
- Positive values use the existing green palette; negative values use red; zero uses neutral.
  Daily scaling is independent by period and sign in both supported themes.
- Daily values remain adjacent to weekly values and accessible at supported narrow widths.
  Preserve the existing layout; any necessary width adjustment must retain chart/button
  accessibility and be demonstrated in browser validation.
- Changing thumbnail period cannot change return values. Performance basis continues to persist
  across sector/industry navigation. Existing native selection and back-navigation remain usable.
- Rendering `1d` and changing basis/thumbnail controls cause zero additional provider/catalog
  requests beyond the existing workflow.

## Acceptance evidence

| Case | Expected daily result |
|---|---|
| Entity endpoints 100 then 102; Absolute | `2.00%`, gain palette |
| Entity endpoints 200 then 198; Absolute | `-1.00%`, loss palette |
| Unchanged valid endpoints | `0.00%`, neutral palette |
| Entity +2%, matching benchmark +0.5%; relative | `1.50%` |
| Monday after a normal Friday session | Friday-to-Monday return, not Sunday-to-Monday |
| Holiday before ending session | Use the prior official trading session |
| Missing/non-finite/non-positive required endpoint | `Unavailable`, uncolored, daily reason visible |
| Missing matching benchmark; relative | `Unavailable`, no absolute fallback |
| Missing matching benchmark; Absolute | Entity daily return still available |
| Incomplete or future observations present | Those observations do not affect the daily result |
| Latest required close missing, but an older valid daily pair exists | `Unavailable`, no observed-date fallback; freshness context and valid longer returns retained |
| Benchmark or basket member has only an older valid pair | Relative/basket daily value is unavailable; no interval shifting |
| Approved 50/50 basket with +2% and -1% constituents | `0.50%` |
| Basket constituent missing one required session | `Unavailable`, no renormalization |
| Valid daily pair but insufficient yearly history | Daily remains available; legacy behavior unchanged |
| Invalid daily pair but valid legacy periods | Daily unavailable; legacy values unchanged |

Validate literal heading order and nine-column count separately from internal constants;
validate both named tables, both themes, narrow-width access, and navigation/control regressions.
