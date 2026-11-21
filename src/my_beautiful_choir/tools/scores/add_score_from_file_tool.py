# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool adding a score read from a file of the user's computer."""

from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.local_file_score_source import LocalFileScoreSource
from my_beautiful_choir.tools.scores.score_data import (
    LABEL_DESCRIPTION,
    WORK_ID_DESCRIPTION,
    added_score_result,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class AddScoreFromFileArguments(BaseModel):
    """Arguments of ``add_score_from_file``."""

    work_id: UUID = Field(description=WORK_ID_DESCRIPTION)
    path: str = Field(
        description=(
            "Absolute path of the score file on the user's computer; a leading ~ is the "
            "user's home directory."
        )
    )
    label: str | None = Field(default=None, description=LABEL_DESCRIPTION)


class AddScoreFromFileTool(Tool[AddScoreFromFileArguments]):
    """Adds a score from a local file."""

    def __init__(self, service: ScoreService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``add_score_from_file``."""
        return "add_score_from_file"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Add to a work a score file of the user's computer, named by its absolute path. "
            "Accepted formats: PDF, MusicXML (.musicxml), compressed MusicXML (.mxl) and "
            "MuseScore (.mscz), up to 50 MB; the file is copied into the repertoire. Use it "
            "only for a file the user asked to add."
        )

    @property
    def arguments_model(self) -> type[AddScoreFromFileArguments]:
        """The work, the path and the optional label."""
        return AddScoreFromFileArguments

    async def execute(
        self, arguments: AddScoreFromFileArguments, context: ToolContext
    ) -> ToolResult:
        """Add the score."""
        source = LocalFileScoreSource(Path(arguments.path))
        work, score = await self._service.add_score(arguments.work_id, source, arguments.label)
        return added_score_result(work, score)
