# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Sample events shared by the event tests."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from my_beautiful_choir.events.event import Event, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.programme_entry import ProgrammeEntry

CREATED = datetime(2026, 11, 1, 9, tzinfo=UTC)
STARTS = datetime(2026, 12, 20, 19, 30, tzinfo=UTC)


def make_event(
    kind: EventKind = EventKind.CONCERT,
    *,
    choir_id: UUID | None = None,
    title: str = "Christmas concert",
    starts_at: datetime = STARTS,
    ends_at: datetime | None = None,
    notes: str | None = "Arrive at 18:30",
    programme: tuple[ProgrammeEntry, ...] = (
        ProgrammeEntry(1, uuid4(), "Ave Maria", None),
        ProgrammeEntry(2, None, None, "Interval"),
    ),
    programme_hidden: bool = False,
    participant_ids: tuple[UUID, ...] = (),
) -> Event:
    """An event with plausible values."""
    return Event(
        id=uuid4(),
        choir_id=choir_id or uuid4(),
        kind=kind,
        details=EventDetails(
            title=title, starts_at=starts_at, ends_at=ends_at, place="Cathedral", notes=notes
        ),
        created_at=CREATED,
        updated_at=CREATED,
        programme=programme,
        programme_hidden=programme_hidden,
        participant_ids=participant_ids,
    )
