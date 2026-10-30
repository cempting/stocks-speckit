from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.universe_import import import_reviewed_file

ROOT = Path(__file__).parents[2]


def _create_database(tmp_path: Path) -> Path:
    database_path = tmp_path / "market-universe.sqlite"
    database = RegionDatabase(database_path)
    database.initialize()
    members = tmp_path / "members.csv"
    members.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry,EffectiveFrom,ResolutionState\n"
        "instrument-a,AAA,Alpha,NASDAQ,Technology,Cloud,2020-01-01\n"
        "instrument-b,BBB,Beta,NASDAQ,Technology,Cloud,2020-01-01\n"
        "instrument-c,CCC,Gamma,NYSE,Financials,Banks,2020-01-01\n"
        "instrument-d,DDD,Delta,NYSE,,,2020-01-01\n"
        "instrument-placeholder,,Unresolved,NASDAQ,Technology,Cloud,2020-01-01,placeholder\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        members,
        region_id="US",
        classification_id="TEST",
        source_id="controlled-test",
        exchange_id=None,
        coverage="controlled sample",
        approval_reference="test-only",
    )
    return database_path


def _run_discovery(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AppTest:
    def build_fixture_provider(*args: object, **kwargs: object) -> FixtureProvider:
        del args, kwargs
        return FixtureProvider()

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        build_fixture_provider,
    )
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(_create_database(tmp_path)))
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    return AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )


def test_discovery_shows_only_sector_tape_until_sector_is_selected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_discovery(monkeypatch, tmp_path)

    assert not app.exception
    assert any(item.value == "Sector performance" for item in app.subheader)
    assert not any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Contained stocks" for item in app.subheader)
    assert any("Coverage: PARTIAL" in item.value for item in app.caption)
    assert any("Price + 50-session SMA" in item.value for item in app.caption)
    assert any("Volume by price direction" in item.value for item in app.caption)
    assert any(item.value == "Ticker" for item in app.caption)
    assert not any(item.value == "Representation" for item in app.caption)
    assert any("not verified buyer or seller activity" in item.value for item in app.caption)


def test_sector_and_industry_selection_replaces_tape_and_shows_all_members(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_discovery(monkeypatch, tmp_path)
    app.selectbox("market_leadership.progressive_discovery.sector").select("test-technology").run(
        timeout=20
    )

    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Sector performance" for item in app.subheader)
    assert any("Price + 50-session SMA" in item.value for item in app.caption)
    app.selectbox("market_leadership.progressive_discovery.industry").select("test-cloud").run(
        timeout=20
    )

    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    assert any(item.label == "AAA · Alpha" for item in app.button)
    assert any(item.label == "BBB · Beta" for item in app.button)
    assert any("Unresolved placeholder" in item.label for item in app.button)
    assert any("Price + 50-session SMA" in item.value for item in app.caption)
    assert any("Volume by price direction" in item.value for item in app.caption)


def test_thumbnail_period_and_performance_basis_persist_across_tapes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_discovery(monkeypatch, tmp_path)
    prefix = "market_leadership.progressive_discovery."
    period = app.segmented_control(prefix + "thumbnail_period")
    assert period.options == ["1w", "1m", "3m", "6m", "1y"]
    assert period.value == "3m"
    period.set_value("1w").run()
    app.segmented_control(prefix + "performance_basis").set_value("vs S&P 500").run()
    app.selectbox(prefix + "sector").select("test-technology").run()

    assert not app.exception
    assert app.segmented_control(prefix + "thumbnail_period").value == "1w"
    assert app.segmented_control(prefix + "performance_basis").value == "vs S&P 500"
    app.selectbox(prefix + "industry").select("test-cloud").run()
    assert not app.exception
    assert app.segmented_control(prefix + "thumbnail_period").value == "1w"
    assert any(item.label == "AAA · Alpha" for item in app.button)


def test_thumbnail_period_does_not_change_performance_returns() -> None:
    from market_leadership.ui.performance_table import PERFORMANCE_COLUMNS
    from market_leadership.ui.workflows.discovery_page import _build_entity_tape

    as_of = date(2026, 10, 29)
    history = pd.DataFrame(
        {"close": range(100, 500), "volume": [1000.0] * 400},
        index=pd.bdate_range(end=as_of, periods=400),
    )
    frames = [
        _build_entity_tape(
            entity_rows=(("sector-a", "Sector A"),),
            label="Sector",
            representation_by_id={"sector-a": "AAA"},
            history={"AAA": history},
            benchmark=history["close"],
            requested_as_of=as_of,
            observed_as_of=as_of,
            performance_mode="Absolute",
            preview_start=start,
        )
        for start in (date(2026, 10, 22), date(2025, 10, 29))
    ]

    assert len(frames[0]["Price chart"].iloc[0]) == 6
    assert len(frames[1]["Price chart"].iloc[0]) > 250
    pd.testing.assert_frame_equal(
        frames[0][list(PERFORMANCE_COLUMNS)],
        frames[1][list(PERFORMANCE_COLUMNS)],
    )
    assert frames[0]["12 months"].notna().all()


def test_missing_database_shows_setup_instructions_without_catalog_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(tmp_path / "missing.sqlite"))
    app = AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )

    assert not app.exception
    assert any("Initialize and populate" in item.value for item in app.info)
    assert not any("STOCK_MEMBERSHIP_CATALOG" in item.value for item in app.error)


def test_invalid_database_shows_explicit_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    invalid_path = tmp_path / "invalid.sqlite"
    invalid_path.write_text("invalid database", encoding="utf-8")
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(invalid_path))

    app = AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )

    assert not app.exception
    assert any("database is invalid" in item.value for item in app.error)


def test_unpopulated_database_shows_import_guidance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "empty.sqlite"
    RegionDatabase(database_path).initialize()
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(database_path))

    app = AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )

    assert not app.exception
    assert any("initialized but has no reviewed data" in item.value for item in app.info)


def test_changing_sector_clears_the_selected_industry_and_members(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_discovery(monkeypatch, tmp_path)
    app.selectbox("market_leadership.progressive_discovery.sector").select("test-technology").run(
        timeout=20
    )
    app.selectbox("market_leadership.progressive_discovery.industry").select("test-cloud").run(
        timeout=20
    )
    assert any(item.label == "AAA · Alpha" for item in app.button)

    app.selectbox("market_leadership.progressive_discovery.sector").select("test-financials").run(
        timeout=20
    )

    assert not app.exception
    assert app.selectbox("market_leadership.progressive_discovery.industry").value is None
    assert not any(item.label == "AAA · Alpha" for item in app.button)


def test_multiple_regions_default_to_us_and_clear_descendants_on_switch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = _create_database(tmp_path)
    database = RegionDatabase(database_path)
    source = tmp_path / "canada.csv"
    source.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "canadian-instrument,XYZ,Example,NASDAQ,Technology,Cloud\n",
        encoding="utf-8",
    )
    import_reviewed_file(
        database,
        source,
        region_id="CA",
        classification_id="CA-TEST",
        source_id="controlled-canada",
        exchange_id=None,
        coverage="controlled sample",
        approval_reference="test-only",
    )

    def build_fixture_provider(*args: object, **kwargs: object) -> FixtureProvider:
        del args, kwargs
        return FixtureProvider()

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        build_fixture_provider,
    )
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    app = AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )

    assert app.selectbox("market_leadership.progressive_discovery.region").value == "US"
    app.selectbox("market_leadership.progressive_discovery.sector").select("test-technology").run(
        timeout=20
    )
    app.selectbox("market_leadership.progressive_discovery.region").select("CA").run(timeout=20)

    assert not app.exception
    assert app.selectbox("market_leadership.progressive_discovery.sector").value is None


def test_industry_deep_dive_uses_the_same_database_memberships(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MARKET_UNIVERSE_DATABASE_PATH", str(_create_database(tmp_path)))
    app = AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/industry_deep_dive.py").run(
        timeout=20
    )
    assert not app.exception

    app.selectbox("market_leadership.screening.sector").select("test-technology").run(timeout=20)
    app.selectbox("market_leadership.screening.industry").select("test-cloud").run(timeout=20)

    assert not app.exception
    assert any("AAA" in str(item.value) for item in app.dataframe)
    assert any("BBB" in str(item.value) for item in app.dataframe)
