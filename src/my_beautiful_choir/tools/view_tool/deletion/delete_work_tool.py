# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool deleting a work with its scores."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.tools.view_tool.deletion.delete_tool import DeleteTool


class DeleteWorkArguments(BaseModel):
    """Arguments of ``delete_work``."""

    work_id: UUID = Field(description="Id of the work, as given by the repertoire.")


class DeleteWorkTool(DeleteTool[DeleteWorkArguments]):
    """Deletes a work after the user's confirmation."""

    @property
    def name(self) -> str:
        """``delete_work``."""
        return "delete_work"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Delete a work of the repertoire with all its scores, after the user's "
            "confirmation, which this tool asks for itself: never ask for it in the "
            "conversation first."
        )

    @property
    def arguments_model(self) -> type[DeleteWorkArguments]:
        """The work."""
        return DeleteWorkArguments

    async def _target_id(self, arguments: DeleteWorkArguments) -> UUID:
        return arguments.work_id
