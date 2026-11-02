# Quickstart: Validate the Membership Revision

Implementation is in progress. Release-v2 parsing, issuer-evidence storage and
composition, file-only source/binding administration, issuer-fact projection,
retained-stock lookup, continuity-filtered history, and stock-detail evidence
controls, and US2 overlap/deep-membership behavior are implemented on synthetic
fixtures. US3/US4 and broad acceptance work remain incomplete. No production catalog
activation, source collection, or rights approval has occurred.

## Prerequisites

Python 3.12, existing development environment, synthetic reviewed fixture inputs in
temporary stores, and completed test-first v2/011 prerequisites. No production
CURRENT, secrets, live market services or actual source approvals in acceptance tests.
See [catalog](contracts/catalog-v2.md), [migration](contracts/membership-migration.md)
and [navigation/peers](contracts/navigation-peer-context.md).

## Runnable now: baseline

From the repository root:

```bash
.venv/bin/python -m pytest tests/integration/test_catalog_performance.py -q --durations=0
.venv/bin/python -m pytest tests/unit/test_catalog.py tests/unit/test_catalog_files.py tests/contract/test_catalog_files.py tests/integration/test_catalog_publication.py tests/integration/test_catalog_workflows.py -q
```

The first selector ran during implementation on branch `main`, worktree
`/Users/emc/Claude/Projects/SectorStockScreener/stocks-speckit`: **1 passed**,
1.17 s test-call duration, 1.69 s total. The catalog regression selectors also ran:
**122 passed**, 5.62 s total, with 12 existing NumPy/exchange-calendars deprecation
warnings. These verify current behavior, not future overlap/deep-tree performance.
Both runs used the existing `.venv` and source-free test fixtures; no production
catalog, setting, approval, or active entry was changed. Do not restore dependencies
unless a later validation fails because a package is missing. Do not use live-marked
tests for membership acceptance.

## Implementation foundation results

The new versioned-catalog and identity projections were first run before their
runtime types existed (collection failed on the missing projection), then passed
with the existing catalog selectors: **149 passed**, 12 existing deprecation
warnings, 4.64 s. After adding inventory lookup, v1/v2 listing resolution, and
typed-cell/size-bound cases, the expanded selectors passed: **157 passed**, 12
existing deprecation warnings, 4.64 s. Ruff passed for the changed Python files;
Pyright reported no
errors (only the environment's unresolved-source warnings for `jsonschema`).

The issuer identity/evidence domain foundation then passed
`tests/unit/domain/test_company_evidence.py`: **11 passed**. Targeted Ruff and
Pyright checks passed for the new domain types; persistence, settings, and production
acquisition remain pending.

## US1 implementation checkpoint

The available stock-history, fundamental-cache, fundamental-normalization,
peer-score and company-evidence domain regressions passed together:
`uv run pytest -q tests/integration/test_stock_evidence.py tests/integration/test_fundamental_cache.py tests/unit/test_fundamentals.py tests/unit/domain/test_peer_scores.py tests/unit/domain/test_company_evidence.py`
reported **56 passed**, with 12 existing NumPy/exchange-calendars deprecation
warnings. This earlier regression did not establish the composed production issuer gate.

The issuer store/configuration/admin command, provider/cache composition, issuer
projection, stock lookup, selected listing history and company-evidence detail
controls have since been implemented. The focused validation command

```bash
uv run pytest tests/app/test_stock_detail.py tests/app/test_stock_lookup.py \
  tests/integration/test_company_evidence.py \
  tests/integration/test_company_evidence_composition.py \
  tests/integration/test_company_evidence_admin.py \
  tests/integration/test_stock_evidence.py tests/integration/test_fundamental_cache.py \
  tests/unit/domain/test_company_evidence.py tests/unit/test_company_evidence_config.py -q
```

reported **63 passed**, with 12 existing NumPy/exchange-calendars deprecation
warnings. It includes production composition checks for current permission
revalidation, stored research discovery across verified sibling share classes,
issuer-owned financial projection, continuity-filtered history/cache refresh,
source/binding administration, and detail rendering of research provenance.
Ruff passed on the changed Python sources/tests and Pyright reported **0 errors,
0 warnings, 0 informations** for the changed source files. The related provider,
fundamental-normalization and peer-score regression selector reported **53 passed**.

The `tests/app/test_stock_lookup.py` cases cover explicit InstrumentId/listing
choice, unassigned and unverified-listing detail, and zero provider/history/
company-evidence requests on open. T013 tests cover mixed ticker rows, inclusive
continuity bounds, distinct listing cache entries, membership expiry, and ineligible
listing gates. T024-T025 are complete: the combined US1 acceptance and regression
selectors reported **95 passed**, with 12 existing NumPy/exchange-calendars
deprecation warnings. In the production financial-composition test, the first
listing caused one provider request and yielded 10 observations; cache reuse and
historical reattachment caused no additional request; the second verified share
class caused one distinct provider request and yielded 10 observations; revoked
permission caused zero further requests. The financial-only path produced no
research snapshots. Catalog release artifact hashes were unchanged after enrichment.
The ticker-reuse history test requested only `FIXTURE` for 2026-10-23 through
2026-10-24 and admitted close values `[20.0, 21.0]` and volume `[200.0, 210.0]`,
while reporting 2026-10-14 through 2026-10-22 as unverifiable. Stored business-
model/moat claims reuse remains limited to reviewed stored snapshots; research
collection, disclosure extraction/import, and new qualitative collectors remain
outside feature 012 and are not marked complete in feature 011. US2/US3/US4 tasks
are not all complete, so this is not an overall feature-completion claim.

## US2 overlap and deep-membership checkpoint

The v2 temporal-forest tests cover sibling and cross-sector overlap while retaining
v1 single-assignment rejection, independent reviewed assertions, conflicting
repeated MembershipIds, temporal parent changes, invalid active edges and cycles,
uncovered ancestors, and a 1,100-node chain without recursion. The noncontemporaneous
union-of-edges cycle remains valid because no cycle exists at one effective date.
Hierarchy validation errors include the offending node and parent identity.

Synthetic query results were exact: `share-class-a` appears under both `industry-a`
(through `nested-3`) and cross-sector `industry-c`; `sector-a` deduplicates to
`share-class-a` and `share-class-b`. `nested-2` resolves to `share-class-a` once.
The direct memberships remain `nested-3` and `industry-c`; selecting `industry-a`
provides parent context without creating a direct parent assertion. Two listing
copies of `membership-parent` produce one logical membership and one instrument,
with `listing-a-primary` selected independently. A retained original snapshot keeps
`share-class-b` under `industry-b` after a second release moves it under
`industry-a`.

The `reparented` node resolves through `industry-a` on 2024-12-31 and through
`industry-b` on 2025-01-01. The old parent rollup contains `share-class-c` only at
the first date; the new parent rollup contains it at the second. Inclusive
membership reassignment also retains the old assertion through 2024-12-31 before
the new assertion begins on 2025-01-01. Representation worklists preserve exact
node applicability: the reviewed `test-cloud` ETF does not cover `test-specialist`,
and the `test-empty` basket retains its explicit `test-inventory-listing` weight
of `100.000`; neither is inferred from descendants.

The first v2 query regression exposed missing descendant unions and a repeated
membership fixture that reused a listing/assertion pair; the fixture was corrected
to use distinct listing IDs for logical copies. The subsequent path regression
exposed that a root industry's sector edge is represented by `SectorId`, not
`ParentIndustryId`; that path invariant is now handled explicitly. The final focused
catalog/membership/representation/selection/AppTest selector reported **145 passed**,
with 12 existing NumPy/exchange-calendars deprecation warnings. Ruff passed and
Pyright reported **0 errors, 0 warnings, 0 informations**. This selector verifies
the US2 overlap, depth, date-specific rollup and retained-history outcomes; it is
not the full feature acceptance suite.

The T024 artifact-hash assertion confirms enrichment leaves catalog release bytes
unchanged. US1's T025 gate is complete, so no pending-US1 enrichment exception is
needed for this checkpoint. No production catalog, approval, activation, or source
permission was changed.

## US3 context and rendering progress

The comparison context, fact-sensitive result fingerprint, canonical membership
cohort fingerprint, A/B result retention, selection reconciliation, full-path labels,
and direct/inherited membership rendering are implemented. The focused UI/peer/cache
regression command reported **97 passed** with 12 existing NumPy/exchange-calendars
deprecation warnings; Ruff passed and Pyright reported **0 errors, 0 warnings, 0
informations**.

The A -> B -> A request-counter regression uses the production company-financial
cache API with controlled binding/policy fingerprints: cohort A made two first
requests, B made only its one new request, and returning to A made no repeats.
Separate cache regressions cover binding, source-policy, mode and TTL changes.
However, peer scoring still does not invoke the reviewed association and issuer-fact
attachment composition for its requests. T036/T039 and the dependent US3 acceptance
gate remain incomplete; no production issuer-fact reuse or permission revalidation
in peer scoring is claimed here.

## Prospective automated acceptance

After new focused test files and behavior are implemented:

```bash
.venv/bin/python -m pytest tests/unit/test_catalog_memberships.py tests/contract/test_catalog_v2.py tests/integration/test_membership_migration.py tests/app/test_stock_lookup.py tests/integration/test_catalog_performance.py -q
```

`tests/unit/test_catalog_memberships.py` and `tests/contract/test_catalog_v2.py`
are present; the migration and lookup acceptance files are still planned. Extend existing
tests/integration/test_stock_evidence.py, tests/integration/test_fundamental_cache.py,
tests/unit/domain/test_peer_scores.py, tests/app/test_progressive_tabs.py and
tests/app/test_stock_detail.py for coupled regressions. Add the minimum 011 reviewed
issuer/profile/reuse integration tests; stubs alone cannot prove production acceptance.

| Controlled case | Required result |
|---|---|
| Sibling/cross-sector overlap | In every approved target, once in parent/sector unions |
| Three/four/deeper levels | Exact descendant sets; no recursion-depth failure |
| Dated reparenting | Original date results; actual cycles/orphans/period gaps rejected |
| Multiple listings/share classes | One stock per instrument, two share classes, independent histories |
| Reused ticker spanning two issuers | Exclude predecessor observations before charts/calculations; unknown continuity unavailable, not membership-clipped |
| Stored business-model/moat claims | Both verified share classes reuse permitted claims with provenance; financial-only/denied/revoked permissions and post-cutoff captures blocked |
| Unassigned/unlisted lookup | Correct retained detail, no fabricated membership/unverified request |
| Industry A -> B -> A | Separate contexts; zero repeats per valid issuer/request; previously unrequested peers load only explicitly, no universe prefetch |
| Missing vintages/cap/issuer gate | Explicit unavailable/insufficient, not invented financial success |
| Draft or changed unreviewed mapping | No activation; compatible approval lineage traceable |
| Valid/stale migration | Complete reconciliation; CURRENT changes only on valid commit |
| V1 -> v2 -> restored v1 | Original data semantics and full audit/archive/report history |
| Enrichment/unrelated edit | Zero classification changes; no needless requests/selection clearing |

For the qualitative cases, use typed stored snapshots under
`tests/fixtures/acceptance/company_evidence/disclosures/reviewed_claim_snapshots.json`
with simulated independent research approvals, no document fetch/import or new
collectors. Cover valid shared claims, financial-only grants, denial/revocation/
expiry and captures on/beyond the requested historical UTC day's end. Assert
original claim source, kind, qualifications, capture and provenance in both details.

For ticker reuse, return one synthetic provider response containing predecessor,
successor and unverifiable dates. Check observations immediately before/on/after
reviewed continuity boundaries, including cached responses; assert exact eligible
close/volume rows used by charts/calculations and explicit missing intervals.
Vary membership dates without changing the permitted history.

For A -> B -> A, keep a ledger per issuer/evidence request and distinguish valid
repeats from necessary first requests and unrelated acquisitions. Assert zero
repeats while bindings/permissions/freshness remain valid, zero new peer calls
before explicit loading, and only the active view's required calls afterward.
Preloading both cohorts or the universe on navigation is not a passing strategy.

## Prospective CLI/UI walkthrough

Use a test-created temporary v1 store and replace these absolute fixture paths
with known paths. After implementation:

```bash
.venv/bin/python -m market_leadership.universe_admin prepare-membership-migration \
  --source-release-manifest /absolute/temp/source/manifest.json \
  --region US --target-classification-id CUSTOM-FIXTURE \
  --target-classification-version v2-test --scheme-name "Custom fixture industries" \
  --target-effective-from 2026-11-01 --output-directory /absolute/temp/candidate
```

Expected: prepared authoring/report files, activation_ready=false. A reviewer
completes valid scope/source approvals and target-bound reconciliation, separately
reviewing changed/new assignments. A status string alone cannot approve the draft.

```bash
.venv/bin/python -m market_leadership.universe_admin validate-catalog \
  --release-manifest /absolute/temp/candidate/manifest.json \
  --source-release-manifest /absolute/temp/source/manifest.json
.venv/bin/python -m market_leadership.universe_admin activate-catalog \
  --manifest /absolute/temp/store/CURRENT.json \
  --release-manifest /absolute/temp/candidate/manifest.json --expected-release SOURCE_RELEASE_ID
```

Source-validation flag is planned; validate/activate commands already exist.
Stale expected release, prepared report or invalid candidate must fail without
changing the temporary entry.

Prefer AppTest with injected source-free loaders. Launch a real app only with
explicitly approved test/provider settings:

```bash
MARKET_CATALOG_MANIFEST_PATH=/absolute/temp/store/CURRENT.json \
  .venv/bin/streamlit run src/market_leadership/app.py
```

This is not an offline switch: startup retains existing market-price behavior.
Check lookup, deep paths, unavailable peers, unchanged tabs/columns and selections.
Restore explicitly with recover-catalog's known target-manifest and expected-entry
SHA-256 flags, not direct CURRENT editing.

## Final implementation gate

After focused acceptance/regressions pass, run the relevant full suite for shared
catalog/UI/evidence changes and:

```bash
.venv/bin/ruff check src tests
.venv/bin/pyright
```

Record exact set/count/identity checks, source-call counters, cold/warm phase timings,
memory and truthful failure states. Full acceptance requires SC-001-SC-009, including
composed production issuer gate/reuse behavior, not merely passing catalog tests.
