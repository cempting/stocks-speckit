# Validation Guide: Company Risk Evidence

**Status**: Design-time guide. Proposed modules/tests/CLI must be implemented through
`/speckit-tasks` and `/speckit-implement` before their commands can pass. This guide does not
authorize source activation or publication.

See [plan.md](./plan.md), [data-model.md](./data-model.md),
[UI contract](./contracts/company-risk-ui.md) and
[acquisition contract](./contracts/company-evidence-acquisition.md).

## Prerequisites

- Run from repository root in its existing Python 3.12 environment.
- Preserve active catalog, datasets, settings, approvals and unrelated work.
- Default tests are offline: synthetic ticker/profile, submissions, HTML/XBRL, reviewed claims,
  simulated source permissions, UTC clock and temporary evidence root.
- No dependency installation for planning. Restore the existing development environment only
  after a future validation command reports a missing dependency.
- Never run live-marked tests or grant source permission merely to obtain a green test.

## Existing regressions (available now)

```bash
.venv/bin/python -m pytest tests/unit/test_fundamentals.py tests/unit/domain/test_peer_scores.py tests/integration/test_yfinance_fundamentals.py tests/integration/test_fundamental_cache.py tests/app/test_fundamental_grading.py tests/app/test_grading_actions.py tests/app/test_stock_detail.py tests/app/test_sector_stock_explorer.py tests/app/test_progressive_tabs.py -m "not live"
```

These establish old behavior, not the new feature. Documentation-only planning does not require
running the application suite.

## Test-first validation (after proposed tests are added)

```bash
.venv/bin/python -m pytest tests/unit/domain/test_company_evidence.py tests/integration/test_company_evidence.py tests/app/test_company_risk.py -m "not live"
```

Confirm red tests detect absent behavior before implementation. Then combine feature/regression
selectors in one focused runner. Root AppTests are required, not disconnected component demos.

### 1. Cash states and financial integrity

Positive/zero/negative/absent/unloaded/failed/stale/non-comparable cash cases, including negative
OCF plus missing FCF: verify warnings before scores, values/dates/reasons/actions.
Exercise capex conventions, absent capex, source-supplied/derived FCF, mixed units/currencies,
YTD confusion, conflicting aliases, non-finite values, newer income without cash and 135/136-day
reporting boundary. Accepted existing inputs retain eight-slot/aggregate formulas.

### 2. Identity and dates

Similar names, share classes, ADR trading/reporting currencies, reused ticker, missing company ID,
expired binding and unresolved listing: zero cross-company attachment/guessed issuer requests.
For T004/T010/T011, exercise this issuer gate on fresh acquisition, cache/cohort reuse and
historical archive selection:

- Same ticker and exchange, but conflicting successor regulator identity or verified issuer
  domain: `mismatch`, zero successor facts attached to predecessor, zero verified snapshot/latest
  publication. A reviewed dated successor association is required, not a catalog mutation.
- Absent, failed or inconclusive profile, or no independent dated issuer reference: `unresolved`
  with explicit reason/action and preserved safe failure context; zero verified financial facts.
  A matching symbol/exchange/name/currency or cached predecessor success cannot satisfy the gate.
- Independent dated reviewed issuer-domain reference corroborated by the returned profile, no
  conflicts, company ID and CIK both null: permitted financial attachment succeeds using existing
  instrument/listing IDs; null IDs stay null, zero invented identifiers, implicit research grants
  or catalog mutations. Also exercise the corroborated regulator-ID verification route.
- Count one ticker acquisition and no second profile fetch; verify retained issuer evidence,
  provenance, effective binding and identity-aware cache context. Older metadata-free bundles
  remain readable but cannot satisfy verification through listing labels alone.

Old chart date cannot request historical Yahoo; current mode is explicitly distinct; archives
exclude later captures. Peer vintage insufficiency remains, not guessed filing availability.

### 3. Structured research and permission

Injected submissions/documents/fact contexts populate business fields, attributed competitive
claims and separately defined backlog/bookings/RPO with qualifications. Exercise unstructured/
unmapped prose, inspected absence, denial/conflict/amendment and reviewed claim import.
Unsupported parsing cannot become "not disclosed". Unknown/revoked uses block retrieval/display;
Finviz/TradingView remain references. Count transport requests and validate size/time/retry bounds.

### 4. Cache, history and privacy

Verify financial/research TTL expiry at exactly 3,600/86,400 seconds, cache isolation, scoped
refresh and ordinary-navigation reuse. Failed refresh exposes the new failure and labels older
good records history. Revoked permissions block cached display. Inject corruption/interrupted/
concurrent writes; require explicit errors and preserved immutable history.
Compare catalog hashes before/after. Inspect transport/cache/report data for absent credentials,
private portfolios/watchlists and unrelated companies. Required publisher contact is sent only
in its transport header and is absent from returned cache values, evidence, logs and reports.

### 5. Root UI and exact outcomes

Temporary reviewed-catalog AppTest: sector -> industry -> stock -> financial load -> independent
research load. Verify attached identity, warning precedence, overview, exact matrix, citations,
preserved controls and breadcrumb return without research requests; no new root/retired actions.
Record warmed navigation <=1 second with zero extra research calls, hardware/versions/sample
sizes and measured elapsed time, not a proxy test duration.
Separately conduct five-user recognition: at least four identify status/main warning within
ten seconds for complete/incomplete cases. Automated tests cannot replace this human measurement.

## CLI/static checks (after implementation)

```bash
.venv/bin/python -m market_leadership.company_evidence_admin --help
.venv/bin/python -m market_leadership.company_evidence_admin review-source --help
.venv/bin/python -m market_leadership.company_evidence_admin bind-issuer --help
.venv/bin/python -m market_leadership.company_evidence_admin register-document --help
.venv/bin/python -m market_leadership.company_evidence_admin import-claims --help
.venv/bin/ruff check src/market_leadership tests/unit/domain/test_company_evidence.py tests/integration/test_company_evidence.py tests/app/test_company_risk.py
.venv/bin/pyright --pythonpath "$PWD/.venv/bin/python"
```

CLI integration tests exercise actual temporary-root recording, denial, history/revisions and
errors; `--help` is not acceptance. After focused checks, full offline suite when practical:

```bash
.venv/bin/python -m pytest -m "not live"
```

## Optional operational smoke: separate approval required

Only after applicable rights, verified identity and publisher access are recorded may an
operator test one selected company in an isolated persistent evidence directory:

```bash
.venv/bin/python -m streamlit run streamlit_app.py
```

Do not activate/switch catalogs or launch a second server blindly. Use explicitly current company
actions, inspect limitations/provenance, and stop on denial. No alternative-host evasion.
Synthetic tests do not guarantee real source coverage.

## Coverage

| Requirements | Scenarios | Outcomes |
|--------------|-----------|----------|
| FR-001, FR-002 | 1, 5 and existing regressions | SC-008 |
| FR-003 through FR-008 | 1, 2, 4, 5 | SC-001, SC-002, SC-003 |
| FR-009 | 2, 3, 5 | SC-004 |
| FR-010 through FR-012 | 3, 5 and reviewed import | SC-003, SC-005 |
| FR-013 through FR-015 | 3, 4 and reviewer CLI | SC-006 |
| FR-016, FR-017 | 4, 5 and request measurements | SC-006, SC-007 |
| FR-018 | 1, 3, 4 | SC-003, SC-005, SC-006 |
| FR-019, FR-020 | 4 and CLI mutation/privacy checks | SC-006 |
| FR-021 | 1, 5; no advice/order/position actions | SC-008 |

Future tasks are complete only after exact outcomes are verified. Rights/access, real extraction
coverage, target-host persistence and SC-002 human measurement remain release gates.
