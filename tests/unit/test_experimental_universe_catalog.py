from datetime import UTC, datetime

import pytest

from market_leadership.infrastructure.experimental_universe_catalog import (
    UniverseSource,
    build_experimental_catalog,
    load_experimental_catalog,
    write_experimental_catalog,
)


def _write_universe(path, rows: list[str]) -> None:
    path.write_text("Ticker,Name,Sector,Industry\n" + "\n".join(rows) + "\n")


def test_experimental_catalog_prioritizes_sources_and_preserves_conflicts(tmp_path) -> None:
    sp500 = tmp_path / "sp500.csv"
    nasdaq = tmp_path / "nasdaq.csv"
    _write_universe(
        sp500,
        [
            "AAA,Alpha,Information Technology,Application Software",
            "BBB,Beta,Health Care,Biotechnology",
        ],
    )
    _write_universe(
        nasdaq,
        [
            "AAA,Alpha,Technology,Software",
            "CCC,Gamma,Financials,Capital Markets",
            "BAD SYMBOL,Skip,Financials,Banks",
            "DDD,Skip,undefined,undefined",
        ],
    )

    catalog = build_experimental_catalog(
        (
            UniverseSource("sp500-gics", sp500, 0),
            UniverseSource("nasdaq-provider", nasdaq, 1),
        ),
        generated_at=datetime(2026, 10, 30, tzinfo=UTC),
    )

    assert catalog.member_count == 3
    application_software = next(
        industry for industry in catalog.industries if industry.industry == "Application Software"
    )
    assert application_software.member_count == 1
    assert application_software.source_ids == ("nasdaq-provider", "sp500-gics")
    assert application_software.classification_conflict_count == 1


def test_experimental_catalog_round_trips_and_rejects_invalid_schema(tmp_path) -> None:
    universe = tmp_path / "universe.csv"
    _write_universe(universe, ["AAA,Alpha,Information Technology,Application Software"])
    catalog = build_experimental_catalog(
        (UniverseSource("sp500-gics", universe, 0),),
        generated_at=datetime(2026, 10, 30, tzinfo=UTC),
    )
    output = tmp_path / "catalog.json"

    write_experimental_catalog(catalog, output)

    assert load_experimental_catalog(output) == catalog
    output.write_text("{}")
    with pytest.raises(ValueError, match="schema"):
        load_experimental_catalog(output)
