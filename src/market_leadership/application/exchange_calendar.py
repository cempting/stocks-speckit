"""Typed boundary for the untyped exchange-calendars factory."""

from datetime import date
from importlib import import_module
from typing import Protocol, cast

import pandas as pd


class ExchangeCalendar(Protocol):
    def sessions_in_range(self, start: date | str, end: date | str) -> pd.DatetimeIndex: ...

    def date_to_session(self, date: str, direction: str = "none") -> pd.Timestamp: ...

    def session_close(self, session: pd.Timestamp) -> pd.Timestamp: ...

    def previous_session(self, session: pd.Timestamp) -> pd.Timestamp: ...


class _CalendarFactory(Protocol):
    def get_calendar(self, name: str) -> ExchangeCalendar: ...


_calendars = cast(_CalendarFactory, import_module("exchange_calendars"))


def get_calendar(name: str) -> ExchangeCalendar:
    return _calendars.get_calendar(name)
