# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on the scores of a work (flows G, H and I of issue #7)."""

import asyncio
from dataclasses import replace
from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.deletion.stale_confirmation_error import StaleConfirmationError
from my_beautiful_choir.deletion.stored_contents import remove_stored_contents
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork, UnitOfWorkFactory
from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.scores.errors import (
    InvalidScoreSizeError,
    ScoreFileMissingError,
    StoredScoreTooLargeError,
)
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_text
from my_beautiful_choir.scores.opening.score_opener import ScoreOpener
from my_beautiful_choir.scores.recognition.errors import (
    RecognitionError,
    UnsupportedSourceScoreError,
)
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_rules import (
    MAXIMUM_SIZE,
    original_name,
    score_label,
    storage_key,
)
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from my_beautiful_choir.storage.file_storage import FileStorage


class ScoreService(Deleter):
    """Adds, lists, reads, opens and deletes the scores of the works."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        clock: Clock,
        authorization: Authorization,
        file_storage: FileStorage,
        format_detector: ScoreFormatDetector,
        opener: ScoreOpener,
        maximum_size: int = MAXIMUM_SIZE,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._authorization = authorization
        self._file_storage = file_storage
        self._format_detector = format_detector
        self._opener = opener
        self._maximum_size = maximum_size

    async def add_score(
        self,
        work_id: UUID,
        source: ScoreSource,
        label: str | None = None,
    ) -> tuple[Work, Score]:
        """Add a score to the work, with the content given by ``source``.

        The label is the one given, otherwise the original file name without
        its extension. The content is stored before the score is saved; if
        saving fails, the stored content is removed.

        Raises:
            WorkNotFoundError: if no work has this id.
            ScoreSourceError: if the content cannot be obtained.
            InvalidScoreSizeError: if the content is empty or too large.
            UnsupportedScoreFormatError: if the content is not a supported score.
            InvalidScoreError: if the label is too long.
        """
        async with self._unit_of_work() as unit_of_work:
            work = await unit_of_work.works.get(work_id)
            self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
        # Fetch outside any transaction: a download may be long.
        score, content = await self._prepare_score(work, source, label)
        await self._file_storage.store(score.storage_key, content)
        try:
            async with self._unit_of_work() as unit_of_work:
                work = await unit_of_work.works.get(work_id)
                await unit_of_work.scores.add(score)
                await unit_of_work.commit()
        except BaseException:
            await remove_stored_contents(self._file_storage, [score.storage_key])
            raise
        return work, score

    async def latest_transcriptions(self, source_id: UUID) -> tuple[Score, ...]:
        """Return the last complete set, or an empty tuple if a movement is missing."""
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot()
            source = await unit_of_work.scores.get(source_id)
            work = await unit_of_work.works.get(source.work_id)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, work.choir_id)
            return await self._latest_complete(unit_of_work, source_id)

    async def add_transcriptions(
        self, source_id: UUID, movements: tuple[ScoreSource, ...], *, reuse: bool
    ) -> tuple[Score, ...]:
        """Validate, stage and publish all movements in one database transaction.

        An incomplete export or a storage failure cannot publish a partial run.
        A competing complete run can be reused under the write transaction.
        """
        work, source = await self.describe_score(source_id)
        self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
        if source.format is not ScoreFormat.PDF:
            raise UnsupportedSourceScoreError("Choose a stored PDF score to transcribe.")
        if not movements:
            raise RecognitionError("No movement was transcribed. Check the source PDF.")
        staged: list[Score] = []
        published = False
        try:
            for number, movement in enumerate(movements, start=1):
                movement_number = number if len(movements) > 1 else None
                label = "Transcription" if movement_number is None else f"Movement {number}"
                score, content = await self._prepare_score(work, movement, label)
                await asyncio.to_thread(musicxml_text, content)
                staged.append(
                    replace(
                        score,
                        origin=ScoreOrigin.TRANSCRIPTION,
                        original_name=f"{label}.musicxml",
                        source_score_id=source_id,
                        movement_number=movement_number,
                    )
                )
                await self._file_storage.store(score.storage_key, content)
            async with self._unit_of_work() as unit_of_work:
                await unit_of_work.start_snapshot(for_update=True)
                # Losing the PDF during recognition must roll back the staged results.
                await unit_of_work.scores.get(source_id)
                if reuse and (existing := await self._latest_complete(unit_of_work, source_id)):
                    return existing
                run = await unit_of_work.transcription_runs.add(work.id, source_id, len(staged))
                results = tuple(replace(score, transcription_run_id=run.id) for score in staged)
                for score in results:
                    await unit_of_work.scores.add(score)
                await unit_of_work.commit()
                published = True
                return results
        finally:
            if not published:
                await remove_stored_contents(
                    self._file_storage, (score.storage_key for score in staged)
                )

    async def _latest_complete(
        self, unit_of_work: UnitOfWork, source_id: UUID
    ) -> tuple[Score, ...]:
        run = await unit_of_work.transcription_runs.latest(source_id)
        if run is None:
            return ()
        scores = await unit_of_work.scores.list_transcriptions(run.id)
        if len(scores) != run.movement_count:
            return ()
        for score in scores:
            if not await self._file_storage.exists(score.storage_key):
                return ()
        return tuple(scores)

    async def _prepare_score(
        self, work: Work, source: ScoreSource, label: str | None
    ) -> tuple[Score, bytes]:
        fetched = await source.fetch(self._maximum_size)
        if fetched.size == 0:
            raise InvalidScoreSizeError(self._maximum_size)
        score_format = self._format_detector.detect(fetched.content)
        name = original_name(fetched.original_name)
        score_id = uuid4()
        score = Score(
            id=score_id,
            work_id=work.id,
            label=score_label(label, name, score_format),
            format=score_format,
            size=fetched.size,
            original_name=name,
            origin=source.origin,
            link=source.link,
            storage_key=storage_key(work.choir_id, score_id),
            added_at=self._clock.now(),
        )
        return score, fetched.content

    async def list_scores(self, work_id: UUID) -> list[Score]:
        """Scores of the work, the oldest first.

        Raises:
            WorkNotFoundError: if no work has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            work = await unit_of_work.works.get(work_id)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, work.choir_id)
            return await unit_of_work.scores.list(work_id)

    async def describe_score(self, score_id: UUID) -> tuple[Work, Score]:
        """Return metadata for a score the user may consult."""
        async with self._unit_of_work() as unit_of_work:
            score = await unit_of_work.scores.get(score_id)
            work = await unit_of_work.works.get(score.work_id)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, work.choir_id)
        return work, score

    async def read_score(self, score_id: UUID) -> tuple[Work, Score, bytes]:
        """The score, its work and its stored content, exactly as stored.

        Reading never changes the repertoire. A score larger than the score
        maximum is refused: on its recorded size before anything is read, and
        on its stored size after reading at most the maximum plus one byte, so
        that a file changed outside the application never loads in full.

        Raises:
            ScoreNotFoundError: if no score has this id.
            WorkNotFoundError: if its work no longer exists.
            AccessDeniedError: if the user may not consult the repertoire of its choir.
            ScoreFileMissingError: if its content is missing from the storage.
            StoredScoreTooLargeError: if its recorded or stored size exceeds the maximum.
        """
        work, score = await self.describe_score(score_id)
        if score.size > self._maximum_size:
            raise StoredScoreTooLargeError(score.id, score.label, self._maximum_size)
        if not await self._file_storage.exists(score.storage_key):
            raise ScoreFileMissingError(score.id, score.label)
        content = await self._file_storage.read(score.storage_key, self._maximum_size)
        if len(content) > self._maximum_size:
            raise StoredScoreTooLargeError(score.id, score.label, self._maximum_size)
        return work, score, content

    async def open_score(self, score_id: UUID) -> tuple[Work, Score]:
        """Open the score in the application of the user's computer that opens its format.

        Raises:
            ScoreNotFoundError: if no score has this id.
            ScoreFileMissingError: if its content is missing from the storage.
            ScoreOpenError: if it cannot be opened.
        """
        work, score, content = await self.read_score(score_id)
        await self._opener.open(score, content)
        return work, score

    @property
    def deletion_target(self) -> DeletionTarget:
        """Scores."""
        return DeletionTarget.SCORE

    async def describe_deletion(self, target_id: UUID) -> DeletionPreview:
        """The score and its work.

        Raises:
            ScoreNotFoundError: if no score has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot()
            return await self._deletion(unit_of_work, target_id)

    async def delete(self, preview: DeletionPreview) -> Deletion:
        """Delete the score, then its stored content.

        Raises:
            ScoreNotFoundError: if no score has this id.
        """
        target_id = preview.deletion.target_id
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot(for_update=True)
            current = await self._deletion(unit_of_work, target_id)
            if current != preview:
                raise StaleConfirmationError(current)
            await unit_of_work.scores.delete(target_id)
            await unit_of_work.commit()
        await remove_stored_contents(
            self._file_storage, [score.storage_key for score in current.scores]
        )
        return current.deletion

    async def _deletion(self, unit_of_work: UnitOfWork, score_id: UUID) -> DeletionPreview:
        score = await unit_of_work.scores.get(score_id)
        work = await unit_of_work.works.get(score.work_id)
        self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
        deletion = Deletion(DeletionTarget.SCORE, score.id, score.label, work.title)
        return DeletionPreview(deletion, scores=(score,))
