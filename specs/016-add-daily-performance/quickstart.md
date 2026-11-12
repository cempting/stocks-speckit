# Validation: Daily Performance

**Current status**: Implementation through T033 and automated contrast regression T035 is complete.
Focused automated checks pass, and both entity tapes have measured geometry at
390/640/641/1440 CSS pixels in both themes. At 390px the final return field is keyboard-reachable
within the table. Touch-dependent acceptance and final cross-surface gates remain open (T034/T029).

Use the [UI contract](contracts/daily-performance-ui.md), [data model](data-model.md) and
[API migration](plan.md#python-api-migration) for expected results.

## Current Verification (2026-11-12)

| Check | Result |
|---|---|
| Focused documented non-live pytest suite | 274 passed, 4 dependency deprecation warnings |
| Ruff on documented feature files | Passed |
| Strict Pyright | 0 errors, 0 warnings, 0 informations |
| Automated return-text contrast | Passed both themes; 670 distinct light-theme pairs (minimum 4.8373:1) and 231 dark-theme pairs (minimum 6.3712:1), including intermediate gain/loss colors; both exceed 4.5:1 normal-text and 3:1 large-text thresholds |
| Sector/Industry phone geometry | At actual 390px in both themes: chart and SVG heights 84px, cue visible, table-local overflow 532px within a 358px container, document width 390px |
| Tablet/desktop boundary | At 640px the strip fits in 608px with no local overflow; at 641px controls return to desktop positions; at 1440px the heading/period/basis columns start at x=80/512/944. Document width matched viewport at all tested widths. |
| Keyboard access to final return | Tab reached the final return field in both tapes and scrolled the table to its 174px maximum; the final cell was fully visible within the table, with no page-level horizontal overflow |
| Touch input | Not verified: the integrated browser reports `navigator.maxTouchPoints = 0` and does not provide a touch-enabled context; T034 remains open |
| Browser request counts | Not instrumented separately; existing AppTest request-spy regressions passed in the focused suite |

Both tables were checked in light and dark themes at actual 390/640/641/1440 CSS pixels.
The 390px Sector chart's SVG viewBox was `0 0 358 84`; the sampled plotted marks remained
within that 84px area. T034 remains open until touch input and the outstanding end-to-end
state/request acceptance can be completed in a touch-capable browser.

## Historical Verification (2026-11-09)

| Check | Result |
|---|---|
| Focused documented non-live pytest suite | 273 passed, 4 dependency deprecation warnings |
| Ruff on documented feature files | Passed |
| Strict Pyright | 0 errors, 0 warnings, 0 informations |
| Industry momentum heading/control geometry | Actual 390/640/641/1440 CSS pixels measured in light and dark themes; zero page overflow |
| Keyboard selection | All five thumbnail options and both basis options selected with keyboard; 3m/Absolute restored and preserved while resizing across all four widths |
| Touch input | Not verified: the integrated browser context reports that it does not support `tap` without `hasTouch` |

Industry geometry used the running Discovery page at actual CSS widths (the browser's
requested viewport width was scaled by its zoom): at 390px the heading was at x=16 and controls
at x=199; at 640px they were at x=16 and x=324; at 641px the three columns began at x=16,
x=224 and x=433; at 1440px they began at x=80, x=512 and x=944. Positions were the same in
both themes, and document overflow was zero at every width. The live page was on Industry
momentum after selecting XLC; its requested/observed dates were 2026-11-09/2026-11-06 and
visible returns were unavailable. Controlled ETF, basket, empty-membership, navigation and
request-spy scenarios are covered by the passing AppTests, not represented as live-market
browser evidence.

The browser's Playwright context has no touch support, so this run does not establish physical
or emulated touch access. The browser run also did not independently instrument provider request
counts. AppTest request-spy regressions passed in the documented suite. Keep T034/T029 open
until the remaining touch-dependent and complete cross-surface acceptance is performed.

## Environment

Use Python 3.12 and the existing uv environment. Live walkthroughs require the current valid
catalog and approved representations; retain `MARKET_CATALOG_MANIFEST_PATH` if configured.
Deterministic cases use existing synthetic fixtures with injected histories/clock/calendar,
never a production fixture/provider selector or altered published release.

## Automated Gates

Confirm new regressions fail before implementing their corresponding fixes, then run from repository root:

```bash
uv run pytest -m "not live" -q \
  tests/unit/domain/test_sector_performance.py \
  tests/unit/test_industry_representations.py \
  tests/unit/test_industry_momentum.py \
  tests/unit/ui/test_performance_table.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_discovery.py \
  tests/app/test_market_selection.py \
  tests/app/test_scoreboard.py \
  tests/integration/test_build_snapshot.py \
  tests/integration/test_industry_representations.py

uv run ruff check \
  packages/market-data/src/market_data/domain/sector_performance.py \
  packages/market-data/src/market_data/domain/industry_representations.py \
  packages/market-data/src/market_data/domain/industry_momentum.py \
  src/market_leadership/application/market_sessions.py \
  src/market_leadership/application/discover_sectors.py \
  src/market_leadership/ui/workflows/discovery_page.py \
  src/market_leadership/ui/performance_table.py \
  src/market_leadership/ui/components/progressive_tape.py \
  tests/unit/domain/test_sector_performance.py \
  tests/unit/test_industry_representations.py \
  tests/unit/test_industry_momentum.py \
  tests/unit/ui/test_performance_table.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_discovery.py \
  tests/app/test_market_selection.py \
  tests/app/test_scoreboard.py \
  tests/integration/test_build_snapshot.py \
  tests/integration/test_industry_representations.py
uv run pyright
```

Verify controlled return/evidence cases in the contract, exact session boundaries, independent
horizons, preserved ranking/snapshot outputs, literal captions/order and 24 return cells for
four rows. Compare longer-period values, palettes, legacy-frame formatting, charts, navigation,
selection and request counts. In both themes, automatically check every gain/loss/neutral return
text foreground/background pair, including intermediate ramp colors, against WCAG AA (4.5:1 for
normal text and 3:1 for large text); verify status remains identifiable from the signed value and
zero without color. Escalate to the full non-live suite when practical or coupled failures warrant it.

For FR-012, extend the existing AppTest patterns in `tests/app/test_market_selection.py`,
`tests/app/test_sector_stock_explorer.py` and `tests/app/test_discovery.py` before source changes:

- Check one native heading/period/basis group at each entity stage, unchanged widget labels,
  options/defaults/keys/order and existing desktop column weights.
- Check entity-only container scope and the inclusive 640px media rule; keep the main header,
  Contained stocks and other tabs outside that scope.
- Exercise both bases, all thumbnail options, theme reruns and hierarchy/back navigation.
  Valid values persist; thumbnail-only changes preserve returns and existing fallback defaults.
- Compare request spies against the existing per-rerun baseline. Resizing adds zero requests;
  changing a control adds no acquisition beyond its existing workflow. Do not redefine that
  baseline as zero total provider invocations.

Structure/CSS assertions prove wiring, not actual two-row placement, readable options or
touch usability. The browser cases below are required separately.

## Browser Acceptance

```bash
uv run streamlit run streamlit_app.py
```

Measure actual CSS width, not just requested viewport size. Run both entity tables and the
Discovery header at **390, 640 and 1440px in light and dark themes** (six combinations).

1. Verify exact captions/order, daily/weekly adjacency, gains/losses/zero/unavailable styling
   and readable charts/values. Use deterministic tests for numerical cases live evidence cannot supply.
   The automated contrast regression must cover every applicable foreground/background pair in both themes.
2. At 1440px retain nine fields and the four-column header. At 640px charts stack above a
   fitting ticker/six-value strip. At 390px charts are exactly 84 CSS pixels high with plotted
   content unclipped, and the same unwrapped strip displays a persistent table-local scroll cue.
   Use touch swipes and keyboard scrolling within the table to reach all seven fields; field text
   itself must not be clipped. Ordinary page overflow must be zero; no overlap.
3. At 390/640px title stays left beside date above refresh/theme. Exercise native date/calendar,
   refresh and theme with touch/keyboard; preserve limits, cache semantics and valid selections.
   DOM-dispatched clicks alone do not prove phone touch usability.
4. Open/close full long-name and unavailable-evidence details by touch and keyboard, without hover.
   Read all applicable source/date/freshness/representation/failure text; confirm no clipping,
   navigation, lost selection or added provider/catalog requests.
5. Exercise both bases, all thumbnail choices, sector/industry/back navigation and stock selection.
   Basis persists; thumbnails change charts, not returns. Stock tables retain five fields and
   explicit detail/history-loading safeguards.

### Heading/Control Boundary Acceptance

In both tables and both themes, measure the additional FR-012/SC-008 matrix:

| Actual CSS width | Expected entity heading/control arrangement |
|---|---|
| 390px | Heading left spanning two rows; Thumbnail period upper right, Performance basis lower right. |
| 640px | Same narrow arrangement; the cutoff includes 640px. |
| 641px | Existing three-column desktop arrangement; narrow rules no longer apply. |
| 1440px | Existing desktop heading/period/basis arrangement and weights. |

This is eight width/theme combinations. The overlapping 390/640/1440 sessions can also
validate the six existing table/main-header combinations; the new 641px case checks this
group's boundary only and does not redefine table or main-header acceptance.

1. Measure the heading and both control groups' bounds. At 390/640px the heading stays left
   of both groups, period above basis; contents do not overlap or clip. At 641/1440px preserve
   heading/period/basis left-to-right placement.
2. Read complete labels and reach all five thumbnail choices and both basis choices using
   touch and keyboard. Internal wrapping is allowed; moving an entire control below the
   heading, hiding an option, or requiring page scrolling is a failure.
3. Resize across 640/641px without changing selections. Confirm period, basis, hierarchy,
   displayed returns and requested/observed dates persist, with no resize-triggered requests.
4. Switch each control and theme, then navigate sector -> industry -> back. Check existing
   return/chart semantics, valid state and request/cache behavior. Inspect unavailable-only
   rows and existing empty/error states without introducing controls or fetches there.
5. Verify stock-stage controls, main-header layout and table-local scrolling were not changed
   by the entity-only rules. Record actual widths, theme, input method, bounds, overflow,
   selections and outcomes; DOM clicks alone are not touch-input evidence.

Record commands, measured dimensions, theme/input method, outcomes and unresolved gaps.
Do not infer numerical correctness, non-hover usability or zero added requests from an app launch.

## Historical Evidence

These results cover the implementation at the time, **not** the pending caption/390px/detail
requirements or newly planned FR-012 heading/control layout.

| Check | Observed result |
|---|---|
| Unified-API test-first run | 4 failures: endpoint arguments not yet accepted. |
| Initial consolidated nine-file daily suite | 231 passed, 2 failed: daily activity incorrectly suppressed valid older-context longer evidence. |
| Independent activity correction | 233 passed; added short-history/period-selector cases brought the nine-file suite to 243 passed. |
| 640px strip test-first/final checks | Two initial failures; final nine-file daily suite 251 passed, focused renderer/workflow 156 passed. |
| Daily quality gates | Ruff passed; strict Pyright 0 errors/0 warnings. |
| Full offline suite | 1041 passed, 1 failed, 1 deselected; unrelated existing three-tab assertion in [test_default_market_catalog.py](../../tests/unit/test_default_market_catalog.py) versus four-tab [app.py](../../src/market_leadership/app.py). No full-suite success claimed. |
| Header test-first/final checks | Regressions failed before implementation; `uv run pytest tests/app/test_market_selection.py tests/app/test_discovery.py -q`: 13 passed. Ruff/Pyright passed. |

Request spies used the existing one-batched-fetch-per-rerun fixture baseline: no additional
daily/basis/thumbnail/navigation calls, not zero total provider invocations.
The historical nine-file command used the focused pytest list above without
`tests/app/test_market_selection.py` and `tests/app/test_scoreboard.py`.
The 13-test header run reported four existing exchange-calendar warnings.

Browser evidence from 2026-11-07:

- Both tables passed actual 640/1440 CSS pixels in both themes. At 150% browser zoom,
  requested 960/2160 viewports measured exactly 640/1440 `innerWidth`.
  Industry rows included +1%, -1%, zero and two unavailable representations; measured backgrounds
  confirmed gain/loss/neutral/uncolored states after theme rerenders settled.
- At 640px ticker/name and six labeled values shared vertical coordinates below stacked charts,
  with 84px cells/available thumbnails and zero page overflow; missing charts kept explicit placeholders.
  At 1440px nine columns and separate headings remained.
- Entity +2% and benchmark +0.5% produced relative sector 1.50%; industry +1% produced 0.50%,
  independently of its parent. Loss/flat/missing industry rows produced -1.50%/-0.50%/`Unavailable`.
- All five thumbnail controls left returns unchanged. Back navigation preserved basis/thumbnail
  selections; stock detail opened without exceptions and retained five headings/explicit continuity loads.
  Stock tapes had no entity-only responsive wrapper.
- Header passed both widths/themes. At 640px: title x=16, date/refresh x=300, theme x=584;
  buttons y=172, height 40px, theme target width 40px, page overflow zero.
  Theme callback was exercised by DOM click, not claimed as phone-touch evidence.
- Checks used the real Discovery/shared renderer with isolated existing fixture data on an owned
  port-8503 helper. The shared port-8502 process was not restarted or managed; it was unavailable
  during some checks and retained imported header code during later reloads.
  Owned helpers were stopped and their fixture files removed; no production selector, dependency,
  published-catalog change or remote request was introduced.

The current Industry geometry and automated outcomes above do not close the remaining
touch-dependent T034/T029 gates or establish app-wide responsive compliance.
