# Quickstart and Validation: Progressive Stock Screener

**Status**: Post-implementation validation guide for [plan.md](plan.md).
The repository still contains the prior routed application. Writing this guide does
not implement the tabs, new detector, source coverage or financial scorecards.

## Prerequisites and Setup

- Python 3.12 and `uv`; use the existing constrained manifest and lockfile.
- Authorized personal/development access to the selected yfinance source for an
  optional live smoke test. Hosted display/derived-use rights require separate approval.
- Controlled synthetic fixtures for complete membership, technical histories and
  financial publication periods. They do not prove live-provider coverage.

From the repository root:

```bash
uv sync --locked --all-groups
uv run streamlit run src/market_leadership/app.py
```

The new path requires no database, Massive key, snapshot build, persistent Parquet
cache or MCP server. Do not treat legacy provider/snapshot environment settings as
new-path source selection. Avoid public deployment until rights are verified.

## Automated Evidence

Write the relevant tests failing-first, implement, then run the smallest affected
test selection before the full applicable suite:

```bash
uv run pytest tests/unit/domain tests/contract tests/integration tests/app
uv run ruff format --check src tests
uv run ruff check src tests
uv run pyright
```

These are existing tool/directory conventions, not a claim that revised-feature tests
already exist. Track newly introduced and pre-existing diagnostic failures separately;
this plan grants no waiver of required quality gates. Preserve existing legacy
snapshot compatibility tests. Keep live requests mocked by default; live smoke tests
must be opt-in and explicitly labelled.

## End-to-End Controlled Scenarios (after implementation)

Use an injected/mocked yfinance boundary and clock in automated tests, not an
undocumented production provider selector. Prepare at least five valid peers plus
missing/invalid cases and a known full available membership list.

| Scenario | Actions and required result |
|---|---|
| Three-stage entry | Exactly Sectors and Industries, Industry Stocks, Stock Detail; later stages explain prerequisites; rendering/tab switches make no unsolicited remote call |
| Industry returns | Load industries; default five-session interval; change to one. Exact adjusted endpoints, gaining/declining/neutral labels and shared competition ranks agree with fixtures |
| Universe coverage | Test index union, exchange/cap intersection and sector union; 300M/2B/10B boundaries; unknown caps; unsupported index never becomes an unrestricted universe |
| Representation | Qualified ETF before verified largest member; stable-ID cap ties; no broad ETF or incomplete-cap largest claim; missing qualification leaves a visible unranked industry |
| Stocks and selection | Choose industry, load stocks; all available members accessible, including beyond a full page; sorting precedes paging; only checkbox cells editable |
| Technical AND | Independently enable each rule and combinations; SMA equality fails; volume exactly 2x preceding-20 mean passes; insufficient evidence does not pass |
| Consolidation and spike | Prior-session quiet run plus current spike can both match; latest/previous versus older runs differ; compare 4/5-session, multi-month and multi-year cases |
| Charts | Sector/industry/stock uses its own history; at most latest corridor by default, older inspectable; displayed dates, width and duration match detector output; no-interval differs from insufficient |
| Financial blocks | Load scorecards; check all three 0-100 blocks, six raw metrics, periods/publication evidence and peer counts against exact expected values |
| Stable peers | Filter/select/page stocks without changing universe/industry/cutoff: retained-stock scores and financial remote-call counts unchanged |
| Missing facts | Bad equity/prior denominator, wrong periods/currency, missing quarters/publication or post-cutoff revisions produce specific insufficiency, not zeros/reweighted blocks |
| Private state | Rerun and change parent/universe/criteria; retain valid IDs, clear only invalid dependents with explanation; two sessions do not share selections |
| Freshness and failure | Repeat fresh interactions: zero repeated remote calls. Advance clock beyond TTL, fail targeted refresh: old evidence explicitly stale/error, independent results remain, no success-shaped fallback |
| Complete access | Every matching stock has scorecard access regardless of checkbox/page; membership/loaded/failed/missing counts reconcile |

Numerical references: [financial scoring](contracts/fundamental-scoring.md),
[consolidation](contracts/consolidation.md), [data/cache](contracts/market-data-provider.md)
and [workflow](contracts/workflow.md).

## Performance and User Acceptance

For SC-005, use 2,500 synthetic stocks with loaded source payloads and precomputed
history/peer results, including multiple pages and mixed criterion states. Record the
hardware/browser/runtime, dataset fingerprint, loaded counts and test actions.
Warm the app, then measure at least 100 representative filter/sort/selection interactions
from user action to updated visible result. Report p95 (nearest-rank 95th observation
for 100 samples) and the request counter; require <=2 seconds and no remote request
for unchanged fresh inputs. Server-only calculation timing is not sufficient.

Measure cold loads separately with progress/coverage and failure disclosure; do not
fold remote waits into a misleading cached-only result or claim cold-load SLAs.
Test real dataframe/editor/chart behavior in a browser where AppTest lacks coverage.

For SC-001/002/008, recruit representative first-time users and record task outcomes:
at least 90% identify strongest/weakest eligible industry within 60 seconds; at least
90% complete industry-to-filtered-stock-to-three-block inspection within three minutes;
at least 90% interpret corridor dates/width, insufficiency and nonpredictive meaning.
Fixtures/timing do not replace these observed user checks.

## Optional Live Smoke and Release Decision

Verify only source-authorized capabilities. Confirm actual quote/session dates and
cache reuse, not a claim of real-time exchange data. Explicitly inspect limitations:

- Complete eligible industry membership and optional dated index coverage are not
  established by top-company lists or the existence of a screener.
- yfinance's reviewed statement history and missing publication/vintage metadata may
  leave Growth/Cash Flow or all cutoff-dependent blocks insufficient.
- Split-comparable volume and qualification/display rights need independent evidence.

Record source scope, dates, coverage and rights before enabling affected live results.
Unavailable capabilities must stay visibly unavailable; mocked green tests do not
certify them. See [research.md](research.md) for feasibility limits.

Next generate revised tasks specifically for feature 001 while preserving historical
IDs. The active-feature pointer currently targets 002; do not run an unqualified
task-generation command and accidentally replace feature 002's work.
