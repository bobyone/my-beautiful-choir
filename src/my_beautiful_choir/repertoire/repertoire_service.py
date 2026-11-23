# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on the works of a choir (flows D, E, F and I of issue #7)."""

from dataclasses import replace
from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_service import find_choir
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.deletion.stale_confirmation_error import StaleConfirmationError
from my_beautiful_choir.deletion.stored_contents import remove_stored_contents
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork, UnitOfWorkFactory
from my_beautiful_choir.repertoire.repertoire_page import PageRequest, RepertoirePage, page_count
from my_beautiful_choir.repertoire.work import Work, WorkChanges, WorkDetails
from my_beautiful_choir.repertoire.work_rules import apply_work_changes, clean_work_details
from my_beautiful_choir.storage.file_storage import FileStorage


class RepertoireService(Deleter):
    """Adds, edits, finds and deletes the works of a choir."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        clock: Clock,
        authorization: Authorization,
        file_storage: FileStorage,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._authorization = authorization
        self._file_storage = file_storage

    async def add_work(self, choir: str | None, details: WorkDetails) -> tuple[Choir, Work]:
        """Add a work to the choir named ``choir``, or to the default choir.

        Raises:
            ChoirNotFoundError, NoChoirError: if the choir cannot be found.
            InvalidWorkError: if an attribute is invalid.
        """
        cleaned = clean_work_details(details)
        async with self._unit_of_work() as unit_of_work:
            target = await find_choir(unit_of_work.choirs, choir)
            self._authorization.require(Permission.MANAGE_REPERTOIRE, target.id)
            now = self._clock.now()
            work = Work(uuid4(), target.id, cleaned, created_at=now, updated_at=now)
            await unit_of_work.works.add(work)
            await unit_of_work.commit()
        return target, work

    async def edit_work(self, work_id: UUID, changes: WorkChanges) -> Work:
        """Change the given attributes of a work.

        Raises:
            WorkNotFoundError: if no work has this id.
            InvalidWorkError: if an attribute is invalid.
        """
        async with self._unit_of_work() as unit_of_work:
            work = await unit_of_work.works.get(work_id)
            self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
            details = apply_work_changes(work.details, changes)
            edited = replace(work, details=details, updated_at=self._clock.now())
            await unit_of_work.works.update(edited)
            await unit_of_work.commit()
        return edited

    async def get_work(self, work_id: UUID) -> tuple[Choir, Work]:
        """The work with this id, and its choir.

        Raises:
            WorkNotFoundError: if no work has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            work = await unit_of_work.works.get(work_id)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, work.choir_id)
            return await unit_of_work.choirs.get(work.choir_id), work

    async def search(self, choir: str | None, text: str | None = None) -> tuple[Choir, list[Work]]:
        """Works of the choir (or the default choir) whose title or composer contains ``text``.

        Raises:
            ChoirNotFoundError, NoChoirError: if the choir cannot be found.
        """
        async with self._unit_of_work() as unit_of_work:
            target = await find_choir(unit_of_work.choirs, choir)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, target.id)
            return target, await unit_of_work.works.search(target.id, text)

    async def search_page_with_score_counts(
        self, choir: str | None, text: str | None, request: PageRequest
    ) -> RepertoirePage:
        """One repertoire page of the matching works, with their score totals.

        A page number past the last page returns the last page.

        Raises:
            ChoirNotFoundError, NoChoirError: if the choir cannot be found.
        """
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot()
            target = await find_choir(unit_of_work.choirs, choir)
            self._authorization.require(Permission.CONSULT_REPERTOIRE, target.id)
            work_count = await unit_of_work.works.count_matching(target.id, text)
            number = min(request.number, page_count(work_count, request.size))
            works = await unit_of_work.works.search_page(
                target.id, text, offset=(number - 1) * request.size, limit=request.size
            )
            counts = await unit_of_work.scores.counts_of_choir(target.id)
        return RepertoirePage(
            target,
            tuple(works),
            {work.id: counts.get(work.id, 0) for work in works},
            number,
            request.size,
            work_count,
        )

    @property
    def deletion_target(self) -> DeletionTarget:
        """Works."""
        return DeletionTarget.WORK

    async def describe_deletion(self, target_id: UUID) -> DeletionPreview:
        """The work, its choir and its number of scores.

        Raises:
            WorkNotFoundError: if no work has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot()
            return await self._deletion(unit_of_work, target_id)

    async def delete(self, preview: DeletionPreview) -> Deletion:
        """Delete the work, its scores and their stored contents.

        Raises:
            WorkNotFoundError: if no work has this id.
        """
        target_id = preview.deletion.target_id
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot(for_update=True)
            current = await self._deletion(unit_of_work, target_id)
            if current != preview:
                raise StaleConfirmationError(current)
            await unit_of_work.works.delete(target_id)
            await unit_of_work.commit()
        await remove_stored_contents(
            self._file_storage, [score.storage_key for score in current.scores]
        )
        return current.deletion

    async def _deletion(self, unit_of_work: UnitOfWork, work_id: UUID) -> DeletionPreview:
        work = await unit_of_work.works.get(work_id)
        self._authorization.require(Permission.MANAGE_REPERTOIRE, work.choir_id)
        choir = await unit_of_work.choirs.get(work.choir_id)
        scores = await unit_of_work.scores.list(work.id)
        deletion = Deletion(
            DeletionTarget.WORK, work.id, work.title, choir.name, score_count=len(scores)
        )
        return DeletionPreview(
            deletion, works=(work,), scores=tuple(sorted(scores, key=lambda score: score.id))
        )
