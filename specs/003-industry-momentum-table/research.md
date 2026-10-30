# Research: Simplified Live Discovery

## Decision: Use yfinance as the sole runtime provider

**Rationale**: The existing configuration defaults to yfinance, and the bootstrap module already
constructs a cached yfinance provider. Fixing the runtime source removes provider-selection,
priority, and fallback complexity while complying with the single-free-provider constraint.

**Alternatives considered**:

- Keep the configured-provider selector: rejected because the requested interface has one live
  data experience.
- Keep Massive as a selectable alternative: rejected because it retains runtime branching and
  configuration complexity.
- Fall back to a snapshot or fixture on failure: rejected because stale or synthetic results must
  not look like live evidence.

## Decision: Remove all non-live Discovery modes from the user interface

**Rationale**: Discovery currently exposes weekly leadership, live daily, acceptance comparison,
and published snapshot modes. The live-daily path already reports data failures and caches valid
requests; retaining only it creates one understandable journey.

**Alternatives considered**:

- Hide extra modes behind an advanced control: rejected because it still creates multiple evidence
  semantics.
- Keep weekly leadership as the default: rejected because it depends on published fixture-backed
  snapshots rather than an on-demand live request.

## Decision: Restrict Industry Deep-Dive to reviewed live membership

**Rationale**: The existing live membership gate validates source, coverage, approval, and dated
catalog evidence. Requiring that gate protects industry membership from being inferred from a
proxy or a synthetic catalog.

**Alternatives considered**:

- Infer live membership from yfinance sector/industry metadata: rejected because it does not
  establish a complete, dated, reviewed catalog.
- Continue offering the synthetic catalog: rejected because users requested live data only.

## Research limitation

An official yfinance documentation lookup was attempted but could not be completed because the
local Context7 integration lacks a valid credential. This plan therefore relies on verified
repository behavior and does not introduce new yfinance API usage.
