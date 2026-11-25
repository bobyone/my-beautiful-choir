# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read a part's measures using the versioned exchange notation."""

from typing import Literal
from uuid import UUID

from my_beautiful_choir.scores.reading.measure_range import read_range
from my_beautiful_choir.scores.reading.score_reading_service import (
    ScoreReadingService,
    check_snapshot,
)
from my_beautiful_choir.scores.reading.selections import select_position
from my_beautiful_choir.tools.read_only_tool import ReadOnlyTool
from my_beautiful_choir.tools.scores.reading_arguments import ReadingArguments, Selection
from my_beautiful_choir.tools.scores.reading_page import ReadingPage
from my_beautiful_choir.tools.scores.score_data import score_lifecycle_data
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class ReadMeasuresArguments(ReadingArguments):
    """Select a score, part and inclusive measure range."""

    score_id: UUID
    part: Selection
    start: Selection
    end: Selection
    pitch_mode: Literal["sounding", "written"] = "sounding"


class ReadMeasuresTool(ReadOnlyTool[ReadMeasuresArguments]):
    """Read one part's measures in written or sounding pitch."""

    def __init__(self, reading: ScoreReadingService, page: ReadingPage) -> None:
        self._reading = reading
        self._page = page

    @property
    def name(self) -> str:
        return "read_measures"

    @property
    def description(self) -> str:
        return (
            "Read an inclusive measure range in one part. Integers select positions and strings "
            "select printed labels. Payloads contain versioned exchange notation."
        )

    @property
    def arguments_model(self) -> type[ReadMeasuresArguments]:
        return ReadMeasuresArguments

    async def execute(self, arguments: ReadMeasuresArguments, context: ToolContext) -> ToolResult:
        snapshot = await self._reading.read(arguments.score_id)
        check_snapshot(snapshot.fingerprint, arguments.snapshot)
        parts = {part.position: part for part in snapshot.music.parts}
        number = select_position(
            {p: part.label for p, part in parts.items()}, arguments.part, element="part"
        )
        first, records = read_range(parts[number], arguments.start, arguments.end)
        return self._page.build(
            {
                "score_id": str(snapshot.score.id),
                "snapshot": snapshot.fingerprint,
                "part": number,
                "range_start": first,
                "notation_version": 1,
                "pitch_mode": arguments.pitch_mode,
                "unsupported": snapshot.music.unsupported,
                **score_lifecycle_data(snapshot.score),
            },
            records,
            offset=arguments.offset,
            pitch_mode=arguments.pitch_mode,
        )
