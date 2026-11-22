# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Choir repository on an SQL database."""

from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_name import choir_name_key
from my_beautiful_choir.choirs.choir_repository import ChoirRepository
from my_beautiful_choir.choirs.errors import ChoirNotFoundError
from my_beautiful_choir.persistence.sql.tables import choirs

_COLUMNS = (choirs.c.id, choirs.c.name, choirs.c.created_at, choirs.c.is_default)


def _choir(row: Row[*tuple[Any, ...]]) -> Choir:
    return Choir(id=row.id, name=row.name, created_at=row.created_at, is_default=row.is_default)


class SqlChoirRepository(ChoirRepository):
    """Stores the choirs in the ``choirs`` table, within the connection of a unit of work."""

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, choir: Choir) -> None:
        """Insert the choir."""
        await self._connection.execute(
            insert(choirs).values(
                id=choir.id,
                name=choir.name,
                name_key=choir_name_key(choir.name),
                is_default=choir.is_default,
                created_at=choir.created_at,
            )
        )

    async def get(self, choir_id: UUID) -> Choir:
        """Choir with this id; raises ``ChoirNotFoundError``."""
        result = await self._connection.execute(select(*_COLUMNS).where(choirs.c.id == choir_id))
        row = result.one_or_none()
        if row is None:
            raise ChoirNotFoundError(str(choir_id))
        return _choir(row)

    async def find_by_name(self, name: str) -> Choir | None:
        """Choir whose name has the same key."""
        result = await self._connection.execute(
            select(*_COLUMNS).where(choirs.c.name_key == choir_name_key(name))
        )
        row = result.one_or_none()
        return None if row is None else _choir(row)

    async def default(self) -> Choir | None:
        """The default choir, if any."""
        result = await self._connection.execute(select(*_COLUMNS).where(choirs.c.is_default))
        row = result.one_or_none()
        return None if row is None else _choir(row)

    async def list(self) -> list[Choir]:
        """Every choir, the oldest first."""
        rows = await self._connection.execute(
            select(*_COLUMNS).order_by(choirs.c.created_at, choirs.c.name_key)
        )
        return [_choir(row) for row in rows]

    async def rename(self, choir_id: UUID, name: str) -> None:
        """Change the name and its key."""
        await self._connection.execute(
            update(choirs)
            .where(choirs.c.id == choir_id)
            .values(name=name, name_key=choir_name_key(name))
        )

    async def make_default(self, choir_id: UUID) -> None:
        """Clear the previous default choir first: a single default choir is allowed."""
        await self._connection.execute(
            update(choirs).where(choirs.c.is_default).values(is_default=False)
        )
        await self._connection.execute(
            update(choirs).where(choirs.c.id == choir_id).values(is_default=True)
        )

    async def delete(self, choir_id: UUID) -> None:
        """Delete the choir; its works and scores follow (foreign keys)."""
        await self._connection.execute(delete(choirs).where(choirs.c.id == choir_id))
