# Data Model: Company Risk Evidence

**Feature**: [spec.md](./spec.md) | **Design**: [plan.md](./plan.md)

Use frozen typed records and narrow literal states, matching domain conventions. ISO calendar
dates and timezone-aware UTC timestamps remain distinct. JSON formats start at v1; finite
numbers only. Booleans, NaN and infinity are not monetary observations.

## CompanyAssociation

| Field | Meaning / invariant |
|-------|---------------------|
| association_id | Hash of instrument/listing/source/effective binding, not a fabricated company ID. |
| instrument_id, listing_id, region_id | Captured catalog identities; eligible verified primary stock listing. |
| company_id | Existing nullable issuer ID; never synthesized. |
| provider_id, provider_symbol, exchange | Selected financial source and dated listing identity. |
| trading_currency | Independent of statement reporting currency. |
| catalog_revision, effective_from, effective_to | Exact reviewed membership/listing context. |
| issuer_key, cik, issuer_domain | Optional reviewed regulator/issuer identity; CIK is ten digits when present. A verified domain route needs neither company ID nor CIK. |
| binding_reference, identity_evidence | Independently reviewed dated listing-to-issuer reference plus returned issuer discriminator and corroboration/conflict result; never derived solely from matching listing labels. |
| state, reason | `verified`, `unresolved`, `mismatch`, `expired`; affected requests/attachments blocked. |

Financial scope requires an eligible dated reviewed listing and an independent dated issuer
reference corroborated by the acquired public source profile. Accept agreement on a reviewed
regulator-issued issuer identifier or independently verified issuer-controlled domain, with no
conflicting issuer evidence. Matching symbol/exchange is necessary listing validation, not issuer
verification; name/currency equality and hashes of listing labels cannot supply the missing proof.
Keep the reviewed reference, discriminator, source provenance and applicable effective period
in identity evidence. Domains require verified issuer control, not an arbitrary website string.

An absent/failed/inconclusive profile or missing independent reference is `unresolved`;
contradictory issuer evidence or a documented successor outside the binding's period is `mismatch`,
even with identical ticker/exchange. Block attachment of all affected financial components, not
just profile text. Independent component failures preserve facts only after identity verification.
Recheck cache/archive associations against their applicable dated binding; a verified predecessor
capture never authorizes successor attachment or resolves a failed current verification.

Company ID remains nullable; domain-based verification also leaves CIK/issuer key null when
unavailable. Association hashes are technical binding keys, never synthesized issuer identifiers.
Financial verification alone does not approve SEC/issuer research; that scope needs its own
binding and permissions. Share classes may share verified issuer research but retain distinct
financial/listing identity.

## SourceAssessment

Fields: assessment/source IDs, role (`financial`, `disclosure`, `reference`), publisher/terms/
review URLs, coverage/authority/structured capabilities, status (`unreviewed`, `approved`,
`denied`, `revoked`), allowed uses/hosts/routes, review reference/time, optional expiry, fingerprint.

Collection, normalized display, normalized retention and raw retention are independent uses.
No missing grant defaults true; expired/revoked/unknown permission blocks affected cached/stored
uses. Retain review history. Research roles cannot authorize another scored feed.

## EvidenceProvenance

Fields: source/provider and assessment fingerprint, source URL, optional document/accession,
fact/context/section/table locator, optional original publication date/time with precision,
mandatory observation time, applicable period, payload hash, mapping/schema revision, limitations.

Period end never becomes publication date; missing dates/locators remain explicitly unavailable.
Yahoo vintage limitations remain visible. URLs contain no credentials/private request data.

## FinancialObservation

Fields: observation/association IDs, metric key, optional finite value, unit/currency/source
scale, nullable period start, period end, basis (`quarterly`, `annual`, `ytd`, `unknown`),
origin (`source_supplied`, `derived`), definition/status, derivation input IDs, verified positive
capex outflow when known, provenance, state and reason.

States: `available`, `not_loaded`, `insufficient`, `unavailable`, `not_comparable`, `stale`,
`error`. Stored older/non-comparable values may remain visible with their limitation, not as
current comparable evidence. Reported zero/negative values are numeric observations.

Validation:

- Derived FCF requires finite aligned OCF/capex and verified outflow semantics, never zero defaults.
  Keep source-supplied FCF independently; source-supplied is not automatically issuer-reported.
- Do not combine currencies/scales/bases silently. Known scale may normalize to currency units,
  retaining original scale; no FX conversion, invented start date or YTD-as-quarter substitution.
- Conflicting duplicate aliases/contexts produce limitations, not last-value-wins.
- Latest relevant known statement period defines comparison; older cash is not forward-filled.
- Accepted inputs preserve existing eight-slot arithmetic; raw evidence cannot create peer vintages.

## CashFlowAssessment / CashFlowWarning

Assessment: association/context ID, requested/effective date, mode, latest relevant period,
OCF/capex/FCF observation IDs, comparability reference, warning tuple.

Warning: stable code, category (`evidence_gap`, `cash_generation_concern`), prominence,
affected measures, reason, period/source references, next action.

- Unloaded: "Cash flow not assessed", not no cash flow.
- Missing/stale/incomparable/error OCF or FCF: prominent evidence gap.
- Zero OCF: no operating cash generated in the dated period; negative OCF: cash consumption.
- Negative FCF: dated concern with definition, not insolvency/suitability inference.
- Concerns and gaps can coexist; positive quality/growth cannot hide them.
- Comparability exceptions require evidence/review, not a sector-name heuristic.
- Financial retrieval expires at >=3,600 seconds. Quarterly reporting age >135 days is stale;
  known newer statement periods without comparable cash create a gap immediately.

## CompanyResearchClaim

Fields: claim/association/issuer IDs, topic (`business_model`, `competitive_advantage`, `orders`),
field key, short factual summary or finite numeric value, unit/currency if needed, definition,
scope/qualifications, kind (`reported_fact`, `management_claim`, `independent_opinion`),
provenance, state/reason, optional inspected-disclosure scope.

Business keys: products/services, revenue model, customers/markets, segments. Orders:
backlog, bookings and remaining performance obligations are separate, definition-qualified fields.
No automatic moat rating. Independent opinion requires a named source.

States distinguish unloaded, available, not disclosed, unsupported structure, not comparable,
stale, blocked and error. Inspected absence requires an identified successfully inspected scope;
unmapped/inaccessible content is not absence. Annual research age >450 days is visibly stale;
quarterly order observations use >135 days with actual basis visible.

## Request / Outcome / Snapshot

- **CompanyEvidenceRequest**: verified association/catalog revision, financial or research scope,
  current or historical mode, date, selected provider/source set, binding/assessment fingerprints,
  history 4-8, normalization/schema revision, refresh flag.
- **CompanyEvidenceOutcome**: immutable facts/claims and safe component failures, start/capture/
  completion times, state (`complete`, `partial`, `blocked`, `error`), persisted reference if any.
- **CompanyEvidenceSnapshot**: version, request/association, outcome/provenance, content hash,
  optional predecessor, policy references. No private stock list or credential.

```text
not_loaded -> loading -> complete | partial | blocked | error
complete/partial -> stale                   (clock/reporting context)
loaded outcome -> explicit refresh -> new outcome
identity/mode/permission change -> dependent outcome invalid or blocked
```

Historical capture must be no later than the requested UTC day's end, match dated association
and retain current permission. Unknown publication vintage stays unknown. No archive record
promotes existing peer eligibility. Historical reporting age uses the requested assessment date;
historical observations are labelled captures, not expired live-cache responses or promises of
complete information available at that day's end. Live TTL does not erase retained history.
Failed refresh replaces the visible current operation status;
previous good data remains labelled history, never silent current fallback.

## Persistence / Compatibility

Root `.data/company-evidence` supports operator override. Assessments/bindings are separate
from immutable `snapshots/<association-hash>/<snapshot-hash>.json` records. An atomic latest
pointer references validated relative path/hash; compare expected revision before updating.
Concurrent newer results, corrupt hashes/schema and interrupted writes produce actionable errors.

Add optional immutable metadata to FundamentalBundle; old callers remain readable with honest
limitations. Richer cache schema isolates new acquisition. No catalog format/CSV migration,
duplicated universe, raw document retention without permission, or shared private selections.
