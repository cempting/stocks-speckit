"""Controlled file releases and daily prices for frontend tests."""

import csv
import json
from collections.abc import Callable
from datetime import date
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

from market_data.catalog import load_release


def edit_csv(manifest: Path, role: str, edit: Callable[[list[dict[str, str]]], None]) -> None:
    document = json.loads(manifest.read_text())
    artifact = next(item for item in document["artifacts"] if item["role"] == role)
    path = manifest.parent / artifact["path"]
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    assert fields is not None
    edit(rows)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    artifact.update(sha256=sha256(path.read_bytes()).hexdigest(), row_count=len(rows))
    document["catalog_revision"] = "0" * 64
    manifest.write_text(json.dumps(document))


def publish_entry(manifest: Path) -> Path:
    document = json.loads(manifest.read_text())
    document["catalog_revision"] = load_release(manifest).catalog_revision
    manifest.write_text(json.dumps(document))
    entry = manifest.parent / "CURRENT.json"
    entry.write_text(
        json.dumps(
            {
                "format": "market-catalog-entry-1",
                "release_id": document["release_id"],
                "manifest_path": manifest.name,
                "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
            }
        )
    )
    return entry


def detail_release(manifest: Path) -> Path:
    def hierarchy(rows):
        sector = next(row for row in rows if row["NodeType"] == "sector")
        rows.append(
            dict(sector, NodeId="test-financials", SectorId="test-financials", Name="Financials")
        )
        for row in rows:
            if row["NodeId"] == "test-financials":
                continue
            row["SectorId"] = "test-technology"
            if row["NodeType"] == "sector":
                row.update(NodeId="test-technology", Name="Technology")
            if row["NodeId"] == "test-hardware":
                row["SectorId"] = "test-financials"

    def stocks(rows):
        verified = dict(rows[1])
        rows[2].update(
            verified,
            RowId="detail-row-c",
            MembershipId="detail-membership-c",
            ListingId="detail-listing-c",
        )
        for row, suffix, name, industry in zip(
            rows,
            ("aaa", "bbb", "ccc"),
            ("Alpha", "Beta", "Gamma"),
            ("test-cloud", "test-cloud", "test-hardware"),
            strict=True,
        ):
            row.update(
                InstrumentId=f"instrument-{suffix}",
                Ticker=suffix.upper(),
                ProviderSymbol=suffix.upper(),
                Name=name,
                IndustryId=industry,
                SubIndustryId="",
            )

    edit_csv(manifest, "hierarchy", hierarchy)
    edit_csv(manifest, "stocks", stocks)
    edit_csv(
        manifest, "sector_etfs", lambda rows: [row.update(NodeId="test-technology") for row in rows]
    )
    return manifest


def bound_classification(manifest: Path, end: str) -> None:
    for role in ("hierarchy", "sector_etfs", "industry_etfs", "sub_industry_etfs"):
        edit_csv(manifest, role, lambda rows: [row.update(EffectiveTo=end) for row in rows])
    edit_csv(
        manifest, "stocks", lambda rows: [row.update(MembershipEffectiveTo=end) for row in rows]
    )
    document = json.loads(manifest.read_text())
    audit = next(item for item in document["artifacts"] if item["role"] == "audit")
    path = manifest.parent / audit["path"]
    records = [json.loads(line) for line in path.read_text().splitlines()]
    for record in records:
        if record["record_type"] == "basket":
            record["payload"]["period"]["end"] = end
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
    audit["sha256"] = sha256(path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(document))


class DailyProvider:
    provider_id = "yfinance"

    def __init__(self, calls: list[tuple[str, ...]]) -> None:
        self.calls = calls

    def fetch_daily_history(
        self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False
    ) -> dict[str, pd.DataFrame]:
        del start, force
        self.calls.append(symbols)
        return {
            symbol: pd.DataFrame(
                {"close": [100 + index / 100 for index in range(400)], "volume": [1000] * 400},
                index=pd.bdate_range(end=end, periods=400),
            )
            for symbol in symbols
        }


def configure_ui(monkeypatch: pytest.MonkeyPatch, manifest: Path) -> list[tuple[str, ...]]:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setenv("MARKET_CATALOG_MANIFEST_PATH", str(publish_entry(manifest)))
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(manifest.parent / "unused.sqlite"))
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(manifest.parent / "price-cache"))
    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        lambda *args, **kwargs: DailyProvider(calls),
    )
    return calls
