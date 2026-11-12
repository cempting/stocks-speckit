# Research: US Industry and Theme ETF Discovery

## 1. Supplied files and publication readiness

**Decision**: Treat `docs/markets/US/` as candidate authoring data and publish it only through the
existing manifest-managed release workflow after evidence review. Do not load the folder directly,
auto-scan it at runtime, or mark its existing review fields approved.

**Rationale**: The files are structurally compatible with current hierarchy, ETF listing, and
representation roles. A local cross-file check found 65 hierarchy rows, 86 unique listing IDs and
provider symbols, and 98 mappings (47 sector, 28 industry, 23 sub-industry); every current mapping
reference resolved to a supplied node and listing. The data contains two active-looking custom
scopes (`MY_TAXONOMY` and `MY_THEMES`), uses `source-1` in every file, and has no populated
`CandidateReviewId` values. It includes no manifest, audit, benchmark, or stock artifact. The
current default `.data/catalog/CURRENT.json` is absent in this checkout. Valid references and
nonempty evidence fields do not establish that sources, suitability, or approvals exist.

The implemented release-v2 schema already has custom classification metadata and the
`sector_etfs`, `industry_etfs`, and `sub_industry_etfs` artifact roles. It also requires a complete
release, including one stock artifact per active region, benchmarks, and audit. Use those existing
requirements; bring forward or obtain the missing artifacts and evidence rather than weakening the
contract.

**Alternatives considered**:

- Read `docs/markets/US/` as an application default: rejected because it bypasses manifest
  integrity, source authorization, coherent publication, and review.
- Generate source approvals from the CSV values: rejected because catalog validation must not
  manufacture review decisions.
- Introduce a new release-v3 schema: rejected because v2 already supports custom classifications
  and these supplied rows fit its ETF mapping roles.

## 2. Multiple classifications in one region

**Decision**: Add a typed way to enumerate active scopes for a region/date and require explicit
scope selection when more than one exists. Keep the existing single-scope behavior for legacy
callers and one-classification releases. Update Discovery and Industry Deep-Dive so both can
operate safely on multi-classification US releases.

**Rationale**: `CatalogSnapshot.scope_on(region, date)` currently raises
`unavailable_classification` unless exactly one scope is active. The supplied hierarchy has two
simultaneous classifications for `US`, so existing region-only callers cannot consume it without
an explicit scope. The release-v2 model supports multiple custom classifications, so the gap is
scope resolution, not the file format. Session keys must include the selected classification and
clear dependent category selections when it changes.

**Alternatives considered**:

- Pick the first classification or infer a default from its name: rejected as order-dependent and
  potentially misleading.
- Put themes in a different region or merge them into the industry hierarchy: rejected because
  region and classification identities are already explicit in the supplied files.
- Change `scope_on` to silently return a different scope: rejected because it would break the
  invariant existing callers rely on.

## 3. Multiple ETF representations for one node

**Decision**: Project all active, approved ETF mappings for each node into Discovery and render
each listing as a distinct option with its own performance and history state. Deduplicate provider
requests by exact provider symbol, but preserve each mapping/listing identity in the result.

**Rationale**: `snapshot_representation_worklist` currently selects `(eligible_etfs or etfs)[0]`.
That silently hides alternatives when a node has multiple mappings, as several supplied nodes do.
The feature requirement explicitly rules out selecting based on file order or ticker sorting.
Sorting labels for stable presentation is acceptable only if all options remain visible.

**Alternatives considered**:

- Keep only the first mapping: rejected because it hides reviewed alternatives and depends on row
  order.
- Require one mapping per node and discard the others: rejected because the supplied research
  includes legitimate alternative ETFs and the specification requires them to be distinguishable.
- Choose a mapping by ticker order: rejected because lexical order is not a suitability decision.

## 4. yFinance symbol and history behavior

**Decision**: Keep the current yFinance provider and `ProviderSymbol` as the only request identity.
Use the existing batch request, cache, adjusted daily price/volume output, and date normalization.
Add deterministic offline tests for partial symbol results and an opt-in live validation that
reports each ETF symbol and date coverage.

**Rationale**: The current `YFinanceProvider` calls `yfinance.download` with the requested ticker
list, daily interval, adjusted prices, and returns canonical `close`/`volume` frames. The official
[`download` reference](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)
documents list-valued tickers, start-inclusive/end-exclusive date parameters, and daily interval
support. The provider already handles multi-index responses and normalizes missing symbols to
empty history. The existing live test is disabled unless `RUN_LIVE_MARKET_DATA=1` and currently
checks only SPY/XLF; it does not prove that the 86 new provider symbols work.

**Alternatives considered**:

- Replace yFinance or fall back silently to another provider: rejected by the project constitution.
- Use display tickers when provider symbols are absent: rejected because exchange suffixes and
  identity can differ.
- Call the provider once per visible ETF: rejected as wasteful; the existing batch interface
  already supports the required symbols.
- Claim all source symbols are live-verified: rejected because no live fetch of the 86 candidate
  symbols has been performed.

**Use-rights note**: yfinance's [official documentation](https://ranaroussi.github.io/yfinance/)
states it is unaffiliated with Yahoo, intended for research and educational purposes, and directs
users to Yahoo's terms for data rights. Local research checks do not grant publication or hosting
rights; a provider-terms review remains a deployment gate under the project constitution.

## 5. Hierarchy and stock membership

**Decision**: Keep the existing three supported node types (`sector`, `industry`,
`sub_industry`) and use explicit parent/sector relationships. Show a child level only under its
selected parent. Keep ETF performance and stock membership as separate evidence.

**Rationale**: The supplied theme classification uses sector-level theme nodes; the industry
classification has sector, industry, and sub-industry nodes. No new theme node type is needed. The
source folder has no stock artifact and an ETF mapping does not prove issuer or stock membership.
Catalog-v2 still requires a stock artifact per active region, so a complete reviewed release must
retain or supply that artifact; an intentionally empty membership artifact may only be used when
the release reviewer explicitly confirms no membership coverage.

**Alternatives considered**:

- Infer membership from ETF names or holdings: rejected because ETF exposure is not a reviewed
  stock-to-industry assertion.
- Add a generic theme node type: rejected because existing custom classifications and sector-level
  theme nodes already represent the input.
- Flatten industries and sub-industries into one child list: rejected because it loses the
  supplied parent structure and can mix hierarchy levels.
