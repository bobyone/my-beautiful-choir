# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read a choir's repertoire for the model and its view."""

from collections.abc import Mapping, Sequence
from typing import cast

from pydantic import BaseModel, Field

from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.choirs.errors import NoChoirError
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.tools.choirs.choir_data import CHOIR_FIELD_DESCRIPTION, choir_data
from my_beautiful_choir.tools.repertoire.work_data import work_data
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class ShowRepertoireArguments(BaseModel):
    """Optional choir and title or composer search."""

    choir: str | None = Field(default=None, max_length=100, description=CHOIR_FIELD_DESCRIPTION)
    search: str | None = Field(
        default=None, max_length=200, description="Part of a title or composer."
    )


class ShowRepertoireTool(ViewTool[ShowRepertoireArguments]):
    """Show and search the works of a choir."""

    def __init__(self, view: View, repertoire: RepertoireService, choirs: ChoirService) -> None:
        super().__init__(view)
        self._repertoire = repertoire
        self._choirs = choirs

    @property
    def name(self) -> str:
        return "show_repertoire"

    @property
    def description(self) -> str:
        return "Show the repertoire of a choir and find works by title or composer."

    @property
    def arguments_model(self) -> type[ShowRepertoireArguments]:
        return ShowRepertoireArguments

    async def _collect(
        self, arguments: ShowRepertoireArguments, context: ToolContext
    ) -> Mapping[str, object]:
        choirs = await self._choirs.list_choirs()
        try:
            choir, works, counts = await self._repertoire.search_with_score_counts(
                arguments.choir, arguments.search
            )
        except NoChoirError:
            return {"choir": None, "choirs": [], "works": [], "search": ""}
        return {
            "choir": choir.name,
            "choirs": [choir_data(item) for item in choirs],
            "works": [{**work_data(work), "score_count": counts.get(work.id, 0)} for work in works],
            "search": arguments.search or "",
        }

    def _describe(self, data: Mapping[str, object]) -> str:
        if data["choir"] is None:
            return "There are no choirs yet. Ask the user for the name of their first choir."
        works = cast(Sequence[Mapping[str, object]], data["works"])
        summary = f"Repertoire of {data['choir']}: {len(works)} work(s)."
        return "\n".join([summary, *(f"{work['title']} (id {work['id']})" for work in works)])
