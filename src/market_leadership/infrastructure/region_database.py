"""SQLite persistence for reviewed regional security membership."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(".data/market-universe.sqlite")
SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS database_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT OR IGNORE INTO database_metadata (key, value) VALUES ('schema_version', '1');
INSERT OR IGNORE INTO database_metadata (key, value) VALUES ('revision', '0');

CREATE TABLE IF NOT EXISTS regions (
    region_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    coverage_state TEXT NOT NULL CHECK (coverage_state IN ('complete', 'partial', 'unverified')),
    coverage_description TEXT NOT NULL,
    coverage_as_of TEXT NOT NULL,
    last_reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS data_sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN ('local_file', 'live')),
    description TEXT NOT NULL,
    coverage TEXT,
    authority TEXT,
    approval_reference TEXT,
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS classifications (
    classification_id TEXT PRIMARY KEY,
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    name TEXT NOT NULL,
    version TEXT,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    approval_reference TEXT,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    UNIQUE (classification_id, region_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS sectors (
    sector_id TEXT PRIMARY KEY,
    classification_id TEXT NOT NULL REFERENCES classifications(classification_id),
    name TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS industries (
    industry_id TEXT PRIMARY KEY,
    sector_id TEXT NOT NULL REFERENCES sectors(sector_id),
    classification_id TEXT NOT NULL REFERENCES classifications(classification_id),
    name TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS stocks (
    instrument_id TEXT PRIMARY KEY,
    company_id TEXT,
    name TEXT NOT NULL,
    resolution_state TEXT NOT NULL CHECK (resolution_state IN ('identified', 'placeholder')),
    classification_state TEXT NOT NULL
        CHECK (classification_state IN ('classified', 'unclassified', 'conflict'))
);

CREATE TABLE IF NOT EXISTS stock_listings (
    listing_id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL REFERENCES stocks(instrument_id),
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    exchange_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    provider_symbol TEXT,
    currency TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    resolution_state TEXT NOT NULL CHECK (resolution_state IN ('verified', 'unverified')),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS stock_memberships (
    instrument_id TEXT NOT NULL REFERENCES stocks(instrument_id),
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    classification_id TEXT NOT NULL REFERENCES classifications(classification_id),
    industry_id TEXT NOT NULL REFERENCES industries(industry_id),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    approval_reference TEXT,
    review_state TEXT NOT NULL CHECK (review_state IN ('reviewed', 'conflict', 'unreviewed')),
    PRIMARY KEY (instrument_id, region_id, classification_id, industry_id, effective_from),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS entity_representations (
    representation_id TEXT PRIMARY KEY,
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    classification_id TEXT NOT NULL REFERENCES classifications(classification_id),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('sector', 'industry')),
    entity_id TEXT NOT NULL,
    listing_id TEXT NOT NULL REFERENCES stock_listings(listing_id),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS import_runs (
    import_run_id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    input_fingerprint TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('validated', 'committed', 'committed_partial', 'rejected')
    ),
    row_count INTEGER NOT NULL DEFAULT 0,
    accepted_count INTEGER NOT NULL DEFAULT 0,
    issue_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (source_id, input_fingerprint)
);

CREATE TABLE IF NOT EXISTS import_issues (
    import_issue_id INTEGER PRIMARY KEY,
    import_run_id INTEGER NOT NULL REFERENCES import_runs(import_run_id),
    source_row INTEGER,
    entity_id TEXT,
    issue_kind TEXT NOT NULL,
    detail TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_classifications_region
    ON classifications(region_id, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_sectors_classification
    ON sectors(classification_id, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_industries_sector
    ON industries(classification_id, sector_id, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_membership_industry
    ON stock_memberships(region_id, classification_id, industry_id, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_listing_instrument
    ON stock_listings(instrument_id, region_id, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_listing_symbol
    ON stock_listings(region_id, exchange_id, symbol, effective_from, effective_to);

CREATE TRIGGER IF NOT EXISTS prevent_overlapping_primary_listing
BEFORE INSERT ON stock_listings
WHEN NEW.is_primary = 1 AND EXISTS (
    SELECT 1 FROM stock_listings existing
    WHERE existing.instrument_id = NEW.instrument_id
      AND existing.region_id = NEW.region_id
      AND existing.is_primary = 1
      AND COALESCE(existing.effective_to, '9999-12-31') >= NEW.effective_from
      AND COALESCE(NEW.effective_to, '9999-12-31') >= existing.effective_from
)
BEGIN
    SELECT RAISE(ABORT, 'overlapping active primary listings are not allowed');
END;

CREATE TRIGGER IF NOT EXISTS prevent_overlapping_listing_identity
BEFORE INSERT ON stock_listings
WHEN EXISTS (
    SELECT 1 FROM stock_listings existing
    WHERE existing.region_id = NEW.region_id
      AND existing.exchange_id = NEW.exchange_id
      AND existing.symbol = NEW.symbol
      AND COALESCE(existing.effective_to, '9999-12-31') >= NEW.effective_from
      AND COALESCE(NEW.effective_to, '9999-12-31') >= existing.effective_from
)
BEGIN
    SELECT RAISE(ABORT, 'overlapping listing identities are not allowed');
END;

CREATE TRIGGER IF NOT EXISTS prevent_overlapping_industry_membership
BEFORE INSERT ON stock_memberships
WHEN NEW.review_state = 'reviewed' AND EXISTS (
    SELECT 1 FROM stock_memberships existing
    WHERE existing.instrument_id = NEW.instrument_id
      AND existing.region_id = NEW.region_id
      AND existing.classification_id = NEW.classification_id
      AND existing.review_state = 'reviewed'
      AND existing.industry_id != NEW.industry_id
      AND COALESCE(existing.effective_to, '9999-12-31') >= NEW.effective_from
      AND COALESCE(NEW.effective_to, '9999-12-31') >= existing.effective_from
)
BEGIN
    SELECT RAISE(ABORT, 'overlapping reviewed industry memberships are not allowed');
END;

CREATE TRIGGER IF NOT EXISTS prevent_overlapping_entity_representation
BEFORE INSERT ON entity_representations
WHEN EXISTS (
    SELECT 1 FROM entity_representations existing
    WHERE existing.region_id = NEW.region_id
      AND existing.classification_id = NEW.classification_id
      AND existing.entity_type = NEW.entity_type
      AND existing.entity_id = NEW.entity_id
      AND COALESCE(existing.effective_to, '9999-12-31') >= NEW.effective_from
      AND COALESCE(NEW.effective_to, '9999-12-31') >= existing.effective_from
)
BEGIN
    SELECT RAISE(ABORT, 'overlapping entity representations are not allowed');
END;
"""


@dataclass(frozen=True, slots=True)
class RegionRecord:
    region_id: str
    name: str
    status: str
    coverage_state: str
    coverage_description: str
    coverage_as_of: date
    last_reviewed_at: str | None


@dataclass(frozen=True, slots=True)
class SectorRecord:
    sector_id: str
    classification_id: str
    name: str


@dataclass(frozen=True, slots=True)
class IndustryRecord:
    industry_id: str
    sector_id: str
    classification_id: str
    name: str


@dataclass(frozen=True, slots=True)
class ListingRecord:
    listing_id: str
    exchange_id: str
    symbol: str
    provider_symbol: str | None
    currency: str
    is_primary: bool
    resolution_state: str


@dataclass(frozen=True, slots=True)
class EntityRepresentationRecord:
    representation_id: str
    entity_type: str
    entity_id: str
    listing_id: str
    symbol: str


@dataclass(frozen=True, slots=True)
class StockMembershipRecord:
    instrument_id: str
    company_id: str | None
    name: str
    resolution_state: str
    classification_state: str
    sector_id: str
    sector_name: str
    industry_id: str
    industry_name: str
    effective_from: date
    effective_to: date | None
    listings: tuple[ListingRecord, ...]

    @property
    def primary_listing(self) -> ListingRecord | None:
        return next((listing for listing in self.listings if listing.is_primary), None)


class RegionDatabase:
    def __init__(self, path: str | Path | None = None) -> None:
        configured = os.environ.get("MARKET_UNIVERSE_DATABASE_PATH")
        self.path = Path(path or configured or DEFAULT_DATABASE_PATH)

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.connect() as connection:
                connection.executescript(_SCHEMA)
                version = connection.execute(
                    "SELECT value FROM database_metadata WHERE key = 'schema_version'"
                ).fetchone()
                if version is None or int(version["value"]) != SCHEMA_VERSION:
                    raise ValueError("Unsupported regional universe schema version")
        except (OSError, sqlite3.Error) as error:
            raise ValueError(
                f"Could not initialize regional database {self.path}: {error}"
            ) from error

    def is_initialized(self) -> bool:
        if not self.path.is_file():
            return False
        try:
            with self.connect() as connection:
                result = connection.execute(
                    "SELECT value FROM database_metadata WHERE key = 'schema_version'"
                ).fetchone()
                return result is not None and int(result["value"]) == SCHEMA_VERSION
        except (OSError, sqlite3.Error, ValueError):
            return False

    def get_region(self, region_id: str) -> RegionRecord | None:
        if not self.is_initialized():
            return None
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM regions WHERE region_id = ?", (region_id,)
            ).fetchone()
        return _region_from_row(row) if row is not None else None

    def get_regions(self) -> tuple[RegionRecord, ...]:
        if not self.is_initialized():
            return ()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM regions WHERE status = 'active' ORDER BY region_id"
            ).fetchall()
        return tuple(_region_from_row(row) for row in rows)

    def get_classification_id(self, region_id: str) -> str | None:
        if not self.is_initialized():
            return None
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT c.classification_id
                FROM classifications c
                JOIN regions r ON r.region_id = c.region_id
                WHERE r.region_id = ? AND r.status = 'active'
                ORDER BY c.effective_from DESC, c.classification_id
                LIMIT 1
                """,
                (region_id,),
            ).fetchone()
        return str(row["classification_id"]) if row else None

    def get_sectors(
        self, region_id: str, classification_id: str, *, as_of: date
    ) -> tuple[SectorRecord, ...]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT s.sector_id, s.classification_id, s.name
                FROM sectors s
                JOIN classifications c ON c.classification_id = s.classification_id
                WHERE c.region_id = ? AND c.classification_id = ?
                  AND s.effective_from <= ? AND (s.effective_to IS NULL OR s.effective_to >= ?)
                  AND c.effective_from <= ? AND (c.effective_to IS NULL OR c.effective_to >= ?)
                ORDER BY s.name, s.sector_id
                """,
                (
                    region_id,
                    classification_id,
                    as_of.isoformat(),
                    as_of.isoformat(),
                    as_of.isoformat(),
                    as_of.isoformat(),
                ),
            ).fetchall()
        return tuple(SectorRecord(**dict(row)) for row in rows)

    def get_industries(
        self,
        region_id: str,
        classification_id: str,
        sector_id: str,
        *,
        as_of: date,
    ) -> tuple[IndustryRecord, ...]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT i.industry_id, i.sector_id, i.classification_id, i.name
                FROM industries i
                JOIN sectors s ON s.sector_id = i.sector_id
                JOIN classifications c ON c.classification_id = i.classification_id
                WHERE c.region_id = ? AND c.classification_id = ? AND s.sector_id = ?
                  AND i.effective_from <= ? AND (i.effective_to IS NULL OR i.effective_to >= ?)
                  AND s.effective_from <= ? AND (s.effective_to IS NULL OR s.effective_to >= ?)
                  AND c.effective_from <= ? AND (c.effective_to IS NULL OR c.effective_to >= ?)
                ORDER BY i.name, i.industry_id
                """,
                (
                    region_id,
                    classification_id,
                    sector_id,
                    as_of.isoformat(),
                    as_of.isoformat(),
                    as_of.isoformat(),
                    as_of.isoformat(),
                    as_of.isoformat(),
                    as_of.isoformat(),
                ),
            ).fetchall()
        return tuple(IndustryRecord(**dict(row)) for row in rows)

    def get_industry_members(
        self,
        region_id: str,
        classification_id: str,
        industry_id: str,
        *,
        as_of: date,
    ) -> tuple[StockMembershipRecord, ...]:
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        day = as_of.isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT
                    st.instrument_id, st.company_id, st.name, st.resolution_state,
                    st.classification_state, i.sector_id, s.name AS sector_name,
                    i.industry_id, i.name AS industry_name,
                    m.effective_from, m.effective_to
                FROM stock_memberships m
                JOIN stocks st ON st.instrument_id = m.instrument_id
                JOIN industries i ON i.industry_id = m.industry_id
                JOIN sectors s ON s.sector_id = i.sector_id
                JOIN classifications c ON c.classification_id = m.classification_id
                WHERE m.region_id = ? AND c.region_id = ?
                  AND m.classification_id = ? AND m.industry_id = ?
                  AND m.review_state = 'reviewed'
                  AND m.effective_from <= ? AND (m.effective_to IS NULL OR m.effective_to >= ?)
                  AND i.effective_from <= ? AND (i.effective_to IS NULL OR i.effective_to >= ?)
                  AND s.effective_from <= ? AND (s.effective_to IS NULL OR s.effective_to >= ?)
                ORDER BY st.instrument_id
                """,
                (
                    region_id,
                    region_id,
                    classification_id,
                    industry_id,
                    day,
                    day,
                    day,
                    day,
                    day,
                    day,
                ),
            ).fetchall()
            members: list[StockMembershipRecord] = []
            for row in rows:
                listing_rows = connection.execute(
                    """
                    SELECT listing_id, exchange_id, symbol, provider_symbol, currency,
                           is_primary, resolution_state
                    FROM stock_listings
                    WHERE instrument_id = ? AND region_id = ? AND resolution_state = 'verified'
                      AND effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)
                    ORDER BY is_primary DESC, exchange_id, symbol
                    """,
                    (row["instrument_id"], region_id, day, day),
                ).fetchall()
                members.append(
                    StockMembershipRecord(
                        instrument_id=str(row["instrument_id"]),
                        company_id=row["company_id"],
                        name=str(row["name"]),
                        resolution_state=str(row["resolution_state"]),
                        classification_state=str(row["classification_state"]),
                        sector_id=str(row["sector_id"]),
                        sector_name=str(row["sector_name"]),
                        industry_id=str(row["industry_id"]),
                        industry_name=str(row["industry_name"]),
                        effective_from=date.fromisoformat(str(row["effective_from"])),
                        effective_to=(
                            date.fromisoformat(str(row["effective_to"]))
                            if row["effective_to"] is not None
                            else None
                        ),
                        listings=tuple(
                            ListingRecord(
                                listing_id=str(listing["listing_id"]),
                                exchange_id=str(listing["exchange_id"]),
                                symbol=str(listing["symbol"]),
                                provider_symbol=listing["provider_symbol"],
                                currency=str(listing["currency"]),
                                is_primary=bool(listing["is_primary"]),
                                resolution_state=str(listing["resolution_state"]),
                            )
                            for listing in listing_rows
                        ),
                    )
                )
        return tuple(members)

    def get_revision(self) -> str:
        if not self.is_initialized():
            return "uninitialized"
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value FROM database_metadata WHERE key = 'revision'"
            ).fetchone()
        return str(row["value"]) if row else "0"

    def get_entity_representations(
        self,
        region_id: str,
        classification_id: str,
        entity_type: str,
        *,
        as_of: date,
    ) -> tuple[EntityRepresentationRecord, ...]:
        if entity_type not in ("sector", "industry"):
            raise ValueError("Entity representation type must be sector or industry")
        day = as_of.isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT r.representation_id, r.entity_type, r.entity_id, r.listing_id, l.symbol
                FROM entity_representations r
                JOIN stock_listings l ON l.listing_id = r.listing_id
                JOIN classifications c ON c.classification_id = r.classification_id
                WHERE r.region_id = ? AND c.region_id = ? AND r.classification_id = ?
                  AND r.entity_type = ? AND l.resolution_state = 'verified'
                  AND r.effective_from <= ? AND (r.effective_to IS NULL OR r.effective_to >= ?)
                  AND l.effective_from <= ? AND (l.effective_to IS NULL OR l.effective_to >= ?)
                ORDER BY r.entity_id
                """,
                (
                    region_id,
                    region_id,
                    classification_id,
                    entity_type,
                    day,
                    day,
                    day,
                    day,
                ),
            ).fetchall()
        return tuple(EntityRepresentationRecord(**dict(row)) for row in rows)

    def add_entity_representation(
        self,
        *,
        region_id: str,
        classification_id: str,
        entity_type: str,
        entity_id: str,
        exchange_id: str,
        symbol: str,
        source_id: str,
        approval_reference: str,
        effective_from: date,
        effective_to: date | None = None,
    ) -> str:
        if entity_type not in ("sector", "industry"):
            raise ValueError("Entity representation type must be sector or industry")
        if effective_to is not None and effective_to < effective_from:
            raise ValueError("Representation effective dates are reversed")
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        if not approval_reference.strip():
            raise ValueError("Representation approval reference must not be empty")
        identifier = (
            "representation-"
            + sha256(
                (
                    f"{region_id}|{classification_id}|{entity_type}|{entity_id}|"
                    f"{exchange_id}|{symbol}|{source_id}|{approval_reference}|"
                    f"{effective_from.isoformat()}|"
                    f"{effective_to.isoformat() if effective_to else ''}"
                ).encode()
            ).hexdigest()[:20]
        )
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT 1 FROM entity_representations WHERE representation_id = ?",
                (identifier,),
            ).fetchone()
            if existing is not None:
                return identifier
            entity_table = "sectors" if entity_type == "sector" else "industries"
            entity_column = "sector_id" if entity_type == "sector" else "industry_id"
            entity = connection.execute(
                f"""
                SELECT 1
                FROM {entity_table} e
                JOIN classifications c ON c.classification_id = e.classification_id
                WHERE e.classification_id = ? AND c.region_id = ? AND e.{entity_column} = ?
                """,
                (classification_id, region_id, entity_id),
            ).fetchone()
            if entity is None:
                raise ValueError(
                    f"Reviewed {entity_type} {entity_id!r} is not in this classification"
                )
            source = connection.execute(
                """
                SELECT source_type, approval_reference
                FROM data_sources WHERE source_id = ?
                """,
                (source_id,),
            ).fetchone()
            if (
                source is None
                or source["source_type"] != "local_file"
                or source["approval_reference"] != approval_reference
            ):
                raise ValueError(
                    "Representation source and approval reference must match "
                    "a reviewed local import"
                )
            listing = connection.execute(
                """
                SELECT listing_id
                FROM stock_listings
                WHERE region_id = ? AND exchange_id = ? AND symbol = ?
                  AND is_primary = 1 AND resolution_state = 'verified'
                  AND effective_from <= ?
                  AND (effective_to IS NULL OR effective_to >= COALESCE(?, '9999-12-31'))
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                (
                    region_id,
                    exchange_id,
                    symbol,
                    effective_from.isoformat(),
                    effective_to.isoformat() if effective_to else None,
                ),
            ).fetchone()
            if listing is None:
                raise ValueError(f"No verified primary listing found for {exchange_id}:{symbol}")
            try:
                connection.execute(
                    """
                    INSERT INTO entity_representations (
                        representation_id, region_id, classification_id, entity_type,
                        entity_id, listing_id, effective_from, effective_to, source_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        identifier,
                        region_id,
                        classification_id,
                        entity_type,
                        entity_id,
                        listing["listing_id"],
                        effective_from.isoformat(),
                        effective_to.isoformat() if effective_to else None,
                        source_id,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError(f"Could not add entity representation: {error}") from error
            connection.execute(
                "UPDATE database_metadata SET value = CAST(value AS INTEGER) + 1 "
                "WHERE key = 'revision'"
            )
        return identifier


def _region_from_row(row: sqlite3.Row) -> RegionRecord:
    return RegionRecord(
        region_id=str(row["region_id"]),
        name=str(row["name"]),
        status=str(row["status"]),
        coverage_state=str(row["coverage_state"]),
        coverage_description=str(row["coverage_description"]),
        coverage_as_of=date.fromisoformat(str(row["coverage_as_of"])),
        last_reviewed_at=row["last_reviewed_at"],
    )
