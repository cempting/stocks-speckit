# UI Contract: Company Risk Assessment

**Feature**: [spec.md](../spec.md) | **Models**: [data-model.md](../data-model.md)

## Surfaces and non-regressions

- Discovery and Industry Deep-Dive remain the only root tabs.
- Existing verified stock detail hosts evidence; breadcrumbs, return, charts, selection,
  thumbnail period and performance basis remain. No new tape columns.
- Reuse Quality (Gross Margin, Operating Margin, ROCE), Growth (Sales YoY, EPS YoY,
  EPS Consistency), Cash Flow (Cash Conversion, FCF Margin), native 4-8-quarter histories,
  `N/A` / `Data not available` and insufficient-history behavior.
- Peer blocks/Total Score retain their formulas and missing-vintage eligibility. Research
  cannot make unavailable scores available. Do not revive retired JSON-membership grading routes.

## Controls and scope

Use `market_leadership.company_evidence.` keys with stable instrument/listing/context identity.

- Explicit evidence mode/date: chart-date historical or separately requested current evidence.
- `Load financial evidence` / `Refresh financial evidence` for the verified open company.
- Independent `Load company research` / `Refresh company research`.
- Public evidence/source references and labelled retained history.

Current evidence visibly states observation today, not availability at an old chart date.
Historical mode uses eligible archives or actionable limitation, never historical Yahoo fetch.
Mode changes clear only dependent assessment, not breadcrumbs/chart controls.
Ordinary navigation makes zero research requests; cohort score loading stays financial-only.
Unresolved/ineligible listings never produce guessed requests. A user checkbox cannot grant rights.
Matching ticker/exchange alone never labels issuer identity verified. A conflicting same-label
successor shows mismatch/review guidance; an absent/failed/inconclusive profile shows unresolved
identity with review/retry guidance and no attached financial observations. A valid corroborated
domain-based association may display financial evidence with company ID/CIK unavailable; do not
invent labels/IDs or enable research solely because financial verification succeeded.

## Display order

1. Existing company/instrument identity and chart/evidence-date distinction.
2. Prominent cash assessment banner before peer-score numbers.
3. Existing chart/peer-score row.
4. OCF/capex/FCF overview: value/state, period/basis, currency/scale, definition, source/derived.
5. Existing eight-slot matrix from explicitly loaded financial evidence.
6. Independently loaded business/competitive/orders evidence.
7. Expandable provenance/limitations/history.

No large copied reports or unsupported machine-authored business summaries. Use permitted
structured facts/reviewed short factual claims; unsupported interpretation stays explicit.

## Cash banner acceptance

| Case | Required presentation |
|------|-----------------------|
| Unloaded | "Cash flow not assessed"; load action; no distress claim. |
| Missing/insufficient OCF or FCF | High-priority gap, affected measure/period/reason/action. |
| Failure | Error/retry; unaffected partial facts remain independently labelled. |
| Retrieval/reporting stale | Observed/reporting dates and stale warning, not current healthy fallback. |
| Non-comparable | Explained comparability limit, not automatic bank distress. |
| Zero OCF | Numeric zero and no operating cash generated in that period. |
| Negative OCF | Dated numeric value and operating cash-consumption concern. |
| Negative FCF | Dated value/definition and concern, not insolvency inference. |
| Positive valid cash | Status/date visible; no buy/sell or suitability recommendation. |

Gaps and concerns may coexist. Positive quality/growth never hides them. Missing capex alone
does not assert no cash generation when OCF and valid source-defined FCF are available;
its field remains unavailable.

## Research and errors

Business fields have independent citations. Competitive evidence distinguishes management claims,
facts and independent opinions; no "wide moat" badge. Backlog/bookings/RPO retain definitions/
dates/qualifications. Reported zero is not absence; unsupported parsing is not "not disclosed".
Conflicts remain separately attributed.

Recheck permissions even on cache/history hits. Parent identity/catalog changes invalidate only
affected evidence. Failed refresh remains an error/partial outcome; older good data is labelled
history. No success-shaped empty fallback or public cache containing selections.

## Measurement

Root AppTests prove selected-company loading/attachment, not only isolated component demos.
Controlled cases cover SC-001/003/004/005/006 at 100%. Record warmed navigation <=1 second
and zero additional research calls (SC-007). Five-user exercise requires at least four identify
status/main warning within ten seconds (SC-002). Established regressions prove SC-008.
