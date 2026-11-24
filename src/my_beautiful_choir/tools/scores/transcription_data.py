# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""MCP and Work view representation of recognition in progress."""

from my_beautiful_choir.scores.recognition.errors import AUDIVERIS_INSTALL_URL
from my_beautiful_choir.scores.recognition.transcription_job import TranscriptionJob
from my_beautiful_choir.tools.scores.score_data import score_data
from my_beautiful_choir.tools.tool_result import ToolResult


def transcription_result(job: TranscriptionJob) -> ToolResult:
    """Provide actionable status to a model or a work view."""
    status: dict[str, object] = {"job_id": str(job.id), "source_score_id": str(job.source_id)}
    if job.error:
        status.update(state="failed", error_code=job.error.code)
        if job.error.code in {"engine_missing", "engine_unavailable"}:
            status["install_url"] = AUDIVERIS_INSTALL_URL
        return ToolResult(str(job.error), status)
    if job.scores:
        scores = list(map(score_data, job.scores))
        status.update(state="done", scores=scores)
        if len(scores) == 1:
            status["score"] = scores[0]
        score_ids = ", ".join(str(score.id) for score in job.scores)
        return ToolResult(
            f"MusicXML results from source PDF {job.source_id}, in order: {score_ids}. "
            "Use read_musicxml_score with each id to read its XML text directly.",
            status,
        )
    status["state"] = "pending"
    return ToolResult(f"Transcription in progress. Check its status using job id {job.id}.", status)
