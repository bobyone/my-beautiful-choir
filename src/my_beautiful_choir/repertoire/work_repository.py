# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Work repository abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.repertoire.work import Work


class WorkRepository(ABC):
    """Stores the works; used within a unit of work."""

    @abstractmethod
    async def add(self, work: Work) -> None:
        """Add a new work."""

    @abstractmethod
    async def get(self, work_id: UUID) -> Work:
        """Return the work with this id.

        Raises:
            WorkNotFoundError: if there is none.
        """

    @abstractmethod
    async def search(self, choir_id: UUID, text: str | None = None) -> list[Work]:
        """Works of the choir whose title or composer contains ``text``.

        ``text`` is compared ignoring case and accents; None returns every work.
        The order is unspecified: the user interface sorts by language.
        """

    @abstractmethod
    async def update(self, work: Work) -> None:
        """Replace the details and the modification date of a work."""

    @abstractmethod
    async def delete(self, work_id: UUID) -> None:
        """Delete a work with its scores (not the stored score files)."""

    @abstractmethod
    async def count(self, choir_id: UUID) -> int:
        """Number of works of the choir."""
