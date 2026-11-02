from dataclasses import replace

from market_data.domain.stock_selection import (
    SelectionContext,
    reconcile_selection,
    reconcile_selection_with_reason,
)


def test_context_changes_clear_only_invalid_dependents():
    context = SelectionContext("fixture", "TECH", "SOFTWARE", "catalog-one", "2026-10-23")
    assert reconcile_selection(context, context, ("A", "B"), ("A",)) == ("A",)
    assert (
        reconcile_selection(context, replace(context, industry_id="CHIPS"), ("A",), ("A",))
        == ("A",)
    )
    assert reconcile_selection(context, replace(context, mode="live"), ("A",), ("A",)) == ()
    assert reconcile_selection(None, context, (), ("A",)) == ()


def test_context_reconciliation_preserves_valid_intersections_and_explains_removals():
    context = SelectionContext("fixture", "TECH", "SOFTWARE", "catalog-one", "2026-10-23")
    current = replace(context, industry_id="CHIPS", catalog_fingerprint="catalog-two")

    reconciliation = reconcile_selection_with_reason(
        context,
        current,
        ("A", "B", "A"),
        ("A",),
    )

    assert reconciliation.selected_ids == ("A",)
    assert reconciliation.cleared_ids == ("B",)
    assert reconciliation.reason == (
        "Selections removed because they are not eligible in the current context."
    )
