# Quickstart and Validation: Progressive Stock Screener

**Status**: Post-implementation validation guide for [plan.md](plan.md).
Current execution follows the reconciled [tasks](tasks.md). The root already has
Discovery, Industry Deep-Dive, Yahoo Classification Preview and Find a stock.
This guide does not certify the adaptive detector, source coverage or acceptance.

## Prerequisites and Setup

- Python 3.12 and `uv`; use the existing constrained manifest and lockfile.
- Authorized personal/development access to the selected yfinance source for an
  optional live smoke test. Hosted display/derived-use rights require separate approval.
- Controlled synthetic fixtures for complete membership, technical histories and
  financial publication periods. They do not prove live-provider coverage.

From the repository root:

```bash
uv run streamlit run streamlit_app.py
```

Supply a reviewed manifest through `MARKET_CATALOG_MANIFEST_PATH` using the current
application setup. 001 adds no database, provider or store; 013's service/cache
configuration applies on adoption. Restore dependencies only after a missing-package
failure. Avoid public deployment until rights are verified.

## Automated Evidence

Write the relevant tests failing-first, implement, then run the smallest affected
test selection before the full applicable suite:

```bash
uv run pytest tests/unit/domain tests/contract tests/integration tests/app -m "not live"
uv run ruff format --check src packages services tests
uv run ruff check src packages services tests
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
| Root navigation | Preserve all four current tabs and one shared validated catalog/context; Find a stock is absent from Discovery; lookup/detail opening performs no unsolicited history or issuer-evidence load |
| Industry returns | Reuse 004's five visible periods and exact adjusted completed-session endpoints; retain the one-session calculation without restoring its removed selector |
| Membership coverage | Reuse 010/012 reviewed regional identities, dates, deduplicated rollups and explicit invalid/unassigned states; do not restore index, exchange/cap or multi-sector selectors |
| Representation | Reuse 008's exact approved ETF or explicit approved basket; missing representation cannot become a parent ETF, largest stock or inferred proxy |
| Stocks and selection | Choose industry, explicitly load required data; all available members remain accessible beyond a full page; preserve 006's five columns and stable identity |
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

The current [backlog](tasks.md) starts at T099; the [ledger](../task-history.md)
preserves T001-T098 and links their original evidence.
The active pointer selects 015; use an explicit feature-001 context before analyzing
or implementing this backlog. Documentation reconciliation does not mark new work complete.
