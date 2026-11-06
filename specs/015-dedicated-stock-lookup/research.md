# Research: Dedicated Stock Lookup

## Decisions

### Decision: Use a dedicated fourth tab

**Rationale**: The user clarified that “another page” should be a tab alongside the existing
tabs. The current root app now has Discovery, Industry Deep-Dive, Yahoo Classification Preview,
and Find a stock. Lookup is independently accessible without appearing inside Discovery.

**Alternatives considered**: Leave lookup inline in Discovery (does not meet the request); add a
standalone route (not the user's selected navigation); consolidate an existing tab (unrequested
scope change).

### Decision: Reconcile four-tab navigation with constitution 4.0.0

**Rationale**: The explicitly approved 2026-11-06 amendment replaces the fixed three-step tab
constraint with feature-defined native tab counts. FR-001 records the existing four labels and
count; the plan's pre-research and post-design checks therefore pass without an exception.
Issue [#2](https://github.com/cempting/stocks-speckit/issues/2) was verified closed on 2026-11-06.
This resolves C2 through documentation reconciliation, not another amendment or runtime change.
Keep historical T015 and record reconciliation separately as T026.

**Alternatives considered**: Retain the obsolete exception (contradicts current governance);
remove a tab or introduce routing (unnecessary behavior change); amend the constitution again
(4.0.0 already permits the approved layout).

### Decision: Relocate the current lookup behavior rather than redesign it

**Rationale**: Lookup previously inside `discovery_page.py` now lives in `stock_lookup.py`.
It resolves retained stock identities from the active catalog snapshot, requires explicit
identity and active verified listing selection, and renders existing stock detail. Preserving
that flow keeps identity, listing, and detail behavior consistent with feature 012 and avoids
duplicating domain logic.

**Alternatives considered**: Build a second search implementation or expand the lookup to
unretained symbols. Neither is required and both would widen scope.

### Decision: Keep remote loads explicit and reuse the shared catalog snapshot

**Rationale**: The current root app loads one catalog snapshot and passes it to its tabs.
Searching or rendering lookup results must not cause provider requests. Stock history and
company evidence remain available only through their current explicit actions.

**Alternatives considered**: Load history when the tab opens or when an identity is selected.
Those approaches add hidden requests and violate existing explicit-load behavior.

### Decision: Isolate lookup widget state from Discovery

**Rationale**: A separate tab needs its own query and identity/listing controls. Its session-local
state must be namespaced to avoid collisions and must be cleared or revalidated when region,
date, or catalog revision invalidates the selection.

**Alternatives considered**: Share widget keys between both tabs (invalid for concurrently
rendered tabs) or keep lookup state under Discovery-only ownership (misrepresents the new
workflow boundary).

## Repository Evidence

- `src/market_leadership/app.py` registers all four tabs and loads the catalog snapshot once.
- `src/market_leadership/ui/workflows/stock_lookup.py` owns lookup, exact identity/listing
  selection, context revalidation, and explicit detail/history actions; Discovery no longer
  renders inline lookup.
- `tests/app/test_stock_lookup.py` verifies ambiguous identity selection, listing selection, and
  no remote prefetch for identities without verified listings.
- `tests/app/test_stock_detail.py` covers stock-detail behavior and stock-tape selection.
- `specs/004-sector-stock-explorer/spec.md` assigns root navigation and Discovery behavior;
  `specs/012-stock-industry-memberships/spec.md` defines retained identity lookup and listing
  safeguards. This feature supersedes only their within-Discovery placement/two-page assumptions.

## Button Presentation Research (2026-11-06)

### Decision: Reuse the shared native entity-button renderer

**Rationale**: `src/market_leadership/ui/components/progressive_tape.py` already renders sector,
industry, and stock buttons through `_render_visual_tape`. Its `_entity_button_label` escapes
literal Markdown and uses a bold ticker followed by a hard line break and the full name.
Existing styles target only `tape_entity_` keyed containers: 1.5rem ticker and 0.75rem name,
automatic height, normal whitespace, and wrapping even for unbroken names. Reuse this
implementation; no custom component or new widget identity/callback is required.

**Alternatives considered**: Separate renderers per view (duplicates logic); two-paragraph
labels (unnecessary churn); raw HTML buttons/custom components (extra event/state and
accessibility complexity); global CSS (alters unrelated controls).

### Decision: Display only existing ticker evidence

**Rationale**: Sector/industry frames already supply `Ticker`/`ETF`, full names, stable node IDs,
and status/representation evidence. Use the existing symbol when available. Convert missing,
empty, unavailable, uncovered, and basket-only ticker values to `No ticker` for the label only.
Keep distinct statuses and representation details in the existing tooltip; a basket is not
an ETF. Stock buttons retain the existing listing ticker or explicit unresolved-placeholder
state. No provider lookup, synthetic ticker, internal-ID substitution, or model change is
necessary.

**Alternatives considered**: Blank first lines (rejected during clarification); internal IDs
(not tickers); fetching symbols while rendering (changes acquisition and adds hidden requests).

### Decision: Hide redundant entity ticker columns without deleting evidence

The user approved removing the sector Ticker and industry ETF columns because
the entity buttons already display those values. Keep the existing frame fields
and hide only their visible cells/headings in the shared tape renderer. This
preserves ticker/source identity, chart inputs, tooltips, navigation and loading.
Stock Ticker remains visible under 006's unchanged five-column contract.
Removing fields upstream would break button evidence and is unnecessary.

### Decision: Validate CSS in a real browser, not just label tests

**Rationale**: Streamlit supports Markdown labels and keyed containers, but inner Markdown
DOM structure is not a guaranteed public styling API. AppTest proves label content, tooltips,
stable selection, and no-prefetch behavior; browser computed styles and geometry prove
the >=2 ratio and unclipped wrapping. Repeat browser checks on Streamlit upgrades. Current
lockfile: 1.66.1; declared range: `>=1.50,<2`. Checks at selected versions are not proof for
every future version in the range.

**Alternatives considered**: CSS string assertions alone (do not prove rendering); screenshots
alone (do not measure ratio); adding a component, dependency, or version pin without a failure
(unnecessary for this planning change).

**Public sources**:

- [st.button API](https://docs.streamlit.io/develop/api-reference/widgets/st.button):
  supported label Markdown, native interaction, and keyed styling.
- [st.html API](https://docs.streamlit.io/develop/api-reference/text/st.html):
  existing CSS-only style injection without executing catalog text as HTML.
- [Streamlit 1.50 Markdown renderer](https://github.com/streamlit/streamlit/blob/1.50.0/frontend/lib/src/components/shared/StreamlitMarkdown/StreamlitMarkdown.tsx)
  and [1.66 renderer](https://github.com/streamlit/streamlit/blob/1.66.0/frontend/lib/src/components/shared/StreamlitMarkdown/StreamlitMarkdown.tsx):
  label-rendering internals, not a stable application contract.

No unresolved research questions remain. Previously recorded implementation/browser results
remain in `quickstart.md`; this planning pass does not claim to rerun them.
