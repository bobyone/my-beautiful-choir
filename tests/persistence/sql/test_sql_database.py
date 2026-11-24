# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL database on a temporary SQLite file."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Connection, insert, inspect, select, text
from sqlalchemy.exc import IntegrityError

from my_beautiful_choir.persistence.sql.sql_database import DATABASE_FILE_NAME, SqlDatabase
from my_beautiful_choir.persistence.sql.tables import choirs, metadata

NOW = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)


@pytest.fixture
async def database(tmp_path: Path) -> SqlDatabase:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    return database


def _choir(name: str, *, is_default: bool) -> dict[str, object]:
    return {
        "id": uuid4(),
        "name": name,
        "name_key": name.casefold(),
        "is_default": is_default,
        "created_at": NOW,
    }


@pytest.mark.anyio
async def test_in_directory_uses_the_database_file(tmp_path: Path) -> None:
    await SqlDatabase.in_directory(tmp_path).migrate()
    assert (tmp_path / DATABASE_FILE_NAME).is_file()


@pytest.mark.anyio
async def test_migration_creates_the_schema_of_the_tables(database: SqlDatabase) -> None:
    def differences(connection: Connection) -> list[object]:
        return list(compare_metadata(MigrationContext.configure(connection), metadata))

    assert await database.current_revision() == "0002"
    async with database.engine.connect() as connection:
        assert await connection.run_sync(differences) == []


@pytest.mark.anyio
async def test_downgrade_removes_everything(database: SqlDatabase) -> None:
    await database.downgrade("base")
    assert await database.current_revision() is None
    async with database.engine.connect() as connection:
        names = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    assert set(names) <= {"alembic_version"}


@pytest.mark.anyio
async def test_migrating_twice_changes_nothing(database: SqlDatabase) -> None:
    await database.migrate()
    assert await database.current_revision() == "0002"


@pytest.mark.anyio
async def test_foreign_keys_are_enforced(database: SqlDatabase) -> None:
    async with database.engine.connect() as connection:
        assert (await connection.execute(text("PRAGMA foreign_keys"))).scalar() == 1


@pytest.mark.anyio
async def test_a_single_choir_can_be_the_default_one(database: SqlDatabase) -> None:
    async with database.engine.begin() as connection:
        await connection.execute(insert(choirs), [_choir("A", is_default=True)])
        await connection.execute(insert(choirs), [_choir("B", is_default=False)])
        await connection.execute(insert(choirs), [_choir("C", is_default=False)])
    with pytest.raises(IntegrityError):
        async with database.engine.begin() as connection:
            await connection.execute(insert(choirs), [_choir("D", is_default=True)])


@pytest.mark.anyio
async def test_dates_are_read_back_in_utc(database: SqlDatabase) -> None:
    async with database.engine.begin() as connection:
        await connection.execute(insert(choirs), [_choir("A", is_default=True)])
    async with database.engine.connect() as connection:
        created_at = (await connection.execute(select(choirs.c.created_at))).scalar_one()
    assert created_at == NOW
    assert created_at.tzinfo is UTC
    await database.dispose()
