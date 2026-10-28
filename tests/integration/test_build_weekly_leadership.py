import subprocess
import sys
from datetime import date

import pandas as pd
import pytest

from market_leadership.application.build_snapshot import build_weekly_snapshot
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository


def test_weekly_builder_publishes_separate_local_sector_and_industry_snapshots(tmp_path) -> None:
    from market_leadership.application.build_snapshot import build_weekly_snapshot

    repository = ParquetSnapshotRepository(tmp_path)
    provider = FixtureProvider()
    for market_id, benchmark, currency in (
        ("US", "SPX", "USD"),
        ("JP", "N225", "JPY"),
        ("GB", "UKX", "GBP"),
    ):
        for level in ("SECTOR", "INDUSTRY"):
            snapshot_id = f"{market_id.lower()}-{level.lower()}-2026-10-23"
            reference = build_weekly_snapshot(
                provider,
                repository,
                snapshot_id=snapshot_id,
                market_id=market_id,
                level=level,
                as_of=date(2026, 10, 28),
            )
            manifest, tables = repository.load_weekly(snapshot_id)
            assert reference.as_of == date(2026, 10, 23)
            assert manifest["market_id"] == market_id
            assert manifest["level"] == level
            assert manifest["benchmark_id"] == benchmark
            assert manifest["currency"] == currency
            assert set(tables) == {"entries"}
            entries = tables["entries"]
            assert not entries.empty
            assert (entries["market_id"] == market_id).all()
            assert (entries["level"] == level).all()
            assert entries["rank"].notna().any()
            if level == "INDUSTRY":
                assert entries["parent_node_id"].notna().all()
                assert entries["parent_relative_3m"].notna().any()


def test_weekly_builder_uses_previous_completed_week_without_replacing_latest(tmp_path) -> None:
    from market_leadership.application.build_snapshot import build_weekly_snapshot

    repository = ParquetSnapshotRepository(tmp_path)
    provider = FixtureProvider()
    first = build_weekly_snapshot(
        provider,
        repository,
        snapshot_id="completed",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    earlier = build_weekly_snapshot(
        provider,
        repository,
        snapshot_id="earlier",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 23),
    )
    assert earlier.as_of == date(2026, 10, 16)
    assert repository.load_latest_weekly("US", "SECTOR") == first


def test_weekly_builder_leaves_missing_proxy_unranked_without_hiding_other_sectors(
    tmp_path, monkeypatch
) -> None:
    from dataclasses import replace

    from market_leadership.application.build_snapshot import build_weekly_snapshot

    provider = FixtureProvider()
    original = provider.weekly_inputs
    missing_proxy_id = (
        provider.weekly_inputs("US", as_of=date(2026, 10, 28)).representations[0].proxy_id
    )

    def missing_proxy(market_id, *, as_of):
        context = original(market_id, as_of=as_of)
        proxy = context.representations[0]
        histories = dict(context.histories)
        histories.pop(proxy.instrument_id)
        return replace(context, histories=histories)

    monkeypatch.setattr(provider, "weekly_inputs", missing_proxy)
    repository = ParquetSnapshotRepository(tmp_path)
    build_weekly_snapshot(
        provider,
        repository,
        snapshot_id="missing-proxy",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    _, tables = repository.load_weekly("missing-proxy")
    entries = tables["entries"]
    assert entries["rank"].notna().any()
    missing = entries.loc[entries["proxy_id"] == missing_proxy_id]
    assert len(missing) == 1
    assert missing.iloc[0]["sufficiency"] == "INSUFFICIENT"
    assert missing.iloc[0]["rank"] is None or bool(pd.isna(missing.iloc[0]["rank"]))


def test_weekly_browse_and_industry_inspection_preserve_parent_and_market(tmp_path) -> None:
    from market_leadership.application.browse_scoreboard import browse_weekly_scoreboard
    from market_leadership.application.inspect_industry import inspect_industry

    repository = ParquetSnapshotRepository(tmp_path)
    provider = FixtureProvider()
    for market_id in ("US", "JP"):
        for level in ("SECTOR", "INDUSTRY"):
            build_weekly_snapshot(
                provider,
                repository,
                snapshot_id=f"{market_id}-{level}",
                market_id=market_id,
                level=level,
                as_of=date(2026, 10, 28),
            )

    boards = browse_weekly_scoreboard(repository, ("US", "JP"))
    assert [board.market_id for board in boards] == ["US", "JP"]
    assert [board.benchmark_id for board in boards] == ["SPX", "N225"]
    assert [board.currency for board in boards] == ["USD", "JPY"]
    assert all(board.level == "SECTOR" and board.as_of == date(2026, 10, 23) for board in boards)
    assert all((board.entries["market_id"] == board.market_id).all() for board in boards)

    industry = inspect_industry(repository, market_id="US", sector_node_id="US-TECH")
    assert industry.market_id == "US"
    assert industry.parent_sector == "Information Technology"
    assert industry.benchmark_id == "SPX"
    assert industry.currency == "USD"
    assert industry.return_basis == "adjusted"
    assert industry.as_of == date(2026, 10, 23)
    assert industry.entries["name"].tolist() == ["Software"]
    assert industry.entries["parent_relative_3m"].notna().all()
    assert industry.entries["relative_3m"].notna().all()
    with pytest.raises(ValueError, match="sector"):
        inspect_industry(repository, market_id="US", sector_node_id="JP-INDUSTRIAL")


def test_weekly_browse_isolates_missing_market_snapshot(tmp_path) -> None:
    from market_leadership.application.browse_scoreboard import browse_weekly_scoreboard

    repository = ParquetSnapshotRepository(tmp_path)
    build_weekly_snapshot(
        FixtureProvider(),
        repository,
        snapshot_id="us-only",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    us, jp = browse_weekly_scoreboard(repository, ("US", "JP"))
    assert not us.entries.empty
    assert jp.entries.empty
    assert jp.unavailable_reason is not None
    assert jp.benchmark_id is None


def test_weekly_browse_marks_outdated_local_week_stale(tmp_path) -> None:
    from market_leadership.application.browse_scoreboard import browse_weekly_scoreboard

    repository = ParquetSnapshotRepository(tmp_path)
    build_weekly_snapshot(
        FixtureProvider(),
        repository,
        snapshot_id="older",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )

    current = browse_weekly_scoreboard(repository, ("US",), as_of=date(2026, 10, 28))[0]
    stale = browse_weekly_scoreboard(repository, ("US",), as_of=date(2026, 11, 4))[0]

    assert current.freshness == "CURRENT"
    assert stale.freshness == "STALE"


def test_weekly_builder_uses_published_prior_week_for_score_and_rank_deltas(tmp_path) -> None:
    repository = ParquetSnapshotRepository(tmp_path)
    provider = FixtureProvider()
    build_weekly_snapshot(
        provider,
        repository,
        snapshot_id="prior",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 23),
    )
    _, prior_tables = repository.load_weekly("prior")
    build_weekly_snapshot(
        provider,
        repository,
        snapshot_id="current",
        market_id="US",
        level="SECTOR",
        as_of=date(2026, 10, 28),
    )
    _, current_tables = repository.load_weekly("current")
    prior = prior_tables["entries"].set_index("node_id")
    current = current_tables["entries"].set_index("node_id")

    assert current["score_change"].notna().all()
    assert current["rank_change"].notna().all()
    assert current["momentum"].notna().all()
    for node_id, row in current.iterrows():
        assert row["prior_rank"] == prior.loc[node_id, "rank"]
        assert row["prior_composite"] == pytest.approx(prior.loc[node_id, "composite"])
        assert row["score_change"] == pytest.approx(
            row["composite"] - prior.loc[node_id, "composite"]
        )


def test_weekly_builder_rejects_non_fixture_input_provider(tmp_path) -> None:
    class UnverifiedProvider:
        provider_id = "unverified-live"

        def weekly_inputs(self, market_id, *, as_of):
            raise AssertionError("unverified live weekly inputs must not be requested")

    with pytest.raises(NotImplementedError, match="source rights"):
        build_weekly_snapshot(
            UnverifiedProvider(),
            ParquetSnapshotRepository(tmp_path),
            snapshot_id="not-authorized",
            market_id="US",
            level="SECTOR",
            as_of=date(2026, 10, 28),
        )


def test_offline_cli_publishes_weekly_without_changing_daily_flags(tmp_path) -> None:
    command = [
        sys.executable,
        "-m",
        "market_leadership.application.build_snapshot",
        "--weekly",
        "--provider",
        "fixture",
        "--market",
        "US",
        "--level",
        "SECTOR",
        "--as-of",
        "2026-10-28",
        "--snapshot-id",
        "us-weekly",
        "--output",
        str(tmp_path),
    ]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert built.returncode == 0, built.stderr
    assert built.stdout.strip() == "us-weekly"
    manifest, tables = ParquetSnapshotRepository(tmp_path).load_weekly("us-weekly")
    assert manifest["as_of"] == "2026-10-23"
    assert tables["entries"]["rank"].notna().all()
