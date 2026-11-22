# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Clock abstraction."""

from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """Gives the current date and time, so that tests can fix it."""

    @abstractmethod
    def now(self) -> datetime:
        """Current date and time, timezone-aware, in UTC."""
