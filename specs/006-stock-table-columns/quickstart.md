# Quickstart: Stock Table Columns

## Prerequisites

- Python 3.12 and the repository's `uv` environment.
- Deterministic stock-table fixtures for Large, Mid, Small, missing, invalid, unloaded, failed,
  and placeholder capitalization evidence.

## Focused Validation

Run the relevant checks:

```bash
uv run pytest \
  tests/unit/test_fundamentals.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/integration/test_stock_evidence.py \
  tests/app/test_sector_stock_explorer.py -q

uv run ruff check src/market_leadership tests
uv run pyright
```

Expected outcomes:

- The table shows exactly Price chart + 50 MA, Volume chart, Ticker, Name, CAP Type, and Total
  Score, in that order.
- Capitalization boundaries display Large at $10B, Mid at $2B through below $10B, and Small below
  $2B; all absent or invalid cases display Unavailable.
- CAP Type remains Unavailable before the existing explicit score-load action and no table render
  invokes a provider request.
- Total Score preserves its existing values/states; chart-cell and placeholder disclosures remain
  visible.

## Manual End-to-End Validation

1. Start the application with controlled stock and fundamental fixtures, then select an industry.
2. Confirm the table shows the six required columns and CAP Type is Unavailable before scores load.
3. Use the existing explicit score-load action. Confirm stocks at $10B, $2B, and below $2B show
   Large, Mid, and Small respectively.
4. Confirm missing, invalid, failed, and placeholder capitalization evidence shows Unavailable.
5. Confirm Total Score retains its existing values/states and the price/50 MA and volume evidence
   cells retain their disclosures.
