from datetime import date

import pytest

from market_leadership.domain.industry_etf_mappings import ClassificationEtfMapping, mapping_for


def test_mapping_is_scoped_and_date_bound() -> None:
    mapping = ClassificationEtfMapping(
        "us", "gics", "industry-software", "igv", "Software ETF", date(2020, 1, 1)
    )

    assert mapping.symbol == "IGV"
    assert mapping_for((mapping,), region_id="US", classification_id="GICS",
                       node_id="industry-software", as_of=date(2026, 10, 30)) == mapping
    assert mapping_for((mapping,), region_id="US", classification_id="GICS",
                       node_id="other", as_of=date(2026, 10, 30)) is None


def test_mapping_rejects_blank_identity_and_duplicate_active_scope() -> None:
    with pytest.raises(ValueError, match="symbol"):
        ClassificationEtfMapping("US", "GICS", "node", " ", "ETF", date(2020, 1, 1))

    first = ClassificationEtfMapping("US", "GICS", "node", "IGV", "ETF", date(2020, 1, 1))
    second = ClassificationEtfMapping("US", "GICS", "node", "SOXX", "ETF", date(2020, 1, 1))
    with pytest.raises(ValueError, match="multiple"):
        mapping_for((first, second), region_id="US", classification_id="GICS",
                    node_id="node", as_of=date(2026, 10, 30))
