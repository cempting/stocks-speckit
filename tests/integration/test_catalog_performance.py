import json
import platform
import sys
from datetime import date
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from market_leadership.infrastructure import catalog_files
from market_leadership.infrastructure.catalog_files import CatalogReader, load_release
from tests.fixtures.catalogs.performance import expand_performance_release

AS_OF = date(2026, 10, 30)


def test_exact_sc004_cold_and_warm_handling(
    catalog_release: Path, tmp_path: Path, monkeypatch
) -> None:
    expand_performance_release(catalog_release)
    document = json.loads(catalog_release.read_text())
    document["catalog_revision"] = load_release(catalog_release).catalog_revision
    catalog_release.write_text(json.dumps(document))
    entry = tmp_path / "CURRENT.json"
    entry.write_text(
        json.dumps(
            {
                "format": "market-catalog-entry-1",
                "release_id": document["release_id"],
                "manifest_path": str(catalog_release.relative_to(tmp_path)),
                "manifest_sha256": sha256(catalog_release.read_bytes()).hexdigest(),
            }
        )
    )
    parses = 0
    original = catalog_files._csv

    def counted_parse(raw, role):
        nonlocal parses
        parses += 1
        return original(raw, role)

    monkeypatch.setattr(catalog_files, "_csv", counted_parse)
    cold: list[float] = []
    for _ in range(3):
        reader = CatalogReader()
        started = perf_counter()
        snapshot = reader.read(entry)
        scope = snapshot.scope_on("US", AS_OF)
        nodes = snapshot.active_nodes(scope, AS_OF)
        rows = tuple(
            row
            for node in nodes
            if node.node_type == "sector"
            for row in snapshot.members(scope, node.node_id, AS_OF)
        )
        elapsed = perf_counter() - started
        assert len(nodes) == 511
        assert sum(node.node_type != "sector" for node in nodes) == 500
        assert (
            len(snapshot.stocks) == len(rows) == len({row.instrument_id for row in rows}) == 10_000
        )
        cold.append(elapsed)
        assert elapsed <= 5
    assert parses == 21
    warm: list[float] = []
    for i in range(10):
        started = perf_counter()
        current = reader.read(entry)
        selected = current.members(scope, f"perf-industry-{i}", AS_OF)
        symbols = current.provider_symbols(scope, f"perf-industry-{i}", AS_OF)
        elapsed = perf_counter() - started
        assert current is snapshot
        assert len(selected) == len(symbols) == 25
        assert {row.instrument_id for row in selected} == {
            f"perf-stock-{index}" for index in range(i, 10_000, 400)
        }
        warm.append(elapsed)
        assert elapsed <= 1
    assert parses == 21
    print(
        json.dumps(
            {
                "environment": (
                    f"{platform.system()} {platform.machine()} "
                    f"Python {sys.version.split()[0]}"
                ),
                "stock_rows": 10_000,
                "sectors": 11,
                "industry_sub_industry_nodes": 500,
                "cold_seconds": cold,
                "warm_seconds": warm,
                "csv_parses": parses,
            }
        )
    )
