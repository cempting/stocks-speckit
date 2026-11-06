# Quickstart: Validate Industry ETF Momentum

> **Superseded validation workflow (2026-11-06):** Retained as historical evidence.
> Use [008's validation guide](../008-industry-representation-tools/quickstart.md)
> for current reviewed ETF/basket scope and 004's presentation contracts.
> Original T001-T011 are superseded, not completed, in the [ledger](../task-history.md).

## Prerequisites

- Use the repository virtual environment.
- Use reviewed fixture/hierarchy data containing a mapped parent industry, mapped sub-industry,
  an unmapped row, and mapped rows with unavailable and insufficient ETF history.

## Focused validation

```bash
.venv/bin/pytest -q \
  tests/unit/test_industry_etf_mappings.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/integration/test_stock_evidence.py \
  tests/app/test_sector_stock_explorer.py
.venv/bin/ruff check src tests
VIRTUAL_ENV="$PWD/.venv" PATH="$PWD/.venv/bin:$PATH" \
  .venv/bin/pyright --pythonpath "$PWD/.venv/bin/python"
```

## Expected outcomes

1. Every approved valid mapping produces a row whose ETF identity equals the symbol used for
   calculated momentum.
2. Parent and sub-industry mappings remain independently verifiable.
3. Unmapped and invalid rows display their explicit states without any ETF history request or
   substituted momentum.
4. Mapped rows with bad history retain the ETF identity and distinguish unavailable from
   insufficient evidence.
5. Existing stock-member contained-stock and score behavior remains unchanged.
