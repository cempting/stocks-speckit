import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from market_leadership.application.ports import MarketDataProvider

CACHE_SCHEMA_VERSION = 1
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
    def __init__(self, upstream: MarketDataProvider, cache_root: str | Path) -> None:
        self.provider_id = upstream.provider_id
        self._upstream = upstream
        self._cache_root = Path(cache_root)

    def fetch_daily_history(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
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
        self._publish(entry_dir, request, result)
        return result

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
            if manifest.get("coverage", {}).get("requested_end") < request["end"]:
                raise _CacheMiss
            if _sha256(data_path) != manifest.get("data_sha256"):
                raise _CacheMiss

            records = pd.read_parquet(data_path)
            if list(records.columns) != _DATA_COLUMNS:
                raise _CacheMiss
            return _from_records(records, requested_symbols)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            raise _CacheMiss from None

    @staticmethod
    def _publish(
        entry_dir: Path,
        request: dict[str, Any],
        result: dict[str, pd.DataFrame],
    ) -> None:
        records = _to_records(result, tuple(request["symbols"]))
        entry_dir.mkdir(parents=True, exist_ok=True)
        temporary_dir = Path(tempfile.mkdtemp(prefix=".publishing-", dir=entry_dir))
        generation = uuid.uuid4().hex
        generation_dir = entry_dir / generation
        try:
            data_path = temporary_dir / "data.parquet"
            records.to_parquet(data_path, index=False)
            coverage_dates = records["date"].dropna()
            manifest = {
                "schema_version": CACHE_SCHEMA_VERSION,
                "provider_id": request["provider_id"],
                "logical_data_point": "daily_history",
                "retrieved_at": datetime.now(UTC).isoformat(),
                "request": request,
                "coverage": {
                    "requested_start": request["start"],
                    "requested_end": request["end"],
                    "actual_start": (
                        coverage_dates.min().date().isoformat()
                        if not coverage_dates.empty
                        else None
                    ),
                    "actual_end": (
                        coverage_dates.max().date().isoformat()
                        if not coverage_dates.empty
                        else None
                    ),
                },
                "data_file": "data.parquet",
                "data_sha256": _sha256(data_path),
            }
            (temporary_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary_dir, generation_dir)
            _replace_text_file(entry_dir / "CURRENT", generation)
        finally:
            if temporary_dir.exists():
                shutil.rmtree(temporary_dir)


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
        "currency_basis": "native",
    }


def _to_records(
    result: dict[str, pd.DataFrame], requested_symbols: tuple[str, ...]
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol in requested_symbols:
        history = result.get(symbol)
        if history is None or history.empty:
            continue
        if not {"close", "volume"}.issubset(history.columns):
            raise ValueError(f"Daily history for {symbol} lacks canonical columns")
        frame = pd.DataFrame(history.loc[:, ["close", "volume"]].copy())
        frame.insert(0, "date", pd.DatetimeIndex(frame.index).tz_localize(None))
        frame.insert(0, "symbol", symbol)
        frames.append(frame.reset_index(drop=True))
    if not frames:
        return pd.DataFrame(
            {
                "symbol": pd.Series(dtype="string"),
                "date": pd.Series(dtype="datetime64[ns]"),
                "close": pd.Series(dtype="float64"),
                "volume": pd.Series(dtype="float64"),
            }
        )
    records = pd.concat(frames, ignore_index=True)
    records["symbol"] = records["symbol"].astype("string")
    return records.astype({"close": "float64", "volume": "float64"})


def _from_records(
    records: pd.DataFrame, requested_symbols: tuple[str, ...]
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
            continue
        history = symbol_records.set_index("date").sort_index()
        history.index = pd.DatetimeIndex(history.index)
        result[symbol] = history.astype({"close": "float64", "volume": "float64"})
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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