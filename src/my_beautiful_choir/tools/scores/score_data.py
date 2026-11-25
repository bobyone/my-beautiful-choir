# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content, descriptions and results shared by the score tools."""

from collections.abc import Mapping
from typing import cast

from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_rules import LABEL_LENGTH, download_name
from my_beautiful_choir.scores.score_state import ScoreState
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
        **score_lifecycle_data(score),
        **({"movement_number": score.movement_number} if score.movement_number is not None else {}),
        "size": score.size,
        "original_name": score.original_name,
        "origin": score.origin.value,
        "link": score.link,
        "added_at": score.added_at.isoformat(),
    }


def score_lifecycle_data(score: Score) -> Mapping[str, object]:
    """State, version or draft date, and lineage, for compact and full results."""
    data: dict[str, object] = {"state": score.state.value}
    if score.state is ScoreState.FINAL:
        data["version_number"] = score.version_number
    else:
        data["draft_date"] = score.added_at.isoformat()
    if origin := score.originating_score:
        data["originating_score"] = {
            "id": str(origin.id),
            "label": origin.label,
            "version_number": origin.version_number,
        }
    return data


def describe_score_data(data: Mapping[str, object], *, include_id: bool = False) -> str:
    """Describe a score's state consistently in model-facing text."""
    if data["state"] == ScoreState.DRAFT:
        details = f"draft of {str(data['draft_date'])[:10]}"
    else:
        details = f"final v{data['version_number']}"
    if origin := data.get("originating_score"):
        source = cast(Mapping[str, object], origin)
        details += f", from {source['label']!r} v{source['version_number']}"
    if include_id:
        details += f", id {data['id']}"
    return f"{data['label']!r} ({details})"


def describe_score(score: Score, *, include_id: bool = False) -> str:
    """Describe a score from its model representation."""
    return describe_score_data(score_data(score), include_id=include_id)


def score_file_result(work: Work, score: Score, content: bytes) -> ToolResult:
    """Result of a tool giving back the file of a score, named by its download name."""
    name = download_name(
        score.original_name, score.label, score.format, draft=score.state is ScoreState.DRAFT
    )
    return ToolResult(
        text=(
            f"Here is the file of the score {describe_score(score)} ({score.format.display_name}, "
            f"{len(content)} bytes) of the work {work_label(work)}, named {name!r}."
        ),
        structured={"work_id": str(work.id), "score": score_data(score)},
        files=(ToolFile(name, score.format.media_type, content),),
    )


def added_score_result(work: Work, score: Score) -> ToolResult:
    """Result of a tool adding a score."""
    return ToolResult(
        text=(
            f"The score {describe_score(score)} ({score.format.display_name}) was added "
            f"to the work {work_label(work)}; its id is {score.id}."
        ),
        structured={"work_id": str(work.id), "score": score_data(score)},
    )
