# Regional Universe Management CLI Contract

## Purpose and storage

- The CLI initializes and manages the local SQLite database used by Discovery.
- Default database path: `.data/market-universe.sqlite`; `--database` may override it.
- `init` creates the schema and is safe to rerun. It does not invent or seed membership rows.
- The runtime app reads region, classification, sector, industry, stock, listing, membership, and
  sector/industry chart-representation records from this database.

## Commands

### `init`

```text
python -m market_leadership.universe_admin init [--database PATH]
```

Creates or upgrades the schema and reports the database path and schema version. Invalid or
unwritable paths return a nonzero exit status with actionable context.

### `validate`

```text
python -m market_leadership.universe_admin validate \
  --region ID --classification ID --source-id ID \
  [--exchange ID] [--database PATH] INPUT
```

Reads and validates one local CSV or supported reviewed JSON catalog without changing the
database. CSVs use `Ticker,Name,Sector,Industry`; `--exchange` is required when the file does not
provide an exchange/listing identifier. Optional `InstrumentId`, `ResolutionState`, `ProviderSymbol`,
and source effective-date fields are preserved when supplied. Rows without a ticker must
explicitly declare `ResolutionState=placeholder` and provide an `InstrumentId`.

Validation reports accepted rows, unresolved placeholders, duplicates, invalid rows, missing
classification, and conflicting memberships. A placeholder must be explicitly identified as a
placeholder and must not invent a tradable ticker. Listings with valid identity but missing
classification can be retained as unclassified, not assigned to a fabricated industry.
Conflicting or invalid rows are never resolved through source priority.
When the target database exists, validation also checks its reviewed identities, listing
attributes, classification parents, and overlapping memberships without writing to it.
Validation remains usable before initialization.

### `import`

```text
python -m market_leadership.universe_admin import \
  --region ID --classification ID --source-id ID \
  --coverage DESCRIPTION --approval-reference ID \
  [--exchange ID] [--database PATH] INPUT
```

Imports only reviewed local files. `--coverage` records the reviewed source coverage and
`--approval-reference` records the review that authorizes use. The full input is validated before
a single atomic database transaction. Structural errors reject the import and leave the last
valid database state unchanged. Invalid rows and conflicting memberships are reported and
quarantined; valid non-conflicting rows may be committed with a `committed_partial` status and
the region marked partial/unverified. Re-importing the same input is idempotent. Local reviewed
classifications and membership remain authoritative. A partial import returns a nonzero status
with counts and issue details so automation cannot mistake it for a complete import.
Each quarantined row leaves no dependent records behind. If every row is rejected, published
hierarchy, coverage, and revision remain unchanged; import-run and issue audit records may still
be recorded. An accepted matching-identity row can promote a placeholder or unclassified stock,
but incomplete later rows never downgrade reviewed identification or classification.

Idempotent replay requires the original region, classification, source, approval, coverage,
and exchange context. It returns persisted diagnostics and counts with zero inserted rows.
Source-specific coverage is retained alongside the combined regional scope; chart-only imports
do not replace exchange coverage or imply complete stock membership.
Schema version 1 is retained. Legacy runs containing only a file hash cannot establish the
original import context and are not replayed; re-review the input under a new source ID rather
than deleting historical runs or rebuilding the database.

### `represent`

```text
python -m market_leadership.universe_admin represent \
  --region ID --classification ID --entity-type sector|industry --entity-id ID \
  --exchange ID --symbol TICKER --source-id ID --approval-reference ID \
  --effective-from YYYY-MM-DD [--effective-to YYYY-MM-DD] [--database PATH]
```

Adds a reviewed chart representation only when the sector or industry exists in the requested
classification, the ticker is an active verified primary listing in the region, and the source's
stored approval reference matches. The effective period cannot overlap another representation
for the same entity. This command never adds or changes stock membership.

### `refresh`

```text
python -m market_leadership.universe_admin refresh \
  --region ID --source-id ID [--database PATH]
```

Refresh is unavailable until the application's single live provider has been selected and its
coverage, terms, and display rights have been reviewed for the requested data. It does not add a
second live-data provider. A refresh reports differences from local region,
classification, security identity, and membership records; it never silently overwrites those
records. Provider errors and incomplete coverage produce a nonzero status and an explicit report,
not an empty success.

## Shared behavior

- Every command accepts `--database PATH`; otherwise it uses the default path above.
- Commands emit a concise summary and actionable validation/source-conflict details. Failures
  return nonzero status; success-shaped fallbacks are prohibited.
- No command silently fetches from another provider or treats fixture data as live data.
- Credentials, if later required by the approved source, are read from the existing secret
  mechanism and never written to the database or command output.
