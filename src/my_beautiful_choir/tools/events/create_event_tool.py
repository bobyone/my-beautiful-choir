# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool adding an event to a choir."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from my_beautiful_choir.events.event import EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_rules import NOTES_LENGTH, PLACE_LENGTH, TITLE_LENGTH
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.events.visible_event import VisibleEvent
from my_beautiful_choir.tools.choirs.choir_data import CHOIR_FIELD_DESCRIPTION
from my_beautiful_choir.tools.events.event_data import (
    DATE_DESCRIPTION,
    PROGRAMME_DESCRIPTION,
    UTC_NOTICE,
    ProgrammeItemArguments,
    event_data,
    event_label,
    programme_items,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class CreateEventArguments(BaseModel):
    """Arguments of ``create_event``."""

    choir: str | None = Field(default=None, description=CHOIR_FIELD_DESCRIPTION)
    kind: Literal["concert", "rehearsal"] = Field(
        description=(
            "concert: visible to everyone, including the public; rehearsal: visible to the "
            "members of the choir. The kind cannot be changed later."
        )
    )
    title: str = Field(description=f"Title of the event, at most {TITLE_LENGTH} characters.")
    starts_at: datetime = Field(description=f"Start. {DATE_DESCRIPTION}")
    ends_at: datetime | None = Field(
        default=None, description=f"Optional end, not before the start. {DATE_DESCRIPTION}"
    )
    place: str | None = Field(
        default=None, description=f"Place, at most {PLACE_LENGTH} characters."
    )
    notes: str | None = Field(
        default=None,
        description=(
            f"Internal notes for the members, never shown to the public, at most "
            f"{NOTES_LENGTH} characters."
        ),
    )
    programme: list[ProgrammeItemArguments] = Field(
        default_factory=list, description=PROGRAMME_DESCRIPTION
    )


class CreateEventTool(Tool[CreateEventArguments]):
    """Adds a concert or a rehearsal to a choir."""

    def __init__(self, service: EventService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``create_event``."""
        return "create_event"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Add a concert or a rehearsal to a choir, with an optional programme of works of "
            "its repertoire. Fill in only what the user gave, never invented values. Lessons "
            f"are not available yet. {UTC_NOTICE}"
        )

    @property
    def arguments_model(self) -> type[CreateEventArguments]:
        """The choir, the kind, the attributes and the programme of the event."""
        return CreateEventArguments

    async def execute(self, arguments: CreateEventArguments, context: ToolContext) -> ToolResult:
        """Add the event."""
        details = EventDetails(
            title=arguments.title,
            starts_at=arguments.starts_at,
            ends_at=arguments.ends_at,
            place=arguments.place,
            notes=arguments.notes,
        )
        choir, event = await self._service.create_event(
            arguments.choir,
            EventKind(arguments.kind),
            details,
            programme_items(arguments.programme),
        )
        return ToolResult(
            text=f'Added {event_label(event)} to the choir "{choir.name}" (id {event.id}).',
            structured={
                "choir": choir.name,
                "event": event_data(VisibleEvent(event, complete=True)),
            },
        )
