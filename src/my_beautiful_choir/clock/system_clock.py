# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Clock of the system."""

from datetime import UTC, datetime

from my_beautiful_choir.clock.clock import Clock


class SystemClock(Clock):
    """Reads the system clock."""

    def now(self) -> datetime:
        """Current date and time of the system, in UTC."""
        return datetime.now(UTC)
