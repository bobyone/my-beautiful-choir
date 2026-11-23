# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Give the Work view the file of a score the user chose to download."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.errors import ScoreAboveLimitError
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.errors import ScoreTooLargeToReturnError
from my_beautiful_choir.tools.scores.get_score_file_tool import CONVERSATION_FILE_MAXIMUM_SIZE
from my_beautiful_choir.tools.scores.score_data import score_file_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class DownloadScoreArguments(BaseModel):
    """The score chosen in the Work view."""

    score_id: UUID = Field(description="Id of the score, as given by the work.")


class DownloadScoreTool(Tool[DownloadScoreArguments]):
    """Return the file of a score to the Work view, which asks the host to save it.

    App-only, but a client that does not show views may still let the model
    call it: the conversation limit of ``get_score_file`` is lifted only when
    the client declared that it shows views, and the score limit bounds the
    content then.
    """

    def __init__(
        self,
        view: View,
        service: ScoreService,
        conversation_maximum_size: int = CONVERSATION_FILE_MAXIMUM_SIZE,
    ) -> None:
        self._view = view
        self._service = service
        self._conversation_maximum_size = conversation_maximum_size

    @property
    def name(self) -> str:
        return "download_score"

    @property
    def description(self) -> str:
        return "Give the Work view the file of the score the user chose to download."

    @property
    def arguments_model(self) -> type[DownloadScoreArguments]:
        return DownloadScoreArguments

    @property
    def view(self) -> View:
        return self._view

    @property
    def app_only(self) -> bool:
        return True

    async def execute(self, arguments: DownloadScoreArguments, context: ToolContext) -> ToolResult:
        """Return the file of the score.

        Raises:
            ScoreTooLargeToReturnError: if the client does not show views and
                the score is larger than the conversation limit.
        """
        limit = None if context.client_shows_views else self._conversation_maximum_size
        try:
            work, score, content = await self._service.read_score(arguments.score_id, limit)
        except ScoreAboveLimitError as error:
            raise ScoreTooLargeToReturnError(error.label, error.limit) from error
        return score_file_result(work, score, content)
