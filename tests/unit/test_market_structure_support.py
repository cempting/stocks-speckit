import json
import multiprocessing
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd
import pytest

from market_leadership.application.ports import MarketDataProvider
from tests.support.market_structure import (
    FrozenClock,
    RecordingProvider,
    append_call,
    recording_transport,
)


def test_clock_and_partial_failed_provider_outcomes(tmp_path: Path) -> None:
    clock = FrozenClock(datetime(2026, 11, 4, tzinfo=UTC))
    clock.advance(timedelta(seconds=300))
    assert clock() == datetime(2026, 11, 4, 0, 5, tzinfo=UTC)
    frame = pd.DataFrame(
        {"Close": [1.0, 2.0], "Volume": [10, 20]},
        index=pd.date_range("2026-11-02", periods=2),
    )
    ledger = tmp_path / "calls.jsonl"
    recording = RecordingProvider({"TEST": frame}, ledger=ledger)
    provider: MarketDataProvider = recording
    result = provider.fetch_daily_history(
        ("TEST", "MISSING"), start=date(2026, 11, 3), end=date(2026, 11, 3),
    )
    assert list(result) == ["TEST"]
    assert result["TEST"]["Close"].tolist() == [2.0]
    recording.error = RuntimeError("controlled provider failure")
    with pytest.raises(RuntimeError, match="controlled provider failure"):
        provider.fetch_daily_history(
            ("TEST",), start=date(2026, 11, 3), end=date(2026, 11, 3),
        )
    calls = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert len(calls) == 2
    assert calls[0]["symbols"] == ["TEST", "MISSING"]
    assert calls[0]["start"] == calls[0]["end"] == "2026-11-03"


def test_empty_provider_response_is_not_invented_coverage(tmp_path: Path) -> None:
    provider = RecordingProvider({}, ledger=tmp_path / "empty-calls.jsonl")
    assert provider.fetch_daily_history(
        ("MISSING",), start=date(2026, 11, 3), end=date(2026, 11, 3),
    ) == {}


@pytest.mark.parametrize("current", [
    datetime(2026, 11, 4), datetime(2026, 11, 4, tzinfo=timezone(timedelta(hours=1))),
])
def test_clock_rejects_non_utc_values(current: datetime) -> None:
    with pytest.raises(ValueError, match="aware UTC"):
        FrozenClock(current)


def test_transport_records_paths_and_injects_errors_without_network() -> None:
    paths: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/fail":
            raise httpx.ReadTimeout("controlled timeout", request=request)
        return httpx.Response(200, json={"controlled": True})

    with httpx.Client(transport=recording_transport(respond, paths)) as client:
        assert client.get("https://example.invalid/ok").json() == {"controlled": True}
        with pytest.raises(httpx.ReadTimeout):
            client.get("https://example.invalid/fail")
    assert paths == ["/ok", "/fail"]


def test_process_ledger_records_concurrent_calls(tmp_path: Path) -> None:
    context = multiprocessing.get_context("spawn")
    ledger = tmp_path / "process-calls.jsonl"
    processes = [
        context.Process(target=append_call, args=(ledger, {"worker": i})) for i in range(4)
    ]
    try:
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=30)
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=10)
    calls = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert sorted(record["worker"] for record in calls) == [0, 1, 2, 3]
