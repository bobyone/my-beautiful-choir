# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool reading one event."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.tools.events.event_data import UTC_NOTICE, event_data, event_text
from my_beautiful_choir.tools.read_only_tool import ReadOnlyTool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class GetEventArguments(BaseModel):
    """Arguments of ``get_event``."""

    event_id: UUID = Field(description="Id of the event, as given by list_events.")


class GetEventTool(ReadOnlyTool[GetEventArguments]):
    """Reads an event with its programme."""

    def __init__(self, service: EventService, settings: EventSettings) -> None:
        self._service = service
        self._notes_limit = settings.notes_chars

    @property
    def name(self) -> str:
        """``get_event``."""
        return "get_event"

    @property
    def description(self) -> str:
        """Description for the model."""
        return f"Read an event of a choir with its details and its programme. {UTC_NOTICE}"

    @property
    def arguments_model(self) -> type[GetEventArguments]:
        """The event."""
        return GetEventArguments

    async def execute(self, arguments: GetEventArguments, context: ToolContext) -> ToolResult:
        """Read the event."""
        choir, visible = await self._service.get_event(arguments.event_id)
        return ToolResult(
            text=f'Choir "{choir.name}": {event_text(visible, self._notes_limit)}',
            structured={"choir": choir.name, "event": event_data(visible, self._notes_limit)},
        )
