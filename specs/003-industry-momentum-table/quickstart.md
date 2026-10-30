# Quickstart: Validate Simplified Live Discovery

## Prerequisites

- Python 3.12 and development dependencies installed with `uv sync`.
- Network access to yfinance.
- `STOCK_MEMBERSHIP_CATALOG` pointing to a reviewed live membership catalog.
- `FUNDAMENTAL_DISPLAY_APPROVAL` matching that catalog's approval reference.

## Run

```bash
uv run streamlit run streamlit_app.py
```

## Manual Validation

1. Confirm the root interface has only **Discovery** and **Industry Deep-Dive** tabs.
2. Open Discovery and confirm no evidence-mode or provider selector is present.
3. Confirm the page identifies yfinance and the requested/observed data dates.
4. Disconnect the provider or enter an unavailable condition; confirm an explicit error appears
   and that no snapshot, fixture, comparison, or alternate-provider result is shown.
5. Open Industry Deep-Dive with valid catalog configuration. Confirm the catalog identifies itself
   as live and allows dated sector/industry/member selection.
6. Remove or invalidate the catalog configuration. Confirm member display is blocked and dependent
   selected stocks are cleared without showing synthetic data.

## Automated Validation

```bash
uv run pytest tests/app/test_discovery.py tests/app/test_progressive_tabs.py
uv run ruff check src tests
uv run pyright
```

Tests must use deterministic doubles for yfinance responses; no automated test may depend on live
market availability.
