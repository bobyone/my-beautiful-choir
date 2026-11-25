# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Compare two authorised scores of the same work."""

from hashlib import sha256
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.scores.reading.match import Match
from my_beautiful_choir.scores.reading.part_match import PartMatch
from my_beautiful_choir.scores.reading.score_comparison import compare_music
from my_beautiful_choir.scores.reading.score_reading_service import (
    ScoreReadingService,
    check_snapshot,
)
from my_beautiful_choir.tools.read_only_tool import ReadOnlyTool
from my_beautiful_choir.tools.scores.reading_arguments import Position, ReadingArguments
from my_beautiful_choir.tools.scores.reading_page import ReadingPage
from my_beautiful_choir.tools.scores.score_data import score_lifecycle_data
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class MatchArguments(BaseModel):
    """One explicit match by position."""

    before: Position
    after: Position


class PartMatchArguments(MatchArguments):
    """Explicit part match with optional matches for its measures."""

    measures: list[MatchArguments] = Field(default_factory=list, max_length=500)


class CompareScoresArguments(ReadingArguments):
    """Two scores and explicit matches where their labels differ or repeat."""

    before_score_id: UUID
    after_score_id: UUID
    matches: list[PartMatchArguments] = Field(default_factory=list, max_length=100)


class CompareScoresTool(ReadOnlyTool[CompareScoresArguments]):
    """Compare musical events and markings while ignoring graphical layout."""

    def __init__(self, reading: ScoreReadingService, page: ReadingPage) -> None:
        self._reading = reading
        self._page = page

    @property
    def name(self) -> str:
        return "compare_scores"

    @property
    def description(self) -> str:
        return (
            "Compare two scores of the same work. Unique non-empty labels are matched "
            "automatically. Supply explicit positions for renamed or repeated labels."
        )

    @property
    def arguments_model(self) -> type[CompareScoresArguments]:
        return CompareScoresArguments

    async def execute(self, arguments: CompareScoresArguments, context: ToolContext) -> ToolResult:
        before, after = await self._reading.read_pair(
            arguments.before_score_id, arguments.after_score_id
        )
        fingerprint = sha256((before.fingerprint + after.fingerprint).encode("ascii")).hexdigest()
        check_snapshot(fingerprint, arguments.snapshot)
        explicit = tuple(
            PartMatch(
                Match(part.before, part.after),
                tuple(Match(pair.before, pair.after) for pair in part.measures),
            )
            for part in arguments.matches
        )
        report = list(compare_music(before.music, after.music, explicit))
        partial = any(
            row["kind"] == "unsupported" or row.get("status") == "ambiguous" for row in report
        )
        status = "partial" if partial else "different" if report else "identical"
        return self._page.build(
            {
                "before_score": {"id": str(before.score.id), **score_lifecycle_data(before.score)},
                "after_score": {"id": str(after.score.id), **score_lifecycle_data(after.score)},
                "snapshot": fingerprint,
                "status": status,
            },
            report,
            offset=arguments.offset,
        )
