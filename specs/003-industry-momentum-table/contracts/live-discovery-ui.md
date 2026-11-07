# Live Discovery UI Contract

**Retained supporting contract (2026-11-02)**:
[Feature 004](../../004-sector-stock-explorer/spec.md) is the active owner after consolidation.
This path remains stable for existing references; it is not an independent feature 003 backlog.
The progressive tape/tooltip baseline and reviewed 012 membership boundary in 004 take precedence
over older fixed-depth wording below.

## Root Interface

The root retains the following tabs under 004 and
[015](../../015-dedicated-stock-lookup/spec.md), which supersedes the original two-tab limit:

1. **Discovery**
2. **Industry Deep-Dive**
3. **Yahoo Classification Preview**
4. **Find a stock**

015 owns lookup placement, while 012 retains identity and listing safeguards.
Discovery does not contain lookup controls. On 013 adoption all four workflows
consume the same pinned validated context and enforce its acquisition/permission gates.

Fundamental Grading is not rendered. The root does not expose a synthetic-fixture, snapshot,
weekly-leadership, acceptance, or provider-selection control.

## Discovery

Discovery has one live yfinance data path.

The current progressive contract shows no separate sector Ticker or industry ETF
column: the Sector/Industry buttons contain the ticker and full name. Both tapes
have nine fields and six returns under
[016's UI contract](../../016-add-daily-performance/contracts/daily-performance-ui.md),
retaining ticker evidence internally. Stock Ticker remains in the five-column table under 006.

At wide widths, the Discovery heading, **As of** date input, **Refresh data** button,
and session theme button share one bottom-aligned row, in that order, with column
weights 4:3:3:2. At 640 CSS pixels and below, the title stays on the left beside
two rows of controls: **As of** above, then **Refresh data** and the theme button
side by side below. Native controls, keyboard order, state, and callbacks remain unchanged.

| Input | Required behavior |
|---|---|
| Requested date | Uses the current US market date by default and cannot be future dated. |
| Refresh | Replaces only the relevant cached yfinance request. |
| Live response | Shows yfinance as source plus requested and observed dates. |
| Failed/incomplete response | Shows an actionable error or insufficiency state; does not show snapshots, fixtures, or another provider. |

## Industry Deep-Dive

Industry Deep-Dive reads the same activated manifest-backed reviewed regional stock CSV/hierarchy
release as Discovery under [feature 010](../../010-manifest-csv-catalogs/spec.md). It shows dated source and coverage
evidence before allowing sector, industry, member, or stock selection.

- A missing, invalid, stale, or unapproved catalog blocks member display and clears only dependent
  stock selections.
- The UI does not offer a fixture/live evidence-mode selector.
- Changing sector or industry retains only stock selections valid in the updated dated catalog.
- Catalog/review workflows require no legacy catalog database or independent JSON catalog setting.
  Exact industry-to-sector and optional sub-industry parent references determine membership.
  Altered active source identity is invalid/unavailable, never an embedded or stale catalog fallback.
