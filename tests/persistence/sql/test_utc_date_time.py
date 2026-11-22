# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the UTC date column type."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.dialects import sqlite

from my_beautiful_choir.persistence.sql.utc_date_time import UtcDateTime

PARIS_WINTER = timezone(timedelta(hours=1))


def test_naive_dates_are_refused() -> None:
    with pytest.raises(ValueError, match="naive"):
        UtcDateTime().process_bind_param(datetime(2026, 11, 21, 12), sqlite.dialect())


def test_dates_are_stored_in_utc() -> None:
    stored = UtcDateTime().process_bind_param(
        datetime(2026, 11, 21, 13, tzinfo=PARIS_WINTER), sqlite.dialect()
    )
    assert stored == datetime(2026, 11, 21, 12, tzinfo=UTC)
    assert stored is not None
    assert stored.tzinfo is UTC


@pytest.mark.parametrize(
    "read",
    [
        datetime(2026, 11, 21, 12),
        datetime(2026, 11, 21, 13, tzinfo=PARIS_WINTER),
    ],
)
def test_dates_are_read_in_utc(read: datetime) -> None:
    value = UtcDateTime().process_result_value(read, sqlite.dialect())
    assert value == datetime(2026, 11, 21, 12, tzinfo=UTC)
    assert value is not None
    assert value.tzinfo is UTC


def test_null_stays_null() -> None:
    assert UtcDateTime().process_bind_param(None, sqlite.dialect()) is None
    assert UtcDateTime().process_result_value(None, sqlite.dialect()) is None
