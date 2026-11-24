# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Manage background transcription and record the output with its source."""

import asyncio
import logging
from collections import OrderedDict
from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_text
from my_beautiful_choir.scores.recognition.errors import (
    RecognitionError,
    TranscriptionNotFoundError,
    UnsupportedSourceScoreError,
)
from my_beautiful_choir.scores.recognition.score_recognizer import ScoreRecognizer
from my_beautiful_choir.scores.recognition.transcription_job import TranscriptionJob
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.musicxml_score_source import MusicXmlScoreSource

_LOGGER = logging.getLogger(__name__)
_JOB_LIMIT = 32


class TranscriptionService:
    """Coordinate PDF transcription without keeping the MCP request open."""

    def __init__(
        self, scores: ScoreService, recognizer: ScoreRecognizer, authorization: Authorization
    ) -> None:
        self._scores = scores
        self._recognizer = recognizer
        self._authorization = authorization
        self._jobs: OrderedDict[UUID, TranscriptionJob] = OrderedDict()
        self._running: dict[UUID, TranscriptionJob] = {}
        self._worker = asyncio.Lock()
        self._job_registry = asyncio.Lock()

    async def start(self, source_id: UUID, recompute: bool = False) -> TranscriptionJob:
        """Return a stored transcription, join an in-flight job, or schedule a new one."""
        work, source = await self._scores.describe_score(source_id)
        self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
        if source.format is not ScoreFormat.PDF:
            raise UnsupportedSourceScoreError("Choose a stored PDF score to transcribe.")
        async with self._job_registry:
            if job := self._running.get(source.id):
                return job
            existing = await self._scores.list_scores(work.id) if not recompute else ()
            if score := next(
                (item for item in reversed(existing) if item.source_score_id == source_id), None
            ):
                return TranscriptionJob(uuid4(), source.id, score=score)
            self._make_room()
            job = TranscriptionJob(uuid4(), source.id, recompute=recompute)
            self._jobs[job.id] = job
            self._running[source.id] = job
            job.task = asyncio.create_task(self._transcribe(job))
            return job

    def status(self, job_id: UUID) -> TranscriptionJob:
        """Return the status of a recent transcription."""
        try:
            return self._jobs[job_id]
        except KeyError as error:
            raise TranscriptionNotFoundError(
                "Transcription status expired. Ask to transcribe the PDF again."
            ) from error

    def _make_room(self) -> None:
        if len(self._jobs) < _JOB_LIMIT:
            return
        for job_id, job in self._jobs.items():
            if job.task is not None and job.task.done():
                del self._jobs[job_id]
                return
        raise RecognitionError("Too many transcriptions are queued. Wait for one to finish.")

    async def _transcribe(self, job: TranscriptionJob) -> None:
        try:
            async with self._worker:
                work, _, pdf = await self._scores.read_score(job.source_id)
                xml = await self._recognizer.transcribe(pdf)
                await asyncio.to_thread(musicxml_text, xml)
                score_source = MusicXmlScoreSource(
                    xml, "Transcription.musicxml", ScoreOrigin.TRANSCRIPTION
                )
                _, job.score = await self._scores.add_score(
                    work.id,
                    score_source,
                    source_score_id=job.source_id,
                    reuse_transcription=not job.recompute,
                )
        except RecognitionError as error:
            job.error = error
        except DomainError:
            job.error = RecognitionError(
                "The transcription could not be saved. Check the source PDF and try again."
            )
        except Exception as error:
            _LOGGER.error(
                "Unexpected transcription failure", extra={"exception_type": type(error).__name__}
            )
            job.error = RecognitionError(
                "Transcription failed. Check the installation and try again."
            )
        finally:
            async with self._job_registry:
                self._running.pop(job.source_id, None)
