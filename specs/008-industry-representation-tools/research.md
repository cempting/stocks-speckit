# Research

## Decision: Reuse reviewed representation governance

**Rationale**: Existing representations already validate region, classification, verified listing,
source approval, and effective dates.  
**Alternatives considered**: Name-based ETF inference and direct live lookup were rejected because
they are not reviewed or auditable.

## Decision: Use a weighted stock basket only as the no-ETF fallback

**Rationale**: A basket provides transparent specialist coverage without claiming an ETF exists.  
**Alternatives considered**: Parent/sector ETF and largest-stock fallbacks were rejected as
misleading substitutions.

## Decision: Require complete validated weights

**Rationale**: Weights totaling exactly 100%, verified active listings, source evidence, and
effective dates make basket momentum reproducible.
