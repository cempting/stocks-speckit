# Daily Performance UI Contract

**Authority**: [016 spec](../spec.md). [004](../../004-sector-stock-explorer/spec.md) owns
Discovery/navigation, [008](../../008-industry-representation-tools/spec.md) representations,
[015](../../015-dedicated-stock-lookup/spec.md) button identity, and
[006](../../006-stock-table-columns/spec.md) the unchanged stock table.

## Fields and Captions

Both entity tapes have nine ordered fields: existing price/50-session-SMA chart,
directional-volume chart, Sector/Industry button, then these six return fields:

| Display caption | Internal key |
|---|---|
| `1 day` | `1d` |
| `1 week` | `1w` |
| `1 month` | `1m` |
| `3 months` | `3m` |
| `6 months` | `6m` |
| `1 year` | `12m` |

The final caption replaces `12 months` without changing arithmetic or internal keys;
implementation remains pending T030. Daily reason metadata remains `1d reason`.
Ticker/ETF, Node ID, status and representation metadata stay internal, available to buttons,
charts and evidence details. Preserve row ordering, callbacks, keys and stock projections.
No daily thumbnail, period/direction selector, ranking default, tab or stock-horizon change.

## Returns and Evidence

- Daily uses the latest completed official session on/before the requested date and its exact
  official predecessor. Incomplete/future sessions are excluded. Prices and observed dates
  never select endpoints; missing exact closes produce `Unavailable`, not an older interval.
- Exact adjusted endpoints must be unique by date, finite and positive. ETFs use their own
  approved symbol; baskets use every approved constituent, identical session dates and exact
  weights totaling 100%. No dropping, renormalization, inferred membership, parent/alternate
  instruments or fabricated traded-basket charts.
- Absolute is `100 * (end / start - 1)`. Relative is entity percentage minus matching
  benchmark percentage. Absolute daily needs no benchmark; relative failure never falls back.
- All six display horizons are independently available. Preserve valid longer-period arithmetic,
  alignment and existing observed-date cutoffs; daily gaps do not blank other valid periods.
  Ranking/snapshots retain five-period all-required float outputs.
- Shared approval errors remain domain errors. Activity is evaluated separately for daily and
  longer-period dates; inactivity affects only that context unless both are inactive, which raises.
- Missing/invalid evidence displays uncolored `Unavailable` with an actionable `1d:` explanation
  as applicable. Preserve source, requested/observed dates, freshness and representation context;
  provider failures and uncovered rows remain explicit. No silent source or stale-success fallback.

Calculation/result shapes and migration are defined in [data-model.md](../data-model.md) and
[plan.md](../plan.md#python-api-migration), not duplicated by the renderer.

## Presentation and Interaction

- Values are right-aligned two-decimal percentages: green gains, red losses, neutral zero,
  independently scaled by period and sign in both themes.
- Chart thumbnails and aligned performance cells remain 84px high. Sector/industry buttons
  are 84px with wider aligned columns and at most three visible name lines. Compact clipping
  is allowed only with unrestricted full-text touch/keyboard details, never hover alone.
  Ticker stays above the unabbreviated name at at least twice its font size; stock names retain
  unrestricted wrapping/minimum height.
- At 1440 CSS pixels, retain the wide nine-field table and four-column Discovery header.
  At 640px, charts stack above one fitting ticker/name and six-labeled-value strip; hide the
  separate wide heading row. At 390px, retain this unwrapped strip with visibly discoverable
  touch/keyboard-operable horizontal scrolling inside the table. Charts stay stacked/readable.
  No clipped values, overlap or horizontal scrolling of ordinary page content.
- At 390/640px, Discovery title stays left beside `As of` in the upper right row and
  `Refresh data`/theme side by side below. Adapt text/spacing without clipping or overlap.
  Retain desktop order/weights, date limits, native callbacks, refresh/cache and theme behavior.
- Explicit touch/keyboard access reveals full names, source, requested/observed dates, freshness,
  representation and failure explanations without clipped detail text. Opening/closing details
  must not navigate, clear valid selections or add provider/catalog requests.
- Basis persists across hierarchy navigation; thumbnails change chart cropping, not returns.
  Native selection/back actions and stock loading safeguards remain. Rendering and ordinary
  basis/thumbnail/detail projections add zero requests beyond the existing workflow.

## Acceptance Cases

| Controlled evidence | Expected daily result |
|---|---|
| 100/102; Absolute | `2.00%`, gain |
| 200/198; Absolute | `-1.00%`, loss |
| Equal valid endpoints | `0.00%`, neutral |
| Entity +2%, same-interval benchmark +0.5%; relative | `1.50%` |
| Normal Monday or post-holiday session | Return from immediately preceding official session |
| Missing/non-finite/non-positive required endpoint | Uncolored `Unavailable`, actionable reason |
| Older valid entity/benchmark/basket pair only | `Unavailable`, no interval shift; preserve freshness/other valid returns |
| Missing benchmark | Relative unavailable; Absolute daily remains independent |
| Incomplete/future observations | No effect on the required daily interval |
| Approved 50/50 basket of +2%/-1% | `0.50%` |
| Missing constituent endpoint | `Unavailable`, no renormalization |
| Short valid daily history or isolated longer horizon | Supported periods remain independently visible |

Verify literal captions/order independently of constants, nine fields and 24 return cells for
the four-row fixture. [Quickstart](../quickstart.md) defines all six actual width/theme cases
and touch/keyboard, long-name, unavailable, navigation/control/request checks.
T027-T030 remain open; historical 640/1440px evidence does not establish phone or new-caption acceptance.
