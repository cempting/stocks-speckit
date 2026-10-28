"""Sufficient-only weekly leadership status, scoped ranks and historical changes."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from market_leadership.domain.relative_strength import (
    MissingStrengthReason,
    RelativeStrengthResult,
)


class LeadershipStatus(StrEnum):
    """Strict composite/50-session-average leadership classification."""

    GAINING = "gaining"
    DECLINING = "declining"
    NEUTRAL = "neutral"


class Momentum(StrEnum):
    """Descriptive weekly price-score and rank movement, not a forecast."""

    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    STABLE = "stable"


class MissingRankingReason(StrEnum):
    """Additional missing requirements for a status and rank."""

    MISSING_12M = "missing_12m"
    MISSING_50_SESSION_HISTORY = "missing_50_session_history"


RankIdentity = tuple[str, str, str | None, str]
RankingReason = MissingStrengthReason | MissingRankingReason


@dataclass(frozen=True, slots=True)
class LeadershipCandidate:
    """One local classification's dated strength and session composite history.

    ``composite_history`` is ordered oldest to newest; its last value is the
    current session's composite. Fifty complete sessions (including current)
    are required for an average, status and rank.
    """

    market_id: str
    level: str
    parent_node_id: str | None
    node_id: str
    name: str
    strength: RelativeStrengthResult
    composite_history: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class PriorWeeklyRank:
    """Last completed local weekly snapshot's composite and scoped rank."""

    composite: float
    rank: int


@dataclass(frozen=True, slots=True)
class LeadershipRow:
    """Rank and status are ``None`` for insufficient evidence."""

    market_id: str
    level: str
    parent_node_id: str | None
    node_id: str
    name: str
    strength: RelativeStrengthResult
    composite_average: float | None
    rank: int | None
    status: LeadershipStatus | None
    prior_composite: float | None
    prior_rank: int | None
    score_change: float | None
    rank_change: int | None
    momentum: Momentum | None
    missing_reasons: tuple[RankingReason, ...]


def _status(score: float, average: float) -> LeadershipStatus:
    if score > 0 and score > average:
        return LeadershipStatus.GAINING
    if score < 0 and score < average:
        return LeadershipStatus.DECLINING
    return LeadershipStatus.NEUTRAL


def _momentum(score_change: float, rank_change: int) -> Momentum:
    if score_change > 0 and rank_change >= 0:
        return Momentum.STRENGTHENING
    if score_change < 0 and rank_change <= 0:
        return Momentum.WEAKENING
    return Momentum.STABLE


def rank_leadership(
    candidates: Sequence[LeadershipCandidate],
    *,
    previous: Mapping[RankIdentity, PriorWeeklyRank] | None = None,
) -> list[LeadershipRow]:
    """Rank eligible rows within market, level and (for industries) parent.

    Composite descending ties use 6m, 3m, 12m descending then name ascending;
    rank is a unique position (not a fictitious rank for insufficient rows).
    Positive rank change denotes improvement. Unavailable prior evidence yields
    no deltas or momentum; opposed score/rank changes are labelled stable.
    """
    groups: dict[tuple[str, str, str | None], list[LeadershipCandidate]] = {}
    identities: set[RankIdentity] = set()
    for candidate in candidates:
        identity = (
            candidate.market_id,
            candidate.level,
            candidate.parent_node_id,
            candidate.node_id,
        )
        if identity in identities:
            raise ValueError(f"duplicate classification identity: {identity}")
        identities.add(identity)
        if not all((candidate.market_id, candidate.level, candidate.node_id, candidate.name)):
            raise ValueError("classification market, level, node and name must not be empty")
        score = candidate.strength.composite
        if score is not None and not math.isfinite(score):
            raise ValueError("composite must be finite")
        for value in candidate.strength.relative.values():
            if not math.isfinite(value):
                raise ValueError("relative strength must be finite")
        group = identity[:3]
        groups.setdefault(group, []).append(candidate)

    ranked: dict[RankIdentity, int] = {}
    for (market, level, parent), group in groups.items():
        sufficient = [
            item
            for item in group
            if item.strength.composite is not None
            and all(key in item.strength.relative for key in ("3m", "6m", "12m"))
            and len(item.composite_history) >= 50
            and all(math.isfinite(value) for value in item.composite_history[-50:])
            and not any(
                reason in item.strength.missing_reasons
                for reason in (
                    MissingStrengthReason.CURRENCY_MISMATCH,
                    MissingStrengthReason.RETURN_BASIS_MISMATCH,
                    MissingStrengthReason.NO_SHARED_END,
                    MissingStrengthReason.MISSING_3M,
                    MissingStrengthReason.MISSING_6M,
                    MissingStrengthReason.MISSING_12M,
                )
            )
        ]
        sufficient.sort(
            key=lambda item: (
                -float(item.strength.composite or 0),
                -item.strength.relative["6m"],
                -item.strength.relative["3m"],
                -item.strength.relative["12m"],
                item.name,
                item.node_id,
            )
        )
        for rank, item in enumerate(sufficient, start=1):
            ranked[market, level, parent, item.node_id] = rank

    rows: list[LeadershipRow] = []
    for item in candidates:
        identity = (item.market_id, item.level, item.parent_node_id, item.node_id)
        rank = ranked.get(identity)
        score = item.strength.composite
        reasons: list[RankingReason] = list(item.strength.missing_reasons)
        if score is None or "12m" not in item.strength.relative:
            if MissingRankingReason.MISSING_12M not in reasons:
                reasons.append(MissingRankingReason.MISSING_12M)
        if len(item.composite_history) < 50 or not all(
            math.isfinite(value) for value in item.composite_history[-50:]
        ):
            reasons.append(MissingRankingReason.MISSING_50_SESSION_HISTORY)
        average = (
            sum(item.composite_history[-50:]) / 50
            if MissingRankingReason.MISSING_50_SESSION_HISTORY not in reasons
            else None
        )
        prior = previous.get(identity) if previous is not None else None
        if prior is not None and (not math.isfinite(prior.composite) or prior.rank < 1):
            raise ValueError("prior weekly composite must be finite and rank positive")
        score_change = score - prior.composite if score is not None and prior else None
        rank_change = prior.rank - rank if rank is not None and prior else None
        momentum = (
            _momentum(score_change, rank_change)
            if score_change is not None and rank_change is not None
            else None
        )
        rows.append(
            LeadershipRow(
                market_id=item.market_id,
                level=item.level,
                parent_node_id=item.parent_node_id,
                node_id=item.node_id,
                name=item.name,
                strength=item.strength,
                composite_average=average,
                rank=rank,
                status=_status(score, average)
                if rank is not None and score is not None and average is not None
                else None,
                prior_composite=prior.composite if prior else None,
                prior_rank=prior.rank if prior else None,
                score_change=score_change,
                rank_change=rank_change,
                momentum=momentum,
                missing_reasons=tuple(reasons),
            )
        )
    return rows
