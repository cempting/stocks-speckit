# Quickstart: Dedicated Stock Lookup

## Prerequisites

- Python 3.12 and the repository's existing development environment.
- A valid local catalog fixture for deterministic AppTest scenarios.
- Use the existing locked dependencies; do not add packages just to run these checks.
- Behavior is defined by the [UI contract](contracts/stock-lookup-ui.md); frame fields and
  selection invariants are described in the [data model](data-model.md).

## Automated Validation

Run the lookup, detail, Discovery, and root-tab regression tests:

```bash
uv run pytest \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_stock_lookup.py \
  tests/app/test_stock_detail.py \
  tests/app/test_discovery.py \
  tests/app/test_progressive_tabs.py \
  tests/app/test_cloud_entrypoint.py
```

Expected outcomes:

- Find a stock is present as a separate root tab and lookup controls are absent from Discovery.
- Ambiguous results require exact stock identity and listing selections.
- Identities without verified active listings do not cause remote history requests.
- Identities without industry membership remain searchable without an inferred membership.
- History and evidence loads remain explicit, and the other tabs continue to render.
- Sector/industry/stock entity buttons show ticker above the full literal name;
  missing sector/industry ETF evidence shows `No ticker`. Five stock columns,
  chart geometry/palettes, tooltips and stable selection behavior remain unchanged.
- Sector and industry tapes each show exactly eight columns: two charts, the
  Sector/Industry button and five return periods. Neither has a separate
  Ticker/ETF column; the stock table still has its Ticker column.

Run the existing quality gates without adding dependencies:

```bash
uv run ruff check \
  src/market_leadership/ui/components/progressive_tape.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_stock_detail.py
uv run pyright
```

## Local UI Check

Run the application with the configured local catalog:

```bash
uv run streamlit run streamlit_app.py
```

Verify that the root shows Discovery, Industry Deep-Dive, Yahoo Classification Preview, and
Find a stock. Open Find a stock, search and select a retained identity, and confirm that opening
the detail does not request history until the explicit history action is used. Return to
Discovery and confirm its exploration controls remain available without the lookup workflow.

Inspect sector performance, industry momentum and stock lists in light/dark themes
at wide and narrow widths. Each native entity button must show a ticker first
(or `No ticker` for absent sector/industry ETF evidence), then the full wrapping name.
Measure computed font sizes, not just apparent boldness: ticker/name ratio must be
at least 2. Verify long names and literal Markdown characters remain fully visible.
Check selection, tooltips and normal native keyboard activation without changing
chart/control geometry or fetching more data.

Use the recorded 1440px and 640px viewports as reproducible wide/narrow checks in both
themes. Include an unbroken long name, literal Markdown punctuation, duplicate display
names with different IDs, and missing/unavailable/basket ETF cases. Inspect rendered
text and scroll/client bounds as well as computed font sizes; an unchanged label string
alone is not evidence that the full name fits.

For keyboard validation, focus each entity button with Tab and activate with Enter and
Space, then confirm the same selection result as a pointer click. If automation cannot
dispatch keyboard events, record that limitation and perform a manual smoke check rather
than reporting an automated pass. Verify non-entity load/refresh/back/theme controls
retain their appearance. Repeat these checks after Streamlit upgrades.

## Validation Evidence (2026-11-06)

The results below were already recorded before this planning reconciliation; the
documentation-only `/speckit-plan` pass did not rerun runtime or browser tests.

- Added/updated renderer and workflow tests failed in 17 selected cases before the
  implementation, detecting the original single-line/name-only button labels.
- The seven-file regression command above passed **103 tests** after implementation.
  Four existing exchange-calendars/NumPy deprecation warnings remain unrelated.
- Targeted Ruff passed; workspace strict Pyright reported zero errors/warnings.
- A temporary offline Streamlit fixture imported the production renderer/theme and
  used only synthetic sector, industry, stock and absent/basket-ETF rows. No live
  catalog, provider acquisition or user data was needed.
- At viewport widths **1440px and 640px**, in **both light and dark themes**, all
  five fixture buttons retained native focusability. Computed ticker/name sizes
  were **24px / 12px (2:1)**. All three long literal names wrapped without clipping;
  both absent/basket ETF cases showed `No ticker`, never a node ID.
- DOM activation selected the exact sector, industry and stock IDs; production
  AppTests also verified hierarchy/detail navigation and retained control state.
- Keyboard automation limitation: the integrated browser's Enter/Space commands
  did not dispatch key events to the focused native button (instrumentation observed
  none). Native button semantics and focusability were verified; actual keyboard
  activation remains a recommended manual smoke check, not a claimed automated pass.

## Redundant Column Removal Evidence (2026-11-06)

- Six selected renderer/workflow cases failed before removal, identifying the
  unwanted sector Ticker and industry ETF headings.
- The focused renderer, explorer and stock-detail regression run passed **86 tests**.
  It verifies exactly eight entity columns, retained ticker/`No ticker` buttons,
  unchanged backing ticker fields, coverage tooltips, stable selections and five
  visible stock columns. Existing chart/control/return regressions also pass.
- Targeted Ruff, workspace strict Pyright, whitespace and amended documentation-link
  checks passed. Four existing dependency deprecation warnings remain unrelated.
- This is a visible projection change only. No ticker source, catalog record,
  chart input, callback, font rule or acquisition behavior changed. Earlier browser
  typography evidence above predates this removal and is not a new browser run.

## Governance Reconciliation (2026-11-06)

- Constitution 4.0.0 permits the approved four native tabs without a tab-count exception.
- The specification, plan and UI contract record the existing labels/count and current
  architecture gates. Issue [#2](https://github.com/cempting/stocks-speckit/issues/2) was verified
  closed on 2026-11-06; no exception-expiry obligation remains.
- C2 is resolved by this documentation reconciliation. T015 remains historical; T026 records
  the reconciliation and documentation checks. No source, data model, test or runtime behavior
  changed, and no runtime/browser tests were rerun.
- A1's identity-search date-scope clarification and E1's manual keyboard-activation validation
  remain separate follow-ups; this reconciliation does not claim to resolve them.
