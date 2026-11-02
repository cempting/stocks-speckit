import re
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime
from importlib import import_module
from numbers import Real
from typing import Literal, Protocol, cast
from urllib.parse import urlsplit

import pandas as pd

from market_data.domain.fundamentals import (
    FinancialQuarter,
    FundamentalBundle,
    FundamentalRequest,
    peer_facts_from_bundle,
)
from market_data.domain.peer_scores import PeerFacts
from market_leadership.infrastructure.provider_errors import (
    ProviderRequestError,
    is_retryable_provider_failure,
)

ROWS = {
    "Total Revenue": "revenue",
    "TotalRevenue": "revenue",
    "Gross Profit": "gross_profit",
    "GrossProfit": "gross_profit",
    "Operating Income": "operating_income",
    "OperatingIncome": "operating_income",
    "EBIT": "ebit",
    "Net Income": "net_income",
    "NetIncome": "net_income",
    "Diluted EPS": "diluted_eps",
    "DilutedEPS": "diluted_eps",
    "Operating Cash Flow": "ocf",
    "OperatingCashFlow": "ocf",
    "Capital Expenditure": "capex",
    "CapitalExpenditure": "capex",
    "Free Cash Flow": "fcf",
    "FreeCashFlow": "fcf",
    "Total Assets": "assets",
    "TotalAssets": "assets",
    "Current Liabilities": "current_liabilities",
    "CurrentLiabilities": "current_liabilities",
}


class TickerReader(Protocol):
    @property
    def info(self) -> Mapping[str, object]: ...
    @property
    def quarterly_financials(self) -> pd.DataFrame: ...
    @property
    def quarterly_cashflow(self) -> pd.DataFrame: ...
    @property
    def quarterly_balance_sheet(self) -> pd.DataFrame: ...


TickerFactory = Callable[[str], TickerReader]


def _profile_cik(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, Real):
        number = float(value)
        if not number.is_integer() or number < 0 or number >= 10**10:
            return None
        text = str(int(number))
    elif isinstance(value, str):
        text = value.strip()
    else:
        return None
    if not text.isascii() or not text.isdigit() or len(text) > 10:
        return None
    return text.zfill(10)


def _profile_domain(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    parsed = urlsplit(text if "://" in text else f"https://{text}")
    if parsed.scheme not in ("http", "https") or parsed.username or not parsed.hostname:
        return None
    return parsed.hostname.rstrip(".").casefold()


class _TickerAPI(Protocol):
    def Ticker(self, ticker: str) -> TickerReader: ...


yf = cast(_TickerAPI, import_module("yfinance"))


def ticker_factory(symbol: str) -> TickerReader:
    return yf.Ticker(symbol)


def adapt_yfinance_peer_facts(
    bundle: FundamentalBundle,
    *,
    instrument_id: str,
) -> PeerFacts:
    if bundle.provider_id != "yfinance":
        raise ValueError("Peer scoring requires yfinance source evidence")
    return peer_facts_from_bundle(bundle, instrument_id=instrument_id)


class FundamentalAcquisitionError(ProviderRequestError):
    def __init__(self, errors: tuple[str, ...], partial: FundamentalBundle) -> None:
        super().__init__("yfinance", "; ".join(errors) + "; retry Load or Refresh", retryable=False)
        self.partial = partial
        self.component_errors = errors


def _quarters(frame: pd.DataFrame, currency: str, today: date) -> tuple[FinancialQuarter, ...]:
    if frame.columns.has_duplicates or frame.index.has_duplicates:
        raise ValueError("Duplicate statement periods or rows")
    if frame.attrs.get("period_basis", "quarterly") != "quarterly":
        raise ValueError("Statement basis is not standalone quarterly evidence")
    if frame.attrs.get("currency", currency) != currency:
        raise ValueError("Statement currencies do not match")
    if frame.attrs.get("scale", 1) != 1:
        raise ValueError("Statement scale must be reported currency units")
    result: list[FinancialQuarter] = []
    for column in cast(list[object], frame.columns.tolist()):
        if isinstance(column, datetime):
            period = column.date()
        elif isinstance(column, date):
            period = column
        else:
            raise ValueError("Statement reporting periods must be dated")
        period = date.fromisoformat(period.isoformat())
        if period > today:
            raise ValueError("Statement contains an incomplete future period")
        values: dict[str, float | None] = {}
        for row, canonical in ROWS.items():
            if row not in frame.index:
                continue
            raw = cast(object, frame.at[row, column])
            if raw is not None and not isinstance(raw, Real):
                raise ValueError("Statement financial values must be numeric")
            value = float(raw) if isinstance(raw, Real) else None
            if canonical in values and values[canonical] != value:
                raise ValueError("Conflicting aliases for a financial row")
            values[canonical] = value
        result.append(FinancialQuarter(period, tuple(sorted(values.items()))))
    return tuple(sorted(result, key=lambda item: item.period))


def read_fundamentals(
    request: FundamentalRequest,
    factory: TickerFactory = ticker_factory,
    *,
    now: datetime | None = None,
) -> FundamentalBundle:
    fetched_at = now or datetime.now(UTC)
    if request.provider_id != "yfinance":
        raise ValueError("Live fundamentals require the single yfinance provider")
    if request.cutoff is not None and request.cutoff != fetched_at.date():
        raise ValueError("Unsupported historical live cutoff; use matching fixture evidence")
    ticker: TickerReader | None = None
    for attempt in range(request.retry_limit + 1):
        try:
            ticker = factory(request.symbol)
            break
        except Exception as error:
            if is_retryable_provider_failure(error) and attempt < request.retry_limit:
                continue
            partial = FundamentalBundle(
                request.symbol,
                "yfinance",
                fetched_at,
                "",
                (),
                (),
                (),
                ("Ticker initialization failed",),
                profile_state="failed",
                profile_failure="Ticker initialization failed",
            )
            raise FundamentalAcquisitionError(("Ticker initialization failed",), partial) from None
    assert ticker is not None
    components: dict[str, object] = {}
    errors: list[str] = []
    for name in ("info", "quarterly_financials", "quarterly_cashflow", "quarterly_balance_sheet"):
        for attempt in range(request.retry_limit + 1):
            try:
                components[name] = getattr(ticker, name)
                break
            except Exception as error:
                if is_retryable_provider_failure(error) and attempt < request.retry_limit:
                    continue
                errors.append(f"{name}: acquisition failed")
                break
    profile = components.get("info")
    currency = ""
    trading_currency: str | None = None
    market_cap: float | None = None
    issuer_discriminator: str | None = None
    profile_cik: str | None = None
    profile_domain: str | None = None
    profile_state: Literal["available", "missing", "inconclusive", "failed"] = "missing"
    profile_failure: str | None = None
    if isinstance(profile, Mapping) and profile:
        profile = cast(Mapping[str, object], profile)
        currency_value = profile.get("financialCurrency")
        currency = currency_value if isinstance(currency_value, str) else ""
        raw_trading_currency = profile.get("currency")
        if (
            isinstance(raw_trading_currency, str)
            and re.fullmatch(r"[A-Za-z]{3}", raw_trading_currency.strip())
        ):
            trading_currency = raw_trading_currency.strip().upper()
        raw_discriminator = profile.get("uuid") or profile.get("companyId")
        if isinstance(raw_discriminator, str) and raw_discriminator.strip():
            issuer_discriminator = raw_discriminator.strip()
        profile_cik = _profile_cik(profile.get("cik"))
        profile_domain = _profile_domain(profile.get("website"))
        raw_market_cap = profile.get("marketCap")
        if isinstance(raw_market_cap, Real):
            candidate = float(raw_market_cap)
            if candidate > 0 and pd.notna(candidate) and candidate != float("inf"):
                market_cap = candidate
        if profile.get("symbol") != request.symbol:
            errors.append("info: symbol identity mismatch")
            components.clear()
            profile_state = "inconclusive"
            profile_failure = "Profile symbol identity mismatch"
        if not currency:
            errors.append("info: financial currency unavailable")
        if profile_state != "inconclusive":
            if not currency:
                profile_state = "inconclusive"
                profile_failure = "Reporting currency unavailable"
            elif (
                issuer_discriminator is None
                and profile_cik is None
                and profile_domain is None
            ):
                profile_state = "inconclusive"
                profile_failure = "Issuer discriminator unavailable"
            else:
                profile_state = "available"
    else:
        if any(error.startswith("info: acquisition failed") for error in errors):
            profile_state = "failed"
            profile_failure = "Profile acquisition failed"
        else:
            profile_state = "missing"
            profile_failure = "Profile unavailable"
            errors.append("info: unverified_empty")
    tables: list[tuple[FinancialQuarter, ...]] = []
    for name in ("quarterly_financials", "quarterly_cashflow", "quarterly_balance_sheet"):
        frame = components.get(name)
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            errors.append(f"{name}: unverified_empty")
            tables.append(())
            continue
        try:
            tables.append(_quarters(frame, currency, fetched_at.date()) if currency else ())
        except (ValueError, TypeError, OverflowError):
            errors.append(f"{name}: invalid dates, basis, units or financial values")
            tables.append(())
    bundle = FundamentalBundle(
        request.symbol,
        "yfinance",
        fetched_at,
        currency,
        tables[0],
        tables[1],
        tables[2],
        tuple(errors),
        market_cap,
        fetched_at.date() if market_cap is not None else None,
        issuer_discriminator,
        profile_state,
        profile_failure,
        trading_currency,
        profile_cik,
        profile_domain,
    )
    if errors:
        raise FundamentalAcquisitionError(tuple(errors), bundle)
    return bundle
