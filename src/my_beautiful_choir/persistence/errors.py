# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the persistence notion."""

from pathlib import Path
from typing import ClassVar

from my_beautiful_choir.errors import MyBeautifulChoirError, StartupError


class PersistenceError(MyBeautifulChoirError):
    """Base class of the errors related to the data store."""


class DataStoreError(PersistenceError, StartupError):
    """The data store cannot be prepared: the application cannot start."""

    error_code: ClassVar[str] = "MBC-DATA"
    exit_code: ClassVar[int] = 5

    def __init__(self, data_dir: Path, reason: str) -> None:
        super().__init__(
            message=f"the data directory {data_dir} cannot be used: {reason}.",
            remedy=(
                "Check that the directory can be created and written by your user, or choose "
                "another one with MBC_DATA_DIR. If a migration failed, restore your last backup "
                "and report the problem."
            ),
        )
        self.data_dir = data_dir
        self.reason = reason
