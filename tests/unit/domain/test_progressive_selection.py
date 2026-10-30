from datetime import date

from market_leadership.domain.progressive_selection import (
    ProgressiveSelection,
    reconcile_progressive_selection,
)


def reconcile(
    selection: ProgressiveSelection,
    *,
    sectors: tuple[str, ...] = ("TECH", "FIN"),
    industries: dict[str, str] | None = None,
    instruments: dict[str, str] | None = None,
    fingerprint: str = "catalog-1",
    membership_date: date = date(2026, 10, 23),
):
    return reconcile_progressive_selection(
        selection,
        valid_sector_ids=sectors,
        industry_parent_by_id=industries or {"SOFT": "TECH", "BANK": "FIN"},
        instrument_industry_by_id=instruments or {"AAA": "SOFT", "BBB": "BANK"},
        catalog_fingerprint=fingerprint,
        membership_date=membership_date,
        observation_date=date(2026, 10, 23),
    )


def test_default_selection_shows_sector_stage():
    selection = reconcile(ProgressiveSelection())

    assert selection.visible_stage == "sectors"
    assert selection.sector_id is None
    assert selection.industry_id is None
    assert selection.instrument_id is None


def test_valid_hierarchy_preserves_selection_and_selects_stock_stage():
    selection = reconcile(
        ProgressiveSelection("TECH", "SOFT", "AAA"),
        industries={"SOFT": "TECH", "BANK": "FIN"},
        instruments={"AAA": "SOFT", "BBB": "BANK"},
    )

    assert selection.visible_stage == "stock_detail"
    assert (selection.sector_id, selection.industry_id, selection.instrument_id) == (
        "TECH",
        "SOFT",
        "AAA",
    )


def test_invalid_parent_clears_all_descendants():
    selection = reconcile(
        ProgressiveSelection("UNKNOWN", "SOFT", "AAA"),
        industries={"SOFT": "TECH"},
        instruments={"AAA": "SOFT"},
    )

    assert selection.visible_stage == "sectors"
    assert selection.industry_id is None
    assert selection.instrument_id is None


def test_sector_change_clears_child_not_in_new_sector():
    selection = reconcile(
        ProgressiveSelection("FIN", "SOFT", "AAA"),
        industries={"SOFT": "TECH", "BANK": "FIN"},
        instruments={"AAA": "SOFT", "BBB": "BANK"},
    )

    assert selection.sector_id == "FIN"
    assert selection.visible_stage == "industries"
    assert selection.industry_id is None
    assert selection.instrument_id is None


def test_industry_change_clears_stock_not_in_new_industry():
    selection = reconcile(
        ProgressiveSelection("TECH", "SOFT", "BBB"),
        industries={"SOFT": "TECH"},
        instruments={"AAA": "SOFT", "BBB": "OTHER"},
    )

    assert selection.industry_id == "SOFT"
    assert selection.visible_stage == "stocks"
    assert selection.instrument_id is None


def test_catalog_change_clears_industry_and_stock_but_keeps_sector():
    selection = reconcile(
        ProgressiveSelection(
            "TECH",
            "SOFT",
            "AAA",
            catalog_fingerprint="catalog-0",
            membership_date=date(2026, 10, 16),
        ),
        industries={"SOFT": "TECH"},
        instruments={"AAA": "SOFT"},
        fingerprint="catalog-1",
        membership_date=date(2026, 10, 23),
    )

    assert selection.sector_id == "TECH"
    assert selection.visible_stage == "industries"
    assert selection.industry_id is None
    assert selection.instrument_id is None
