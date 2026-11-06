# Implementation Plan: Industry Representation Tools

**Reconciled**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Scope and Current Authority

Provide reviewed worklists and maintenance for industry/sub-industry representations:
exact approved ETFs where suitable, otherwise explicitly reviewed weighted stock baskets.
008 also owns former 007's exact-ETF momentum and distinct mapping/evidence states.
Original 007 T001-T011 are superseded, not completed, in the
[ledger](../task-history.md); retirement does not certify current 008 implementation.

010 owns manifest-managed file sources, publication and durable review/audit records.
012 revises membership/hierarchy only through a reviewed version boundary.
The obsolete SQLite/region-database plan has been removed; do not restore database
storage or recreate app-local domain/catalog modules.
[Tasks](tasks.md) retain active work and historical completion evidence.

## Technical Context and Flow

- Reuse the existing Python/Streamlit/pandas workspace, pytest, Ruff and strict Pyright.
- Shared pure representation/calculation rules belong in
  `packages/market-data/src/market_data/domain/`; catalog/schema authority stays in
  that shared package. Publication and reviewed maintenance belong to
  `services/market-structure/`. App acquisition, cache and UI stay in
  `src/market_leadership/`.
- Resolve only active approved exact region/classification/node/listing mappings
  from the validated release, or 013's pinned context on adoption. Preserve source
  provenance, effective dates, review status and independent source permissions.
- Validate verified constituents and effective-dated basket weights summing to 100%.
  Missing constituents/history cause explicit gaps, not reweighting, substitution
  or invented returns. Parent, sector, broad-market and arbitrary proxies are forbidden.
- Batch only distinct eligible symbols in the displayed scope after existing
  explicit load actions. Separate unmapped, invalid, unavailable and insufficient
  evidence; keep all active reviewed nodes visible.
- Follow [representation-workflow](contracts/representation-workflow.md) for review,
  approval, worklists and evidence. Research under 009 does not approve coverage;
  publishing under 010 does not transfer approvals to another classification.

## Protected Presentation and Validation

004 owns progressive Discovery style/controls, 006 owns the five-column stock tape,
and 015 owns dedicated lookup placement. Keep all four root tabs, chart geometry,
palettes, tooltips, period/basis controls and independent state unchanged.
Hidden representation/status columns retain their tooltip evidence; do not make
new visible columns to satisfy the historical ETF-only wording.

Add failing mapping, approval, weight/date, no-substitution and gap tests before
corresponding changes. Use controlled catalogs and injected history, then run
focused unit/integration/AppTests and existing quality gates.
See [quickstart](quickstart.md). Historical test completion does not establish
live coverage, display rights, migrated approvals or remaining task acceptance.

## Constitution and Complexity

Reuse existing reviewed-source, representation and market-data boundaries; baskets
are governed representations, not a generalized portfolio system. No hidden provider
requests, new store or new exception is authorized. The existing fourth-tab exception
remains owned by 015 under [issue #2](https://github.com/cempting/stocks-speckit/issues/2).
