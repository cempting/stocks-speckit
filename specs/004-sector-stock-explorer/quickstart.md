# Quickstart: Sector-to-Stock Explorer

> **2026-10-31 — pre-cutover guide:** Database setup/import examples and old test outcomes
> below describe implemented legacy behavior. [Feature 010](../010-manifest-csv-catalogs/spec.md)
> targets file-only catalog/review records and one manifest-backed regional stock CSV/hierarchy
> release. Preserve these steps as operational/migration references; they do not activate the
> future file release or prove cutover. Do not modify user-owned data as part of specification alignment.

## Prerequisites

- Python 3.12 and the repository's `uv` environment.
- For deterministic tests: temporary SQLite databases, reviewed sample CSV/JSON inputs, and
  injected market/fundamental providers. No live credentials or network access are required.
- For manual checks: a reviewed US source file. Candidate inputs are in
  `~/Documents/learn/invest_screener/sector_rotation/ticker_universes/`. Its NYSE/Nasdaq files
  represent exchange-listing candidates; S&P/Russell files are overlapping index lists, not
  complete additional exchanges. Do not assume coverage or rights have been approved. Live
  refresh stays disabled until the application's provider passes review.
- The default local database lives under `.data/`, which is ignored by git. No
  `STOCK_MEMBERSHIP_CATALOG` environment variable is required.

## Initialize and populate the database

Initialize the schema:

```bash
uv run python -m market_leadership.universe_admin init
```

Validate a reviewed local listing file before importing it:

```bash
uv run python -m market_leadership.universe_admin validate \
  --region US \
  --exchange NASDAQ \
  --classification <reviewed-classification-id> \
  --source-id <reviewed-source-id> \
  <path-to-reviewed-listings.csv>
```

Import only after validation reports no blocking issues:

```bash
uv run python -m market_leadership.universe_admin import \
  --region US \
  --exchange NASDAQ \
  --classification <reviewed-classification-id> \
  --source-id <reviewed-source-id> \
  --coverage <reviewed-coverage-description> \
  --approval-reference <review-id> \
  <path-to-reviewed-listings.csv>
```

Repeat for other reviewed exchange files. The input's `Ticker`, `Name`, `Sector`, and `Industry`
fields are mapped to stable stock/listing/membership records; source and exchange metadata are
provided explicitly. Invalid symbols and unresolved conflicts are reported and never silently
selected by source priority. Blank or sentinel classification values (such as `undefined`), and
incomplete sector/industry pairs, are retained as unclassified; the import summary counts them and
region coverage remains partial. An unresolved placeholder is retained without requesting live
market data. Live refresh is run only through the approved source contract; its differences cannot
overwrite locally reviewed classifications.

The local CSVs are candidate inputs, not evidence that the full US region is covered. Record
coverage and rights in the source review before treating the region as complete.

Validation uses the selected `--database` read-only to detect conflicts with existing reviewed
identities and memberships; a missing database does not prevent file validation. Import
quarantines each conflicting row without leaving orphan stocks or classification records. An
all-rejected file changes only its audit records, not the published hierarchy, coverage, or
revision. Matching reviewed rows can resolve placeholders and add classification without
downgrading previously accepted states.

Coverage descriptions combine contributing reviewed sources. A chart-only import adds its
limited scope alongside exchange coverage, rather than replacing it. The next accepted import
also reconstructs contributing sources from existing regional provenance; it does not certify
complete regional coverage.

### Existing databases and import replay

Schema version 1 remains supported; no database rebuild is required. New import-run
fingerprints persist a digest of the review/import context as well as the file hash.
Replaying the same file requires the original region, classification, source, approval,
coverage, and exchange arguments and returns the original diagnostics with zero inserted rows.

Legacy runs storing only a raw file hash cannot prove their original context and are rejected
on replay with actionable guidance. After reviewing the input and provenance again, use a new
source ID; existing records and audit history are retained. This also applies to legacy
second-exchange imports under an existing classification. Do not remove historical runs to
bypass the check.

Coverage recovery uses surviving regional listing, membership, classification, and
representation provenance. Historical scope with no surviving provenance cannot be recovered
automatically. Future combined-source history is stored under the existing metadata key
`regional_reviewed_coverage:{region_id}` without a schema migration.

## Add reviewed chart representations

Discovery only requests price history for representations recorded in the database. Import a
reviewed primary listing first, then map it to its reviewed sector or industry. For example, with
the default IDs generated from classification `GICS`:

```bash
uv run python -m market_leadership.universe_admin represent \
  --region US \
  --classification GICS \
  --entity-type sector \
  --entity-id gics-technology \
  --exchange NYSE \
  --symbol <reviewed-representation-ticker> \
  --source-id <reviewed-source-id> \
  --approval-reference <matching-review-id> \
  --effective-from 2020-01-01
```

The source and approval reference must match a reviewed local import, and the listing must be
active, verified, and primary. This command records chart representation only; it does not add
stock membership. Do not copy proxy symbols from old application constants without reviewing
their coverage and display rights.

If every sector displays "Chart representation unavailable", the listing import succeeded but
sector chart mappings have not been configured. Import a separate reviewed file containing the
ETF primary listings (without sector/industry membership), then use `represent` for each sector.
For a reviewed Select Sector ETF setup, the explicit mappings are:

| Sector | Chart symbol (NYSEARCA) |
|--------|------------------------|
| Communication Services | XLC |
| Consumer Discretionary | XLY |
| Consumer Staples | XLP |
| Energy | XLE |
| Financials | XLF |
| Health Care | XLV |
| Industrials | XLI |
| Information Technology | XLK |
| Materials | XLB |
| Real Estate | XLRE |
| Utilities | XLU |

These are ETF proxy returns, not returns aggregated from the imported member stocks. Keep the
ETF listings unclassified so they do not become industry constituents. Their import reports
`committed_partial` (exit code 2) because they intentionally have no membership; check that all
11 rows were accepted with zero conflicts before recording the representations. Set
`--effective-from` to the reviewed mapping start date. Use the same `--database` path for both
commands and set `MARKET_UNIVERSE_DATABASE_PATH` to that path when starting the app.

Sector and industry performance cells use a per-period gain/loss color scale (green for gains,
red for losses, neutral for zero) alongside the chart previews. Returns display as percentages
with two decimal places; missing returns display as "Unavailable" without a gain/loss color.
Price and volume thumbnails use an 84-pixel plot height across sector, industry, and stock tapes.
Use **Thumbnail period** beside the tape heading to select `1w`, `1m`, `3m` (default), `6m`, or
`1y`, measured back from the selected as-of date. Both thumbnails use the same calendar window;
the 50-session SMA is calculated before cropping so shorter windows retain their moving average.
The selection persists when navigating between sector, industry, and stock tapes, and does not
change the return columns or stock-detail chart. **Performance basis** sits to the right of the
heading and switches return columns between absolute and benchmark-relative outcomes.

Unavailable or incomplete member histories remain retryable. Successful members are reused
independently, and Refresh replaces only the matching symbols/date/request cache entries.
Independently usable price or volume stays visible when its sibling series is insufficient;
short price histories explicitly disclose an insufficient 50-session SMA in that chart cell.
The stock tape/detail does not request hidden industry proxies or load financial scores
without the explicit score-load action.

## Focused automated validation

Run the new feature tests after their implementation tasks are complete:

```bash
uv run pytest \
  tests/unit/domain/test_peer_scores.py \
  tests/unit/domain/test_stock_chart.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/unit/ui/test_sector_chart.py \
  tests/unit/infrastructure/test_region_database.py \
  tests/unit/infrastructure/test_universe_import.py \
  tests/integration/test_region_discovery.py \
  tests/integration/test_universe_admin.py \
  tests/integration/test_stock_evidence.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_stock_detail.py -q
```

Expected outcomes:

- Database and import cases prove that a rejected input leaves the last valid database unchanged,
  active members are returned exactly once, multiple listings remain attached to one security,
  and unresolved placeholders make no market-data requests.
- Domain cases match the 001 block-score formulas, peer-count thresholds, tie rules, missing
  evidence, and analysis cutoff.
- Tape cases prove that only the correct hierarchy stage is visible and all active members are
  accounted for; each has a row-specific price thumbnail with a 50-session average and an
  adjacent volume thumbnail using green/up, red/down, and neutral/unchanged-or-unknown bars.
- Provider tests prove that stock requests are limited to the selected industry's members and
  financial loads occur only after explicit intent.
- App cases prove row-specific chart previews, stable stock detail identity, error/insufficiency
  disclosures, and return to the prior valid selection context.

Run focused style and type checks:

```bash
uv run ruff check src/market_leadership tests
uv run pyright
```

After focused checks pass, run the full non-live regression suite:

```bash
uv run pytest -m "not live"
```

## Manual end-to-end check

Start the app:

```bash
uv run streamlit run streamlit_app.py
```

Using a validated local import and deterministic market-data/fundamental fixtures:

1. Initialize the SQLite database and import a reviewed US file. Confirm an invalid import is
   rejected without changing the last valid database contents.
2. Open Discovery with no sector selected. Confirm the US sector tape is the only tape and that
   each row has adjacent price and volume thumbnails.
3. Select a sector. Confirm it is replaced by only that sector's industry tape; verify its chart
   thumbnails match each row's own history.
4. Select an industry. Confirm the stock tape contains every active database member exactly once,
   including unresolved placeholders and explicit unavailable states for members without valid
   history.
5. In all three tapes, verify price thumbnails include the 50-session average when sufficient
   history exists, volume thumbnails are immediately adjacent, and volume bars are green for
   higher closes, red for lower closes, and neutral for unchanged/unknown direction. Verify the
   legend does not imply verified buyer/seller activity.
6. Confirm the stock rows show ticker/listing, name, latest price, and three peer score cells.
   Before an explicit load, score cells must not cause financial provider calls. After requesting
   scores, compare them to the controlled cohort and verify insufficient inputs are not shown as
   zero.
7. Open a stock detail view. Confirm its identity, price/volume chart, 50- and 150-session
   averages or explicit insufficiency, and matching peer scores.
8. Return to Discovery. Confirm the region, sector, and industry selections remain. Change the sector and
   confirm no stale industry, stock, chart, or score evidence is shown.
9. Exercise an uninitialized database, stale membership, empty industry, unresolved placeholder,
   invalid import, live-source classification conflict, per-stock history failure, and partial
   financial acquisition. Confirm each failure is visible and independent valid rows remain usable.
10. Confirm live membership refresh stays blocked with an explicit explanation until a source has
    passed coverage, terms, taxonomy, and display-rights review.

Live provider runs are optional and cannot replace deterministic evidence for empty, partial,
stale, invalid, or insufficient cases.

## Convergence preservation evidence (2026-10-30)

Browser verification used a fresh temporary server, a temporary reviewed-format database with
all 11 explicit ETF mappings, and an injected deterministic provider. Synthetic evidence was
prominently labeled; no user database was rebuilt and no live-data permission was inferred.

At a 1920x1080 viewport:

- The heading, period, and basis controls shared the same top coordinate, with left positions
  80, 672, and 1264 pixels respectively. The two root tabs remained Discovery and Industry
  Deep-Dive.
- All 22 separate price/volume plots measured exactly 84 pixels high. The first pair was
  adjacent at the same vertical coordinate.
- All 55 return cells retained colored two-decimal percentages. Selecting a different preview
  period left the return-cell contents unchanged.
- Each period was selected and its rendered price-path point count matched the inclusive
  synthetic calendar window:

  | Period | Points | Charts | Plot height | App exceptions |
  |--------|-------:|-------:|------------:|---------------:|
  | 1w | 6 | 22 | 84 px | 0 |
  | 1m | 23 | 22 | 84 px | 0 |
  | 3m | 67 | 22 | 84 px | 0 |
  | 6m | 132 | 22 | 84 px | 0 |
  | 1y | 262 | 22 | 84 px | 0 |

These are deterministic UI observations, not live coverage or user-study measurements. The
temporary server is stopped after verification.

Final automated quality gates passed: **455 non-live tests**, with one live test deselected,
Ruff, strict Pyright, and `git diff --check`. The root-app missing-database cases used an
explicitly absent test database path; populated user databases were left unchanged.
Twelve existing dependency deprecation warnings remain.
