# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""File storage abstraction."""

import re
from abc import ABC, abstractmethod

from my_beautiful_choir.storage.errors import InvalidStorageKeyError

_KEY_PATTERN = re.compile(r"[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*")


def check_storage_key(key: str) -> str:
    """Return ``key`` if it is a valid storage key, such as ``choirs/<id>/scores/<id>``.

    A key is made of segments separated by ``/``, each of ASCII letters,
    digits, ``-`` or ``_``: it can never designate a place outside the storage.
    Raises ``InvalidStorageKeyError`` otherwise.
    """
    if _KEY_PATTERN.fullmatch(key) is None:
        raise InvalidStorageKeyError(key)
    return key


class FileStorage(ABC):
    """Keeps the content of files under keys, such as ``choirs/<id>/scores/<id>``.

    Keys are checked with ``check_storage_key``; an invalid key raises
    ``InvalidStorageKeyError``. Any other failure raises ``StorageError``.
    """

    @abstractmethod
    async def store(self, key: str, content: bytes) -> None:
        """Store ``content`` under ``key``, replacing any previous content, atomically."""

    @abstractmethod
    async def read(self, key: str) -> bytes:
        """Content stored under ``key``; raises ``StorageError`` if there is none."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the content stored under ``key``; does nothing if there is none."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Whether content is stored under ``key``."""
