"""Rights-gated ETF or single-stock representations for live industry discovery."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class IndustryProxyKind(StrEnum):
    ETF = "ETF"
    STOCK = "STOCK"


@dataclass(frozen=True, slots=True)
class IndustryProxyCandidate:
    market_id: str
    sector_node_id: str
    industry_node_id: str
    symbol: str
    name: str
    kind: IndustryProxyKind
    source_id: str
    composition_basis: str
    effective_from: date
    effective_to: date | None
    available_on: date
    rights_verified: bool
    qualified: bool
    member_verified: bool
    market_cap: float | None
    market_cap_as_of: date | None

    def __post_init__(self) -> None:
        for field in (
            "market_id",
            "sector_node_id",
            "industry_node_id",
            "symbol",
            "name",
            "source_id",
            "composition_basis",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"{field.replace('_', ' ')} is required")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective end precedes start")
        if self.kind is IndustryProxyKind.STOCK and self.market_cap is not None:
            if self.market_cap <= 0:
                raise ValueError("stock market cap must be positive")
        if self.kind is IndustryProxyKind.ETF and (
            self.member_verified or self.market_cap is not None or self.market_cap_as_of is not None
        ):
            raise ValueError("ETF candidates cannot carry constituent market-cap evidence")


def select_industry_proxy(
    candidates: tuple[IndustryProxyCandidate, ...],
    *,
    market_id: str,
    sector_node_id: str,
    industry_node_id: str,
    as_of: date,
) -> tuple[IndustryProxyCandidate | None, str | None]:
    active = tuple(
        candidate
        for candidate in candidates
        if candidate.market_id == market_id
        and candidate.sector_node_id == sector_node_id
        and candidate.industry_node_id == industry_node_id
        and candidate.effective_from <= as_of
        and (candidate.effective_to is None or as_of <= candidate.effective_to)
        and candidate.available_on <= as_of
        and candidate.rights_verified
        and candidate.qualified
    )
    etfs = tuple(candidate for candidate in active if candidate.kind is IndustryProxyKind.ETF)
    if len(etfs) > 1:
        raise ValueError(f"multiple qualified ETF representations for {industry_node_id}")
    if etfs:
        return etfs[0], None

    stocks = tuple(
        candidate
        for candidate in active
        if candidate.kind is IndustryProxyKind.STOCK
        and candidate.member_verified
        and candidate.market_cap is not None
        and candidate.market_cap_as_of == as_of
    )
    if not stocks:
        return None, "NO_QUALIFIED_REPRESENTATION"

    def selection_key(candidate: IndustryProxyCandidate) -> tuple[float, str]:
        assert candidate.market_cap is not None
        return -candidate.market_cap, candidate.symbol

    selected = min(stocks, key=selection_key)
    return selected, None
