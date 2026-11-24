# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""GetTranscriptionStatus MCP tool."""

from uuid import UUID

from pydantic import BaseModel

from my_beautiful_choir.scores.recognition.transcription_service import TranscriptionService
from my_beautiful_choir.tools.scores.transcription_data import transcription_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class GetTranscriptionStatusArguments(BaseModel):
    """Arguments for get_transcription_status."""

    job_id: UUID


class GetTranscriptionStatusTool(Tool[GetTranscriptionStatusArguments]):
    """GetTranscriptionStatus operation."""

    def __init__(self, transcriptions: TranscriptionService) -> None:
        self._transcriptions = transcriptions

    @property
    def name(self) -> str:
        return "get_transcription_status"

    @property
    def description(self) -> str:
        return (
            "Read the status of a PDF transcription. When complete, "
            "use read_musicxml_score to access the XML directly."
        )

    @property
    def arguments_model(self) -> type[GetTranscriptionStatusArguments]:
        return GetTranscriptionStatusArguments

    async def execute(
        self, arguments: GetTranscriptionStatusArguments, context: ToolContext
    ) -> ToolResult:
        return transcription_result(self._transcriptions.status(arguments.job_id))
