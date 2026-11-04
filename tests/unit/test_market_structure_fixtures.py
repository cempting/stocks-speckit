import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from market_data.catalog import load_release
from tests.fixtures.market_structure.build_demo import build_demo

ROOT = Path(__file__).parents[2]


def test_demo_builds_valid_reviewed_versions_without_acquisition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Fixture building must not acquire external data")

    monkeypatch.setattr("socket.socket.connect", forbidden)
    paths = build_demo(tmp_path / "demo")
    for version in (1, 2):
        manifest = paths[f"v{version}"]
        assert json.loads(manifest.read_text())["format"] == f"market-catalog-release-{version}"
        snapshot = load_release(manifest)
        assert snapshot.instrument_registry
        assert snapshot.release.catalog_revision == snapshot.catalog_revision
        registry_dir = paths["registries" if version == 1 else "registries_v2"]
        assert {p.name for p in registry_dir.iterdir()} == {
            "sources.json", "bindings.json", "observation-policies.json", "indexes.json",
        }
        bindings = json.loads((registry_dir / "bindings.json").read_text())["bindings"]
        assert bindings
        assert all(b["catalog_revision"] == snapshot.catalog_revision for b in bindings)
        sources = json.loads((registry_dir / "sources.json").read_text())
        assert any(source["kind"] == "news" for source in sources["sources"])
        policy = json.loads((registry_dir / "observation-policies.json").read_text())
        schema = json.loads((
            ROOT / "specs/013-market-structure-service/contracts/observation-policies.schema.json"
        ).read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(policy)
        policy_record = dict(policy["policies"][0])
        assert policy_record["frequencies"] == ["1d"]
        assert policy_record["return_bases"] == ["adjusted"]
        fingerprint = policy_record.pop("fingerprint")
        assert fingerprint == sha256(json.dumps(
            policy_record, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode()).hexdigest()
        indexes = json.loads((registry_dir / "indexes.json").read_text())
        assert indexes["indexes"][0]["index_id"] == "test-index"
    with (paths["v2"].parent / "stocks.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    listings: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["ListingId"]:
            listings[row["InstrumentId"]].add(row["ListingId"])
    memberships = Counter(r["InstrumentId"] for r in rows if r["RowKind"] == "membership")
    assert max(len(values) for values in listings.values()) >= 2
    assert max(memberships.values()) >= 2
    assert not list((tmp_path / "demo").rglob("*.parquet"))
    build_demo(tmp_path / "second")
    for path in (tmp_path / "demo").rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (
                tmp_path / "second" / path.relative_to(tmp_path / "demo")
            ).read_bytes()
    with pytest.raises(FileExistsError):
        build_demo(tmp_path / "demo")


def test_demo_cli_uses_explicit_output(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tests.fixtures.market_structure.build_demo",
         "--output", str(tmp_path / "cli")],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["format"] == "market-structure-demo-1"
    assert (tmp_path / "cli/catalog/manifest.json").is_file()
