# Data Model

Representation, constituent, approval, and source/provenance identities persist in
manifest-registered files under [feature 010](../010-manifest-csv-catalogs/spec.md).
Worklists use the exact reviewed hierarchy; listing/member evidence comes from the same scoped
file release and regional stock CSV. These are logical invariants, not a new serialization contract.
Preserve historical basket records and exact weights through export; no automatic basket creation.

## Representation Review Item

An active region/classification/node with current status: `etf`, `basket`, or `not_covered`.

## Stock-Basket Alternative

An approved fallback bound to a classification and effective period, with source and approval
evidence.

## Basket Constituent

A verified listing ID and positive weight. Active weights must total exactly 100%; constituents
must be valid for the basket's region and effective period.

## State Rules

Use an active approved ETF first. Only with no such ETF may an approved valid basket be used.
Invalid/incomplete evidence never receives a substitute.
