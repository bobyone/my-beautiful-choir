# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the removal of stored contents."""

import pytest

from my_beautiful_choir.deletion.stored_contents import remove_stored_contents
from my_beautiful_choir.storage.errors import StorageError
from tests.score_doubles import InMemoryFileStorage


class _PartlyLockedStorage(InMemoryFileStorage):
    async def delete(self, key: str) -> None:
        if key == "locked":
            raise StorageError(key, "locked")
        await super().delete(key)


@pytest.mark.anyio
async def test_removes_every_content_and_logs_those_left(
    caplog: pytest.LogCaptureFixture,
) -> None:
    storage = _PartlyLockedStorage()
    storage.files = {"first": b"1", "locked": b"2", "last": b"3", "kept": b"4"}
    await remove_stored_contents(storage, ["first", "locked", "last", "missing"])
    assert storage.files == {"locked": b"2", "kept": b"4"}
    [record] = caplog.records
    assert record.getMessage() == "A stored content could not be deleted and is left"
    assert record.__dict__["key"] == "locked"
