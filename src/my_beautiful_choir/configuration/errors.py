# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the configuration notion."""

from dataclasses import dataclass
from typing import ClassVar

from my_beautiful_choir.errors import StartupError


@dataclass(frozen=True)
class ConfigurationIssue:
    """One invalid configuration entry: its key, as the user writes it, and what is expected."""

    key: str
    message: str


class ConfigurationError(StartupError):
    """The configuration is invalid; the application cannot start."""

    error_code: ClassVar[str] = "MBC-CONFIG"
    exit_code: ClassVar[int] = 2

    def __init__(self, issues: tuple[ConfigurationIssue, ...]) -> None:
        super().__init__(
            message="invalid configuration.",
            remedy="Fix the values listed above, then restart.",
        )
        self.issues = issues
