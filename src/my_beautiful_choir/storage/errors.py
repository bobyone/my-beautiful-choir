# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the storage notion."""

from my_beautiful_choir.errors import MyBeautifulChoirError


class StorageError(MyBeautifulChoirError):
    """A file cannot be stored, read or deleted."""

    def __init__(self, key: str, reason: str) -> None:
        super().__init__(f"the stored file {key!r} cannot be used: {reason}")
        self.key = key
        self.reason = reason


class InvalidStorageKeyError(StorageError, ValueError):
    """A storage key does not follow the expected form; this is a programming error."""

    def __init__(self, key: str) -> None:
        super().__init__(
            key,
            "a key is made of segments separated by '/', each of letters, digits, '-' or '_'",
        )
