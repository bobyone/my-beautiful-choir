# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool editing a work."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import WorkChanges
from my_beautiful_choir.tools.repertoire.work_data import (
    SUNG_LANGUAGES_DESCRIPTION,
    VOICING_DESCRIPTION,
    work_data,
    work_label,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult

_KEEP_OR_CLEAR = "Omit it to keep the current value; give an empty value to clear it."


class EditWorkArguments(BaseModel):
    """Arguments of ``edit_work``: only the given attributes change."""

    work_id: UUID = Field(description="Id of the work, as given by the repertoire.")
    title: str | None = Field(default=None, description="New title. Omit it to keep the title.")
    composer: str | None = Field(default=None, description=f"Composer. {_KEEP_OR_CLEAR}")
    arranger: str | None = Field(default=None, description=f"Arranger. {_KEEP_OR_CLEAR}")
    voicing: str | None = Field(default=None, description=f"{VOICING_DESCRIPTION} {_KEEP_OR_CLEAR}")
    sung_languages: list[str] | None = Field(
        default=None,
        description=f"{SUNG_LANGUAGES_DESCRIPTION} Replaces the current list. {_KEEP_OR_CLEAR}",
    )
    notes: str | None = Field(default=None, description=f"Free notes. {_KEEP_OR_CLEAR}")


class EditWorkTool(Tool[EditWorkArguments]):
    """Edits the attributes of a work."""

    def __init__(self, service: RepertoireService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``edit_work``."""
        return "edit_work"

    @property
    def description(self) -> str:
        """Description for the model."""
        return "Edit the attributes of a work of the repertoire; only the given ones change."

    @property
    def arguments_model(self) -> type[EditWorkArguments]:
        """The work and its changed attributes."""
        return EditWorkArguments

    async def execute(self, arguments: EditWorkArguments, context: ToolContext) -> ToolResult:
        """Edit the work."""
        languages = arguments.sung_languages
        changes = WorkChanges(
            title=arguments.title,
            composer=arguments.composer,
            arranger=arguments.arranger,
            voicing=arguments.voicing,
            sung_languages=None if languages is None else tuple(languages),
            notes=arguments.notes,
        )
        work = await self._service.edit_work(arguments.work_id, changes)
        return ToolResult(
            text=f"The work {work_label(work)} was updated.",
            structured={"work": work_data(work)},
        )
