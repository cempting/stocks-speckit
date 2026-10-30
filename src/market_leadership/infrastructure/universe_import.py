"""Validation and atomic ingestion of reviewed local universe files."""

import csv
import json
import re
import sqlite3
import unicodedata
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
    seen_listings: dict[tuple[str | None, str | None, str | None], _InputRow] = {}
    for row in rows:
        by_instrument.setdefault(row.instrument_id, []).append(row)
        if row.ticker:
            key = row.exchange_id, row.ticker, row.effective_from.isoformat()
            prior = seen_listings.get(key)
            if prior is not None:
                if (
                    prior.instrument_id == row.instrument_id
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
                elif prior.instrument_id != row.instrument_id:
                    issues.append(
                        ImportIssue(
                            row.source_row,
                            row.instrument_id,
                            "conflicting_listing",
                            f"Listing {row.exchange_id}:{row.ticker} has conflicting row values.",
                            "error",
                        )
                    )
            else:
                seen_listings[key] = row

    conflicting_ids: set[str] = set()
    for instrument_id, instrument_rows in by_instrument.items():
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
    duplicate_row_ids = {issue.source_row for issue in issues if issue.kind == "duplicate_listing"}
    valid: list[_InputRow] = []
    invalid_listing_rows = {
        issue.source_row for issue in issues if issue.kind == "conflicting_listing"
    }
    for row in rows:
        if (
            row.instrument_id not in conflicting_ids
            and row.source_row not in duplicate_row_ids | invalid_listing_rows
        ):
            valid.append(row)
    placeholders = sum(row.resolution_state == "placeholder" for row in valid)
    unclassified = sum(row.classification_key == (None, None) for row in valid)
    return valid, tuple(issues), placeholders, unclassified


def _report(
    *,
    status: ImportStatus,
    fingerprint: str,
    row_count: int,
    accepted: int,
    inserted: int,
    placeholders: int,
    unclassified: int,
    conflicts: int,
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
        conflicts,
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
) -> ImportReport:
    for label, value in (
        ("region_id", region_id),
        ("classification_id", classification_id),
        ("source_id", source_id),
    ):
        if not value.strip():
            raise ValueError(f"{label} must not be empty")
    raw, rows = _read_rows(path, fallback_exchange=exchange_id)
    accepted, issues, placeholders, unclassified = _validated_rows(rows)
    conflicts = sum(issue.severity == "error" for issue in issues)
    return _report(
        status="validated",
        fingerprint=sha256(raw).hexdigest(),
        row_count=len(rows),
        accepted=len(accepted),
        inserted=0,
        placeholders=placeholders,
        unclassified=unclassified,
        conflicts=conflicts,
        issues=issues,
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
    valid_rows, parse_issues, placeholders, unclassified = _validated_rows(rows)
    fingerprint = sha256(raw).hexdigest()
    started_at = datetime.now(UTC).isoformat()
    today = date.today().isoformat()
    issues = list(parse_issues)
    accepted_rows: list[_InputRow] = []
    accepted_by_instrument: dict[str, _InputRow] = {}
    inserted = 0
    partial = bool(parse_issues or placeholders or unclassified)
    database.initialize()

    with database.connect() as connection:
        existing_run = connection.execute(
            """
            SELECT status, accepted_count, issue_count FROM import_runs
            WHERE source_id = ? AND input_fingerprint = ?
            """,
            (source_id, fingerprint),
        ).fetchone()
        if existing_run is not None:
            return _report(
                status=existing_run["status"],
                fingerprint=fingerprint,
                row_count=len(rows),
                accepted=int(existing_run["accepted_count"]),
                inserted=0,
                placeholders=placeholders,
                unclassified=unclassified,
                conflicts=sum(issue.severity == "error" for issue in parse_issues),
                issues=tuple(parse_issues),
            )

        source = connection.execute(
            "SELECT source_type, approval_reference FROM data_sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        if source is not None and (
            source["source_type"] != "local_file"
            or source["approval_reference"] not in (None, approval_reference)
        ):
            raise ValueError("Source ID conflicts with existing reviewed source metadata")
        connection.execute(
            """
            INSERT INTO data_sources (
                source_id, source_type, description, coverage, authority,
                approval_reference, reviewed_at
            ) VALUES (?, 'local_file', ?, ?, 'reviewed_local', ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                coverage = excluded.coverage,
                authority = excluded.authority,
                reviewed_at = excluded.reviewed_at
            """,
            (source_id, Path(path).name, coverage, approval_reference, started_at),
        )
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
            UPDATE regions SET coverage_description = ?, coverage_as_of = ?, last_reviewed_at = ?
            WHERE region_id = ?
            """,
            (coverage, today, started_at, region_id),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO classifications (
                classification_id, region_id, name, source_id, approval_reference, effective_from
            ) VALUES (?, ?, ?, ?, ?, '1970-01-01')
            """,
            (classification_id, region_id, classification_id, source_id, approval_reference),
        )
        classification = connection.execute(
            "SELECT region_id FROM classifications WHERE classification_id = ?",
            (classification_id,),
        ).fetchone()
        if classification is None or classification["region_id"] != region_id:
            raise ValueError("Classification ID already belongs to a different region")

        listing_primary_state: dict[str, bool] = {}
        for row in valid_rows:
            if row.instrument_id in accepted_by_instrument:
                prior = accepted_by_instrument[row.instrument_id]
                if prior.name != row.name:
                    issues.append(
                        ImportIssue(
                            row.source_row,
                            row.instrument_id,
                            "identity_conflict",
                            "The same instrument has conflicting names; "
                            "the new row was quarantined.",
                            "error",
                        )
                    )
                    partial = True
                    continue
            accepted_by_instrument.setdefault(row.instrument_id, row)
            if row.sector_id and row.industry_id and row.sector_name and row.industry_name:
                sector_id = f"{classification_id.lower()}-{row.sector_id}"
                industry_id = f"{classification_id.lower()}-{row.industry_id}"
                conflict = connection.execute(
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
                if conflict is not None:
                    issues.append(
                        ImportIssue(
                            row.source_row,
                            row.instrument_id,
                            "classification_conflict",
                            "The imported membership disagrees with a reviewed local membership; "
                            "the original was preserved.",
                            "error",
                        )
                    )
                    partial = True
                    continue
                existing_industry = connection.execute(
                    """
                    SELECT i.sector_id, i.name, s.name AS sector_name
                    FROM industries i JOIN sectors s ON s.sector_id = i.sector_id
                    WHERE i.industry_id = ?
                    """,
                    (industry_id,),
                ).fetchone()
                if existing_industry is not None and (
                    existing_industry["name"] != row.industry_name
                    or existing_industry["sector_name"] != row.sector_name
                ):
                    issues.append(
                        ImportIssue(
                            row.source_row,
                            row.instrument_id,
                            "classification_conflict",
                            "The imported industry identity conflicts with the reviewed database; "
                            "the row was quarantined.",
                            "error",
                        )
                    )
                    partial = True
                    continue
                connection.execute(
                    """
                    INSERT OR IGNORE INTO sectors (
                        sector_id, classification_id, name, effective_from
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (sector_id, classification_id, row.sector_name, row.effective_from.isoformat()),
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

            existing_stock = connection.execute(
                "SELECT name FROM stocks WHERE instrument_id = ?", (row.instrument_id,)
            ).fetchone()
            if existing_stock is not None and existing_stock["name"] != row.name:
                issues.append(
                    ImportIssue(
                        row.source_row,
                        row.instrument_id,
                        "identity_conflict",
                        "The imported name disagrees with the stored security identity; "
                        "existing values were preserved.",
                        "error",
                    )
                )
                partial = True
                continue
            classification_state = "classified" if industry_id else "unclassified"
            connection.execute(
                """
                INSERT OR IGNORE INTO stocks (
                    instrument_id, company_id, name, resolution_state, classification_state
                ) VALUES (?, ?, ?, ?, ?)
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
                try:
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
                except sqlite3.IntegrityError as error:
                    issues.append(
                        ImportIssue(
                            row.source_row,
                            row.instrument_id,
                            "listing_conflict",
                            str(error),
                            "error",
                        )
                    )
                    partial = True
                    continue
                row_inserted = row_inserted or cursor.rowcount > 0
                listing_primary_state[row.instrument_id] = primary or row_inserted
            if industry_id is not None:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO stock_memberships (
                        instrument_id, region_id, classification_id, industry_id,
                        effective_from, effective_to, source_id, approval_reference, review_state
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
                fingerprint,
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
        previous_coverage = connection.execute(
            "SELECT coverage_state FROM regions WHERE region_id = ?", (region_id,)
        ).fetchone()
        coverage_state = (
            "partial"
            if partial or (previous_coverage and previous_coverage["coverage_state"] == "partial")
            else "unverified"
        )
        connection.execute(
            "UPDATE regions SET coverage_state = ? WHERE region_id = ?",
            (coverage_state, region_id),
        )
        connection.execute(
            "UPDATE database_metadata SET value = CAST(value AS INTEGER) + 1 WHERE key = 'revision'"
        )

    return _report(
        status=status,
        fingerprint=fingerprint,
        row_count=len(rows),
        accepted=len(accepted_rows),
        inserted=inserted,
        placeholders=placeholders,
        unclassified=unclassified,
        conflicts=sum(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )
