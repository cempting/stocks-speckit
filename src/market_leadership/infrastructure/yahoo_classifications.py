"""Local-only Yahoo sector and industry classification snapshots."""

import argparse
import json
import os
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from importlib import import_module
from pathlib import Path
from typing import Literal, cast

from market_data.catalog import CatalogReader, CatalogSnapshot
from market_data.domain.catalog import CatalogError
from market_leadership.config import load_settings

ClassificationStatus = Literal["classified", "partial", "unclassified", "no_metadata"]
_STATUSES = frozenset({"classified", "partial", "unclassified", "no_metadata"})
_UNCLASSIFIED_LABELS = frozenset({"", "undefined", "n/a", "na", "null"})
_MAX_CACHE_BYTES = 32 * 1024 * 1024
_MAX_BATCH_SIZE = 100
_DEFAULT_BATCH_SIZE = 25
_REQUEST_DELAY_SECONDS = 1.0
_CACHE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class YahooClassification:
    provider_symbol: str
    status: ClassificationStatus
    sector: str | None
    industry: str | None
    observed_at: datetime

    def __post_init__(self) -> None:
        if (
            not self.provider_symbol
            or self.provider_symbol != self.provider_symbol.strip().upper()
            or len(self.provider_symbol) > 64
            or any(character.isspace() or ord(character) < 32 for character in self.provider_symbol)
        ):
            raise ValueError("provider_symbol must be a normalized Yahoo symbol")
        if self.status not in _STATUSES:
            raise ValueError("classification status is invalid")
        for field in ("sector", "industry"):
            value = getattr(self, field)
            if value is not None and (not value or value != value.strip()):
                raise ValueError(f"{field} must be a non-empty trimmed label or None")
        has_sector = self.sector is not None
        has_industry = self.industry is not None
        expected_status = (
            "classified"
            if has_sector and has_industry
            else "partial"
            if has_sector or has_industry
            else self.status
        )
        if self.status in ("classified", "partial") and self.status != expected_status:
            raise ValueError("classification status does not match its labels")
        if self.status in ("unclassified", "no_metadata") and (has_sector or has_industry):
            raise ValueError("unknown classifications cannot contain sector or industry labels")
        if (
            self.observed_at.tzinfo is None
            or self.observed_at.utcoffset() != UTC.utcoffset(None)
        ):
            raise ValueError("observed_at must be UTC-aware")


@dataclass(frozen=True, slots=True)
class RefreshFailure:
    provider_symbol: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class RefreshReport:
    attempted: int
    stored: int
    cache_size: int
    status_counts: tuple[tuple[str, int], ...]
    failures: tuple[RefreshFailure, ...]


def catalog_provider_symbols(
    snapshot: CatalogSnapshot, *, as_of: date | None = None
) -> tuple[str, ...]:
    effective_date = as_of or date.today()
    return tuple(
        sorted(
            {
                symbol
                for stock in snapshot.stocks
                if stock.scope.region_id == "US"
                if (symbol := stock.provider_symbol_on(effective_date)) is not None
            }
        )
    )


def classification_from_info(
    provider_symbol: str,
    info: object,
    *,
    observed_at: datetime | None = None,
) -> YahooClassification:
    if not isinstance(info, Mapping):
        raise TypeError("Yahoo get_info() must return a mapping")
    values: dict[str, object] = {}
    for key, value in cast(Mapping[object, object], info).items():
        if not isinstance(key, str):
            raise TypeError("Yahoo get_info() mapping keys must be text")
        values[key] = value
    sector = _label(values, "sector")
    industry = _label(values, "industry")
    if sector and industry:
        status: ClassificationStatus = "classified"
    elif sector or industry:
        status = "partial"
    elif values:
        status = "unclassified"
    else:
        status = "no_metadata"
    return YahooClassification(
        provider_symbol=provider_symbol.strip().upper(),
        status=status,
        sector=sector,
        industry=industry,
        observed_at=observed_at or datetime.now(UTC),
    )


def read_classification_cache(path: str | Path) -> dict[str, YahooClassification]:
    source = Path(path)
    try:
        raw = source.read_bytes()
    except FileNotFoundError:
        return {}
    if len(raw) > _MAX_CACHE_BYTES:
        raise ValueError("Yahoo classification cache exceeds the supported size limit")
    try:
        document = cast(
            object, json.loads(raw, object_pairs_hook=_unique_object)
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"Yahoo classification cache is invalid: {error}") from None
    if not isinstance(document, dict):
        raise ValueError("Yahoo classification cache has an invalid document shape")
    parsed_document = cast(dict[str, object], document)
    if set(parsed_document) != {"schema_version", "records"}:
        raise ValueError("Yahoo classification cache has an invalid document shape")
    if parsed_document["schema_version"] != _CACHE_SCHEMA_VERSION:
        raise ValueError("Yahoo classification cache uses an unsupported schema version")
    raw_records = parsed_document["records"]
    if not isinstance(raw_records, list):
        raise ValueError("Yahoo classification cache records must be a list")
    records: dict[str, YahooClassification] = {}
    for raw_record in cast(list[object], raw_records):
        record = _parse_record(raw_record)
        if record.provider_symbol in records:
            raise ValueError("Yahoo classification cache contains duplicate symbols")
        records[record.provider_symbol] = record
    return records


def write_classification_cache(
    path: str | Path, records: Mapping[str, YahooClassification]
) -> None:
    destination = Path(path)
    if any(symbol != record.provider_symbol for symbol, record in records.items()):
        raise ValueError("Yahoo classification cache keys must match their provider symbols")
    document = {
        "schema_version": _CACHE_SCHEMA_VERSION,
        "records": [
            _record_document(records[symbol])
            for symbol in sorted(records)
        ],
    }
    encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > _MAX_CACHE_BYTES:
        raise ValueError("Yahoo classification cache exceeds the supported size limit")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def refresh_classification_cache(
    snapshot: CatalogSnapshot,
    cache_path: str | Path,
    *,
    fetch_info: Callable[[str], Mapping[str, object]],
    symbols: tuple[str, ...] | None = None,
    limit: int = _DEFAULT_BATCH_SIZE,
    force: bool = False,
    now: datetime | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> RefreshReport:
    if not 1 <= limit <= _MAX_BATCH_SIZE:
        raise ValueError(f"limit must be between 1 and {_MAX_BATCH_SIZE}")
    catalog_symbols = catalog_provider_symbols(snapshot)
    catalog_symbol_set = set(catalog_symbols)
    if symbols is None:
        candidates = catalog_symbols
    else:
        normalized = tuple(symbol.strip().upper() for symbol in symbols)
        if not normalized or any(not symbol for symbol in normalized):
            raise ValueError("explicit symbols must be non-empty")
        if len(normalized) > _MAX_BATCH_SIZE:
            raise ValueError(f"at most {_MAX_BATCH_SIZE} explicit symbols may be requested")
        if len(set(normalized)) != len(normalized):
            raise ValueError("explicit symbols must be unique")
        unknown = set(normalized).difference(catalog_symbol_set)
        if unknown:
            raise ValueError(
                "symbols are not active primary US catalog listings: "
                + ", ".join(sorted(unknown))
            )
        candidates = normalized

    cache = read_classification_cache(cache_path)
    pending = tuple(symbol for symbol in candidates if force or symbol not in cache)
    selected = pending if symbols is not None else pending[:limit]
    failures: list[RefreshFailure] = []
    stored_count = 0
    for index, symbol in enumerate(selected):
        try:
            info = fetch_info(symbol)
            record = classification_from_info(symbol, info, observed_at=now)
        except Exception as error:
            failures.append(RefreshFailure(symbol, type(error).__name__, str(error)))
        else:
            cache[symbol] = record
            stored_count += 1
        if index + 1 < len(selected):
            sleeper(_REQUEST_DELAY_SECONDS)

    if stored_count:
        write_classification_cache(cache_path, cache)
    counts = {status: 0 for status in sorted(_STATUSES)}
    for record in cache.values():
        counts[record.status] += 1
    return RefreshReport(
        attempted=len(selected),
        stored=stored_count,
        cache_size=len(cache),
        status_counts=tuple(counts.items()),
        failures=tuple(failures),
    )


def _label(info: Mapping[str, object], key: str) -> str | None:
    value = info.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Yahoo {key} value must be text or null")
    normalized = value.strip()
    return None if normalized.casefold() in _UNCLASSIFIED_LABELS else normalized


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_record(value: object) -> YahooClassification:
    if not isinstance(value, dict):
        raise ValueError("Yahoo classification cache record has an invalid shape")
    record = cast(dict[str, object], value)
    if set(record) != {
        "provider_symbol",
        "status",
        "sector",
        "industry",
        "observed_at",
    }:
        raise ValueError("Yahoo classification cache record has an invalid shape")
    symbol = record["provider_symbol"]
    status = record["status"]
    sector = record["sector"]
    industry = record["industry"]
    observed_at = record["observed_at"]
    if (
        not isinstance(symbol, str)
        or not isinstance(status, str)
        or status not in _STATUSES
        or (sector is not None and not isinstance(sector, str))
        or (industry is not None and not isinstance(industry, str))
        or not isinstance(observed_at, str)
    ):
        raise ValueError("Yahoo classification cache record contains invalid values")
    try:
        parsed_date = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        return YahooClassification(
            symbol,
            cast(ClassificationStatus, status),
            sector,
            industry,
            parsed_date,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"Yahoo classification cache record is invalid: {error}") from None


def _record_document(record: YahooClassification) -> dict[str, object]:
    return {
        "provider_symbol": record.provider_symbol,
        "status": record.status,
        "sector": record.sector,
        "industry": record.industry,
        "observed_at": record.observed_at.isoformat(),
    }


def _fetch_yahoo_info(symbol: str) -> Mapping[str, object]:
    yfinance = import_module("yfinance")
    ticker_factory = cast(Callable[[str], object], yfinance.Ticker)
    ticker = ticker_factory(symbol)
    get_info = getattr(ticker, "get_info", None)
    if not callable(get_info):
        raise TypeError("yfinance Ticker does not expose get_info()")
    info = get_info()
    if not isinstance(info, Mapping):
        raise TypeError("Yahoo get_info() must return a mapping")
    result: dict[str, object] = {}
    for key, value in cast(Mapping[object, object], info).items():
        if not isinstance(key, str):
            raise TypeError("Yahoo get_info() mapping keys must be text")
        result[key] = value
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market-yahoo-classifications",
        description="Refresh a bounded local-only Yahoo sector/industry metadata cache.",
    )
    parser.add_argument("--catalog-manifest", type=Path)
    parser.add_argument("--cache", type=Path)
    batch = parser.add_mutually_exclusive_group()
    batch.add_argument("--limit", type=_batch_size, default=_DEFAULT_BATCH_SIZE)
    batch.add_argument("--symbols", nargs="+")
    parser.add_argument("--force", action="store_true")
    return parser


def _batch_size(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("limit must be an integer") from None
    if not 1 <= parsed <= _MAX_BATCH_SIZE:
        raise argparse.ArgumentTypeError(f"limit must be between 1 and {_MAX_BATCH_SIZE}")
    return parsed


def _default_catalog_manifest() -> Path:
    configured = os.getenv("MARKET_CATALOG_MANIFEST_PATH", "").strip()
    if configured:
        return Path(configured)
    return (
        Path(__file__).resolve().parents[3]
        / "data"
        / "catalog-us-etf-clusters"
        / "CURRENT.json"
    )


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        settings = load_settings()
        catalog_path = arguments.catalog_manifest or _default_catalog_manifest()
        snapshot = CatalogReader().read(catalog_path)
        report = refresh_classification_cache(
            snapshot,
            arguments.cache or settings.yahoo_classification_cache_path,
            fetch_info=_fetch_yahoo_info,
            symbols=tuple(arguments.symbols) if arguments.symbols else None,
            limit=arguments.limit,
            force=arguments.force,
        )
    except (CatalogError, OSError, ValueError) as error:
        print(f"Yahoo classification refresh failed: {error}", file=sys.stderr)
        return 2

    for failure in report.failures:
        print(
            f"Yahoo lookup failed for {failure.provider_symbol}: "
            f"{failure.error_type}: {failure.message}",
            file=sys.stderr,
        )
    print(
        json.dumps(
            {
                "report_version": "yahoo-classification-refresh-1",
                "attempted": report.attempted,
                "stored": report.stored,
                "cache_size": report.cache_size,
                "status_counts": dict(report.status_counts),
                "failures": len(report.failures),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 2 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
