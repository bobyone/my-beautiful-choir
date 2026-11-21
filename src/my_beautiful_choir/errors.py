# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Root exceptions of my-beautiful-choir."""

from typing import ClassVar


class MyBeautifulChoirError(Exception):
    """Base class of every exception raised by my-beautiful-choir."""


class StartupError(MyBeautifulChoirError):
    """An error preventing the application from starting.

    Each subclass defines a stable error code, shown to the user, and the exit
    code of the process.
    """

    error_code: ClassVar[str] = "MBC-STARTUP"
    exit_code: ClassVar[int] = 1

    def __init__(self, message: str, remedy: str) -> None:
        super().__init__(message)
        self.message = message
        self.remedy = remedy
