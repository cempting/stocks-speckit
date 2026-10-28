from datetime import date

import pytest

from market_leadership.domain.industry_proxies import (
    IndustryProxyCandidate,
    IndustryProxyKind,
    select_industry_proxy,
)


def _candidate(**overrides) -> IndustryProxyCandidate:
    values = {
        "market_id": "US",
        "sector_node_id": "US-TECH",
        "industry_node_id": "US-TECH-SOFTWARE",
        "symbol": "SOFT",
        "name": "Software ETF",
        "kind": IndustryProxyKind.ETF,
        "source_id": "issuer",
        "composition_basis": "tracks an official software industry index",
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "available_on": date(2026, 10, 23),
        "rights_verified": True,
        "qualified": True,
        "member_verified": False,
        "market_cap": None,
        "market_cap_as_of": None,
    }
    return IndustryProxyCandidate(**(values | overrides))


def test_industry_proxy_prefers_qualified_etf_over_largest_member_stock() -> None:
    etf = _candidate()
    stock = _candidate(
        symbol="STOCK",
        name="Largest software company",
        kind=IndustryProxyKind.STOCK,
        source_id="licensed-membership",
        composition_basis="verified dated industry membership",
        member_verified=True,
        market_cap=1_000_000_000_000,
        market_cap_as_of=date(2026, 10, 23),
    )

    selected, reason = select_industry_proxy(
        (stock, etf),
        market_id="US",
        sector_node_id="US-TECH",
        industry_node_id="US-TECH-SOFTWARE",
        as_of=date(2026, 10, 23),
    )

    assert selected == etf
    assert reason is None


def test_industry_proxy_uses_largest_verified_as_of_member_when_no_qualified_etf() -> None:
    smaller = _candidate(
        symbol="SMALL",
        kind=IndustryProxyKind.STOCK,
        member_verified=True,
        market_cap=10_000_000_000,
        market_cap_as_of=date(2026, 10, 23),
    )
    larger = _candidate(
        symbol="LARGE",
        kind=IndustryProxyKind.STOCK,
        member_verified=True,
        market_cap=20_000_000_000,
        market_cap_as_of=date(2026, 10, 23),
    )

    selected, reason = select_industry_proxy(
        (smaller, larger),
        market_id="US",
        sector_node_id="US-TECH",
        industry_node_id="US-TECH-SOFTWARE",
        as_of=date(2026, 10, 23),
    )

    assert selected == larger
    assert reason is None


def test_industry_proxy_ties_are_deterministic_and_unqualified_data_fails_closed() -> None:
    tied = (
        _candidate(
            symbol="ZZZ",
            kind=IndustryProxyKind.STOCK,
            member_verified=True,
            market_cap=100,
            market_cap_as_of=date(2026, 10, 23),
        ),
        _candidate(
            symbol="AAA",
            kind=IndustryProxyKind.STOCK,
            member_verified=True,
            market_cap=100,
            market_cap_as_of=date(2026, 10, 23),
        ),
    )
    selected, reason = select_industry_proxy(
        tied,
        market_id="US",
        sector_node_id="US-TECH",
        industry_node_id="US-TECH-SOFTWARE",
        as_of=date(2026, 10, 23),
    )
    assert selected == tied[1]
    assert reason is None

    missing_cap = _candidate(
        kind=IndustryProxyKind.STOCK,
        member_verified=True,
        market_cap=100,
        market_cap_as_of=date(2026, 10, 22),
    )
    selected, reason = select_industry_proxy(
        (missing_cap,),
        market_id="US",
        sector_node_id="US-TECH",
        industry_node_id="US-TECH-SOFTWARE",
        as_of=date(2026, 10, 23),
    )
    assert selected is None
    assert reason == "NO_QUALIFIED_REPRESENTATION"


def test_industry_proxy_rejects_multiple_qualified_etfs_and_other_parent_context() -> None:
    with pytest.raises(ValueError, match="multiple"):
        select_industry_proxy(
            (_candidate(), _candidate(symbol="OTHER")),
            market_id="US",
            sector_node_id="US-TECH",
            industry_node_id="US-TECH-SOFTWARE",
            as_of=date(2026, 10, 23),
        )

    wrong_parent = _candidate(sector_node_id="US-COMMS")
    selected, reason = select_industry_proxy(
        (wrong_parent,),
        market_id="US",
        sector_node_id="US-TECH",
        industry_node_id="US-TECH-SOFTWARE",
        as_of=date(2026, 10, 23),
    )
    assert selected is None
    assert reason == "NO_QUALIFIED_REPRESENTATION"
