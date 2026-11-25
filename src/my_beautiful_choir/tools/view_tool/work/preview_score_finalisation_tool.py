# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Show the work and a validated draft awaiting the user's confirmation."""

from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations
from my_beautiful_choir.scores.finalisation_preview import FinalisationPreview
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.get_score_file_tool import GetScoreFileArguments
from my_beautiful_choir.tools.scores.score_data import describe_score_data, score_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.tools.view_tool.work.show_work_tool import ShowWorkTool
from my_beautiful_choir.views.view import View


class PreviewScoreFinalisationTool(Tool[GetScoreFileArguments]):
    """Prepare finalisation and deliver the confirmation token only to the view."""

    def __init__(
        self,
        work_view: ShowWorkTool,
        scores: ScoreService,
        pending: PendingConfirmations[tuple[object, FinalisationPreview]],
        enabled: bool,
    ) -> None:
        self._work_view = work_view
        self._scores = scores
        self._pending = pending
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "preview_score_finalisation"

    @property
    def view(self) -> View:
        return self._work_view.view

    @property
    def description(self) -> str:
        return "Validate a draft and open the Work view for the user to confirm finalisation."

    @property
    def arguments_model(self) -> type[GetScoreFileArguments]:
        return GetScoreFileArguments

    async def execute(self, arguments: GetScoreFileArguments, context: ToolContext) -> ToolResult:
        if not self._enabled or context.session is None:
            return ToolResult("Open the Work view in a configured MCP Apps client to finalise.")
        report, preview = await self._scores.preview_finalisation(arguments.score_id)
        if preview is None:
            return ToolResult(
                "Draft validation failed: " + " ".join(report.errors),
                {"validation_errors": list(report.errors)},
            )
        data = await self._work_view.collect_work(preview.score.work_id)
        score = score_data(preview.score)
        return ToolResult(
            f"Ask the user to confirm finalisation of {describe_score_data(score)} "
            "in the Work view.",
            {**data, "finalisation": score},
            view_metadata={"finalisation_token": self._pending.keep((context.session, preview))},
        )
