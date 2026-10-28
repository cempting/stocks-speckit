# Quickstart: Market Leadership Screener

This guide covers controlled US/JP/GB weekly sector-and-industry snapshots, US daily-history
discovery and input snapshots, and the earlier acceptance-fixture comparison. The default **Discovery**
page has three explicit modes: Weekly leadership, US live daily, and US acceptance comparison.
**Industry Discovery** is a separate page, defaults to US weekly industries, and can be opened
directly or from a selected sector. The UI exposes US only; JP/GB fixture calculations remain
available to tests/builds and do not imply live coverage or display rights. Live industry data,
constituent participation and observed flows are not enabled.

## Prerequisites

- Python 3.12
- `uv`
- The existing US daily-history fixture or an authorized daily-history source. The US/JP/GB
  controlled fixture is for acceptance testing only, not a live feed or proof of display rights.

## Local Configuration

```bash
cp .env.example .env
```

Add `MASSIVE_API_KEY` to `.env` when using the Massive REST provider. The application loads this
file for local development without overriding variables already exported by the process. The
`yfinance` adapter requires no key. `.env` is ignored by Git and must never be committed.

Set `MARKET_DATA_PROVIDER` to `massive` or `yfinance` to choose the provider offered by the
discovery page; `yfinance` is the default. Massive is shown only when `MASSIVE_API_KEY` is present.
The page does not silently switch providers after a request fails. `MARKET_DATA_SOURCE_CACHE_PATH`
selects the persistent Parquet source-cache location; it defaults to `MARKET_DATA_CACHE_PATH`.
`MARKET_DATA_RETRY_LIMIT` configures bounded retries for transient upstream failures.
Source-cache schema version 4 identifies the US daily-history currency basis as USD and rejects
nonpositive closes or negative volumes. Older cache entries remain on disk but are not reused;
the first matching request fetches and publishes a new generation.

## Build a Daily-History Input Snapshot

```bash
uv run python -m market_leadership.application.build_snapshot \
  --provider fixture \
  --start 2026-10-01 \
  --as-of 2026-10-23 \
  --symbols SPY XLB \
  --snapshot-id daily-2026-10-23 \
  --output .data/snapshots
```

`--as-of` is an upper bound: weekends and exchange holidays resolve to the previous XNYS
session, and an open session resolves to the previous completed one. Future dates and start
dates after the required session are rejected. The manifest records the resolved session, and
each symbol must contain its observation or publication fails. `--force-refresh` bypasses the
selected provider's persistent source-cache hit. A new snapshot ID is required for every
publication: existing snapshots are immutable, and an upstream failure leaves them untouched.
The published `prices` Parquet file and manifest are a canonical *input* snapshot, not a calculated
industry scoreboard. Live ingestion
requires explicit `--provider yfinance` or `--provider massive`; Massive requires `MASSIVE_API_KEY`.

## Build Calculated Weekly Fixture Snapshots

Publish a separate completed-week artifact for each market and level:

```bash
uv run python -m market_leadership.application.build_snapshot \
  --weekly --provider fixture --market US --level SECTOR \
  --as-of 2026-10-28 --snapshot-id us-sector-2026-10-23 --output .data/snapshots
uv run python -m market_leadership.application.build_snapshot \
  --weekly --provider fixture --market US --level INDUSTRY \
  --as-of 2026-10-28 --snapshot-id us-industry-2026-10-23 --output .data/snapshots
```

Repeat with `--market JP` and `--market GB` and distinct snapshot IDs to populate those markets.
The date is a cutoff, not a promise that its week is complete. For this fixture the latest completed
local week is 2026-10-23; a Friday cutoff before that week's completion selects the previous week.
Market holidays may yield a different last session for each market. Weekly artifacts live under
`.data/snapshots/weekly/` with their own `weekly-1.0.0` manifest and immutable IDs. They contain
calculated local rankings and never reinterpret Phase 2 `prices` inputs as weekly results. A missing
or invalid weekly artifact leaves the scoreboard empty or shows an error; it never fetches a live
provider or silently uses a daily input snapshot. Only the controlled fixture provider can publish
weekly inputs until source rights and dated non-price contracts are verified.

## Install

```bash
uv sync --all-groups
```

`uv` creates `.venv`, verifies `uv.lock`, and installs the application and development tools.

## Verify Before Running

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

The current suite covers implemented Phase 1–4 behavior. Future participation, observed flows and
filter/trust tests in `tasks.md` must be written failing-first before enabling those capabilities.

## Run the App

```bash
MARKET_LEADERSHIP_SNAPSHOT_DIR=.data/snapshots \
  uv run streamlit run src/market_leadership/app.py
```

The default Discovery page opens in **Weekly leadership** mode and reads the latest completed US
SECTOR snapshot. Select **Sector** and follow **Open Industry Discovery** to open the separate page
filtered to that stable parent-sector ID. The Industry Discovery page can also be opened directly
and accepts multiple US sectors; it renders a separate local ranking context per parent, never a
pooled cross-sector ranking. Weekly mode reads only the immutable weekly snapshot and makes no
upstream request. Rankings and deltas appear only when their required history exists; absent
evidence is labelled insufficient. These fixture-backed results describe past relative performance,
not forecasts.

Choose **US live daily** in Discovery to request adjusted daily history for SPY and the 11 US sector proxies. It persists
canonical source responses in the configured Parquet cache and reuses entries only when the cached
schema, checksum, and per-symbol date coverage are valid. Runtime requests also resolve the latest
completed XNYS session before cache lookup, so non-trading days reuse the correct source entry.
The Refresh data button bypasses the source-cache hit. This workflow uses direct Massive REST or
`yfinance`; it does not depend on MCP.
If yfinance returns an incomplete trailing bar (for example, volume without a closing price),
the bar is not used as a daily observation. Discovery displays the latest usable SPY observation
date, flags results as stale when it precedes the requested completed session, and aligns relative
returns to that SPY date. Invalid prices in earlier bars still fail validation.

From a selected live sector, follow **Open live Industry Discovery** to open the separate page
with that parent selected. Live industry results are currently unavailable: source research found
some candidate ETF exposures but did not verify an authorized point-in-time industry catalog,
historical membership and market-cap input, or deployment rights for displaying derived data. No
live provider request is made by this unavailable mode. See
[`contracts/us-industry-proxies.md`](contracts/us-industry-proxies.md) before enabling a catalog.

Choose **US acceptance comparison** to view the controlled US benchmark-regime and three-month
local-relative sector sample. It is not a live feed or calculated weekly ranking and does not
expose JP/GB in the user interface. The full US/JP/GB acceptance data and weekly snapshots remain
available to automated tests and offline builds.

The user-facing daily **Published snapshot** mode was removed. Daily input snapshots and their
build/read contracts remain supported; they are not weekly industry rankings.

## Validate the Remaining Release Workflow (after T049+ implementation)

Using `tests/fixtures/acceptance/market_data.json` and `expected.json`, exercise US, JP and GB
selection individually and together. Check each local regime, benchmark, currency, latest completed
weekly date and top/bottom sectors independently; never display a pooled ranking. The controlled
fixture now includes dated 1w/1m/3m/6m/12m close histories, 50-session composite inputs,
sector/industry classifications, and representation sources. Publish the preceding completed
weekly snapshot first to see score/rank deltas. Extend it with constituent evidence and observed
flow records for later phases. Verify source rights and provider contracts separately before
enabling non-US live ingestion.

Confirm sector is the default level, industries retain their parent and market, filter reset retains
selected markets, and stale/missing breadth or observed flows do not change price rank. Verify
observed flow is distinct from inferred trading activity and all outcomes expose basis, dates,
sources and coverage. Run the same `uv run pytest` and quality-gate commands above after each phase.
See [contracts/deferred-evidence.md](contracts/deferred-evidence.md) for phase-specific inputs and
[data-model.md](data-model.md) for insufficiency rules.

## Run Focused Tests

```bash
uv run pytest tests/unit/domain
uv run pytest tests/contract
uv run pytest tests/integration
uv run pytest tests/app
```

During implementation, write the smallest failing test first, implement its owning unit, rerun that
test, then run the complete suite before closing the task.

## Add or Replace a Workflow

1. Add a function under `src/market_leadership/ui/workflows/` that follows
   [contracts/workflow.md](contracts/workflow.md).
2. Add its `WorkflowSpec` in `bootstrap.py`, or replace the existing descriptor with the same key.
3. Add an `AppTest` covering initial, interaction, empty, insufficient, and error states.
4. Run the workflow tests and full suite. No domain or infrastructure module should change solely to
   register the workflow.

## Add a Data Provider

1. Implement only declared supported capabilities from
   [contracts/market-data-provider.md](contracts/market-data-provider.md), respecting the
   [deferred input contracts](contracts/deferred-evidence.md).
2. Run the conformance suite for those capabilities; verify source and display rights separately.
3. Register the adapter in the offline builder composition root.
4. Keep vendor credentials outside snapshots, logs, and Streamlit session state.