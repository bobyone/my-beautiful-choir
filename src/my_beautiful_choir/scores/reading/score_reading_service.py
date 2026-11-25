# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read authorised score snapshots for musical inspection and comparison."""

from hashlib import sha256
from uuid import UUID

from my_beautiful_choir.scores.reading.errors import ScoreComparisonError, ScoreSelectionError
from my_beautiful_choir.scores.reading.read_score import ReadScore
from my_beautiful_choir.scores.reading.score_reader import ScoreReader
from my_beautiful_choir.scores.score_service import ScoreService


class ScoreReadingService:
    """Keep authorisation and source representation outside the musical operations."""

    def __init__(self, scores: ScoreService, reader: ScoreReader) -> None:
        self._scores = scores
        self._reader = reader

    async def read(self, score_id: UUID) -> ReadScore:
        """Read a score through the existing repertoire permissions."""
        _, score, contents = await self._scores.read_score(score_id)
        return ReadScore(
            score, await self._reader.read(score.format, contents), sha256(contents).hexdigest()
        )

    async def read_pair(self, before: UUID, after: UUID) -> tuple[ReadScore, ReadScore]:
        """Require access to both scores and a shared work before reading either file."""
        _, left = await self._scores.describe_score(before)
        _, right = await self._scores.describe_score(after)
        if left.work_id != right.work_id:
            raise ScoreComparisonError("Choose two scores of the same work.")
        first = await self.read(before)
        return first, first if before == after else await self.read(after)


def check_snapshot(actual: str, expected: str | None) -> None:
    """Require a fresh inspection if the score has changed between pages."""
    if expected is not None and expected != actual:
        raise ScoreSelectionError("The score changed. Restart the inspection from the first page.")
