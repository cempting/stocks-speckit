import ast
import importlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from market_data.catalog import load_release
from market_data_tools.catalog_admin import main
from tests.membership_helpers import build_v2_release, membership_fixture

ROOT = Path(__file__).parents[2]
SRC = ROOT / "src"


@pytest.mark.parametrize(
    ("package", "forbidden"),
    [
        ("market_data", {"market_leadership", "market_data_tools", "streamlit", "yfinance"}),
        ("market_data_tools", {"market_leadership", "streamlit", "yfinance", "sqlite3"}),
    ],
)
def test_data_and_tools_do_not_depend_on_the_app(package: str, forbidden: set[str]) -> None:
    violations = []
    for path in (SRC / package).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            modules = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module]
                if isinstance(node, ast.ImportFrom) and node.module is not None
                else []
            )
            for module in modules:
                if module.split(".")[0] in forbidden:
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {module}")
    assert not violations, "\n".join(violations)


def test_app_does_not_depend_on_maintenance_tools() -> None:
    compatibility_entrypoints = {
        "catalog_admin.py",
        "company_evidence_admin.py",
        "universe_admin.py",
    }
    for path in (SRC / "market_leadership").rglob("*.py"):
        if path.parent == SRC / "market_leadership" and path.name in compatibility_entrypoints:
            continue
        tree = ast.parse(path.read_text())
        assert not any(
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".")[0] == "market_data_tools"
            or isinstance(node, ast.Import)
            and any(alias.name.split(".")[0] == "market_data_tools" for alias in node.names)
            for node in ast.walk(tree)
        ), str(path)


@pytest.mark.parametrize("module", ["catalog_admin", "company_evidence_admin"])
def test_tools_run_without_app_ui_provider_or_database_imports(
    module: str, tmp_path: Path
) -> None:
    script = """
import importlib.abc
import runpy
import sys

class ForbidApp(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {
            "market_leadership", "streamlit", "yfinance", "sqlite3"
        }:
            raise AssertionError(f"Forbidden dependency: {fullname}")

sys.meta_path.insert(0, ForbidApp())
module = sys.argv[1]
sys.argv = [module, "--help"]
runpy.run_module(module, run_name="__main__")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, f"market_data_tools.{module}"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(SRC)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


@pytest.mark.parametrize("version", [1, 2])
def test_tool_publication_is_readable_by_the_app_without_network(
    version: int,
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from market_leadership.ui.cache import load_catalog_snapshot

    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Catalog maintenance must not fetch market data")

    monkeypatch.setattr("socket.socket.connect", no_network)
    candidate = (
        build_v2_release(
            catalog_release, tmp_path / "v2", membership_fixture(deep_levels=4)
        )
        if version == 2
        else catalog_release
    )
    before = load_release(candidate)
    entry = tmp_path / "published/CURRENT.json"
    assert main(["validate-catalog", "--release-manifest", str(candidate)]) == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation["publication_state"] == "not_published"
    assert not entry.exists()
    assert main([
        "activate-catalog",
        "--manifest", str(entry),
        "--release-manifest", str(candidate),
        "--expected-release", "none",
    ]) == 0
    published = json.loads(capsys.readouterr().out)

    snapshot = load_catalog_snapshot(entry)
    assert snapshot.release.release_id == published["catalog"]["release_id"]
    assert snapshot.catalog_revision == before.catalog_revision
    assert snapshot.instrument_registry == before.instrument_registry
    assert snapshot.membership_registry == before.membership_registry
    assert snapshot.regional_listings == before.regional_listings
    as_of = date(2026, 10, 30)
    scope = snapshot.scope_on("US", as_of)
    assert scope is not None
    assert snapshot.provider_symbols(scope, "test-sector", as_of) == (
        before.provider_symbols(scope, "test-sector", as_of)
    )

    candidate.write_text('{"format": "unsupported-release"}')
    original_entry = entry.read_bytes()
    assert main([
        "activate-catalog",
        "--manifest", str(entry),
        "--release-manifest", str(candidate),
        "--expected-release", snapshot.release.release_id,
    ]) == 2
    failure = json.loads(capsys.readouterr().out)
    assert failure["status"] == "failed"
    assert entry.read_bytes() == original_entry
    assert load_catalog_snapshot(entry).catalog_revision == before.catalog_revision


@pytest.mark.parametrize(
    ("legacy", "shared"),
    [
        ("domain.catalog", "market_data.domain.catalog"),
        ("domain.fundamentals", "market_data.domain.fundamentals"),
        ("infrastructure.catalog_files", "market_data.catalog"),
        ("infrastructure.company_evidence_files", "market_data.company_evidence"),
    ],
)
def test_legacy_imports_share_the_same_contract_identity(legacy: str, shared: str) -> None:
    assert importlib.import_module(f"market_leadership.{legacy}") is (
        importlib.import_module(shared)
    )
