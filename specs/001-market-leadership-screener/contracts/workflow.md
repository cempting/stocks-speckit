# Three-Tab Streamlit Workflow Contract

**Design version**: `progressive-ui-v1`; planned, not implemented.

## Composition and Loads

One entrypoint creates tabs in this order:

1. **Sectors and Industries**: sector/universe controls, industry ranking and charts.
2. **Industry Stocks**: industry members, technical criteria and selection-only editor.
3. **Stock Detail**: paged stock scorecards and focused-stock chart/facts.

No separate-page navigation is required. Each tab explains its missing prerequisites;
choosing an industry gives a clear prompt to continue to Industry Stocks. The first tab's
ranking is an `st.dataframe`; selecting a row uses its stable industry ID, not its name.
Default period is five completed-session intervals; one interval is also available.

Tab bodies may execute on every rerun. Remote requests are permitted only on explicit
**Load industries**, **Load stocks**, **Load scorecards**, or scoped **Refresh** intent.
No initial full-market fundamental download, hidden-tab load or rerun-triggered retry.
Loads show requested/loaded/failed counts and progress; retries target failed requests.
Previously authorized loads produce private view records for subsequent rendering.
Their stored expiry metadata must be checked on every render, including after a
failed refresh; stale data is never labelled current.

Changing an input invalidates only dependent view results. A period/filter change using
already-loaded valid data recalculates locally; it does not demand another remote load.
When new source data is actually required, show why and enable the appropriate load action.

## Ranking and Scope

Show industry, sector, representation symbol/type, selected period, absolute percent
return, direction, rank, ending observation, source and sufficiency. Show qualification/
exposure limitations, membership date, available counts, known gaps and cache/source age.
Rank the visibly declared eligible industry scope before direction-only filtering, so
gainers/decliners views do not silently relabel their ranks. Return sort defaults descending;
ascending recomputes ranks in that declared order. Shared competition ranks use exact
unrounded returns, then name/ID for deterministic tied display. Missing evidence has no rank.

Use selected-sector union, universe constraints, direction filters and explicit unsupported
index states. Sector context never substitutes a sector's return for an industry's.
No implied breadth, composite leadership status or benchmark-relative calculation.

## Industry Stocks

Show **all available matching members**, once each, including through explicit pagination.
Display total known membership, available/loaded/failed/matching counts and dates; use
unknown rather than a made-up total. Sorting precedes paging over the whole matching set.
No silent top-N or only-first-page source fetch.

`st.data_editor` has fixed rows. Only the Boolean selection column is editable; identity,
price, cap, technical results, fundamentals, scores and index are disabled/read-only.
Reconcile returned checked rows to stable instrument IDs, maintaining valid selections
across sorting/paging. Never write edited financial cells back to canonical records.

The four technical criteria are independent toggles with shared volume parameters.
Show pass/fail/insufficient per criterion, including disabled ones where computed.
Enabled rules AND together; no rules means all available members. Report excluded/
insufficient counts separately from an empty valid match set.

## Scorecards

Load financial data for every eligible pre-technical-filter peer, not just checked rows.
A selected subset may focus the initial page, but an **All matching stocks** view remains
available without losing nonselected scorecards. Selection is not a peer filter.

For each stock, use three `st.columns` blocks with `st.metric`: Quality, Growth, Cash Flow.
Show numeric block scores on the 0-100 scale to one decimal when sufficient; otherwise
show **Insufficient** with the specific reason, not zero or a letter grade. Raw metric
values/units, periods, publication availability, valuation date and peer-valid counts
remain accessible. No overall score. Every scorecard uses the same block structure.

## Charts and State

Sector/industry/stock charts are based on their own instrument's evidence. Shade at most
the latest detected interval and draw subtle horizontal corridor boundaries by default.
Older intervals are explicitly inspectable. Adjacent metrics show dates, trading-session/
approximate calendar duration, bounds, width, median ATR, volume context, cutoff, ongoing/
completed state and truncation. No interval differs visibly from insufficient history.

Use the [data-model state transitions](../data-model.md). Tab changes/reruns preserve
valid selection. Parent/universe/criterion changes clear only invalid dependent IDs,
with a message; cached data is independent of private selections.

## Required Error and Acceptance States

Distinguish: not loaded; loading; valid empty/no matches; partial coverage; insufficient
history/facts; unsupported dataset; expired evidence; rate limit; source/validation error.
Preserve independent valid results and actionable retry context. A failed refresh never
looks like fresh success or a legitimate empty industry.

AppTest covers three stages, controlled selections, editor protection, parent invalidation,
all-stock access, source-call counts and each failure state. Use browser checks for
dataframe/editor interaction, tab visibility, chart annotations and final UI timing that
AppTest cannot establish. Do not equate server-side render success with browser acceptance.
