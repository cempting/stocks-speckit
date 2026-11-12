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

The final caption replaces `12 months` without changing arithmetic or internal keys.
Daily reason metadata remains `1d reason`.
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
  independently scaled by period and sign in both themes. Return text meets WCAG AA contrast
  ratios of at least 4.5:1 for normal text and 3:1 for large text in both themes; gain/loss/neutral
  status remains distinguishable without color. A browser or automated check covers every
  applicable return-text foreground/background pair.
- Chart thumbnails and aligned performance cells remain 84px high. Sector/industry buttons
  are 84px with wider aligned columns and at most three visible name lines. Compact clipping
  is allowed only with unrestricted full-text touch/keyboard details, never hover alone.
  Ticker stays above the unabbreviated name at at least twice its font size; stock names retain
  unrestricted wrapping/minimum height.
- At 1440 CSS pixels, retain the wide nine-field table and four-column Discovery header.
  At 640px, charts stack above one fitting ticker/name and six-labeled-value strip; hide the
  separate wide heading row. At 390px, retain this unwrapped strip with a persistent visible
  table-local scroll cue while fields extend beyond the viewport. Touch and keyboard scrolling
  reaches the final field; text is not clipped within its cell. Charts remain 84 CSS pixels high
  without clipping plotted content. No overlap or horizontal scrolling of ordinary page content.
- At 390/640px, Discovery title stays left beside `As of` in the upper right row and
  `Refresh data`/theme side by side below. Adapt text/spacing without clipping or overlap.
  Retain desktop order/weights, date limits, native callbacks, refresh/cache and theme behavior.
- Explicit touch/keyboard access reveals full names, source, requested/observed dates, freshness,
  representation and failure explanations without clipped detail text. Opening/closing details
  must not navigate, clear valid selections or add provider/catalog requests.
- Basis persists across hierarchy navigation; thumbnails change chart cropping, not returns.
  Native selection/back actions and stock loading safeguards remain. Rendering and ordinary
  basis/thumbnail/detail projections add zero requests beyond the existing workflow.
- On the Industry momentum tape, select an industry from its row; do not show the Industry
  dropdown there.

## Entity Heading and Controls

FR-012/SC-008 apply only to the Sector performance and Industry momentum heading/control groups,
not the Discovery title/date/refresh/theme header or Contained stocks.

- At viewport widths up to and including 640 CSS pixels, the heading occupies the left column
  beside two right-hand control groups: `Thumbnail period` above `Performance basis`.
  The heading spans their two rows; neither control group moves beneath it.
- Above 640px, including wider tablets, retain the existing single-row order: heading left,
  Thumbnail period middle, Performance basis right. Preserve the existing three-column weights.
- Keep the current native widgets, namespaced keys and selection semantics. Thumbnail options
  remain `1w`, `1m`, `3m`, `6m`, `1y`, default `3m`; basis options remain `Absolute` and
  `vs S&P 500`, default `Absolute`. Retain existing empty-selection defaults.
  Labels/options remain readable and reachable by touch/keyboard; contents may wrap within
  their own cells, but no hiding, ellipsis, clipping, overlap or page-level horizontal scrolling.
- Changing viewport width alone must not rerun acquisition or alter hierarchy, valid selections,
  chart choice or return values. Ordinary control changes preserve existing rerun/cache behavior;
  no duplicate mobile widgets, new requests or calculation changes.
- Keep the existing heading/control presence for no-industry, empty, loading and failure states.
  This layout change does not introduce new controls or data loads into those states.

Narrow placement:

```text
Heading (left, spanning both rows) | Thumbnail period (upper right)
                                  | Performance basis (lower right)
```

At 390/640px, verify this placement in both tables and themes. At 641/1440px, verify desktop
preservation. These heading/control cases are additional to the existing table/main-header
acceptance matrix; they do not change those surfaces' breakpoints or acceptance widths.

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
the four-row fixture. [Quickstart](../quickstart.md) defines the six existing width/theme cases,
eight heading/control cases, and touch/keyboard, long-name, unavailable, navigation/control/request checks.
T034 and T029 remain open; FR-012/SC-008 test-first, shared-layout and story-specific acceptance
work is tracked in [tasks](../tasks.md). Current browser measurements are recorded in
[quickstart](../quickstart.md); outstanding touch acceptance is not established by those measurements.
