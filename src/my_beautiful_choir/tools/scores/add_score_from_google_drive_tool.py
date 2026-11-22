# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool adding a score downloaded from a public Google Drive link."""

from collections.abc import Callable
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.google_drive.google_drive_link import GoogleDriveLink
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from my_beautiful_choir.tools.scores.score_data import (
    LABEL_DESCRIPTION,
    WORK_ID_DESCRIPTION,
    added_score_result,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult

type GoogleDriveSourceFactory = Callable[[GoogleDriveLink], ScoreSource]
"""Creates the source downloading the file of a link."""


class AddScoreFromGoogleDriveArguments(BaseModel):
    """Arguments of ``add_score_from_google_drive``."""

    work_id: UUID = Field(description=WORK_ID_DESCRIPTION)
    link: str = Field(
        description=(
            "Sharing link of a Google Drive file shared with 'Anyone with the link', for "
            "example https://drive.google.com/file/d/<id>/view."
        )
    )
    label: str | None = Field(default=None, description=LABEL_DESCRIPTION)


class AddScoreFromGoogleDriveTool(Tool[AddScoreFromGoogleDriveArguments]):
    """Adds a score from a public Google Drive link."""

    def __init__(self, service: ScoreService, source_factory: GoogleDriveSourceFactory) -> None:
        self._service = service
        self._source_factory = source_factory

    @property
    def name(self) -> str:
        """``add_score_from_google_drive``."""
        return "add_score_from_google_drive"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Add to a work a score file shared publicly on Google Drive: the file is "
            "downloaded and copied into the repertoire, and the link is kept. Accepted "
            "formats: PDF, MusicXML (.musicxml), compressed MusicXML (.mxl) and MuseScore "
            "(.mscz), up to 50 MB. Folder links are not supported."
        )

    @property
    def arguments_model(self) -> type[AddScoreFromGoogleDriveArguments]:
        """The work, the link and the optional label."""
        return AddScoreFromGoogleDriveArguments

    async def execute(
        self, arguments: AddScoreFromGoogleDriveArguments, context: ToolContext
    ) -> ToolResult:
        """Download and add the score."""
        source = self._source_factory(GoogleDriveLink.parse(arguments.link))
        work, score = await self._service.add_score(arguments.work_id, source, arguments.label)
        return added_score_result(work, score)
