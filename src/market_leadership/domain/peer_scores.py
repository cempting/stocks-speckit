"""Contract-based industry peer percentiles for verified, normalized facts."""

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import TypeGuard

MIN_VALID_PEERS = 5


@dataclass(frozen=True, slots=True)
class PeerFacts:
    instrument_id: str
    facts_available_on: date | None
    current_ttm_start: date | None
    current_ttm_end: date | None
    prior_ttm_start: date | None
    prior_ttm_end: date | None
    net_income: float | None
    revenue: float | None
    prior_revenue: float | None
    opening_equity: float | None
    closing_equity: float | None
    diluted_eps: float | None
    prior_diluted_eps: float | None
    operating_cash_flow: float | None
    prior_operating_cash_flow: float | None
    positive_capex_outflow: float | None
    market_cap: float | None
    market_cap_date: date | None
    currency: str | None
    market_cap_currency: str | None
    unavailable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class MetricPeerScore:
    key: str
    raw_value: float | None
    percentile: float | None
    valid_peer_count: int
    state: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class BlockPeerScore:
    block: str
    value: float | None
    state: str
    metrics: tuple[MetricPeerScore, ...]
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PeerScorecard:
    instrument_id: str
    quality: BlockPeerScore
    growth: BlockPeerScore
    cash_flow: BlockPeerScore


_BLOCKS = (
    ("Quality", "quality", ("roe", "net_margin")),
    ("Growth", "growth", ("revenue_yoy", "diluted_eps_yoy")),
    ("Cash Flow", "cash_flow", ("fcf_yield", "ocf_yoy")),
)


def _finite(value: float | None) -> TypeGuard[float]:
    return value is not None and isfinite(value)


def _window_is_comparable(facts: PeerFacts, cutoff: date) -> bool:
    current_start, current_end = facts.current_ttm_start, facts.current_ttm_end
    prior_start, prior_end = facts.prior_ttm_start, facts.prior_ttm_end
    if None in (current_start, current_end, prior_start, prior_end):
        return False
    assert current_start is not None and current_end is not None
    assert prior_start is not None and prior_end is not None
    if (
        prior_start > prior_end
        or current_start > current_end
        or prior_end >= current_start
        or current_end > cutoff
    ):
        return False
    prior_length = (prior_end - prior_start).days
    current_length = (current_end - current_start).days
    return 330 <= prior_length <= 400 and prior_length == current_length


def _raw_metrics(
    facts: PeerFacts | None, cutoff: date
) -> dict[str, tuple[float | None, str | None]]:
    keys = ("roe", "net_margin", "revenue_yoy", "diluted_eps_yoy", "fcf_yield", "ocf_yoy")
    if facts is None:
        return {key: (None, "Financial facts were not loaded.") for key in keys}
    if facts.facts_available_on is None:
        reason = facts.unavailable_reason or "Fact publication availability is unknown."
        return {key: (None, reason) for key in keys}
    if facts.facts_available_on > cutoff:
        return {key: (None, "Fact publication availability is after the cutoff.") for key in keys}
    if not _window_is_comparable(facts, cutoff):
        return {
            key: (None, "Comparable, non-overlapping TTM windows are unavailable.") for key in keys
        }

    results: dict[str, tuple[float | None, str | None]] = {}

    def ratio(
        key: str, numerator: float | None, denominator: float | None, *, multiplier: float = 100
    ) -> None:
        if not _finite(numerator) or not _finite(denominator) or denominator <= 0:
            results[key] = (None, "Required fact or positive denominator is unavailable.")
            return
        value = multiplier * numerator / denominator
        results[key] = (
            (value, None) if isfinite(value) else (None, "Calculated fact is non-finite.")
        )

    equity_mean = None
    if (
        _finite(facts.opening_equity)
        and _finite(facts.closing_equity)
        and facts.opening_equity > 0
        and facts.closing_equity > 0
    ):
        equity_mean = (facts.opening_equity + facts.closing_equity) / 2
    ratio(
        "roe",
        facts.net_income,
        equity_mean,
    )
    ratio("net_margin", facts.net_income, facts.revenue)
    if _finite(facts.revenue) and _finite(facts.prior_revenue) and facts.prior_revenue > 0:
        value = 100 * (facts.revenue / facts.prior_revenue - 1)
        results["revenue_yoy"] = (
            (value, None) if isfinite(value) else (None, "Calculated fact is non-finite.")
        )
    else:
        results["revenue_yoy"] = (None, "Required fact or positive prior revenue is unavailable.")
    if (
        _finite(facts.diluted_eps)
        and _finite(facts.prior_diluted_eps)
        and facts.prior_diluted_eps > 0
    ):
        value = 100 * (facts.diluted_eps / facts.prior_diluted_eps - 1)
        results["diluted_eps_yoy"] = (
            (value, None) if isfinite(value) else (None, "Calculated fact is non-finite.")
        )
    else:
        results["diluted_eps_yoy"] = (
            None,
            "Required fact or positive prior diluted EPS is unavailable.",
        )

    cap_is_valid = False
    if _finite(facts.market_cap):
        cap_is_valid = (
            facts.market_cap > 0
            and facts.market_cap_date == facts.current_ttm_end
            and facts.currency is not None
            and facts.market_cap_currency == facts.currency
        )
    if (
        cap_is_valid
        and _finite(facts.operating_cash_flow)
        and _finite(facts.positive_capex_outflow)
        and facts.positive_capex_outflow >= 0
    ):
        assert (
            facts.operating_cash_flow is not None
            and facts.positive_capex_outflow is not None
            and facts.market_cap is not None
        )
        fcf_yield = (
            100 * (facts.operating_cash_flow - facts.positive_capex_outflow) / facts.market_cap
        )
        results["fcf_yield"] = (
            (fcf_yield, None) if isfinite(fcf_yield) else (None, "Calculated fact is non-finite.")
        )
    else:
        results["fcf_yield"] = (
            None,
            "Dated, currency-compatible market cap and cash-flow facts are required.",
        )
    if (
        _finite(facts.operating_cash_flow)
        and _finite(facts.prior_operating_cash_flow)
        and facts.prior_operating_cash_flow > 0
    ):
        value = 100 * (facts.operating_cash_flow / facts.prior_operating_cash_flow - 1)
        results["ocf_yoy"] = (
            (value, None) if isfinite(value) else (None, "Calculated fact is non-finite.")
        )
    else:
        results["ocf_yoy"] = (
            None,
            "Required fact or positive prior operating cash flow is unavailable.",
        )
    return results


def _percentiles(
    values: dict[str, tuple[float | None, str | None]],
) -> dict[str, tuple[float | None, int, str | None]]:
    valid = [
        (instrument_id, value) for instrument_id, (value, _) in values.items() if _finite(value)
    ]
    count = len(valid)
    if count < MIN_VALID_PEERS:
        return {
            instrument_id: (
                None,
                count,
                reason or f"Fewer than {MIN_VALID_PEERS} valid peers for this metric.",
            )
            for instrument_id, (_, reason) in values.items()
        }
    result: dict[str, tuple[float | None, int, str | None]] = {}
    for instrument_id, (value, reason) in values.items():
        if not _finite(value):
            result[instrument_id] = (None, count, reason)
            continue
        lower = sum(peer_value < value for _, peer_value in valid)
        equal = sum(peer_value == value for _, peer_value in valid)
        result[instrument_id] = (
            100 * (lower + 0.5 * (equal - 1)) / (count - 1),
            count,
            None,
        )
    return result


def calculate_peer_scores(
    facts: tuple[PeerFacts, ...],
    *,
    eligible_instrument_ids: tuple[str, ...],
    cutoff: date,
) -> tuple[PeerScorecard, ...]:
    if len(set(eligible_instrument_ids)) != len(eligible_instrument_ids):
        raise ValueError("Eligible industry membership must not contain duplicate instruments")
    facts_by_id = {item.instrument_id: item for item in facts}
    if len(facts_by_id) != len(facts):
        raise ValueError("Peer facts must not contain duplicate instruments")

    raw_by_id = {
        instrument_id: _raw_metrics(facts_by_id.get(instrument_id), cutoff)
        for instrument_id in eligible_instrument_ids
    }
    percentiles = {
        key: _percentiles(
            {instrument_id: metrics[key] for instrument_id, metrics in raw_by_id.items()}
        )
        for _, _, metric_keys in _BLOCKS
        for key in metric_keys
    }
    scorecards: list[PeerScorecard] = []
    for instrument_id in eligible_instrument_ids:
        blocks: dict[str, BlockPeerScore] = {}
        for label, attribute, metric_keys in _BLOCKS:
            metric_scores = tuple(
                MetricPeerScore(
                    key,
                    raw_by_id[instrument_id][key][0],
                    percentiles[key][instrument_id][0],
                    percentiles[key][instrument_id][1],
                    "available"
                    if percentiles[key][instrument_id][0] is not None
                    else "insufficient",
                    percentiles[key][instrument_id][2],
                )
                for key in metric_keys
            )
            values = tuple(score.percentile for score in metric_scores)
            available = all(_finite(value) for value in values)
            reasons = tuple(score.reason for score in metric_scores if score.reason)
            blocks[attribute] = BlockPeerScore(
                label,
                sum(value for value in values if value is not None) / len(values)
                if available
                else None,
                "available" if available else "insufficient",
                metric_scores,
                "; ".join(dict.fromkeys(reasons)) if reasons else None,
            )
        scorecards.append(
            PeerScorecard(
                instrument_id,
                blocks["quality"],
                blocks["growth"],
                blocks["cash_flow"],
            )
        )
    return tuple(scorecards)
