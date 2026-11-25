# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Duplicate a final MusicXML score as a draft."""

from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.get_score_file_tool import GetScoreFileArguments
from my_beautiful_choir.tools.scores.score_data import added_score_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class DuplicateScoreAsDraftTool(Tool[GetScoreFileArguments]):
    """Create a draft independently of its originating final score."""

    def __init__(self, scores: ScoreService) -> None:
        self._scores = scores

    @property
    def name(self) -> str:
        return "duplicate_score_as_draft"

    @property
    def description(self) -> str:
        return "Make an editable draft of a final MusicXML or compressed MusicXML score."

    @property
    def arguments_model(self) -> type[GetScoreFileArguments]:
        return GetScoreFileArguments

    async def execute(self, arguments: GetScoreFileArguments, context: ToolContext) -> ToolResult:
        work, score = await self._scores.duplicate_as_draft(arguments.score_id)
        return added_score_result(work, score)
