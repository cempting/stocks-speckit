# Acquisition and File Contract: Company Evidence

**Feature**: [spec.md](../spec.md) | **Models**: [data-model.md](../data-model.md)

These are planned use-case/reader, CLI and file interfaces, not a new HTTP service.

## Application boundary

`load_company_evidence(request, *, financial_loader, disclosure_reader, store, clock)` returns
a typed outcome. Refresh targets financial or research scope. Inject readers, UTC clock/root;
UI/session state is not a reader dependency.

Validate request/schema/context -> eligible dated listing and current permissions -> current
yfinance or historical archive -> source profile/binding verification -> normalization/warnings
-> immutable persistence -> safe outcome. Research needs separately reviewed issuer identity.
Partial income/balance failure need not erase valid cash facts. Supplemental order facts never
enter financial score fields or repair missing Yahoo vintages.

### Financial issuer verification

Before attachment, require the captured eligible dated listing plus an independently reviewed
dated listing-to-issuer reference. Corroborate a regulator-issued issuer identifier or verified
issuer-controlled domain against the issuer discriminator returned in the same one-ticker
profile acquisition. Retain both evidence references, discriminator, observation time and
effective context. Matching symbol/exchange alone, name/currency equality, or a hash/reference
constructed only from those labels cannot establish issuer continuity.

| Case | Required outcome |
|------|------------------|
| Same ticker/exchange, conflicting successor issuer | `mismatch`; no affected financial attachment or successful verified snapshot/latest pointer. Require reviewed dated successor association; do not mutate catalogs. |
| Missing/failed/inconclusive profile or missing independent reviewed issuer reference | `unresolved` with safe reason/review or retry action; no affected financial attachment or successful verified persistence. Preserve transport failure context where applicable. |
| Reviewed domain corroborated, no conflicts, nullable company ID and CIK | Verified financial association; attach permitted facts using existing instrument/listing IDs, preserving null IDs; no automatic research grant. |

Apply the same gate on cache/cohort reuse and archive selection. Identity evidence and binding
fingerprints must participate in association/cache context; recheck binding validity and conflicts
outside cached results. Archives need captured verification for the applicable dated issuer;
predecessor observations never attach to a successor. A previously good capture cannot replace
an unresolved current profile. Safe blocked/error diagnostics may be retained when permitted,
but must not publish unverified observations as verified evidence.

## Transport and extraction

- Financial: reuse one-ticker reader, four-to-eight requested quarterly histories; no guaranteed
  universal coverage, second profile fetch, or alternate provider.
- SEC: reviewed CIK -> submissions JSON -> eligible annual 10-K/20-F and quarterly 10-Q.
  Validate issuer, form, accession and document metadata. Optional approved Company Facts order
  concepts must match issuer/accession/period/context/unit, not newer restated alternatives.
- Issuer: registered HTTPS URLs on verified domains only. Validate redirects; reject credentials,
  unapproved hosts, local/private destinations and unsafe paths.
- Extraction: standard-library JSON/HTML, exact reviewed concepts/tables and source locators/
  mapping revision. Backlog/custom tags need definitions; RPO is not universally interchangeable.
  Unsupported structure is a limitation, not absence.
- Narrative interpretation: reviewed short factual structured claims with citations; no LLM,
  general crawler, full-report reproduction, keyword moat or mandatory undocumented search API.

Initial bounds: serial research <=1 request/second, <=6 HTTP requests per explicit research
operation, <=10 MiB per document, <=30 seconds per attempt and <=10-second socket waits bounded
by remaining attempt time. At most two transient network/5xx retries within the total budget;
honor Retry-After or report deferred retry when it exceeds the wait bound. No alternative-host
retry or changed identity to evade 401/403.

SEC requires an operator-configured publisher-compliant contact User-Agent before collection.
Keep it out of cache results/logs/evidence. Missing rights/contact or denied access is explicit;
the header does not guarantee access. Bounds are application policy, not proof of publisher
compliance. Add only evidence-root and required contact settings beyond existing configuration.

## Cache

- Financial `st.cache_data`: TTL 3,600 seconds, existing bounded cache and richer schema revision;
  provider/symbol/history/frequency/date/mode/normalization plus relevant identity/policy context.
- Disclosure discovery/documents/transforms: TTL 86,400 seconds, bounded entries;
  source/CIK/URL/accession/date/binding/assessment and content/mapping/schema revisions.
- Successful raw responses may support a changed parser mapping; failed parses/outcomes never
  cache as successful normalized evidence. Network/denial failures remain uncached.
- Recheck current rights/clocks outside cached results; no stale boolean without evaluation date.
- Historical captures use historical assessment date for reporting age and a visible archival
  label; current live TTL does not invalidate retention. Current source permission still applies.
- Refresh only affected keys. Return no selections, headers, credentials or transport instances.
  Offline fixtures must be isolated from live caches.

## Versioned JSON formats

Envelopes include format/version/fingerprint and finite validated public data. Reject unknown
required versions and unsafe relative paths; do not default invalid input into empty success.

| Format | Required payload |
|--------|------------------|
| `company-source-assessments-1` | Source/role/coverage/structured capabilities, routes, independent uses, status, review/time/expiry/history. |
| `company-issuer-bindings-1` | Instrument/listing/source, CIK/domain, effective dates, catalog/identity references. |
| `company-evidence-snapshot-1` | Request/association, outcome, facts/claims/provenance/failures, capture times, predecessor/hash. |
| `company-evidence-entry-1` | Association/context, latest relative snapshot path/hash, expected revision. |
| `company-reviewed-claims-1` | Association/issuer/source/document/locator, field/value/definition/kind/qualification, inspection/review references. |

Immutable snapshots precede atomic latest-pointer publication. Compare expected pointer revision
and reject silent overwrites of concurrent newer outcomes. Corruption, interrupted writes and
pointer conflicts are explicit; older success never silently replaces failure. Separate permission
is needed for raw retention; otherwise keep permitted facts/provenance/hash, not report bodies.

## Reviewer CLI

Proposed entry point: `python -m market_leadership.company_evidence_admin`, argparse patterns,
file-only evidence administration. No SQL or catalog activation.

- `review-source`: ID/role/terms/coverage/status/uses/hosts/review, optional expiry, expected
  assessment revision. Records actual permission evidence; does not grant publisher rights.
- `bind-issuer`: captured manifest, instrument/listing, CIK/domain, effective dates, identity
  reference and expected binding revision. No guessed issuer/company ID.
- `register-document`: binding/source/public URL/accession/form/dates/expected registry revision.
  Registration itself does not fetch arbitrary URLs.
- `import-claims`: versioned reviewed-claims input, verified binding/document/review references;
  normalizes supported factual claims and persists evidence without editing catalog rows.

Each supports explicit root override and `--help`; versioned JSON reports show recorded IDs/
limitations. Invalid input, rights/identity/access limits, corruption and revision conflicts give
nonzero exit and actionable context. No default approvals or secret-containing reports.

Common options: `--evidence-root` (default configured root), `--expected-revision` (required for
mutations; explicit `none` for creation), and JSON report output. Command options:

| Command | Required options | Optional options |
|---------|------------------|------------------|
| review-source | `--source-id`, `--role`, `--publisher`, `--terms-url`, `--coverage-reference`, `--authority`, `--status`, `--review-reference` | Repeated `--structured-capability`, `--permission`, `--allowed-host`, `--expires-at`; approved collection requires explicit capability/uses/hosts. |
| bind-issuer | `--manifest`, `--instrument-id`, `--listing-id`, `--effective-from`, `--identity-reference` | `--cik`, `--issuer-domain`, `--effective-to`; at least one regulator/domain identity required. |
| register-document | `--binding-id`, `--source-id`, `--document-url`, `--form`, `--review-reference` | `--published-on` or `--publication-limitation` is required; optional `--accession`, `--report-period`; unknown dates are never fabricated. |
| import-claims | `--input`, `--binding-id`, `--review-reference` | Source/document references come from validated input; no guessed defaults. |

Dates/timestamps and enum values follow the data model. A source review records explicit coverage,
authority and structured-capability assessments in its report. URL restrictions and permission
validation are identical for CLI and UI; no CLI path bypasses source gates.

## Failure/acceptance

Codes distinguish identity unresolved/mismatch, historical unavailable, unapproved/expired
source, denied/rate-limited/failed transport, size/period/unit limits, unsupported structure,
inspected absence, stale evidence, corrupt store and revision conflict.

Offline acceptance covers denial before transport, issuer mismatch before attachment (including
same-ticker/same-exchange successors), absent/failed/inconclusive profiles, missing independent
issuer references, and valid domain-based verification with company ID/CIK remaining null; cover
fresh acquisition, cache/cohort reuse and archive selection. Also cover compatible
cash definitions/periods, missing publication vintages, unsupported vs absent claims, conflicts,
targeted reuse/expiry/refresh, revoked cached display, partial/error history, concurrent/interrupted
writes, catalog immutability and no sensitive transmission.
