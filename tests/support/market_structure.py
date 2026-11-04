"""Controlled acquisition, HTTP, time and process evidence for service/cache tests."""

import fcntl
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd


@dataclass
class FrozenClock:
    current: datetime

    def __post_init__(self) -> None:
        if self.current.tzinfo is None or self.current.utcoffset() != timedelta():
            raise ValueError("Controlled clock requires an aware UTC datetime")

    def __call__(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


def append_call(path: Path, record: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(record, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


class RecordingProvider:
    provider_id = "yfinance"

    def __init__(
        self, frames: dict[str, pd.DataFrame], *, ledger: Path,
    ) -> None:
        self.frames = frames
        self.ledger = ledger
        self.error: Exception | None = None

    def fetch_daily_history(
        self, symbols: tuple[str, ...], *, start: date, end: date, force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        append_call(self.ledger, {
            "symbols": list(symbols), "start": start.isoformat(), "end": end.isoformat(),
            "force": force,
        })
        if self.error is not None:
            raise self.error
        return {
            symbol: frame.loc[start.isoformat():end.isoformat()].copy()
            for symbol in symbols if (frame := self.frames.get(symbol)) is not None
        }


def recording_transport(
    handler: Callable[[httpx.Request], httpx.Response], paths: list[str],
) -> httpx.MockTransport:
    def send(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return handler(request)

    return httpx.MockTransport(send)
