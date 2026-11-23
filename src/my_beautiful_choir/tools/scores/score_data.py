# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content, descriptions and results shared by the score tools."""

from collections.abc import Mapping

from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_rules import LABEL_LENGTH, download_name
from my_beautiful_choir.tools.repertoire.work_data import work_label
from my_beautiful_choir.tools.tool_file import ToolFile
from my_beautiful_choir.tools.tool_result import ToolResult

WORK_ID_DESCRIPTION = "Id of the work, as given by the repertoire."


LABEL_DESCRIPTION = (
    "Label distinguishing the score from the other scores of the work, for example "
    f"'Alto part', at most {LABEL_LENGTH} characters. Omit it to use the file name."
)


def score_data(score: Score) -> Mapping[str, object]:
    """Structured content describing a score."""
    return {
        "id": str(score.id),
        "work_id": str(score.work_id),
        "label": score.label,
        "format": score.format.value,
        "size": score.size,
        "original_name": score.original_name,
        "origin": score.origin.value,
        "link": score.link,
        "added_at": score.added_at.isoformat(),
    }


def score_file_result(work: Work, score: Score, content: bytes) -> ToolResult:
    """Result of a tool giving back the file of a score, named by its download name."""
    name = download_name(score.original_name, score.label, score.format)
    return ToolResult(
        text=(
            f"Here is the file of the score {score.label!r} ({score.format.display_name}, "
            f"{len(content)} bytes) of the work {work_label(work)}, named {name!r}."
        ),
        structured={"work_id": str(work.id), "score": score_data(score)},
        files=(ToolFile(name, score.format.media_type, content),),
    )


def added_score_result(work: Work, score: Score) -> ToolResult:
    """Result of a tool adding a score."""
    return ToolResult(
        text=(
            f"The score {score.label!r} ({score.format.display_name}) was added to the work "
            f"{work_label(work)}; its id is {score.id}."
        ),
        structured={"work_id": str(work.id), "score": score_data(score)},
    )
