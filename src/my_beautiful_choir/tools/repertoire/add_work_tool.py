# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool adding a work to the repertoire of a choir."""

from pydantic import BaseModel, Field

from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import WorkDetails
from my_beautiful_choir.repertoire.work_rules import (
    NAME_LENGTH,
    NOTES_LENGTH,
    TITLE_LENGTH,
    VOICING_LENGTH,
)
from my_beautiful_choir.tools.choirs.choir_data import CHOIR_FIELD_DESCRIPTION
from my_beautiful_choir.tools.repertoire.work_data import (
    SUNG_LANGUAGES_DESCRIPTION,
    VOICING_DESCRIPTION,
    work_data,
    work_label,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class AddWorkArguments(BaseModel):
    """Arguments of ``add_work``."""

    choir: str | None = Field(default=None, description=CHOIR_FIELD_DESCRIPTION)
    title: str = Field(description=f"Title of the work, at most {TITLE_LENGTH} characters.")
    composer: str | None = Field(
        default=None, description=f"Composer, at most {NAME_LENGTH} characters."
    )
    arranger: str | None = Field(
        default=None, description=f"Arranger, at most {NAME_LENGTH} characters."
    )
    voicing: str | None = Field(
        default=None, description=f"{VOICING_DESCRIPTION} At most {VOICING_LENGTH} characters."
    )
    sung_languages: list[str] = Field(default_factory=list, description=SUNG_LANGUAGES_DESCRIPTION)
    notes: str | None = Field(
        default=None, description=f"Free notes, at most {NOTES_LENGTH} characters."
    )


class AddWorkTool(Tool[AddWorkArguments]):
    """Adds a work to the repertoire."""

    def __init__(self, service: RepertoireService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``add_work``."""
        return "add_work"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Add a work to the repertoire of a choir. Only the title is required; fill in the "
            "other attributes the user gave, never invented ones. Two works may have the same "
            "title, for example two arrangements."
        )

    @property
    def arguments_model(self) -> type[AddWorkArguments]:
        """The choir and the attributes of the work."""
        return AddWorkArguments

    async def execute(self, arguments: AddWorkArguments, context: ToolContext) -> ToolResult:
        """Add the work."""
        details = WorkDetails(
            title=arguments.title,
            composer=arguments.composer,
            arranger=arguments.arranger,
            voicing=arguments.voicing,
            sung_languages=tuple(arguments.sung_languages),
            notes=arguments.notes,
        )
        choir, work = await self._service.add_work(arguments.choir, details)
        return ToolResult(
            text=f"The work {work_label(work)} was added to {choir.name}; its id is {work.id}.",
            structured={"choir": choir.name, "work": work_data(work)},
        )
