from dataclasses import replace

from market_leadership.domain.stock_selection import SelectionContext, reconcile_selection


def test_context_changes_clear_only_invalid_dependents():
    context = SelectionContext("fixture", "TECH", "SOFTWARE", "catalog-one", "2026-10-23")
    assert reconcile_selection(context, context, ("A", "B"), ("A",)) == ("A",)
    assert reconcile_selection(context, replace(context, industry_id="CHIPS"), ("A",), ("A",)) == ()
    assert reconcile_selection(context, replace(context, mode="live"), ("A",), ("A",)) == ()
    assert reconcile_selection(None, context, (), ("A",)) == ()
