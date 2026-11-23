# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool giving the file of a score back in the conversation."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.errors import MEGABYTE
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.errors import ScoreTooLargeToReturnError
from my_beautiful_choir.tools.scores.score_data import score_file_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult

CONVERSATION_FILE_MAXIMUM_SIZE = 2 * MEGABYTE
"""Largest score returned in the conversation, in bytes: a returned file may enter
the model context."""


class GetScoreFileArguments(BaseModel):
    """Arguments of ``get_score_file``."""

    score_id: UUID = Field(description="Id of the score, as given by the work.")


class GetScoreFileTool(Tool[GetScoreFileArguments]):
    """Gives back the file of a score, up to a size limit."""

    def __init__(
        self, service: ScoreService, maximum_size: int = CONVERSATION_FILE_MAXIMUM_SIZE
    ) -> None:
        self._service = service
        self._maximum_size = maximum_size

    @property
    def name(self) -> str:
        """``get_score_file``."""
        return "get_score_file"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Give the file of a score back in the conversation, when the user asks to receive "
            f"or send them a score. Scores up to {self._maximum_size / MEGABYTE:g} MB only; for "
            "a larger one, use open_score, or let the user download it from the Work view."
        )

    @property
    def arguments_model(self) -> type[GetScoreFileArguments]:
        """The score."""
        return GetScoreFileArguments

    async def execute(self, arguments: GetScoreFileArguments, context: ToolContext) -> ToolResult:
        """Return the file of the score.

        Raises:
            ScoreTooLargeToReturnError: if the score is larger than the limit.
        """
        work, score, content = await self._service.read_score(arguments.score_id)
        if max(score.size, len(content)) > self._maximum_size:
            raise ScoreTooLargeToReturnError(score.label, self._maximum_size)
        return score_file_result(work, score, content)
