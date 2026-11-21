# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on choirs (flows A, B, C and I of issue #7)."""

from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_name import clean_choir_name
from my_beautiful_choir.choirs.choir_repository import ChoirRepository
from my_beautiful_choir.choirs.errors import ChoirNameTakenError, ChoirNotFoundError, NoChoirError
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.deletion.stored_contents import remove_stored_contents
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork, UnitOfWorkFactory
from my_beautiful_choir.storage.file_storage import FileStorage


async def find_choir(choirs: ChoirRepository, name: str | None) -> Choir:
    """Choir named ``name`` (ignoring case), or the default choir when no name is given.

    Raises:
        ChoirNotFoundError: if no choir has this name.
        NoChoirError: if no name is given and no choir exists.
    """
    if name is not None:
        choir = await choirs.find_by_name(name)
        if choir is None:
            raise ChoirNotFoundError(name)
        return choir
    default = await choirs.default()
    if default is None:
        raise NoChoirError
    return default


class ChoirService(Deleter):
    """Creates, renames, lists and deletes choirs, and chooses the default choir."""

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

    async def list_choirs(self) -> list[Choir]:
        """Every choir, the oldest first."""
        self._authorization.require(Permission.CONSULT_REPERTOIRE)
        async with self._unit_of_work() as unit_of_work:
            return await unit_of_work.choirs.list()

    async def create(self, name: str) -> Choir:
        """Create a choir; the first one becomes the default choir.

        Raises:
            InvalidChoirNameError: if the name is empty or too long.
            ChoirNameTakenError: if another choir has this name.
        """
        self._authorization.require(Permission.MANAGE_CHOIRS)
        cleaned = clean_choir_name(name)
        async with self._unit_of_work() as unit_of_work:
            choirs = unit_of_work.choirs
            if await choirs.find_by_name(cleaned) is not None:
                raise ChoirNameTakenError(cleaned)
            is_first = await choirs.default() is None
            choir = Choir(uuid4(), cleaned, self._clock.now(), is_default=is_first)
            await choirs.add(choir)
            await unit_of_work.commit()
        return choir

    async def rename(self, choir: str, new_name: str) -> Choir:
        """Rename the choir named ``choir``.

        Raises:
            ChoirNotFoundError: if no choir has this name.
            InvalidChoirNameError: if the new name is empty or too long.
            ChoirNameTakenError: if another choir has the new name.
        """
        cleaned = clean_choir_name(new_name)
        async with self._unit_of_work() as unit_of_work:
            choirs = unit_of_work.choirs
            current = await find_choir(choirs, choir)
            self._authorization.require(Permission.MANAGE_CHOIRS, current.id)
            homonym = await choirs.find_by_name(cleaned)
            if homonym is not None and homonym.id != current.id:
                raise ChoirNameTakenError(cleaned)
            await choirs.rename(current.id, cleaned)
            await unit_of_work.commit()
        return Choir(current.id, cleaned, current.created_at, current.is_default)

    async def set_default(self, choir: str) -> Choir:
        """Make the choir named ``choir`` the default choir.

        Raises:
            ChoirNotFoundError: if no choir has this name.
        """
        async with self._unit_of_work() as unit_of_work:
            current = await find_choir(unit_of_work.choirs, choir)
            self._authorization.require(Permission.MANAGE_CHOIRS, current.id)
            await unit_of_work.choirs.make_default(current.id)
            await unit_of_work.commit()
        return Choir(current.id, current.name, current.created_at, is_default=True)

    async def get_choir(self, choir: str) -> Choir:
        """The choir named ``choir``, ignoring case.

        Raises:
            ChoirNotFoundError: if no choir has this name.
        """
        async with self._unit_of_work() as unit_of_work:
            found = await find_choir(unit_of_work.choirs, choir)
        self._authorization.require(Permission.CONSULT_REPERTOIRE, found.id)
        return found

    @property
    def deletion_target(self) -> DeletionTarget:
        """Choirs."""
        return DeletionTarget.CHOIR

    async def describe_deletion(self, target_id: UUID) -> Deletion:
        """The choir with its number of works and scores.

        Raises:
            ChoirNotFoundError: if no choir has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            deletion, _ = await self._deletion(unit_of_work, target_id)
        return deletion

    async def delete(self, target_id: UUID) -> Deletion:
        """Delete the choir, its works, its scores and their stored contents.

        When the default choir is deleted and choirs remain, the oldest one
        becomes the default choir.

        Raises:
            ChoirNotFoundError: if no choir has this id.
        """
        async with self._unit_of_work() as unit_of_work:
            deletion, keys = await self._deletion(unit_of_work, target_id)
            choirs = unit_of_work.choirs
            was_default = (await choirs.get(target_id)).is_default
            await choirs.delete(target_id)
            remaining = await choirs.list()
            if was_default and remaining:
                await choirs.make_default(remaining[0].id)
            await unit_of_work.commit()
        await remove_stored_contents(self._file_storage, keys)
        return deletion

    async def _deletion(
        self, unit_of_work: UnitOfWork, choir_id: UUID
    ) -> tuple[Deletion, list[str]]:
        choir = await unit_of_work.choirs.get(choir_id)
        self._authorization.require(Permission.MANAGE_CHOIRS, choir.id)
        keys = await unit_of_work.scores.storage_keys_of_choir(choir.id)
        deletion = Deletion(
            DeletionTarget.CHOIR,
            choir.id,
            choir.name,
            work_count=await unit_of_work.works.count(choir.id),
            score_count=len(keys),
        )
        return deletion, keys
