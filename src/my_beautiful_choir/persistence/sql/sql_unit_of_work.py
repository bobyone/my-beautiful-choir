# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Unit of Work on an SQL database."""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncTransaction

from my_beautiful_choir.choirs.sql.sql_choir_repository import SqlChoirRepository
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork


class SqlUnitOfWork(UnitOfWork):
    """One database transaction; the repositories share its connection."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._connection: AsyncConnection | None = None
        self._transaction: AsyncTransaction | None = None

    @property
    def connection(self) -> AsyncConnection:
        """Connection of the current transaction.

        Raises:
            RuntimeError: outside the ``async with`` block.
        """
        if self._connection is None:
            raise RuntimeError("The unit of work is not started")
        return self._connection

    @property
    def choirs(self) -> SqlChoirRepository:
        """Choirs, in the transaction of this unit of work."""
        return SqlChoirRepository(self.connection)

    async def __aenter__(self) -> Self:
        """Open a connection and begin a transaction."""
        self._connection = await self._engine.connect()
        self._transaction = await self._connection.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back what was not committed, then close the connection."""
        try:
            if self._transaction is not None and self._transaction.is_active:
                await self._transaction.rollback()
        finally:
            if self._connection is not None:
                await self._connection.close()
            self._connection = None
            self._transaction = None

    async def commit(self) -> None:
        """Commit the transaction, and begin a new one for the following changes."""
        connection = self.connection
        if self._transaction is not None:
            await self._transaction.commit()
        self._transaction = await connection.begin()
