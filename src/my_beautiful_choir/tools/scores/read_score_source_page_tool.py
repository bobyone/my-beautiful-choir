# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""ReadScoreSourcePage MCP tool."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.pdf.pdf_page_renderer import PdfPageRenderer
from my_beautiful_choir.scores.recognition.errors import UnsupportedSourceScoreError
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class ReadScoreSourcePageArguments(BaseModel):
    """Arguments for read_score_source_page."""

    score_id: UUID
    page: int = Field(ge=1, description="One-based page number in the source PDF.")


class ReadScoreSourcePageTool(Tool[ReadScoreSourcePageArguments]):
    """ReadScoreSourcePage operation."""

    def __init__(self, scores: ScoreService, renderer: PdfPageRenderer) -> None:
        self._scores = scores
        self._renderer = renderer

    @property
    def name(self) -> str:
        return "read_score_source_page"

    @property
    def description(self) -> str:
        return (
            "Read an existing PDF page as an image for verification when the user asks. "
            "Compare the image to the MusicXML and report whether each page could be inspected."
        )

    @property
    def arguments_model(self) -> type[ReadScoreSourcePageArguments]:
        return ReadScoreSourcePageArguments

    async def execute(
        self, arguments: ReadScoreSourcePageArguments, context: ToolContext
    ) -> ToolResult:
        _, score, content = await self._scores.read_score(arguments.score_id)
        if score.format is not ScoreFormat.PDF:
            raise UnsupportedSourceScoreError("Choose a stored PDF score.")
        image, count = await self._renderer.render(content, arguments.page)
        return ToolResult(
            f"Page {arguments.page} of {count} from source PDF {score.id}.",
            {"page": arguments.page, "page_count": count, "score_id": str(score.id)},
            png_images=(image,),
        )
