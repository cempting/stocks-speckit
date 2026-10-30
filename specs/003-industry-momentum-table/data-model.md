# Data Model: Simplified Live Discovery

## Live Discovery Context

| Field | Description | Validation |
|---|---|---|
| `provider_id` | Runtime price-data provider | Fixed to `yfinance` |
| `requested_as_of` | User-requested US market date | Not in the future |
| `observed_as_of` | Latest completed session delivered by the provider | Must be shown; never substituted |
| `source_id` | Source attached to returned history | Must identify yfinance |
| `freshness` | Current, stale, or insufficient result state | Derived from completed-session coverage |

## Live Industry Membership Context

| Field | Description | Validation |
|---|---|---|
| `catalog_path` | Reviewed live membership catalog location | Required |
| `mode` | Membership evidence mode | Fixed to `live` |
| `observed_on` | Catalog observation date | Required and used for membership selection |
| `approval_reference` | Evidence-review record | Required before member display |
| `sector_id` / `industry_id` | Current dated classification selection | Stable catalog identifiers |

## Session State

| Key category | Purpose | Rule |
|---|---|---|
| Discovery controls | Current live requested date and refresh state | No evidence-mode or provider-selection state |
| Membership selection | Current sector, industry, and selected stock identifiers | Clear only selections invalidated by a new catalog or parent selection |

## State Transitions

1. A live Discovery request succeeds only when yfinance returns sufficient completed-session data.
2. A failed or incomplete request shows an error or insufficiency state; it does not transition to
   fixture, snapshot, or alternate-provider data.
3. A valid reviewed live catalog permits sector and industry selection.
4. An invalid, stale, or unapproved catalog clears dependent selected stocks and blocks member
   display.
