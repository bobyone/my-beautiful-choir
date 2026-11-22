# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Choir repository abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.choirs.choir import Choir


class ChoirRepository(ABC):
    """Stores the choirs; used within a unit of work."""

    @abstractmethod
    async def add(self, choir: Choir) -> None:
        """Add a new choir."""

    @abstractmethod
    async def get(self, choir_id: UUID) -> Choir:
        """Return the choir with this id.

        Raises:
            ChoirNotFoundError: if there is none.
        """

    @abstractmethod
    async def find_by_name(self, name: str) -> Choir | None:
        """Return the choir with this name, ignoring case, or None."""

    @abstractmethod
    async def default(self) -> Choir | None:
        """Return the default choir, or None when there is no choir."""

    @abstractmethod
    async def list(self) -> list[Choir]:
        """Return every choir, the oldest first."""

    @abstractmethod
    async def rename(self, choir_id: UUID, name: str) -> None:
        """Change the name of a choir."""

    @abstractmethod
    async def make_default(self, choir_id: UUID) -> None:
        """Make this choir the default one, and the previous default choir an ordinary one."""

    @abstractmethod
    async def delete(self, choir_id: UUID) -> None:
        """Delete a choir with its works and scores (not the stored score files)."""
