# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on choirs (flows A, B and C of issue #7)."""

from uuid import uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_name import clean_choir_name
from my_beautiful_choir.choirs.choir_repository import ChoirRepository
from my_beautiful_choir.choirs.errors import ChoirNameTakenError, ChoirNotFoundError, NoChoirError
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.persistence.unit_of_work import UnitOfWorkFactory


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


class ChoirService:
    """Creates, renames and lists choirs, and chooses the default choir."""

    def __init__(
        self, unit_of_work: UnitOfWorkFactory, clock: Clock, authorization: Authorization
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._authorization = authorization

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
