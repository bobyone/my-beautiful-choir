# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""TranscribeScore MCP tool."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.recognition.transcription_service import TranscriptionService
from my_beautiful_choir.tools.scores.transcription_data import transcription_result
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class TranscribeScoreArguments(BaseModel):
    """Arguments for transcribe_score."""

    score_id: UUID = Field(description="Id of the existing PDF score.")
    recompute: bool = False


class TranscribeScoreTool(Tool[TranscribeScoreArguments]):
    """TranscribeScore operation."""

    def __init__(self, transcriptions: TranscriptionService) -> None:
        self._transcriptions = transcriptions

    @property
    def name(self) -> str:
        return "transcribe_score"

    @property
    def description(self) -> str:
        return (
            "Start local recognition of an existing PDF score without opening a view. "
            "Poll get_transcription_status while pending. Use recompute only when the user "
            "asks for a new transcription."
        )

    @property
    def arguments_model(self) -> type[TranscribeScoreArguments]:
        return TranscribeScoreArguments

    async def execute(
        self, arguments: TranscribeScoreArguments, context: ToolContext
    ) -> ToolResult:
        job = await self._transcriptions.start(arguments.score_id, arguments.recompute)
        return transcription_result(job)
