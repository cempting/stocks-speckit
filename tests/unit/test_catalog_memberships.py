from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from market_data.domain.catalog import (
    CatalogError,
    CatalogMember,
    Classification,
    EvidenceSource,
    HierarchyNode,
    IndustryMembership,
    Listing,
    NodeType,
    Period,
    Scope,
    StockInstrument,
    StockRow,
    validate_catalog,
)
from tests.membership_helpers import counted_load

SCOPE = Scope("US", "CUSTOM", "v2")
PERIOD = Period(date(2020, 1, 1))
SOURCE = EvidenceSource(
    "reviewed-source",
    "local_file",
    "Test source",
    None,
    None,
    "review-1",
    date(2026, 10, 30),
)


def _hierarchy_node(
    node_id: str,
    node_type: NodeType,
    sector_id: str,
    parent_id: str | None = None,
    period: Period = PERIOD,
) -> HierarchyNode:
    return HierarchyNode(
        SCOPE,
        node_id,
        node_type,
        node_id,
        sector_id,
        parent_id,
        period,
        SOURCE.source_id,
        SOURCE.approval_reference,
        "own",
    )


def _validate_v2_nodes(nodes: tuple[HierarchyNode, ...]) -> None:
    classification = Classification(
        SCOPE,
        "Custom industries",
        SOURCE.source_id,
        SOURCE.approval_reference,
        Period(date(2020, 1, 1)),
        "custom",
    )
    validate_catalog(
        (classification,),
        (SOURCE,),
        nodes,
        (),
        (),
        (),
        (),
        format_version=2,
    )


def _membership_row(
    row_id: str,
    membership_id: str,
    instrument_id: str,
    industry_id: str,
    period: Period = PERIOD,
) -> StockRow:
    return StockRow(
        row_id,
        membership_id,
        SCOPE,
        instrument_id,
        None,
        instrument_id,
        industry_id,
        None,
        "identified",
        period,
        SOURCE.source_id,
        SOURCE.approval_reference,
        "reviewed",
        None,
    )


def _unverified_listing(listing_id: str) -> Listing:
    return Listing(
        listing_id,
        "instrument-a",
        "US",
        "stock",
        None,
        None,
        None,
        None,
        None,
        None,
        "unverified",
        None,
        None,
        None,
    )


def test_counted_loader_tracks_each_request_identity() -> None:
    from collections import Counter

    calls: Counter[str] = Counter()

    assert counted_load(calls, "issuer-a:income-statement", lambda: 7) == 7
    assert calls == {"issuer-a:income-statement": 1}


def test_instrument_membership_and_member_projections_are_immutable() -> None:
    instrument = StockInstrument("share-class-a", "US", None, "Example", "identified")
    membership = IndustryMembership(
        "membership-a",
        SCOPE,
        instrument.instrument_id,
        "industry-a",
        PERIOD,
        "reviewed-source",
        "review-1",
        "reviewed",
    )
    member = CatalogMember(instrument, (membership,), ())

    assert member.instrument.company_id is None
    assert member.memberships == (membership,)
    assert member.listings == ()
    with pytest.raises(FrozenInstanceError):
        instrument.name = "Changed"


@pytest.mark.parametrize(
    "values",
    [
        ("", "US", None, "Example", "identified"),
        ("instrument", "", None, "Example", "identified"),
        ("instrument", "US", None, "", "identified"),
        ("instrument", "US", None, "Example", "guessed"),
    ],
)
def test_instrument_rejects_missing_or_unreviewed_identity(values: tuple[object, ...]) -> None:
    with pytest.raises(CatalogError):
        StockInstrument(*values)


@pytest.mark.parametrize(
    "changes",
    [
        {"membership_id": ""},
        {"instrument_id": ""},
        {"industry_id": ""},
        {"source_id": ""},
        {"approval_reference": ""},
        {"review_state": "unreviewed"},
    ],
)
def test_membership_requires_scoped_reviewed_identity(changes: dict[str, str]) -> None:
    values = {
        "membership_id": "membership-a",
        "scope": SCOPE,
        "instrument_id": "instrument-a",
        "industry_id": "industry-a",
        "period": PERIOD,
        "source_id": "reviewed-source",
        "approval_reference": "review-1",
        "review_state": "reviewed",
    }
    values.update(changes)
    with pytest.raises(CatalogError):
        IndustryMembership(**values)


def test_catalog_member_rejects_duplicate_memberships_and_listing_mismatch() -> None:
    instrument = StockInstrument("instrument-a", "US", None, "Example", "identified")
    membership = IndustryMembership(
        "membership-a",
        SCOPE,
        "instrument-a",
        "industry-a",
        PERIOD,
        "reviewed-source",
        "review-1",
        "reviewed",
    )
    with pytest.raises(CatalogError, match="duplicate_membership"):
        CatalogMember(instrument, (membership, membership), ())


def test_v2_hierarchy_accepts_deep_trees_and_noncontemporaneous_union_cycles() -> None:
    nodes = [_hierarchy_node("sector-a", "sector", "sector-a")]
    nodes.append(_hierarchy_node("industry-1", "industry", "sector-a"))
    parent_id = "industry-1"
    for level in range(2, 1_101):
        node_id = f"industry-{level}"
        nodes.append(_hierarchy_node(node_id, "industry", "sector-a", parent_id))
        parent_id = node_id
    _validate_v2_nodes(tuple(nodes))

    first_period = Period(date(2020, 1, 1), date(2021, 12, 31))
    second_period = Period(date(2022, 1, 1))
    temporal_nodes = (
        _hierarchy_node("sector-a", "sector", "sector-a"),
        _hierarchy_node("industry-a", "industry", "sector-a", "industry-b", first_period),
        _hierarchy_node("industry-a", "industry", "sector-a", period=second_period),
        _hierarchy_node("industry-b", "industry", "sector-a", "industry-c", first_period),
        _hierarchy_node("industry-b", "industry", "sector-a", period=second_period),
        _hierarchy_node("industry-c", "industry", "sector-a", period=first_period),
        _hierarchy_node("industry-c", "industry", "sector-a", "industry-a", second_period),
    )
    _validate_v2_nodes(temporal_nodes)


@pytest.mark.parametrize(
    ("nodes", "code"),
    [
        (
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node("industry-a", "industry", "sector-a", "industry-b"),
                _hierarchy_node("industry-b", "industry", "sector-a", "industry-a"),
            ),
            "hierarchy_cycle",
        ),
        (
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node("industry-a", "industry", "sector-a", "industry-a"),
            ),
            "hierarchy_cycle",
        ),
        (
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node("industry-a", "industry", "sector-a", "missing"),
            ),
            "invalid_parent_reference",
        ),
        (
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node(
                    "industry-a",
                    "industry",
                    "sector-a",
                    "industry-b",
                    Period(date(2020, 1, 1), date(2021, 12, 31)),
                ),
                _hierarchy_node(
                    "industry-b",
                    "industry",
                    "sector-a",
                    period=Period(date(2021, 1, 1)),
                ),
            ),
            "invalid_parent_reference",
        ),
        (
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node("sector-b", "sector", "sector-b"),
                _hierarchy_node("industry-a", "industry", "sector-a"),
                _hierarchy_node("child", "industry", "sector-b", "industry-a"),
            ),
            "invalid_parent_reference",
        ),
    ],
)
def test_v2_hierarchy_rejects_invalid_active_edges(
    nodes: tuple[HierarchyNode, ...], code: str
) -> None:
    with pytest.raises(CatalogError, match=code):
        _validate_v2_nodes(nodes)


def test_v2_hierarchy_rejects_overlapping_parent_revisions() -> None:
    with pytest.raises(CatalogError, match="conflicting_node"):
        _validate_v2_nodes(
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node("industry-a", "industry", "sector-a"),
                _hierarchy_node("industry-b", "industry", "sector-a"),
                _hierarchy_node("child", "industry", "sector-a", "industry-a"),
                _hierarchy_node(
                    "child",
                    "industry",
                    "sector-a",
                    "industry-b",
                    Period(date(2021, 1, 1)),
                ),
            )
        )


def test_v2_hierarchy_diagnostic_identifies_invalid_edge() -> None:
    with pytest.raises(CatalogError, match="node=child; parent=missing"):
        _validate_v2_nodes(
            (
                _hierarchy_node("sector-a", "sector", "sector-a"),
                _hierarchy_node("child", "industry", "sector-a", "missing"),
            )
        )


def test_v2_allows_cross_sector_memberships_while_v1_remains_single_assignment() -> None:
    classifications = (
        Classification(
            SCOPE,
            "Custom industries",
            SOURCE.source_id,
            SOURCE.approval_reference,
            Period(date(2020, 1, 1)),
            "custom",
        ),
    )
    nodes = (
        _hierarchy_node("sector-a", "sector", "sector-a"),
        _hierarchy_node("sector-b", "sector", "sector-b"),
        _hierarchy_node("industry-a", "industry", "sector-a"),
        _hierarchy_node("industry-b", "industry", "sector-b"),
    )
    rows = (
        _membership_row("row-a", "membership-a", "instrument-a", "industry-a"),
        _membership_row("row-b", "membership-b", "instrument-a", "industry-b"),
    )
    instruments = (
        StockInstrument("instrument-a", "US", None, "instrument-a", "identified"),
    )

    with pytest.raises(CatalogError, match="conflicting_assignment"):
        validate_catalog(
            classifications,
            (SOURCE,),
            nodes,
            rows,
            (),
            (),
            (),
            format_version=1,
        )
    validate_catalog(
        classifications,
        (SOURCE,),
        nodes,
        rows,
        (),
        (),
        (),
        format_version=2,
        instruments=instruments,
    )


def test_v2_accepts_independent_overlapping_membership_sources() -> None:
    secondary = replace(
        SOURCE,
        source_id="secondary-source",
        approval_reference="secondary-approval",
    )
    classification = Classification(
        SCOPE,
        "Custom industries",
        SOURCE.source_id,
        SOURCE.approval_reference,
        Period(date(2020, 1, 1)),
        "custom",
    )
    nodes = (
        _hierarchy_node("sector-a", "sector", "sector-a"),
        _hierarchy_node("industry-a", "industry", "sector-a"),
        _hierarchy_node("industry-b", "industry", "sector-a"),
    )
    rows = (
        _membership_row("row-a", "membership-a", "instrument-a", "industry-a"),
        replace(
            _membership_row("row-b", "membership-b", "instrument-a", "industry-b"),
            source_id=secondary.source_id,
            approval_reference=secondary.approval_reference,
        ),
    )

    validate_catalog(
        (classification,),
        (SOURCE, secondary),
        nodes,
        rows,
        (),
        (),
        (),
        format_version=2,
        instruments=(
            StockInstrument("instrument-a", "US", None, "instrument-a", "identified"),
        ),
    )


def test_v2_conflicting_repeated_membership_identity_is_rejected() -> None:
    classification = Classification(
        SCOPE,
        "Custom industries",
        SOURCE.source_id,
        SOURCE.approval_reference,
        Period(date(2020, 1, 1)),
        "custom",
    )
    nodes = (
        _hierarchy_node("sector-a", "sector", "sector-a"),
        _hierarchy_node("industry-a", "industry", "sector-a"),
        _hierarchy_node("industry-b", "industry", "sector-a"),
    )
    rows = (
        replace(
            _membership_row("row-a", "shared-membership", "instrument-a", "industry-a"),
            listing=_unverified_listing("listing-a"),
        ),
        replace(
            _membership_row("row-b", "shared-membership", "instrument-a", "industry-b"),
            listing=_unverified_listing("listing-b"),
        ),
    )
    with pytest.raises(CatalogError, match="conflicting_membership"):
        validate_catalog(
            (classification,),
            (SOURCE,),
            nodes,
            rows,
            (),
            (),
            (),
            format_version=2,
            instruments=(
                StockInstrument("instrument-a", "US", None, "instrument-a", "identified"),
            ),
        )
