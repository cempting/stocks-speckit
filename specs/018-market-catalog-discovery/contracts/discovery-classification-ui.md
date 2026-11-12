# Discovery Classification and ETF UI Contract

## Classification selection

- Keep the existing root tabs, labels, and navigation; add no new route or root tab.
- Use the active catalog scopes for the selected region and as-of date.
- When one classification is active, preserve the current no-extra-selection workflow.
- When multiple classifications are active, require an explicit choice with a clear human-readable
  label and exact stable scope. Never choose by manifest order, identifier order, or naming
  heuristic.
- Namespace classification selection separately in Discovery and Industry Deep-Dive. When it
  changes, clear only the selected category path and other dependent selections.

## Hierarchy navigation

- Discovery displays only direct reviewed children of the selected node.
- Sector selection displays its active industries; industry selection displays active
  sub-industries when present.
- A custom theme classification uses its root sector-level theme nodes. It does not expose
  industry or sub-industry rows unless those nodes are explicitly present in that scope.
- Stable IDs and exact classification scope drive lookups; display-name equality is never used to
  join nodes.
- Retain empty nodes and show a specific not-covered/unavailable reason rather than substituting a
  parent ETF.

## ETF options and history

- Show every active approved ETF mapping for each node as a distinct option with ticker/name and
  its own history/performance state.
- Do not select one mapping by file order, ticker sort, name, popularity, or implicit fallback.
- Fetch only distinct `ProviderSymbol` values needed for visible nodes and configured benchmarks
  through the current yFinance provider. A shared fetched symbol may serve several mapping rows,
  but each mapping retains its exact identity and approval evidence.
- Preserve current adjusted daily close/volume semantics and supported comparison periods.
- Distinguish no approved mapping, invalid/unverified listing, no returned history, insufficient
  history, and request failure. A failed symbol does not hide valid partial results; batch-level
  failures remain explicit.
- Do not infer contained-stock membership from an ETF or holdings disclosure.

## State and responsive behavior

- Use namespaced Streamlit session-state keys and exact classification/node identifiers.
- Cache only provider responses and deterministic results using the existing request/catalog
  identity inputs. Catalog invalidation must not reuse stale success-shaped data.
- Validate the affected workflow in a browser at 1440px and 390px widths. Controls, category
  labels, per-ETF status, and performance must be usable without clipping, overlap, or
  page-level horizontal scrolling.
