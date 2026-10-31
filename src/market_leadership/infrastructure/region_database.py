"""SQLite persistence for reviewed regional security membership."""

import json
import logging
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from market_leadership.domain.industry_representations import (
    BasketConstituent,
    ReviewedRepresentation,
    validate_weights,
)
from market_leadership.domain.local_etf_evidence import (
    CollectionRun,
    Evidence,
    Inventory,
    ResearchSnapshot,
    ReviewDecision,
    compare_observations,
    review_evidence,
    selected_review,
    support_reasons,
    validate_review,
)

DEFAULT_DATABASE_PATH = Path(".data/market-universe.sqlite")
SCHEMA_VERSION = 3
_LOGGER = logging.getLogger(__name__)

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

_REPRESENTATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_baskets (
    representation_id TEXT PRIMARY KEY,
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    classification_id TEXT NOT NULL REFERENCES classifications(classification_id),
    entity_id TEXT NOT NULL REFERENCES industries(industry_id),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    source_id TEXT NOT NULL REFERENCES data_sources(source_id),
    approval_reference TEXT NOT NULL CHECK (length(trim(approval_reference)) > 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    review_state TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (review_state IN ('unreviewed', 'reviewed')),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE TABLE IF NOT EXISTS basket_constituents (
    representation_id TEXT NOT NULL REFERENCES stock_baskets(representation_id),
    listing_id TEXT NOT NULL REFERENCES stock_listings(listing_id),
    weight TEXT NOT NULL CHECK (CAST(weight AS REAL) > 0),
    PRIMARY KEY (representation_id, listing_id)
);
CREATE INDEX IF NOT EXISTS idx_baskets_scope
    ON stock_baskets(region_id, classification_id, entity_id, effective_from, effective_to);
CREATE TRIGGER IF NOT EXISTS prevent_overlapping_baskets
BEFORE INSERT ON stock_baskets
WHEN EXISTS (
    SELECT 1 FROM stock_baskets b
    WHERE b.region_id = NEW.region_id AND b.classification_id = NEW.classification_id
      AND b.entity_id = NEW.entity_id
      AND COALESCE(b.effective_to, '9999-12-31') >= NEW.effective_from
      AND COALESCE(NEW.effective_to, '9999-12-31') >= b.effective_from
)
BEGIN
    SELECT RAISE(ABORT, 'overlapping stock baskets are not allowed');
END;
"""


_ETF_EVIDENCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS etf_collection_runs (
    run_id TEXT PRIMARY KEY,
    event_order INTEGER NOT NULL UNIQUE,
    observed_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('complete', 'partial', 'failed')),
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
CREATE TABLE IF NOT EXISTS etf_mapping_evidence (
    evidence_id TEXT PRIMARY KEY,
    candidate_id TEXT,
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
CREATE INDEX IF NOT EXISTS idx_etf_evidence_candidate ON etf_mapping_evidence(candidate_id);
CREATE TABLE IF NOT EXISTS etf_collection_evidence (
    run_id TEXT NOT NULL REFERENCES etf_collection_runs(run_id),
    evidence_id TEXT NOT NULL REFERENCES etf_mapping_evidence(evidence_id),
    PRIMARY KEY (run_id, evidence_id)
);
CREATE TABLE IF NOT EXISTS etf_candidate_reviews (
    event_order INTEGER PRIMARY KEY,
    review_id TEXT NOT NULL UNIQUE,
    candidate_id TEXT NOT NULL,
    region_id TEXT NOT NULL REFERENCES regions(region_id),
    classification_id TEXT NOT NULL REFERENCES classifications(classification_id),
    entity_id TEXT NOT NULL REFERENCES industries(industry_id),
    as_of TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES etf_collection_runs(run_id),
    decision TEXT NOT NULL CHECK (decision IN ('accept', 'reject')),
    reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
    review_reference TEXT NOT NULL CHECK (length(trim(review_reference)) > 0),
    payload TEXT NOT NULL CHECK (json_valid(payload))
);
CREATE TABLE IF NOT EXISTS etf_review_evidence (
    review_id TEXT NOT NULL REFERENCES etf_candidate_reviews(review_id),
    evidence_id TEXT NOT NULL REFERENCES etf_mapping_evidence(evidence_id),
    PRIMARY KEY (review_id, evidence_id)
);
CREATE TABLE IF NOT EXISTS etf_representation_provenance (
    representation_id TEXT NOT NULL REFERENCES entity_representations(representation_id),
    review_id TEXT NOT NULL REFERENCES etf_candidate_reviews(review_id),
    approval_run_id TEXT NOT NULL REFERENCES etf_collection_runs(run_id),
    PRIMARY KEY (representation_id, review_id)
);
"""


def _execute_schema(connection: sqlite3.Connection, script: str) -> None:
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        raise ValueError("Incomplete regional database schema statement")


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
    node_type: str = "industry"
    parent_industry_id: str | None = None


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
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE name='database_metadata'"
                ).fetchone():
                    version = connection.execute(
                        "SELECT value FROM database_metadata WHERE key = 'schema_version'"
                    ).fetchone()
                    if version is None or version["value"] not in ("1", "2", "3"):
                        raise ValueError("Unsupported regional universe schema version")
                _execute_schema(connection, _SCHEMA)
                columns = {
                    row["name"] for row in connection.execute("PRAGMA table_info(industries)")
                }
                if "node_type" not in columns:
                    connection.execute(
                        "ALTER TABLE industries ADD COLUMN node_type TEXT NOT NULL "
                        "DEFAULT 'industry' CHECK (node_type IN ('industry', 'sub_industry'))"
                    )
                    connection.execute(
                        "ALTER TABLE industries ADD COLUMN parent_industry_id TEXT "
                        "REFERENCES industries(industry_id)"
                    )
                if "source_id" not in columns:
                    connection.execute(
                        "ALTER TABLE industries ADD COLUMN source_id TEXT "
                        "REFERENCES data_sources(source_id)"
                    )
                    connection.execute("ALTER TABLE industries ADD COLUMN approval_reference TEXT")
                representation_columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(entity_representations)")
                }
                if "approval_reference" not in representation_columns:
                    connection.execute(
                        "ALTER TABLE entity_representations ADD COLUMN approval_reference TEXT"
                    )
                    connection.execute(
                        "UPDATE entity_representations SET approval_reference = "
                        "(SELECT approval_reference FROM data_sources s "
                        "WHERE s.source_id = entity_representations.source_id)"
                    )
                _execute_schema(connection, _REPRESENTATION_SCHEMA)
                _execute_schema(connection, _ETF_EVIDENCE_SCHEMA)
                connection.execute(
                    "UPDATE database_metadata SET value = ? WHERE key = 'schema_version'",
                    (str(SCHEMA_VERSION),),
                )
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

    def save_etf_collection(self, inventory: Inventory) -> None:
        if not self.is_initialized():
            raise ValueError(f"Local ETF research requires an initialized database: {self.path}")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            order = connection.execute(
                "SELECT COALESCE(MAX(event_order), 0) + 1 FROM etf_collection_runs"
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO etf_collection_runs VALUES (?, ?, ?, ?, ?)",
                (
                    inventory.run.run_id,
                    order,
                    inventory.run.observed_at,
                    inventory.run.status,
                    json.dumps(asdict(inventory.run)),
                ),
            )
            for item in inventory.evidence:
                connection.execute(
                    "INSERT OR IGNORE INTO etf_mapping_evidence VALUES (?, ?, ?)",
                    (item.evidence_id, item.candidate_id, json.dumps(asdict(item))),
                )
                connection.execute(
                    "INSERT INTO etf_collection_evidence VALUES (?, ?)",
                    (inventory.run.run_id, item.evidence_id),
                )

    def get_etf_inventory(self, run_id: str | None = None) -> Inventory:
        if not self.is_initialized():
            raise ValueError(f"Local ETF research requires an initialized database: {self.path}")
        with self.connect() as connection:
            inventories = _etf_inventories(connection)
        inventory = (
            next(
                (item for item in inventories if item.run.run_id == run_id),
                None,
            )
            if run_id is not None
            else next(iter(reversed(inventories)), None)
        )
        if inventory is None:
            raise ValueError("No persisted ETF collection matches the requested run")
        prior = inventories[: inventories.index(inventory)]
        from dataclasses import replace

        return replace(inventory, changes=compare_observations(inventory, prior))

    def get_etf_snapshot(self) -> ResearchSnapshot:
        if not self.is_initialized():
            raise ValueError(f"Local ETF research requires an initialized database: {self.path}")
        with self.connect() as connection:
            return _etf_snapshot(connection)

    def validate_etf_scope(self, region_id: str, classification_id: str, as_of: date) -> None:
        if not self.is_initialized():
            raise ValueError(f"Local ETF research requires an initialized database: {self.path}")
        with self.connect() as connection:
            row = connection.execute(
                "SELECT c.* FROM classifications c JOIN regions r ON r.region_id=c.region_id "
                "WHERE c.region_id=? AND c.classification_id=? AND r.status='active'",
                (region_id, classification_id),
            ).fetchone()
            if row is None or not _covers(row, as_of, as_of):
                raise ValueError("Invalid or inactive reviewed ETF research scope")
            _validate_source(connection, row["source_id"], row["approval_reference"] or "")

    def add_etf_candidate_review(self, review: ReviewDecision) -> ReviewDecision:
        if not self.is_initialized():
            raise ValueError(f"Local ETF research requires an initialized database: {self.path}")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            as_of = date.fromisoformat(review.as_of)
            _validate_entity(
                connection,
                review.region_id,
                review.classification_id,
                "industry",
                review.entity_id,
                as_of,
                as_of,
            )
            snapshot = _etf_snapshot(connection)
            evidence = review_evidence(review, snapshot)
            node = connection.execute(
                "SELECT node_type FROM industries WHERE industry_id=?",
                (review.entity_id,),
            ).fetchone()
            validate_review(review, evidence, node_level=node["node_type"])
            order = connection.execute(
                "SELECT COALESCE(MAX(event_order), 0)+1 FROM etf_candidate_reviews"
            ).fetchone()[0]
            from dataclasses import replace

            stored = replace(review, event_order=order)
            connection.execute(
                "INSERT INTO etf_candidate_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    order,
                    stored.review_id,
                    stored.candidate_id,
                    stored.region_id,
                    stored.classification_id,
                    stored.entity_id,
                    stored.as_of,
                    stored.run_id,
                    stored.decision,
                    stored.reason,
                    stored.review_reference,
                    json.dumps(asdict(stored)),
                ),
            )
            for evidence_id in stored.evidence_ids:
                connection.execute(
                    "INSERT INTO etf_review_evidence VALUES (?, ?)",
                    (stored.review_id, evidence_id),
                )
        return stored

    def get_regions(self) -> tuple[RegionRecord, ...]:
        if not self.is_initialized():
            return ()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM regions WHERE status = 'active' ORDER BY region_id"
            ).fetchall()
        return tuple(_region_from_row(row) for row in rows)

    def get_classification_id(self, region_id: str, *, as_of: date | None = None) -> str | None:
        if not self.is_initialized():
            return None
        day = (as_of or date.today()).isoformat()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT c.classification_id
                FROM classifications c
                JOIN regions r ON r.region_id = c.region_id
                WHERE r.region_id = ? AND r.status = 'active'
                  AND c.effective_from <= ?
                  AND (c.effective_to IS NULL OR c.effective_to >= ?)
                ORDER BY c.effective_from DESC, c.classification_id
                LIMIT 1
                """,
                (region_id, day, day),
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
                SELECT i.industry_id, i.sector_id, i.classification_id, i.name,
                       i.node_type, i.parent_industry_id
                FROM industries i
                JOIN sectors s ON s.sector_id = i.sector_id
                JOIN classifications c ON c.classification_id = i.classification_id
                WHERE c.region_id = ? AND c.classification_id = ? AND s.sector_id = ?
                  AND i.effective_from <= ? AND (i.effective_to IS NULL OR i.effective_to >= ?)
                  AND s.effective_from <= ? AND (s.effective_to IS NULL OR s.effective_to >= ?)
                  AND c.effective_from <= ? AND (c.effective_to IS NULL OR c.effective_to >= ?)
                  AND (i.parent_industry_id IS NULL OR EXISTS (
                    SELECT 1 FROM industries parent WHERE parent.industry_id = i.parent_industry_id
                      AND parent.classification_id = i.classification_id
                      AND parent.sector_id = i.sector_id AND parent.node_type = 'industry'
                      AND parent.effective_from <= ?
                      AND (parent.effective_to IS NULL OR parent.effective_to >= ?)
                  ))
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
                SELECT
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
                  AND c.effective_from <= ? AND (c.effective_to IS NULL OR c.effective_to >= ?)
                ORDER BY st.instrument_id, m.effective_from DESC
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
                    day,
                    day,
                ),
            ).fetchall()
            members: list[StockMembershipRecord] = []
            seen_instruments: set[str] = set()
            for row in rows:
                instrument_id = str(row["instrument_id"])
                if instrument_id in seen_instruments:
                    continue
                seen_instruments.add(instrument_id)
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
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        day = as_of.isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT r.representation_id, r.entity_type, r.entity_id, r.listing_id,
                       r.source_id, COALESCE(r.approval_reference, s.approval_reference) AS approval
                FROM entity_representations r
                JOIN data_sources s ON s.source_id = r.source_id
                WHERE r.region_id = ? AND r.classification_id = ? AND r.entity_type = ?
                  AND r.effective_from <= ? AND (r.effective_to IS NULL OR r.effective_to >= ?)
                ORDER BY r.entity_id
                """,
                (region_id, classification_id, entity_type, day, day),
            ).fetchall()
            valid_rows: list[EntityRepresentationRecord] = []
            for row in rows:
                try:
                    _validate_entity(
                        connection,
                        region_id,
                        classification_id,
                        entity_type,
                        str(row["entity_id"]),
                        as_of,
                        as_of,
                    )
                    _validate_source(connection, row["source_id"], row["approval"] or "")
                    listing = _validate_listing(
                        connection,
                        row["listing_id"],
                        region_id,
                        as_of,
                        as_of,
                    )
                except ValueError as error:
                    _LOGGER.warning(
                        "Excluded invalid representation %s: %s",
                        row["representation_id"],
                        error,
                    )
                    continue
                valid_rows.append(
                    EntityRepresentationRecord(
                        row["representation_id"],
                        row["entity_type"],
                        row["entity_id"],
                        row["listing_id"],
                        str(listing["provider_symbol"] or listing["symbol"]),
                    )
                )
        return tuple(valid_rows)

    def get_verified_listings(self, region_id: str, *, as_of: date) -> tuple[ListingRecord, ...]:
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        region = self.get_region(region_id)
        if region is None or region.status != "active":
            raise ValueError(f"No active reviewed region: {region_id}")
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT listing_id FROM stock_listings WHERE region_id = ? "
                "AND resolution_state = 'verified' AND effective_from <= ? "
                "AND (effective_to IS NULL OR effective_to >= ?) ORDER BY symbol, listing_id",
                (region_id, as_of.isoformat(), as_of.isoformat()),
            ).fetchall()
            results: list[ListingRecord] = []
            for row in rows:
                try:
                    listing = _validate_listing(
                        connection,
                        row["listing_id"],
                        region_id,
                        as_of,
                        as_of,
                    )
                except ValueError as error:
                    _LOGGER.warning("Excluded invalid listing %s: %s", row["listing_id"], error)
                    continue
                results.append(
                    ListingRecord(
                        listing["listing_id"],
                        listing["exchange_id"],
                        listing["symbol"],
                        listing["provider_symbol"],
                        listing["currency"],
                        bool(listing["is_primary"]),
                        listing["resolution_state"],
                    )
                )
        return tuple(results)

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
        candidate_review_id: str | None = None,
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
            connection.execute("BEGIN IMMEDIATE")
            _validate_entity(
                connection,
                region_id,
                classification_id,
                entity_type,
                entity_id,
                effective_from,
                effective_to,
            )
            _validate_source(connection, source_id, approval_reference)
            listing = connection.execute(
                """
                SELECT l.listing_id
                FROM stock_listings l
                JOIN stocks st ON st.instrument_id = l.instrument_id
                JOIN data_sources s ON s.source_id = l.source_id
                WHERE l.region_id = ? AND l.exchange_id = ? AND l.symbol = ?
                  AND l.is_primary = 1 AND l.resolution_state = 'verified'
                  AND st.resolution_state = 'identified'
                  AND s.reviewed_at IS NOT NULL AND length(trim(s.approval_reference)) > 0
                  AND l.effective_from <= ?
                  AND (l.effective_to IS NULL OR l.effective_to >= COALESCE(?, '9999-12-31'))
                ORDER BY l.effective_from DESC
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
            reviewed_listing = _validate_listing(
                connection,
                listing["listing_id"],
                region_id,
                effective_from,
                effective_to,
            )
            approval_run_id = None
            if candidate_review_id is not None:
                if entity_type != "industry":
                    raise ValueError("Candidate review must target an exact industry/sub-industry")
                approval_run_id = _validate_etf_candidate_approval(
                    connection,
                    candidate_review_id,
                    region_id,
                    classification_id,
                    entity_id,
                    reviewed_listing,
                )
            existing = connection.execute(
                "SELECT 1 FROM entity_representations WHERE representation_id = ?",
                (identifier,),
            ).fetchone()
            if existing is not None:
                if candidate_review_id is not None and approval_run_id is not None:
                    _link_etf_provenance(
                        connection,
                        identifier,
                        candidate_review_id,
                        approval_run_id,
                    )
                return identifier
            try:
                connection.execute(
                    """
                    INSERT INTO entity_representations (
                        representation_id, region_id, classification_id, entity_type,
                        entity_id, listing_id, effective_from, effective_to, source_id,
                        approval_reference
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        approval_reference,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError(f"Could not add entity representation: {error}") from error
            if candidate_review_id is not None and approval_run_id is not None:
                _link_etf_provenance(connection, identifier, candidate_review_id, approval_run_id)
            connection.execute(
                "UPDATE database_metadata SET value = CAST(value AS INTEGER) + 1 "
                "WHERE key = 'revision'"
            )
        return identifier

    def add_review_node(
        self,
        *,
        region_id: str,
        classification_id: str,
        entity_id: str,
        name: str,
        sector_id: str,
        source_id: str,
        approval_reference: str,
        effective_from: date,
        effective_to: date | None = None,
        parent_industry_id: str | None = None,
    ) -> None:
        """Register reviewed hierarchy nodes even when no stock membership exists."""
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        if not entity_id.strip() or not name.strip():
            raise ValueError("Node identity and name are required")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            _validate_source(connection, source_id, approval_reference)
            _validate_entity(
                connection,
                region_id,
                classification_id,
                "sector",
                sector_id,
                effective_from,
                effective_to,
            )
            if parent_industry_id:
                _validate_entity(
                    connection,
                    region_id,
                    classification_id,
                    "industry",
                    parent_industry_id,
                    effective_from,
                    effective_to,
                )
                parent = connection.execute(
                    "SELECT sector_id, node_type FROM industries WHERE industry_id = ?",
                    (parent_industry_id,),
                ).fetchone()
                if parent["sector_id"] != sector_id or parent["node_type"] != "industry":
                    raise ValueError("Sub-industry parent must be an industry in the same sector")
            try:
                connection.execute(
                    "INSERT INTO industries (industry_id, sector_id, classification_id, name, "
                    "effective_from, effective_to, node_type, parent_industry_id, "
                    "source_id, approval_reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        entity_id,
                        sector_id,
                        classification_id,
                        name,
                        effective_from.isoformat(),
                        effective_to.isoformat() if effective_to else None,
                        "sub_industry" if parent_industry_id else "industry",
                        parent_industry_id,
                        source_id,
                        approval_reference,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError(f"Could not register reviewed node: {error}") from error
            _bump_revision(connection)

    def add_stock_basket(
        self,
        *,
        region_id: str,
        classification_id: str,
        entity_id: str,
        name: str,
        source_id: str,
        approval_reference: str,
        effective_from: date,
        constituents: tuple[tuple[str, Decimal], ...],
        effective_to: date | None = None,
    ) -> str:
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        if not name.strip():
            raise ValueError("Basket name is required")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            _validate_entity(
                connection,
                region_id,
                classification_id,
                "industry",
                entity_id,
                effective_from,
                effective_to,
            )
            _validate_source(connection, source_id, approval_reference)
            members: list[BasketConstituent] = []
            for listing_id, weight in constituents:
                listing = _validate_listing(
                    connection,
                    listing_id,
                    region_id,
                    effective_from,
                    effective_to,
                )
                members.append(
                    BasketConstituent(
                        listing_id,
                        str(listing["provider_symbol"] or listing["symbol"]),
                        weight,
                    )
                )
            validate_weights(tuple(members))
            overlapping_etfs = connection.execute(
                "SELECT r.effective_from, r.effective_to, l.effective_from AS listing_from "
                "FROM entity_representations r "
                "JOIN stock_listings l ON l.listing_id = r.listing_id "
                "WHERE r.region_id = ? AND r.classification_id = ? AND r.entity_type = 'industry' "
                "AND r.entity_id = ? AND COALESCE(r.effective_to, '9999-12-31') >= ? "
                "AND r.effective_from <= ?",
                (
                    region_id,
                    classification_id,
                    entity_id,
                    effective_from.isoformat(),
                    effective_to.isoformat() if effective_to else "9999-12-31",
                ),
            ).fetchall()
            for etf in overlapping_etfs:
                overlap_start = max(
                    effective_from,
                    date.fromisoformat(etf["effective_from"]),
                    date.fromisoformat(etf["listing_from"]),
                )
                if effective_to is not None and overlap_start > effective_to:
                    continue
                if any(
                    item.entity_id == entity_id
                    for item in self.get_entity_representations(
                        region_id,
                        classification_id,
                        "industry",
                        as_of=overlap_start,
                    )
                ):
                    raise ValueError("A basket requires no approved active ETF in its period")
            signature = repr(
                (
                    region_id,
                    classification_id,
                    entity_id,
                    name,
                    source_id,
                    approval_reference,
                    effective_from,
                    effective_to,
                    sorted((item.listing_id, str(item.weight)) for item in members),
                )
            )
            identifier = "basket-" + sha256(signature.encode()).hexdigest()[:20]
            if connection.execute(
                "SELECT 1 FROM stock_baskets WHERE representation_id = ?",
                (identifier,),
            ).fetchone():
                return identifier
            try:
                connection.execute(
                    "INSERT INTO stock_baskets (representation_id, region_id, classification_id, "
                    "entity_id, name, source_id, approval_reference, effective_from, effective_to, "
                    "review_state) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'reviewed')",
                    (
                        identifier,
                        region_id,
                        classification_id,
                        entity_id,
                        name,
                        source_id,
                        approval_reference,
                        effective_from.isoformat(),
                        effective_to.isoformat() if effective_to else None,
                    ),
                )
                connection.executemany(
                    "INSERT INTO basket_constituents VALUES (?, ?, ?)",
                    ((identifier, item.listing_id, str(item.weight)) for item in members),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError(f"Could not approve stock basket: {error}") from error
            _bump_revision(connection)
        return identifier

    def get_stock_baskets(
        self,
        region_id: str,
        classification_id: str,
        *,
        as_of: date,
    ) -> tuple[ReviewedRepresentation, ...]:
        return self._reviewed_representations(
            region_id, classification_id, as_of=as_of, basket=True
        )

    def get_reviewed_industry_etfs(
        self,
        region_id: str,
        classification_id: str,
        *,
        as_of: date,
    ) -> tuple[ReviewedRepresentation, ...]:
        return self._reviewed_representations(
            region_id, classification_id, as_of=as_of, basket=False
        )

    def _reviewed_representations(
        self,
        region_id: str,
        classification_id: str,
        *,
        as_of: date,
        basket: bool,
    ) -> tuple[ReviewedRepresentation, ...]:
        if not self.is_initialized():
            raise ValueError(f"Regional database is missing or invalid: {self.path}")
        table = "stock_baskets" if basket else "entity_representations"
        extra = "AND r.review_state = 'reviewed'" if basket else "AND r.entity_type = 'industry'"
        day = as_of.isoformat()
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT r.*, COALESCE(r.approval_reference, s.approval_reference) AS approval "
                f"FROM {table} r JOIN data_sources s ON s.source_id = r.source_id "
                f"WHERE r.region_id = ? AND r.classification_id = ? {extra} "
                "AND r.effective_from <= ? AND (r.effective_to IS NULL OR r.effective_to >= ?) "
                "ORDER BY r.entity_id",
                (region_id, classification_id, day, day),
            ).fetchall()
            results: list[ReviewedRepresentation] = []
            for row in rows:
                reason: str | None = None
                members: list[BasketConstituent] = []
                symbol: str | None = None
                start = date.fromisoformat(row["effective_from"])
                end = date.fromisoformat(row["effective_to"]) if row["effective_to"] else None
                try:
                    _validate_entity(
                        connection,
                        region_id,
                        classification_id,
                        "industry",
                        row["entity_id"],
                        as_of,
                        as_of,
                    )
                    _validate_source(connection, row["source_id"], row["approval"] or "")
                    if basket:
                        constituent_rows = connection.execute(
                            "SELECT listing_id, weight FROM basket_constituents "
                            "WHERE representation_id = ? ORDER BY listing_id",
                            (row["representation_id"],),
                        ).fetchall()
                        for member in constituent_rows:
                            listing = _validate_listing(
                                connection,
                                member["listing_id"],
                                region_id,
                                start,
                                end,
                            )
                            members.append(
                                BasketConstituent(
                                    member["listing_id"],
                                    str(listing["provider_symbol"] or listing["symbol"]),
                                    Decimal(member["weight"]),
                                )
                            )
                        validate_weights(tuple(members))
                    else:
                        raw_listing = connection.execute(
                            "SELECT provider_symbol, symbol FROM stock_listings "
                            "WHERE listing_id = ?",
                            (row["listing_id"],),
                        ).fetchone()
                        if raw_listing:
                            symbol = str(raw_listing["provider_symbol"] or raw_listing["symbol"])
                        listing = _validate_listing(
                            connection,
                            row["listing_id"],
                            region_id,
                            as_of,
                            as_of,
                        )
                        symbol = str(listing["provider_symbol"] or listing["symbol"])
                except (ValueError, InvalidOperation) as error:
                    reason = str(error)
                results.append(
                    ReviewedRepresentation(
                        representation_id=row["representation_id"],
                        node_id=row["entity_id"],
                        kind="basket" if basket else "etf",
                        name=row["name"] if basket else symbol or row["listing_id"],
                        source_id=row["source_id"],
                        approval_reference=row["approval"] or "",
                        effective_from=start,
                        effective_to=end,
                        symbol=symbol,
                        constituents=tuple(sorted(members, key=lambda item: item.symbol)),
                        reason=reason,
                    )
                )
        return tuple(results)


def _etf_inventories(connection: sqlite3.Connection) -> tuple[Inventory, ...]:
    results: list[Inventory] = []
    for row in connection.execute("SELECT payload FROM etf_collection_runs ORDER BY event_order"):
        run = CollectionRun.decode(row["payload"])
        evidence = tuple(
            Evidence.decode(item["payload"])
            for item in connection.execute(
                "SELECT e.payload FROM etf_mapping_evidence e JOIN etf_collection_evidence m "
                "ON m.evidence_id=e.evidence_id WHERE m.run_id=? ORDER BY e.evidence_id",
                (run.run_id,),
            )
        )
        results.append(Inventory(run, evidence))
    return tuple(results)


def _etf_snapshot(connection: sqlite3.Connection) -> ResearchSnapshot:
    reviews = tuple(
        ReviewDecision.decode(row["payload"])
        for row in connection.execute(
            "SELECT payload FROM etf_candidate_reviews ORDER BY event_order"
        )
    )
    return ResearchSnapshot(_etf_inventories(connection), reviews)


def _validate_etf_candidate_approval(
    connection: sqlite3.Connection,
    review_id: str,
    region: str,
    classification: str,
    node: str,
    listing: sqlite3.Row,
) -> str:
    snapshot = _etf_snapshot(connection)
    selected = selected_review(snapshot.reviews, region, classification, node)
    if selected is None or selected.review_id != review_id:
        raise ValueError("Candidate review is not the current accepted exact-node selection")
    reasons = support_reasons(selected, snapshot)
    if reasons:
        raise ValueError(f"Candidate review requires re-review: {', '.join(reasons)}")
    supported = review_evidence(selected, snapshot)
    node_row = connection.execute(
        "SELECT node_type FROM industries WHERE industry_id=?",
        (node,),
    ).fetchone()
    validate_review(selected, supported, node_level=node_row["node_type"])
    verified_symbols = {listing["symbol"].strip().upper()}
    if listing["provider_symbol"]:
        verified_symbols.add(listing["provider_symbol"].strip().upper())
    if any(e.normalized_ticker not in verified_symbols for e in supported):
        raise ValueError(
            "Candidate review ticker does not match the verified listing/provider identity"
        )
    return snapshot.latest.run.run_id


def _link_etf_provenance(
    connection: sqlite3.Connection,
    representation_id: str,
    review_id: str,
    run_id: str,
) -> None:
    connection.execute(
        "INSERT OR IGNORE INTO etf_representation_provenance VALUES (?, ?, ?)",
        (representation_id, review_id, run_id),
    )


def _bump_revision(connection: sqlite3.Connection) -> None:
    connection.execute(
        "UPDATE database_metadata SET value = CAST(value AS INTEGER) + 1 WHERE key = 'revision'"
    )


def _validate_source(
    connection: sqlite3.Connection,
    source_id: str,
    approval_reference: str,
) -> None:
    source = connection.execute(
        "SELECT * FROM data_sources WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    if (
        not approval_reference.strip()
        or source is None
        or source["source_type"] != "local_file"
        or not source["reviewed_at"]
        or source["approval_reference"] != approval_reference
    ):
        raise ValueError("Source and approval reference must match a reviewed local import")


def _covers(row: sqlite3.Row, start: date, end: date | None) -> bool:
    return row["effective_from"] <= start.isoformat() and (
        row["effective_to"] is None
        or row["effective_to"] >= (end.isoformat() if end else "9999-12-31")
    )


def _validate_entity(
    connection: sqlite3.Connection,
    region_id: str,
    classification_id: str,
    entity_type: str,
    entity_id: str,
    start: date,
    end: date | None,
) -> None:
    if end is not None and end < start:
        raise ValueError("Representation effective dates are reversed")
    table = "sectors" if entity_type == "sector" else "industries"
    column = "sector_id" if entity_type == "sector" else "industry_id"
    node = connection.execute(
        f"SELECT * FROM {table} WHERE {column} = ? AND classification_id = ?",
        (entity_id, classification_id),
    ).fetchone()
    classification = connection.execute(
        "SELECT c.* FROM classifications c JOIN regions r ON r.region_id = c.region_id "
        "WHERE c.classification_id = ? AND c.region_id = ? AND r.status = 'active'",
        (classification_id, region_id),
    ).fetchone()
    if node is None or classification is None:
        raise ValueError(f"Reviewed {entity_type} {entity_id!r} is not in this classification")
    if not _covers(node, start, end) or not _covers(classification, start, end):
        raise ValueError(f"Classification/node {entity_id} is inactive during the effective period")
    _validate_source(
        connection,
        classification["source_id"],
        classification["approval_reference"] or "",
    )
    if entity_type == "industry":
        _validate_entity(
            connection,
            region_id,
            classification_id,
            "sector",
            node["sector_id"],
            start,
            end,
        )
        if node["source_id"] is not None:
            _validate_source(connection, node["source_id"], node["approval_reference"] or "")
        if node["node_type"] == "sub_industry":
            parent_id = node["parent_industry_id"]
            parent = connection.execute(
                "SELECT * FROM industries WHERE industry_id = ?",
                (parent_id,),
            ).fetchone()
            if parent is None or parent["node_type"] != "industry":
                raise ValueError("Sub-industry requires a reviewed industry parent")
            if parent["sector_id"] != node["sector_id"]:
                raise ValueError("Sub-industry parent belongs to a different sector")
            _validate_entity(
                connection,
                region_id,
                classification_id,
                "industry",
                parent_id,
                start,
                end,
            )


def _validate_listing(
    connection: sqlite3.Connection,
    listing_id: str,
    region_id: str,
    start: date,
    end: date | None,
) -> sqlite3.Row:
    listing = connection.execute(
        "SELECT l.*, st.resolution_state AS instrument_state FROM stock_listings l "
        "JOIN stocks st ON st.instrument_id = l.instrument_id WHERE l.listing_id = ?",
        (listing_id,),
    ).fetchone()
    if (
        listing is None
        or listing["region_id"] != region_id
        or listing["resolution_state"] != "verified"
        or listing["instrument_state"] != "identified"
        or not _covers(listing, start, end)
    ):
        raise ValueError(f"Listing {listing_id} must be verified and active for this region/period")
    source = connection.execute(
        "SELECT approval_reference FROM data_sources WHERE source_id = ?",
        (listing["source_id"],),
    ).fetchone()
    _validate_source(
        connection,
        listing["source_id"],
        (source["approval_reference"] or "") if source else "",
    )
    return listing


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
