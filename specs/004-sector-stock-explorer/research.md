# Research: Sector-to-Stock Explorer

## Decisions

### 1. Extend the existing two-tab Streamlit application

**Decision**: Keep the current `Discovery` and `Industry Deep-Dive` root tabs. Implement sector,
industry, and stock tapes plus the selected-stock detail view within the Discovery journey.

**Rationale**: The current entrypoint already uses the two-tab composition, and the latest
live-discovery specification explicitly excludes a separate Fundamental Grading tab. A detail
view in the existing journey satisfies the new behavior without reintroducing a competing route
or changing the root shell.

**Alternatives considered**: Restore the older three-tab screen; add a separate routed page.
Both expand or replace the current shell without a requirement for another top-level workflow.

### 2. Preserve stable identities and dependent selection state

**Decision**: Key selections and detail handoff by stable sector, industry, and instrument IDs.
Keep them in namespaced session-local state; clear only dependent IDs invalidated by a parent
change.

**Rationale**: This follows the current membership and selection models and prevents ticker/name
changes or duplicate display names from opening the wrong stock.

**Alternatives considered**: Use display names or tickers as selection keys; reset every selection
on each change. These can misidentify entities or discard valid user context.

### 3. Reuse the reviewed live membership and market-data boundaries

**Decision**: Reuse the current membership catalog validation and yfinance daily-history provider.
After a valid industry is selected, request history for its active members only; preserve
catalog/source/freshness information with the rows.

**Rationale**: The existing provider supports batched symbol history, and the catalog already
enforces dated stock identities and reviewed live-display access. This satisfies the all-members
view without requesting the entire market before user selection.

**Alternatives considered**: Infer members from an industry ETF or use a provisional provider
label catalog. Neither establishes the verified stock membership required by the feature.

### 4. Use the existing 001 peer-score contract, not raw metrics as scores

**Decision**: Implement and display the three 0–100 peer-percentile block scores—Quality, Growth,
and Cash Flow—according to [fundamental-scoring.md](../001-market-leadership-screener/contracts/fundamental-scoring.md).
The chosen score is computed from its two defined metrics only when both are valid; each metric
requires at least five valid peers. Do not define an overall score.

**Rationale**: The current `FundamentalScorecard` contains eight raw quarterly metrics in three
groups, but no numeric group scores. The earlier scoring contract supplies the exact formulas,
cohort rules, sufficiency threshold, tie behavior, and scale. The user selected the three peer
scores for this feature.

**Alternatives considered**: Treat the current eight raw metrics as three scores; create a new
aggregate; leave all score cells permanently unavailable. The first mislabels raw evidence, the
second invents scoring, and the third fails the selected requirement.

### 5. Load financial evidence only on explicit user intent

**Decision**: Do not fetch fundamentals on a normal tape render, selection, sort, or rerun. An
explicit score-load action loads the eligible industry peer cohort, reuses successful cached
bundles, and reports per-stock failures and score insufficiency.

**Rationale**: The existing financial workflow uses explicit load actions and its score formulas
depend on the complete unfiltered peer cohort. Automatic financial retrieval for every displayed
row would waste provider requests and obscure failures.

**Alternatives considered**: Fetch financial data for every stock as soon as the industry is
selected; calculate scores from selected/displayed rows. The first causes implicit bulk requests;
the second makes peer scores change when UI filtering changes.

### 6. Fail closed for unavailable point-in-time score evidence

**Decision**: Apply the scoring contract's cutoff, publication-availability, unit, period, and
denominator requirements. If the provider cannot establish required evidence, show the score as
insufficient/unavailable; do not use current facts for a historical cutoff or substitute another
security's data.

**Rationale**: The existing yfinance reader rejects unsupported historical live cutoffs and its
current profile/statement data do not establish all historical publication vintages. Relaxing the
contract would make historical peer scores misleading.

**Alternatives considered**: Assume report-period dates equal publication dates; use today's
profile or market cap for a historical date. Neither is supported by verified evidence.

### 7. Keep chart previews tied to each row's own history

**Decision**: Render each sector, industry, and stock thumbnail from that entity's own validated
price history. Reuse already-loaded sector and industry history; request member histories only for
the active industry. The detail chart adds volume and the requested simple moving averages.

**Rationale**: This uses existing chart logic and makes unavailable histories explicit without
cross-entity substitution.

**Alternatives considered**: Use the sector chart for its industries or ETF representation charts
for their member stocks. These would misrepresent the row's entity.

## Resolved Technical Context

- Python 3.12 and the existing Streamlit/pandas/Altair/yfinance stack are already pinned or
  constrained in `pyproject.toml`.
- The existing root application has two Streamlit tabs and uses yfinance for live Discovery.
- The sector/industry discovery workflow currently loads representation history; it does not load
  every member-stock history or render the progressive stock tape.
- The existing live membership catalog has stable instrument IDs, effective dates, source
  metadata, and explicit live-access validation.
- The existing fundamental bundle/cache and raw-metric scorecard can be reused as acquisition and
  cache foundations. A separate pure peer-score calculation remains required by the accepted
  score definition.
- pytest, Streamlit AppTest, Ruff, and Pyright are configured. No new dependency or unresolved
  technology choice is required.
