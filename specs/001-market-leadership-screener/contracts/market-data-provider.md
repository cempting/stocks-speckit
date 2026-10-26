# Market Data Provider Contract

## Purpose

The application calculates from canonical records rather than a vendor SDK. Any adapter, including
local Parquet and deterministic fixtures, must satisfy this contract.

## Protocol

```python
class MarketDataProvider(Protocol):
    def catalog(self) -> DataCatalog: ...
    def markets(self, as_of: date) -> Sequence[Market]: ...
    def classification(self, as_of: date) -> Sequence[ClassificationNode]: ...
    def companies_and_instruments(self, as_of: date) -> InstrumentUniverse: ...
    def prices(self, request: PriceRequest) -> PriceFrame: ...
    def fx_rates(self, request: FxRequest) -> FxFrame: ...
    def proxy_inputs(self, as_of: date) -> ProxyInputs: ...
    def fundamentals(self, as_of: date) -> FundamentalFrame: ...
    def evidence(self, request: EvidenceRequest) -> Sequence[EvidenceItem]: ...
```

Requests include explicit date ranges, identifiers, return basis, and currency basis. Results are
deterministically ordered and include source ID plus availability date. Methods perform no ranking,
status, or eligibility calculation.

## Canonical Tables

| Table | Required key | Required content |
|-------|--------------|------------------|
| `markets` | `market_id`, effective interval | currency, calendar, local benchmark, scheme |
| `classification_nodes` | `node_id`, effective interval | scheme, level, parent, name |
| `companies` | `company_id`, effective interval | primary market and classification path |
| `instruments` | `instrument_id`, effective interval | kind, listing, symbol, currency, company link |
| `prices` | `instrument_id`, `date`, `return_basis` | official-session prices, volume, source, availability |
| `fx_rates` | currencies and `date` | same-close rate, source, availability |
| `fund_holdings` | fund, holding, `as_of` | weight, source, availability |
| `liquidity` | instrument, `as_of` | ADV20 USD and fund AUM where applicable |
| `fundamentals` | company, fiscal period | required survival inputs, source, availability |
| `evidence` | `evidence_id` | subject, kind, event/available dates, source, coverage |

Parquet files use string column names, UTC timestamps for retrieval metadata, ISO dates for market
dates, decimal or float values with documented units, and no serialized Python objects.

## Contract Invariants

1. `catalog()` returns dataset version, generated time, ruleset compatibility, file checksums, and
   source records before any table is read.
2. Returned data never includes observations whose `available_on` is after the requested `as_of`.
3. Instrument/date/basis keys are unique. Conflicting duplicates are an adapter error.
4. Official regular-session close is distinct from adjusted/total-return values and clearly labeled.
5. A missing same-date FX rate is returned as missing data, not forward-filled silently.
6. Effective-dated classification and proxy records resolve to at most one active record per key.
7. An empty valid query returns a typed empty result with its schema. It is not an error.

## Errors

- `SnapshotNotFound`: requested dataset or file is absent.
- `SchemaMismatch`: column, type, enum, or manifest contract is incompatible.
- `IntegrityError`: duplicate key, broken hierarchy, invalid effective interval, or checksum failure.
- `SourceUnavailable`: an upstream set is declared unavailable; callers may produce insufficiency.

Errors include dataset version, logical table, and safe context. Credentials and local absolute paths
are not included in user-visible text.

## Conformance Tests

Every adapter runs the same tests for as-of filtering, deterministic ordering, empty results, duplicate
rejection, same-date FX behavior, source traceability, and all canonical schemas. The fixture adapter
is the reference implementation, not a relaxed test double.