# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Commit the draft finalisation confirmed from the Work view."""

from pydantic import BaseModel, Field

from my_beautiful_choir.confirmation.errors import ConfirmationExpiredError
from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations
from my_beautiful_choir.scores.errors import StaleFinalisationError
from my_beautiful_choir.scores.finalisation_preview import FinalisationPreview
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.score_data import describe_score_data, score_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class ConfirmScoreFinalisationArguments(BaseModel):
    """Private, single-use confirmation token."""

    token: str = Field(description="Private token of the reviewed draft.")


class ConfirmScoreFinalisationTool(Tool[ConfirmScoreFinalisationArguments]):
    """Finalise the exact draft approved from the Work view."""

    def __init__(
        self,
        view: View,
        scores: ScoreService,
        pending: PendingConfirmations[tuple[object, FinalisationPreview]],
    ) -> None:
        self._view = view
        self._scores = scores
        self._pending = pending

    @property
    def name(self) -> str:
        return "confirm_score_finalisation"

    @property
    def description(self) -> str:
        return "Finalise the draft confirmed by the user in the Work view."

    @property
    def view(self) -> View:
        return self._view

    @property
    def app_only(self) -> bool:
        return True

    @property
    def arguments_model(self) -> type[ConfirmScoreFinalisationArguments]:
        return ConfirmScoreFinalisationArguments

    async def execute(
        self, arguments: ConfirmScoreFinalisationArguments, context: ToolContext
    ) -> ToolResult:
        try:
            session, preview = self._pending.take(arguments.token)
            if session is not context.session:
                raise ConfirmationExpiredError()
            _, final = await self._scores.finalise(preview)
        except (ConfirmationExpiredError, StaleFinalisationError):
            return ToolResult(
                "The confirmation is no longer current. Review the draft again.",
                {"finalisation_stale": True},
            )
        score = score_data(final)
        return ToolResult(f"Finalised {describe_score_data(score)}.", {"score": score})
