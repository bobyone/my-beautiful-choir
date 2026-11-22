# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score repository on an SQL database."""

import builtins
from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from my_beautiful_choir.persistence.sql.tables import scores, works
from my_beautiful_choir.scores.errors import ScoreNotFoundError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_repository import ScoreRepository

_COLUMNS = (
    scores.c.id,
    scores.c.work_id,
    scores.c.label,
    scores.c.format,
    scores.c.size,
    scores.c.original_name,
    scores.c.origin,
    scores.c.link,
    scores.c.storage_key,
    scores.c.added_at,
)


def _score(row: Row[*tuple[Any, ...]]) -> Score:
    return Score(
        id=row.id,
        work_id=row.work_id,
        label=row.label,
        format=ScoreFormat(row.format),
        size=row.size,
        original_name=row.original_name,
        origin=ScoreOrigin(row.origin),
        link=row.link,
        storage_key=row.storage_key,
        added_at=row.added_at,
    )


class SqlScoreRepository(ScoreRepository):
    """Stores the scores in the ``scores`` table, within the connection of a unit of work."""

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, score: Score) -> None:
        """Insert the score."""
        await self._connection.execute(
            insert(scores).values(
                id=score.id,
                work_id=score.work_id,
                label=score.label,
                format=score.format.value,
                size=score.size,
                original_name=score.original_name,
                origin=score.origin.value,
                link=score.link,
                storage_key=score.storage_key,
                added_at=score.added_at,
            )
        )

    async def get(self, score_id: UUID) -> Score:
        """Score with this id; raises ``ScoreNotFoundError``."""
        result = await self._connection.execute(select(*_COLUMNS).where(scores.c.id == score_id))
        row = result.one_or_none()
        if row is None:
            raise ScoreNotFoundError(score_id)
        return _score(row)

    async def list(self, work_id: UUID) -> list[Score]:
        """Scores of the work, by date added then label."""
        rows = await self._connection.execute(
            select(*_COLUMNS)
            .where(scores.c.work_id == work_id)
            .order_by(scores.c.added_at, scores.c.label, scores.c.id)
        )
        return [_score(row) for row in rows]

    async def list_of_choir(self, choir_id: UUID) -> builtins.list[Score]:
        """Read every score of the choir in a single query."""
        rows = await self._connection.execute(
            select(*_COLUMNS)
            .join(works, works.c.id == scores.c.work_id)
            .where(works.c.choir_id == choir_id)
        )
        return [_score(row) for row in rows]

    async def counts_of_choir(self, choir_id: UUID) -> dict[UUID, int]:
        """Number of scores per work of the choir, in one query."""
        rows = await self._connection.execute(
            select(scores.c.work_id, func.count())
            .join(works, works.c.id == scores.c.work_id)
            .where(works.c.choir_id == choir_id)
            .group_by(scores.c.work_id)
        )
        return {work_id: count for work_id, count in rows}

    async def delete(self, score_id: UUID) -> None:
        """Delete the score."""
        await self._connection.execute(delete(scores).where(scores.c.id == score_id))

    async def storage_keys_of_work(self, work_id: UUID) -> builtins.list[str]:
        """Storage keys of the scores of the work."""
        result = await self._connection.execute(
            select(scores.c.storage_key).where(scores.c.work_id == work_id)
        )
        return list(result.scalars())

    async def storage_keys_of_choir(self, choir_id: UUID) -> builtins.list[str]:
        """Storage keys of the scores of the works of the choir."""
        result = await self._connection.execute(
            select(scores.c.storage_key)
            .join(works, works.c.id == scores.c.work_id)
            .where(works.c.choir_id == choir_id)
        )
        return list(result.scalars())
