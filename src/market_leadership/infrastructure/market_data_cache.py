import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from market_leadership.application.ports import MarketDataProvider

CACHE_SCHEMA_VERSION = 4
_DATA_COLUMNS = ["symbol", "date", "close", "volume"]


class _CacheMiss(Exception):
    pass


def daily_history_fingerprint(
    *,
    provider_id: str,
    symbols: tuple[str, ...],
    start: date,
    end: date,
) -> str:
    request = _normalized_request(provider_id, symbols, start, end)
    encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class CachedMarketDataProvider:
    def __init__(
        self,
        upstream: MarketDataProvider,
        cache_root: str | Path,
        *,
        alternatives: tuple[str, ...] = (),
        selection_reason: str | None = None,
    ) -> None:
        self.provider_id = upstream.provider_id.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", self.provider_id):
            raise ValueError("provider_id must be a non-empty path-safe identifier")
        self._upstream = upstream
        self._cache_root = Path(cache_root)
        self._selection = {
            "selected_provider": self.provider_id,
            "alternatives": list(alternatives),
            "reason": selection_reason,
        }

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        symbols = tuple(symbol.strip().upper() for symbol in symbols)
        if not symbols or any(not symbol for symbol in symbols):
            raise ValueError("at least one non-empty symbol is required")
        if len(set(symbols)) != len(symbols):
            raise ValueError("requested symbols must be unique after normalization")
        if end < start:
            raise ValueError("request end date must not precede its start")
        request = _normalized_request(self.provider_id, symbols, start, end)
        entry_dir = self._entry_dir(symbols=symbols, start=start, end=end)
        if not force:
            try:
                return self._load(entry_dir, request, symbols)
            except _CacheMiss:
                pass

        result = self._upstream.fetch_daily_history(
            symbols,
            start=start,
            end=end,
            force=force,
        )
        records, source_availability = _to_records(result, symbols, start=start, end=end)
        canonical_result = _from_records(records, symbols, source_id=self.provider_id)
        for symbol, history in canonical_result.items():
            history.attrs["available_on"] = source_availability.get(symbol)
        self._publish(
            entry_dir,
            request,
            records,
            selection=self._selection,
            source_availability=source_availability,
        )
        return canonical_result

    def _entry_dir(self, *, symbols: tuple[str, ...], start: date, end: date) -> Path:
        fingerprint = daily_history_fingerprint(
            provider_id=self.provider_id,
            symbols=symbols,
            start=start,
            end=end,
        )
        return self._cache_root / self.provider_id / "daily_history" / fingerprint

    @staticmethod
    def _load(
        entry_dir: Path,
        request: dict[str, Any],
        requested_symbols: tuple[str, ...],
    ) -> dict[str, pd.DataFrame]:
        try:
            generation = (entry_dir / "CURRENT").read_text(encoding="ascii").strip()
            if not generation or any(
                character not in "0123456789abcdef" for character in generation
            ):
                raise _CacheMiss
            generation_dir = entry_dir / generation
            manifest_path = generation_dir / "manifest.json"
            data_path = generation_dir / "data.parquet"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema_version") != CACHE_SCHEMA_VERSION:
                raise _CacheMiss
            if manifest.get("request") != request:
                raise _CacheMiss
            if (
                manifest.get("provider_id") != request["provider_id"]
                or manifest.get("logical_data_point") != "daily_history"
                or manifest.get("data_file") != "data.parquet"
                or not isinstance(manifest.get("retrieved_at"), str)
                or not isinstance(manifest.get("selection"), dict)
                or manifest["selection"].get("selected_provider") != request["provider_id"]
            ):
                raise _CacheMiss
            retrieved_at = datetime.fromisoformat(manifest["retrieved_at"])
            if retrieved_at.tzinfo is None or retrieved_at.utcoffset() != UTC.utcoffset(None):
                raise _CacheMiss
            if _sha256(data_path) != manifest.get("data_sha256"):
                raise _CacheMiss

            records = pd.read_parquet(data_path)
            if list(records.columns) != _DATA_COLUMNS:
                raise _CacheMiss
            if not _has_canonical_record_types(records):
                raise _CacheMiss
            if not _valid_numeric_records(records):
                raise _CacheMiss
            if records.duplicated(subset=["symbol", "date"]).any():
                raise _CacheMiss
            if records["symbol"].isna().any() or records["date"].isna().any():
                raise _CacheMiss
            if not records["symbol"].isin(request["symbols"]).all():
                raise _CacheMiss
            date_values = records["date"].dt.date
            if (
                (date_values < date.fromisoformat(request["start"]))
                | (date_values > date.fromisoformat(request["end"]))
            ).any():
                raise _CacheMiss
            actual_start, actual_end, starts, ends = _record_coverage(records, requested_symbols)
            coverage = manifest.get("coverage")
            availability = manifest.get("source_availability_by_symbol")
            if not isinstance(coverage, dict) or not isinstance(availability, dict):
                raise _CacheMiss
            availability = cast(dict[str, object], availability)
            if coverage != {
                "requested_start": request["start"],
                "requested_end": request["end"],
                "actual_start": actual_start,
                "actual_end": actual_end,
                "actual_start_by_symbol": starts,
                "actual_end_by_symbol": ends,
            } or set(availability) != set(requested_symbols):
                raise _CacheMiss
            for symbol in requested_symbols:
                available_on = availability[symbol]
                if available_on is not None:
                    if not isinstance(available_on, str):
                        raise _CacheMiss
                    available_date = date.fromisoformat(available_on)
                    if ends.get(symbol) is None or available_date < date.fromisoformat(
                        ends[symbol]
                    ):
                        raise _CacheMiss
                elif ends.get(symbol) is not None:
                    raise _CacheMiss
                if ends.get(symbol) is None or ends[symbol] < request["end"]:
                    raise _CacheMiss
            result = _from_records(
                records,
                requested_symbols,
                source_id=request["provider_id"],
            )
            for symbol, history in result.items():
                history.attrs["available_on"] = availability[symbol]
            return result
        except (AttributeError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            raise _CacheMiss from None

    @staticmethod
    def _publish(
        entry_dir: Path,
        request: dict[str, Any],
        records: pd.DataFrame,
        *,
        selection: dict[str, Any],
        source_availability: dict[str, str | None],
    ) -> None:
        entry_dir.mkdir(parents=True, exist_ok=True)
        temporary_dir = Path(tempfile.mkdtemp(prefix=".publishing-", dir=entry_dir))
        generation = uuid.uuid4().hex
        generation_dir = entry_dir / generation
        published = False
        try:
            data_path = temporary_dir / "data.parquet"
            records.to_parquet(data_path, index=False)
            actual_start, actual_end, starts, ends = _record_coverage(records, request["symbols"])
            manifest = {
                "schema_version": CACHE_SCHEMA_VERSION,
                "provider_id": request["provider_id"],
                "logical_data_point": "daily_history",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "request": request,
                "coverage": {
                    "requested_start": request["start"],
                    "requested_end": request["end"],
                    "actual_start": actual_start,
                    "actual_end": actual_end,
                    "actual_start_by_symbol": starts,
                    "actual_end_by_symbol": ends,
                },
                "source_availability_by_symbol": source_availability,
                "selection": selection,
                "data_file": "data.parquet",
                "data_sha256": _sha256(data_path),
            }
            (temporary_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            for path in (data_path, temporary_dir / "manifest.json"):
                with path.open("rb") as file:
                    os.fsync(file.fileno())
            os.replace(temporary_dir, generation_dir)
            _replace_text_file(entry_dir / "CURRENT", generation)
            published = True
        finally:
            if temporary_dir.exists():
                shutil.rmtree(temporary_dir)
            if not published and generation_dir.exists():
                shutil.rmtree(generation_dir)


def _normalized_request(
    provider_id: str,
    symbols: tuple[str, ...],
    start: date,
    end: date,
) -> dict[str, Any]:
    return {
        "provider_id": provider_id.strip().lower(),
        "logical_data_point": "daily_history",
        "schema_version": CACHE_SCHEMA_VERSION,
        "symbols": sorted({symbol.strip().upper() for symbol in symbols}),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "frequency": "1d",
        "return_basis": "adjusted",
        "currency_basis": "USD",
    }


def _to_records(
    result: dict[str, pd.DataFrame],
    requested_symbols: tuple[str, ...],
    *,
    start: date,
    end: date,
) -> tuple[pd.DataFrame, dict[str, str | None]]:
    if set(result) - set(requested_symbols):
        raise ValueError("Daily history contains unexpected symbols")
    frames: list[pd.DataFrame] = []
    availability: dict[str, str | None] = {}
    for symbol in requested_symbols:
        history = result.get(symbol)
        if history is None or history.empty:
            availability[symbol] = None
            continue
        if not {"close", "volume"}.issubset(history.columns):
            raise ValueError(f"Daily history for {symbol} lacks canonical columns")
        frame = pd.DataFrame(history.loc[:, ["close", "volume"]].copy())
        frame.columns.name = None
        frame.insert(0, "date", pd.DatetimeIndex(frame.index).tz_localize(None))
        frame.insert(0, "symbol", symbol)
        if (
            frame["date"].isna().any()
            or frame["date"].duplicated().any()
            or (frame["date"].dt.date < start).any()
            or (frame["date"].dt.date > end).any()
        ):
            raise ValueError(f"Daily history for {symbol} has invalid dates")
        try:
            frame = frame.astype({"close": "float64", "volume": "float64"})
        except (TypeError, ValueError) as error:
            raise ValueError(f"Daily history for {symbol} has invalid values") from error
        if not _valid_numeric_records(frame):
            raise ValueError(f"Daily history for {symbol} has invalid values")
        available_on = history.attrs.get("available_on")
        if available_on is None:
            available_on = frame["date"].max().date().isoformat()
        if not isinstance(available_on, str) or (
            date.fromisoformat(available_on) < frame["date"].max().date()
        ):
            raise ValueError(f"Daily history for {symbol} has invalid availability")
        availability[symbol] = available_on
        frames.append(frame.reset_index(drop=True))
    if not frames:
        return pd.DataFrame(
            {
                "symbol": pd.Series(dtype="string"),
                "date": pd.Series(dtype="datetime64[ns]"),
                "close": pd.Series(dtype="float64"),
                "volume": pd.Series(dtype="float64"),
            }
        ), availability
    records = pd.concat(frames, ignore_index=True)
    records["symbol"] = records["symbol"].astype("string")
    return records.astype({"close": "float64", "volume": "float64"}), availability


def _record_coverage(
    records: pd.DataFrame, symbols: tuple[str, ...] | list[str]
) -> tuple[str | None, str | None, dict[str, str], dict[str, str]]:
    dates = records["date"]
    starts: dict[str, str] = {}
    ends: dict[str, str] = {}
    for symbol in symbols:
        symbol_dates = dates.loc[records["symbol"] == symbol]
        if not symbol_dates.empty:
            starts[symbol] = symbol_dates.min().date().isoformat()
            ends[symbol] = symbol_dates.max().date().isoformat()
    return (
        dates.min().date().isoformat() if not dates.empty else None,
        dates.max().date().isoformat() if not dates.empty else None,
        starts,
        ends,
    )


def _from_records(
    records: pd.DataFrame,
    requested_symbols: tuple[str, ...],
    *,
    source_id: str,
) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for symbol in requested_symbols:
        symbol_records = records.loc[records["symbol"] == symbol, ["date", "close", "volume"]]
        if symbol_records.empty:
            result[symbol] = pd.DataFrame(
                {
                    "close": pd.Series(dtype="float64"),
                    "volume": pd.Series(dtype="float64"),
                }
            )
            result[symbol].attrs.update({"source_id": source_id, "available_on": None})
            continue
        history = symbol_records.set_index("date").sort_index()
        history.index = pd.DatetimeIndex(history.index)
        history = history.astype({"close": "float64", "volume": "float64"})
        history.attrs.update(
            {
                "source_id": source_id,
                "available_on": history.index[-1].date().isoformat(),
            }
        )
        result[symbol] = history
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _has_canonical_record_types(records: pd.DataFrame) -> bool:
    return (
        str(records["symbol"].dtype).startswith("string")
        and str(records["date"].dtype) == "datetime64[ns]"
        and str(records["close"].dtype) == "float64"
        and str(records["volume"].dtype) == "float64"
    )


def _valid_numeric_records(records: pd.DataFrame) -> bool:
    return bool(
        all(records[column].map(math.isfinite).all() for column in ("close", "volume"))
        and (records["close"] > 0).all()
        and (records["volume"] >= 0).all()
    )


def _replace_text_file(path: Path, value: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as file:
            file.write(value)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
