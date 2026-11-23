# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the file storage on the local file system."""

from pathlib import Path

import pytest

from my_beautiful_choir.storage.errors import InvalidStorageKeyError, StorageError
from my_beautiful_choir.storage.file_system.local_file_storage import LocalFileStorage

KEY = "choirs/c1/scores/s1"


@pytest.fixture
def storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path / "files")


def test_in_directory_uses_the_files_subdirectory(tmp_path: Path) -> None:
    assert LocalFileStorage.in_directory(tmp_path).root == tmp_path / "files"


@pytest.mark.anyio
async def test_stores_and_reads_a_file(storage: LocalFileStorage) -> None:
    await storage.store(KEY, b"%PDF-1.7 content")
    assert await storage.exists(KEY)
    assert await storage.read(KEY) == b"%PDF-1.7 content"
    assert (storage.root / "choirs" / "c1" / "scores" / "s1").read_bytes() == b"%PDF-1.7 content"


@pytest.mark.anyio
async def test_storing_again_replaces_the_content_and_leaves_no_temporary_file(
    storage: LocalFileStorage,
) -> None:
    await storage.store(KEY, b"first")
    await storage.store(KEY, b"second")
    assert await storage.read(KEY) == b"second"
    assert [path.name for path in (storage.root / "choirs" / "c1" / "scores").iterdir()] == ["s1"]


@pytest.mark.anyio
async def test_deletes_a_file(storage: LocalFileStorage) -> None:
    await storage.store(KEY, b"content")
    await storage.delete(KEY)
    assert not await storage.exists(KEY)


@pytest.mark.anyio
async def test_deleting_a_missing_file_does_nothing(storage: LocalFileStorage) -> None:
    await storage.delete(KEY)
    assert not await storage.exists(KEY)


@pytest.mark.anyio
async def test_a_bounded_read_stops_one_byte_after_the_limit(storage: LocalFileStorage) -> None:
    await storage.store(KEY, b"0123456789")
    assert await storage.read(KEY, maximum_size=4) == b"01234"
    assert await storage.read(KEY, maximum_size=10) == b"0123456789"
    assert await storage.read(KEY, maximum_size=0) == b"0"
    with pytest.raises(StorageError):
        await storage.read("choirs/c1/scores/missing", maximum_size=4)


@pytest.mark.anyio
async def test_reading_a_missing_file_raises_a_storage_error(storage: LocalFileStorage) -> None:
    with pytest.raises(StorageError) as raised:
        await storage.read(KEY)
    assert raised.value.key == KEY


@pytest.mark.anyio
async def test_a_directory_is_not_a_stored_file(storage: LocalFileStorage) -> None:
    await storage.store(KEY, b"content")
    assert not await storage.exists("choirs/c1")


@pytest.mark.anyio
async def test_unusable_root_raises_a_storage_error(tmp_path: Path) -> None:
    root = tmp_path / "file"
    root.write_text("not a directory", encoding="utf-8")
    storage = LocalFileStorage(root)
    with pytest.raises(StorageError) as raised:
        await storage.store(KEY, b"content")
    assert raised.value.key == KEY
    assert root.read_text(encoding="utf-8") == "not a directory"


@pytest.mark.anyio
@pytest.mark.parametrize("key", ["../outside", "choirs/../../outside"])
async def test_a_key_cannot_leave_the_root(storage: LocalFileStorage, key: str) -> None:
    with pytest.raises(InvalidStorageKeyError):
        await storage.store(key, b"content")
    with pytest.raises(InvalidStorageKeyError):
        await storage.read(key)
    with pytest.raises(InvalidStorageKeyError):
        await storage.delete(key)
    with pytest.raises(InvalidStorageKeyError):
        await storage.exists(key)
    assert not storage.root.exists()
