# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL unit of work on a temporary SQLite file."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, insert, select

from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.persistence.sql.sql_unit_of_work import SqlUnitOfWork
from my_beautiful_choir.persistence.sql.tables import choirs


@pytest.fixture
async def database(tmp_path: Path) -> SqlDatabase:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    return database


async def _add_choir(unit_of_work: SqlUnitOfWork, name: str) -> None:
    await unit_of_work.connection.execute(
        insert(choirs),
        [
            {
                "id": uuid4(),
                "name": name,
                "name_key": name.casefold(),
                "is_default": False,
                "created_at": datetime.now(UTC),
            }
        ],
    )


async def _count(database: SqlDatabase) -> int:
    async with database.unit_of_work() as unit_of_work:
        result = await unit_of_work.connection.execute(select(func.count()).select_from(choirs))
        return int(result.scalar_one())


@pytest.mark.anyio
async def test_committed_changes_are_kept(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        await _add_choir(unit_of_work, "A")
        await unit_of_work.commit()
        await _add_choir(unit_of_work, "B")
        await unit_of_work.commit()
    assert await _count(database) == 2


@pytest.mark.anyio
async def test_uncommitted_changes_are_discarded(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        await _add_choir(unit_of_work, "A")
        await unit_of_work.commit()
        await _add_choir(unit_of_work, "B")
    assert await _count(database) == 1


async def _add_then_fail(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        await _add_choir(unit_of_work, "A")
        raise RuntimeError("failure")


@pytest.mark.anyio
async def test_an_exception_discards_the_changes(database: SqlDatabase) -> None:
    with pytest.raises(RuntimeError):
        await _add_then_fail(database)
    assert await _count(database) == 0


def test_connection_is_unavailable_outside_the_block(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not started"):
        _ = SqlDatabase.in_directory(tmp_path).unit_of_work().connection
