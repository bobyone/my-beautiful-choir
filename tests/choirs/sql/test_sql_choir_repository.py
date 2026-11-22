# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL choir repository on a temporary SQLite file."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.errors import ChoirNotFoundError
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase

START = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)


@pytest.fixture
async def database(tmp_path: Path) -> SqlDatabase:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    return database


def _choir(name: str, minutes: int = 0, *, is_default: bool = False) -> Choir:
    return Choir(uuid4(), name, START + timedelta(minutes=minutes), is_default)


@pytest.mark.anyio
async def test_add_get_and_list(database: SqlDatabase) -> None:
    lyon, paris = _choir("Chœur de Lyon", 0, is_default=True), _choir("Ensemble", 1)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(paris)
        await unit_of_work.choirs.add(lyon)
        await unit_of_work.commit()
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.choirs.get(lyon.id) == lyon
        assert await unit_of_work.choirs.list() == [lyon, paris]
        assert await unit_of_work.choirs.default() == lyon


@pytest.mark.anyio
async def test_get_unknown_choir(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        with pytest.raises(ChoirNotFoundError):
            await unit_of_work.choirs.get(uuid4())


@pytest.mark.anyio
async def test_find_by_name_ignores_case(database: SqlDatabase) -> None:
    choir = _choir("Chœur de Lyon", is_default=True)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(choir)
        assert await unit_of_work.choirs.find_by_name(" CHŒUR DE LYON ") == choir
        assert await unit_of_work.choirs.find_by_name("Paris") is None
        assert await unit_of_work.choirs.default() == choir


@pytest.mark.anyio
async def test_no_default_without_choirs(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.choirs.default() is None
        assert await unit_of_work.choirs.list() == []


@pytest.mark.anyio
async def test_rename_updates_the_name_key(database: SqlDatabase) -> None:
    choir = _choir("Chœur", is_default=True)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(choir)
        await unit_of_work.choirs.rename(choir.id, "Ensemble")
        assert (await unit_of_work.choirs.get(choir.id)).name == "Ensemble"
        assert await unit_of_work.choirs.find_by_name("ensemble") is not None
        assert await unit_of_work.choirs.find_by_name("chœur") is None


@pytest.mark.anyio
async def test_make_default_moves_the_default(database: SqlDatabase) -> None:
    first, second = _choir("A", 0, is_default=True), _choir("B", 1)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(first)
        await unit_of_work.choirs.add(second)
        await unit_of_work.choirs.make_default(second.id)
        assert [c.is_default for c in await unit_of_work.choirs.list()] == [False, True]


@pytest.mark.anyio
async def test_delete(database: SqlDatabase) -> None:
    choir = _choir("A", is_default=True)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(choir)
        await unit_of_work.choirs.delete(choir.id)
        assert await unit_of_work.choirs.list() == []
