"""Determine the most recent completed US exchange session for a request."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from market_leadership.application.exchange_calendar import get_calendar


def latest_completed_us_session(as_of: date, *, now: datetime | None = None) -> date:
    current = datetime.now(UTC) if now is None else now
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("current time must be timezone-aware")
    if as_of > current.astimezone(ZoneInfo("America/New_York")).date():
        raise ValueError("as-of date cannot be in the future")
    calendar = get_calendar("XNYS")
    session = calendar.date_to_session(as_of.isoformat(), direction="previous")
    if current < calendar.session_close(session).to_pydatetime():
        session = calendar.previous_session(session)
    return session.date()
