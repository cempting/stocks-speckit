# Feature Specification: Dedicated Stock Lookup

**Feature Branch**: `015-dedicated-stock-lookup`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "why is there a find a stock feature in teh discovery page? Pleas extract the \"Find a stock\" feature to another page ." The user clarified that the destination should be a tab.

## Clarifications

**Presentation owner**: [016](../016-add-daily-performance/spec.md) defines current entity-tape
captions, daily evidence, responsive layout and complete non-hover details.
Historical 015 validation remains recorded separately from that feature's pending acceptance.

### Session 2026-11-06

- Q: How should cross-feature documentation be consolidated after moving stock lookup? → A: Rebuild 001's current executable backlog while preserving completed IDs and recording retired work; supersede 002's unbuilt multi-sector increment; reconcile 013 with all current tabs and one shared service context; defer lookup placement to 015 while preserving 012 identity safeguards; update pending paths to the shared-package layout. These are documentation changes, not implementation completion.
- Q: Should the two-line button requirements be added to the active Dedicated Stock Lookup specification, even though they also affect Discovery views? → A: Extend this specification to cover the sector performance table, industry momentum, and stock list view.
- Q: What should the first line show for a sector or industry that has no associated ETF ticker? → A: Use the associated ETF ticker when available; otherwise show "No ticker" above the full name.
- Q: How large should the ticker be compared with the full name below it? → A: The ticker font size is at least twice the name's font size.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a Stock on Its Own Page (Priority: P1)

As a user looking for a particular stock, I want to use a dedicated Find a stock page rather than search within Discovery, so stock lookup is distinct from exploring the market.

**Why this priority**: The requested change is to separate stock lookup from the Discovery workflow while keeping the lookup easy to find.

**Independent Test**: Open the Find a stock page from the application's primary navigation, search for a retained stock identity, and verify that the matching identity can be selected without opening Discovery.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** the user navigates to Find a stock, **Then** the stock search and selection workflow is available on that page.
2. **Given** the user opens Discovery, **When** the page is displayed, **Then** it no longer contains the Find a stock search and lookup workflow, and its remaining Discovery functions continue to work.
3. **Given** the user navigates between Find a stock and Discovery, **When** either page is opened, **Then** each page presents only its own workflow and the selected page is reachable through the primary navigation.
4. **Given** the sector performance table, industry momentum, or stock list view is displayed, **When** an entity button is rendered, **Then** its ticker appears above its full unabbreviated name at least twice the name's font size, and a long name wraps without truncation.
5. **Given** a sector or industry has no associated ETF ticker, **When** its button is rendered, **Then** "No ticker" appears above its full name using the same font-size hierarchy.
6. **Given** an entity button in any of the three views, **When** the user activates it, **Then** its selection and navigation result is unchanged by the presentation update.

### User Story 2 - Verify the Stock Before Opening Its Detail (Priority: P1)

As a user searching for a stock, I want to distinguish the exact stock identity and an active verified listing before opening its detail, so the app does not load data for an ambiguous or unverified listing.

**Why this priority**: A search result can have multiple listings or no active listing; users must be able to confirm what they are opening.

**Independent Test**: Search for identities with one, multiple, and no active verified stock listings; verify identity selection, listing disambiguation, and that no remote history request is made without an eligible listing and an explicit load action.

**Acceptance Scenarios**:

1. **Given** a search matches multiple stock identities, **When** the user chooses one, **Then** the app requires an exact identity selection before opening its detail.
2. **Given** the selected identity has active verified stock listings, **When** the user opens its detail, **Then** the user can choose the exact active listing and sees detail for that selection.
3. **Given** the selected identity has no active verified stock listing for the chosen date, **When** the user opens its detail, **Then** the limitation is explained and no remote listing-history request is made.
4. **Given** the user has opened a valid stock detail, **When** history is requested, **Then** history is loaded only through an explicit user action and failures or incomplete history remain visible.

### User Story 3 - Find Retained Stocks Without an Industry Assignment (Priority: P2)

As a user looking for a retained stock that has no active industry membership, I want the dedicated lookup to find it without implying a classification, so identity lookup remains useful without inventing market relationships.

**Why this priority**: Existing lookup supports identified instruments without active memberships; moving the workflow should preserve this ability.

**Independent Test**: Search for a retained stock identity with no active industry membership, select an active verified listing where available, and verify the detail opens without assigning an industry.

**Acceptance Scenarios**:

1. **Given** a retained stock identity has no active industry membership, **When** the user searches for it on Find a stock, **Then** it remains discoverable and its detail is available subject to listing verification.
2. **Given** a query has no retained identity matches, **When** the user searches, **Then** the page explains that no retained stock identity matches and does not show stale results.

### Edge Cases

- Long button names wrap onto additional lines below the ticker; they are not abbreviated, truncated, or replaced with an ellipsis.
- A sector or industry has no associated ETF ticker; its button shows "No ticker" above its full name and preserves its existing selection behavior.
- The selected region or date changes after a query; identity, listing, detail, and loaded-history selections that are no longer valid are cleared or revalidated.
- The catalog revision changes while the page is open; an earlier selection is not silently treated as valid under the new revision.
- A selected stock has several active verified listings; the user must choose one exact listing.
- No active verified listing is available; identity details may be shown only under existing rules, and remote listing history remains unavailable.
- A history request fails or returns incomplete coverage; the page identifies the failure or gap and does not present it as complete current history.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST expose exactly four root tabs: Discovery, Industry Deep-Dive, Yahoo Classification Preview, and Find a stock. Find a stock MUST remain separate from Discovery, using constitution 4.1.0's native-tab architecture.
- **FR-002**: The Discovery page MUST NOT render the Find a stock search, identity-selection, listing-selection, or lookup-detail workflow.
- **FR-003**: The Find a stock page MUST search retained stock identities in the selected region and for the selected date, and MUST provide an explicit no-match state.
- **FR-004**: The page MUST require the user to select an exact stock identity when a query has multiple matches before opening its detail.
- **FR-005**: The page MUST allow the user to select only an active, verified stock listing for the selected date before requesting remote listing history.
- **FR-006**: If no active verified listing is available, the page MUST explain the limitation and MUST NOT request remote listing history.
- **FR-007**: The page MUST preserve lookup access to retained stock identities without active industry memberships, without assigning or implying an industry membership.
- **FR-008**: Stock history MUST be requested only after an explicit user action; refresh MUST remain explicit, and request failures or incomplete history MUST be visible.
- **FR-009**: Changes to region, date, or catalog revision MUST cause dependent selections and history to be revalidated; invalid prior selections MUST NOT appear current.
- **FR-010**: The relocation MUST preserve existing Discovery behavior unrelated to stock lookup and MUST NOT add a market-data source or broaden the existing lookup's retained-identity scope.
  Lookup placement is owned by this feature; identity and listing safeguards remain owned by 012.
  On adoption of 013, lookup MUST use the same validated context and permission gates as the other
  root workflows, not a separate local catalog authority.
- **FR-011**: Clickable entity buttons in sector performance, industry momentum and stock lists MUST show ticker above the full unabbreviated name, at least twice its font size. Stock names MUST wrap without truncation. Compact sector/industry labels MUST provide complete wrapped touch/keyboard details under [016](../016-add-daily-performance/spec.md); hover alone is insufficient.
- **FR-012**: The button presentation change MUST preserve existing selection and navigation behavior in all three views.
- **FR-013**: Sector and industry buttons MUST use the associated ETF ticker on the first line when available, or the explicit label "No ticker" otherwise; they MUST NOT invent a ticker or substitute an internal identifier.
- **FR-014**: Sector performance MUST omit its separate Ticker column and Industry momentum its separate ETF column. Both entity tapes MUST retain nine fields: two charts, Sector/Industry button and the six returns defined by [016](../016-add-daily-performance/contracts/daily-performance-ui.md). Keep ticker/ETF evidence internally for buttons/charts/source identity; preserve the five-column stock table including Ticker.

### Key Entities *(include if feature involves data)*

- **Stock identity**: A retained instrument identity, including its stable identifier and associated name and region.
- **Stock listing**: A verified, time-bounded listing associated with a stock identity, including the listing's provider symbol and exchange details needed to identify it.
- **Lookup context**: The region, selected date, catalog revision, identity, and optional listing that determine whether a lookup result and its history remain valid.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The primary navigation exposes a dedicated Find a stock page, and the stock lookup workflow is absent from Discovery.
- **SC-002**: In all controlled search cases, users can distinguish matching identities, choose an exact eligible listing, and open only the requested stock detail.
- **SC-003**: In all controlled cases without an active verified listing, no remote listing-history request occurs.
- **SC-004**: Search results include retained stocks without active industry memberships and do not create or imply an industry membership.
- **SC-005**: Existing Discovery workflows unrelated to stock lookup pass their current regression checks after the relocation.
- **SC-006**: All three views show ticker (or "No ticker") above name at a font-size ratio of at least 2:1; full stock names wrap visibly and compact entity names are completely readable through touch/keyboard details. Selection retains its existing result.
- **SC-007**: Controlled sector/industry renderings retain nine fields with no separate Ticker/ETF column; buttons show ticker or "No ticker", selections retain exact node IDs, and stock tables retain five columns.

## Assumptions

- “Another page” means a separate Find a stock tab alongside the existing tabs, rather than a panel within Discovery.
- The move relocates the existing retained-stock identity lookup and its detail/history interactions; it does not introduce new search sources, broaden the catalog, or change identity, listing verification, or history-loading rules.
- This feature also includes the requested button presentation change across the sector performance table, industry momentum, and stock list view, plus removal of the now-redundant sector Ticker and industry ETF columns; it does not otherwise redesign those views.
- This feature supersedes the exact two-page navigation limit in 004 FR-033 only to the extent required to add Find a stock as a separate page, and relocates the within-Discovery lookup described by 012 FR-023/FR-024. Other Discovery, Industry Deep-Dive, and stock-identity requirements remain in effect.
