# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Event repository on an SQL database."""

from collections import defaultdict
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, distinct, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from my_beautiful_choir.events.errors import EventNotFoundError
from my_beautiful_choir.events.event import Event, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_repository import EventRepository
from my_beautiful_choir.events.period import Period
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.persistence.sql.tables import events, programme_entries, works


def _event(row: Row[*tuple[Any, ...]], programme: Sequence[ProgrammeEntry]) -> Event:
    details = EventDetails(
        title=row.title,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        place=row.place,
        notes=row.notes,
    )
    return Event(
        id=row.id,
        choir_id=row.choir_id,
        kind=EventKind(row.kind),
        details=details,
        created_at=row.created_at,
        updated_at=row.updated_at,
        programme=tuple(programme),
        programme_hidden=row.programme_hidden,
    )


def _values(event: Event) -> dict[str, object]:
    details = event.details
    return {
        "title": details.title,
        "starts_at": details.starts_at,
        "ends_at": details.ends_at,
        "place": details.place,
        "notes": details.notes,
        "programme_hidden": event.programme_hidden,
        "updated_at": event.updated_at,
    }


def _entry_values(event: Event) -> list[dict[str, object]]:
    return [
        {
            "event_id": event.id,
            "position": entry.position,
            "work_id": entry.work_id,
            "work_title": entry.work_title,
            "note": entry.note,
        }
        for entry in event.programme
    ]


def _require_no_participants(event: Event) -> None:
    if event.participant_ids:
        raise NotImplementedError("Lesson participants are stored with choir members (#31)")


class SqlEventRepository(EventRepository):
    """Stores the events in the ``events`` and ``programme_entries`` tables.

    Lesson participants are not stored yet: they need choir members (#31).
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, event: Event) -> None:
        """Insert the event and its programme entries."""
        _require_no_participants(event)
        await self._connection.execute(
            insert(events).values(
                id=event.id,
                choir_id=event.choir_id,
                kind=event.kind.value,
                created_at=event.created_at,
                **_values(event),
            )
        )
        await self._insert_programme(event)

    async def get(self, event_id: UUID) -> Event:
        """The event with its programme.

        Raises:
            EventNotFoundError: if there is none.
        """
        row = (
            await self._connection.execute(select(events).where(events.c.id == event_id))
        ).first()
        if row is None:
            raise EventNotFoundError(event_id)
        programmes = await self._programmes([event_id])
        return _event(row, programmes[event_id])

    async def update(self, event: Event) -> None:
        """Replace the attributes and the whole programme."""
        _require_no_participants(event)
        await self._connection.execute(
            update(events).where(events.c.id == event.id).values(**_values(event))
        )
        await self._connection.execute(
            delete(programme_entries).where(programme_entries.c.event_id == event.id)
        )
        await self._insert_programme(event)

    async def delete(self, event_id: UUID) -> None:
        """Delete the event; its programme entries cascade."""
        await self._connection.execute(delete(events).where(events.c.id == event_id))

    async def list_overlapping(self, choir_id: UUID, period: Period) -> list[Event]:
        """Events of the choir overlapping the period, by start, title, then id."""
        rows = (
            await self._connection.execute(
                select(events)
                .where(
                    events.c.choir_id == choir_id,
                    events.c.starts_at <= period.end,
                    func.coalesce(events.c.ends_at, events.c.starts_at) >= period.start,
                )
                .order_by(events.c.starts_at, events.c.title, events.c.id)
            )
        ).all()
        programmes = await self._programmes([row.id for row in rows])
        return [_event(row, programmes[row.id]) for row in rows]

    async def count_of_choir(self, choir_id: UUID) -> int:
        """Number of events of the choir."""
        count = await self._connection.scalar(
            select(func.count()).select_from(events).where(events.c.choir_id == choir_id)
        )
        return count or 0

    async def count_referencing_work(self, work_id: UUID) -> int:
        """Number of distinct events whose programme refers to the work."""
        count = await self._connection.scalar(
            select(func.count(distinct(programme_entries.c.event_id))).where(
                programme_entries.c.work_id == work_id
            )
        )
        return count or 0

    async def _insert_programme(self, event: Event) -> None:
        values = _entry_values(event)
        if values:
            await self._connection.execute(insert(programme_entries), values)

    async def _programmes(self, event_ids: Sequence[UUID]) -> dict[UUID, list[ProgrammeEntry]]:
        """Programme entries of the events, with the current title of existing works."""
        programmes: dict[UUID, list[ProgrammeEntry]] = defaultdict(list)
        if not event_ids:
            return programmes
        rows = await self._connection.execute(
            select(
                programme_entries.c.event_id,
                programme_entries.c.position,
                programme_entries.c.work_id,
                func.coalesce(works.c.title, programme_entries.c.work_title).label("title"),
                programme_entries.c.note,
            )
            .outerjoin(works, works.c.id == programme_entries.c.work_id)
            .where(programme_entries.c.event_id.in_(event_ids))
            .order_by(programme_entries.c.event_id, programme_entries.c.position)
        )
        for row in rows:
            programmes[row.event_id].append(
                ProgrammeEntry(row.position, row.work_id, row.title, row.note)
            )
        return programmes
