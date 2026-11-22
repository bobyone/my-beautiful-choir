# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Accept the bytes of a score chosen by the user in the Work view."""

from base64 import b64decode
from collections.abc import Callable
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.errors import InvalidScoreError
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE, ORIGINAL_NAME_LENGTH
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from my_beautiful_choir.tools.scores.score_data import (
    LABEL_DESCRIPTION,
    WORK_ID_DESCRIPTION,
    added_score_result,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View

MAXIMUM_ENCODED_SIZE = 4 * ((MAXIMUM_SIZE + 2) // 3)


class UploadScoreArguments(BaseModel):
    """The Work view's file picker result."""

    work_id: UUID = Field(description=WORK_ID_DESCRIPTION)
    file_name: str = Field(min_length=1, max_length=ORIGINAL_NAME_LENGTH)
    content: str = Field(min_length=4, max_length=MAXIMUM_ENCODED_SIZE)
    label: str | None = Field(default=None, description=LABEL_DESCRIPTION)


class UploadScoreTool(Tool[UploadScoreArguments]):
    """Add a score from a file chosen in the Work view."""

    def __init__(
        self, view: View, service: ScoreService, source_factory: Callable[[str, bytes], ScoreSource]
    ) -> None:
        self._view = view
        self._service = service
        self._source_factory = source_factory

    @property
    def name(self) -> str:
        return "upload_score"

    @property
    def description(self) -> str:
        return "Add the score selected by the user in the Work view's file picker."

    @property
    def arguments_model(self) -> type[UploadScoreArguments]:
        return UploadScoreArguments

    @property
    def view(self) -> View:
        return self._view

    @property
    def app_only(self) -> bool:
        return True

    async def execute(self, arguments: UploadScoreArguments, context: ToolContext) -> ToolResult:
        try:
            content = b64decode(arguments.content, validate=True)
        except ValueError as error:
            raise InvalidScoreError("content", "expected a base64-encoded file") from error
        work, score = await self._service.add_score(
            arguments.work_id, self._source_factory(arguments.file_name, content), arguments.label
        )
        return added_score_result(work, score)
