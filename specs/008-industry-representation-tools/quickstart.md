# Quickstart

```bash
.venv/bin/pytest -q tests/unit/test_industry_representations.py \
  tests/unit/test_industry_momentum.py tests/unit/test_universe_admin.py \
  tests/integration/test_industry_representations.py tests/integration/test_universe_admin.py \
  tests/integration/test_region_discovery.py tests/integration/test_stock_evidence.py \
  tests/app/test_sector_stock_explorer.py
.venv/bin/ruff check src tests
VIRTUAL_ENV="$PWD/.venv" PATH="$PWD/.venv/bin:$PATH" \
  .venv/bin/pyright --pythonpath "$PWD/.venv/bin/python"
```

Validate a reviewed ETF, a valid 100% basket, an invalid basket, and an unmapped classification.
Confirm the table labels each representation type and requests only active approved symbols.

See [review commands and schema migration](../../README.md#reviewing-industry-coverage).
Basket momentum uses weighted constituent returns, with no reweighting of missing members.
Basket charts remain unavailable rather than implying traded ETF price/volume evidence.
