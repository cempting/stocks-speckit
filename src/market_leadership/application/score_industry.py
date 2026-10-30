"""Load a complete eligible peer cohort and calculate contract-defined block scores."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from market_leadership.bootstrap import load_selected_fundamentals
from market_leadership.domain.fundamentals import FundamentalBundle, FundamentalRequest
from market_leadership.domain.peer_scores import (
    PeerFacts,
    PeerScorecard,
    calculate_peer_scores,
)
from market_leadership.domain.stock_selection import MembershipEntry
from market_leadership.infrastructure.provider_errors import ProviderRequestError
from market_leadership.infrastructure.yfinance_fundamentals import adapt_yfinance_peer_facts


class FundamentalLoader(Protocol):
    def __call__(
        self,
        request: FundamentalRequest,
        *,
        refresh: bool = False,
    ) -> FundamentalBundle: ...


@dataclass(frozen=True, slots=True)
class StockScoreEvidence:
    instrument_id: str
    scorecard: PeerScorecard
    state: str
    reason: str | None = None
    market_cap: float | None = None
    market_cap_as_of: date | None = None


@dataclass(frozen=True, slots=True)
class IndustryScoreResult:
    analysis_cutoff: date
    eligible_instrument_ids: tuple[str, ...]
    stocks: tuple[StockScoreEvidence, ...]


def score_industry(
    members: tuple[MembershipEntry, ...],
    *,
    cutoff: date,
    refresh: bool = False,
    loader: FundamentalLoader = load_selected_fundamentals,
) -> IndustryScoreResult:
    active_members = tuple(entry for entry in members if entry.active_on(cutoff))
    ids = tuple(entry.instrument_id for entry in active_members)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Industry scoring requires nonempty, unique active membership")

    facts: list[PeerFacts] = []
    errors: dict[str, str] = {}
    market_caps: dict[str, tuple[float | None, date | None]] = {}
    for member in active_members:
        request = FundamentalRequest(
            member.symbol,
            provider_id="yfinance",
            cutoff=cutoff,
        )
        try:
            bundle = loader(request, refresh=refresh)
            market_caps[member.instrument_id] = (bundle.market_cap, bundle.market_cap_as_of)
            facts.append(adapt_yfinance_peer_facts(bundle, instrument_id=member.instrument_id))
        except (ProviderRequestError, ValueError) as error:
            errors[member.instrument_id] = str(error)

    scorecards = calculate_peer_scores(
        tuple(facts),
        eligible_instrument_ids=ids,
        cutoff=cutoff,
    )
    stocks = tuple(
        StockScoreEvidence(
            scorecard.instrument_id,
            scorecard,
            "error" if scorecard.instrument_id in errors else "insufficient",
            errors.get(scorecard.instrument_id)
            or scorecard.quality.reason
            or "Verified point-in-time peer evidence is insufficient.",
            *market_caps.get(scorecard.instrument_id, (None, None)),
        )
        for scorecard in scorecards
    )
    return IndustryScoreResult(cutoff, ids, stocks)
