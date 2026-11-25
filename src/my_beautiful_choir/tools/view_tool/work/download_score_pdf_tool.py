# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Render and download a score PDF through the Work view."""

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.pdf.pdf_watermarker import PdfWatermarker
from my_beautiful_choir.scores.pdf.score_pdf_exporter import ScorePdfExporter
from my_beautiful_choir.scores.score_rules import download_name
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.score_state import ScoreState
from my_beautiful_choir.tools.scores.get_score_file_tool import GetScoreFileArguments
from my_beautiful_choir.tools.scores.score_data import describe_score, score_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_file import ToolFile
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class DownloadScorePdfTool(Tool[GetScoreFileArguments]):
    """Only return a draft PDF after every page has been watermarked."""

    def __init__(
        self,
        view: View,
        scores: ScoreService,
        exporter: ScorePdfExporter,
        watermarker: PdfWatermarker,
    ) -> None:
        self._view = view
        self._scores = scores
        self._exporter = exporter
        self._watermarker = watermarker

    @property
    def name(self) -> str:
        return "download_score_pdf"

    @property
    def description(self) -> str:
        return "Render a PDF copy of a MusicXML score for download from the Work view."

    @property
    def view(self) -> View:
        return self._view

    @property
    def app_only(self) -> bool:
        return True

    @property
    def arguments_model(self) -> type[GetScoreFileArguments]:
        return GetScoreFileArguments

    async def execute(self, arguments: GetScoreFileArguments, context: ToolContext) -> ToolResult:
        work, score, content = await self._scores.read_score(arguments.score_id)
        draft = score.state is ScoreState.DRAFT
        pdf = await self._exporter.export(score.format, content)
        if draft:
            pdf = await self._watermarker.mark_draft(pdf)
        name = download_name(score.original_name, score.label, ScoreFormat.PDF, draft=draft)
        return ToolResult(
            f"Rendered a PDF of {describe_score(score)}.",
            {"work_id": str(work.id), "score": score_data(score)},
            files=(ToolFile(name, ScoreFormat.PDF.media_type, pdf),),
        )
