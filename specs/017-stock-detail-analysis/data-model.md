# Stock Detail Analysis Data Model

This is an internal presentation and validation model, not a new persistence format or public
service. Reuse typed history and company-evidence outcomes; do not make UI state or chart objects
the source of financial or indicator facts.

## StockDetailContext

| Field | Meaning / invariant |
|---|---|
| `instrument_id`, `listing_id`, `company_id` | Existing stable identities; company identity stays nullable and follows the reviewed issuer-binding rules. |
| `symbol`, `exchange`, `region`, `trading_currency` | Selected verified listing context, not a company-name search result. |
| `provider_id` | The application's selected runtime market-data source. |
| `as_of` | Latest requested completed-session cutoff; future observations are excluded. |
| `visible_range` | One of `1m`, `3m`, `6m`, `12m`, `18m`, or `24m`; default `6m`. |
| `history_fingerprint` | Identifies the applicable listing, provider, cutoff, request window, and normalized history revision. |

The detail view can load only for an eligible selected listing. Changing listing identity clears
or revalidates the chart, company bundle, metrics, and selected consolidation interval. Ordinary
reruns preserve valid session-local selections.

## DailyPriceHistory

| Field | Meaning / invariant |
|---|---|
| `requested_start`, `requested_end`, `as_of` | Requested coverage and explicit cutoff. The request starts early enough for the visible range and required indicator warm-up. |
| `bars` | Ordered unique completed-session observations for the selected listing only. |
| `requested_on`, `observed_on` | Request and latest actual observation dates; never shift the requested cutoff to hide a gap. |
| `coverage_state`, `reason` | Available, partial, insufficient, unavailable, or failed under the existing history boundary. |
| `provider_id`, `currency`, `price_basis` | Source and comparable adjusted-price/volume basis. |

### DailyBar

- Session date, adjusted open/high/low/close, comparable volume, source/provenance where known.
- All numeric values must be finite. Adjusted prices must be positive; volume must be non-negative.
- Dates must be unique and ordered. Duplicate or incompatible records are validation errors.
- Missing required OHLC or volume is a visible data gap; never infer high/low/open from close.
- A split-comparability or missing-session gap breaks consolidation continuity. No forward-fill.

The visible series is the requested month-based range ending at the latest completed session. The
history may include earlier bars strictly for calculation warm-up; those bars do not expand the
visible chart range.

## ChartIndicator

| Field | Meaning / invariant |
|---|---|
| `indicator_id` | `sma_50` or `sma_150`. |
| `window_sessions` | Exactly 50 or 150 completed daily closes. |
| `values` | Dated rolling simple averages on the same adjusted close basis as displayed price. |
| `state`, `reason` | Available, insufficient, unavailable, or failed; unavailable output is never zero-filled. |

Only observations at or before `as_of` may contribute. Prior observations may seed the first
visible value. If there are insufficient contiguous valid closes, keep valid price/volume visible
and report the relevant moving average as insufficient.

## ConsolidationInterval

The interval is the typed result owned by feature 001's `quiet-sideways-v1` detector, not a
chart-specific recalculation.

- Selected instrument identity and detection cutoff.
- Observable start/end, ongoing/completed status, and boundary-truncation flag.
- Consecutive qualifying-session duration.
- Observed adjusted lower/upper price corridor, width, and detector context available under
  feature 001.
- Coverage state that distinguishes no qualifying interval from insufficient evidence.

Detection uses the selected stock's own adjusted OHLC and comparable volume, historical cutoff,
the existing 150-session ADX warm-up, and preceding valid BandWidth baseline. To evaluate the
first visible candidate, request up to 271 prior valid sessions for the preceding 252 valid
20-session BandWidth values. Any unobserved gap, source limitation, or shorter listing remains
visible and is never bridged. The UI displays only the latest interval by default and may inspect
older intervals; it does not label intervals as forecasts.

## CompanyProfile

| Field | Meaning / invariant |
|---|---|
| `instrument_id`, `listing_id`, `company_id` | Existing verified association; never resolve identity by symbol/name alone. |
| `company_name`, `symbol`, `exchange` | Profile context reconciled with the selected listing. |
| `sector`, `industry` | Provider/profile context only; not membership authority. |
| `market_capitalization` | Current supported company-size observation, with currency and observation date. |
| `profile_state`, `reason` | Verified/available, partial, unavailable, unresolved, stale, or failed according to the existing company-evidence contract. |
| `source_id`, `observed_at`, `provenance` | Existing evidence-source context; no inferred publication date. |

An unverified or conflicting issuer profile cannot be attached to the selected stock. Missing
market capitalization does not hide verified listing identity. A current profile value must not
be presented as historical market capitalization.

## QuarterlyFinancialBundle

The bundle reuses the existing fundamental request, provider/cache identity, company-evidence
association, and safe partial-failure semantics.

- Request: one verified listing, selected source, quarterly frequency, current or supported
  archived date mode, cutoff, and four-to-eight-quarter window.
- Statements: income, cash flow, and balance sheet, each with its own coverage/error state.
- Profile context: company identity, reporting currency, market capitalization/date, and source
  provenance where available.
- Observations: ordered unique fiscal periods, normalized metric IDs, finite numeric values,
  units/currency/scale, source basis, publication/observation date when known, and reported or
  derived origin.
- A complete bundle can contain absent rows; absent facts are not acquisition failures. Failed,
  empty-unverified, partial, stale, or blocked components retain their existing status and safe
  explanation.

### FinancialObservation

| Field | Meaning / invariant |
|---|---|
| `metric_id` | Stable row identifier from the explicit provider mapping. |
| `period_start`, `period_end`, `fiscal_period` | Actual reported period, including non-calendar fiscal quarters. |
| `basis` | `quarterly`, `annual`, `ytd`, or `unknown`; cumulative figures are not silently converted to standalone quarters. |
| `value`, `unit`, `currency`, `source_scale` | Finite reported or derived value and its original measurement context. |
| `origin`, `input_observation_ids` | `source_supplied` or `derived`; derivations retain their input references. |
| `source_id`, `publication_date`, `observed_at` | Provenance and dated context when known; period end does not become publication date. |
| `state`, `reason` | Available, insufficient, unavailable, not-comparable, stale, error, or existing equivalent state. |

Reported zero and negative values remain numeric facts. Missing values are not replaced with zero;
currencies, scales, fiscal periods, and units are not silently combined. A gap or incompatible
period is not interpolated.

## FundamentalMetric

Existing metrics preserve feature 002's definitions and format. The following derived history
uses only aligned reported inputs and keeps its value, formula/definition, period, inputs, and
availability state accessible:

| Metric | Definition / validity |
|---|---|
| Revenue YoY | Current quarter revenue divided by revenue for the same fiscal quarter one year earlier, minus one; prior revenue must be positive. Reuse `sales_yoy` semantics. |
| Diluted EPS YoY | Current diluted EPS divided by same-fiscal-quarter EPS one year earlier, minus one; prior EPS must be positive. Reuse `eps_yoy` semantics. |
| Gross margin | Gross profit divided by revenue; positive revenue required. Reuse feature 002. |
| Operating margin | Operating income divided by revenue; positive revenue required. Reuse feature 002. |
| Net margin | Net income divided by revenue; positive revenue required. |
| FCF margin | Free cash flow divided by revenue; positive revenue and comparable cash-flow period required. Reuse feature 002. |
| ROCE | Reuse feature 002's defined TTM EBIT divided by quarter-end capital employed, requiring four consecutive EBIT quarters and a positive matching denominator. |
| Current ratio | Quarter-end current assets divided by quarter-end current liabilities; positive current liabilities required. |
| Debt-to-equity | Quarter-end total debt divided by shareholders' equity; positive equity required. |

Each derived metric has its own insufficient/unavailable state when an input, denominator, period,
currency, or publication context is missing or incompatible. Available underlying reported facts
remain visible. The view does not reinterpret or change peer scores.

## ValuationSnapshot

- Optional latest P/E, P/S, EV/EBITDA, or FCF yield.
- Snapshot date, source, currency, required numerator/denominator references, and availability
  reason.
- Display only when source dates and currency are compatible and inputs are available.
- Never create a quarterly valuation history by applying current market value to prior quarters.

## Relationships and State Boundaries

```text
StockDetailContext
  ├── DailyPriceHistory ──> ChartIndicator[50, 150]
  │                     └──> ConsolidationInterval[0..n]
  └── CompanyProfile
      └── QuarterlyFinancialBundle
          ├── FinancialObservation[quarterly statements]
          ├── FundamentalMetric[raw/derived]
          └── ValuationSnapshot[optional latest]
```

- Provider caches identify provider, selected symbol, date window/cutoff, frequency, schema, and
  relevant normalized calculation version. Caches exclude UI selections and user-specific state.
- UI selections use the existing namespaced Streamlit session state and stable listing identity.
- Existing explicit request, targeted refresh, TTL, and error semantics apply. Rendering and
  resizing do not trigger acquisition. A range change may request only the newly required coverage.
- Current live fundamental data is not backdated. Use an existing supported archived snapshot for
  historical context; otherwise show the limitation.
