# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""SQL persistence for completed transcription runs."""

from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from my_beautiful_choir.persistence.sql.tables import transcription_runs
from my_beautiful_choir.scores.recognition.transcription_run import TranscriptionRun
from my_beautiful_choir.scores.recognition.transcription_run_repository import (
    TranscriptionRunRepository,
)


class SqlTranscriptionRunRepository(TranscriptionRunRepository):
    """Persist runs using the connection shared by the unit of work."""

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(
        self, work_id: UUID, source_score_id: UUID, movement_count: int
    ) -> TranscriptionRun:
        result = await self._connection.execute(
            insert(transcription_runs)
            .values(work_id=work_id, source_score_id=source_score_id, movement_count=movement_count)
            .returning(transcription_runs.c.id)
        )
        return TranscriptionRun(result.scalar_one(), work_id, source_score_id, movement_count)

    async def latest(self, source_score_id: UUID) -> TranscriptionRun | None:
        result = await self._connection.execute(
            select(transcription_runs)
            .where(transcription_runs.c.source_score_id == source_score_id)
            .order_by(transcription_runs.c.id.desc())
            .limit(1)
        )
        row = result.one_or_none()
        return (
            TranscriptionRun(row.id, row.work_id, row.source_score_id, row.movement_count)
            if row is not None
            else None
        )
