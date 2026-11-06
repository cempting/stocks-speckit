# Quickstart: Contained Stock Score Summary

> **Superseded validation workflow (2026-11-06):** Retained as historical evidence.
> Use [006's validation guide](../006-stock-table-columns/quickstart.md) for the
> current five-column table and Total Score label. The old assertions below must
> not restore removed columns. Completion evidence is in the [ledger](../task-history.md).

## Prerequisites

- Python 3.12 and the repository's `uv` environment.
- Deterministic contained-stock fixtures with available, not-loaded, insufficient, unavailable,
  error, and placeholder score cases.

## Focused Validation

Run the focused table and application checks:

```bash
uv run pytest \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_sector_stock_explorer.py -q

uv run ruff check src/market_leadership/ui/components tests/unit/ui tests/app
uv run pyright
```

Expected outcomes:

- A row with all three available component scores displays their one-decimal equally weighted
  average in the single Score column.
- Every incomplete, unavailable, error, not-loaded, and placeholder case displays the required
  explicit non-numeric state.
- The table has no Quality, Growth, Cash Flow, Score Status, Observed, or Chart Status column.
- Price and volume chart cells still disclose unavailable or insufficient evidence.
- Opening or rerendering the table does not load score evidence until the user selects the
  existing score-load action.

## Manual End-to-End Validation

1. Start the application with the controlled regional universe and select an industry.
2. Before requesting scores, confirm each contained stock has one Score column reading `Not
   loaded` and that no score request starts automatically.
3. Request scores using the existing explicit action. Confirm a stock with all three component
   scores shows their one-decimal average.
4. Confirm rows with insufficient, unavailable, failed, or placeholder evidence show their
   required explicit state rather than a number.
5. Confirm the table retains price chart, volume chart, ticker, name, and price, but has no
   removed score or metadata columns.
6. Exercise missing price and volume evidence and confirm its chart-cell disclosure remains
   visible.
