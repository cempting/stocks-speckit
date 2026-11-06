# Implementation Plan: Progressive Stock Screener

## Active Execution Reconciliation (2026-11-06)

This plan and the current [spec](spec.md)/[tasks](tasks.md) govern new work.
The obsolete historical planning body has been removed; original completed/retired
IDs and Git evidence remain in the [consolidated ledger](../task-history.md).
The active pointer remains feature 015; use an explicit feature-001 context for its work.

- Scope: tri-state technical criteria, adaptive consolidation and unchanged six-metric
  industry-peer component formulas. 004/006/008 own navigation, columns and representations;
  010/012 own catalog/membership; 011 owns issuer evidence; 014 owns score evaluation;
  015 owns dedicated lookup placement. Respect 013's shared service context on adoption.
- Stack: existing constrained Python/Streamlit/yfinance workspace. Pure calculation
  changes belong in `packages/market-data/src/market_data/domain/`; reuse `peer_scores.py`
  and `stock_chart.py`, adding `screening.py`/`consolidation.py` only where required.
  Application/provider/cache/UI changes remain in `src/market_leadership/`.
- Storage: no new catalog or observation store in 001. Consume the current validated
  snapshot or 013's pinned context on adoption; preserve its identity/permission gates.
  Do not recreate moved domain modules, SQL catalogs or runtime fixtures.
- Delivery: T099 baseline -> criteria/reference tests -> pure calculations and verified
  OHLC/volume handoff -> chart/peer-context tests -> existing workflow integration ->
  explicit-load/cache regressions -> measured browser/user acceptance and quality gates.
  The dependency graph in [tasks](tasks.md) controls shared-file ordering.
- Evidence: all current FR/SC IDs have an explicit task or active-owner mapping.
  The ledger retains completed T001-T048 and identifies T049-T098 as superseded,
  not complete. Neither documentation reconciliation nor existing scores prove
  the new adaptive detector or acceptance thresholds.
- Gates: one source, cache/selection isolation, explicit failures, source/display rights,
  reviewed migration boundaries, exact heuristic tests and visible-update p95 <=2 seconds
  over 2,500 loaded stocks. Reuse existing behavior before adding another implementation.
  This work adds no exception; 015's existing fourth-tab exception remains owned and
  time-bounded under [issue #2](https://github.com/cempting/stocks-speckit/issues/2).

## Protected Application Baseline

Retain Discovery, Industry Deep-Dive, Yahoo Classification Preview and Find a stock.
Preserve one progressive tape at a time, 006's five-column stock table, 004's chart
geometry/palettes/controls, explicit history and evidence loading, and independent
workflow state. Do not restore weekly leadership, index selectors, provider modes
or automatic proxies. This cleanup changes documentation only.

## Validation and Execution

Follow [quickstart](quickstart.md), [contracts](contracts/) and T099-T115.
Tests must fail before the corresponding behavior is changed; run the smallest
affected selectors and existing Ruff/strict Pyright gates. Measure the spec's
actual heuristic and user-visible thresholds, not a proxy benchmark.
Completed historical IDs do not certify acceptance of revised requirements.
