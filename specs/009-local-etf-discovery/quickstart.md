# Quickstart Validation: Local ETF Mapping Discovery

> **2026-10-31 — pre-cutover guide:** Schema 3 setup and database-backed commands/test results
> below remain implemented-version evidence. [Feature 010](../010-manifest-csv-catalogs/spec.md)
> requires manifest-registered optional research inputs, file-only histories, and coherent
> mapping/provenance publication. Preserve all prior acceptance evidence and export relationships;
> do not claim these commands validate the new storage boundary or replay completed implementation tasks.

**Status**: Implemented acceptance/run guide for schema 3 and feature 009 commands.
Production upgrades remain an explicit administrator action after backup.

## Prerequisites

- Complete `/speckit-tasks 009` and `/speckit-implement 009`.
- Use the repository's existing Python 3.12 environment (`uv sync` if dependencies are missing).
- Back up an existing regional database before schema upgrade. Prefer an isolated test database
  for the scenarios below.
- Supplied controlled fixture resources include literal/annotated catalogs, identical and conflicting
  duplicate keys, provider labels, sector/index/commodity context, unsupported expressions,
  an execution side-effect sentinel, and reviewed test-only ETF listings/hierarchy.
- No permanent validation depends on user-owned project paths or live market-data responses.

Contracts: [CLI/grammar](./contracts/local-etf-review-cli.md).
States and audit integrity: [data model](./data-model.md).

## 1. Initialize an Isolated Database and Collect Real Local Research

After implementation, choose a new ignored local database:

```bash
uv run python -m market_leadership.universe_admin init \
  --database .data/local-etf-discovery-validation.sqlite

uv run python -m market_leadership.universe_admin collect-etf-candidates \
  --database .data/local-etf-discovery-validation.sqlite
```

Expected: a versioned JSON inventory, all four resource statuses, candidate IDs, and exact
provenance. With stockviewer still missing, expect `partial` and exit 2, not complete success.
Readable sources remain useful research; source projects, approved data, and universe revision
are unchanged. No project side effects or remote calls occur.

To correct stockviewer after locating its actual catalog, use the descriptor form:

```text
collect-etf-candidates --root stockviewer=/actual/project \
  --catalog stockviewer=config.py:INDUSTRY_ETFS --database YOUR_TEST_DATABASE
```

Replace this example with the actual known file/catalog, not an invented path.

## 2. Validate Controlled End-to-End Scenarios

Use these explicit fixture roots instead of real project dependencies for controlled validation:

```bash
uv run python -m market_leadership.universe_admin collect-etf-candidates \
  --database .data/local-etf-discovery-validation.sqlite \
  --root sector_rotation=tests/fixtures/local_etf_discovery/sector_rotation \
  --root analyzer=tests/fixtures/local_etf_discovery/analyzer \
  --root stockfinder=tests/fixtures/local_etf_discovery/stockfinder \
  --root stockviewer=tests/fixtures/local_etf_discovery/stockviewer \
  --catalog stockviewer=config.py:INDUSTRY_ETFS
```

Expected: complete exit 0, ten industry occurrences and four context occurrences. The execution
sentinel is parsed but never run. Automated opt-in fixtures also register a sub-industry and an
uncovered node through the existing reviewed-node boundary.

The repository supplies `tests/fixtures/local_etf_discovery/listings.csv` as reviewed test-only
listing/hierarchy evidence. Never use fixture approval references as real display rights.

```bash
uv run python -m market_leadership.universe_admin import \
  --database .data/local-etf-discovery-validation.sqlite \
  --region US --classification LOCAL-ETF-TEST --source-id local-etf-test \
  --coverage "controlled test evidence" --approval-reference test-only \
  tests/fixtures/local_etf_discovery/listings.csv
```

The fixture hierarchy includes a Semiconductors node and verified SOXX/SMH test listings.
Use IDs actually returned by the commands below, not guessed classification/node identifiers.

```bash
uv run python -m market_leadership.universe_admin review-etf-candidates \
  --database .data/local-etf-discovery-validation.sqlite \
  --region US --classification LOCAL-ETF-TEST --as-of 2026-10-30

uv run python -m market_leadership.universe_admin review-listings \
  --database .data/local-etf-discovery-validation.sqlite \
  --region US --as-of 2026-10-30
```

Expected: every active node remains visible, SOXX/SMH alternatives retain separate provenance,
unknown scope/provider labels require reconciliation, and no candidate increases approved coverage.
Original duplicate declarations remain recoverable rather than disappearing through dict loading.

Record an explicit decision using the returned candidate/run/node/occurrence identifiers:

```text
review-etf-candidate --database YOUR_TEST_DATABASE \
  --candidate-id CANDIDATE --collection-run RUN \
  --region US --classification LOCAL-ETF-TEST --entity-id RETURNED_NODE --as-of 2026-10-30 \
  --decision accept --reason "Test-only exact classification and fund suitability review" \
  --review-reference test-only --evidence-id RETURNED_OCCURRENCE \
  --confirm-etf-identity --confirm-exact-scope --confirm-suitability \
  --issue-resolution unknown_instrument_type="Test-only fund identity assessment" \
  --issue-resolution unknown_region="Test-only explicit US scope assessment" \
  --issue-resolution unknown_classification="Test-only exact classification reconciliation"
```

This example selects the unqualified analyzer Semiconductors/SOXX occurrence. For other evidence
or targets, resolve the applicable issues returned by the worklist, including any scope or
node-level mismatch; do not treat these test-only rationales as real suitability evidence.

```text
approve-etf --database YOUR_TEST_DATABASE \
  --region US --classification LOCAL-ETF-TEST --entity-id RETURNED_NODE \
  --exchange NASDAQ --symbol SOXX --source-id local-etf-test \
  --approval-reference test-only --effective-from 2020-01-01 \
  --candidate-review-id RETURNED_REVIEW
```

Expected: representation and its review/source provenance become linked in one transaction.
Omitting confirmations, using an index, choosing a different node/ticker, or lacking
listing/source/date evidence fails without mutation. No-flag approval retains its existing behavior.

## 3. Rerun, Change, Remove, and Recover Evidence

Automated fixture scenarios must prove:

1. Unchanged collection preserves candidate/evidence identities and counts and adds no reviews;
   approved representations, memberships, baskets, and universe revision remain unchanged.
2. Modifying a supported fixture declaration identifies affected review relationships without
   overwriting the original approved evidence.
3. Removing a declaration from a complete catalog marks it removed; making the catalog unreadable
   marks support unknown, not removed. New provenance-linked approval remains blocked.
4. Restoring complete matching support resolves observability; changed semantics still require a
   new explicit review. Rejecting a selected candidate never selects an older accepted alternative.
5. An unrelated missing root does not invalidate complete selected supporting catalogs.
6. A simulated provenance-link or schema-migration failure rolls back mapping/version/revision
   changes, while existing approval evidence remains intact.
7. Source snippets containing unrelated private values never appear in persisted snapshots,
   diagnostics, or inventory output; the executable sentinel is never triggered.

## 4. Automated Validation

```bash
.venv/bin/pytest -q \
  tests/unit/test_local_etf_evidence.py tests/unit/test_local_etf_sources.py \
  tests/unit/test_universe_admin.py tests/integration/test_local_etf_discovery.py \
  tests/integration/test_industry_representations.py \
  tests/contract/test_local_etf_discovery.py
.venv/bin/ruff check src tests
VIRTUAL_ENV="$PWD/.venv" PATH="$PWD/.venv/bin:$PATH" \
  .venv/bin/pyright --pythonpath "$PWD/.venv/bin/python"
git diff --check
```

Tests must assert 100% controlled declaration recovery and active hierarchy row coverage, retained
duplicate locations, zero automatic approvals/provider requests, and rollback/currentness behavior.
Escalate to `.venv/bin/pytest -q -m 'not live'` for full offline regression validation, including
unchanged feature 008 approval and Discovery behavior.

## 5. Verified Results (2026-10-31)

- Focused new and existing reviewer/representation suites: **77 passed**.
- Full offline regression: **566 passed**, one live test deselected. Twelve existing dependency
  deprecation warnings remain; no live provider tests were invoked.
- Ruff and strict Pyright passed.
- SC-001/SC-002: all four controlled roots reported; **10/10 industry** and **4/4 context**
  occurrences recovered, including original duplicate locations.
- SC-003: **4/4 active controlled hierarchy nodes** returned with independent approved status.
- SC-004/SC-005: zero automatic approvals; valid explicit approval links retained exact
  node/listing/date/review/source evidence. Invalid prerequisites and injected link failure roll back.
- SC-006: unchanged collection adds zero duplicate evidence or reviews; changed/removed/new-conflict
  support triggers re-review, while unobservable source/context remains unknown. Restored complete
  support, partial-baseline re-review, location-only moves, and explicit root changes are tested.
  Both explicitly bound relationships (**2/2**, in distinct classifications) are flagged on a shared
  source change; acceptance does not propagate to another classification automatically.
- SC-007: controlled CLI collect/compare/accept/approve completes without source-project searching.
- An optional read-only real-resource smoke check recovered **318 industry occurrences** into
  **308 candidates**: sector_rotation 225, Analyzer 73, stockfinder 20. Stockviewer was missing,
  so the report was partial. The disposable database had zero approvals/reviews and revision zero,
  and was removed afterward; no production database or source project was modified.
