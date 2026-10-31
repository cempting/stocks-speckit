# Research: Sector-to-Stock Explorer

> **2026-10-31 alignment:** The SQLite/initialization/seed decisions below are historical
> rationale. [Feature 010](../010-manifest-csv-catalogs/spec.md) supersedes them with file-only
> manifest authority and one stock CSV per region. Source coverage, listing verification,
> conflict reporting, and no inferred membership remain applicable. Existing local inputs
> remain candidates, not approved seeds; do not replay database setup as the new architecture.

## Decisions

### 1. Extend the existing two-tab Streamlit application

**Decision**: Keep the current `Discovery` and `Industry Deep-Dive` root tabs. Implement sector,
industry, and stock tapes plus the selected-stock detail view within the Discovery journey.

**Rationale**: The current entrypoint already uses the two-tab composition, and the latest
live-discovery specification explicitly excludes a separate Fundamental Grading tab. A detail
view in the existing journey satisfies the new behavior without reintroducing a competing route
or changing the root shell.

**Alternatives considered**: Restore the older three-tab screen; add a separate routed page.
Both expand or replace the current shell without a requirement for another top-level workflow.

### 2. Preserve stable identities and dependent selection state

**Decision**: Key selections and detail handoff by stable sector, industry, and instrument IDs.
Keep them in namespaced session-local state; clear only dependent IDs invalidated by a parent
change.

**Rationale**: This follows the current membership and selection models and prevents ticker/name
changes or duplicate display names from opening the wrong stock.

**Alternatives considered**: Use display names or tickers as selection keys; reset every selection
on each change. These can misidentify entities or discard valid user context.

### 3. Separate persistent membership from live market evidence

**Decision**: Store reviewed region, classification, sector, industry, stock, listing, and
membership records in a local SQLite database. Keep yfinance as the live price-history provider;
after a valid region and industry are selected, request history only for their verified listings.
Preserve source, coverage, approval, and freshness information with records and evidence.

**Rationale**: The current app separates provider/cache logic from membership validation, but its
JSON catalog is a required runtime configuration and there is no persistent database. Python's
standard `sqlite3` provides the requested local database without a new dependency or service. The
provider supports batched history without requesting the entire region before selection.

**Alternatives considered**: Keep membership only in an environment-selected JSON file; add a
database service or ORM dependency; infer members from an industry ETF. The first preserves the
current setup failure, the second adds operational/dependency cost without a present need, and the
third does not establish verified membership.

### 4. Use reviewed local data as classification authority

**Decision**: Provide a CLI for database initialization, validation, and reviewed local-file
import. Live refresh is permitted only through the application's single selected live provider
after its US coverage, terms, and display rights are approved. Local reviewed files remain
authoritative for region, sector, industry, stock identity, and membership. Report live-source
discrepancies without overwriting those fields.

**Rationale**: This supports repeatable database setup while retaining explicit data lineage and
the project's provider-rights constraints. It also avoids silently preferring one overlapping
source when classifications disagree.

**Alternatives considered**: Hard-code list membership or source priority in application code;
allow live refresh to overwrite classifications; add a second or unreviewed runtime provider.
These approaches reintroduce hard-coded configuration, conflict with the one-provider constraint,
or can misstate coverage and classification.

### 5. Treat US as one region and preserve distinct listings

**Decision**: Combine US records into one region. Store an underlying security once by stable
instrument identity and model each exchange/ticker as a separate listing. Keep classification
systems scoped to regions; do not assume GICS.

**Rationale**: The user wants one cross-exchange US discovery view, while a security can have
multiple listings and future regions can use different taxonomies. Identity must not depend on
display name or ticker alone.

**Alternatives considered**: Make NYSE, Nasdaq, and each index a separate user-selectable region;
deduplicate by company name or ticker. These options split the requested US view or can merge
different securities.

### 6. Use the existing 001 peer-score contract, not raw metrics as scores

**Decision**: Implement and display the three 0–100 peer-percentile block scores—Quality, Growth,
and Cash Flow—according to [fundamental-scoring.md](../001-market-leadership-screener/contracts/fundamental-scoring.md).
The chosen score is computed from its two defined metrics only when both are valid; each metric
requires at least five valid peers. Do not define an overall score.

**Rationale**: The current `FundamentalScorecard` contains eight raw quarterly metrics in three
groups, but no numeric group scores. The earlier scoring contract supplies the exact formulas,
cohort rules, sufficiency threshold, tie behavior, and scale. The user selected the three peer
scores for this feature.

**Alternatives considered**: Treat the current eight raw metrics as three scores; create a new
aggregate; leave all score cells permanently unavailable. The first mislabels raw evidence, the
second invents scoring, and the third fails the selected requirement.

### 7. Load financial evidence only on explicit user intent

**Decision**: Do not fetch fundamentals on a normal tape render, selection, sort, or rerun. An
explicit score-load action loads the eligible industry peer cohort, reuses successful cached
bundles, and reports per-stock failures and score insufficiency.

**Rationale**: The existing financial workflow uses explicit load actions and its score formulas
depend on the complete unfiltered peer cohort. Automatic financial retrieval for every displayed
row would waste provider requests and obscure failures.

**Alternatives considered**: Fetch financial data for every stock as soon as the industry is
selected; calculate scores from selected/displayed rows. The first causes implicit bulk requests;
the second makes peer scores change when UI filtering changes.

### 8. Fail closed for unavailable point-in-time score evidence

**Decision**: Apply the scoring contract's cutoff, publication-availability, unit, period, and
denominator requirements. If the provider cannot establish required evidence, show the score as
insufficient/unavailable; do not use current facts for a historical cutoff or substitute another
security's data.

**Rationale**: The existing yfinance reader rejects unsupported historical live cutoffs and its
current profile/statement data do not establish all historical publication vintages. Relaxing the
contract would make historical peer scores misleading.

**Alternatives considered**: Assume report-period dates equal publication dates; use today's
profile or market cap for a historical date. Neither is supported by verified evidence.

### 9. Keep chart previews tied to each row's own history

**Decision**: Render each sector, industry, and stock thumbnail from that entity's own validated
price history. Each price thumbnail includes the 50-session simple moving average when supported;
an immediately adjacent volume thumbnail colors each bar by close-to-close direction (green up,
red down, neutral unchanged or unknown). Reuse already-loaded sector and industry history;
request member histories only for the active industry. The detail chart retains its price/volume
view and 50-/150-session averages.

**Rationale**: This uses existing chart logic and makes unavailable histories explicit without
cross-entity substitution. The current dataframe chart-column API sets one color per column, so
it cannot represent direction-dependent colors within one volume sparkline. Use compact
row-specific charts that support per-observation colors and verify their placement in the actual
Streamlit view. Green/red indicate price direction, not verified buyer/seller identities.

**Alternatives considered**: Use the sector chart for its industries or ETF representation charts
for their member stocks. These would misrepresent the row's entity.

### 10. Gate membership-source onboarding on review

**Decision**: Do not select or implement a live membership provider yet. Require evidence for US
coverage, classification taxonomy, identity and effective-date semantics, refresh behavior, terms,
and display/redistribution rights before enabling one source. Import reviewed local files through
the database tooling and report live-source differences without overwriting local classifications.

**Rationale**: The source assessment found no candidate confirmed to meet the full coverage,
history, and rights requirements. Yahoo/yfinance terms are not evidence of permission for this
use; Nasdaq symbol files do not supply industry classifications; SEC/SIC data has coverage and
rights questions; and index taxonomies/holdings have limited universes and unverified app-display
terms. Choosing one now would assert unsupported coverage or rights.

**Alternatives considered**: Use yfinance profile fields, SEC/SIC, Nasdaq files, or a provisional
provider-label catalog as a complete live source. None is established by the reviewed evidence as
a complete, effective-dated, app-authorized US membership feed.

**Primary references**:

- [Yahoo Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)
- [yfinance project README](https://github.com/ranaroussi/yfinance)
- [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation)
- [SEC company ticker/exchange data](https://www.sec.gov/files/company_tickers_exchange.json)
- [Nasdaq symbol-directory definitions](https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs)
- [MSCI GICS](https://www.msci.com/indexes/index-resources/gics)
- [FTSE Russell ICB](https://www.ftserussell.com/analytics/industry-classification-benchmark-icb)

## Resolved Technical Context

- Python 3.12 and the existing Streamlit/pandas/Altair/yfinance stack are already pinned or
  constrained in `pyproject.toml`.
- The existing root application has two Streamlit tabs and uses yfinance for live Discovery.
- The sector/industry discovery workflow currently loads representation history; it does not load
  every member-stock history or render the progressive stock tape.
- There is no existing SQL database or SQLAlchemy dependency in the application. SQLite is
  available through the Python standard library, and `.data/` is already ignored by git.
- The existing live membership catalog has stable instrument IDs, effective dates, source
  metadata, and explicit live-access validation. Its reviewed records can seed the database; it
  should no longer be a mandatory runtime JSON path.
- The user's local `~/Documents/learn/invest_screener/sector_rotation/ticker_universes/`
  directory contains ticker-universe CSVs with `Ticker`, `Name`, `Sector`, and `Industry`
  columns, including NYSE and Nasdaq listing candidates and overlapping S&P/Russell index
  sources. These files are outside this repository and have no exchange column; import requires
  explicit exchange/source metadata and source, coverage, and rights review. Invalid tickers and
  conflicting rows must be reported rather than silently resolved.
- A read-only audit on 2026-10-30 found 4,160 NYSE rows and 6,736 Nasdaq rows; 71 and 129 rows,
  respectively, lacked complete sector/industry classification. The two exchange files had no
  shared tickers in that snapshot. Across the exchange and S&P/Russell files, 647 shared ticker
  records had conflicting classifications. Use the exchange files as candidate listing inputs;
  do not apply index-source priority to silently combine taxonomies, and disclose unclassified
  records and coverage as partial until reviewed.
- The experimental JSON catalog builder currently resolves classification conflicts by fixed
  source priority and only counts conflicts. That behavior does not meet the accepted local-file
  authority rule; reuse its parsing conventions only, and replace priority selection with an
  explicit conflict report.
- The existing fundamental bundle/cache and raw-metric scorecard can be reused as acquisition and
  cache foundations. A separate pure peer-score calculation remains required by the accepted
  score definition.
- The default Streamlit dataframe chart column accepts a fixed series color, not a different
  directional color per volume observation. The thumbnail renderer therefore needs compact
  row-level chart composition rather than relying on a fixed-color volume chart column.
- pytest, Streamlit AppTest, Ruff, and Pyright are configured. No new runtime dependency is
  required. SQLite is the chosen persistence technology; enabling live refresh requires the
  application's single provider to pass source coverage and rights review.
