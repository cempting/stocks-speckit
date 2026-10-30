# Quickstart: Sector-to-Stock Explorer

## Prerequisites

- Python 3.12 and the repository's `uv` environment.
- For deterministic tests: the existing test fixtures and injected provider/membership/fundamental
  doubles. No live market-data credentials or network access are required.
- For manual live checks: a reviewed current membership catalog and matching live-display approval
  configured as required by the existing application settings. Without those approvals, the
  member-stock and peer-score evidence must remain blocked with a visible explanation.

## Focused automated validation

Run the new feature tests after their implementation tasks are complete:

```bash
uv run pytest \
  tests/unit/domain/test_peer_scores.py \
  tests/unit/domain/test_stock_chart.py \
  tests/unit/ui/test_progressive_tape.py \
  tests/unit/ui/test_sector_chart.py \
  tests/integration/test_stock_evidence.py \
  tests/app/test_sector_stock_explorer.py \
  tests/app/test_stock_detail.py -q
```

Expected outcomes:

- Domain cases match the 001 block-score formulas, peer-count thresholds, tie rules, missing
  evidence, and analysis cutoff.
- Tape cases prove that only the correct hierarchy stage is visible and all active members are
  accounted for.
- Provider tests prove that stock requests are limited to the selected industry's members and
  financial loads occur only after explicit intent.
- App cases prove row-specific chart previews, stable stock detail identity, error/insufficiency
  disclosures, and return to the prior valid selection context.

Run focused style and type checks:

```bash
uv run ruff check src/market_leadership tests
uv run pyright
```

After focused checks pass, run the full non-live regression suite:

```bash
uv run pytest -m "not live"
```

## Manual end-to-end check

Start the app:

```bash
uv run streamlit run streamlit_app.py
```

Using a controlled, approved test catalog and deterministic market-data fixture:

1. Open Discovery with no sector selected. Confirm the sector tape is the only tape.
2. Select a sector. Confirm it is replaced by only that sector's industry tape and that industry
   thumbnails match their own rows.
3. Select an industry. Confirm the stock tape contains all active catalog members, including
   explicit unavailable states for members without valid history.
4. Confirm the stock rows show thumbnail, ticker, name, latest price, and three peer score cells.
   Before an explicit load, score cells must not cause financial provider calls. After requesting
   scores, compare them to the controlled cohort and verify insufficient inputs are not shown as
   zero.
5. Open a stock detail view. Confirm its identity, price/volume chart, 50- and 150-session
   averages or explicit insufficiency, and matching peer scores.
6. Return to Discovery. Confirm the sector and industry selections remain. Change the sector and
   confirm no stale industry, stock, chart, or score evidence is shown.
7. Exercise missing catalog, stale membership, empty industry, per-stock history failure, and
   partial financial acquisition. Confirm each failure is visible and independent valid rows
   remain usable.

Live provider runs are optional and cannot replace deterministic evidence for empty, partial,
stale, invalid, or insufficient cases.
