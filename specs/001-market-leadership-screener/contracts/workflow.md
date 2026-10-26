# Streamlit Workflow Contract

## Descriptor

```python
@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    key: str
    title: str
    url_path: str
    icon: str
    render: Callable[[], None]
    default: bool = False
```

The composition root builds an ordered tuple of descriptors and converts each descriptor to one
`st.Page`. Exactly one workflow is the default. Keys and URL paths are unique and stable.

## Workflow Rules

1. A workflow is a zero-argument function with dependencies captured by the composition root.
2. It may import Streamlit and UI components, but it may call domain behavior only through an
   application use case.
3. It owns page-level layout and widget orchestration, not formulas, eligibility, data loading, or
   cache invalidation.
4. Shared filter and drill-down values use namespaced session keys defined in `ui/state.py`.
5. The workflow renders loading, empty, insufficient, and operational-error states explicitly.
6. Displayed outcomes include as-of date and access to provenance; warnings do not overwrite the
   underlying result state.
7. A replacement implementing the same user outcome may be swapped by changing one registry entry.

## Initial Registry

| Key | Responsibility | Required use case |
|-----|----------------|-------------------|
| `scoreboard` | Default regimes, ranking, filtering, search, sort, and hierarchy movement | Browse scoreboard |
| `industry-detail` | Components, proxy, local/global context, evidence, and constituents | Inspect industry |
| `stock-research` | Candidate gates, failures, stale evidence, and research reason | Inspect industry/stock |
| `methodology` | Definitions, basis, provenance guidance, and non-advice warning | Read snapshot metadata |

## Component Contract

UI components receive typed view records or primitive display values and return only user intent.
For example, filters return a `FilterState`; they do not mutate a dataframe or session state directly.
Tables do not infer status from colors or values. Provenance components accept a complete provenance
record and mark unavailable fields explicitly.

## AppTest Evidence

Each workflow must have tests for initial render, primary interaction, empty state, insufficient-data
state, and safe operational failure. Registry tests assert one default, unique paths, deterministic
order, and successful construction when any single workflow is replaced by a test workflow.