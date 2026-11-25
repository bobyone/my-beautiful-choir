# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Period value object."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Self

from my_beautiful_choir.events.errors import InvalidPeriodError

_OUT_OF_RANGE = "it is outside the supported dates; give both bounds explicitly"


def _utc(bound: str, moment: datetime) -> datetime:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise InvalidPeriodError(f"the {bound} must include a time zone offset")
    try:
        return moment.astimezone(UTC)
    except OverflowError:
        raise InvalidPeriodError(f"the {bound} is outside the supported dates") from None


@dataclass(frozen=True)
class Period:
    """Time interval, both bounds included, in UTC, used to list events."""

    start: datetime
    end: datetime

    def overlaps(self, starts_at: datetime, ends_at: datetime | None) -> bool:
        """Whether an event overlaps the period; without an end it is an instant."""
        return starts_at <= self.end and (ends_at or starts_at) >= self.start

    @classmethod
    def resolve(
        cls,
        start: datetime | None,
        end: datetime | None,
        *,
        now: datetime,
        default_days: int,
        maximum_days: int,
    ) -> Self:
        """The requested period, completed with the default length.

        Without bounds the period starts now. With one bound, the other one is
        ``default_days`` away from it.

        Raises:
            InvalidPeriodError: if a bound has no time zone offset, the end is
                before the start or the period exceeds ``maximum_days``.
        """
        length = timedelta(days=default_days)
        first = None if start is None else _utc("start", start)
        last = None if end is None else _utc("end", end)
        try:
            if first is None:
                first = now.astimezone(UTC) if last is None else last - length
            if last is None:
                last = first + length
        except OverflowError:
            raise InvalidPeriodError(_OUT_OF_RANGE) from None
        if last < first:
            raise InvalidPeriodError("the end must not be before the start")
        if last - first > timedelta(days=maximum_days):
            raise InvalidPeriodError(f"it must not exceed {maximum_days} days")
        return cls(first, last)
