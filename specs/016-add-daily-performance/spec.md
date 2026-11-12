# Feature Specification: Daily Sector and Industry Performance

**Feature**: `016-add-daily-performance` | **Working branch**: `main`
**Created**: 2026-11-06
**Status**: Daily calculation, `1 year` caption, and responsive heading/control layout
implemented. Focused automated checks and Industry momentum geometry passed; touch-dependent
and final cross-surface acceptance remain pending.

## Scope

Add `1 day` before the weekly return in Sector performance and Industry momentum.
The [UI contract](contracts/daily-performance-ui.md) defines the six display horizons;
internal keys are `1d`, `1w`, `1m`, `3m`, `6m`, `12m`.
The approved final caption is `1 year`; the internal period key remains `12m`.
Discovery also needs the responsive header, phone scrolling, and non-hover evidence access below.
The Sector performance and Industry momentum heading/control groups also need a two-row
layout at widths up to 640 CSS pixels, with the controls beside their heading.
No stock-table horizons, thumbnail options, ranking defaults, tabs, data sources, or loading workflows change.

## Clarifications

- One day is the exact consecutive completed official-session interval for the requested date,
  never an older observed pair, intraday movement, or 24 hours.
- The representation API returns six independently available value/reason entries.
  Ranking and snapshots retain their five-period all-required outputs.
- At 640px, charts stack above one fitting ticker/six-value strip.
  At 390px, the strip stays unwrapped with discoverable table-local scrolling, not page scrolling.
- Display captions use `1 day` and `1 year`; calculation keys remain `1d` and `12m`.

### Session 2026-11-08

- Q: How should the heading and the two controls be arranged on tablet and iPhone screens?
  → A: Keep the heading on the left, with Thumbnail period on the upper-right row and
  Performance basis on the lower-right row.
- Q: Up to what screen width should the heading-left, controls-stacked-right layout apply?
  → A: Through 640 CSS pixels, retaining the existing narrow-screen cutoff.
  Wider screens, including wider tablets, retain the desktop arrangement.

### Session 2026-11-09

- Q: After hiding the source captions above Contained stocks, where should provider and requested/observed-date evidence remain available?
  → A: Hide shared captions; keep applicable source, requested/observed-date, and freshness evidence accessible through per-stock details for the separate Discovery update, not feature 016.
- Q: Should the active Daily Sector and Industry Performance specification include the recent Contained stocks changes, or should those remain a separate Discovery update?
  → A: Keep this feature limited to daily performance; track Contained stocks changes as a separate Discovery update.

## User Scenarios & Testing

### US1 - Compare Daily Sector Performance (P1)

Compare the latest daily sector movement directly with longer horizons, without selecting an industry.

**Independent test**: Open Sector performance with controlled completed-session prices.

1. Both available and unavailable rows show the six ordered horizons from the UI contract.
2. Absolute closes 100/102 display `2.00%`; losses and zero use existing loss/neutral formatting.
3. At 390/640px, the title sits beside date above refresh/theme controls; at 1440px, the desktop header remains.
4. At 640px the ticker/six-value strip fits below stacked charts; at 390px charts remain 84 CSS pixels high without clipping plotted content, and a visible table-local scroll cue helps touch and keyboard users reach every field.
5. At 390/640px, Sector performance stays left beside Thumbnail period above
   Performance basis on the right; neither control moves below the heading.

### US2 - Compare Daily Industry Momentum (P1)

Compare industries using the same horizons and each industry's own approved representation.

**Independent test**: Select a sector with controlled industry ETF and basket evidence.

1. ETF closes 200/198 display `-1.00%`, independently of the parent sector.
2. An approved 50/50 basket of +2%/-1% displays `0.50%`.
3. Both tables retain the same horizon order and responsive behavior; thumbnail changes do not change returns.
4. At 390/640px, Industry momentum uses the same heading-left, controls-stacked-right layout
   as Sector performance; wider screens retain the desktop arrangement.

### US3 - Interpret Daily Returns Consistently (P2)

Distinguish valid movement from missing evidence under both performance bases.

**Independent test**: Exercise matching benchmark intervals, insufficient histories, and stale/incomplete observations.

1. Entity +2% minus matching benchmark +0.5% displays relative `1.50%`.
2. Missing/invalid entity endpoints, or required relative benchmark endpoints, display uncolored `Unavailable`.
3. An older valid pair never replaces missing requested-date endpoints; valid other horizons and freshness warnings remain.
4. Touch and keyboard reveal full names and evidence explanations without navigation, lost selections, or new requests.

## Requirements

### Functional Requirements

- **FR-001**: Both named tables MUST show `1 day` immediately before `1 week`, including unavailable-only rows.
- **FR-002**: Both tables MUST retain the five longer horizons in order and preserve valid arithmetic.
  The final display caption MUST be `1 year`, with internal key `12m` unchanged.
  Each horizon MUST be independently available; missing yearly history MUST NOT suppress supported shorter horizons.
- **FR-003**: Absolute daily performance MUST be `100 * (end / start - 1)` using exact adjusted closes.
  The application MUST resolve the latest completed official session on/before the requested date and its immediate
  official predecessor, excluding incomplete sessions. Prices and observed dates MUST NOT move either endpoint.
  Missing either exact close MUST yield `Unavailable`; weekends/holidays are not trading sessions.
- **FR-004**: Daily performance MUST follow the existing basis: entity return for Absolute, entity minus
  benchmark return over identical session dates for vs S&P 500. Absolute daily performance MUST NOT require benchmark evidence.
- **FR-005**: Available returns MUST be right-aligned two-decimal percentages with readable light/dark
  gain/loss/neutral palettes, independently scaled by period and sign. In both themes, return text MUST
  meet WCAG AA contrast ratios of at least 4.5:1 for normal text and 3:1 for large text. Gain, loss,
  and neutral status MUST remain distinguishable without color.
- **FR-006**: Missing, invalid, or insufficient evidence MUST produce uncolored `Unavailable` and an
  actionable explanation accessible without hover. Fabricated zero, alternate representations, and silent Absolute fallback are prohibited.
- **FR-007**: Each row MUST use its own approved ETF or exact approved basket and preserve source,
  representation, requested/observed dates, and freshness disclosures. Every basket constituent MUST supply
  both endpoints with exact approved weights totaling 100%; no dropping, renormalization, or parent substitution.
- **FR-008**: Except for the specified caption/layout/detail changes, navigation, valid selections,
  sorting/ranking, charts, 84px thumbnails, other fields, and stock behavior MUST remain unchanged.
  Basis MUST persist across hierarchy navigation; thumbnail changes MUST NOT change returns.
  Rendering or inspecting details MUST NOT add provider/catalog requests.
- **FR-009**: Entity rows MUST preserve all nine fields. At 1440 CSS pixels, retain the wide layout.
  At 640px, stack charts above one fitting ticker/name plus six-labeled-value strip without horizontal scrolling.
  At 390px, charts MUST remain 84 CSS pixels high without clipping plotted content. Keep the strip unwrapped
  and show a visible table-local scroll cue; touch and keyboard users MUST be able to reach its final field
  by scrolling within the table. Daily and weekly values MUST stay adjacent; ordinary page content MUST NOT
  scroll horizontally.
- **FR-010**: At 390/640px, the Discovery title MUST stay left beside two right-hand rows:
  `As of` above, then `Refresh data` and theme side by side below. At 1440px, retain the
  bottom-aligned four-column title/date/refresh/theme layout. Controls MUST NOT clip or overlap;
  date limits, native actions, refresh/cache behavior, theme, and valid state MUST be preserved.
- **FR-011**: At every acceptance width, touch and keyboard MUST expose complete unabbreviated names
  and applicable source, requested/observed-date, freshness, representation, and failure explanations.
  Compact labels and hover tooltips MUST NOT be the only access. Details MUST wrap without clipping;
  opening/closing them MUST NOT navigate, clear valid selections, or fetch data.
- **FR-012**: At viewport widths up to and including 640 CSS pixels, the Sector performance
  and Industry momentum heading/control
  groups MUST keep their heading on the left beside two right-hand rows: `Thumbnail period` above
  `Performance basis`. The controls MUST NOT move below the heading or overlap it.
  Labels and all existing options MUST remain readable and touch/keyboard operable without
  page-level horizontal scrolling. Above 640px, retain the existing desktop heading/control
  arrangement, including on wider tablets. Preserve options, defaults, keys, callbacks,
  valid selections, and existing return/data-loading behavior. This group is separate from the
  Discovery title/date/refresh/theme header in FR-010.

### Key Entities

- **Performance row**: Sector/industry, approved representation, six independently available returns and evidence context.
- **Daily interval**: Requested-date completed official session and its exact predecessor; observed date is disclosure only.
- **Performance basis**: Existing Absolute or vs S&P 500 selection.

## Success Criteria

- **SC-001**: Every tested row state shows the exact six display captions and order in the UI contract;
  at 640px the ticker/name and six values share one fitting line below stacked charts.
- **SC-002**: All controlled positive, negative, zero, relative, weekend/holiday, and historical-date cases
  match expected completed-session returns to two decimal places, excluding incomplete/future observations.
- **SC-003**: Every controlled missing/invalid endpoint case shows uncolored `Unavailable`, never a fabricated return.
- **SC-004**: Before/after comparisons preserve valid longer-period values, sorting, chart choices, navigation
  and ranking/snapshot contracts. The only longer-period caption change is `12 months` to `1 year`;
  supported horizons remain visible when another lacks history.
- **SC-005**: Walkthroughs identify gaining and declining entities by adjacent daily/weekly values in either table,
  without another view or period control.
- **SC-006**: Browser acceptance passes actual 390/640/1440 CSS pixels in both themes for the header and both tables:
  readable non-overlapping controls/charts/values, zero page overflow, charts 84 CSS pixels high without clipped
  plotted content at 390px, a visible table-local scroll cue and touch/keyboard access to the final field at 390px,
  fitting strip at 640px, and preserved desktop layouts. Exercise date/calendar, refresh, theme, hierarchy/back,
  basis and thumbnail controls while preserving state/loading safeguards.
- **SC-007**: Every width/theme combination exposes full long names and unavailable explanations by touch and
  keyboard without hover or clipped details; opening/closing details preserves valid selections and adds zero requests.
- **SC-008**: In both named tables and both themes, browser checks at 390 and 640 CSS pixels show the heading
  beside the upper-right Thumbnail period row and lower-right Performance basis row.
  Every option remains accessible without clipped controls, overlap, or page-level horizontal
  scrolling; changing either control preserves existing state and calculation semantics.
  At 641 and 1440px, the existing desktop heading/control arrangement remains unchanged.
  These widths apply to this group only and do not change the row or Discovery header
  acceptance widths in SC-006.
- **SC-009**: In both themes, a browser or automated contrast check covers every foreground/background pair used
  by gain, loss, and neutral return text. Each pair meets WCAG AA contrast ratios of at least 4.5:1 for normal
  text and 3:1 for large text. Gain, loss, and neutral status remain distinguishable when color is unavailable.

## Dependencies and Evidence

[004](../004-sector-stock-explorer/spec.md) owns Discovery/navigation, [008](../008-industry-representation-tools/spec.md)
approved representations, [015](../015-dedicated-stock-lookup/spec.md) button identity, and
[006](../006-stock-table-columns/spec.md) the unchanged five-column stock table.
Constitution 4.1.0 governs affected phone/desktop usability.
[Tasks](tasks.md) retain completed IDs; [quickstart](quickstart.md) distinguishes measured history from pending acceptance.
