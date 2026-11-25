# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Event value objects."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.programme_entry import ProgrammeEntry


@dataclass(frozen=True)
class EventDetails:
    """What describes an event, as entered by the user; dates are timezone-aware."""

    title: str
    starts_at: datetime
    ends_at: datetime | None = None
    place: str | None = None
    notes: str | None = None
    """Internal notes, never shown to the public."""


@dataclass(frozen=True)
class EventChanges:
    """Changes of an event: None leaves an attribute unchanged, an empty text clears it."""

    title: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    clear_end: bool = False
    """Remove the end of the event."""
    place: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class Event:
    """Dated occasion of a choir: a concert, a rehearsal or a lesson."""

    id: UUID
    choir_id: UUID
    kind: EventKind
    details: EventDetails
    created_at: datetime
    updated_at: datetime
    programme: tuple[ProgrammeEntry, ...] = ()
    programme_hidden: bool = False
    """True for a concert whose programme is not shown to the public."""
    participant_ids: tuple[UUID, ...] = ()
    """Members of the choir who may see a lesson."""

    @property
    def title(self) -> str:
        """Title of the event."""
        return self.details.title
