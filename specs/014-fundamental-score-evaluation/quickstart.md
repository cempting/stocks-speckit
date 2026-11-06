# Fundamental Score Evaluation Quickstart

This guide validates the current score rules and user-visible states with controlled data.
It does not require live Yahoo requests or change the checked-in market catalog.

## Prerequisites

- Python 3.12 and `uv` installed.
- Repository dependencies installed:

  ```bash
  uv sync --all-packages
  ```

- Run commands from the repository root.

## Run focused score and presentation tests

```bash
uv run pytest \
  tests/unit/domain/test_peer_scores.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/app/test_stock_detail.py \
  tests/integration/test_fundamental_cache.py \
  tests/integration/test_stock_membership.py \
  -q
```

The cases use controlled facts and fake loaders. They must not call a live provider.

## Validate required scenarios

Confirm these observable outcomes in tests or equivalent controlled review:

1. Five distinct ascending peer values rank at `0, 25, 50, 75, 100`; exact ties receive
   midranks; five equal peers each rank at 50; four valid peers are insufficient.
2. Each component requires both of its metric percentiles. Missing denominators, incompatible
   periods/currencies, unknown publication dates, or post-cutoff facts remain insufficient.
3. Valid current zero or negative cash flow remains a numeric observation, while absent,
   unloaded, invalid, stale, and failed cash-flow evidence remains explicitly unavailable or
   unassessed.
4. The list's Total Score equals the three component mean to one decimal only when all three
   components are available. In an end-to-end controlled scoring case, the application state
   remains available and does not suppress the numeric total. Every other case preserves its
   correct non-numeric state.
5. A stock's raw negative cash-flow value and its peer-relative percentile are both interpretable;
   the percentile does not erase the raw value or claim financial safety.
6. Stock detail exposes all six peer metrics, their raw values and percentiles, valid-peer
   counts, states, and available source/period/currency/cutoff context without another load.
   Missing provenance remains explicitly unavailable.
7. The live yfinance evidence gate does not treat fetch time as publication availability or
   infer a dated market cap; unsupported facts remain unavailable.
8. Changing industry, cohort, cutoff, or rules revision cannot silently reuse a non-comparable
   value. Ordinary rendering initiates no score or financial-data request.
9. Any proposed rule change is documented and does not change user-visible results until
   explicitly approved and versioned.

The detailed invariants are in [score-presentation.md](contracts/score-presentation.md), and
the current evidence and result relationships are in [data-model.md](data-model.md).

## Broader quality gates

After focused tests pass:

```bash
uv run ruff check src packages services tests
uv run pyright
uv run pytest -m "not live" -q
```

Expected: all selected tests, lint, and strict type checks pass; no live provider call is
required for these gates.
