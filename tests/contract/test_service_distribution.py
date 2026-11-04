import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
    }
    return subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True, text=True, timeout=180,
    )


@pytest.fixture(scope="module")
def distribution_wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    output = tmp_path_factory.mktemp("structure-wheels")
    result = run(
        ["uv", "build", "--all-packages", "--wheel", "--out-dir", str(output)], ROOT,
    )
    assert result.returncode == 0, result.stderr
    names = ("market_data", "market_leadership", "market_structure")
    wheels = {name: output / f"{name}-0.1.0-py3-none-any.whl" for name in names}
    assert all(path.is_file() for path in wheels.values()), (
        f"Expected three independent wheels, found {sorted(p.name for p in output.iterdir())}"
    )
    return wheels


@pytest.mark.parametrize("installation", ["shared", "app", "service", "maintenance"])
def test_isolated_distribution_installs(
    installation: str, distribution_wheels: dict[str, Path], tmp_path: Path,
) -> None:
    environment = tmp_path / "environment"
    created = run(["uv", "venv", "--python", sys.executable, str(environment)], tmp_path)
    assert created.returncode == 0, created.stderr
    python = environment / "bin/python"
    wheels = [str(distribution_wheels["market_data"])]
    if installation in {"app", "maintenance"}:
        suffix = "[maintenance]" if installation == "maintenance" else ""
        wheels.append(str(distribution_wheels["market_leadership"]) + suffix)
    if installation in {"service", "maintenance"}:
        wheels.append(str(distribution_wheels["market_structure"]))
    installed = run(
        ["uv", "pip", "install", "--python", str(python), *wheels], tmp_path,
    )
    assert installed.returncode == 0, installed.stderr
    script = """
import importlib.metadata
import importlib.util
import json
import sys
from importlib.resources import files

mode = sys.argv[1]
assert files("market_data.schemas").joinpath("catalog-manifest.schema.json").is_file()
assert files("market_data.schemas").joinpath("catalog-manifest-v2.schema.json").is_file()
assert files("market_data.schemas").joinpath("snapshot-manifest.schema.json").is_file()
assert files("market_data.schemas").joinpath("weekly-snapshot-manifest.schema.json").is_file()
if mode in {"shared", "service"}:
    for name in ("market_leadership", "streamlit", "yfinance", "massive", "httpx"):
        assert importlib.util.find_spec(name) is None, name
if mode in {"shared", "app"}:
    for name in ("market_structure", "market_data_tools"):
        assert importlib.util.find_spec(name) is None, name
if mode == "shared":
    for name in ("starlette", "uvicorn"):
        assert importlib.util.find_spec(name) is None, name
if mode in {"app", "maintenance"}:
    import market_leadership.bootstrap
    import market_leadership.domain.catalog as legacy
    import market_data.domain.catalog as shared
    assert legacy is shared
    scripts = importlib.metadata.distribution("market-leadership").entry_points
    assert not any(e.name in {
        "market-catalog", "market-company-evidence", "market-universe-legacy",
        "market-structure",
    } for e in scripts)
if mode in {"service", "maintenance"}:
    import market_structure
    import market_data_tools.catalog_admin
    scripts = importlib.metadata.distribution("market-structure").entry_points
    assert {"market-catalog", "market-company-evidence", "market-universe-legacy",
            "market-structure"} <= {e.name for e in scripts if e.group == "console_scripts"}
print(json.dumps({"installation": mode, "isolated": True}))
"""
    verified = run([str(python), "-c", script, installation], tmp_path)
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["isolated"] is True
    if installation in {"service", "maintenance"}:
        for command in ["market-catalog", "market-company-evidence", "market-universe-legacy"]:
            result = run([str(environment / "bin" / command), "--help"], tmp_path)
            assert result.returncode == 0, result.stderr
            assert "usage:" in result.stdout
    if installation in {"app", "maintenance"}:
        for module in ["catalog_admin", "company_evidence_admin", "universe_admin"]:
            result = run(
                [str(python), "-m", f"market_leadership.{module}", "--help"], tmp_path,
            )
            if installation == "app":
                assert result.returncode == 2, result.stderr
                assert "market-leadership[maintenance]" in result.stderr
                assert "Traceback" not in result.stderr
            else:
                assert result.returncode == 0, result.stderr
                assert "usage:" in result.stdout


@pytest.mark.parametrize("module", ["catalog_admin", "company_evidence_admin", "universe_admin"])
def test_optional_delegates_do_not_mask_unrelated_import_failures(
    module: str, tmp_path: Path,
) -> None:
    script = """
import importlib
import importlib.abc
import sys
module = importlib.import_module(sys.argv[1])
class BrokenDependency(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("market_data_tools"):
            raise ModuleNotFoundError(
                "broken maintenance dependency", name="unrelated_missing_dependency"
            )
sys.meta_path.insert(0, BrokenDependency())
try:
    module.main(["--help"])
except ModuleNotFoundError as error:
    assert error.name == "unrelated_missing_dependency"
    print("unrelated-import-preserved")
else:
    raise AssertionError("Internal import failure was masked")
"""
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join([
        str(ROOT / "src"), str(ROOT / "packages/market-data/src"),
        str(ROOT / "services/market-structure/src"),
    ])}
    result = subprocess.run(
        [sys.executable, "-c", script, f"market_leadership.{module}"],
        cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unrelated-import-preserved"
