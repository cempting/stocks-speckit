from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from math import isfinite

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
class FundamentalScorecard:
    symbol: str
    provider_id: str
    fetched_at: datetime
    period: date | None
    fingerprint: str
    metrics: tuple[FundamentalMetric, ...]
    warnings: tuple[str, ...] = ()


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
