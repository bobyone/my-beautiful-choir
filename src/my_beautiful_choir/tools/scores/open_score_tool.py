# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool opening a score on the user's computer."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.repertoire.work_data import work_label
from my_beautiful_choir.tools.scores.score_data import describe_score, score_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class OpenScoreArguments(BaseModel):
    """Arguments of ``open_score``."""

    score_id: UUID = Field(description="Id of the score, as given by the work.")


class OpenScoreTool(Tool[OpenScoreArguments]):
    """Opens a score with the default application of the user's computer."""

    def __init__(self, service: ScoreService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``open_score``."""
        return "open_score"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Open a score on the user's computer, in the application that opens its format "
            "(a PDF reader, MuseScore...). A copy is opened: changes made in the application "
            "do not change the score of the repertoire."
        )

    @property
    def arguments_model(self) -> type[OpenScoreArguments]:
        """The score."""
        return OpenScoreArguments

    async def execute(self, arguments: OpenScoreArguments, context: ToolContext) -> ToolResult:
        """Open the score."""
        work, score = await self._service.open_score(arguments.score_id)
        return ToolResult(
            text=(
                f"The score {describe_score(score)} of the work {work_label(work)} "
                "was opened on the user's computer."
            ),
            structured={"work_id": str(work.id), "score": score_data(score)},
        )
