# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read a page of a choir's repertoire for the model and its view."""

from collections.abc import Mapping, Sequence
from typing import cast

from pydantic import BaseModel, Field

from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.choirs.errors import NoChoirError
from my_beautiful_choir.repertoire.repertoire_page import (
    DEFAULT_PAGE_SIZE,
    MAXIMUM_PAGE_SIZE,
    PageRequest,
)
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.tools.choirs.choir_data import CHOIR_FIELD_DESCRIPTION, choir_data
from my_beautiful_choir.tools.repertoire.work_data import work_data
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class ShowRepertoireArguments(BaseModel):
    """Optional choir, title or composer search, and repertoire page."""

    choir: str | None = Field(default=None, max_length=100, description=CHOIR_FIELD_DESCRIPTION)
    search: str | None = Field(
        default=None, max_length=200, description="Part of a title or composer."
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Number of the repertoire page, from 1; past the last page, the last one.",
    )
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAXIMUM_PAGE_SIZE,
        description="Number of works per repertoire page.",
    )


class ShowRepertoireTool(ViewTool[ShowRepertoireArguments]):
    """Show and search the works of a choir, one repertoire page at a time."""

    def __init__(self, view: View, repertoire: RepertoireService, choirs: ChoirService) -> None:
        super().__init__(view)
        self._repertoire = repertoire
        self._choirs = choirs

    @property
    def name(self) -> str:
        return "show_repertoire"

    @property
    def description(self) -> str:
        return (
            "Show one page of the repertoire of a choir, ordered by title, "
            "and find works by title or composer."
        )

    @property
    def arguments_model(self) -> type[ShowRepertoireArguments]:
        return ShowRepertoireArguments

    async def _collect(
        self, arguments: ShowRepertoireArguments, context: ToolContext
    ) -> Mapping[str, object]:
        choirs = await self._choirs.list_choirs()
        request = PageRequest(arguments.page, arguments.page_size)
        try:
            page = await self._repertoire.search_page_with_score_counts(
                arguments.choir, arguments.search, request
            )
        except NoChoirError:
            return {
                "choir": None,
                "choirs": [],
                "works": [],
                "search": "",
                "page": 1,
                "page_size": request.size,
                "page_count": 1,
                "work_count": 0,
            }
        return {
            "choir": page.choir.name,
            "choirs": [choir_data(item) for item in choirs],
            "works": [
                {**work_data(work), "score_count": page.score_counts[work.id]}
                for work in page.works
            ],
            "search": arguments.search or "",
            "page": page.number,
            "page_size": page.size,
            "page_count": page.page_count,
            "work_count": page.work_count,
        }

    def _describe(self, data: Mapping[str, object]) -> str:
        if data["choir"] is None:
            return "There are no choirs yet. Ask the user for the name of their first choir."
        works = cast(Sequence[Mapping[str, object]], data["works"])
        summary = (
            f"Repertoire of {data['choir']}: {data['work_count']} work(s), "
            f"page {data['page']} of {data['page_count']}."
        )
        return "\n".join([summary, *(f"{work['title']} (id {work['id']})" for work in works)])
