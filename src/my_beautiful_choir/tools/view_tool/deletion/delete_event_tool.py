# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool deleting an event with its programme."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.tools.view_tool.deletion.delete_tool import DeleteTool


class DeleteEventArguments(BaseModel):
    """Arguments of ``delete_event``."""

    event_id: UUID = Field(description="Id of the event, as given by list_events.")


class DeleteEventTool(DeleteTool[DeleteEventArguments]):
    """Deletes an event after the user's confirmation."""

    @property
    def name(self) -> str:
        """``delete_event``."""
        return "delete_event"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Delete an event of a choir (concert, rehearsal or lesson) with its programme, "
            "after the user's confirmation, which this tool asks for itself: never ask for "
            "it in the conversation first."
        )

    @property
    def arguments_model(self) -> type[DeleteEventArguments]:
        """The event."""
        return DeleteEventArguments

    async def _target_id(self, arguments: DeleteEventArguments) -> UUID:
        return arguments.event_id
