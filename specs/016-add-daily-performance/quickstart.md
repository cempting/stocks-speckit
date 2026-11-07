# Validation: Daily Performance

**Current status**: Daily calculations and 640/1440px layouts have historical evidence.
T030 (`1 year` caption) and T027-T029 (phone/details and final acceptance) remain open.
This documentation cleanup runs no application tests and establishes no new browser pass.

Use the [UI contract](contracts/daily-performance-ui.md), [data model](data-model.md) and
[API migration](plan.md#python-api-migration) for expected results.

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
selection and request counts. Escalate to the full non-live suite when practical or coupled failures warrant it.

## Browser Acceptance

```bash
uv run streamlit run streamlit_app.py
```

Measure actual CSS width, not just requested viewport size. Run both entity tables and the
Discovery header at **390, 640 and 1440px in light and dark themes** (six combinations).

1. Verify exact captions/order, daily/weekly adjacency, gains/losses/zero/unavailable styling
   and readable charts/values. Use deterministic tests for numerical cases live evidence cannot supply.
2. At 1440px retain nine fields and the four-column header. At 640px charts stack above a
   fitting ticker/six-value strip. At 390px charts remain readable and the same unwrapped strip
   has a visible local-scroll cue; use touch swipes and keyboard scrolling to reach all seven fields.
   Ordinary page overflow must be zero; no value clipping or overlap.
3. At 390/640px title stays left beside date above refresh/theme. Exercise native date/calendar,
   refresh and theme with touch/keyboard; preserve limits, cache semantics and valid selections.
   DOM-dispatched clicks alone do not prove phone touch usability.
4. Open/close full long-name and unavailable-evidence details by touch and keyboard, without hover.
   Read all applicable source/date/freshness/representation/failure text; confirm no clipping,
   navigation, lost selection or added provider/catalog requests.
5. Exercise both bases, all thumbnail choices, sector/industry/back navigation and stock selection.
   Basis persists; thumbnails change charts, not returns. Stock tables retain five fields and
   explicit detail/history-loading safeguards.

Record commands, measured dimensions, theme/input method, outcomes and unresolved gaps.
Do not infer numerical correctness, non-hover usability or zero added requests from an app launch.

## Historical Evidence

These results cover the implementation at the time, **not** the pending caption/390px/detail requirements.

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

Only passing T027-T030 and the current six-combination walkthrough can close the remaining gates;
historical results do not establish app-wide responsive compliance.
