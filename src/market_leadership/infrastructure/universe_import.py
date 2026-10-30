"""Validation and atomic ingestion of reviewed local universe files."""

import csv
import json
import re
import sqlite3
import unicodedata
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal, cast

from market_leadership.infrastructure.region_database import RegionDatabase

ImportStatus = Literal["validated", "committed", "committed_partial", "rejected"]


@dataclass(frozen=True, slots=True)
class ImportIssue:
    source_row: int | None
    entity_id: str | None
    kind: str
    detail: str
    severity: Literal["warning", "error"]


@dataclass(frozen=True, slots=True)
class ImportReport:
    status: ImportStatus
    input_fingerprint: str
    row_count: int
    accepted_rows: int
    inserted_rows: int
    placeholder_rows: int
    unclassified_rows: int
    conflicting_rows: int
    issues: tuple[ImportIssue, ...]
    completed_at: datetime


@dataclass(frozen=True, slots=True)
class _InputRow:
    source_row: int
    instrument_id: str
    company_id: str | None
    ticker: str | None
    name: str
    exchange_id: str | None
    provider_symbol: str | None
    currency: str
    sector_id: str | None
    sector_name: str | None
    industry_id: str | None
    industry_name: str | None
    effective_from: date
    effective_to: date | None
    resolution_state: Literal["identified", "placeholder"]

    @property
    def classification_key(self) -> tuple[str | None, str | None]:
        return self.sector_id, self.industry_id


_HEADER_ALIASES = {
    "instrumentid": "instrument_id",
    "companyid": "company_id",
    "ticker": "ticker",
    "symbol": "ticker",
    "name": "name",
    "exchange": "exchange_id",
    "exchangeid": "exchange_id",
    "providersymbol": "provider_symbol",
    "currency": "currency",
    "sector": "sector_name",
    "sectorid": "sector_id",
    "industry": "industry_name",
    "industryid": "industry_id",
    "effectivestart": "effective_from",
    "effectivefrom": "effective_from",
    "effectiveend": "effective_to",
    "effectiveto": "effective_to",
    "resolutionstate": "resolution_state",
}
_MISSING_CLASSIFICATION_VALUES = {"", "undefined", "unknown", "n/a", "na", "none", "null"}


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "unnamed"


def _value(row: dict[str, object], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _classification_value(value: str | None) -> str | None:
    if value is None or value.casefold() in _MISSING_CLASSIFICATION_VALUES:
        return None
    return value


def _parse_date(value: str | None, *, default: date) -> date:
    if value is None:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Invalid ISO effective date {value!r}") from error


def _normalized_record(raw: dict[str, object], source_row: int) -> _InputRow:
    record = {
        _HEADER_ALIASES.get(key.lower().replace("_", ""), key.lower()): value
        for key, value in raw.items()
    }
    name = _value(record, "name")
    ticker = _value(record, "ticker")
    state_text = _value(record, "resolution_state") or ("identified" if ticker else "")
    if state_text not in ("identified", "placeholder"):
        raise ValueError("ResolutionState must be 'identified' or 'placeholder'")
    resolution_state: Literal["identified", "placeholder"] = state_text
    instrument_id = _value(record, "instrument_id")
    exchange_id = _value(record, "exchange_id")
    if not name:
        raise ValueError("Name must not be empty")
    if ticker:
        ticker = ticker.upper()
        if not re.fullmatch(r"[A-Z0-9.^=-]{1,32}", ticker):
            raise ValueError(f"Ticker {ticker!r} contains unsupported characters")
        if not instrument_id:
            if not exchange_id:
                raise ValueError("InstrumentId or exchange metadata is required for a ticker")
            instrument_id = (
                f"{_slug(_value(record, 'region_id') or 'US')}-"
                f"{_slug(exchange_id)}-{ticker.lower()}"
            )
        if resolution_state != "identified":
            raise ValueError("A placeholder must not declare a tradable ticker")
    else:
        if resolution_state != "placeholder" or not instrument_id:
            raise ValueError("Rows without a ticker must declare placeholder and InstrumentId")
        exchange_id = None
    sector_name = _classification_value(_value(record, "sector_name"))
    industry_name = _classification_value(_value(record, "industry_name"))
    sector_id = _classification_value(_value(record, "sector_id"))
    industry_id = _classification_value(_value(record, "industry_id"))
    if not sector_name or not industry_name:
        sector_name = None
        industry_name = None
        sector_id = None
        industry_id = None
    if sector_name and not sector_id:
        sector_id = _slug(sector_name)
    if industry_name and not industry_id:
        industry_id = _slug(industry_name)
    effective_from = _parse_date(_value(record, "effective_from"), default=date(1970, 1, 1))
    effective_to = (
        _parse_date(_value(record, "effective_to"), default=date.max)
        if _value(record, "effective_to")
        else None
    )
    if effective_to is not None and effective_to < effective_from:
        raise ValueError("EffectiveTo must not be earlier than EffectiveFrom")
    currency = (_value(record, "currency") or "USD").upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("Currency must be a three-letter alphabetic code")
    if resolution_state == "placeholder" and not sector_name:
        raise ValueError("A placeholder must have a reviewed sector and industry membership")
    return _InputRow(
        source_row=source_row,
        instrument_id=instrument_id,
        company_id=_value(record, "company_id"),
        ticker=ticker,
        name=name,
        exchange_id=exchange_id.upper() if exchange_id else None,
        provider_symbol=(_value(record, "provider_symbol") or ticker) if ticker else None,
        currency=currency,
        sector_id=sector_id,
        sector_name=sector_name,
        industry_id=industry_id,
        industry_name=industry_name,
        effective_from=effective_from,
        effective_to=effective_to,
        resolution_state=resolution_state,
    )


def _read_rows(path: str | Path, *, fallback_exchange: str | None) -> tuple[bytes, list[_InputRow]]:
    source = Path(path)
    raw = source.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("Universe input exceeds the two-megabyte limit")
    if source.suffix.lower() == ".json":
        decoded: object = json.loads(raw)
        if not isinstance(decoded, dict):
            raise ValueError("JSON universe input must be an object")
        document = cast(dict[str, object], decoded)
        if document.get("schema_version") != 1 or document.get("market") != "US":
            raise ValueError("JSON catalog requires schema_version 1 and market US")
        entries = document.get("entries")
        if not isinstance(entries, list):
            raise ValueError("JSON catalog entries must be an array")
        raw_rows: list[dict[str, object]] = []
        for item in cast(list[object], entries):
            if not isinstance(item, dict):
                raise ValueError("Each JSON catalog entry must be an object")
            raw_rows.append(cast(dict[str, object], item))
    elif source.suffix.lower() == ".csv":
        decoded = raw.decode("utf-8-sig")
        reader = csv.DictReader(decoded.splitlines())
        if reader.fieldnames is None:
            raise ValueError("CSV input must include a header row")
        required = {"ticker", "name", "sector", "industry"}
        headers = {header.lower().replace("_", "") for header in reader.fieldnames}
        if not required.issubset(headers):
            missing = ", ".join(sorted(required - headers))
            raise ValueError(f"CSV is missing required columns: {missing}")
        if "exchange" not in headers and "exchangeid" not in headers and not fallback_exchange:
            raise ValueError("Exchange metadata is required when the input has no Exchange column")
        raw_rows = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"CSV row {line_number} has more values than header columns")
            values = cast(
                dict[str, object], {key: value for key, value in row.items() if key is not None}
            )
            values.setdefault("Exchange", fallback_exchange)
            raw_rows.append(values)
    else:
        raise ValueError("Universe input must be a .csv or .json file")

    rows: list[_InputRow] = []
    for source_row, raw_row in enumerate(raw_rows, start=2):
        normalized = dict(raw_row)
        normalized.setdefault("Exchange", fallback_exchange)
        rows.append(_normalized_record(normalized, source_row))
    return raw, rows


def _validated_rows(
    rows: list[_InputRow],
) -> tuple[list[_InputRow], tuple[ImportIssue, ...], int, int]:
    issues: list[ImportIssue] = []
    by_instrument: dict[str, list[_InputRow]] = {}
    seen_listings: dict[tuple[str | None, str | None], list[_InputRow]] = {}
    sector_values: dict[str, set[str]] = {}
    industry_values: dict[str, set[tuple[str | None, str | None, str | None]]] = {}
    for row in rows:
        by_instrument.setdefault(row.instrument_id, []).append(row)
        if row.sector_id and row.sector_name:
            sector_values.setdefault(row.sector_id, set()).add(row.sector_name)
        if row.industry_id and row.industry_name:
            industry_values.setdefault(row.industry_id, set()).add(
                (row.sector_id, row.sector_name, row.industry_name)
            )
        if row.ticker:
            key = row.exchange_id, row.ticker
            prior_rows = seen_listings.setdefault(key, [])
            for prior in prior_rows:
                overlaps = (
                    (prior.effective_to or date.max) >= row.effective_from
                    and (row.effective_to or date.max) >= prior.effective_from
                )
                if not overlaps:
                    continue
                if prior.instrument_id == row.instrument_id:
                    if (
                        prior.effective_from == row.effective_from
                        and prior.classification_key == row.classification_key
                        and prior.name == row.name
                    ):
                        issues.append(
                            ImportIssue(
                                row.source_row,
                                row.instrument_id,
                                "duplicate_listing",
                                f"Duplicate listing {row.exchange_id}:{row.ticker} was ignored.",
                                "warning",
                            )
                        )
                else:
                    issues.append(
                        ImportIssue(
                            prior.source_row,
                            prior.instrument_id,
                            "conflicting_listing",
                            f"Listing {row.exchange_id}:{row.ticker} overlaps another instrument.",
                            "error",
                        )
                    )
                    issues.append(
                        ImportIssue(
                            row.source_row,
                            row.instrument_id,
                            "conflicting_listing",
                            f"Listing {row.exchange_id}:{row.ticker} conflicts with another row.",
                            "error",
                        )
                    )
            prior_rows.append(row)

    conflicting_ids: set[str] = set()
    for instrument_id, instrument_rows in by_instrument.items():
        names = {row.name for row in instrument_rows}
        companies = {row.company_id for row in instrument_rows if row.company_id is not None}
        if len(names) > 1 or len(companies) > 1:
            conflicting_ids.add(instrument_id)
            for row in instrument_rows:
                issues.append(
                    ImportIssue(
                        row.source_row,
                        instrument_id,
                        "identity_conflict",
                        "The same instrument has conflicting identity values; "
                        "all conflicting rows were quarantined.",
                        "error",
                    )
                )
        classifications = {
            row.classification_key
            for row in instrument_rows
            if row.classification_key != (None, None)
        }
        if len(classifications) > 1:
            conflicting_ids.add(instrument_id)
            for row in instrument_rows:
                issues.append(
                    ImportIssue(
                        row.source_row,
                        instrument_id,
                        "classification_conflict",
                        "The same instrument has conflicting sector or industry values; "
                        "all conflicting rows were quarantined.",
                        "error",
                    )
                )
    for sector_id, names in sector_values.items():
        if len(names) > 1:
            issues.extend(
                ImportIssue(
                    row.source_row,
                    sector_id,
                    "classification_conflict",
                    "The same sector identity has conflicting names; "
                    "all conflicting rows were quarantined.",
                    "error",
                )
                for row in rows
                if row.sector_id == sector_id
            )
    for industry_id, identities in industry_values.items():
        if len(identities) > 1:
            issues.extend(
                ImportIssue(
                    row.source_row,
                    industry_id,
                    "classification_conflict",
                    "The same industry identity has conflicting names or parents; "
                    "all conflicting rows were quarantined.",
                    "error",
                )
                for row in rows
                if row.industry_id == industry_id
            )
    invalid_row_ids = {
        issue.source_row for issue in issues if issue.severity == "error" and issue.source_row
    }
    duplicate_row_ids = {
        issue.source_row for issue in issues if issue.kind == "duplicate_listing"
    }
    valid: list[_InputRow] = []
    for row in rows:
        if (
            row.instrument_id not in conflicting_ids
            and row.source_row not in invalid_row_ids
            and row.source_row not in duplicate_row_ids
        ):
            valid.append(row)
    placeholders = sum(row.resolution_state == "placeholder" for row in valid)
    unclassified = sum(row.classification_key == (None, None) for row in valid)
    return valid, tuple(issues), placeholders, unclassified


def _listing_matches(
    listing: sqlite3.Row, row: _InputRow, *, region_id: str
) -> bool:
    return (
        listing["instrument_id"] == row.instrument_id
        and listing["region_id"] == region_id
        and listing["exchange_id"] == row.exchange_id
        and listing["symbol"] == row.ticker
        and listing["provider_symbol"] == row.provider_symbol
        and listing["currency"] == row.currency
        and listing["effective_from"] == row.effective_from.isoformat()
        and listing["effective_to"]
        == (row.effective_to.isoformat() if row.effective_to else None)
    )


def _database_conflicts(
    connection: sqlite3.Connection,
    rows: list[_InputRow],
    *,
    region_id: str,
    classification_id: str,
) -> tuple[list[_InputRow], tuple[ImportIssue, ...]]:
    issues: list[ImportIssue] = []
    classification = connection.execute(
        "SELECT region_id FROM classifications WHERE classification_id = ?",
        (classification_id,),
    ).fetchone()
    if classification is not None and classification["region_id"] != region_id:
        return [], tuple(
            ImportIssue(
                row.source_row,
                classification_id,
                "classification_conflict",
                "The classification identity belongs to a different region; "
                "the row was quarantined.",
                "error",
            )
            for row in rows
        )
    for row in rows:
        stock = connection.execute(
            "SELECT name, company_id FROM stocks WHERE instrument_id = ?",
            (row.instrument_id,),
        ).fetchone()
        if stock is not None and (
            stock["name"] != row.name
            or (
                stock["company_id"] is not None
                and row.company_id is not None
                and stock["company_id"] != row.company_id
            )
        ):
            issues.append(
                ImportIssue(
                    row.source_row,
                    row.instrument_id,
                    "identity_conflict",
                    "The imported name or company identity disagrees with the stored security; "
                    "the row was quarantined.",
                    "error",
                )
            )

        if row.ticker and row.exchange_id:
            listings = connection.execute(
                """
                SELECT instrument_id, region_id, exchange_id, symbol, provider_symbol,
                       currency, effective_from, effective_to
                FROM stock_listings
                WHERE region_id = ? AND exchange_id = ? AND symbol = ?
                  AND COALESCE(effective_to, '9999-12-31') >= ?
                  AND COALESCE(?, '9999-12-31') >= effective_from
                """,
                (
                    region_id,
                    row.exchange_id,
                    row.ticker,
                    row.effective_from.isoformat(),
                    row.effective_to.isoformat() if row.effective_to else None,
                ),
            ).fetchall()
            if any(
                not _listing_matches(listing, row, region_id=region_id)
                for listing in listings
            ):
                issues.append(
                    ImportIssue(
                        row.source_row,
                        row.instrument_id,
                        "listing_conflict",
                        f"Listing {row.exchange_id}:{row.ticker} conflicts with a stored "
                        "listing identity, provider symbol, currency, or effective period.",
                        "error",
                    )
                )

        industry_id = (
            f"{classification_id.lower()}-{row.industry_id}" if row.industry_id else None
        )
        if industry_id is None:
            continue
        sector_id = f"{classification_id.lower()}-{row.sector_id}"
        sector = connection.execute(
            "SELECT name, classification_id FROM sectors WHERE sector_id = ?",
            (sector_id,),
        ).fetchone()
        if sector is not None and (
            sector["name"] != row.sector_name
            or sector["classification_id"] != classification_id
        ):
            issues.append(
                ImportIssue(
                    row.source_row,
                    sector_id,
                    "classification_conflict",
                    "The imported sector identity, name, or classification conflicts with "
                    "the reviewed database; the row was quarantined.",
                    "error",
                )
            )
        membership = connection.execute(
            """
            SELECT industry_id FROM stock_memberships
            WHERE instrument_id = ? AND region_id = ? AND classification_id = ?
              AND review_state = 'reviewed'
              AND COALESCE(effective_to, '9999-12-31') >= ?
              AND COALESCE(?, '9999-12-31') >= effective_from
              AND industry_id != ?
            LIMIT 1
            """,
            (
                row.instrument_id,
                region_id,
                classification_id,
                row.effective_from.isoformat(),
                row.effective_to.isoformat() if row.effective_to else None,
                industry_id,
            ),
        ).fetchone()
        if membership is not None:
            issues.append(
                ImportIssue(
                    row.source_row,
                    row.instrument_id,
                    "classification_conflict",
                    "The imported membership disagrees with a reviewed local membership; "
                    "the row was quarantined.",
                    "error",
                )
            )

        identity = connection.execute(
            """
            SELECT i.name AS industry_name, i.sector_id, i.classification_id,
                   s.name AS sector_name
            FROM industries i JOIN sectors s ON s.sector_id = i.sector_id
            WHERE i.industry_id = ?
            """,
            (industry_id,),
        ).fetchone()
        if identity is not None and (
            identity["industry_name"] != row.industry_name
            or identity["sector_name"] != row.sector_name
            or identity["sector_id"] != sector_id
            or identity["classification_id"] != classification_id
        ):
            issues.append(
                ImportIssue(
                    row.source_row,
                    industry_id,
                    "classification_conflict",
                    "The imported industry identity or parent conflicts with the reviewed "
                    "database; the row was quarantined.",
                    "error",
                )
            )

    invalid_rows = {
        issue.source_row for issue in issues if issue.severity == "error" and issue.source_row
    }
    return (
        [row for row in rows if row.source_row not in invalid_rows],
        tuple(issues),
    )


def _read_only_database_conflicts(
    database: RegionDatabase,
    rows: list[_InputRow],
    *,
    region_id: str,
    classification_id: str,
) -> tuple[list[_InputRow], tuple[ImportIssue, ...]]:
    if not database.path.exists():
        return rows, ()
    uri = f"{database.path.resolve().as_uri()}?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            required_tables = {
                "stocks",
                "stock_listings",
                "stock_memberships",
                "industries",
                "sectors",
                "classifications",
            }
            if not required_tables.issubset(tables):
                return rows, ()
            return _database_conflicts(
                connection,
                rows,
                region_id=region_id,
                classification_id=classification_id,
            )
    except sqlite3.Error as error:
        raise ValueError(f"Could not read validation database {database.path}: {error}") from error


def _regional_coverage(
    connection: sqlite3.Connection, *, region_id: str, source_id: str, coverage: str
) -> str:
    metadata_key = f"regional_reviewed_coverage:{region_id}"
    stored = connection.execute(
        "SELECT value FROM database_metadata WHERE key = ?", (metadata_key,)
    ).fetchone()
    scope_history: dict[str, list[str]] = {}
    if stored is not None:
        decoded: object = json.loads(stored["value"])
        if not isinstance(decoded, dict):
            raise ValueError("Stored regional coverage metadata must be a source-to-scope mapping")
        for key, value in cast(dict[str, object], decoded).items():
            if not isinstance(value, list) or not all(
                isinstance(scope, str) for scope in cast(list[object], value)
            ):
                raise ValueError("Stored regional coverage scopes must be lists of descriptions")
            scope_history[key] = cast(list[str], value)

    coverage_rows = connection.execute(
        """
        WITH regional_sources AS (
            SELECT source_id FROM classifications WHERE region_id = ?
            UNION
            SELECT source_id FROM stock_listings WHERE region_id = ?
            UNION
            SELECT source_id FROM stock_memberships WHERE region_id = ?
            UNION
            SELECT source_id FROM entity_representations WHERE region_id = ?
        )
        SELECT DISTINCT ds.source_id, ds.coverage
        FROM data_sources ds
        JOIN regional_sources rs ON rs.source_id = ds.source_id
        WHERE ds.coverage IS NOT NULL
        ORDER BY ds.source_id
        """,
        (region_id, region_id, region_id, region_id),
    ).fetchall()
    for row in coverage_rows:
        scopes = scope_history.setdefault(str(row["source_id"]), [])
        description = str(row["coverage"])
        if description not in scopes:
            scopes.append(description)
    scopes = scope_history.setdefault(source_id, [])
    if coverage not in scopes:
        scopes.append(coverage)

    # Accepted reviews can reuse every stored row without creating a new source association.
    connection.execute(
        """
        INSERT INTO database_metadata (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (metadata_key, json.dumps(scope_history, sort_keys=True)),
    )
    return "Reviewed sources: " + "; ".join(
        f"{key} — {' | '.join(scopes)}" for key, scopes in sorted(scope_history.items())
    )


def _report(
    *,
    status: ImportStatus,
    fingerprint: str,
    row_count: int,
    accepted: int,
    inserted: int,
    placeholders: int,
    unclassified: int,
    issues: tuple[ImportIssue, ...],
) -> ImportReport:
    return ImportReport(
        status,
        fingerprint,
        row_count,
        accepted,
        inserted,
        placeholders,
        unclassified,
        len(
            {
                issue.source_row
                for issue in issues
                if issue.severity == "error" and issue.source_row is not None
            }
        ),
        issues,
        datetime.now(UTC),
    )


def validate_import(
    path: str | Path,
    *,
    region_id: str,
    classification_id: str,
    source_id: str,
    exchange_id: str | None = None,
    database: RegionDatabase | None = None,
) -> ImportReport:
    for label, value in (
        ("region_id", region_id),
        ("classification_id", classification_id),
        ("source_id", source_id),
    ):
        if not value.strip():
            raise ValueError(f"{label} must not be empty")
    raw, rows = _read_rows(path, fallback_exchange=exchange_id)
    accepted, parse_issues, _, _ = _validated_rows(rows)
    issues = list(parse_issues)
    if database is not None:
        accepted, database_issues = _read_only_database_conflicts(
            database,
            accepted,
            region_id=region_id,
            classification_id=classification_id,
        )
        issues.extend(database_issues)
    return _report(
        status="validated",
        fingerprint=sha256(raw).hexdigest(),
        row_count=len(rows),
        accepted=len(accepted),
        inserted=0,
        placeholders=sum(row.resolution_state == "placeholder" for row in accepted),
        unclassified=sum(row.classification_key == (None, None) for row in accepted),
        issues=tuple(issues),
    )


def import_reviewed_file(
    database: RegionDatabase,
    path: str | Path,
    *,
    region_id: str,
    classification_id: str,
    source_id: str,
    exchange_id: str | None,
    coverage: str,
    approval_reference: str,
) -> ImportReport:
    if not coverage.strip() or not approval_reference.strip():
        raise ValueError("Reviewed imports require coverage and approval reference metadata")
    raw, rows = _read_rows(path, fallback_exchange=exchange_id)
    fingerprint = sha256(raw).hexdigest()
    context = json.dumps(
        [region_id, classification_id, source_id, approval_reference, coverage, exchange_id],
        separators=(",", ":"),
    )
    stored_fingerprint = f"{fingerprint}:{sha256(context.encode()).hexdigest()}"
    started_at = datetime.now(UTC).isoformat()
    today = date.today().isoformat()
    candidate_rows, parse_issues, _, _ = _validated_rows(rows)
    issues = list(parse_issues)
    accepted_rows: list[_InputRow] = []
    inserted = 0
    database.initialize()

    with database.connect() as connection:
        source = connection.execute(
            "SELECT source_type, approval_reference FROM data_sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        if source is not None and (
            source["source_type"] != "local_file"
            or source["approval_reference"] not in (None, approval_reference)
        ):
            raise ValueError("Source ID conflicts with existing reviewed source metadata")

        candidate_rows, database_issues = _database_conflicts(
            connection,
            candidate_rows,
            region_id=region_id,
            classification_id=classification_id,
        )
        issues.extend(database_issues)

        prior_runs = connection.execute(
            """
            SELECT import_run_id, input_fingerprint, status, row_count, accepted_count
            FROM import_runs
            WHERE source_id = ? AND (input_fingerprint = ? OR input_fingerprint LIKE ?)
            ORDER BY import_run_id
            """,
            (source_id, fingerprint, f"{fingerprint}:%"),
        ).fetchall()
        existing_run = next(
            (run for run in prior_runs if run["input_fingerprint"] == stored_fingerprint), None
        )
        legacy_run = next(
            (run for run in prior_runs if run["input_fingerprint"] == fingerprint), None
        )
        if existing_run is None and legacy_run is not None:
            raise ValueError(
                "Legacy import replay has no persisted review/import context. "
                "Re-review the input and import with a new source ID; existing records "
                "and audit history will be preserved."
            )
        elif existing_run is None and prior_runs:
            raise ValueError("Import replay does not match its stored review context")

        if existing_run is not None:
            stored_issues = connection.execute(
                """
                SELECT source_row, entity_id, issue_kind, detail
                FROM import_issues WHERE import_run_id = ?
                ORDER BY import_issue_id
                """,
                (existing_run["import_run_id"],),
            ).fetchall()
            replay_issues = tuple(
                ImportIssue(
                    issue["source_row"],
                    issue["entity_id"],
                    issue["issue_kind"],
                    issue["detail"],
                    "warning" if issue["issue_kind"] == "duplicate_listing" else "error",
                )
                for issue in stored_issues
            )
            return _report(
                status=existing_run["status"],
                fingerprint=fingerprint,
                row_count=int(existing_run["row_count"]),
                accepted=int(existing_run["accepted_count"]),
                inserted=0,
                placeholders=sum(row.resolution_state == "placeholder" for row in candidate_rows),
                unclassified=sum(row.classification_key == (None, None) for row in candidate_rows),
                issues=replay_issues,
            )

        connection.execute(
            """
            INSERT INTO data_sources (
                source_id, source_type, description, coverage, authority,
                approval_reference, reviewed_at
            ) VALUES (?, 'local_file', ?, ?, 'reviewed_local', ?, ?)
            ON CONFLICT(source_id) DO NOTHING
            """,
            (source_id, Path(path).name, coverage, approval_reference, started_at),
        )

        partial = bool(issues)
        listing_primary_state: dict[str, bool] = {}
        for row in candidate_rows:
            savepoint = f"import_row_{row.source_row}"
            connection.execute(f"SAVEPOINT {savepoint}")
            primary = False
            try:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO regions (
                        region_id, name, coverage_state, coverage_description, coverage_as_of,
                        last_reviewed_at
                    ) VALUES (?, ?, 'unverified', ?, ?, ?)
                    """,
                    (
                        region_id,
                        "United States" if region_id == "US" else region_id,
                        coverage,
                        today,
                        started_at,
                    ),
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO classifications (
                        classification_id, region_id, name, source_id, approval_reference,
                        effective_from
                    ) VALUES (?, ?, ?, ?, ?, '1970-01-01')
                    """,
                    (
                        classification_id,
                        region_id,
                        classification_id,
                        source_id,
                        approval_reference,
                    ),
                )
                classification = connection.execute(
                    "SELECT region_id FROM classifications WHERE classification_id = ?",
                    (classification_id,),
                ).fetchone()
                if classification is None or classification["region_id"] != region_id:
                    raise ValueError("Classification ID already belongs to a different region")

                if row.sector_id and row.industry_id and row.sector_name and row.industry_name:
                    sector_id = f"{classification_id.lower()}-{row.sector_id}"
                    industry_id = f"{classification_id.lower()}-{row.industry_id}"
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO sectors (
                            sector_id, classification_id, name, effective_from
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            sector_id,
                            classification_id,
                            row.sector_name,
                            row.effective_from.isoformat(),
                        ),
                    )
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO industries (
                            industry_id, sector_id, classification_id, name, effective_from
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            industry_id,
                            sector_id,
                            classification_id,
                            row.industry_name,
                            row.effective_from.isoformat(),
                        ),
                    )
                else:
                    industry_id = None
                    sector_id = None

                classification_state = "classified" if industry_id else "unclassified"
                connection.execute(
                    """
                    INSERT INTO stocks (
                        instrument_id, company_id, name, resolution_state, classification_state
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(instrument_id) DO UPDATE SET
                        company_id = COALESCE(stocks.company_id, excluded.company_id),
                        resolution_state = CASE
                            WHEN excluded.resolution_state = 'identified' THEN 'identified'
                            ELSE stocks.resolution_state
                        END,
                        classification_state = CASE
                            WHEN stocks.classification_state = 'conflict' THEN 'conflict'
                            WHEN excluded.classification_state = 'classified' THEN 'classified'
                            ELSE stocks.classification_state
                        END
                    """,
                    (
                        row.instrument_id,
                        row.company_id,
                        row.name,
                        row.resolution_state,
                        classification_state,
                    ),
                )
                row_inserted = False
                if row.ticker is not None and row.exchange_id is not None:
                    primary = listing_primary_state.get(row.instrument_id)
                    if primary is None:
                        primary = (
                            connection.execute(
                                """
                                SELECT 1 FROM stock_listings
                                WHERE instrument_id = ? AND region_id = ? AND is_primary = 1
                                  AND COALESCE(effective_to, '9999-12-31') >= ?
                                  AND COALESCE(?, '9999-12-31') >= effective_from
                                LIMIT 1
                                """,
                                (
                                    row.instrument_id,
                                    region_id,
                                    row.effective_from.isoformat(),
                                    row.effective_to.isoformat() if row.effective_to else None,
                                ),
                            ).fetchone()
                            is None
                        )
                    listing_id = (
                        "listing-"
                        + sha256(
                            f"{region_id}|{row.exchange_id}|{row.ticker}|{row.effective_from}".encode()
                        ).hexdigest()[:20]
                    )
                    existing_listing = connection.execute(
                        """
                        SELECT instrument_id, region_id, exchange_id, symbol, provider_symbol,
                               currency, effective_from, effective_to
                        FROM stock_listings WHERE listing_id = ?
                        """,
                        (listing_id,),
                    ).fetchone()
                    if existing_listing is not None and not _listing_matches(
                        existing_listing, row, region_id=region_id
                    ):
                        raise sqlite3.IntegrityError(
                            f"Listing identity {row.exchange_id}:{row.ticker} conflicts "
                            "with a stored listing."
                        )
                    if existing_listing is None:
                        cursor = connection.execute(
                            """
                            INSERT OR IGNORE INTO stock_listings (
                                listing_id, instrument_id, region_id, exchange_id, symbol,
                                provider_symbol, currency, is_primary, effective_from, effective_to,
                                source_id, resolution_state
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'verified')
                            """,
                            (
                                listing_id,
                                row.instrument_id,
                                region_id,
                                row.exchange_id,
                                row.ticker,
                                row.provider_symbol,
                                row.currency,
                                int(primary),
                                row.effective_from.isoformat(),
                                row.effective_to.isoformat() if row.effective_to else None,
                                source_id,
                            ),
                        )
                        row_inserted = row_inserted or cursor.rowcount > 0
                if industry_id is not None:
                    cursor = connection.execute(
                        """
                        INSERT OR IGNORE INTO stock_memberships (
                            instrument_id, region_id, classification_id, industry_id,
                            effective_from, effective_to, source_id, approval_reference,
                            review_state
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'reviewed')
                        """,
                        (
                            row.instrument_id,
                            region_id,
                            classification_id,
                            industry_id,
                            row.effective_from.isoformat(),
                            row.effective_to.isoformat() if row.effective_to else None,
                            source_id,
                            approval_reference,
                        ),
                    )
                    row_inserted = row_inserted or cursor.rowcount > 0
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            except sqlite3.IntegrityError as error:
                connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                kind = (
                    "classification_conflict"
                    if "membership" in str(error).lower()
                    else "listing_conflict"
                )
                issues.append(
                    ImportIssue(row.source_row, row.instrument_id, kind, str(error), "error")
                )
                partial = True
                continue
            if row.ticker is not None and row.exchange_id is not None:
                listing_primary_state[row.instrument_id] = (
                    listing_primary_state.get(row.instrument_id, False) or primary or row_inserted
                )
            if row.resolution_state == "placeholder" or industry_id is None:
                partial = True
            if row_inserted:
                inserted += 1
            accepted_rows.append(row)

        status: ImportStatus = (
            "rejected"
            if not accepted_rows and issues
            else "committed_partial"
            if partial
            else "committed"
        )
        cursor = connection.execute(
            """
            INSERT INTO import_runs (
                source_id, input_fingerprint, started_at, completed_at, status,
                row_count, accepted_count, issue_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                stored_fingerprint,
                started_at,
                datetime.now(UTC).isoformat(),
                status,
                len(rows),
                len(accepted_rows),
                len(issues),
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return the import run identifier")
        run_id = cursor.lastrowid
        connection.executemany(
            """
            INSERT INTO import_issues (
                import_run_id, source_row, entity_id, issue_kind, detail
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (run_id, issue.source_row, issue.entity_id, issue.kind, issue.detail)
                for issue in issues
            ],
        )
        if accepted_rows:
            combined_coverage = _regional_coverage(
                connection, region_id=region_id, source_id=source_id, coverage=coverage
            )
            connection.execute(
                """
                UPDATE data_sources
                SET coverage = ?, authority = 'reviewed_local', reviewed_at = ?
                WHERE source_id = ?
                """,
                (coverage, started_at, source_id),
            )
            previous_coverage = connection.execute(
                "SELECT coverage_state FROM regions WHERE region_id = ?", (region_id,)
            ).fetchone()
            coverage_state = (
                "partial"
                if partial
                or (previous_coverage and previous_coverage["coverage_state"] == "partial")
                else "unverified"
            )
            connection.execute(
                """
                UPDATE regions
                SET coverage_state = ?, coverage_description = ?, coverage_as_of = ?,
                    last_reviewed_at = ?
                WHERE region_id = ?
                """,
                (coverage_state, combined_coverage, today, started_at, region_id),
            )
            connection.execute(
                "UPDATE database_metadata SET value = CAST(value AS INTEGER) + 1 "
                "WHERE key = 'revision'"
            )

    placeholders = sum(row.resolution_state == "placeholder" for row in accepted_rows)
    unclassified = sum(row.classification_key == (None, None) for row in accepted_rows)
    return _report(
        status=status,
        fingerprint=fingerprint,
        row_count=len(rows),
        accepted=len(accepted_rows),
        inserted=inserted,
        placeholders=placeholders,
        unclassified=unclassified,
        issues=tuple(issues),
    )
