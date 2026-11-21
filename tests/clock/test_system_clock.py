# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the system clock."""

from datetime import UTC, datetime

from my_beautiful_choir.clock.system_clock import SystemClock


def test_now_is_the_current_utc_time() -> None:
    before = datetime.now(UTC)
    now = SystemClock().now()
    assert now.tzinfo is UTC
    assert before <= now <= datetime.now(UTC)
