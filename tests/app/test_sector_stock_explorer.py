from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from market_leadership.config import Settings
from market_leadership.domain.stock_selection import MembershipCatalog, MembershipEntry
from market_leadership.infrastructure.fixture_provider import FixtureProvider

ROOT = Path(__file__).parents[2]


def _catalog() -> MembershipCatalog:
    return MembershipCatalog(
        observed_on=date(2026, 10, 23),
        source_id="controlled-test",
        classification="controlled",
        mode="fixture",
        coverage="two controlled members",
        approval_reference="test-only",
        entries=(
            MembershipEntry(
                "instrument-a",
                "company-a",
                "AAA",
                "Alpha",
                "NASDAQ",
                "USD",
                "TECH",
                "Information Technology",
                "CLOUD",
                "Cloud Computing",
                date(2026, 1, 1),
                None,
            ),
            MembershipEntry(
                "instrument-b",
                "company-b",
                "BBB",
                "Beta",
                "NASDAQ",
                "USD",
                "TECH",
                "Information Technology",
                "CLOUD",
                "Cloud Computing",
                date(2026, 1, 1),
                None,
            ),
        ),
        fingerprint="controlled-catalog",
    )


def _run_discovery(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AppTest:
    def build_fixture_provider(*args: object, **kwargs: object) -> FixtureProvider:
        del args, kwargs
        return FixtureProvider()

    def load_test_catalog(path: str) -> MembershipCatalog:
        del path
        return _catalog()

    monkeypatch.setattr(
        "market_leadership.bootstrap.build_request_provider",
        build_fixture_provider,
    )
    monkeypatch.setattr(
        "market_leadership.infrastructure.stock_membership.load_membership_catalog",
        load_test_catalog,
    )
    monkeypatch.setattr(
        "market_leadership.infrastructure.stock_membership.validate_live_access",
        _validate_test_catalog,
    )
    monkeypatch.setenv("STOCK_MEMBERSHIP_CATALOG", "controlled-test.json")
    monkeypatch.setenv("MARKET_DATA_SOURCE_CACHE_PATH", str(tmp_path))
    return AppTest.from_file(ROOT / "src/market_leadership/ui/workflows/discovery_page.py").run(
        timeout=20
    )


def _validate_test_catalog(catalog: MembershipCatalog, settings: Settings) -> None:
    del catalog, settings


def test_discovery_shows_only_sector_tape_until_sector_is_selected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_discovery(monkeypatch, tmp_path)

    assert not app.exception
    assert any(item.value == "Sector performance" for item in app.subheader)
    assert not any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Contained stocks" for item in app.subheader)


def test_sector_and_industry_selection_replaces_tape_and_shows_all_members(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    app = _run_discovery(monkeypatch, tmp_path)
    app.selectbox("market_leadership.progressive_discovery.sector").select("XLK").run(timeout=20)

    assert not app.exception
    assert any(item.value == "Industry momentum" for item in app.subheader)
    assert not any(item.value == "Sector performance" for item in app.subheader)
    app.selectbox("market_leadership.progressive_discovery.industry").select(
        "US-CLOUD-COMPUTING"
    ).run(timeout=20)

    assert not app.exception
    assert any(item.value == "Contained stocks" for item in app.subheader)
    member_frame = next(item.value for item in app.dataframe if "Ticker" in item.value.columns)
    assert member_frame["Ticker"].tolist() == ["AAA", "BBB"]
