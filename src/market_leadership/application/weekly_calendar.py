"""Completed local-market trading week resolution."""

from datetime import date, timedelta

import exchange_calendars as xcals  # pyright: ignore[reportMissingTypeStubs]


def latest_completed_market_week(calendar_id: str, as_of: date) -> date:
    calendar = xcals.get_calendar(calendar_id)
    monday = as_of - timedelta(days=as_of.weekday())
    for offset in (0, 7):
        start = monday - timedelta(days=offset)
        end = start + timedelta(days=4)
        sessions = calendar.sessions_in_range(start, end)
        if len(sessions) and sessions[-1].date() < as_of:
            return sessions[-1].date()
    raise ValueError(f"no completed local week is available for {calendar_id} on {as_of}")
