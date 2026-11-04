"""Bounded, read-only extraction of selected literal Python ETF catalogs."""

import ast
import io
import json
import tokenize
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from market_data.domain.local_etf_evidence import (
    CatalogObservation,
    CollectionRun,
    Evidence,
    Inventory,
    ResourceInspection,
    identity,
)

CONTEXT_NAMES = {
    "US_SECTOR_ETFS": "sector_context",
    "EU_SECTOR_ETFS": "sector_context",
    "EUROPE_SECTOR_ETFS": "sector_context",
    "SECTOR_ETFS": "sector_context",
    "MORNINGSTAR_SECTOR_ETFS": "sector_context",
    "ASIA_SECTOR_PROXIES": "index_context",
    "ASX_SECTOR_INDICES": "index_context",
    "METAL_PROXIES": "commodity_context",
}
INDUSTRY_NAMES = {"INDUSTRY_ETFS", "US_INDUSTRY_ETFS", "EUROPE_INDUSTRY_ETFS"}


def utc_observation(observed_at: datetime | None) -> str:
    clock = observed_at or datetime.now(UTC)
    if clock.tzinfo is None:
        raise ValueError("Local ETF observation clock must be timezone-aware")
    return clock.astimezone(UTC).isoformat()


def _string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
        return node.value
    return None


def _extract(
    tree: ast.Module,
    *,
    alias: str,
    root: Path,
    file: str,
    catalog: str,
    observed_at: str,
    optional: bool,
) -> tuple[list[Evidence], CatalogObservation]:
    kind = "industry" if catalog in INDUSTRY_NAMES else CONTEXT_NAMES.get(catalog)
    issues: list[str] = []
    entries: list[Evidence] = []
    found = False
    ordinal = 0
    if kind is None:
        issues.append(f"{file}:{catalog}: unsupported_catalog; select a supported catalog name")
    for statement in tree.body:
        value: ast.expr | None = None
        name = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            if isinstance(statement.targets[0], ast.Name):
                name, value = statement.targets[0].id, statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            name, value = statement.target.id, statement.value
        if name != catalog or kind is None:
            continue
        found = True
        if not isinstance(value, ast.Dict):
            issues.append(f"{file}:{catalog}:{statement.lineno}: unsupported_dictionary")
            continue
        for key, literal in zip(value.keys, value.values, strict=True):
            label, ticker = _string(key), _string(literal)
            context: tuple[str, ...] = ()
            if catalog == "METAL_PROXIES":
                ticker = label
                label = None
                if isinstance(literal, ast.Tuple) and len(literal.elts) == 2:
                    label, category = (_string(item) for item in literal.elts)
                    if category is not None:
                        context = (category,)
                    else:
                        label = None
            if label is None or ticker is None or key is None:
                issues.append(f"{file}:{catalog}:{literal.lineno}: unsupported_literal")
                ordinal += 1
                continue
            region = (
                "US"
                if catalog.startswith("US_")
                else "EUROPE"
                if catalog.startswith(("EUROPE_", "EU_"))
                else None
            )
            entries.append(
                Evidence(
                    resource=alias,
                    root=str(root),
                    file=file,
                    catalog=catalog,
                    label=label,
                    ticker=ticker,
                    catalog_type=kind,
                    region=region,
                    classification=None,
                    node_level="industry" if kind == "industry" else None,
                    ordinal=ordinal,
                    line=key.lineno,
                    end_line=literal.end_lineno or literal.lineno,
                    column=key.col_offset,
                    end_column=literal.end_col_offset or literal.col_offset,
                    catalog_content_id="",
                    context=context,
                    observed_at=observed_at,
                )
            )
            ordinal += 1
    if not found and not optional and kind is not None:
        issues.append(f"{file}:{catalog}: missing_catalog; check the explicit descriptor")
    content_id = identity(
        tuple(
            (
                item.label,
                item.ticker,
                item.catalog_type,
                item.region,
                item.classification,
                item.node_level,
                item.ordinal,
                item.context,
            )
            for item in entries
        )
    )
    entries = [replace(item, catalog_content_id=content_id) for item in entries]
    observation = CatalogObservation(
        identity(alias, str(root), file, catalog),
        file,
        catalog,
        not issues,
        content_id,
        tuple(item.evidence_id for item in entries),
        tuple(issues),
    )
    return entries, observation


def inspect_sources(
    *,
    roots: dict[str, Path] | None = None,
    catalogs: tuple[str, ...] = (),
    observed_at: datetime | None = None,
) -> Inventory:
    timestamp = utc_observation(observed_at)
    if not roots or not catalogs:
        raise ValueError("Local research requires explicit --root and --catalog inputs")
    if any(not alias.strip() or alias != alias.strip() for alias in roots):
        raise ValueError("Local resource aliases must be nonempty and trimmed")
    configured = dict(roots)
    descriptors: dict[str, list[tuple[str, str]]] = {alias: [] for alias in configured}
    for descriptor in catalogs:
        alias, equal, location = descriptor.partition("=")
        file, colon, catalog = location.rpartition(":")
        if not equal or not colon or not file or not catalog or alias not in configured:
            raise ValueError("Catalog must use known RESOURCE=RELATIVE_PATH:CATALOG")
        if (file, catalog) not in descriptors[alias]:
            descriptors[alias].append((file, catalog))
    if any(not items for items in descriptors.values()):
        raise ValueError("Every configured root requires an explicit --catalog descriptor")
    resources: list[ResourceInspection] = []
    evidence: list[Evidence] = []
    for alias, configured_root in sorted(configured.items()):
        try:
            root = configured_root.expanduser().resolve()
        except (OSError, RuntimeError):
            resources.append(
                ResourceInspection(
                    alias,
                    str(configured_root),
                    "inaccessible",
                    (),
                    ("invalid_root_path; correct --root explicitly",),
                )
            )
            continue
        observations: list[CatalogObservation] = []
        resource_issues: list[str] = []
        try:
            root.stat()
        except FileNotFoundError:
            resources.append(
                ResourceInspection(
                    alias,
                    str(root),
                    "missing",
                    (),
                    ("missing_root; correct --root explicitly",),
                )
            )
            continue
        except OSError:
            resources.append(
                ResourceInspection(
                    alias,
                    str(root),
                    "inaccessible",
                    (),
                    ("inaccessible_root; check permissions",),
                )
            )
            continue
        if not root.is_dir() or not descriptors[alias]:
            resources.append(
                ResourceInspection(
                    alias,
                    str(root),
                    "unsupported",
                    (),
                    ("unsupported_root; specify its actual supported --catalog",),
                )
            )
            continue
        selected_files = sorted({file for file, _ in descriptors[alias]})
        for file in selected_files:
            required = {name for path, name in descriptors[alias] if path == file}
            names = sorted(required | set(CONTEXT_NAMES))
            problem: str | None = None
            tree: ast.Module | None = None
            relative = Path(file)
            forbidden = any(
                part.lower() in {".git", ".venv", "__pycache__", "logs", "cache", "caches"}
                or any(
                    word in part.lower()
                    for word in ("secret", "credential", "portfolio", "watchlist")
                )
                for part in relative.parts
            )
            try:
                path = (root / relative).resolve()
                if (
                    relative.is_absolute()
                    or ".." in relative.parts
                    or forbidden
                    or relative.suffix != ".py"
                    or not path.is_relative_to(root)
                ):
                    problem = "unsafe_descriptor; use a mapping Python file within the root"
                else:
                    raw = path.read_bytes()
                    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
                    tree = ast.parse(raw.decode(encoding), filename=file)
            except FileNotFoundError:
                problem = "missing_file; correct the descriptor"
            except OSError:
                problem = "inaccessible_file; check permissions"
            except RuntimeError:
                problem = "unsafe_descriptor; resolve the symlink loop"
            except (SyntaxError, UnicodeError, LookupError) as error:
                line = error.lineno if isinstance(error, SyntaxError) else None
                problem = f"invalid_source_encoding_or_syntax at line {line}"
            for name in names:
                if tree is None:
                    if name not in required:
                        continue
                    issue = f"{file}:{name}: {problem}"
                    observations.append(
                        CatalogObservation(
                            identity(alias, str(root), file, name),
                            file,
                            name,
                            False,
                            None,
                            (),
                            (issue,),
                        )
                    )
                    resource_issues.append(issue)
                    continue
                items, observation = _extract(
                    tree,
                    alias=alias,
                    root=root,
                    file=file,
                    catalog=name,
                    observed_at=timestamp,
                    optional=name not in required,
                )
                observations.append(observation)
                resource_issues.extend(observation.issues)
                evidence.extend(items)
        useful = any(
            item.complete
            for item in observations
            if (item.file, item.catalog) in descriptors[alias]
        ) or any(item.resource == alias for item in evidence)
        status = (
            "inspected"
            if not resource_issues
            else "inspected_with_issues"
            if useful
            else "unsupported"
        )
        if not useful and any("inaccessible_file" in issue for issue in resource_issues):
            status = "inaccessible"
        resources.append(
            ResourceInspection(
                alias,
                str(root),
                status,
                tuple(observations),
                tuple(resource_issues),
            )
        )

    contexts = [item for item in evidence if item.catalog_type != "industry"]
    annotated: list[Evidence] = []
    for item in evidence:
        if item.catalog_type == "industry":
            facts = tuple(
                sorted(
                    {
                        f"{context.catalog_type}:"
                        + json.dumps(
                            (
                                context.label,
                                context.ticker,
                                context.region,
                                context.classification,
                                context.node_level,
                                context.context,
                            )
                        )
                        for context in contexts
                        if context.normalized_ticker == item.normalized_ticker
                    }
                )
            )
            thematic = any(
                context.normalized_ticker == item.normalized_ticker
                and any(value.lower() in ("theme", "thematic") for value in context.context)
                for context in contexts
            )
            item = replace(
                item, context=facts + (("thematic_context:source_claim",) if thematic else ())
            )
        annotated.append(item)
    # Qualification facts change evidence IDs; finalize memberships after attaching them.
    resources = [
        replace(
            resource,
            catalogs=tuple(
                replace(
                    catalog,
                    evidence_ids=tuple(
                        sorted(
                            item.evidence_id
                            for item in annotated
                            if item.source_key == catalog.source_key
                        )
                    ),
                )
                for catalog in resource.catalogs
            ),
        )
        for resource in resources
    ]
    status = (
        "complete"
        if all(r.status == "inspected" for r in resources)
        else "partial"
        if any(r.status in ("inspected", "inspected_with_issues") for r in resources)
        else "failed"
    )
    return Inventory(
        CollectionRun(str(uuid4()), timestamp, status, tuple(resources)),
        tuple(sorted(annotated, key=lambda item: item.evidence_id)),
    )
