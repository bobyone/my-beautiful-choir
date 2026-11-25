# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Rules of the attributes, the programme and the audience of an event."""

import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from my_beautiful_choir.events.errors import InvalidEventError, ProgrammeNotHideableError
from my_beautiful_choir.events.event import EventChanges, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.events.programme_item import ProgrammeItem

TITLE_LENGTH = 200
PLACE_LENGTH = 200
NOTES_LENGTH = 2000
ENTRY_NOTE_LENGTH = 200
MAXIMUM_PROGRAMME_ENTRIES = 100


def _text(attribute: str, value: str | None, maximum: int) -> str | None:
    """Trimmed text in Unicode normal form C; empty becomes None."""
    if value is None:
        return None
    cleaned = unicodedata.normalize("NFC", value.strip())
    if len(cleaned) > maximum:
        raise InvalidEventError(attribute, f"at most {maximum} characters")
    return cleaned or None


def _utc(attribute: str, moment: datetime) -> datetime:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise InvalidEventError(attribute, "it must include a time zone offset")
    return moment.astimezone(UTC)


def clean_event_details(details: EventDetails) -> EventDetails:
    """Validated and normalized details, with dates in UTC.

    Raises:
        InvalidEventError: if the title is empty, an attribute is too long, a date
            has no time zone offset or the end is before the start.
    """
    title = _text("title", details.title, TITLE_LENGTH)
    if title is None:
        raise InvalidEventError("title", "it must not be empty")
    starts_at = _utc("start", details.starts_at)
    ends_at = None if details.ends_at is None else _utc("end", details.ends_at)
    if ends_at is not None and ends_at < starts_at:
        raise InvalidEventError("end", "it must not be before the start")
    return EventDetails(
        title=title,
        starts_at=starts_at,
        ends_at=ends_at,
        place=_text("place", details.place, PLACE_LENGTH),
        notes=_text("notes", details.notes, NOTES_LENGTH),
    )


def apply_event_changes(details: EventDetails, changes: EventChanges) -> EventDetails:
    """Details with the changes applied, validated and normalized.

    Raises:
        InvalidEventError: as ``clean_event_details``, or if an end is both given
            and cleared.
    """
    if changes.clear_end and changes.ends_at is not None:
        raise InvalidEventError("end", "it cannot be both given and cleared")
    updated = replace(
        details,
        **{
            name: getattr(changes, name)
            for name in ("title", "starts_at", "ends_at", "place", "notes")
            if getattr(changes, name) is not None
        },
    )
    if changes.clear_end:
        updated = replace(updated, ends_at=None)
    return clean_event_details(updated)


def clean_programme(items: Sequence[ProgrammeItem]) -> tuple[ProgrammeItem, ...]:
    """Validated programme items, with normalized notes.

    Raises:
        InvalidEventError: if there are too many entries, an entry has neither a
            work nor a note, or a note is too long.
    """
    if len(items) > MAXIMUM_PROGRAMME_ENTRIES:
        raise InvalidEventError("programme", f"at most {MAXIMUM_PROGRAMME_ENTRIES} entries")
    cleaned = []
    for position, item in enumerate(items, start=1):
        note = _text(f"note of programme entry {position}", item.note, ENTRY_NOTE_LENGTH)
        if item.work_id is None and note is None:
            raise InvalidEventError("programme", f"entry {position} needs a work, a note, or both")
        cleaned.append(ProgrammeItem(item.work_id, note))
    return tuple(cleaned)


def build_programme(
    items: Sequence[ProgrammeItem], titles: Mapping[UUID, str]
) -> tuple[ProgrammeEntry, ...]:
    """Programme entries numbered from 1, keeping the title of each work.

    ``titles`` gives the title of every work referred to by the items.
    """
    return tuple(
        ProgrammeEntry(
            position=position,
            work_id=item.work_id,
            work_title=None if item.work_id is None else titles[item.work_id],
            note=item.note,
        )
        for position, item in enumerate(items, start=1)
    )


def check_audience(
    kind: EventKind, programme_hidden: bool, participant_ids: Sequence[UUID]
) -> tuple[UUID, ...]:
    """Participants without duplicates, once the audience fits the kind.

    Raises:
        ProgrammeNotHideableError: if the programme of an event that is not a
            concert is hidden.
        InvalidEventError: if a lesson has no participant, or another kind has some.
    """
    if programme_hidden and kind is not EventKind.CONCERT:
        raise ProgrammeNotHideableError(kind)
    participants = tuple(dict.fromkeys(participant_ids))
    if kind is EventKind.LESSON and not participants:
        raise InvalidEventError("participants", "a lesson needs at least one participant")
    if kind is not EventKind.LESSON and participants:
        raise InvalidEventError("participants", f"a {kind.value} has no participants")
    return participants
