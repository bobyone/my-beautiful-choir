# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read a work and its scores for the model and its view."""

from collections.abc import Mapping, Sequence
from typing import cast
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.repertoire.work_data import work_data
from my_beautiful_choir.tools.scores.score_data import WORK_ID_DESCRIPTION, score_data
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class ShowWorkArguments(BaseModel):
    """The id of the requested work."""

    work_id: UUID = Field(description=WORK_ID_DESCRIPTION)


class ShowWorkTool(ViewTool[ShowWorkArguments]):
    """Show the details and scores of a work."""

    def __init__(
        self,
        view: View,
        repertoire: RepertoireService,
        scores: ScoreService,
        supports_transcription: bool = False,
    ) -> None:
        super().__init__(view)
        self._repertoire = repertoire
        self._scores = scores
        self._supports_transcription = supports_transcription

    @property
    def name(self) -> str:
        return "show_work"

    @property
    def description(self) -> str:
        return "Show a work and its scores, including the score ids."

    @property
    def arguments_model(self) -> type[ShowWorkArguments]:
        return ShowWorkArguments

    async def _collect(
        self, arguments: ShowWorkArguments, context: ToolContext
    ) -> Mapping[str, object]:
        choir, work = await self._repertoire.get_work(arguments.work_id)
        scores = await self._scores.list_scores(work.id)
        return {
            "choir": choir.name,
            "work": work_data(work),
            "scores": list(map(score_data, scores)),
            "supports_transcription": self._supports_transcription,
        }

    def _describe(self, data: Mapping[str, object]) -> str:
        work = cast(Mapping[str, object], data["work"])
        scores = cast(Sequence[Mapping[str, object]], data["scores"])
        summary = f"{work['title']} ({data['choir']}) has {len(scores)} score(s)."
        return "\n".join([summary, *(f"{score['label']} (id {score['id']})" for score in scores)])
