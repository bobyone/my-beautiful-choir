# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the period used to list events."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from my_beautiful_choir.events.errors import InvalidPeriodError
from my_beautiful_choir.events.period import Period

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)
PARIS = timezone(timedelta(hours=1))


def _resolve(start: datetime | None, end: datetime | None) -> Period:
    return Period.resolve(start, end, now=NOW, default_days=92, maximum_days=366)


def test_without_bounds_the_period_starts_now() -> None:
    assert _resolve(None, None) == Period(NOW, NOW + timedelta(days=92))


def test_a_start_alone_gets_the_default_length() -> None:
    start = datetime(2027, 1, 1, tzinfo=UTC)
    assert _resolve(start, None) == Period(start, start + timedelta(days=92))


def test_an_end_alone_gets_the_default_length_before_it() -> None:
    end = datetime(2027, 1, 1, tzinfo=UTC)
    assert _resolve(None, end) == Period(end - timedelta(days=92), end)


def test_bounds_are_converted_to_utc() -> None:
    period = _resolve(datetime(2027, 1, 1, 1, tzinfo=PARIS), datetime(2027, 2, 1, tzinfo=PARIS))
    assert period.start == datetime(2027, 1, 1, tzinfo=UTC)
    assert period.start.tzinfo is UTC


def test_a_period_of_exactly_the_maximum_is_accepted() -> None:
    period = _resolve(NOW, NOW + timedelta(days=366))
    assert period.end - period.start == timedelta(days=366)


@pytest.mark.parametrize(
    ("start", "end", "reason"),
    [
        (NOW, NOW - timedelta(seconds=1), "before the start"),
        (NOW, NOW + timedelta(days=366, seconds=1), "366 days"),
        (datetime(2027, 1, 1), None, "start must include a time zone"),
        (None, datetime(2027, 1, 1), "end must include a time zone"),
    ],
)
def test_invalid_periods_are_refused(
    start: datetime | None, end: datetime | None, reason: str
) -> None:
    with pytest.raises(InvalidPeriodError, match=reason):
        _resolve(start, end)


@pytest.mark.parametrize(
    ("starts_at", "ends_at", "overlaps"),
    [
        (NOW - timedelta(days=1), None, False),
        (NOW, None, True),
        (NOW + timedelta(days=10), None, True),
        (NOW + timedelta(days=10, seconds=1), None, False),
        (NOW - timedelta(days=2), NOW - timedelta(seconds=1), False),
        (NOW - timedelta(days=2), NOW, True),
        (NOW - timedelta(days=2), NOW + timedelta(days=20), True),
    ],
)
def test_overlap_includes_both_bounds(
    starts_at: datetime, ends_at: datetime | None, overlaps: bool
) -> None:
    period = Period(NOW, NOW + timedelta(days=10))
    assert period.overlaps(starts_at, ends_at) is overlaps
