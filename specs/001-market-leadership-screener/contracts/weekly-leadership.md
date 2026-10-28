# Calculated Weekly Leadership Snapshot Contract

This US2 contract is implemented for controlled fixture-backed weekly results with the separate
[`weekly-1.0.0` manifest](weekly-snapshot-manifest.schema.json), distinct from the Phase 2 daily
input manifest (`snapshot-manifest.schema.json`). No live non-US or licensed classification source
is claimed. A daily input manifest fails weekly loading; it is never silently upgraded.

## Publication boundary

- One immutable calculated snapshot per market, classification level, completed local-market week,
  ruleset version and compatible schema version. Publish atomically after validation; retain the
  prior good snapshot on failure. Resolve the completed week using that market's trading calendar,
  not a presumed global Friday or common observation date.
- Manifest identifies snapshot ID, market, level (`SECTOR` or `INDUSTRY`), completed-week as-of,
  built-at, schema/ruleset versions, local benchmark, currency/return bases, dated classification
  and representation versions, sources, table row counts and checksums. A new version or documented
  migration is required for incompatible changes.
- Each entry identifies node and parent where applicable; representation type, composition basis,
  effective date and source; absolute/local-relative returns for 1w/1m/3m/6m/12m; industry
  parent-sector-relative return; 3m/6m/12m composite components, composite and 50-session
  composite average; prior weekly composite and rank, score/rank deltas, rank, status and momentum;
  observation/comparison dates, availability, coverage, sufficiency reasons and provenance.
- A rank/status is absent when required twelve-month or 50-session composite history, matching
  return basis or shared ending observation is absent. Rank scope is market plus classification
  level (industry drill-down retains selected parent). Tied composites sort by 6m, then 3m, then
  12m relative strength, then name, without changing the displayed tied score.
- Keep optional global context, constituent evidence and observed flows outside the price rank.
  Missing optional inputs do not invalidate a valid local ranking. Reading a weekly artifact never
  makes an upstream provider request.

The controlled US/JP/GB fixture includes dated close histories, local benchmarks, sector/industry
ancestry and documented fixture representations. Its weekly builder calculates all five horizons,
50-session composite histories and prior score/rank deltas when a prior weekly artifact was
published. This is acceptance data, not a licensed live market source. See `deferred-evidence.md`
for additional live-source gates.
