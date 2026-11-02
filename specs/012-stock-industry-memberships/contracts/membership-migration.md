# Contract: Reviewed Membership Migration and Restoration

**Status**: Target workflow. Planning does not migrate or activate any catalog.

## Preparation interface

Add one command to universe_admin:

```text
prepare-membership-migration
  --source-release-manifest ABSOLUTE_PATH
  --region REGION_ID
  --target-classification-id ID
  --target-classification-version VERSION
  --scheme-name NAME
  --target-effective-from YYYY-MM-DD
  --output-directory NEW_ABSOLUTE_DIRECTORY
```

Initial conversion targets the existing single-region US catalog. Refuse unsupported
multi-region/source-scope conversions rather than dropping regions or guessing targets.

Capture/validate source bytes with the strict source-format loader. Refuse an existing
output directory or a destination inside published releases; do not overwrite CURRENT,
source files, audit history, approval records or configuration. No network calls,
issuer inference, ETF selection or automatic membership expansion.

Generate authoring files and registered report with state=prepared, approval fields
null and activation_ready=false. Return prepared, not validated/published, exit 0.
Invalid inputs use existing-style failed/conflict JSON, actionable stderr and exit 2.
No approve-by-flag command or review UI is added.

## Deterministic source mapping

- Group listing copies by original MembershipId and retain original scoped/physical
  identities in reconciliation.
- V1 SubIndustryId becomes the exact direct target; otherwise use IndustryId.
  Do not add a second direct parent assertion; ancestor inclusion is query-derived.
- Scope/period changes are explicit transformations. Keep unchanged instrument/listing
  IDs. Keep MembershipId only for unchanged logical identity; otherwise derive stable
  IDs from original scope/membership, target scope/node/period, retaining original
  IDs as lineage. Never use row order, time, labels or these fingerprints as CompanyId.
- Intersect operational memberships with reviewed target period. Retain out-of-period
  associations historically and identified instrument/listing records for lookup.
  Preserve null identifiers and source facts unchanged.
- Unresolved/placeholder inventory does not become identified, reviewed or request-
  eligible through conversion. Use only exact known stock identity for instrument rows.
- Do not rename/reparent meanings or add industries automatically. Changed/new
  assignments require reviewer-authored target evidence.

## Registered report

Add immutable required membership_migration JSONL artifacts with path/hash/row_count.
Retain previous report files/hashes; multiple report artifacts may exist historically.
Keep legacy migration_archive bytes and audit vocabulary unchanged.

One summary and one record per captured source artifact record, including hierarchy,
stock/listing, representation, audit/archive and retained inventory records. Source
manifest checksum preserves source metadata. Use natural source keys (RowId, ledger
RecordId, scoped NodeId/period, or exact original role-specific primary keys).
source_record_sha256 hashes canonical original parsed field values; source artifact
SHA-256 separately preserves exact bytes. Target row IDs refer to stock records;
unchanged non-stock identities remain traceable through source_identity and target
scope or are explicitly retained historically.

The [schema](membership-migration.schema.json) validates individual JSONL records.
Semantic validation additionally requires:

- One summary per migration ID; unique source-artifact/key pair; every original
  record accounted for exactly once, with no unexplained duplicate/omission.
- Counts equal dispositions; target rows/membership IDs resolve in the candidate;
  source record hashes and original scoped identities match captured input.
- target_data_sha256 is the canonical digest of target scope/classification/source
  metadata and operational artifact identity/hash/count vectors, excluding audit,
  legacy archives and report artifacts to avoid a self-referential hash.
- Approved summary requires a valid reviewed source/reference for the exact migration,
  not a status string or copied reference alone.
- unchanged_reviewed requires valid original approval and documented unchanged
  identity/meaning/permissions/periods. new_reviewed requires separate target review.
  not_operational authorizes no membership.

Reports remain historical proofs of their original target digest. Later native v2
edits retain prior reports but do not compare every historical digest to current data
or use it to approve new changes.

### Example prepared summary (not activation-ready)

```json
{
  "record_type": "membership_migration_summary",
  "migration_id": "migration-fixture-12",
  "source_release_id": "source-fixture",
  "source_manifest_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_catalog_revision": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "target_scope": {"region_id": "US", "classification_id": "CUSTOM-FIXTURE", "classification_version": "v2-test"},
  "target_data_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "state": "prepared",
  "review_source_id": null,
  "approval_reference": null,
  "counts": {"source_records": 1, "preserved": 0, "transformed": 1, "retained_historical": 0, "unresolved": 0}
}
```

## Review, validation and adoption

Reviewer approval covers the custom scope and compatible migration; unchanged valid
assignments do not need mandatory individual re-review. Changed/new assertions stay
non-operational until reviewed. Preserve old NodeReview/representation ledger records
under original scope; historical validation uses captured source/explicit retained
parent-chain snapshots, not current-scope reinterpretation.

Extend validate-catalog with optional --source-release-manifest for full candidate
reconciliation. A newly applying migration cannot report fully validated without
captured source and approved report. Already-published loading validates registered
report shapes/hashes and historical applicability; publication rechecks newly added
report reconciliation against known source before committing.

Use existing activate-catalog --expected-release. Under its writer lock, verify
current/source release/checksum, source accounting, target digest, migration approval,
ledger prefix, archive/report retention and complete target validation.
Reject stale source, altered candidate/review bytes, unsupported format, invalid
parents/memberships or competing publishers without changing CURRENT.
The source manifest's validated checksum must still match at commit, not merely
when preparation started. Historical report retention is not report reapplication.

## Historical reading and restoration

Retained v1/v2 snapshots are immutable. Dates outside the selected release's coverage
remain unavailable; inspect a known prior manifest explicitly, never silently substitute
another release or scan directories for candidates.

Keep recover-catalog target-manifest and expected-entry SHA-256 arguments.
Compose a new publication from target data/format/original approval semantics,
complete current audit history plus recovery event, and all retained archives/reports.
Validate the composition before commit; do not publish an old short ledger against
a newer parent or rewrite the original target.

New-reader v1 metadata support permits only the typed nonoperational report-history
extension for this restoration; v1 stock/hierarchy rules remain unchanged.
An older binary unable to parse that extension must fail explicitly. Restoring
data does not authorize downgrading the application binary and discarding history.

Acceptance includes v1 -> v2 -> restored-v1 publication, full audit-prefix/report
retention, original target membership/hierarchy results, unchanged evidence store,
source corruption/concurrency failures and clearing only invalid dependent selections.
