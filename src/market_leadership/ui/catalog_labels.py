"""Stable display labels for deeply nested catalog nodes."""

from market_data.domain.catalog import CatalogError, HierarchyNode


def industry_path_label(
    node: HierarchyNode,
    active_nodes: tuple[HierarchyNode, ...],
) -> str:
    nodes_by_id = {item.node_id: item for item in active_nodes}
    path: list[str] = []
    visited: set[str] = set()
    current = node
    while True:
        if current.node_id in visited:
            raise CatalogError(
                "hierarchy_cycle",
                "ParentIndustryId",
                context=f"node={node.node_id}",
            )
        visited.add(current.node_id)
        path.append(current.name)
        if current.node_type == "sector":
            break
        parent_id = (
            current.parent_industry_id
            if current.parent_industry_id is not None
            else current.sector_id
        )
        parent = nodes_by_id.get(parent_id)
        if parent is None:
            raise CatalogError(
                "incomplete_membership_path",
                "ParentIndustryId/SectorId",
                context=f"node={node.node_id}; parent={parent_id}",
            )
        current = parent
    return f"{' / '.join(reversed(path))} [{node.node_id}]"
