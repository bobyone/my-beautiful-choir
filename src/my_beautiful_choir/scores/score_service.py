# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on the scores of a work (flows G, H and I of issue #7)."""

from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.deletion.stored_contents import remove_stored_contents
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork, UnitOfWorkFactory
from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.scores.errors import InvalidScoreSizeError, ScoreFileMissingError
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.opening.score_opener import ScoreOpener
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_rules import (
    MAXIMUM_SIZE,
    original_name,
    score_label,
    storage_key,
)
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from my_beautiful_choir.storage.file_storage import FileStorage


class ScoreService(Deleter):
    """Adds, lists, opens and deletes the scores of the works."""

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
        self, work_id: UUID, source: ScoreSource, label: str | None = None
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
        # The content is fetched outside any transaction: a download may be long.
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
        await self._file_storage.store(score.storage_key, fetched.content)
        try:
            async with self._unit_of_work() as unit_of_work:
                work = await unit_of_work.works.get(work_id)
                await unit_of_work.scores.add(score)
                await unit_of_work.commit()
        except BaseException:
            await remove_stored_contents(self._file_storage, [score.storage_key])
            raise
        return work, score

    async def list_scores(self, work_id: UUID) -> list[Score]:
        """Scores of the work, the oldest first.

        Raises:
            WorkNotFoundError: if no work has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            work = await unit_of_work.works.get(work_id)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, work.choir_id)
            return await unit_of_work.scores.list(work_id)

    async def open_score(self, score_id: UUID) -> tuple[Work, Score]:
        """Open the score in the application of the user's computer that opens its format.

        Raises:
            ScoreNotFoundError: if no score has this id.
            ScoreFileMissingError: if its content is missing from the storage.
            ScoreOpenError: if it cannot be opened.
        """
        async with self._unit_of_work() as unit_of_work:
            score = await unit_of_work.scores.get(score_id)
            work = await unit_of_work.works.get(score.work_id)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, work.choir_id)
        if not await self._file_storage.exists(score.storage_key):
            raise ScoreFileMissingError(score.id, score.label)
        content = await self._file_storage.read(score.storage_key)
        await self._opener.open(score, content)
        return work, score

    @property
    def deletion_target(self) -> DeletionTarget:
        """Scores."""
        return DeletionTarget.SCORE

    async def describe_deletion(self, target_id: UUID) -> Deletion:
        """The score and its work.

        Raises:
            ScoreNotFoundError: if no score has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            deletion, _ = await self._deletion(unit_of_work, target_id)
        return deletion

    async def delete(self, target_id: UUID) -> Deletion:
        """Delete the score, then its stored content.

        Raises:
            ScoreNotFoundError: if no score has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            deletion, key = await self._deletion(unit_of_work, target_id)
            await unit_of_work.scores.delete(target_id)
            await unit_of_work.commit()
        await remove_stored_contents(self._file_storage, [key])
        return deletion

    async def _deletion(self, unit_of_work: UnitOfWork, score_id: UUID) -> tuple[Deletion, str]:
        score = await unit_of_work.scores.get(score_id)
        work = await unit_of_work.works.get(score.work_id)
        self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
        deletion = Deletion(DeletionTarget.SCORE, score.id, score.label, work.title)
        return deletion, score.storage_key
