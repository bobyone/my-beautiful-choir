# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Startup step abstraction."""

from abc import ABC, abstractmethod


class StartupStep(ABC):
    """Something to do before serving, such as preparing the data store."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short English name, for the logs."""

    @abstractmethod
    async def run(self) -> None:
        """Do the step.

        Raises:
            StartupError: if the application cannot start.
        """
