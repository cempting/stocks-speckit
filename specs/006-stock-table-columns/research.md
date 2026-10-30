# Research: Stock Table Columns

## Decisions

### 1. Reuse the explicit fundamental-score action for CAP Type

**Decision**: Capture the current positive capitalization value from the selected provider's
existing fundamental profile only when the user triggers the established score-load action.

**Rationale**: The profile is already acquired in that action. Reusing it avoids a hidden request
or a second provider call while making absent evidence explicit before loading.

**Alternatives considered**: Fetch capitalization whenever the table renders; add a separate CAP
load action; infer CAP Type from price or industry. These add requests or misleading inference
without a requirement.

### 2. Keep current CAP Type separate from historical peer-score evidence

**Decision**: Classify current capitalization as Large >= $10B, Mid >= $2B and < $10B, Small <
$2B, or Unavailable. Do not require the stricter historical market-cap evidence used by the
peer-scoring Cash Flow block.

**Rationale**: CAP Type is a current table classification. The peer-score rule requires a dated,
currency-compatible historical capitalization for a separate historical calculation; applying it
here would incorrectly hide usable current classifications.

**Alternatives considered**: Reuse the peer-score historical gate; calculate a currency-converted
value; retain CAP Type permanently. These are unsupported by the requested current display and
would add scope.

### 3. Preserve existing charts and rename Score

**Decision**: Use the established price/50 MA and volume chart cells unchanged. Rename Score to
Total Score while retaining the existing equal-weight three-component numeric and explicit
non-numeric states.

**Rationale**: The prior table feature already implements the requested evidence behavior and
aggregate semantics.

**Alternatives considered**: Rebuild charts or redefine Total Score. Neither is requested and
would risk regression.

## Resolved Technical Context

- The selected yfinance fundamental reader already retrieves a profile as part of its explicit
  score-loading path, but its `FundamentalBundle` currently does not retain `marketCap`.
- `StockScoreEvidence` currently transports the scorecard/state to Discovery and can carry the
  optional current capitalization value without adding a separate boundary.
- A stocks-table rerun must not fetch fundamentals, capitalization, or scores. Before score
  evidence exists, CAP Type is Unavailable.
- Current CAP Type evidence is not a historical backtest input and does not alter peer-score
  formulas.
