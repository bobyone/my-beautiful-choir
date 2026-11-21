# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Work repository on an SQL database."""

from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from my_beautiful_choir.persistence.sql.tables import works
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.repertoire.work_repository import WorkRepository
from my_beautiful_choir.repertoire.work_rules import search_text

_COLUMNS = (
    works.c.id,
    works.c.choir_id,
    works.c.title,
    works.c.composer,
    works.c.arranger,
    works.c.voicing,
    works.c.sung_languages,
    works.c.notes,
    works.c.created_at,
    works.c.updated_at,
)


def _work(row: Row[*tuple[Any, ...]]) -> Work:
    details = WorkDetails(
        title=row.title,
        composer=row.composer,
        arranger=row.arranger,
        voicing=row.voicing,
        sung_languages=tuple(row.sung_languages),
        notes=row.notes,
    )
    return Work(row.id, row.choir_id, details, row.created_at, row.updated_at)


def _values(work: Work) -> dict[str, object]:
    details = work.details
    return {
        "title": details.title,
        "title_search": search_text(details.title),
        "composer": details.composer,
        "composer_search": search_text(details.composer),
        "arranger": details.arranger,
        "voicing": details.voicing,
        "sung_languages": list(details.sung_languages),
        "notes": details.notes,
        "updated_at": work.updated_at,
    }


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SqlWorkRepository(WorkRepository):
    """Stores the works in the ``works`` table, within the connection of a unit of work.

    The normalized search columns are computed on every write (ADR 0012).
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, work: Work) -> None:
        """Insert the work."""
        await self._connection.execute(
            insert(works).values(
                id=work.id, choir_id=work.choir_id, created_at=work.created_at, **_values(work)
            )
        )

    async def get(self, work_id: UUID) -> Work:
        """Work with this id; raises ``WorkNotFoundError``."""
        result = await self._connection.execute(select(*_COLUMNS).where(works.c.id == work_id))
        row = result.one_or_none()
        if row is None:
            raise WorkNotFoundError(work_id)
        return _work(row)

    async def search(self, choir_id: UUID, text: str | None = None) -> list[Work]:
        """Works of the choir matching ``text`` on the normalized columns."""
        query = select(*_COLUMNS).where(works.c.choir_id == choir_id)
        normalized = search_text(text)
        if normalized:
            pattern = f"%{_escape_like(normalized)}%"
            query = query.where(
                or_(
                    works.c.title_search.like(pattern, escape="\\"),
                    works.c.composer_search.like(pattern, escape="\\"),
                )
            )
        rows = await self._connection.execute(query)
        return [_work(row) for row in rows]

    async def update(self, work: Work) -> None:
        """Replace the details and the modification date."""
        await self._connection.execute(
            update(works).where(works.c.id == work.id).values(**_values(work))
        )

    async def delete(self, work_id: UUID) -> None:
        """Delete the work; its scores follow (foreign keys)."""
        await self._connection.execute(delete(works).where(works.c.id == work_id))

    async def count(self, choir_id: UUID) -> int:
        """Number of works of the choir."""
        result = await self._connection.execute(
            select(func.count()).select_from(works).where(works.c.choir_id == choir_id)
        )
        return int(result.scalar_one())
