# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool hiding the programme of a concert from the public, or showing it again."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.events.visible_event import VisibleEvent
from my_beautiful_choir.tools.events.event_data import event_data, event_label
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class SetProgrammeHiddenArguments(BaseModel):
    """Arguments of ``set_programme_hidden``."""

    event_id: UUID = Field(description="Id of the concert, as given by list_events.")
    hidden: bool = Field(
        description="True to hide the programme from the public, False to show it again."
    )


class SetProgrammeHiddenTool(Tool[SetProgrammeHiddenArguments]):
    """Hides or shows the programme of a concert to the public."""

    def __init__(self, service: EventService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``set_programme_hidden``."""
        return "set_programme_hidden"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Hide the programme of a concert from the public, or show it again. Members of "
            "the choir always see it. Only concerts have a public programme. Asking for the "
            "current state changes nothing."
        )

    @property
    def arguments_model(self) -> type[SetProgrammeHiddenArguments]:
        """The concert and the wanted state."""
        return SetProgrammeHiddenArguments

    async def execute(
        self, arguments: SetProgrammeHiddenArguments, context: ToolContext
    ) -> ToolResult:
        """Change the state of the programme."""
        event = await self._service.set_programme_hidden(arguments.event_id, arguments.hidden)
        state = "hidden from" if event.programme_hidden else "shown to"
        return ToolResult(
            text=f"The programme of {event_label(event)} is {state} the public.",
            structured={"event": event_data(VisibleEvent(event, complete=True))},
        )
