# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""ListScores MCP tool."""

from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, model_validator

from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work_rules import TITLE_LENGTH
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.repertoire.work_data import work_label
from my_beautiful_choir.tools.scores.score_data import WORK_ID_DESCRIPTION
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult

WorkQuery = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_LENGTH)
]


class ListScoresArguments(BaseModel):
    """Arguments for list_scores."""

    work_id: UUID | None = Field(default=None, description=WORK_ID_DESCRIPTION)
    work_title: WorkQuery | None = Field(default=None, description="Title or part of a title.")
    work_reference: WorkQuery | None = Field(
        default=None, description="Complete reference in a work title, for example NL15.2."
    )
    choir: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Choir for a title or reference search.",
    )

    @model_validator(mode="after")
    def validate_selector(self) -> Self:
        """Require one work selector and allow a choir only for searches."""
        if (
            sum(value is not None for value in (self.work_id, self.work_title, self.work_reference))
            != 1
        ):
            raise ValueError("Provide exactly one of work_id, work_title or work_reference.")
        if self.work_id is not None and self.choir is not None:
            raise ValueError("Provide a choir only when searching by title or reference.")
        return self


class ListScoresTool(Tool[ListScoresArguments]):
    """Return the scores of one work or choices for an ambiguous search."""

    def __init__(self, scores: ScoreService, repertoire: RepertoireService) -> None:
        self._scores = scores
        self._repertoire = repertoire

    @property
    def name(self) -> str:
        return "list_scores"

    @property
    def description(self) -> str:
        return (
            "Find the scores of a work without opening a view. Provide exactly one work id, "
            "title or reference within a title. Searches use the default choir unless a choir "
            "is supplied. Ask which work to use if several match. Use get_score_file with "
            "the score id to send the file in the conversation."
        )

    @property
    def arguments_model(self) -> type[ListScoresArguments]:
        return ListScoresArguments

    async def execute(self, arguments: ListScoresArguments, context: ToolContext) -> ToolResult:
        work_id = arguments.work_id
        if work_id is None:
            query = arguments.work_reference or arguments.work_title
            assert query is not None  # noqa: S101 - Guaranteed by argument validation.
            works = await self._repertoire.search_titles(
                arguments.choir, query, reference=arguments.work_reference is not None
            )
            if len(works) != 1:
                choices = [{"id": str(work.id), "label": work_label(work)} for work in works]
                text = "No works match in this choir. Check the title or reference and the choir."
                if choices:
                    options = "\n".join(
                        f"{choice['label']} (id {choice['id']})" for choice in choices
                    )
                    text = f"Several works match. Ask which work to use.\n{options}"
                return ToolResult(text, {"works": choices, "work_count": len(works)})
            work_id = works[0].id
        scores = await self._scores.list_scores(work_id)
        text = "\n".join(
            f"{score.label!r} ({score.format.display_name}, id {score.id})" for score in scores
        )
        return ToolResult(
            text or "This work has no scores.",
            {
                "work_id": str(work_id),
                "scores": [
                    {"id": str(score.id), "label": score.label, "format": score.format.value}
                    for score in scores
                ],
            },
        )
