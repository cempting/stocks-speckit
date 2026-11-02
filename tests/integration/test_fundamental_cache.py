from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from market_data.domain.catalog import Scope
from market_data.domain.fundamentals import FundamentalRequest
from market_data.domain.stock_selection import MembershipEntry
from market_leadership.application.score_industry import (
    PEER_OBSERVATION_BASIS,
    PEER_SCORE_RULES_REVISION,
    PeerComparisonContext,
    score_industry,
)
from market_leadership.infrastructure.yfinance_fundamentals import FundamentalAcquisitionError
from market_leadership.ui.cache import (
    clear_company_evidence_caches,
    load_company_financial_bundle,
    load_fundamental_bundle,
    refresh_fundamental_bundle,
)
from tests.integration.test_yfinance_fundamentals import FakeTicker


def test_fresh_reuse_key_isolation_expiry_and_targeted_refresh():
    calls = []

    def factory(symbol):
        calls.append(symbol)
        ticker = FakeTicker()
        ticker.info = {**ticker.info, "symbol": symbol}
        return ticker

    request = FundamentalRequest("CACHE-TEST")
    now = datetime.now(UTC)
    first = refresh_fundamental_bundle(request, _factory=factory, now=now)
    assert load_fundamental_bundle(request, _factory=factory, now=now) == first
    other = replace(request, symbol="OTHER")
    refresh_fundamental_bundle(other, _factory=factory, now=now)
    refresh_fundamental_bundle(request, _factory=factory, now=now)
    load_fundamental_bundle(other, _factory=factory, now=now)
    assert calls == ["CACHE-TEST", "OTHER", "CACHE-TEST"]
    load_fundamental_bundle(request, _factory=factory, now=now + timedelta(seconds=3601))
    assert calls[-1] == "CACHE-TEST"
    assert len(calls) == 4
    load_fundamental_bundle(replace(request, schema_version=2), _factory=factory, now=now)
    assert len(calls) == 5


def test_failed_operation_is_not_cached():
    class Empty(FakeTicker):
        info = {}

    calls = []
    request = FundamentalRequest("FAILED-CACHE")
    for _ in range(2):
        with pytest.raises(FundamentalAcquisitionError):
            load_fundamental_bundle(request, _factory=lambda _: calls.append(1) or Empty())
    assert len(calls) == 2


def test_company_financial_cache_rechecks_identity_policy_context_and_targeted_refresh():
    clear_company_evidence_caches()
    calls = []

    def factory(symbol):
        calls.append(symbol)
        ticker = FakeTicker()
        ticker.info = {**ticker.info, "symbol": symbol}
        return ticker

    request = FundamentalRequest("COMPANY-CACHE")
    now = datetime.now(UTC)
    key = {
        "binding_fingerprint": "a" * 64,
        "assessment_fingerprint": "b" * 64,
        "source_ids": ("yfinance",),
        "as_of": now.date(),
        "mode": "current",
        "normalization_revision": "normalization-1",
        "schema_revision": "schema-1",
        "_factory": factory,
        "now": now,
    }
    first = load_company_financial_bundle(request, **key)
    assert load_company_financial_bundle(request, **key) == first
    assert len(calls) == 1

    changed_binding = {**key, "binding_fingerprint": "c" * 64}
    load_company_financial_bundle(request, **changed_binding)
    changed_policy = {**key, "assessment_fingerprint": "d" * 64}
    load_company_financial_bundle(request, **changed_policy)
    changed_mode = {**key, "mode": "historical"}
    load_company_financial_bundle(request, **changed_mode)
    assert len(calls) == 4

    load_company_financial_bundle(request, **{**changed_binding, "refresh": True})
    load_company_financial_bundle(request, **key)
    assert len(calls) == 5

    load_company_financial_bundle(
        request, **{**key, "now": now + timedelta(seconds=3601)}
    )
    assert len(calls) == 6
    clear_company_evidence_caches()


def test_company_financial_cache_reuses_only_explicitly_loaded_a_b_a_peer_requests():
    clear_company_evidence_caches()
    calls = []
    now = datetime.now(UTC)
    cutoff = now.date()

    def factory(symbol):
        calls.append(symbol)
        ticker = FakeTicker()
        ticker.info = {**ticker.info, "symbol": symbol}
        return ticker

    def member(instrument_id):
        symbol = instrument_id.upper()
        return MembershipEntry(
            instrument_id,
            None,
            symbol,
            instrument_id,
            "TESTEX",
            "USD",
            "sector-a",
            "Sector A",
            "industry-a",
            "Industry A",
            date(2020, 1, 1),
            None,
        )

    cohort_a = (member("peer-a"), member("peer-shared"))
    cohort_b = (member("peer-shared"), member("peer-b"))
    binding_fingerprints = {
        "PEER-A": "a" * 64,
        "PEER-SHARED": "b" * 64,
        "PEER-B": "c" * 64,
    }
    requests = []

    def load(request, *, refresh=False):
        requests.append(request)
        return load_company_financial_bundle(
            request,
            binding_fingerprint=binding_fingerprints[request.symbol],
            assessment_fingerprint="d" * 64,
            source_ids=("yfinance",),
            as_of=cutoff,
            mode="current",
            normalization_revision="normalization-1",
            schema_revision="schema-1",
            refresh=refresh,
            _factory=factory,
            now=now,
        )

    def compare(members, industry_id):
        ids = tuple(item.instrument_id for item in members)
        context = PeerComparisonContext(
            Scope("US", "CUSTOM", "v2"),
            industry_id,
            cutoff,
            ids,
            tuple((item.instrument_id, f"listing-{item.instrument_id}") for item in members),
            f"cohort-{industry_id}",
            PEER_SCORE_RULES_REVISION,
            PEER_OBSERVATION_BASIS,
        )
        return score_industry(
            members,
            cutoff=cutoff,
            loader=load,
            cohort_fingerprint=context.cohort_fingerprint,
            comparison_context=context,
        )

    assert calls == []
    result_a = compare(cohort_a, "industry-a")
    assert calls == ["PEER-A", "PEER-SHARED"]
    result_b = compare(cohort_b, "industry-b")
    assert requests[1] == requests[2]
    assert calls == ["PEER-A", "PEER-SHARED", "PEER-B"]
    returned_a = compare(cohort_a, "industry-a")

    assert result_a.eligible_instrument_ids == ("peer-a", "peer-shared")
    assert result_b.eligible_instrument_ids == ("peer-shared", "peer-b")
    assert returned_a.result_fingerprint == result_a.result_fingerprint
    assert calls == ["PEER-A", "PEER-SHARED", "PEER-B"]
    clear_company_evidence_caches()
