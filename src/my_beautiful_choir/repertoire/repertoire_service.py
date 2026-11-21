# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on the works of a choir (flows D, E and F of issue #7)."""

from dataclasses import replace
from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_service import find_choir
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.persistence.unit_of_work import UnitOfWorkFactory
from my_beautiful_choir.repertoire.work import Work, WorkChanges, WorkDetails
from my_beautiful_choir.repertoire.work_rules import apply_work_changes, clean_work_details


class RepertoireService:
    """Adds, edits and finds the works of a choir."""

    def __init__(
        self, unit_of_work: UnitOfWorkFactory, clock: Clock, authorization: Authorization
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._authorization = authorization

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
