# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool editing an event."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.event import EventChanges
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.events.visible_event import VisibleEvent
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

_KEEP_OR_CLEAR = "Omit it to keep the current value; give an empty value to clear it."


class EditEventArguments(BaseModel):
    """Arguments of ``edit_event``: only the given attributes change."""

    event_id: UUID = Field(description="Id of the event, as given by list_events.")
    title: str | None = Field(default=None, description="New title. Omit it to keep the title.")
    starts_at: datetime | None = Field(
        default=None, description=f"New start. Omit it to keep the start. {DATE_DESCRIPTION}"
    )
    ends_at: datetime | None = Field(
        default=None, description=f"New end. Omit it to keep the end. {DATE_DESCRIPTION}"
    )
    clear_end: bool = Field(default=False, description="True to remove the end of the event.")
    place: str | None = Field(default=None, description=f"Place. {_KEEP_OR_CLEAR}")
    notes: str | None = Field(
        default=None, description=f"Short internal notes, as for create_event. {_KEEP_OR_CLEAR}"
    )
    programme: list[ProgrammeItemArguments] | None = Field(
        default=None,
        description=(
            f"{PROGRAMME_DESCRIPTION} Replaces the whole current programme; give the complete "
            "list. Omit it to keep the programme; give an empty list to clear it."
        ),
    )


class EditEventTool(Tool[EditEventArguments]):
    """Edits the attributes and the programme of an event."""

    def __init__(self, service: EventService, settings: EventSettings) -> None:
        self._service = service
        self._notes_limit = settings.notes_chars

    @property
    def name(self) -> str:
        """``edit_event``."""
        return "edit_event"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Edit the attributes or the programme of an event; only the given ones change. "
            "The kind of an event cannot change: to change it, delete the event and create a "
            f"new one. To hide a concert programme from the public, use set_programme_hidden. "
            f"{UTC_NOTICE}"
        )

    @property
    def arguments_model(self) -> type[EditEventArguments]:
        """The event and its changed attributes."""
        return EditEventArguments

    async def execute(self, arguments: EditEventArguments, context: ToolContext) -> ToolResult:
        """Edit the event."""
        changes = EventChanges(
            title=arguments.title,
            starts_at=arguments.starts_at,
            ends_at=arguments.ends_at,
            clear_end=arguments.clear_end,
            place=arguments.place,
            notes=arguments.notes,
        )
        programme = None if arguments.programme is None else programme_items(arguments.programme)
        event = await self._service.edit_event(arguments.event_id, changes, programme)
        return ToolResult(
            text=f"Updated {event_label(event)}.",
            structured={"event": event_data(VisibleEvent(event, complete=True), self._notes_limit)},
        )
