# Quickstart: Market Leadership Screener

This guide describes the planned commands once implementation tasks are complete.

## Prerequisites

- Python 3.12
- `uv`
- A licensed canonical snapshot directory, or the repository acceptance fixture

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

## Build a Fixture Snapshot

```bash
uv run python -m market_leadership.application.build_snapshot \
  --provider fixture \
  --as-of 2026-10-23 \
  --output .data/snapshots
```

The builder validates source schemas, calculates both local and global weekly views, writes to a
temporary directory, verifies checksums, and atomically publishes the completed snapshot. It never
publishes a partially calculated directory.

## Run the App

```bash
MARKET_LEADERSHIP_SNAPSHOT_DIR=.data/snapshots \
  uv run streamlit run src/market_leadership/app.py
```

The default page opens the latest completed weekly industry scoreboard. The page header must show
the selected snapshot ID and as-of date. Use the acceptance fixture for deterministic review; it is
not live market data.

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