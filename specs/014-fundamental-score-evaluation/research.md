# Fundamental Score Evaluation Research

## Decisions

### Preserve the current peer-relative scoring rules as the evaluation baseline

**Decision**: Evaluate the current six metric percentiles and equal-weight components without
changing metric definitions, directions, peer eligibility, thresholds, or weights.

**Rationale**: The implementation in
[peer_scores.py](../../packages/market-data/src/market_data/domain/peer_scores.py) defines
Quality as ROE and net margin, Growth as revenue and diluted-EPS YoY growth, and Cash Flow as
FCF yield and OCF YoY growth. Each metric is ranked higher-is-better within its eligible industry
cohort, requires at least five valid observations, and uses tied midranks. A component requires
both percentiles; the list Total Score requires all three components and is their equal mean,
displayed to one decimal. The current behavior is therefore a peer ranking, not an absolute
financial-health threshold.

**Alternatives considered**: Adding absolute solvency thresholds, changing cash-flow weights,
or replacing percentiles with a new scoring model. These would change score meaning and require
separate evidence, approval, and rules versioning; this evaluation does not authorize them.

### Treat relative rank and absolute financial condition as separate evidence

**Decision**: Label peer percentiles and the Total Score as relative to their stated cohort and
cutoff. Show raw metrics and financial context alongside percentiles; do not infer safety from a
high rank.

**Rationale**: A percentile only locates a company within its valid peer distribution; it does
not say whether the whole cohort is financially strong. Cross-sectional and time-series
comparisons answer different questions, and industry/accounting differences can make unrelated
companies difficult to compare. The
[financial-ratio overview](https://en.wikipedia.org/wiki/Financial_ratio) summarizes these
comparison limitations. This is secondary reference material used for conceptual framing, not
authority for the application's formulas.

**Alternatives considered**: Presenting a percentile as an absolute risk grade, or suppressing
peer context to make scores appear universally comparable. Both would overstate what the current
calculation measures.

### Keep cash-flow evidence, missingness, and interpretation distinct

**Decision**: Preserve missing/unassessed evidence separately from reported zero or negative
cash flow. Show the metric definition, value, period, and known provenance; describe negative
FCF as a cash-generation concern, not proof of insolvency.

**Rationale**: The current FCF-yield input is derived as OCF less positive capex outflow, divided
by dated market capitalization. FCF can be volatile because capital spending is charged when
made; year-to-year interpretation should consider surrounding periods and other evidence. The
[Investopedia FCF overview](https://www.investopedia.com/terms/f/freecashflow.asp) describes
this lumpiness and cautions against interpreting FCF in isolation. It is a secondary explainer,
so it informs disclosure, not scoring methodology. Internally, `PeerFacts` already distinguishes
`None` from numeric zero, and valid negative current cash-flow values are not automatically
discarded.

**Alternatives considered**: Filling missing values with zero, silently reweighting a component,
or treating one negative FCF period as an insolvency diagnosis. Each would conflate distinct
evidence or exceed the available model.

### Preserve the current yfinance evidence gate

**Decision**: Do not bypass missing source-vintage or dated-market-cap checks, add a provider
fallback, or fabricate publication dates. Keep affected scores explicitly unavailable until
comparable verified facts are available.

**Rationale**: `peer_facts_from_bundle()` currently returns unavailable peer facts because the
selected source path does not expose verified publication vintages or matching dated market
capitalization. This means the default live path cannot produce a supported numeric peer score
from those bundles today. Controlled `PeerFacts` fixtures remain appropriate for formula and
presentation evaluation, but they must not be confused with live-source availability.

**Alternatives considered**: Treating fetch time as publication time, using an undated market
cap, or silently switching sources. Each violates the point-in-time/comparability constraints
and would create unsupported scores.

### Correct and regression-test score state propagation

**Decision**: Set an application's stock score state from its actual result: an available
scorecard is available; metric insufficiency remains insufficient; load failure remains error.
Keep the list aggregate derived from the same scorecard.

**Rationale**: `score_industry()` currently assigns `"insufficient"` to every non-error stock at
[score_industry.py](../../src/market_leadership/application/score_industry.py), even when all
three scorecard components are available. `_overall_score_text()` returns `"Insufficient"`
before computing the aggregate when passed that state, at
[progressive_tape.py](../../src/market_leadership/ui/components/progressive_tape.py).
A deterministic controlled run with five valid peer facts produced three available components,
application state `insufficient`, and list total `Insufficient`. This is a confirmed state
propagation defect, not a proposed scoring-rule change.

**Alternatives considered**: Changing percentile calculations or making the UI ignore all
application states. The first is unrelated; the second would risk masking genuine errors and
missing-data states. Fix the producer mapping and retain explicit downstream state handling.

### Expose the six peer metrics in the existing stock detail

**Decision**: Make each of the six metric results inspectable on the existing detail surface,
including raw metric value, peer percentile, valid-peer count, state/reason, and available
period/currency/source/cutoff context. Keep the five-column stock list unchanged and do not
start new loads during rendering.

**Rationale**: The domain `PeerScorecard` retains two metric results per component, but
`render_stock_detail()` currently renders only the three component values. The separate
fundamental matrix is not the same peer-score evidence. Exposing existing metric results and
their context is needed to explain a total and meet FR-006. The data model must preserve known
metric provenance through the score result; unknown provenance remains explicitly unavailable
and must not be inferred.

**Alternatives considered**: Adding stock-list columns, treating the separate fundamental
matrix as a substitute, or hiding the metric evidence behind another provider request. Those
options either violate the presentation contract or fail to explain the score currently shown.

## Validation and Source Limitations

- The controlled state-propagation check used five distinct instruments with valid, comparable,
  pre-cutoff `PeerFacts`; it required no network request. All three component states were
  `available`, while the application and list states were incorrectly `insufficient`.
- The source facts above were verified against repository code and its current data contracts.
- The FCF interpretation reference is secondary. A CFA Institute page returned 404 and SEC staff
  guidance returned 403 in this research environment, so neither is used as verified support.
- No external reference establishes a suitable replacement threshold, metric weighting, or
  investment-risk prediction for this app. Such a change requires a separate evaluation and
  explicit approval.
