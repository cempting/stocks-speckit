import json
from datetime import UTC, date, datetime

import pandas as pd
import pytest

from market_leadership.application.build_snapshot import build_daily_history_snapshot
from market_leadership.application.market_sessions import latest_completed_us_session
from market_leadership.application.ports import (
    ProviderCandidate,
    ProviderCapability,
    SelectionReason,
)
from market_leadership.application.request_market_data import RequestedMarketData
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository


class RequestSpy:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.requests = []
        self.forces: list[bool] = []

    def execute(self, request, *, force=False):
        self.requests.append(request)
        self.forces.append(force)
        if self.failure:
            raise self.failure
        provider = type("Provider", (), {"provider_id": "fixture"})()
        selected = ProviderCandidate(
            "fixture",
            provider,
            ProviderCapability(
                "daily_history",
                frozenset({"US"}),
                frozenset({"1d"}),
                frozenset({"USD"}),
                frozenset({"adjusted"}),
            ),
            0,
        )
        return RequestedMarketData(
            data={
                symbol: pd.DataFrame(
                    {"close": [100.0], "volume": [1000.0]},
                    index=pd.DatetimeIndex(["2026-10-23"], name="date"),
                )
                for symbol in request.identifiers
            },
            selected=selected,
            alternatives=(),
            selection_reason=SelectionReason.PROVIDER_ID,
        )


def test_daily_history_build_publishes_verified_snapshot_and_force(tmp_path):
    service = RequestSpy()
    repository = ParquetSnapshotRepository(tmp_path)

    reference = build_daily_history_snapshot(
        service,
        repository,
        snapshot_id="daily-2026-10-23",
        as_of=date(2026, 10, 23),
        symbols=("SPY", "XLB"),
        start=date(2026, 10, 1),
        force_refresh=True,
    )

    assert service.forces == [True]
    assert service.requests[0].end == date(2026, 10, 23)
    assert service.requests[0].identifiers == ("SPY", "XLB")
    assert reference == repository.reference("daily-2026-10-23")
    assert repository.load(reference.snapshot_id)["prices"].to_dict(orient="records") == [
        {"symbol": "SPY", "date": date(2026, 10, 23), "close": 100.0, "volume": 1000.0},
        {"symbol": "XLB", "date": date(2026, 10, 23), "close": 100.0, "volume": 1000.0},
    ]
    manifest = json.loads((tmp_path / reference.snapshot_id / "manifest.json").read_text())
    assert manifest["sources"][0]["source_id"] == "fixture"
    assert len(manifest["sources"][0]["checksum"]) == 64
    assert manifest["sources"][0]["checksum"] == manifest["tables"][0]["sha256"]


def test_daily_history_build_does_not_publish_after_upstream_failure(tmp_path):
    service = RequestSpy(failure=RuntimeError("upstream unavailable"))
    repository = ParquetSnapshotRepository(tmp_path)

    with pytest.raises(RuntimeError, match="upstream unavailable"):
        build_daily_history_snapshot(
            service,
            repository,
            snapshot_id="new",
            as_of=date(2026, 10, 23),
            symbols=("SPY",),
            start=date(2026, 10, 1),
        )

    assert not (tmp_path / "new").exists()


def test_daily_history_build_rejects_undercovered_data_without_publication(tmp_path):
    class UndercoveredRequest(RequestSpy):
        def execute(self, request, *, force=False):
            result = super().execute(request, force=force)
            for history in result.data.values():
                history.index = pd.DatetimeIndex(["2026-10-22"], name="date")
            return result

    repository = ParquetSnapshotRepository(tmp_path)
    with pytest.raises(ValueError, match="required session"):
        build_daily_history_snapshot(
            UndercoveredRequest(),
            repository,
            snapshot_id="undercovered",
            as_of=date(2026, 10, 23),
            symbols=("SPY",),
            start=date(2026, 10, 1),
        )

    assert not (tmp_path / "undercovered").exists()


def test_required_session_skips_weekends_holidays_and_open_sessions():
    now = datetime(2026, 10, 26, 22, tzinfo=UTC)
    assert latest_completed_us_session(date(2026, 10, 25), now=now) == date(2026, 10, 23)
    assert latest_completed_us_session(date(2026, 7, 3), now=now) == date(2026, 7, 2)
    assert latest_completed_us_session(
        date(2026, 10, 23), now=datetime(2026, 10, 23, 14, tzinfo=UTC)
    ) == date(2026, 10, 22)
    with pytest.raises(ValueError, match="future"):
        latest_completed_us_session(date(2026, 10, 27), now=now)


def test_snapshot_build_uses_resolved_session(tmp_path):
    service = RequestSpy()
    repository = ParquetSnapshotRepository(tmp_path)
    reference = build_daily_history_snapshot(
        service,
        repository,
        snapshot_id="weekend",
        as_of=date(2026, 10, 25),
        symbols=("SPY",),
        start=date(2026, 10, 1),
    )
    assert service.requests[0].end == date(2026, 10, 23)
    assert reference.as_of == date(2026, 10, 23)


def test_failed_refresh_leaves_published_snapshot_unchanged(tmp_path):
    repository = ParquetSnapshotRepository(tmp_path)
    build_daily_history_snapshot(
        RequestSpy(),
        repository,
        snapshot_id="existing",
        as_of=date(2026, 10, 23),
        symbols=("SPY",),
        start=date(2026, 10, 1),
    )
    old_reference = repository.reference("existing")
    service = RequestSpy(failure=RuntimeError("upstream unavailable"))
    with pytest.raises(RuntimeError, match="upstream unavailable"):
        build_daily_history_snapshot(
            service,
            repository,
            snapshot_id="existing",
            as_of=date(2026, 10, 23),
            symbols=("SPY",),
            start=date(2026, 10, 1),
            force_refresh=True,
        )
    assert service.forces == [True]
    assert repository.reference("existing") == old_reference


def test_snapshot_build_rejects_invalid_observation_before_publication(tmp_path):
    class InvalidRequest(RequestSpy):
        def execute(self, request, *, force=False):
            result = super().execute(request, force=force)
            result.data["SPY"].loc[:, "close"] = -1.0
            return result

    with pytest.raises(ValueError, match="invalid close"):
        build_daily_history_snapshot(
            InvalidRequest(),
            ParquetSnapshotRepository(tmp_path),
            snapshot_id="invalid",
            as_of=date(2026, 10, 23),
            symbols=("SPY",),
            start=date(2026, 10, 1),
        )
    assert not (tmp_path / "invalid").exists()
