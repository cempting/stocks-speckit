from datetime import date

import pytest

from market_leadership.domain.rankings import (
    LeadershipCandidate,
    LeadershipStatus,
    MissingRankingReason,
    Momentum,
    PriorWeeklyRank,
    rank_leadership,
)
from market_leadership.domain.relative_strength import MissingStrengthReason, RelativeStrengthResult


def _candidate(
    node: str,
    score: float | None = 1.0,
    *,
    market: str = "US",
    level: str = "SECTOR",
    parent: str | None = None,
    name: str | None = None,
    six: float = 1,
    three: float = 1,
    twelve: float = 1,
    history: tuple[float, ...] | None = None,
) -> LeadershipCandidate:
    strength = RelativeStrengthResult(
        absolute={},
        relative={"3m": three, "6m": six, "12m": twelve} if score is not None else {},
        starting_on={},
        ending_on=date(2026, 10, 26),
        composite=score,
        missing_reasons=(),
    )
    return LeadershipCandidate(
        market_id=market,
        level=level,
        parent_node_id=parent,
        node_id=node,
        name=name or node,
        strength=strength,
        composite_history=history
        if history is not None
        else (score,) * 50
        if score is not None
        else (),
    )


def test_strict_boundaries_and_last_fifty_observations() -> None:
    entries = [
        _candidate("gain", 2, history=(1,) * 49 + (2,)),
        _candidate("decline", -2, history=(-1,) * 49 + (-2,)),
        _candidate("equal", 1, history=(1,) * 50),
        _candidate("equal_negative", -1, history=(-1,) * 50),
        _candidate("zero", 0, history=(-1,) * 49 + (0,)),
        _candidate("positive_below", 1, history=(2,) * 49 + (1,)),
        _candidate("negative_above", -1, history=(-2,) * 49 + (-1,)),
        _candidate("last_fifty", 2, history=(100,) + (1,) * 49 + (2,)),
    ]
    results = {row.node_id: row for row in rank_leadership(entries)}
    assert results["gain"].status is LeadershipStatus.GAINING
    assert results["decline"].status is LeadershipStatus.DECLINING
    for node in ("equal", "equal_negative", "zero", "positive_below", "negative_above"):
        assert results[node].status is LeadershipStatus.NEUTRAL
    assert results["last_fifty"].composite_average == pytest.approx(1.02)


def test_rank_scope_ties_and_insufficient_rows() -> None:
    rows = rank_leadership(
        [
            _candidate("z", 1, six=4, three=1, twelve=1),
            _candidate("a", 1, six=4, three=2, twelve=1),
            _candidate("b", 1, six=4, three=2, twelve=2, name="Zulu"),
            _candidate("c", 1, six=4, three=2, twelve=2, name="Alpha"),
            _candidate("missing12", None),
            _candidate("short", 3, history=(3,) * 49),
            _candidate("other-market", 5, market="JP"),
            _candidate("industry-a", 5, level="INDUSTRY", parent="tech"),
            _candidate("industry-b", 6, level="INDUSTRY", parent="finance"),
        ]
    )
    by_id = {row.node_id: row for row in rows}
    assert [by_id[node].rank for node in ("c", "b", "a", "z")] == [1, 2, 3, 4]
    assert by_id["other-market"].rank == 1
    assert by_id["industry-a"].rank == by_id["industry-b"].rank == 1
    for node, reason in (
        ("missing12", MissingRankingReason.MISSING_12M),
        ("short", MissingRankingReason.MISSING_50_SESSION_HISTORY),
    ):
        assert by_id[node].rank is None and by_id[node].status is None
        assert reason in by_id[node].missing_reasons


def test_weekly_deltas_and_momentum_use_prior_score_and_rank() -> None:
    candidates = [_candidate("strong", 2), _candidate("weak", 1), _candidate("flat", 0)]
    previous = {
        ("US", "SECTOR", None, "strong"): PriorWeeklyRank(1, 2),
        ("US", "SECTOR", None, "weak"): PriorWeeklyRank(2, 1),
        ("US", "SECTOR", None, "flat"): PriorWeeklyRank(0, 3),
    }
    results = {row.node_id: row for row in rank_leadership(candidates, previous=previous)}
    assert (
        results["strong"].score_change,
        results["strong"].rank_change,
        results["strong"].momentum,
    ) == (1, 1, Momentum.STRENGTHENING)
    assert (
        results["weak"].score_change,
        results["weak"].rank_change,
        results["weak"].momentum,
    ) == (-1, -1, Momentum.WEAKENING)
    assert (
        results["flat"].score_change,
        results["flat"].rank_change,
        results["flat"].momentum,
    ) == (0, 0, Momentum.STABLE)
    assert rank_leadership(candidates)[0].momentum is None


def test_conflicting_score_and_rank_changes_are_stable() -> None:
    result = rank_leadership(
        [_candidate("a", 2), _candidate("b", 3)],
        previous={("US", "SECTOR", None, "a"): PriorWeeklyRank(1, 1)},
    )[0]
    assert result.momentum is Momentum.STABLE


def test_missing_history_and_duplicate_node_identity_are_not_silently_ranked() -> None:
    row = rank_leadership([_candidate("a", 1, history=(float("nan"),) * 50)])[0]
    assert row.rank is None and row.status is None
    assert MissingRankingReason.MISSING_50_SESSION_HISTORY in row.missing_reasons
    with pytest.raises(ValueError, match="duplicate"):
        rank_leadership([_candidate("a"), _candidate("a")])


def test_missing_short_lookback_does_not_invent_returns_or_block_sufficient_rank() -> None:
    entry = _candidate("a")
    result = rank_leadership(
        [
            LeadershipCandidate(
                market_id=entry.market_id,
                level=entry.level,
                parent_node_id=entry.parent_node_id,
                node_id=entry.node_id,
                name=entry.name,
                strength=RelativeStrengthResult(
                    absolute={},
                    relative=entry.strength.relative,
                    starting_on={},
                    ending_on=entry.strength.ending_on,
                    composite=entry.strength.composite,
                    missing_reasons=(MissingStrengthReason.MISSING_1W,),
                ),
                composite_history=entry.composite_history,
            )
        ]
    )[0]
    assert result.rank == 1
    assert result.missing_reasons == (MissingStrengthReason.MISSING_1W,)
