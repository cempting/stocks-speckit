"""Load a complete eligible peer cohort and calculate contract-defined block scores."""

import json
from dataclasses import dataclass, replace
from datetime import date
from hashlib import sha256
from typing import Protocol

from market_data.domain.catalog import Scope
from market_data.domain.fundamentals import FundamentalBundle, FundamentalRequest
from market_data.domain.peer_scores import (
    PeerFacts,
    PeerScorecard,
    calculate_peer_scores,
)
from market_data.domain.stock_selection import MembershipEntry
from market_leadership.bootstrap import load_selected_fundamentals
from market_leadership.infrastructure.provider_errors import ProviderRequestError
from market_leadership.infrastructure.yfinance_fundamentals import adapt_yfinance_peer_facts

PEER_SCORE_RULES_REVISION = "peer-score-v1"
PEER_OBSERVATION_BASIS = "published-statements;dated-ttm;dated-market-cap;currency-matched"


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
class PeerComparisonContext:
    scope: Scope
    industry_id: str
    membership_as_of: date
    eligible_instrument_ids: tuple[str, ...]
    eligible_listing_ids: tuple[tuple[str, str], ...]
    cohort_fingerprint: str
    rules_revision: str
    observation_basis: str
    fact_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.industry_id.strip() or not self.cohort_fingerprint.strip():
            raise ValueError("Peer comparison context requires an industry and cohort")
        if not self.rules_revision.strip() or not self.observation_basis.strip():
            raise ValueError("Peer comparison context requires rules and observation basis")
        if len(set(self.eligible_instrument_ids)) != len(self.eligible_instrument_ids):
            raise ValueError("Peer comparison context has duplicate instruments")
        if len(set(self.eligible_listing_ids)) != len(self.eligible_listing_ids):
            raise ValueError("Peer comparison context has duplicate listings")
        if any(
            instrument_id not in self.eligible_instrument_ids
            for instrument_id, _ in self.eligible_listing_ids
        ):
            raise ValueError("Peer comparison listing does not belong to an eligible instrument")


@dataclass(frozen=True, slots=True)
class IndustryScoreResult:
    analysis_cutoff: date
    eligible_instrument_ids: tuple[str, ...]
    stocks: tuple[StockScoreEvidence, ...]
    cohort_fingerprint: str | None = None
    context: PeerComparisonContext | None = None

    def __post_init__(self) -> None:
        if self.context is not None and (
            self.context.eligible_instrument_ids != self.eligible_instrument_ids
            or self.context.cohort_fingerprint != self.cohort_fingerprint
        ):
            raise ValueError("Peer comparison result does not match its context")

    @property
    def result_fingerprint(self) -> str | None:
        if self.context is None:
            return None
        payload = json.dumps(
            {
                "scope": self.context.scope,
                "industry_id": self.context.industry_id,
                "membership_as_of": self.context.membership_as_of,
                "eligible_instrument_ids": self.context.eligible_instrument_ids,
                "eligible_listing_ids": self.context.eligible_listing_ids,
                "cohort_fingerprint": self.context.cohort_fingerprint,
                "rules_revision": self.context.rules_revision,
                "observation_basis": self.context.observation_basis,
                "fact_fingerprint": self.context.fact_fingerprint,
            },
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        return sha256(payload.encode()).hexdigest()


def score_industry(
    members: tuple[MembershipEntry, ...],
    *,
    cutoff: date,
    refresh: bool = False,
    loader: FundamentalLoader = load_selected_fundamentals,
    cohort_fingerprint: str | None = None,
    comparison_context: PeerComparisonContext | None = None,
) -> IndustryScoreResult:
    active_members = tuple(entry for entry in members if entry.active_on(cutoff))
    ids = tuple(entry.instrument_id for entry in active_members)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Industry scoring requires nonempty, unique active membership")
    if comparison_context is not None and (
        comparison_context.eligible_instrument_ids != ids
        or comparison_context.cohort_fingerprint != cohort_fingerprint
        or comparison_context.membership_as_of != cutoff
    ):
        raise ValueError("Peer comparison context does not match active membership")

    facts: list[PeerFacts] = []
    errors: dict[str, str] = {}
    market_caps: dict[str, tuple[float | None, date | None]] = {}
    fact_references: dict[str, str] = {}
    for member in active_members:
        request = FundamentalRequest(
            member.symbol,
            provider_id="yfinance",
            cutoff=cutoff,
        )
        try:
            bundle = loader(request, refresh=refresh)
            fact_references[member.instrument_id] = bundle.fingerprint
            market_caps[member.instrument_id] = (bundle.market_cap, bundle.market_cap_as_of)
            facts.append(adapt_yfinance_peer_facts(bundle, instrument_id=member.instrument_id))
        except (ProviderRequestError, ValueError) as error:
            errors[member.instrument_id] = str(error)
            fact_references[member.instrument_id] = f"{type(error).__name__}:{error}"

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
    if comparison_context is not None:
        fact_payload = json.dumps(
            sorted(fact_references.items()),
            separators=(",", ":"),
        )
        comparison_context = replace(
            comparison_context,
            fact_fingerprint=sha256(fact_payload.encode()).hexdigest(),
        )
    return IndustryScoreResult(cutoff, ids, stocks, cohort_fingerprint, comparison_context)
