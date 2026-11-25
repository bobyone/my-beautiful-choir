# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Describe musical contents of an existing score without transferring its file."""

from uuid import UUID

from my_beautiful_choir.scores.reading.score_description import describe_music
from my_beautiful_choir.scores.reading.score_reading_service import (
    ScoreReadingService,
    check_snapshot,
)
from my_beautiful_choir.tools.read_only_tool import ReadOnlyTool
from my_beautiful_choir.tools.scores.reading_arguments import ReadingArguments
from my_beautiful_choir.tools.scores.reading_page import ReadingPage
from my_beautiful_choir.tools.scores.score_data import score_lifecycle_data
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class DescribeScoreArguments(ReadingArguments):
    """Identify a score through the existing repertoire."""

    score_id: UUID


class DescribeScoreTool(ReadOnlyTool[DescribeScoreArguments]):
    """Summarise parts, instruments, keys, metres, ranges, verses and detected anomalies."""

    def __init__(self, reading: ScoreReadingService, page: ReadingPage) -> None:
        self._reading = reading
        self._page = page

    @property
    def name(self) -> str:
        return "describe_score"

    @property
    def description(self) -> str:
        return "Describe the parts and musical content of a stored MusicXML score."

    @property
    def arguments_model(self) -> type[DescribeScoreArguments]:
        return DescribeScoreArguments

    async def execute(self, arguments: DescribeScoreArguments, context: ToolContext) -> ToolResult:
        snapshot = await self._reading.read(arguments.score_id)
        check_snapshot(snapshot.fingerprint, arguments.snapshot)
        return self._page.build(
            {
                "score_id": str(snapshot.score.id),
                "snapshot": snapshot.fingerprint,
                **score_lifecycle_data(snapshot.score),
            },
            describe_music(snapshot.music),
            offset=arguments.offset,
        )
