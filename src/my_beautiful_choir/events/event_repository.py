# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Event repository abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.events.event import Event
from my_beautiful_choir.events.period import Period


class EventRepository(ABC):
    """Stores the events with their programmes; used within a unit of work.

    The programme entries returned carry the current title of their work while
    it exists, and the kept title after its deletion. The kept title is the one
    given when the programme was last replaced: updating the other attributes
    never changes it.
    """

    @abstractmethod
    async def add(self, event: Event) -> None:
        """Add a new event with its programme."""

    @abstractmethod
    async def get(self, event_id: UUID) -> Event:
        """Return the event with this id.

        Raises:
            EventNotFoundError: if there is none.
        """

    @abstractmethod
    async def update(self, event: Event) -> None:
        """Replace the details, the flags and the modification date; not the programme."""

    @abstractmethod
    async def replace_programme(self, event: Event) -> None:
        """Replace the whole programme of the event, keeping the titles it carries."""

    @abstractmethod
    async def delete(self, event_id: UUID) -> None:
        """Delete an event with its programme."""

    @abstractmethod
    async def list_overlapping(self, choir_id: UUID, period: Period) -> list[Event]:
        """Events of the choir overlapping the period, sorted by start, title, then id.

        An event without an end counts as an instant at its start.
        """

    @abstractmethod
    async def list_of_choir(self, choir_id: UUID) -> list[Event]:
        """Every event of the choir, sorted by id."""

    @abstractmethod
    async def count_referencing_work(self, work_id: UUID) -> int:
        """Number of events whose programme refers to the work."""
