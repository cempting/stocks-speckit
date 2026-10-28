# Quickstart: Market Leadership Screener

This guide covers US daily-history discovery and the daily-history input snapshot builder.
The full weekly sector-and-industry scoreboard and non-price data ingestion are not implemented yet.

## Prerequisites

- Python 3.12
- `uv`
- A licensed canonical snapshot directory, or the repository acceptance fixture

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

The full suite includes formula boundaries, provider contracts, use-case integration, equity baseline
compatibility, and Streamlit `AppTest` workflows.

## Run the App

```bash
MARKET_LEADERSHIP_SNAPSHOT_DIR=.data/snapshots \
  uv run streamlit run src/market_leadership/app.py
```

The discovery page requests adjusted daily history for SPY and the 11 US sector proxies. It persists
canonical source responses in the configured Parquet cache and reuses entries only when the cached
schema, checksum, and per-symbol date coverage are valid. Runtime requests also resolve the latest
completed XNYS session before cache lookup, so non-trading days reuse the correct source entry.
The Refresh data button bypasses the source-cache hit. This workflow uses direct Massive REST or
`yfinance`; it does not depend on MCP.

Choose **Published snapshot** from **Data source** to load the latest published daily input snapshot
from `MARKET_LEADERSHIP_SNAPSHOT_DIR` (default `.data/snapshots`). That mode displays the snapshot
ID and as-of date, makes no upstream requests on page reruns, and does not offer a live refresh
button. If no input snapshot has been published, the page displays a build instruction instead of
switching providers. **Live provider** remains the default; the snapshot mode does not calculate
weekly leadership rankings.

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

1. Implement the protocol in [contracts/market-data-provider.md](contracts/market-data-provider.md).
2. Run the shared provider conformance suite.
3. Register the adapter in the offline builder composition root.
4. Keep vendor credentials outside snapshots, logs, and Streamlit session state.