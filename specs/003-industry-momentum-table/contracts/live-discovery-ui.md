# Live Discovery UI Contract

## Root Interface

The root application exposes exactly two tabs:

1. **Discovery**
2. **Industry Deep-Dive**

Fundamental Grading is not rendered. The root does not expose a synthetic-fixture, snapshot,
weekly-leadership, acceptance, or provider-selection control.

## Discovery

Discovery has one live yfinance data path.

| Input | Required behavior |
|---|---|
| Requested date | Uses the current US market date by default and cannot be future dated. |
| Refresh | Replaces only the relevant cached yfinance request. |
| Live response | Shows yfinance as source plus requested and observed dates. |
| Failed/incomplete response | Shows an actionable error or insufficiency state; does not show snapshots, fixtures, or another provider. |

## Industry Deep-Dive

Industry Deep-Dive reads one reviewed live membership catalog. It shows dated source and coverage
evidence before allowing sector, industry, member, or stock selection.

- A missing, invalid, stale, or unapproved catalog blocks member display and clears only dependent
  stock selections.
- The UI does not offer a fixture/live evidence-mode selector.
- Changing sector or industry retains only stock selections valid in the updated dated catalog.
