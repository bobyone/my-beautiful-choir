# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""FindScoreSources MCP tool."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.repertoire.page_request import PageRequest
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.recognition.errors import UnsupportedSourceScoreError
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.repertoire.work_data import work_label
from my_beautiful_choir.tools.scores.score_data import score_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class FindScoreSourcesArguments(BaseModel):
    """Arguments for find_score_sources."""

    work_id: UUID | None = None
    work_title: str | None = Field(default=None, min_length=1, max_length=200)
    choir: str | None = Field(default=None, max_length=100)
    label: str | None = Field(default=None, max_length=100)


class FindScoreSourcesTool(Tool[FindScoreSourcesArguments]):
    """FindScoreSources operation."""

    def __init__(self, scores: ScoreService, repertoire: RepertoireService) -> None:
        self._scores = scores
        self._repertoire = repertoire

    @property
    def name(self) -> str:
        return "find_score_sources"

    @property
    def description(self) -> str:
        return (
            "Find PDF scores without opening a view. Provide a work id or a work title "
            "and optional choir. Ask the user which work or PDF to use if several match."
        )

    @property
    def arguments_model(self) -> type[FindScoreSourcesArguments]:
        return FindScoreSourcesArguments

    async def execute(
        self, arguments: FindScoreSourcesArguments, context: ToolContext
    ) -> ToolResult:
        work_id = arguments.work_id
        if work_id is None:
            if arguments.work_title is None or not arguments.work_title.strip():
                raise UnsupportedSourceScoreError("Provide a work id or a work title.")
            page = await self._repertoire.search_page_with_score_counts(
                arguments.choir, arguments.work_title, PageRequest()
            )
            if page.work_count != 1:
                choices = [{"id": str(work.id), "label": work_label(work)} for work in page.works]
                message = (
                    "Several works match. Ask which work to use or narrow the search."
                    if choices
                    else "No works match in this choir. Check the title and choir."
                )
                return ToolResult(message, {"works": choices, "work_count": page.work_count})
            work_id = page.works[0].id
        matches = [
            score
            for score in await self._scores.list_scores(work_id)
            if score.format is ScoreFormat.PDF
            and (arguments.label is None or arguments.label.casefold() in score.label.casefold())
        ]
        text = "\n".join(f"{score.label!r} (id {score.id})" for score in matches)
        return ToolResult(
            text or "No PDF scores match.",
            {"work_id": str(work_id), "scores": list(map(score_data, matches))},
        )
