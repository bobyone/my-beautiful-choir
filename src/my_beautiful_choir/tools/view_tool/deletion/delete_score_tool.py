# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool deleting a score."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.tools.view_tool.deletion.delete_tool import DeleteTool


class DeleteScoreArguments(BaseModel):
    """Arguments of ``delete_score``."""

    score_id: UUID = Field(description="Id of the score, as given by the work.")


class DeleteScoreTool(DeleteTool[DeleteScoreArguments]):
    """Deletes a score after the user's confirmation."""

    @property
    def name(self) -> str:
        """``delete_score``."""
        return "delete_score"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Delete a score of a work, after the user's confirmation, which this tool asks "
            "for itself: never ask for it in the conversation first."
        )

    @property
    def arguments_model(self) -> type[DeleteScoreArguments]:
        """The score."""
        return DeleteScoreArguments

    async def _target_id(self, arguments: DeleteScoreArguments) -> UUID:
        return arguments.score_id
