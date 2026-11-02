# Research: Company Risk Evidence

**Date**: 2026-11-01 | **Feature**: [spec.md](./spec.md)

## Evidence and confidence

Inspection confirmed the existing financial domain/reader/cache, stock-detail/root workflows,
and peer adapter under `src/market_leadership/`. The root is two tabs; standalone matrix
AppTests do not prove live root integration. Retired independent grading actions stay retired.

Public references include [yfinance docs](https://ranaroussi.github.io/yfinance/),
[its README](https://github.com/ranaroussi/yfinance),
[TradingView policies](https://www.tradingview.com/policies/), and
[SEC documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
Direct SEC documentation access returned 403; actual deployment access is unverified.
Context7 authentication was previously unavailable; credentials were not changed or retried.
No company dataset was fetched.

Reject research overclaims: universal provider history depth or capex signs, guaranteed remedies
for 403, Finviz permission inferred from an upsell page, and universal cross-company RPO
comparability. Documentation/source selection is not approval to collect or publish data.

## R1. Current detail, not a legacy route

- **Decision**: Controls in Discovery stock detail; shared risk component plus existing matrix.
- **Rationale**: Detail lacks raw cash/research, while the matrix already supplies exact eight
  slots/history. The legacy loader cannot authorize manifest-backed live requests.
- **Alternatives considered**: Another root tab, resurrected grading workflow, new tape columns.

## R2. Single financial reader with retained metadata

- **Decision**: Extend the existing one-ticker acquisition with optional immutable profile,
  provenance and safe component context. Reuse `info`, `quarterly_financials`,
  `quarterly_cashflow`, `quarterly_balance_sheet` and acquired cohort bundles.
- **Rationale**: Existing aliases include OCF/capex/FCF, but most metadata is discarded.
  The [Ticker reference](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html)
  does not guarantee complete histories or verified fact publication vintages.
- **Alternatives considered**: Another Yahoo HTTP client, SEC score fallback, Finviz/TradingView
  pooling, unverified universal four-quarter cap or fabricated missing quarters.

## R3. Permissions are independent reviewed capabilities

- **Decision**: Versioned source assessments separately authorize collection, normalized display,
  normalized retention and raw retention. Unknown/expired/revoked uses block even cached display.
  Production candidates begin unapproved.
- **Rationale**: Software licensing is not Yahoo data licensing. TradingView restricts relevant
  processing; Finviz terms were not verified. A CLI records rights evidence, not rights grants.
- **Alternatives considered**: Accessibility or environment boolean as permission; optional
  Wikipedia integration adds no necessary capability and is deferred.

## R4. Dated identity rather than ticker/name joins

- **Decision**: Capture StockRow/primary Listing IDs, source symbol/exchange, revision and dates;
  validate returned profile before attachment against an independent reviewed dated
  listing-to-issuer reference. Require corroborated regulator-issued issuer identity or verified
  issuer-controlled domain and no conflicts; ticker/exchange/name/currency agreement alone is
  insufficient. A conflicting same-label successor is a mismatch; absent/failed/inconclusive
  profiles or missing independent references remain unresolved. Keep company ID nullable and
  CIK/issuer key absent on the valid domain route. Enforce the gate on fresh, cache/cohort and
  archival attachment without turning a predecessor capture into successor evidence.
  SEC/issuer research requires a separately reviewed CIK/domain binding and permissions.
- **Rationale**: MembershipEntry loses listing ID; original snapshot retains it. ADRs, share
  classes and recycled tickers need verified association, not name or currency equality.
- **Alternatives considered**: Synthetic company IDs, broad issuer searches, sharing evidence
  across unverified similarly named listings, ticker/exchange-only continuity, or requiring
  a regulator ID for every financial association despite available verified domain evidence.

## R5. Observation is not historical publication

- **Decision**: Explicit current mode labels UTC retrieval knowledge time. Historical mode uses
  dated captured snapshots only, observed no later than the requested UTC day's end.
- **Rationale**: Reader rejects historical live cutoffs; peer adapter deliberately lacks
  verified vintages. Filing dates cannot repair Yahoo observation vintages.
- **Alternatives considered**: Period end as publication date, relaxing the historical guard,
  or newer filings silently backfilling earlier scores.

## R6. Cash warning independent of weights

- **Decision**: OCF/FCF gaps, unloaded/errors/stale/incomparable evidence produce gap warnings;
  zero/negative OCF and negative FCF produce dated cash-generation concerns. Both may coexist.
- **Rationale**: Missing evidence does not prove distress; negative FCF may reflect investment.
  Partial failures do not erase unaffected valid facts.
- **Alternatives considered**: Cash reweighting, missing-to-zero, automatic buy/sell/risk ratings.

## R7. Definitions, signs and periods

- **Decision**: Preserve source-supplied FCF and definition status. Derive missing FCF only from
  finite aligned OCF/capex with verified outflow convention:
  `FCF = OCF - positive_capex_outflow`. Negative signed outflow gives equivalent OCF plus capex.
  Reject unqualified YTD/cumulative contexts; retain unknown start/publication dates.
- **Rationale**: Existing metric formula is preserved for accepted normalized inputs.
  Source-supplied need not mean issuer-reported.
- **Alternatives considered**: Blind sign flipping, assumed positive outflow, zero capex defaults,
  mixed period/currency/unit inputs or invented quarter starts.

## R8. Explicit retrieval and reporting freshness

- **Decision**: Financial TTL 3,600 seconds, research TTL 86,400 seconds; quarterly reporting
  older than 135 days is stale, annual research older than 450 days is stale. A known newer
  statement without matching cash creates a gap immediately. Evaluate current freshness at
  render time. Historical captures remain explicitly archival: assess reporting age against the
  historical date, not today's date, and do not apply a live cache TTL as an archive deletion rule.
- **Rationale**: New retrieval of old data is not fresh reporting. These are conservative product
  policies allowing reporting lag, not legal filing deadlines.
- **Alternatives considered**: TTL-only freshness, older positive cash as current, speculative
  issuer-specific deadline configuration.

## R9. Bounded disclosure collection

- **Decision**: Approved CIK -> documented submissions JSON
  `https://data.sec.gov/submissions/CIK{ten_digit_cik}.json` -> eligible annual 10-K/20-F and
  quarterly 10-Q accession documents. Approved Company Facts concepts may supply accession-linked
  order/RPO research only. Issuer URLs require verified domains/registered documents.
- **Rationale**: Submission metadata is not narrative; numeric facts do not imply universal
  backlog/business coverage. RPO definitions/coverage remain issuer-qualified.
- **Alternatives considered**: Mandatory undocumented search endpoints, market-wide crawl,
  blanket standardization claims, alternative-host retries to evade denial.
  Publisher-compliant contact/access verification remains a deployment gate, not a 403 cure.

## R10. Honest structured extraction and reviewed claims

- **Decision**: Exact reviewed concept/context/unit/table mappings retain locators/revisions.
  Permitted structured profiles and reviewed short factual summaries populate business fields.
  Competitive claims stay attributed. Human interpretation enters through reviewed structured
  claims/imports, not machine-invented summaries.
- **Rationale**: Arbitrary prose cannot safely become revenue model or moat via keywords.
  Accessible but unmapped content is unsupported structure, not "not disclosed".
- **Alternatives considered**: LLM, report reproduction, generic regex moat ratings, guaranteed
  complete coverage across the market. Useful partial evidence plus review is more truthful.

## R11. Sidecar history and scoped cache

- **Decision**: File-only assessments/bindings and immutable hashed normalized snapshots with
  atomic latest pointers. Preserve dated partial/error outcomes. Failures are not cached
  successes and older good evidence is history, not silent current fallback.
- **Rationale**: Retained provenance requires persistence, but catalog/SQL mutation is unrelated.
  Assessment/binding/content fingerprints isolate caches. Raw retention needs separate permission.
- **Alternatives considered**: Shared session-state store, catalog CSV edits, new database/service,
  unlimited raw archive, broad cache clears.

All design choices are resolved; rights/access, extraction coverage, persistence and human
measurement remain explicit operational/implementation checks.
