import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class ClassificationLevel(StrEnum):
    SECTOR = "SECTOR"
    INDUSTRY_GROUP = "INDUSTRY_GROUP"
    INDUSTRY = "INDUSTRY"
    SUB_INDUSTRY = "SUB_INDUSTRY"


HierarchyLevel = ClassificationLevel


class InstrumentKind(StrEnum):
    STOCK = "STOCK"
    FUND = "FUND"
    INDEX = "INDEX"


class ProxyType(StrEnum):
    FUND = "FUND"
    INDEX = "INDEX"
    EQUAL_WEIGHT_BASKET = "EQUAL_WEIGHT_BASKET"
    NONE = "NONE"


class SlopeState(StrEnum):
    RISING = "RISING"
    FLAT = "FLAT"
    FALLING = "FALLING"
    UNDEFINED = "UNDEFINED"


class MarketRegime(StrEnum):
    BULLISH = "BULLISH"
    SIDEWAYS = "SIDEWAYS"
    BEARISH = "BEARISH"
    INSUFFICIENT = "INSUFFICIENT"


class AssetCategory(StrEnum):
    EQUITY = "EQUITY"


class BenchmarkScope(StrEnum):
    LOCAL = "LOCAL"
    GLOBAL = "GLOBAL"


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_currency(value: str) -> None:
    if re.fullmatch(r"[A-Z]{3}", value) is None:
        raise ValueError("currency must be an uppercase three-letter ISO 4217 code")


def _validate_interval(start: date, end: date | None) -> None:
    if end is not None and end < start:
        raise ValueError("effective interval end must not precede its start")


@dataclass(frozen=True, slots=True)
class Market:
    market_id: str
    name: str
    base_currency: str
    timezone: str
    calendar_id: str
    local_benchmark_id: str
    classification_scheme_id: str
    enabled_from: date
    enabled_to: date | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "market_id",
            "name",
            "timezone",
            "calendar_id",
            "local_benchmark_id",
            "classification_scheme_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        _require_currency(self.base_currency)
        _validate_interval(self.enabled_from, self.enabled_to)


@dataclass(frozen=True, slots=True)
class ClassificationNode:
    node_id: str
    scheme_id: str
    level: ClassificationLevel
    name: str
    parent_node_id: str | None
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        for field_name in ("node_id", "scheme_id", "name"):
            _require_text(getattr(self, field_name), field_name)
        if self.level is ClassificationLevel.SECTOR and self.parent_node_id is not None:
            raise ValueError("a sector classification cannot have a parent")
        if self.level is not ClassificationLevel.SECTOR and not self.parent_node_id:
            raise ValueError("a non-sector classification must have a parent")
        _validate_interval(self.effective_from, self.effective_to)


@dataclass(frozen=True, slots=True)
class Company:
    company_id: str
    name: str
    primary_market_id: str
    classification_path: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("company_id", "name", "primary_market_id"):
            _require_text(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class Instrument:
    instrument_id: str
    company_id: str | None
    asset_category: AssetCategory
    kind: InstrumentKind
    symbol: str
    exchange: str
    currency: str
    return_basis: str
    name: str
    active_from: date
    isin: str | None = None
    active_to: date | None = None

    def __post_init__(self) -> None:
        for field_name in ("instrument_id", "symbol", "exchange", "return_basis", "name"):
            _require_text(getattr(self, field_name), field_name)
        _require_currency(self.currency)
        if self.kind is InstrumentKind.STOCK and not self.company_id:
            raise ValueError("a stock instrument must reference a company")
        if self.kind is not InstrumentKind.STOCK and self.company_id is not None:
            raise ValueError("funds and indices must not impersonate companies")
        _validate_interval(self.active_from, self.active_to)


@dataclass(frozen=True, slots=True)
class Benchmark:
    benchmark_id: str
    instrument_id: str
    scope: BenchmarkScope
    market_id: str | None
    currency: str
    return_basis: str

    def __post_init__(self) -> None:
        for field_name in ("benchmark_id", "instrument_id", "return_basis"):
            _require_text(getattr(self, field_name), field_name)
        _require_currency(self.currency)
        if self.scope is BenchmarkScope.LOCAL and not self.market_id:
            raise ValueError("a local benchmark must identify its market")


@dataclass(frozen=True, slots=True)
class IndustryProxy:
    proxy_id: str
    market_id: str
    node_id: str
    proxy_type: ProxyType
    instrument_id: str | None
    member_ids: tuple[str, ...]
    selected_as_of: date
    effective_from: date
    effective_to: date | None = None
    purity_pct: float | None = None
    aum_usd: float | None = None
    adv20_usd: float | None = None
    qualification_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("proxy_id", "market_id", "node_id"):
            _require_text(getattr(self, field_name), field_name)
        _validate_interval(self.effective_from, self.effective_to)
        if self.proxy_type is ProxyType.NONE and self.instrument_id is not None:
            raise ValueError("a NONE proxy cannot identify an instrument")
        if self.proxy_type is ProxyType.EQUAL_WEIGHT_BASKET and len(self.member_ids) < 5:
            raise ValueError("an equal-weight basket requires at least five members")


@dataclass(frozen=True, slots=True)
class PriceObservation:
    instrument_id: str
    observed_on: date
    return_basis: str
    source_id: str
    available_on: date
    close: float | None
    volume: float | None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    adjusted_close: float | None = None

    def __post_init__(self) -> None:
        if self.available_on < self.observed_on:
            raise ValueError("price availability cannot precede its observation")


@dataclass(frozen=True, slots=True)
class FxObservation:
    base_currency: str
    quote_currency: str
    observed_on: date
    close: float
    source_id: str
    available_on: date

    def __post_init__(self) -> None:
        _require_currency(self.base_currency)
        _require_currency(self.quote_currency)
        if self.available_on < self.observed_on:
            raise ValueError("FX availability cannot precede its observation")


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    name: str
    dataset: str
    version: str
    retrieved_at: datetime
    checksum: str
    license_label: str | None = None


@dataclass(frozen=True, slots=True)
class MarketRegimeSnapshot:
    market_id: str
    benchmark_id: str
    as_of: date
    close: float | None
    sma150: float | None
    normalized_slope_pct: float | None
    slope_state: SlopeState
    regime: MarketRegime
    data_quality: str
    reason_codes: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
