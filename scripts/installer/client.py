# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Desktop client registration contract."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from scripts.installer.launcher import Launcher

SERVER_NAME = "my-beautiful-choir"


class ClientRegistration(ABC):
    """A registration for the personal-mode server in a desktop client."""

    @abstractmethod
    def register(self, launcher: Launcher, confirm_replace: Callable[[], bool]) -> None:
        """Keep or register the launcher. Request agreement before a conflicting replacement."""
