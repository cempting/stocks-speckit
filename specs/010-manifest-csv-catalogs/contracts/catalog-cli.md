# Catalog Administration CLI Contract

**Entry point**: `python -m market_leadership.universe_admin`
**Report version**: `market-catalog-cli-1`
**Status**: Planned interfaces, not currently implemented commands.

## Common Inputs and Results

`--manifest PATH` selects the store entry (`CURRENT.json`); otherwise use
`MARKET_CATALOG_MANIFEST_PATH`, then `.data/catalog/CURRENT.json`.
No database/independent stock-catalog/default instrument fallback.
Node commands require exact `--region`, `--classification`, `--classification-version`.
Review uses explicit `--as-of`; publication periods use explicit `--effective-from`/optional
`--effective-to`. The observation clock remains a separate injected UTC clock.

Every mutating command requires `--expected-release ID`; first activation requires the literal
`none`. An already published mapping may be idempotent, but new provenance is still a coherent
publication. Concurrent mismatch/lock contention yields a conflict, not silent rebase.
Commands retain ordinary argparse exit 2 for malformed input.

Common stdout envelope:

```json
{
  "report_version": "market-catalog-cli-1",
  "command": "review-representations",
  "status": "complete",
  "publication_state": "not_published",
  "catalog": {
    "release_id": "example-release",
    "catalog_revision": "example-content-digest",
    "catalog_changed": false
  },
  "result": {}
}
```

IDs/digest above illustrate fields, not a deployable release.
`status`: complete, partial, failed, conflict, indeterminate.
`publication_state`: not_published, published, unknown.
Exit 0 means complete validated read/publication; exit 2 means partial/failed/conflict/indeterminate,
with bounded stderr diagnostics and truthful publication state. No exception becomes a successful
empty report. Source snippets, credentials and full legacy payloads are excluded from default output.
Research `result` retains its existing `local-etf-discovery-1` domain report/identity semantics
inside the new catalog-context envelope.

## Bootstrap, Validation and Activation

```text
catalog-init --directory DIR
validate-catalog --release-manifest PATH
activate-catalog --manifest ENTRY --release-manifest PATH --expected-release ID_OR_none
```

- Init creates the local store directories/lock structure only; no approved sources, stock/ETF
  roster, research roots, or active entry are invented.
- Validate reads an authoring release manifest and captured registered bytes without mutation.
  Check shape, all required roles for declared regions, counts/checksums, exact scope/parentage,
  effective periods, source/approval ownership, mappings, inventory/ledger references and conflicts.
  Explain unconfigured/unreviewed coverage separately from a valid empty membership result.
- Activate revalidates captured candidate data, takes the writer lock, compares expected entry,
  stages copies and a new publication record, computes revision, assigns a release ID and parent
  link, and atomically chooses one coherent generation. Do not edit input files.
- Whole-release authoring is the supported way to introduce new source/region/classification
  metadata and reviewed stock CSV updates. New code changes or per-industry imports are unnecessary.
  Source review must be actual recorded evidence, not synthesized from a valid format.

## Existing Governed Commands, New File Boundary

The following command names retain their business purpose and gain the common file/expected-release
and exact-version inputs instead of `--database`.

| Command | Specific inputs / behavior |
|---|---|
| `review-representations` | Exact scope, as-of, optional `--uncovered-only`; all active reviewed nodes including zero members |
| `review-listings` | Region/as-of; verified/unverified stock, ETF and listing-only inventory status; no membership inferred |
| `review-node` | Scope, `--sector-id`, `--entity-id`, `--name`, source/reference/period; optional `--parent-industry-id` for sub-industry |
| `approve-etf` | Scope/node, `--exchange`, `--symbol`, source/reference/period, explicit `--suitability-reference`; optional `--candidate-review-id` |
| `approve-basket` | Scope/node/name, source/reference/period, repeated `--constituent LISTING_ID=DECIMAL_PERCENT` |
| `collect-etf-candidates` | Registered optional research sources only; writes an observation/run and new evidence once, no market calls |
| `review-etf-candidates` | Exact scope/as-of, optional `--collection-run`; current candidate/binding/conflict/qualification states |
| `review-etf-candidate` | Exact candidate/run/evidence IDs, scope/node/as-of, accept/reject, reason/review reference, confirmations/issues |

For accept: preserve `--confirm-etf-identity`, `--confirm-exact-scope`,
`--confirm-suitability` and repeatable `--issue-resolution`; reject does not acquire accept-only
confirmations. Acceptance remains separate from listing/source/representation approval.
ETF selection by symbol is allowed only if it uniquely resolves an already verified regional
primary listing; it does not create a new listing or infer ETF identity.

Every write publishes ledger/CSV changes together against the latest expected snapshot under the
writer lock. Validate candidate support, exact selected decision, source/scope/listing/period
prerequisites in that same snapshot. A stale request cannot append a review/provenance link to a
newer silently selected release.

Root/catalog corrections are authoring manifest updates, not transient hidden override flags.
Retire research `--root`/`--catalog` overrides with guidance to explicitly update the registered
research descriptors and activate the candidate manifest. Parser grammar and supported source
claims remain unchanged; metadata configuration never becomes approval.

Collection may publish a complete ledger update with `status=partial`/exit 2 while leaving
`catalog_changed=false`. Missing optional research does not invalidate unrelated approved sources.
Unchanged sources reuse candidate/evidence IDs; observation runs can be new. Changed/removed/
conflicting/unobservable support is retained for re-review, not automatic replacement of approvals.

## Read-Only Legacy Export

```text
export-database --database PATH --output DIR
```

This is the only command allowed to import SQLite/open a catalog database. It requires an explicit
path, opens it read-only, captures a consistent committed snapshot including WAL-visible rows,
and accepts actual schemas 1/2/3 without initialization/upgrading. Unsupported schema fails.
Do not infer a database path from retired environment settings.

Output: draft release artifacts, lossless registered archive, and a reconciliation report.
No active entry switch, source modification, inferred GICS version, normalized-name reassignment,
automatic suitability approval, or deletion occurs.
The report accounts for each table's original PK row and dependent links, using
transferred/quarantined/archived dispositions. Missing columns/history are recorded as missing.
Readiness is blocked when required scope/listing/approval bindings remain unresolved even if
the archive export completed. Exit 2 for blocked operational migration, with retained outputs;
complete safe export returns 0, but still requires separate validation/activation.

Missing reviewed versions or target scope are resolved in explicit reviewed authoring metadata,
not a default `legacy` GICS version or replay of old imports. Resolve/quarantine conflicts and
then validate a candidate release. Preserved unclassified verified listing inventory can remain
available to existing explicit baskets without generating stock memberships.
Archived issue records cannot restore original rejected rows never stored by the importer.

## Recovery

```text
recover-catalog --manifest ENTRY --release-manifest KNOWN_REVIEWED_PATH \
  --target-manifest-sha256 HASH --expected-entry-sha256 HASH
```

The raw expected-entry checksum permits explicit recovery of a corrupt entry without assuming
its release ID. Verify target against a known recorded/backup checksum, all artifact hashes and
current domain prerequisites. Acquire the same writer lock and compare raw current entry bytes
before replacement. Recovery is deliberate; it never scans for a newest generation, discards
history, reapproves records, or uses SQL fallback. Keep a receipt linking the operation/target/parent
where the previous valid identity is known.

A commit/durability acknowledgement failure is reported as indeterminate rather than claimed
rollback. Inspect validated entry and retained operation/parent IDs before retrying. Both old/new
selected generations must be complete; do not blindly repeat an approval after uncertain commit.

## Retired Commands and Settings

Old `init`, single-file `validate/import`, live `refresh` mutation, and any ordinary command's
`--database` flag fail with migration guidance. New activation replaces the catalog import authority;
live market-data refresh remains the existing provider action, never silent membership overwrite.
Nonempty `MARKET_UNIVERSE_DATABASE_PATH`, `STOCK_MEMBERSHIP_CATALOG`,
`EXPERIMENTAL_UNIVERSE_CATALOG`, or obsolete independent `FUNDAMENTAL_DISPLAY_APPROVAL` configuration
cannot silently select a second catalog; report the relevant migration/source-review guidance.
Empty tracked template values may be treated as unset. Export's explicit `--database` remains supported.

Legacy industry/synthetic snapshot/catalog entry points are refactored to manifest input or return
actionable retirement errors before any instrument/provider request. Synthetic provider definitions
are test-only, not accessible through a runtime mode. Existing stored snapshot readers remain
historical file readers, not approved catalog seeds.
