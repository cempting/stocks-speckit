import ast
import inspect
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from market_leadership.application.discover_sectors import discover_sectors
from market_leadership.infrastructure.catalog_files import load_release

SOURCE = Path(__file__).parents[2] / "src/market_leadership"


@pytest.mark.parametrize(
    "relative,names",
    [
        ("application/discover_sectors.py", {"BENCHMARK", "SECTOR_PROXIES"}),
        ("domain/industry_momentum.py", {"INDUSTRY_PROXIES", "INDUSTRY_REPRESENTATIONS"}),
        ("infrastructure/stock_membership.py", {"FIXTURE_CATALOG"}),
        ("infrastructure/local_etf_sources.py", {"DEFAULT_ROOTS", "DEFAULT_CATALOGS"}),
    ],
)
def test_no_embedded_runtime_catalog(relative: str, names: set[str]) -> None:
    tree = ast.parse((SOURCE / relative).read_text())
    assignments = {
        node.id
        for statement in tree.body
        if isinstance(statement, (ast.Assign, ast.AnnAssign))
        for target in (
            statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        )
        for node in ast.walk(target)
        if isinstance(node, ast.Name)
    }
    assert assignments.isdisjoint(names), f"Embedded catalog authority in {relative}"


def test_no_production_fixture_provider() -> None:
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name != "FixtureProvider", f"Runtime fixture catalog in {path.name}"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "market_leadership.infrastructure.fixture_provider", (
                    f"Runtime fixture import in {path.name}"
                )


def test_sql_is_exclusive_to_explicit_migration() -> None:
    for path in SOURCE.rglob("*.py"):
        if path.name == "catalog_migration.py":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(alias.name != "sqlite3" for alias in node.names), (
                    f"SQL outside migration in {path.name}"
                )
            if isinstance(node, ast.ImportFrom):
                assert node.module != "sqlite3", f"SQL outside migration in {path.name}"


def test_no_default_benchmark_in_regime_calculation() -> None:
    tree = ast.parse((SOURCE / "domain/regimes.py").read_text())
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "calculate_market_sentiment"
    )
    assert not any(
        isinstance(default, ast.Constant) and isinstance(default.value, str)
        for default in (*function.args.defaults, *function.args.kw_defaults)
        if default is not None
    ), "Benchmark must be supplied by reviewed file evidence"


def test_sector_requests_require_explicit_controlled_catalog(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    requested = {listing.provider_symbol for listing in snapshot.listings}
    assert requested == {"TEST_ETF"}
    tree = ast.parse((SOURCE / "application/discover_sectors.py").read_text())
    embedded = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)}
    assert requested.isdisjoint(embedded)
    assert "snapshot" in inspect.signature(discover_sectors).parameters, (
        "Sector discovery must accept the same explicit file snapshot as other views"
    )
    assert snapshot.provider_symbols(
        snapshot.release.regions[0].classifications[0].scope, "test-sector", date(2026, 10, 30)
    ) == ("TEST_STOCK_1", "TEST_STOCK_2")


def test_current_sector_request_set_does_not_inherit_a_code_roster(catalog_release: Path) -> None:
    snapshot = load_release(catalog_release)
    expected = {listing.provider_symbol for listing in snapshot.listings}

    class RequestSpy:
        provider_id = "test-catalog-boundary"

        def fetch_daily_history(
            self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False
        ) -> dict[str, pd.DataFrame]:
            assert set(symbols) == expected, (
                "Production requests must follow controlled file evidence"
            )
            return {}

    discover_sectors(
        RequestSpy(),
        snapshot=snapshot,
        scope=snapshot.scope_on("US", date(2026, 10, 30)),
        as_of=date(2026, 10, 30),
    )
