from dataclasses import replace
from datetime import date

import pytest

from market_leadership.domain.peer_scores import (
    PeerFacts,
    calculate_peer_scores,
)

CUTOFF = date(2026, 3, 1)


def _facts(
    instrument_id: str,
    rank: float,
    *,
    available_on: date | None = date(2026, 2, 1),
) -> PeerFacts:
    return PeerFacts(
        instrument_id=instrument_id,
        facts_available_on=available_on,
        current_ttm_start=date(2025, 1, 1),
        current_ttm_end=date(2025, 12, 31),
        prior_ttm_start=date(2024, 1, 2),
        prior_ttm_end=date(2024, 12, 31),
        net_income=rank,
        revenue=100 + rank,
        prior_revenue=100,
        opening_equity=100,
        closing_equity=100,
        diluted_eps=1 + rank,
        prior_diluted_eps=1,
        operating_cash_flow=10 + rank,
        prior_operating_cash_flow=10,
        positive_capex_outflow=2,
        market_cap=100 + rank,
        market_cap_date=date(2025, 12, 31),
        currency="USD",
        market_cap_currency="USD",
    )


def _score(facts: tuple[PeerFacts, ...]):
    return calculate_peer_scores(
        facts,
        eligible_instrument_ids=tuple(item.instrument_id for item in facts),
        cutoff=CUTOFF,
    )


def test_contract_formulas_are_applied_to_normalized_facts():
    facts = _facts("stock-0", 1)
    evidence = replace(
        facts,
        net_income=20,
        revenue=120,
        prior_revenue=100,
        opening_equity=100,
        closing_equity=300,
        diluted_eps=3,
        prior_diluted_eps=2,
        operating_cash_flow=80,
        prior_operating_cash_flow=50,
        positive_capex_outflow=20,
        market_cap=500,
    )

    scores = _score((evidence, *(_facts(f"peer-{rank}", rank) for rank in range(2, 6))))
    metrics = {metric.key: metric for metric in scores[0].quality.metrics}
    metrics.update({metric.key: metric for metric in scores[0].growth.metrics})
    metrics.update({metric.key: metric for metric in scores[0].cash_flow.metrics})

    assert metrics["roe"].raw_value == 10
    assert metrics["net_margin"].raw_value is not None
    assert abs(metrics["net_margin"].raw_value - 100 * 20 / 120) < 1e-10
    assert metrics["revenue_yoy"].raw_value is not None
    assert abs(metrics["revenue_yoy"].raw_value - 20) < 1e-10
    assert metrics["diluted_eps_yoy"].raw_value == 50
    assert metrics["fcf_yield"].raw_value == 12
    assert metrics["ocf_yoy"].raw_value is not None
    assert abs(metrics["ocf_yoy"].raw_value - 60) < 1e-10


def test_five_distinct_increasing_peers_get_expected_percentiles():
    scores = _score(tuple(_facts(f"stock-{rank}", rank) for rank in range(1, 6)))

    assert [card.quality.value for card in scores] == [0, 25, 50, 75, 100]


def test_exact_ties_share_midranks_and_all_equal_peers_score_fifty():
    tied = tuple(_facts(f"stock-{index}", rank) for index, rank in enumerate((1, 2, 2, 4, 5)))
    tied_scores = _score(tied)
    assert [card.quality.value for card in tied_scores] == [0, 37.5, 37.5, 75, 100]

    equal_scores = _score(tuple(_facts(f"equal-{index}", 1) for index in range(5)))
    assert [card.quality.value for card in equal_scores] == [50] * 5


def test_four_valid_peers_are_insufficient_and_no_overall_score_exists():
    scores = _score(tuple(_facts(f"stock-{index}", index) for index in range(4)))

    assert all(card.quality.value is None for card in scores)
    assert all(metric.valid_peer_count == 4 for metric in scores[0].quality.metrics)
    assert not hasattr(scores[0], "overall")


def test_each_block_requires_both_metrics_and_positive_denominators():
    facts = tuple(_facts(f"stock-{index}", index + 1) for index in range(5))
    facts = (
        replace(facts[0], prior_revenue=0, opening_equity=0),
        *facts[1:],
    )

    scores = _score(facts)

    assert scores[0].quality.value is None
    assert scores[0].quality.metrics[0].raw_value is None
    assert scores[0].growth.value is None
    assert scores[0].growth.metrics[0].raw_value is None
    assert scores[0].cash_flow.value is not None


def test_unknown_or_post_cutoff_publication_is_insufficient():
    for availability in (None, date(2026, 3, 2)):
        scores = _score(
            tuple(
                _facts(
                    f"stock-{index}",
                    index,
                    available_on=availability,
                )
                for index in range(5)
            )
        )
        assert all(card.quality.value is None for card in scores)
        reason = scores[0].quality.metrics[0].reason
        assert reason is not None and "publication availability" in reason


def test_invalid_market_cap_date_and_currency_block_cash_flow_yield():
    facts = tuple(_facts(f"stock-{index}", index + 1) for index in range(5))
    facts = (
        replace(facts[0], market_cap_date=date(2025, 12, 30)),
        *facts[1:],
    )
    score = _score(facts)[0]

    assert score.cash_flow.value is None
    assert score.cash_flow.metrics[0].raw_value is None
    assert score.cash_flow.metrics[1].raw_value is not None


def test_duplicate_eligible_membership_is_rejected():
    with pytest.raises(ValueError, match="duplicate instruments"):
        calculate_peer_scores(
            (),
            eligible_instrument_ids=("same", "same"),
            cutoff=CUTOFF,
        )
