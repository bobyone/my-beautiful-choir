# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score repository on an SQL database."""

import builtins
from collections.abc import Collection
from dataclasses import replace
from typing import Any
from uuid import UUID

from sqlalchemy import Row, case, delete, func, insert, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from my_beautiful_choir.persistence.sql.tables import score_version_counters, scores, works
from my_beautiful_choir.scores.errors import ScoreNotFoundError, StaleFinalisationError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.originating_score import OriginatingScore
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_repository import ScoreRepository
from my_beautiful_choir.scores.score_state import ScoreState

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
    scores.c.source_score_id,
    scores.c.content_origin,
    scores.c.transcription_run_id,
    scores.c.movement_number,
    scores.c.state,
    scores.c.version_number,
    scores.c.draft_revision,
    scores.c.originating_score_id,
    scores.c.originating_score_label,
    scores.c.originating_score_version,
)


def _score(row: Row[*tuple[Any, ...]]) -> Score:
    return Score(
        id=row.id,
        work_id=row.work_id,
        label=row.label,
        format=ScoreFormat(row.format),
        size=row.size,
        original_name=row.original_name,
        origin=ScoreOrigin(row.content_origin or row.origin),
        link=row.link,
        storage_key=row.storage_key,
        added_at=row.added_at,
        source_score_id=row.source_score_id,
        transcription_run_id=row.transcription_run_id,
        movement_number=row.movement_number,
        state=ScoreState(row.state),
        version_number=row.version_number,
        draft_revision=row.draft_revision,
        originating_score=(
            OriginatingScore(
                row.originating_score_id, row.originating_score_label, row.originating_score_version
            )
            if row.originating_score_id is not None
            else None
        ),
    )


class SqlScoreRepository(ScoreRepository):
    """Stores the scores in the ``scores`` table, within the connection of a unit of work."""

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, score: Score) -> Score:
        """Insert the score, numbering final scores under the caller's transaction."""
        if score.state is ScoreState.FINAL:
            score = replace(score, version_number=await self._next_version(score.work_id))
        origin = score.originating_score
        await self._connection.execute(
            insert(scores).values(
                id=score.id,
                work_id=score.work_id,
                label=score.label,
                format=score.format.value,
                size=score.size,
                original_name=score.original_name,
                # Keep the legacy column readable by the previous application.
                origin=(
                    ScoreOrigin.LOCAL_FILE.value
                    if score.origin is ScoreOrigin.TRANSCRIPTION
                    else ScoreOrigin.FILE_PICKER.value
                    if score.origin is ScoreOrigin.MUSICXML_TEXT
                    else score.origin.value
                ),
                content_origin=score.origin.value
                if score.origin in (ScoreOrigin.TRANSCRIPTION, ScoreOrigin.MUSICXML_TEXT)
                else None,
                source_score_id=score.source_score_id,
                transcription_run_id=score.transcription_run_id,
                movement_number=score.movement_number,
                link=score.link,
                storage_key=score.storage_key,
                added_at=score.added_at,
                state=score.state.value,
                version_number=score.version_number,
                draft_revision=score.draft_revision,
                originating_score_id=origin.id if origin else None,
                originating_score_label=origin.label if origin else None,
                originating_score_version=origin.version_number if origin else None,
            )
        )
        return score

    async def _next_version(self, work_id: UUID) -> int:
        counter = score_version_counters.c
        result = await self._connection.execute(
            sqlite_insert(score_version_counters)
            .values(work_id=work_id, last_number=1)
            .on_conflict_do_update(
                index_elements=[counter.work_id], set_={"last_number": counter.last_number + 1}
            )
            .returning(counter.last_number)
        )
        return int(result.scalar_one())

    async def finalise(self, score: Score) -> Score:
        """Promote the reviewed draft within the caller's write transaction."""
        version = await self._next_version(score.work_id)
        result = await self._connection.execute(
            update(scores)
            .where(
                scores.c.id == score.id,
                scores.c.work_id == score.work_id,
                scores.c.state == ScoreState.DRAFT.value,
                scores.c.draft_revision == score.draft_revision,
            )
            .values(state=ScoreState.FINAL.value, version_number=version, draft_revision=None)
            .returning(scores.c.id)
        )
        if result.scalar_one_or_none() is None:
            raise StaleFinalisationError()
        return replace(score, state=ScoreState.FINAL, version_number=version, draft_revision=None)

    async def get(self, score_id: UUID) -> Score:
        """Score with this id; raises ``ScoreNotFoundError``."""
        result = await self._connection.execute(select(*_COLUMNS).where(scores.c.id == score_id))
        row = result.one_or_none()
        if row is None:
            raise ScoreNotFoundError(score_id)
        return _score(row)

    async def list(self, work_id: UUID) -> list[Score]:
        """Scores of the work, keeping each group in numeric movement order."""
        rows = await self._connection.execute(
            select(*_COLUMNS)
            .where(scores.c.work_id == work_id)
            .order_by(
                scores.c.added_at,
                case((scores.c.movement_number.is_not(None), scores.c.transcription_run_id)),
                scores.c.movement_number,
                scores.c.label,
                scores.c.id,
            )
        )
        return [_score(row) for row in rows]

    async def list_transcriptions(self, run_id: int) -> builtins.list[Score]:
        rows = await self._connection.execute(
            select(*_COLUMNS)
            .where(scores.c.transcription_run_id == run_id)
            .order_by(scores.c.movement_number)
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

    async def counts_of_works(self, work_ids: Collection[UUID]) -> dict[UUID, int]:
        """Number of scores of each given work, in one query."""
        if not work_ids:
            return {}
        rows = await self._connection.execute(
            select(scores.c.work_id, func.count())
            .where(scores.c.work_id.in_(work_ids))
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
