from datetime import date

import pytest

from market_leadership.domain.models import ProxyType
from market_leadership.domain.proxies import DocumentedRepresentation, select_representation


def _representation(**overrides) -> DocumentedRepresentation:
    values = {
        "market_id": "US",
        "node_id": "US-TECH",
        "proxy_id": "US-TECH-FUND",
        "proxy_type": ProxyType.FUND,
        "instrument_id": "TECH",
        "composition_basis": "dated fund composition",
        "source_id": "fixture",
        "qualified": True,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
    }
    return DocumentedRepresentation(**(values | overrides))


def test_representation_requires_documented_source_composition_and_effective_dates() -> None:
    for field in ("source_id", "composition_basis"):
        with pytest.raises(ValueError, match=field.replace("_", " ")):
            _representation(**{field: ""})
    with pytest.raises(ValueError, match="effective"):
        _representation(effective_to=date(2024, 12, 31))
    with pytest.raises(ValueError, match="members"):
        _representation(proxy_type=ProxyType.EQUAL_WEIGHT_BASKET, member_ids=("A", "B"))


def test_selection_fails_closed_for_unqualified_and_expired_representations() -> None:
    expired = _representation(effective_to=date(2025, 12, 31))
    unqualified = _representation(proxy_id="fund-2", qualified=False)

    selected, reason = select_representation(
        (expired, unqualified), market_id="US", node_id="US-TECH", as_of=date(2026, 10, 23)
    )

    assert selected is None
    assert reason == "NO_QUALIFIED_REPRESENTATION"


def test_selection_never_uses_another_markets_proxy_or_guesses_between_active_proxies() -> None:
    valid = _representation()
    other_market = _representation(market_id="JP", proxy_id="JP-TECH")
    selected, reason = select_representation(
        (valid, other_market), market_id="US", node_id="US-TECH", as_of=date(2026, 10, 23)
    )
    assert selected == valid
    assert reason is None
    with pytest.raises(ValueError, match="multiple"):
        select_representation(
            (valid, _representation(proxy_id="second")),
            market_id="US",
            node_id="US-TECH",
            as_of=date(2026, 10, 23),
        )
