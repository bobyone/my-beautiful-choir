# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the startup step preparing the data store."""

from pathlib import Path

import pytest

from my_beautiful_choir.persistence.errors import DataStoreError
from my_beautiful_choir.persistence.sql.prepare_data_store import PrepareDataStore
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase


class _FailingDatabase(SqlDatabase):
    async def migrate(self, revision: str = "head") -> None:
        raise RuntimeError("broken migration")


@pytest.mark.anyio
async def test_creates_the_directory_and_migrates(tmp_path: Path) -> None:
    data_dir = tmp_path / "a" / "b"
    database = SqlDatabase.in_directory(data_dir)
    step = PrepareDataStore(data_dir, database)
    await step.run()
    assert step.name == "prepare data store"
    assert await database.current_revision() == "0005"
    assert [path.name for path in data_dir.iterdir()] == ["my-beautiful-choir.sqlite3"]


@pytest.mark.anyio
async def test_unusable_directory_prevents_startup(tmp_path: Path) -> None:
    data_dir = tmp_path / "file"
    data_dir.write_text("not a directory", encoding="utf-8")
    with pytest.raises(DataStoreError) as raised:
        await PrepareDataStore(data_dir, SqlDatabase.in_directory(data_dir)).run()
    assert raised.value.error_code == "MBC-DATA"
    assert raised.value.exit_code == 5
    assert str(data_dir) in raised.value.message
    assert "MBC_DATA_DIR" in raised.value.remedy


@pytest.mark.anyio
async def test_failed_migration_prevents_startup(tmp_path: Path) -> None:
    with pytest.raises(DataStoreError) as raised:
        await PrepareDataStore(tmp_path, _FailingDatabase.in_directory(tmp_path)).run()
    assert raised.value.reason == "the database migration failed"
