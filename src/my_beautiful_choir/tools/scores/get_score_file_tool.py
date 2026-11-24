# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool giving the file of a score back in the conversation."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.score_data import score_file_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class GetScoreFileArguments(BaseModel):
    """Arguments of ``get_score_file``."""

    score_id: UUID = Field(description="Id of the score, as given by the work.")


class GetScoreFileTool(Tool[GetScoreFileArguments]):
    """Gives back the file of a score."""

    def __init__(self, service: ScoreService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``get_score_file``."""
        return "get_score_file"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Give the file of a score back in the conversation, when the user asks to receive "
            "or send them a score."
        )

    @property
    def arguments_model(self) -> type[GetScoreFileArguments]:
        """The score."""
        return GetScoreFileArguments

    async def execute(self, arguments: GetScoreFileArguments, context: ToolContext) -> ToolResult:
        """Return the file of the score."""
        work, score, content = await self._service.read_score(arguments.score_id)
        return score_file_result(work, score, content)
