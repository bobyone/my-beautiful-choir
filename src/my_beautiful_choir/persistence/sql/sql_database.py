# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""SQL database: engine, units of work and migrations."""

from importlib import resources
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import URL, Connection, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import ConnectionPoolEntry, NullPool

from my_beautiful_choir.persistence.sql.sql_unit_of_work import SqlUnitOfWork

DATABASE_FILE_NAME = "my-beautiful-choir.sqlite3"


def _enable_sqlite_foreign_keys(
    connection: DBAPIConnection, connection_record: ConnectionPoolEntry
) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class SqlDatabase:
    """A database reached through SQLAlchemy's asyncio extension (ADR 0012)."""

    def __init__(self, url: URL) -> None:
        self._url = url
        # Without a pool, no connection (and no aiosqlite thread) outlives its unit of work.
        self._engine: AsyncEngine = create_async_engine(url, poolclass=NullPool)
        if url.get_backend_name() == "sqlite":
            event.listen(self._engine.sync_engine, "connect", _enable_sqlite_foreign_keys)

    @classmethod
    def sqlite_file(cls, path: Path) -> "SqlDatabase":
        """Database stored in the SQLite file ``path``."""
        return cls(URL.create("sqlite+aiosqlite", database=str(path)))

    @classmethod
    def in_directory(cls, data_dir: Path) -> "SqlDatabase":
        """SQLite database of personal mode, in the data directory."""
        return cls.sqlite_file(data_dir / DATABASE_FILE_NAME)

    @property
    def engine(self) -> AsyncEngine:
        """Engine of the database."""
        return self._engine

    def unit_of_work(self) -> SqlUnitOfWork:
        """New unit of work: one transaction."""
        return SqlUnitOfWork(self._engine)

    async def migrate(self, revision: str = "head") -> None:
        """Upgrade (or downgrade) the schema to ``revision``."""
        async with self._engine.begin() as connection:
            await connection.run_sync(_run_alembic, "upgrade", revision)

    async def downgrade(self, revision: str) -> None:
        """Downgrade the schema to ``revision`` (``base`` removes everything)."""
        async with self._engine.begin() as connection:
            await connection.run_sync(_run_alembic, "downgrade", revision)

    async def current_revision(self) -> str | None:
        """Revision of the schema, or None when the database is empty."""
        async with self._engine.connect() as connection:
            return await connection.run_sync(
                lambda sync: MigrationContext.configure(sync).get_current_revision()
            )

    async def dispose(self) -> None:
        """Close every connection."""
        await self._engine.dispose()


def _alembic_config(connection: Connection) -> Config:
    config = Config()
    location = resources.files("my_beautiful_choir.persistence.sql") / "migrations"
    config.set_main_option("script_location", str(location))
    config.attributes["connection"] = connection
    return config


def _run_alembic(connection: Connection, operation: str, revision: str) -> None:
    config = _alembic_config(connection)
    if operation == "upgrade":
        command.upgrade(config, revision)
    else:
        command.downgrade(config, revision)
