# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""AddMusicXmlScore MCP tool."""

import asyncio
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_bytes, musicxml_text
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_rules import LABEL_LENGTH, MAXIMUM_SIZE
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.musicxml_score_source import MusicXmlScoreSource
from my_beautiful_choir.tools.scores.score_data import added_score_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class AddMusicXmlScoreArguments(BaseModel):
    """Arguments for add_musicxml_score."""

    work_id: UUID
    xml: str = Field(min_length=1, max_length=MAXIMUM_SIZE)
    label: str | None = Field(default=None, max_length=LABEL_LENGTH)


class AddMusicXmlScoreTool(Tool[AddMusicXmlScoreArguments]):
    """AddMusicXmlScore operation."""

    def __init__(self, scores: ScoreService) -> None:
        self._scores = scores

    @property
    def name(self) -> str:
        return "add_musicxml_score"

    @property
    def description(self) -> str:
        return (
            "Add raw MusicXML text directly as a new score of a work when requested by the user. "
            "Pass the actual XML text."
        )

    @property
    def arguments_model(self) -> type[AddMusicXmlScoreArguments]:
        return AddMusicXmlScoreArguments

    async def execute(
        self, arguments: AddMusicXmlScoreArguments, context: ToolContext
    ) -> ToolResult:
        content = musicxml_bytes(arguments.xml)
        await asyncio.to_thread(musicxml_text, content)
        source = MusicXmlScoreSource(content, "Score.musicxml", ScoreOrigin.MUSICXML_TEXT)
        return added_score_result(
            *await self._scores.add_score(arguments.work_id, source, arguments.label)
        )
