import json
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import cast

from market_leadership.config import Settings
from market_leadership.domain.stock_selection import MembershipCatalog, MembershipEntry

FIXTURE_CATALOG = (
    Path(__file__).parents[3] / "tests/fixtures/acceptance/fundamental_membership.json"
)


def _record(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Membership catalog objects must be JSON objects")
    return cast(dict[str, object], value)


def _text(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Membership catalog requires nonempty {key}")
    return value.strip()


def load_membership_catalog(path: str | Path) -> MembershipCatalog:
    source = Path(path)
    if source.stat().st_size > 2_000_000:
        raise ValueError("Membership catalog exceeds the two-megabyte input limit")
    raw = source.read_bytes()
    document = _record(json.loads(raw))
    if document.get("schema_version") != 1 or document.get("market") != "US":
        raise ValueError("Membership catalog requires schema version 1 and US market")
    mode = _text(document, "evidence_mode")
    if mode not in ("fixture", "live"):
        raise ValueError("Membership evidence mode must be fixture or live")
    observed_on = date.fromisoformat(_text(document, "observation_date"))
    if observed_on > date.today():
        raise ValueError("Membership observation date cannot be in the future")
    entries_value = document.get("entries")
    if not isinstance(entries_value, list):
        raise ValueError("Membership entries must be an array")
    entries: list[MembershipEntry] = []
    identities: set[str] = set()
    listings: set[str] = set()
    industries: dict[str, tuple[str, str]] = {}
    sectors: dict[str, str] = {}
    for raw_entry in cast(list[object], entries_value):
        row = _record(raw_entry)
        if row.get("instrument_type") != "stock":
            raise ValueError("Membership entries must identify stock instruments")
        entry = MembershipEntry(
            _text(row, "instrument_id"),
            _text(row, "company_id"),
            _text(row, "symbol"),
            _text(row, "name"),
            _text(row, "exchange"),
            _text(row, "currency"),
            _text(row, "sector_id"),
            _text(row, "sector_name"),
            _text(row, "industry_id"),
            _text(row, "industry_name"),
            date.fromisoformat(_text(row, "effective_from")),
            date.fromisoformat(_text(row, "effective_to"))
            if row.get("effective_to") is not None
            else None,
        )
        if (
            len(entry.currency) != 3
            or not entry.currency.isalpha()
            or entry.currency != entry.currency.upper()
        ):
            raise ValueError("Membership currency must use a three-letter code")
        if entry.symbol != entry.symbol.upper():
            raise ValueError("Membership symbols must use canonical uppercase provider symbols")
        if entry.effective_to is not None and entry.effective_to < entry.effective_from:
            raise ValueError("Membership effective dates are reversed")
        if entry.instrument_id in identities or entry.symbol in listings:
            raise ValueError("Membership contains duplicate instruments or listings")
        parent = (entry.sector_id, entry.industry_name)
        if entry.industry_id in industries and industries[entry.industry_id] != parent:
            raise ValueError("Membership industry has conflicting parent relationships")
        if entry.sector_id in sectors and sectors[entry.sector_id] != entry.sector_name:
            raise ValueError("Membership sector identity has conflicting names")
        identities.add(entry.instrument_id)
        listings.add(entry.symbol)
        industries[entry.industry_id] = parent
        sectors[entry.sector_id] = entry.sector_name
        entries.append(entry)
    return MembershipCatalog(
        observed_on,
        _text(document, "source_id"),
        _text(document, "classification"),
        mode,
        _text(document, "coverage"),
        _text(document, "approval_reference"),
        tuple(entries),
        sha256(raw).hexdigest(),
    )


def validate_live_access(catalog: MembershipCatalog, settings: Settings) -> None:
    if settings.provider_ids != ("yfinance",) or settings.default_provider != "yfinance":
        raise ValueError("Live grading requires a single yfinance source; review provider settings")
    if catalog.mode != "live":
        raise ValueError("A fixture catalog cannot authorize live requests")
    if not settings.fundamental_display_approval or (
        settings.fundamental_display_approval != catalog.approval_reference
    ):
        raise ValueError("Review live display rights and configure the matching approval reference")
    if catalog.observed_on != date.today():
        raise ValueError("Unsupported historical live membership context; use matching fixtures")
