# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""ReadMusicXmlScore MCP tool."""

import asyncio
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.errors import ScoreNotFoundError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_text
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.score_data import describe_score, score_lifecycle_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class ReadMusicXmlScoreArguments(BaseModel):
    """Arguments for read_musicxml_score."""

    score_id: UUID
    offset: int = Field(default=0, ge=0, description="Character offset in the XML text.")
    length: int = Field(default=12000, ge=1, le=12000)


class ReadMusicXmlScoreTool(Tool[ReadMusicXmlScoreArguments]):
    """ReadMusicXmlScore operation."""

    def __init__(self, scores: ScoreService) -> None:
        self._scores = scores

    @property
    def name(self) -> str:
        return "read_musicxml_score"

    @property
    def description(self) -> str:
        return (
            "Read MusicXML directly as text. Continue at next_offset until the score is read. "
            "For verification, use read_score_source_page with the returned source_score_id "
            "when the source is available, and report any unavailable pages."
        )

    @property
    def arguments_model(self) -> type[ReadMusicXmlScoreArguments]:
        return ReadMusicXmlScoreArguments

    async def execute(
        self, arguments: ReadMusicXmlScoreArguments, context: ToolContext
    ) -> ToolResult:
        _, score, content = await self._scores.read_score(arguments.score_id)
        if score.format is not ScoreFormat.MUSICXML:
            raise InvalidMusicXmlError("Choose an uncompressed MusicXML score.")
        xml = await asyncio.to_thread(musicxml_text, content)
        if arguments.offset >= len(xml):
            raise InvalidMusicXmlError("Use an offset within the MusicXML score.")
        end = min(arguments.offset + arguments.length, len(xml))
        portion = xml[arguments.offset : end]
        next_offset = end if end < len(xml) else None
        source = None
        source_available = None
        source_description = "No source PDF is recorded."
        if score.source_score_id is not None:
            try:
                await self._scores.describe_score(score.source_score_id)
            except ScoreNotFoundError:
                source_available = False
                source_description = "The source PDF is no longer available."
            else:
                source_available = True
                source = str(score.source_score_id)
                source_description = f"Source PDF: {source}."
        return ToolResult(
            f"MusicXML of {describe_score(score, include_id=True)}, "
            f"characters {arguments.offset}-{end} of {len(xml)}. "
            f"{source_description} Next offset: {next_offset}.\n\n{portion}",
            {
                "score_id": str(score.id),
                **score_lifecycle_data(score),
                "source_score_id": source,
                "source_available": source_available,
                "xml": portion,
                "offset": arguments.offset,
                "next_offset": next_offset,
            },
        )
