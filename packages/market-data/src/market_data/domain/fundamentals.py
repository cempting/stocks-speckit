from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from math import isfinite
from typing import Literal

from market_data.domain.peer_scores import PeerFacts

METRIC_GROUPS = (
    (
        "Quality",
        (
            ("gross_margin", "Gross Margin"),
            ("operating_margin", "Operating Margin"),
            ("roce", "ROCE"),
        ),
    ),
    (
        "Growth",
        (
            ("sales_yoy", "Sales YoY"),
            ("eps_yoy", "EPS YoY"),
            ("eps_consistency", "EPS Consistency"),
        ),
    ),
    ("Cash Flow", (("cash_conversion", "Cash Conversion"), ("fcf_margin", "FCF Margin"))),
)


@dataclass(frozen=True)
class FundamentalRequest:
    symbol: str
    provider_id: str = "yfinance"
    cutoff: date | None = None
    history_window: int = 8
    frequency: str = "quarterly"
    schema_version: int = 1
    retry_limit: int = 2

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        if not self.symbol or self.provider_id not in ("yfinance", "fixture"):
            raise ValueError("A symbol and a supported single provider are required")
        if not 4 <= self.history_window <= 8 or self.frequency != "quarterly":
            raise ValueError("Fundamentals require a four-to-eight-quarter display window")
        if self.retry_limit < 0:
            raise ValueError("retry_limit must be non-negative")


@dataclass(frozen=True)
class FinancialQuarter:
    period: date
    values: tuple[tuple[str, float | None], ...]

    def get(self, key: str) -> float | None:
        value = dict(self.values).get(key)
        return value if value is not None and isfinite(value) else None


@dataclass(frozen=True)
class FundamentalBundle:
    symbol: str
    provider_id: str
    fetched_at: datetime
    currency: str
    income: tuple[FinancialQuarter, ...]
    cash: tuple[FinancialQuarter, ...]
    balance: tuple[FinancialQuarter, ...]
    warnings: tuple[str, ...] = ()
    market_cap: float | None = None
    market_cap_as_of: date | None = None
    issuer_discriminator: str | None = None
    profile_state: Literal["available", "missing", "inconclusive", "failed"] = "missing"
    profile_failure: str | None = None
    trading_currency: str | None = None
    profile_cik: str | None = None
    profile_domain: str | None = None

    @property
    def fingerprint(self) -> str:
        return sha256(repr(self).encode()).hexdigest()


@dataclass(frozen=True)
class QuarterlyObservation:
    period: date
    value: float


@dataclass(frozen=True)
class FundamentalMetric:
    key: str
    label: str
    group: str
    value: float | None
    formatted: str
    commentary: str
    history: tuple[QuarterlyObservation, ...]
    detail: str


@dataclass(frozen=True)
class HistoryMetric:
    key: str
    label: str
    period: date
    value: float | None
    state: Literal["available", "insufficient"]
    detail: str


@dataclass(frozen=True)
class FundamentalScorecard:
    symbol: str
    provider_id: str
    fetched_at: datetime
    period: date | None
    fingerprint: str
    metrics: tuple[FundamentalMetric, ...]
    warnings: tuple[str, ...] = ()


def peer_facts_from_bundle(
    bundle: FundamentalBundle,
    *,
    instrument_id: str,
) -> PeerFacts:
    if not instrument_id.strip():
        raise ValueError("Peer facts require a stable instrument ID")
    reason = (
        "The fundamental source does not expose verified fact publication vintages or a "
        "matching dated market capitalization."
    )
    if bundle.warnings:
        reason += " The source bundle also contains incomplete evidence."
    return PeerFacts(
        instrument_id=instrument_id,
        facts_available_on=None,
        current_ttm_start=None,
        current_ttm_end=None,
        prior_ttm_start=None,
        prior_ttm_end=None,
        net_income=None,
        revenue=None,
        prior_revenue=None,
        opening_equity=None,
        closing_equity=None,
        diluted_eps=None,
        prior_diluted_eps=None,
        operating_cash_flow=None,
        prior_operating_cash_flow=None,
        positive_capex_outflow=None,
        market_cap=None,
        market_cap_date=None,
        currency=bundle.currency or None,
        market_cap_currency=None,
        unavailable_reason=reason,
    )


def _consecutive(periods: tuple[date, ...]) -> bool:
    # Fiscal quarters may use a 52/53-week calendar rather than calendar month ends.
    return all(
        70 <= (later - earlier).days <= 110
        for earlier, later in zip(periods, periods[1:], strict=False)
    )


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    result = numerator / denominator
    return result if isfinite(result) else None


def _value(bundle: FundamentalBundle, key: str, period: date) -> float | None:
    incomes = {quarter.period: quarter for quarter in bundle.income}
    cashflows = {quarter.period: quarter for quarter in bundle.cash}
    balances = {quarter.period: quarter for quarter in bundle.balance}
    income = incomes.get(period, FinancialQuarter(period, ()))
    cash = cashflows.get(period, FinancialQuarter(period, ()))
    balance = balances.get(period, FinancialQuarter(period, ()))
    revenue = income.get("revenue")
    if key == "gross_margin":
        return _ratio(income.get("gross_profit"), revenue)
    if key == "operating_margin":
        return _ratio(income.get("operating_income"), revenue)
    if key == "net_margin":
        return _ratio(income.get("net_income"), revenue)
    if key == "current_ratio":
        return _ratio(balance.get("current_assets"), balance.get("current_liabilities"))
    if key == "debt_to_equity":
        return _ratio(balance.get("total_debt"), balance.get("shareholders_equity"))
    if key == "cash_conversion":
        return _ratio(cash.get("ocf"), income.get("net_income"))
    if key == "fcf_margin":
        fcf = cash.get("fcf")
        if fcf is None and cash.get("ocf") is not None and cash.get("capex") is not None:
            ocf, capex = cash.get("ocf"), cash.get("capex")
            assert ocf is not None and capex is not None
            fcf = ocf - abs(capex)
        return _ratio(fcf, revenue)
    periods = tuple(sorted(p for p in incomes if p <= period))
    if not periods or periods[-1] != period:
        return None
    window_length = 8 if key == "eps_consistency" else 4 if key == "roce" else 5
    window = periods[-window_length:]
    if len(window) != window_length or not _consecutive(window):
        return None
    if key == "eps_consistency":
        eps = tuple(incomes[p].get("diluted_eps") for p in window)
        if any(value is None for value in eps):
            return None
        return float(sum(value > 0 for value in eps if value is not None))
    if key == "roce":
        ebit = tuple(incomes[p].get("ebit") for p in window)
        assets, liabilities = balance.get("assets"), balance.get("current_liabilities")
        if any(value is None for value in ebit) or assets is None or liabilities is None:
            return None
        total_ebit = sum(value for value in ebit if value is not None)
        return _ratio(total_ebit, assets - liabilities)
    row = "revenue" if key == "sales_yoy" else "diluted_eps"
    result = _ratio(income.get(row), incomes[window[0]].get(row))
    return result - 1 if result is not None else None


def build_history_metrics(bundle: FundamentalBundle) -> tuple[HistoryMetric, ...]:
    definitions = (
        ("sales_yoy", "Revenue YoY", "Same fiscal quarter one year earlier"),
        ("eps_yoy", "Diluted EPS YoY", "Same fiscal quarter one year earlier"),
        ("gross_margin", "Gross margin", "Gross profit / revenue"),
        ("operating_margin", "Operating margin", "Operating income / revenue"),
        ("net_margin", "Net margin", "Net income / revenue"),
        ("fcf_margin", "FCF margin", "Free cash flow / revenue"),
        ("roce", "ROCE", "TTM EBIT / quarter-end capital employed"),
        ("current_ratio", "Current ratio", "Current assets / current liabilities"),
        ("debt_to_equity", "Debt-to-equity", "Total debt / shareholders' equity"),
    )
    periods = tuple(
        sorted(
            {
                quarter.period
                for table in (bundle.income, bundle.cash, bundle.balance)
                for quarter in table
            }
        )
    )
    metrics: list[HistoryMetric] = []
    for period in periods:
        for key, label, formula in definitions:
            value = _value(bundle, key, period)
            detail = formula
            if value is None:
                detail += "; required comparable evidence or a positive denominator unavailable"
            metrics.append(
                HistoryMetric(
                    key=key,
                    label=label,
                    period=period,
                    value=value,
                    state="available" if value is not None else "insufficient",
                    detail=detail,
                )
            )
    return tuple(metrics)


def build_scorecard(bundle: FundamentalBundle, history_window: int = 8) -> FundamentalScorecard:
    if not 4 <= history_window <= 8:
        raise ValueError("History window must be between four and eight")
    periods = tuple(
        sorted(
            {
                quarter.period
                for table in (bundle.income, bundle.cash, bundle.balance)
                for quarter in table
            }
        )
    )
    latest = periods[-1] if periods else None
    metrics: list[FundamentalMetric] = []
    for group, definitions in METRIC_GROUPS:
        for key, label in definitions:
            value = _value(bundle, key, latest) if latest is not None else None
            formatted = (
                "N/A"
                if value is None
                else f"{int(value)}/8 quarters"
                if key == "eps_consistency"
                else f"{value * 100:.1f}%"
            )
            commentary = (
                "Data not available"
                if value is None
                else "Losing money on operations"
                if key == "operating_margin" and value < 0
                else f"{label}: {formatted}"
            )
            history: list[QuarterlyObservation] = []
            for period in reversed(periods):
                observation = _value(bundle, key, period)
                if observation is None:
                    break
                if history and not _consecutive((period, history[-1].period)):
                    break
                history.append(QuarterlyObservation(period, observation))
                if len(history) == history_window:
                    break
            basis = (
                "TTM EBIT / quarter-end capital employed"
                if key == "roce"
                else "Eight consecutive fiscal quarters; strictly positive diluted EPS"
                if key == "eps_consistency"
                else "Same fiscal quarter prior year; positive baseline"
                if key.endswith("yoy")
                else "Latest completed quarter; aligned statement periods"
            )
            if key == "fcf_margin" and latest is not None:
                cash = next((q for q in bundle.cash if q.period == latest), None)
                if cash is not None and cash.get("fcf") is None:
                    basis += "; FCF derived from operating cash flow minus absolute capex"
            if value is None:
                basis += "; required comparable evidence or positive denominator unavailable"
            metrics.append(
                FundamentalMetric(
                    key, label, group, value, formatted, commentary, tuple(reversed(history)), basis
                )
            )
    return FundamentalScorecard(
        bundle.symbol,
        bundle.provider_id,
        bundle.fetched_at,
        latest,
        bundle.fingerprint,
        tuple(metrics),
        bundle.warnings,
    )
