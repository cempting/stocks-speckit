"""Generate the exact local-handling dataset in a caller-owned test directory."""

import csv
import io
import json
from hashlib import sha256
from pathlib import Path


def expand_performance_release(manifest: Path) -> None:
    document = json.loads(manifest.read_text())
    artifacts = {item["role"]: item for item in document["artifacts"]}

    def read(role):
        path = manifest.parent / artifacts[role]["path"]
        reader = csv.DictReader(io.StringIO(path.read_text()))
        return reader.fieldnames, list(reader)

    def write(role, headers, rows):
        path = manifest.parent / artifacts[role]["path"]
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        artifacts[role].update(row_count=len(rows), sha256=sha256(path.read_bytes()).hexdigest())

    headers, original = read("hierarchy")
    template = original[0]
    nodes = [
        {
            **template,
            "NodeId": f"perf-sector-{i}",
            "NodeType": "sector",
            "Name": f"Performance sector {i}",
            "SectorId": f"perf-sector-{i}",
            "ParentIndustryId": "",
        }
        for i in range(11)
    ]
    nodes.extend(
        {
            **template,
            "NodeId": f"perf-industry-{i}",
            "NodeType": "industry",
            "Name": f"Performance industry {i}",
            "SectorId": f"perf-sector-{i % 11}",
            "ParentIndustryId": "",
        }
        for i in range(400)
    )
    nodes.extend(
        {
            **template,
            "NodeId": f"perf-sub-{i}",
            "NodeType": "sub_industry",
            "Name": f"Performance sub-industry {i}",
            "SectorId": f"perf-sector-{i % 11}",
            "ParentIndustryId": f"perf-industry-{i}",
        }
        for i in range(100)
    )
    write("hierarchy", headers, nodes)
    headers, original = read("stocks")
    template = original[0]
    stocks = [
        {
            **template,
            "RowId": f"perf-row-{i}",
            "MembershipId": f"perf-membership-{i}",
            "InstrumentId": f"perf-stock-{i}",
            "Name": f"Performance stock {i}",
            "IndustryId": f"perf-industry-{i % 400}",
            "SubIndustryId": f"perf-sub-{i % 400}" if i % 400 < 100 else "",
            "ListingId": f"perf-listing-{i}",
            "Ticker": f"PERF_STOCK_{i}",
            "ProviderSymbol": f"PERF_STOCK_{i}",
        }
        for i in range(10_000)
    ]
    write("stocks", headers, stocks)
    for role, node_id in (("sector_etfs", "perf-sector-0"), ("industry_etfs", "perf-industry-0")):
        headers, rows = read(role)
        for row in rows:
            row["NodeId"] = node_id
        write(role, headers, rows)
    audit = artifacts["audit"]
    path = manifest.parent / audit["path"]
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for record in records:
        if record["record_type"] == "basket":
            record["payload"]["node_id"] = "perf-industry-399"
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
    audit["sha256"] = sha256(path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(document))
