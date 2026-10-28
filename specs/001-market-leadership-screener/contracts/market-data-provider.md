# Progressive Screener Data and Cache Contract

**Design version**: `screener-data-v1`. Local functions around the existing yfinance
boundary, not a new pluggable provider protocol. See [data model](../data-model.md).

## Source and Operations

`source_id = yfinance` throughout the new runtime path. An environment API key never
selects Massive, and an error never switches provider. Controlled test doubles are
not runtime fallback sources. No database or persistent snapshot cache is required.

| Operation | Inputs | Successful output and limits |
|---|---|---|
| Discover universe | Normalized exchange/type/cap/sector query, cutoff, page cursor | Validated candidate page plus pagination/coverage metadata; no assumption that top lists are all members |
| Resolve memberships | Universe, industry/index IDs, effective date/cutoff | Verified dated membership; explicit unsupported/partial status when not provided |
| Load daily history | Instrument, date range or full-available-history request, completed cutoff, adjustment/action options | Adjusted OHLC, volume basis, actions, actual history/session coverage and source metadata |
| Load financial facts | Instrument, statement families, requested current/prior fiscal windows, information cutoff | Raw period facts and actual availability/vintage metadata where known; missing dates remain missing |
| Resolve cap/representation | Instrument/node IDs, membership date, valuation date | Currency/date-qualified cap and qualified representation evidence, or explicit insufficiency |

These names express responsibilities, not a requirement for classes or one function per row.
No operation ranks industries or computes score percentiles.

## Universe and Representation Rules

1. Screen pages must retain cursors/offsets and reconcile reported totals where present.
   Deduplicate stable instrument IDs. Stop only on verified completion or an explicit
   partial/error condition, never a hidden row cap. Detect repeated/nonadvancing pages.
2. Map verified provider exchange codes to NYSE/Nasdaq, and distinguish common stocks,
   preferreds, ADRs, funds and ambiguous types. Ambiguous data is not presumed eligible.
3. No index membership is inferred from an ETF or broad exchange list. A requested
   unsupported index gives an unavailable state, not an unrestricted successful result.
4. Keep observed/current classification separate from verified effective-dated membership.
   Do not backdate an observation to an earlier price cutoff. Display known coverage gaps.
5. Apply union/intersection and cap-band boundaries from the model. Dollar thresholds
   require dated USD caps; no guessed FX conversion or cap observation date.
6. Prefer an explicitly qualified one-industry ETF; competing qualified ETFs require a
   recorded dated choice rather than random order. Otherwise use the greatest positive
   dated market cap among verified industry members, breaking ties by stable instrument ID.
   Missing membership/cap coverage cannot prove a largest-stock choice. Label single-company
   proxies; show missing qualified representations without rank.
7. Representations do not define membership. Exposure/rights qualification metadata may
   be reviewed statically, but no second runtime financial feed is introduced.

## Prices, Sessions and Validation

Use exchange-calendars and an injected clock to resolve the latest completed regular
session. Request enough adjusted history for the selected analyses; full available
daily history is appropriate for inspecting unbounded-duration consolidation. Show actual
coverage and truncation; source history limits are not detector maximum durations.

Use `auto_adjust=True` explicitly for OHLC and request actions where needed to validate
split handling. Specify daily interval, date inclusivity, timezone and price/volume basis.
Preserve legacy close/volume consumers separately; adding OHLC cannot silently break
their canonical frame contract.

Finite positive OHLC and consistent high/low bounds are required. Dates must be unique,
ordered and no later than cutoff. Nonnegative finite volume is not automatically
comparable across splits: verify units/normalization using action fixtures. Unknown
split comparability invalidates affected volume criteria and consolidation evidence,
not an otherwise valid price-only ADX or adjusted return.

Drop an incomplete trailing bar with explicit latest-usable-session metadata; do not
silently replace requested return endpoints with that older session. Invalid interior
bars/conflicting duplicates are validation errors, not dropped rows. Legitimately absent
sessions/history produce precise insufficiency. No forward filling across gaps.

## Fundamentals and Availability

Preserve raw field identity, units, reported sign, period boundaries, accounting basis,
availability/revision timestamps and currency. Do not label period end or retrieval as
publication. Only facts available by cutoff, with the appropriate historical version,
may contribute to scores. Unverified availability yields insufficiency.

Current/prior comparable non-overlapping TTM flows may require eight valid quarters.
ROE needs positive opening/closing common equity for the current TTM window. Current
summary ratios, estimates and annual values with different windows do not substitute
for missing facts. See [financial calculations](fundamental-scoring.md).

Successful source payloads may legitimately contain missing fields; retain those typed
gaps. Failure to retrieve/validate a payload is an operational error, not a successful
payload full of `None`. Never invent history, ratios, dates or peer counts.

## Cache Keys, TTL and Refresh

All source caches use `st.cache_data(persist=None, ttl=..., max_entries=...)`.
Initial policy:

| Payload | TTL | Key components in addition to source/version |
|---|---|---|
| Daily OHLC/actions | 15 minutes | Stable instrument and provider symbol, start/end or full-history mode, interval, adjustment/action settings, cutoff |
| Universe/membership/cap | 24 hours | Complete normalized query, dataset, cursor/offset, effective/valuation date and cutoff |
| Financial statements | 6 hours | Instrument, statement families/frequency, requested periods, currency/basis and cutoff |
| Numerical transforms | Bounded cache, keyed to immutable payload fingerprints | Source fingerprints, cutoff, detector/scoring version and actual numerical parameters |

Use canonical sorted identifiers, never mutable session selections, credentials or
underscore-excluded material arguments. Prefer per-instrument reusable price/fact keys
so sorting/filter changes or a smaller selected subset do not refetch the same data.
Compute payload fingerprints once when loading, not by rehashing full histories for
every local widget event.

Financial peer-cache identity includes the full industry/universe/cutoff/facts, and
excludes technical filters, selected rows, sort and page. Detector identity includes
volume parameters even if the spike checkbox is off.

Store `retrieved_at`/`expires_at` with successful payloads and private loaded views.
Rerenders check expiry and show stale/refresh-required state rather than treating a
session copy as permanently fresh. Cache TTL never substitutes for observation-date checks.
Do not use persistence, which changes documented TTL behavior.

Refresh clears only the applicable cached function arguments, then issues an explicit
load. Recompute dependent views from new fingerprints; do not globally clear unrelated
users/data. Refreshing a scorecard's entire peer calculation refreshes its declared full
cohort, not merely the currently visible stock. Do not cache exceptions as success.

## Error, Retry and Coverage Contract

Maintain distinct states for valid empty data, partial data, unsupported capability,
expected missing observation, stale data and operational failure. Show affected symbols,
safe operation context, loaded/failed counts and retry guidance; log diagnostic cause
without exposing credentials or sensitive paths.

Start with sequential on-demand requests. At most two retries for classified transient
connection/server failures, with bounded backoff. On rate limit, stop the affected load,
report partial progress and require explicit retry after cooldown; never tight-loop
or retry on every Streamlit rerun. No automatic retry for invalid/schema/auth requests.

Keep validated independent results; do not cache a batch containing failed members as
complete success. Track failed requests separately and retry only them. An expired
previous value may be inspected as explicitly stale context, never fresh fallback.

Contract tests use recorded synthetic/mocked payloads for all boundaries, pagination,
split/trailing-bar behavior, missing dates, request counts and failure categories.
Live smoke tests are opt-in and cannot certify completeness or legal entitlement.
