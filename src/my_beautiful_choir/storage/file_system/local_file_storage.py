# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""File storage in a directory of the local file system."""

import asyncio
import os
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from my_beautiful_choir.storage.errors import StorageError
from my_beautiful_choir.storage.file_storage import FileStorage, check_storage_key

FILES_DIRECTORY_NAME = "files"


class LocalFileStorage(FileStorage):
    """Each key is a file under the root directory; its segments are subdirectories.

    Directories are created when needed. Writing goes through a temporary file
    in the same directory, then a rename, so that a stored file is never left
    half written. File system calls run in a worker thread, not to block the
    event loop with large files.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    @classmethod
    def in_directory(cls, data_dir: Path) -> "LocalFileStorage":
        """File storage of personal mode, in the ``files`` subdirectory of the data directory."""
        return cls(data_dir / FILES_DIRECTORY_NAME)

    @property
    def root(self) -> Path:
        """Directory holding the stored files."""
        return self._root

    async def store(self, key: str, content: bytes) -> None:
        path = self._path(key)
        await self._run(key, self._write, path, content)

    async def read(self, key: str, maximum_size: int | None = None) -> bytes:
        path = self._path(key)
        if maximum_size is None:
            return await self._run(key, path.read_bytes)
        return await self._run(key, self._read_at_most, path, maximum_size + 1)

    async def delete(self, key: str) -> None:
        path = self._path(key)
        await self._run(key, path.unlink, True)

    async def exists(self, key: str) -> bool:
        path = self._path(key)
        return await self._run(key, path.is_file)

    def _path(self, key: str) -> Path:
        return self._root.joinpath(*check_storage_key(key).split("/"))

    @staticmethod
    def _read_at_most(path: Path, size: int) -> bytes:
        with path.open("rb") as file:
            return file.read(size)

    @staticmethod
    def _write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_bytes(content)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    async def _run[R](key: str, function: Callable[..., R], *args: object) -> R:
        try:
            return await asyncio.to_thread(function, *args)
        except OSError as error:
            raise StorageError(key, error.strerror or type(error).__name__) from error
