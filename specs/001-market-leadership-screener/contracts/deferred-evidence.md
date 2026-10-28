# Deferred Canonical Input Contracts

These are release-target records, **not Phase 2 provider capabilities**. Each contract is introduced
with failing contract tests before its owning story implementation. Fixture availability never
implies a licensed, refreshable live source. Before enabling a live adapter, record its data
coverage, usage/display rights, calendar, return basis, source availability, freshness policy and
error behavior; otherwise expose the dataset as unavailable, without substituting price or volume.

| Owning phase | Required canonical record (key) | Validation and failure behavior |
|---|---|---|
| US1 | Market and local benchmark (`market_id`, effective interval); optional global benchmark/FX (`currency pair`, session) | Currency, calendar, return basis, dated source and availability; same-close FX only. Missing FX blocks global comparisons alone. US/JP/GB acceptance is fixture-only. |
| US2 | Sector/industry node and representation (`node_id`, effective interval); weekly calculated snapshot (`market_id`, level, completed-week date, ruleset) | Acyclic dated ancestry, fund/index/basket type, composition basis and effective dates. Missing required proxy history blocks only affected price rank. Do not reinterpret Phase 2 daily-input manifests; use a separately versioned weekly artifact. |
| US3 | Dated membership, constituent history and weights (`node_id`, `instrument_id`, effective interval); daily close/volume (`instrument_id`, session) | Reject duplicate/conflicting memberships or weights; report eligible/included counts and coverage. Missing weights affects concentration, missing history affects breadth, missing volume affects activity, never the existing price rank. |
| US4 | Observed fund net flow and assets (`fund_id`, event period, source version) | Distinguish event period, publication date, monetary units, assets date, represented classification, overlap group, age and coverage. Only positive, compatible assets permit `100 * net_flow / assets`; do not sum overlapping funds without documented treatment. Stale/partial/unavailable means no observed-flow claim, not a change to rank. |
| US5 | Per-result provenance and freshness (subject, metric, source) | Observation/comparison period, return/currency bases, benchmark, representation, availability date, source and coverage; missing fields explicitly unavailable, stale/insufficient dependent metrics suppressed. |

The [calculated weekly snapshot contract](weekly-leadership.md) and fixture conformance must precede weekly publication and read
(`snapshot-manifest.schema.json` remains the Phase 2 input manifest). A compatible producer and
consumer version is required for weekly scoreboards; never pass a daily input snapshot off as a
completed ranking.
