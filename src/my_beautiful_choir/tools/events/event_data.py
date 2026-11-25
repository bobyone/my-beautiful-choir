# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content, English texts and arguments shared by the event tools."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.events.event import Event
from my_beautiful_choir.events.event_rules import ENTRY_NOTE_LENGTH, MAXIMUM_PROGRAMME_ENTRIES
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.events.programme_item import ProgrammeItem
from my_beautiful_choir.events.visible_event import VisibleEvent

DATE_DESCRIPTION = (
    "ISO 8601 date and time with its time zone offset, for example "
    "2026-12-20T20:30:00+01:00. Use the user's time zone when they give a local time."
)
UTC_NOTICE = "Dates are returned in UTC: present them in the user's time zone."
PROGRAMME_DESCRIPTION = (
    f"Ordered programme, at most {MAXIMUM_PROGRAMME_ENTRIES} entries. Each entry names a work "
    "of the choir's repertoire by its id, or gives only a note (an interval, a piece outside "
    "the repertoire), or both. A work may appear several times."
)


class ProgrammeItemArguments(BaseModel):
    """One requested programme entry."""

    work_id: UUID | None = Field(
        default=None, description="Id of a work of the choir's repertoire, as given by it."
    )
    note: str | None = Field(
        default=None, description=f"Free note, at most {ENTRY_NOTE_LENGTH} characters."
    )


def programme_items(arguments: Sequence[ProgrammeItemArguments]) -> list[ProgrammeItem]:
    """Programme items requested through a tool."""
    return [ProgrammeItem(item.work_id, item.note) for item in arguments]


def _date(moment: datetime | None) -> str | None:
    return None if moment is None else moment.isoformat()


def _entry_data(entry: ProgrammeEntry) -> Mapping[str, object]:
    return {
        "position": entry.position,
        "work_id": None if entry.work_id is None else str(entry.work_id),
        "work_title": entry.work_title,
        "note": entry.note,
    }


def _shown_notes(visible: VisibleEvent, notes_limit: int) -> tuple[str | None, bool]:
    """Notes the model may receive, and whether longer notes were withheld."""
    notes = visible.event.details.notes if visible.complete else None
    if notes is not None and len(notes) > notes_limit:
        return None, True
    return notes, False


def event_data(visible: VisibleEvent, notes_limit: int) -> Mapping[str, object]:
    """Structured content describing an event as the observer may see it.

    Notes longer than ``notes_limit`` are free text that is never given to the
    model: they are left out and ``notes_withheld`` is set.
    """
    event = visible.event
    details = event.details
    data: dict[str, object] = {
        "id": str(event.id),
        "kind": event.kind.value,
        "title": details.title,
        "starts_at": details.starts_at.isoformat(),
        "ends_at": _date(details.ends_at),
        "place": details.place,
        "programme": [_entry_data(entry) for entry in event.programme],
        "programme_withheld": visible.programme_withheld,
    }
    if visible.complete:
        notes, withheld = _shown_notes(visible, notes_limit)
        data |= {
            "notes": notes,
            "notes_withheld": withheld,
            "programme_hidden": event.programme_hidden,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
        }
    return data


def event_label(event: Event) -> str:
    """Kind, title and start of the event, in English."""
    return f'the {event.kind.value} "{event.title}" starting {event.details.starts_at.isoformat()}'


def _entry_text(entry: ProgrammeEntry) -> str:
    parts = [part for part in (entry.work_title, entry.note) if part]
    return f"{entry.position}. " + "; ".join(parts)


def event_text(visible: VisibleEvent, notes_limit: int) -> str:
    """Self-sufficient English description of an event, with its programme.

    Notes longer than ``notes_limit`` are left out, as in ``event_data``.
    """
    event = visible.event
    details = event.details
    label = event_label(event)
    lines = [f"{label[0].upper()}{label[1:]} (id {event.id})."]
    if details.ends_at is not None:
        lines.append(f"Ends: {details.ends_at.isoformat()}.")
    if details.place:
        lines.append(f"Place: {details.place}.")
    notes, withheld = _shown_notes(visible, notes_limit)
    if notes:
        lines.append(f"Notes: {notes}")
    if withheld:
        lines.append(
            f"The notes are longer than {notes_limit} characters and are not shown; "
            "shorten them with edit_event to read them here."
        )
    if visible.programme_withheld:
        lines.append("The programme is hidden from the public.")
    elif event.programme:
        lines.append("Programme:")
        lines.extend(_entry_text(entry) for entry in event.programme)
    else:
        lines.append("No programme.")
    if visible.complete and event.programme_hidden:
        lines.append("The programme is hidden from the public; members of the choir see it.")
    return "\n".join(lines)
