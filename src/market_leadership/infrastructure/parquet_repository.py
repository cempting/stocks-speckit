import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from jsonschema import Draft202012Validator, FormatChecker

from market_leadership.application.ports import SnapshotReference
from market_leadership.infrastructure.snapshot_errors import (
    IntegrityError,
    SchemaMismatch,
    SnapshotNotFound,
)

_SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs/001-market-leadership-screener/contracts/snapshot-manifest.schema.json"
)
_MANIFEST_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_MANIFEST_VALIDATOR = Draft202012Validator(_MANIFEST_SCHEMA, format_checker=FormatChecker())
_WEEKLY_SCHEMA_PATH = _SCHEMA_PATH.with_name("weekly-snapshot-manifest.schema.json")
_WEEKLY_VALIDATOR = Draft202012Validator(
    json.loads(_WEEKLY_SCHEMA_PATH.read_text(encoding="utf-8")),
    format_checker=FormatChecker(),
)
_IDENTIFIER = re.compile(r"^[A-Za-z0-9._-]+$")
_TABLE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class ParquetSnapshotRepository:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def publish_weekly(
        self,
        *,
        snapshot_id: str,
        market_id: str,
        level: str,
        as_of: date,
        benchmark_id: str,
        currency: str,
        return_basis: str,
        classification_version: str,
        representation_version: str,
        ruleset_version: str,
        tables: dict[str, pd.DataFrame],
        sources: tuple[dict[str, str | None], ...],
    ) -> SnapshotReference:
        if _IDENTIFIER.fullmatch(snapshot_id) is None:
            raise ValueError("invalid snapshot ID")
        if level not in ("SECTOR", "INDUSTRY"):
            raise ValueError("level must be SECTOR or INDUSTRY")
        if not market_id.strip():
            raise ValueError("market ID is required")
        if isinstance(as_of, datetime):
            raise ValueError("as_of must be a completed-week date")
        if not tables:
            raise ValueError("at least one weekly snapshot table is required")
        root = self._root / "weekly"
        root.mkdir(parents=True, exist_ok=True)
        destination = root / snapshot_id
        if destination.exists():
            raise IntegrityError(snapshot_id, "manifest", "snapshot IDs are immutable")
        temporary = Path(tempfile.mkdtemp(prefix=".publishing-", dir=root))
        try:
            table_records: list[dict[str, Any]] = []
            for name, frame in sorted(tables.items()):
                if _TABLE_NAME.fullmatch(name) is None:
                    raise ValueError(f"invalid snapshot table name: {name}")
                _validate_weekly_frame(frame, snapshot_id, name, market_id, level)
                path = temporary / f"{name}.parquet"
                frame.to_parquet(path, index=False)
                persisted = pd.read_parquet(path)
                table_records.append(
                    {
                        "name": name,
                        "path": path.name,
                        "rows": len(persisted),
                        "sha256": _sha256(path),
                        "columns": _columns(persisted),
                    }
                )
            manifest: dict[str, Any] = {
                "schema_version": "weekly-1.0.0",
                "snapshot_id": snapshot_id,
                "market_id": market_id,
                "level": level,
                "as_of": as_of.isoformat(),
                "built_at": datetime.now(UTC).isoformat(),
                "benchmark_id": benchmark_id,
                "currency": currency,
                "return_basis": return_basis,
                "classification_version": classification_version,
                "representation_version": representation_version,
                "ruleset_version": ruleset_version,
                "tables": table_records,
                "sources": list(sources),
            }
            _validate_weekly_manifest(manifest, snapshot_id)
            for directory in root.iterdir():
                if not directory.is_dir() or directory.name.startswith("."):
                    continue
                existing, _ = self._read_weekly_manifest(directory.name)
                if all(
                    existing[field] == manifest[field]
                    for field in ("market_id", "level", "as_of", "ruleset_version")
                ):
                    raise IntegrityError(snapshot_id, "manifest", "weekly scope already published")
            manifest_path = temporary / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if destination.exists():
                raise IntegrityError(snapshot_id, "manifest", "snapshot IDs are immutable")
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        return _reference(manifest, destination / "manifest.json")

    def load_weekly(self, snapshot_id: str) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
        manifest, directory = self._read_weekly_manifest(snapshot_id)
        tables: dict[str, pd.DataFrame] = {}
        for record in manifest["tables"]:
            name = record["name"]
            path = directory / record["path"]
            if not path.is_file():
                raise SnapshotNotFound(snapshot_id, name)
            if _sha256(path) != record["sha256"]:
                raise IntegrityError(snapshot_id, name, "checksum does not match manifest")
            try:
                frame = pd.read_parquet(path)
            except (OSError, ValueError, ImportError) as error:
                raise SchemaMismatch(snapshot_id, name, "Parquet data cannot be read") from error
            if len(frame) != record["rows"]:
                raise IntegrityError(snapshot_id, name, "row count does not match manifest")
            if _columns(frame) != record["columns"]:
                raise SchemaMismatch(snapshot_id, name, "column schema does not match manifest")
            _validate_weekly_frame(
                frame, snapshot_id, name, manifest["market_id"], manifest["level"]
            )
            tables[name] = frame
        return manifest, tables

    def load_latest_weekly(self, market_id: str, level: str) -> SnapshotReference:
        if not market_id.strip():
            raise ValueError("market ID is required")
        if level not in ("SECTOR", "INDUSTRY"):
            raise ValueError("level must be SECTOR or INDUSTRY")
        root = self._root / "weekly"
        if not root.is_dir():
            raise SnapshotNotFound(market_id, level)
        matches: list[tuple[date, SnapshotReference]] = []
        for directory in root.iterdir():
            if not directory.is_dir() or directory.name.startswith("."):
                continue
            manifest, _ = self._read_weekly_manifest(directory.name)
            if manifest["market_id"] != market_id or manifest["level"] != level:
                continue
            self.load_weekly(directory.name)
            matches.append(
                (
                    date.fromisoformat(manifest["as_of"]),
                    _reference(manifest, directory / "manifest.json"),
                )
            )
        if not matches:
            raise SnapshotNotFound(market_id, level)
        return max(matches, key=lambda match: (match[0], match[1].snapshot_id))[1]

    def _read_weekly_manifest(self, snapshot_id: str) -> tuple[dict[str, Any], Path]:
        if _IDENTIFIER.fullmatch(snapshot_id) is None:
            raise ValueError("invalid snapshot ID")
        directory = self._root / "weekly" / snapshot_id
        try:
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            # A Phase 2 input snapshot with this ID is not a calculated weekly artifact.
            if (self._root / snapshot_id / "manifest.json").is_file():
                raise SchemaMismatch(
                    snapshot_id, "manifest", "daily input is not a weekly snapshot"
                ) from error
            raise SnapshotNotFound(snapshot_id, "manifest") from error
        except json.JSONDecodeError as error:
            raise SchemaMismatch(snapshot_id, "manifest", "manifest is not valid JSON") from error
        _validate_weekly_manifest(manifest, snapshot_id)
        return manifest, directory

    def reference(self, snapshot_id: str) -> SnapshotReference:
        manifest = self._read_manifest(snapshot_id)
        return _reference(manifest, self._snapshot_dir(snapshot_id) / "manifest.json")

    def load_latest(self) -> SnapshotReference:
        if not self._root.is_dir():
            raise SnapshotNotFound("snapshot", "manifest")
        manifests: list[tuple[datetime, SnapshotReference]] = []
        for directory in self._root.iterdir():
            if (
                not directory.is_dir()
                or directory.name.startswith(".")
                or directory.name == "weekly"
            ):
                continue
            manifest = self._read_manifest(directory.name)
            built_at = datetime.fromisoformat(manifest["built_at"].replace("Z", "+00:00"))
            manifests.append((built_at, _reference(manifest, directory / "manifest.json")))
        if not manifests:
            raise SnapshotNotFound("snapshot", "manifest")
        return max(manifests, key=lambda item: (item[0], item[1].snapshot_id))[1]

    def load(self, snapshot_id: str) -> dict[str, pd.DataFrame]:
        directory = self._snapshot_dir(snapshot_id)
        manifest = self._read_manifest(snapshot_id)
        tables: dict[str, pd.DataFrame] = {}
        for table in manifest["tables"]:
            table_name = table["name"]
            relative_path = Path(table["path"])
            if relative_path.is_absolute() or len(relative_path.parts) != 1:
                raise SchemaMismatch(snapshot_id, table_name, "table path must be a filename")
            path = directory / relative_path
            if not path.is_file():
                raise SnapshotNotFound(snapshot_id, table_name)
            if _sha256(path) != table["sha256"]:
                raise IntegrityError(snapshot_id, table_name, "checksum does not match manifest")
            try:
                frame = pd.read_parquet(path)
            except (OSError, ValueError, ImportError) as error:
                raise SchemaMismatch(
                    snapshot_id, table_name, "Parquet data cannot be read"
                ) from error
            if len(frame) != table["rows"]:
                raise IntegrityError(snapshot_id, table_name, "row count does not match manifest")
            if any(not isinstance(column, str) for column in frame.columns):
                raise SchemaMismatch(snapshot_id, table_name, "column names must be strings")
            if frame.columns.has_duplicates:
                raise SchemaMismatch(snapshot_id, table_name, "column names must be unique")
            tables[table_name] = frame
        return tables

    def publish(
        self,
        *,
        snapshot_id: str,
        as_of: date,
        markets: tuple[str, ...],
        ruleset_version: str,
        tables: dict[str, pd.DataFrame],
        sources: tuple[dict[str, str | None], ...],
    ) -> SnapshotReference:
        if _IDENTIFIER.fullmatch(snapshot_id) is None:
            raise ValueError(
                "snapshot ID must contain only letters, digits, dot, underscore, or hyphen"
            )
        if not tables:
            raise ValueError("at least one snapshot table is required")
        if not markets or not ruleset_version.strip() or not sources:
            raise ValueError("markets, ruleset version, and source records are required")

        self._root.mkdir(parents=True, exist_ok=True)
        destination = self._snapshot_dir(snapshot_id)
        if destination.exists():
            raise IntegrityError(snapshot_id, "manifest", "snapshot IDs are immutable")
        temporary = Path(tempfile.mkdtemp(prefix=".publishing-", dir=self._root))
        try:
            table_records = []
            for name, frame in sorted(tables.items()):
                if _TABLE_NAME.fullmatch(name) is None:
                    raise ValueError(f"invalid snapshot table name: {name}")
                if any(not isinstance(column, str) for column in frame.columns):
                    raise ValueError(f"column names for {name} must be strings")
                if frame.columns.has_duplicates:
                    raise ValueError(f"column names for {name} must be unique")
                relative_path = f"{name}.parquet"
                table_path = temporary / relative_path
                frame.to_parquet(table_path, index=False)
                table_records.append(
                    {
                        "name": name,
                        "path": relative_path,
                        "rows": len(frame),
                        "sha256": _sha256(table_path),
                    }
                )
            manifest: dict[str, Any] = {
                "schema_version": "1.0.0",
                "snapshot_id": snapshot_id,
                "as_of": as_of.isoformat(),
                "built_at": datetime.now(UTC).isoformat(),
                "ruleset_version": ruleset_version,
                "markets": list(markets),
                "tables": table_records,
                "sources": list(sources),
            }
            _validate_manifest(manifest, snapshot_id)
            manifest_path = temporary / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        return _reference(manifest, destination / "manifest.json")

    def _snapshot_dir(self, snapshot_id: str) -> Path:
        if _IDENTIFIER.fullmatch(snapshot_id) is None:
            raise ValueError("invalid snapshot ID")
        return self._root / snapshot_id

    def _read_manifest(self, snapshot_id: str) -> dict[str, Any]:
        path = self._snapshot_dir(snapshot_id) / "manifest.json"
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise SnapshotNotFound(snapshot_id, "manifest") from error
        except json.JSONDecodeError as error:
            raise SchemaMismatch(snapshot_id, "manifest", "manifest is not valid JSON") from error
        _validate_manifest(manifest, snapshot_id)
        return manifest


def _validate_manifest(manifest: Any, snapshot_id: str) -> None:
    errors = sorted(
        _MANIFEST_VALIDATOR.iter_errors(manifest),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "; ".join(error.message for error in errors[:3])
        raise SchemaMismatch(snapshot_id, "manifest", detail)
    if manifest["snapshot_id"] != snapshot_id:
        raise IntegrityError(snapshot_id, "manifest", "snapshot ID does not match directory")
    table_names = [table["name"] for table in manifest["tables"]]
    table_paths = [table["path"] for table in manifest["tables"]]
    if len(set(table_names)) != len(table_names) or len(set(table_paths)) != len(table_paths):
        raise IntegrityError(snapshot_id, "manifest", "table names and paths must be unique")


def _validate_weekly_manifest(manifest: Any, snapshot_id: str) -> None:
    errors = sorted(
        _WEEKLY_VALIDATOR.iter_errors(manifest),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise SchemaMismatch(
            snapshot_id, "manifest", "; ".join(error.message for error in errors[:3])
        )
    if manifest["snapshot_id"] != snapshot_id:
        raise IntegrityError(snapshot_id, "manifest", "snapshot ID does not match directory")
    for field in (
        "market_id",
        "benchmark_id",
        "return_basis",
        "classification_version",
        "representation_version",
        "ruleset_version",
    ):
        if not manifest[field].strip():
            raise SchemaMismatch(snapshot_id, "manifest", f"{field} must not be blank")
    names = [table["name"] for table in manifest["tables"]]
    paths = [table["path"] for table in manifest["tables"]]
    if len(set(names)) != len(names) or len(set(paths)) != len(paths):
        raise IntegrityError(snapshot_id, "manifest", "table names and paths must be unique")
    for record in manifest["tables"]:
        if record["path"] != f"{record['name']}.parquet":
            raise SchemaMismatch(snapshot_id, record["name"], "table path does not match name")
        columns = [column["name"] for column in record["columns"]]
        if len(set(columns)) != len(columns):
            raise SchemaMismatch(snapshot_id, record["name"], "column names must be unique")
        if "market_id" not in columns or "level" not in columns:
            raise SchemaMismatch(
                snapshot_id, record["name"], "market_id and level columns required"
            )


def _columns(frame: pd.DataFrame) -> list[dict[str, str]]:
    return [{"name": name, "dtype": str(dtype)} for name, dtype in frame.dtypes.items()]


def _validate_weekly_frame(
    frame: pd.DataFrame, snapshot_id: str, table_name: str, market_id: str, level: str
) -> None:
    if type(frame) is not pd.DataFrame:
        raise SchemaMismatch(snapshot_id, table_name, "table must be a DataFrame")
    if any(not isinstance(name, str) or not name for name in frame.columns):
        raise SchemaMismatch(snapshot_id, table_name, "column names must be nonempty strings")
    if frame.columns.has_duplicates:
        raise SchemaMismatch(snapshot_id, table_name, "column names must be unique")
    if "market_id" not in frame or "level" not in frame:
        raise SchemaMismatch(snapshot_id, table_name, "market_id and level columns required")
    if any(value != market_id for value in frame["market_id"]):
        raise SchemaMismatch(snapshot_id, table_name, "market_id does not match weekly scope")
    if any(value != level for value in frame["level"]):
        raise SchemaMismatch(snapshot_id, table_name, "level does not match weekly scope")


def _reference(manifest: dict[str, Any], manifest_path: Path) -> SnapshotReference:
    return SnapshotReference(
        snapshot_id=manifest["snapshot_id"],
        as_of=date.fromisoformat(manifest["as_of"]),
        manifest_checksum=_sha256(manifest_path),
        ruleset_version=manifest["ruleset_version"],
        source_id=(manifest["sources"][0]["source_id"] if len(manifest["sources"]) == 1 else None),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
